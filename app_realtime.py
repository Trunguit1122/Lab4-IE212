"""
Real-time Background Remover - NHƯ ZOOM/GOOGLE MEET
Video stream liên tục → Gửi TCP → Spark xử lý → Nhận kết quả → Hiển thị
"""
import streamlit as st
import cv2
import numpy as np
import socket
import struct
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av
import threading

st.set_page_config(
    page_title="Background Remover - Spark Stream",
    page_icon="🎬",
    layout="centered"
)

SPARK_SERVER_HOST = "processing-server"
SPARK_SERVER_PORT = 9998


class SparkBackgroundRemover(VideoProcessorBase):
    """
    Video processor: Mỗi frame gửi đến Spark Server → nhận kết quả → hiển thị
    Giống Zoom/Meet nhưng đi qua Spark!
    """
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.frame_count = 0
        self.lock = threading.Lock()
        self.last_result = None
        
        # Connect to Spark server
        self._connect()
        
    def _connect(self):
        """Connect to Spark Stream Server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((SPARK_SERVER_HOST, SPARK_SERVER_PORT))
            self.connected = True
        except Exception as e:
            pass
            self.connected = False
            
    def _send_receive_frame(self, frame):
        """Send frame to Spark, receive processed result"""
        if not self.connected:
            self._connect()
            if not self.connected:
                return frame
                
        try:
            # Encode frame
            _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_data = encoded.tobytes()
            
            with self.lock:
                # Send: size + data
                self.socket.sendall(struct.pack('!I', len(frame_data)))
                self.socket.sendall(frame_data)
                
                # Receive: size + data
                size_data = self._recv_exact(4)
                if not size_data:
                    return frame
                    
                result_size = struct.unpack('!I', size_data)[0]
                
                if result_size == 0:
                    return frame
                    
                result_data = self._recv_exact(result_size)
                if not result_data:
                    return frame
                
            # Decode result
            nparr = np.frombuffer(result_data, np.uint8)
            result_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return result_frame if result_frame is not None else frame
            
        except Exception as e:
            self.connected = False
            return frame
            
    def _recv_exact(self, size):
        """Receive exact bytes"""
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
        
    def recv(self, frame):
        """Process each video frame - REAL-TIME"""
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        
        # Send to Spark every frame
        processed = self._send_receive_frame(img)
        self.last_result = processed
            
        return av.VideoFrame.from_ndarray(processed, format="bgr24")
        
    def __del__(self):
        """Cleanup"""
        if self.socket:
            try:
                self.socket.sendall(struct.pack('!I', 0))  # Signal end
                self.socket.close()
            except:
                pass


# ========== STREAMLIT UI ==========

st.title("🎬 Background Remover")

# WebRTC Configuration
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Main video stream
ctx = webrtc_streamer(
    key="spark-bg-remover",
    video_processor_factory=SparkBackgroundRemover,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

# Status indicator
if ctx.state.playing:
    st.success("🟢 Đang xử lý video...")
else:
    st.info("⏸️ Nhấn START để bắt đầu")
