"""
Processing Server - Server xử lý ảnh
Nhận gói tin frame từ Camera Server qua TCP Socket
Xử lý xóa nền bằng Spark và lưu kết quả
"""
import socket
import struct
import cv2
import numpy as np
import os
import argparse
from datetime import datetime
from pyspark import SparkContext, SparkConf
from background_remover import remove_background


class ProcessingServer:
    def __init__(self, camera_host='camera-server', camera_port=9999, output_folder='output_images'):
        """Khởi tạo Processing Server"""
        self.camera_host = camera_host
        self.camera_port = camera_port
        self.output_folder = output_folder
        self.socket = None
        self.spark_context = None
        self.received_frames = []
        
        # Tạo session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def init_spark(self, app_name="BackgroundRemover-Stream"):
        """Khởi tạo Spark Context"""
        spark_master = os.getenv('SPARK_MASTER_URL', 'local[*]')
        
        conf = SparkConf().setAppName(app_name).setMaster(spark_master)
        conf.set("spark.driver.host", "processing-server")
        conf.set("spark.driver.bindAddress", "0.0.0.0")
        
        self.spark_context = SparkContext.getOrCreate(conf=conf)
        self.spark_context.setLogLevel("ERROR")
        
        # Gửi file dependency đến workers để xử lý phân tán
        self.spark_context.addPyFile("/app/background_remover.py")
        
        print(f"[Processing Server] Spark Context da khoi tao: {spark_master}")
        
    def connect_to_camera(self):
        """Kết nối đến Camera Server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        print(f"[Processing Server] Dang ket noi den Camera Server {self.camera_host}:{self.camera_port}...")
        
        # Retry kết nối
        max_retries = 10
        for i in range(max_retries):
            try:
                self.socket.connect((self.camera_host, self.camera_port))
                print("[Processing Server] Da ket noi thanh cong!")
                return True
            except socket.error:
                print(f"[Processing Server] Thu lai lan {i+1}/{max_retries}...")
                import time
                time.sleep(2)
        
        print("[Processing Server] Khong the ket noi den Camera Server")
        return False
    
    def receive_frame(self):
        """
        Nhận một frame từ Camera Server
        Giải mã gói tin TCP thành frame ảnh
        """
        try:
            # Nhận header (8 bytes): frame_id + data_size
            header = self._recv_exact(8)
            if not header:
                return None, None, None
            
            frame_id, data_size = struct.unpack('!II', header)
            
            # Kiểm tra tín hiệu kết thúc
            if frame_id == 0xFFFFFFFF:
                return None, None, "END"
            
            # Nhận data
            data = self._recv_exact(data_size)
            if not data:
                return None, None, None
            
            # Decode frame
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return frame_id, frame, "OK"
        except Exception as e:
            print(f"[Processing Server] Loi nhan frame: {e}")
            return None, None, None
    
    def _recv_exact(self, size):
        """Nhận chính xác số bytes yêu cầu"""
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def receive_all_frames(self):
        """Nhận tất cả frame từ Camera Server"""
        # Nhận số lượng frame
        num_frames_data = self._recv_exact(4)
        if not num_frames_data:
            return []
        
        num_frames = struct.unpack('!I', num_frames_data)[0]
        print(f"[Processing Server] Se nhan {num_frames} frame")
        
        if num_frames == 0:
            print("[Processing Server] Khong co frame nao de nhan")
            return []
        
        frames = []
        for i in range(num_frames):
            # Nhận tên file
            name_len_data = self._recv_exact(4)
            name_len = struct.unpack('!I', name_len_data)[0]
            filename = self._recv_exact(name_len).decode('utf-8')
            
            # Nhận frame
            frame_id, frame, status = self.receive_frame()
            
            if status == "END":
                break
            
            if frame is not None:
                frames.append((frame_id, frame, filename))
                print(f"[Processing Server] Da nhan frame {frame_id}: {filename}")
        
        print(f"[Processing Server] Tong cong da nhan {len(frames)} frame")
        return frames
    
    def receive_and_process_streaming(self):
        """
        XỬ LÝ STREAMING THỰC SỰ - Đúng yêu cầu đề bài:
        Nhận từng frame → Xử lý ngay với Spark → Lưu kết quả
        Mỗi frame được xử lý trong ngữ cảnh Spark
        """
        # Nhận số lượng frame sẽ được stream
        num_frames_data = self._recv_exact(4)
        if not num_frames_data:
            print("[Processing Server] Khong nhan duoc thong tin so luong frame")
            return []
        
        num_frames = struct.unpack('!I', num_frames_data)[0]
        print(f"[Processing Server - STREAMING MODE] Se xu ly {num_frames} frame theo thoi gian thuc")
        
        if num_frames == 0:
            print("[Processing Server] Khong co frame nao de xu ly")
            return []
        
        # Tạo output folder cho session
        session_output = os.path.join(self.output_folder, self.session_id)
        os.makedirs(session_output, exist_ok=True)
        
        results = []
        
        # XỬ LÝ TỪNG FRAME NGAY KHI NHẬN ĐƯỢC
        for i in range(num_frames):
            # Nhận tên file
            name_len_data = self._recv_exact(4)
            if not name_len_data:
                break
            name_len = struct.unpack('!I', name_len_data)[0]
            filename = self._recv_exact(name_len).decode('utf-8')
            
            # Nhận frame
            frame_id, frame, status = self.receive_frame()
            
            if status == "END":
                print("[Processing Server] Nhan tin hieu ket thuc")
                break
            
            if frame is None:
                print(f"[Processing Server] Frame {frame_id} bi loi")
                continue
            
            print(f"[Processing Server] Nhan frame {frame_id}: {filename}")
            
            # XỬ LÝ NGAY FRAME NÀY VỚI SPARK (không đợi nhận hết)
            result = self._process_single_frame_streaming(frame, frame_id, filename, session_output)
            results.append(result)
            
            print(f"[Processing Server] ✓ Da xu ly xong frame {frame_id} - {result[2]}")
        
        print(f"\n[Processing Server] HOAN THANH! Xu ly {len(results)}/{num_frames} frame")
        return results
    
    def _process_single_frame_streaming(self, frame, frame_id, filename, output_folder):
        """
        Xử lý 1 frame trong streaming mode
        QUAN TRỌNG: Mỗi frame được xử lý TRONG NGỮ CẢNH SPARK
        """
        try:
            # Lưu frame tạm để Spark worker có thể đọc
            temp_folder = f"/tmp/spark_stream_{self.session_id}"
            os.makedirs(temp_folder, exist_ok=True)
            temp_path = os.path.join(temp_folder, filename)
            cv2.imwrite(temp_path, frame)
            
            output_path = os.path.join(output_folder, filename)
            
            # ĐƯA VÀO SPARK CONTEXT - Xử lý từng frame riêng lẻ
            # Tạo RDD với 1 phần tử duy nhất (frame này)
            rdd = self.spark_context.parallelize([(temp_path, output_path, filename)])
            
            # Map operation trên Spark worker
            result = rdd.map(self._process_single_frame).collect()[0]
            
            # Xóa file tạm
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            print(f"[Processing Server] Loi xu ly frame {frame_id}: {e}")
            return (filename, None, f"Error: {str(e)}")
    
    def process_frames_with_spark(self, frames):
        """
        Xử lý xóa nền cho tất cả frame bằng Spark
        Mỗi frame được xử lý song song trên các worker
        """
        if not frames:
            print("[Processing Server] Khong co frame de xu ly")
            return []
        
        # Tạo output folder
        session_output = os.path.join(self.output_folder, self.session_id)
        os.makedirs(session_output, exist_ok=True)
        
        # Lưu tạm các frame để Spark worker có thể đọc
        temp_folder = f"/tmp/spark_frames_{self.session_id}"
        os.makedirs(temp_folder, exist_ok=True)
        
        frame_paths = []
        for frame_id, frame, filename in frames:
            temp_path = os.path.join(temp_folder, filename)
            cv2.imwrite(temp_path, frame)
            output_path = os.path.join(session_output, filename)
            frame_paths.append((temp_path, output_path, filename))
        
        print(f"[Processing Server] Bat dau xu ly {len(frame_paths)} frame voi Spark...")
        
        # Xử lý song song với Spark RDD
        rdd = self.spark_context.parallelize(frame_paths)
        results = rdd.map(self._process_single_frame).collect()
        
        # Xóa temp folder
        import shutil
        shutil.rmtree(temp_folder, ignore_errors=True)
        
        # Thống kê kết quả
        success = sum(1 for r in results if r[2] == "Success")
        print(f"[Processing Server] Hoan thanh! {success}/{len(results)} frame xu ly thanh cong")
        
        return results
    
    @staticmethod
    def _process_single_frame(frame_info):
        """Xử lý một frame - chạy trên Spark worker"""
        input_path, output_path, filename = frame_info
        
        try:
            # Đọc frame
            frame = cv2.imread(input_path)
            if frame is None:
                return (filename, None, "Khong doc duoc frame")
            
            # Chuyển BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Xóa nền
            processed = remove_background(frame_rgb)
            
            # Chuyển RGB -> BGR để lưu
            processed_bgr = cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)
            
            # Lưu kết quả
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, processed_bgr)
            
            return (filename, output_path, "Success")
        except Exception as e:
            return (filename, None, str(e))
    
    def stop(self):
        """Dừng server"""
        if self.socket:
            self.socket.close()
        if self.spark_context:
            self.spark_context.stop()
        print("[Processing Server] Da dung server")


def main():
    parser = argparse.ArgumentParser(description='Processing Server - Receive and process frames')
    parser.add_argument('--camera-host', default='camera-server', help='Camera server host')
    parser.add_argument('--camera-port', type=int, default=9999, help='Camera server port')
    parser.add_argument('--output', default='output_images', help='Output folder')
    parser.add_argument('--mode', choices=['streaming', 'batch'], default='streaming',
                        help='Mode: streaming (xu ly tung frame ngay) hoac batch (nhan het roi xu ly)')
    args = parser.parse_args()
    
    server = ProcessingServer(
        camera_host=args.camera_host,
        camera_port=args.camera_port,
        output_folder=args.output
    )
    
    try:
        # Khởi tạo Spark
        server.init_spark()
        
        # Kết nối đến Camera Server
        if server.connect_to_camera():
            if args.mode == 'streaming':
                print("\n=== CHE DO: STREAMING (Xu ly tung frame ngay khi nhan) ===")
                # XỬ LÝ STREAMING - Đúng yêu cầu đề bài
                results = server.receive_and_process_streaming()
            else:
                print("\n=== CHE DO: BATCH (Nhan het roi xu ly) ===")
                # Nhận tất cả frame
                frames = server.receive_all_frames()
                # Xử lý frame với Spark
                results = server.process_frames_with_spark(frames)
            
            # In kết quả
            print("\n=== KET QUA XU LY ===")
            for filename, output_path, status in results:
                print(f"  {filename}: {status}")
                
    except KeyboardInterrupt:
        print("\n[Processing Server] Dang dung...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
