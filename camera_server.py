"""
Camera Server - Giả lập server camera
Sử dụng webcam để chụp hình ảnh trực tiếp, chuyển thành các gói tin và gửi đến server xử lý qua TCP Socket
"""
import socket
import struct
import cv2
import numpy as np
import os
import time
import argparse

class CameraServer:
    def __init__(self, host='0.0.0.0', port=9999):
        """Khởi tạo Camera Server"""
        self.host = host
        self.port = port
        self.socket = None
        self.client_socket = None
        self.camera = None
        
    def start(self):
        """Khởi động server và chờ kết nối từ Processing Server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[Camera Server] Dang cho ket noi tai {self.host}:{self.port}...")
        
        self.client_socket, addr = self.socket.accept()
        print(f"[Camera Server] Da ket noi voi Processing Server: {addr}")
        return True
    
    def init_camera(self, camera_id=0):
        """Khởi tạo webcam"""
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            print("[Camera Server] Khong the mo webcam!")
            return False
        print(f"[Camera Server] Da mo webcam {camera_id}")
        return True
    
    def capture_frame(self):
        """Chụp một frame từ webcam"""
        if self.camera is None:
            return None
        ret, frame = self.camera.read()
        if ret:
            return frame
        return None
    
    def send_frame(self, frame, frame_id, filename="frame"):
        """
        Gửi một frame ảnh đến Processing Server
        Đóng gói frame thành các gói tin TCP
        """
        try:
            # Encode frame thành bytes (JPEG để giảm kích thước)
            _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            data = encoded.tobytes()
            
            # Gửi tên file trước
            fname = f"{filename}_{frame_id}.jpg"
            filename_bytes = fname.encode('utf-8')
            self.client_socket.sendall(struct.pack('!I', len(filename_bytes)))
            self.client_socket.sendall(filename_bytes)
            
            # Tạo header: frame_id (4 bytes) + data_size (4 bytes)
            header = struct.pack('!II', frame_id, len(data))
            
            # Gửi header
            self.client_socket.sendall(header)
            
            # Gửi data
            self.client_socket.sendall(data)
            
            print(f"[Camera Server] Da gui frame {frame_id} ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"[Camera Server] Loi gui frame: {e}")
            return False
    
    def stream_from_camera(self, num_frames=10, delay=0.5):
        """
        Chụp và stream các frame từ webcam trực tiếp
        """
        if not self.init_camera():
            # Gửi số lượng = 0 nếu không mở được camera
            self.client_socket.sendall(struct.pack('!I', 0))
            return 0
        
        print(f"[Camera Server] Bat dau chup {num_frames} frame tu webcam...")
        
        # Gửi số lượng frame trước
        self.client_socket.sendall(struct.pack('!I', num_frames))
        
        # Chụp và gửi từng frame
        sent_count = 0
        for i in range(num_frames):
            frame = self.capture_frame()
            
            if frame is not None:
                self.send_frame(frame, i, "camera_frame")
                sent_count += 1
                time.sleep(delay)  # Delay giữa các frame
            else:
                print(f"[Camera Server] Khong chup duoc frame {i}")
        
        # Đóng camera
        self.camera.release()
        print(f"[Camera Server] Da gui xong {sent_count} frame")
        return sent_count
    
    def send_images_from_folder(self, folder_path, delay=0.5):
        """
        Đọc tất cả ảnh từ folder và gửi như các frame
        (Backup mode khi không có webcam)
        """
        if not os.path.exists(folder_path):
            print(f"[Camera Server] Khong tim thay folder: {folder_path}")
            self.client_socket.sendall(struct.pack('!I', 0))
            return 0
        
        # Lấy danh sách file ảnh
        image_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        image_files.sort()
        
        if not image_files:
            print("[Camera Server] Khong co file anh nao trong folder")
            self.client_socket.sendall(struct.pack('!I', 0))
            return 0
        
        print(f"[Camera Server] Tim thay {len(image_files)} anh, bat dau streaming...")
        
        # Gửi số lượng frame
        self.client_socket.sendall(struct.pack('!I', len(image_files)))
        
        # Gửi từng frame
        for idx, filename in enumerate(image_files):
            filepath = os.path.join(folder_path, filename)
            frame = cv2.imread(filepath)
            
            if frame is not None:
                # Gửi tên file
                filename_bytes = filename.encode('utf-8')
                self.client_socket.sendall(struct.pack('!I', len(filename_bytes)))
                self.client_socket.sendall(filename_bytes)
                
                # Gửi frame
                _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                data = encoded.tobytes()
                header = struct.pack('!II', idx, len(data))
                self.client_socket.sendall(header)
                self.client_socket.sendall(data)
                
                print(f"[Camera Server] Da gui frame {idx}: {filename} ({len(data)} bytes)")
                time.sleep(delay)
            else:
                print(f"[Camera Server] Khong doc duoc anh: {filename}")
        
        print(f"[Camera Server] Da gui xong {len(image_files)} frame")
        return len(image_files)
    
    def stop(self):
        """Dừng server"""
        if self.camera:
            self.camera.release()
        if self.client_socket:
            self.client_socket.close()
        if self.socket:
            self.socket.close()
        print("[Camera Server] Da dung server")


def main():
    parser = argparse.ArgumentParser(description='Camera Server - Stream từ webcam hoặc folder')
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=9999, help='Port number')
    parser.add_argument('--mode', choices=['camera', 'folder'], default='camera', 
                        help='Chế độ: camera (webcam) hoặc folder (đọc từ file)')
    parser.add_argument('--input', default='input_images', help='Input folder (mode=folder)')
    parser.add_argument('--frames', type=int, default=10, help='Số frame chụp (mode=camera)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay giữa các frame')
    args = parser.parse_args()
    
    server = CameraServer(host=args.host, port=args.port)
    
    try:
        if server.start():
            if args.mode == 'camera':
                # Chụp từ webcam trực tiếp
                server.stream_from_camera(num_frames=args.frames, delay=args.delay)
            else:
                # Đọc từ folder (backup)
                server.send_images_from_folder(args.input, delay=args.delay)
    except KeyboardInterrupt:
        print("\n[Camera Server] Dang dung...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
