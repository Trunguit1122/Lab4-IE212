"""
Spark Stream Server
"""
import socket
import struct
import cv2
import numpy as np
import os
import threading
from pyspark import SparkContext, SparkConf

class SparkStreamServer:
    def __init__(self, host="0.0.0.0", port=9998):
        self.host = host
        self.port = port
        self.server_socket = None
        self.spark_context = None
        self.running = True
        
    def init_spark(self):
        spark_master = os.getenv("SPARK_MASTER_URL", "local[*]")
        conf = SparkConf().setAppName("SparkStreamServer").setMaster(spark_master)
        conf.set("spark.driver.host", "processing-server")
        conf.set("spark.driver.bindAddress", "0.0.0.0")
        self.spark_context = SparkContext.getOrCreate(conf=conf)
        self.spark_context.setLogLevel("ERROR")
        self.spark_context.addPyFile("/app/background_remover.py")
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                thread.daemon = True
                thread.start()
            except:
                pass
                    
    def handle_client(self, client_socket, address):
        try:
            while True:
                size_data = self._recv_exact(client_socket, 4)
                if not size_data:
                    break
                frame_size = struct.unpack("!I", size_data)[0]
                if frame_size == 0:
                    break
                frame_data = self._recv_exact(client_socket, frame_size)
                if not frame_data:
                    break
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    client_socket.sendall(struct.pack("!I", 0))
                    continue
                processed_frame = self.process_frame_spark(frame)
                _, encoded = cv2.imencode(".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                result_data = encoded.tobytes()
                client_socket.sendall(struct.pack("!I", len(result_data)))
                client_socket.sendall(result_data)
        except:
            pass
        finally:
            client_socket.close()
            
    def _recv_exact(self, sock, size):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
        
    def process_frame_spark(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self._process_single_local(frame_rgb)
            result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            return result_bgr
        except:
            return frame
    
    def _process_single_local(self, frame_rgb):
        try:
            from background_remover import remove_background, BG_COLOR
            processed = remove_background(frame_rgb)
            bg_color_array = np.array(BG_COLOR, dtype=np.uint8)
            is_bg_color = np.all(processed == bg_color_array, axis=-1)
            result = np.where(~is_bg_color[:,:,np.newaxis], frame_rgb, bg_color_array)
            return result
        except:
            return frame_rgb
            
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.spark_context:
            self.spark_context.stop()

def main():
    server = SparkStreamServer(host="0.0.0.0", port=9998)
    try:
        server.init_spark()
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    main()

