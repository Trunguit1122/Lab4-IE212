import os
import cv2
import numpy as np
from pyspark import SparkContext, SparkConf
from background_remover import remove_background
from datetime import datetime
import uuid

def process_image(img_info):
    """Xử lý một ảnh - dùng trong Spark map"""
    input_path, output_path = img_info
    
    try:
        # Đọc ảnh
        img = cv2.imread(input_path)
        if img is None:
            return (input_path, None, "Không đọc được ảnh")
        
        # Chuyển BGR sang RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Xóa nền
        processed = remove_background(img_rgb)
        
        # Chuyển về BGR để lưu
        processed_bgr = cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)
        
        # Tạo thư mục output nếu chưa có
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, processed_bgr)
        
        return (input_path, output_path, "Success")
    except Exception as e:
        return (input_path, None, str(e))

class SparkImageProcessor:
    def __init__(self, app_name="BackgroundRemover"):
        """Khởi tạo Spark context"""
        spark_master = os.getenv('SPARK_MASTER_URL', 'local[*]')
        
        conf = SparkConf().setAppName(app_name).setMaster(spark_master)
        conf.set("spark.driver.host", "streamlit-app")
        conf.set("spark.driver.bindAddress", "0.0.0.0")
        
        self.sc = SparkContext.getOrCreate(conf=conf)
        self.sc.setLogLevel("ERROR")
        self.sc.addPyFile("/app/background_remover.py")
        self.sc.addPyFile("/app/spark_processor.py")
    
    def create_session_id(self):
        """Tạo session ID duy nhất"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = str(uuid.uuid4())[:8]
        return f"{ts}_{uid}"
    
    def process_images_batch(self, input_folder, output_folder, session_id):
        # Tạo thư mục session
        session_input = os.path.join(input_folder, session_id)
        session_output = os.path.join(output_folder, session_id)
        
        os.makedirs(session_input, exist_ok=True)
        os.makedirs(session_output, exist_ok=True)
        
        # Lấy danh sách ảnh
        img_files = []
        for fname in os.listdir(session_input):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                inp = os.path.join(session_input, fname)
                out = os.path.join(session_output, fname)
                img_files.append((inp, out))
        
        if not img_files:
            return []
        
        # Xử lý song song với Spark RDD
        rdd = self.sc.parallelize(img_files)
        results = rdd.map(process_image).collect()
        
        return results
    
    def stop(self):
        """Dừng Spark context"""
        if self.sc:
            self.sc.stop()
    
    def get_session_history(self, input_folder, output_folder):
        sessions = []
        
        if not os.path.exists(input_folder):
            return sessions
        
        for sid in os.listdir(input_folder):
            s_path = os.path.join(input_folder, sid)
            if os.path.isdir(s_path):
                # Đếm ảnh input
                input_imgs = [f for f in os.listdir(s_path) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                # Đếm ảnh output
                o_path = os.path.join(output_folder, sid)
                output_imgs = []
                if os.path.exists(o_path):
                    output_imgs = [f for f in os.listdir(o_path) 
                                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                # Lấy timestamp từ session_id
                ts_str = sid.split('_')[0] + '_' + sid.split('_')[1]
                try:
                    ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    time_str = ts.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    time_str = sid
                
                sessions.append({
                    'session_id': sid,
                    'timestamp': time_str,
                    'input_count': len(input_imgs),
                    'output_count': len(output_imgs),
                    'input_path': s_path,
                    'output_path': o_path
                })
        
        sessions.sort(key=lambda x: x['session_id'], reverse=True)
        return sessions
