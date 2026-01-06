# 🎨 Real-time Background Remover với Apache Spark

<div align="center">

![Demo](gif/Recording%202026-01-06%20204846.gif)

**Hệ thống xóa phông nền video real-time với Apache Spark & MediaPipe**

[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange?style=flat-square&logo=apache-spark)](https://spark.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-AI-4285F4?style=flat-square)](https://google.github.io/mediapipe/)
[![Streamlit](https://img.shields.io/badge/Streamlit-WebRTC-FF4B4B?style=flat-square)](https://streamlit.io/)

</div>

---

## 👨‍💻 Thông Tin Sinh Viên

- **Môn học:** IE212 - Big Data Technologies
- **Sinh viên:** Trần Nguyễn Đức Trung
- **MSSV:** 23521687
- **Lớp:** IE212.P11
- **Học kỳ:** 1, Năm học 2024-2025
- **GitHub:** [Trunguit1122](https://github.com/Trunguit1122)

---

## 📖 Giới Thiệu Đề Tài

### 🎯 Mục Tiêu
Xây dựng hệ thống xử lý video streaming real-time để loại bỏ phông nền, sử dụng:
- **Apache Spark** để xử lý phân tán các frame video
- **MediaPipe** để phân đoạn người và nền
- **Streamlit WebRTC** để capture và hiển thị video từ webcam
- **TCP Socket** để streaming dữ liệu giữa các thành phần

### 🏆 Yêu Cầu Bài Tập
✅ Stream video frames qua **TCP Socket**  
✅ Xử lý frames bằng **Apache Spark RDD**  
✅ Hiển thị kết quả real-time trên **Web UI**  
✅ Deploy hệ thống bằng **Docker Compose**  

### 💡 Ý Tưởng Thực Hiện
Hệ thống gồm 3 thành phần chính:
1. **Streamlit WebRTC Client**: Capture video từ webcam, hiển thị kết quả
2. **TCP Socket Channel**: Stream frames giữa client và server
3. **Spark Processing Server**: Nhận frames, xử lý phân tán với Spark, trả về kết quả

---

## 🏗️ Kiến Trúc Hệ Thống

### Sơ Đồ Tổng Quan

```
┌──────────────────┐
│   Browser        │
│   (Webcam)       │  Streamlit WebRTC
└────────┬─────────┘  Capture Video
         │
         ▼
┌──────────────────┐
│  Streamlit App   │  
│  (Client)        │  Encode frame → JPEG bytes
└────────┬─────────┘
         │ TCP Socket
         │ Port 9998
         │ [Header: frame_id, size | Payload: JPEG data]
         ▼
┌──────────────────┐
│  Spark Stream    │  
│  Server          │  TCP Server
│  (Processing)    │  
│                  │  1. Receive & decode frame
│                  │  2. Create Spark RDD: 
│                  │     sc.parallelize([frame])
│                  │  3. Process with Spark:
│                  │     rdd.map(remove_bg)
│                  │  4. Collect result
│                  │  5. Encode & send back
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Apache Spark    │
│  Cluster         │
│                  │
│  Master + 2      │  MediaPipe Segmentation
│  Workers         │  Background Removal
└──────────────────┘  Parallel Processing
```

### Luồng Xử Lý Chi Tiết

1. 📷 **Webcam** → Streamlit WebRTC capture frame (30fps)
2. 🔄 **Streamlit** → Encode frame thành JPEG bytes
3. 📦 **TCP Client** → Đóng gói packet với header: `[frame_id: 4 bytes][size: 4 bytes][data: N bytes]`
4. 🌐 **TCP Stream** → Gửi qua socket đến Spark Server (port 9998)
5. 📥 **Spark Server** → Nhận và giải mã packet thành numpy array
6. ⚡ **Spark RDD** → `spark_context.parallelize([frame]).map(remove_background).collect()`
7. 🤖 **MediaPipe** → Phân đoạn người/nền, thay nền thành màu xám (192, 192, 192)
8. 📤 **Response** → Encode kết quả thành JPEG, gửi về client qua TCP
9. 🖥️ **Display** → Streamlit nhận và hiển thị frame đã xử lý

---

## 📁 Cấu Trúc Project

```
Lab04-BackgroundRemover/
│
├── 🐍 app_realtime.py           # Streamlit WebRTC interface
├── 🐍 spark_stream_server.py    # TCP Server + Spark processing
├── 🐍 background_remover.py     # MediaPipe segmentation module
├── 🐍 spark_processor.py        # Spark processor helper
│
├── 🐳 docker-compose.yml        # Orchestration: Spark + Services
├── 🐳 Dockerfile                # Build image với Python dependencies
├── 📦 requirements.txt          # Python packages
├── 📘 README.md                 # Documentation
│
├── 📂 models/
│   └── selfie_segmenter.tflite # MediaPipe AI model (segmentation)
│
└── 📂 output_images/            # Saved processed frames
```

**Core Files:**
- `app_realtime.py`: Giao diện Streamlit với WebRTC, TCP client để gửi/nhận frames
- `spark_stream_server.py`: TCP server nhận frames, xử lý bằng Spark RDD, trả về kết quả
- `background_remover.py`: Module AI xóa nền với MediaPipe Selfie Segmentation
- `docker-compose.yml`: Deploy Spark cluster (1 master + 2 workers) + application

---

## 🚀 Hướng Dẫn Chạy Hệ Thống

### Yêu Cầu

- **Docker** và **Docker Compose** đã cài đặt
- **4GB RAM** trở lên (cho Spark cluster)
- **Webcam** để test real-time
- **Ports** khả dụng: 7077, 8080, 8501, 9998

### Cài Đặt & Chạy

#### Bước 1: Clone Repository

```bash
git clone https://github.com/Trunguit1122/Lab4-IE212.git
cd Lab4-IE212
```

#### Bước 2: Khởi động hệ thống

```bash
# Build và start tất cả services
docker-compose up -d --build

# Hệ thống sẽ tự động khởi động:
# - Spark Master (port 7077, 8080)
# - Spark Worker 1 & 2
# - Spark Stream Server (port 9998)
# - Streamlit App (port 8501)
```

#### Bước 3: Truy cập giao diện

```bash
# Mở Streamlit Web UI
http://localhost:8501

# Mở Spark Master UI (theo dõi jobs)
http://localhost:8080
```

#### Bước 4: Sử dụng

1. Truy cập `http://localhost:8501`
2. Cho phép trình duyệt truy cập webcam
3. Nhấn **START** để bắt đầu xử lý
4. Video sẽ hiển thị với nền đã được thay thế màu xám

### Kiểm Tra Logs

```bash
# Xem log Spark Stream Server
docker logs -f processing-background-remover

# Xem log Streamlit App
docker logs -f streamlit-background-remover

# Xem log Spark Master
docker logs -f spark-master
```

### Dừng Hệ Thống

```bash
# Stop tất cả containers
docker-compose down

# Stop và xóa volumes
docker-compose down -v
```

---

## 🔧 Chi Tiết Kỹ Thuật

### 1️⃣ Streamlit WebRTC Client (`app_realtime.py`)

**Công nghệ:**
- `streamlit-webrtc` để capture video từ webcam
- `av` (PyAV) để xử lý video frames
- Custom `VideoProcessor` kế thừa `VideoProcessorBase`

**Workflow:**
```python
class SparkBackgroundRemover(VideoProcessorBase):
    def recv(self, frame):
        # 1. Convert WebRTC frame → numpy array
        img = frame.to_ndarray(format="bgr24")
        
        # 2. Encode → JPEG bytes
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # 3. Send via TCP to Spark Server
        processed = self._send_to_spark_server(buffer.tobytes())
        
        # 4. Decode response & display
        return av.VideoFrame.from_ndarray(processed, format="bgr24")
```

**TCP Protocol:**
```python
# Client gửi:
struct.pack('!I', frame_id)    # 4 bytes: ID
struct.pack('!I', len(data))   # 4 bytes: size
data                            # N bytes: JPEG payload
```

### 2️⃣ Spark Stream Server (`spark_stream_server.py`)

**Chức năng chính:**
- TCP Server lắng nghe trên port 9998
- Nhận frames từ client, giải mã thành numpy array
- Sử dụng Spark RDD để xử lý phân tán
- Trả kết quả về client

**Spark Processing:**
```python
# Khởi tạo Spark Context
conf = SparkConf().setAppName("BackgroundRemover") \
                  .setMaster("spark://spark-master:7077")
sc = SparkContext(conf=conf)

# Xử lý frame
def process_frame(frame_data):
    # 1. Create RDD từ frame
    rdd = sc.parallelize([frame_data])
    
    # 2. Map với background removal function
    results = rdd.map(lambda x: remove_background(x)).collect()
    
    # 3. Return processed frame
    return results[0]
```

**TCP Server:**
```python
def handle_client(conn):
    while True:
        # 1. Receive header (frame_id + size)
        header = conn.recv(8)
        frame_id, size = struct.unpack('!II', header)
        
        # 2. Receive payload (JPEG data)
        data = b''
        while len(data) < size:
            packet = conn.recv(min(8192, size - len(data)))
            data += packet
        
        # 3. Decode → numpy array
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        
        # 4. Process with Spark
        processed = process_frame(frame)
        
        # 5. Encode & send back
        _, buffer = cv2.imencode('.jpg', processed)
        response = struct.pack('!I', len(buffer)) + buffer.tobytes()
        conn.sendall(response)
```

### 3️⃣ Background Remover (`background_remover.py`)

**Công nghệ:**
- **MediaPipe Selfie Segmentation** (Google Research)
- Model: `selfie_segmenter.tflite` (pretrained)
- Output: Segmentation mask (person vs background)

**Algorithm:**
```python
def remove_background(image, bg_color=(192, 192, 192)):
    # 1. MediaPipe segmentation
    results = segmenter.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    mask = results.segmentation_mask
    
    # 2. Threshold mask (person > 0.2)
    condition = mask > 0.2
    
    # 3. Create background color image
    bg_image = np.full(image.shape, bg_color, dtype=np.uint8)
    
    # 4. Composite: person = original, background = gray
    output = np.where(condition[:, :, np.newaxis], image, bg_image)
    
    return output
```

**Note:** Code gốc của giảng viên có logic đảo ngược (person→gray, bg→original), nên trong `spark_stream_server.py` có invert lại với NOT operator để đúng yêu cầu.

---

## 📊 Services & Containers

| Service | Container Name | Image | Port | Resource |
|---------|---------------|-------|------|----------|
| **Spark Master** | spark-master | bitnami/spark:3.5.0 | 7077, 8080 | 1GB RAM |
| **Spark Worker 1** | spark-worker-1 | Custom Dockerfile | - | 2 cores, 2GB |
| **Spark Worker 2** | spark-worker-2 | Custom Dockerfile | - | 2 cores, 2GB |
| **Processing Server** | processing-background-remover | Custom Dockerfile | 9998 | 2GB RAM |
| **Streamlit App** | streamlit-background-remover | Custom Dockerfile | 8501 | 1GB RAM |

**Docker Compose Configuration:**
```yaml
services:
  spark-master:
    image: bitnami/spark:3.5.0
    ports: ["8080:8080", "7077:7077"]
    environment:
      - SPARK_MODE=master
    restart: unless-stopped

  spark-worker-1:
    build: .
    command: /opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
    environment:
      - SPARK_WORKER_CORES=2
      - SPARK_WORKER_MEMORY=2g
      - MEDIAPIPE_DISABLE_GPU=1
    restart: unless-stopped

  processing-server:
    build: .
    command: python spark_stream_server.py
    ports: ["9998:9998"]
    depends_on: [spark-master, spark-worker-1, spark-worker-2]
    restart: unless-stopped

  streamlit-app:
    build: .
    command: streamlit run app_realtime.py --server.port=8501
    ports: ["8501:8501"]
    depends_on: [processing-server]
    restart: unless-stopped
```

---

## ⚡ Performance & Scalability

### Thông Số Đo Được

- **Throughput:** ~15-20 frames/second với 2 workers
- **Latency:** ~50-100ms/frame (bao gồm network + processing)
- **GPU:** Disable (CPU-only với `MEDIAPIPE_DISABLE_GPU=1`)

### Khả Năng Mở Rộng

**Tăng số workers:**
```yaml
# Thêm vào docker-compose.yml
spark-worker-3:
  build: .
  command: /opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
  environment:
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=2g
    - MEDIAPIPE_DISABLE_GPU=1
  restart: unless-stopped
```

**Tăng resource cho worker:**
```yaml
environment:
  - SPARK_WORKER_CORES=4      # Tăng cores
  - SPARK_WORKER_MEMORY=4g    # Tăng RAM
```

---

## 🎓 Kiến Thức Áp Dụng

### Big Data Concepts

✅ **Streaming Data Processing**
- TCP Socket streaming giữa các components
- Real-time data pipeline (capture → process → display)

✅ **Distributed Computing với Apache Spark**
- Spark RDD (Resilient Distributed Dataset)
- Transformation: `parallelize()`, `map()`
- Action: `collect()`
- Cluster mode: Master + Multiple Workers

✅ **Fault Tolerance**
- Docker restart policies: `unless-stopped`
- Spark automatic task retry khi worker fail

✅ **Scalability**
- Horizontal scaling: Thêm workers để tăng throughput
- Load balancing: Spark tự động phân phối tasks

### Technologies Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit WebRTC | Video capture & display |
| **Communication** | TCP Socket | Frame streaming protocol |
| **Processing** | Apache Spark | Distributed computing |
| **AI/ML** | MediaPipe | Selfie segmentation |
| **Container** | Docker Compose | Orchestration & deployment |
| **Language** | Python 3.9+ | Application runtime |

---

## 🐛 Troubleshooting

### Container không start

```bash
# Xem logs chi tiết
docker-compose logs -f

# Restart specific service
docker-compose restart processing-server
```

### Port đã được sử dụng

```bash
# Kiểm tra port
sudo lsof -i :8501
sudo lsof -i :9998

# Kill process cũ
sudo kill -9 <PID>

# Hoặc thay đổi port trong docker-compose.yml
```

### Connection refused

```bash
# Đảm bảo processing server đã chạy
docker ps | grep processing

# Check network connectivity giữa containers
docker exec streamlit-background-remover ping processing-server
```

### Webcam không hoạt động

- Đảm bảo browser hỗ trợ WebRTC (Chrome, Firefox)
- Cho phép quyền truy cập webcam
- Kiểm tra webcam đang được sử dụng bởi app khác

### Frame rate thấp

```bash
# Giảm JPEG quality trong app_realtime.py
cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])  # Từ 85 → 70

# Hoặc tăng số workers
docker-compose scale spark-worker=4
```

---

## 📚 Tài Liệu Tham Khảo

1. **Apache Spark**
   - [Spark RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html)
   - [Spark Cluster Mode Overview](https://spark.apache.org/docs/latest/cluster-overview.html)

2. **MediaPipe**
   - [Selfie Segmentation Guide](https://google.github.io/mediapipe/solutions/selfie_segmentation.html)
   - [MediaPipe Python API](https://google.github.io/mediapipe/getting_started/python.html)

3. **Streamlit WebRTC**
   - [streamlit-webrtc Documentation](https://github.com/whitphx/streamlit-webrtc)
   - [WebRTC Best Practices](https://webrtc.org/getting-started/overview)

4. **Docker**
   - [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
   - [Docker Networking](https://docs.docker.com/network/)

---

## 🎯 Kết Luận

### Thành Quả Đạt Được

✅ Xây dựng thành công hệ thống streaming real-time với TCP Socket  
✅ Tích hợp Apache Spark để xử lý phân tán video frames  
✅ Áp dụng AI (MediaPipe) vào Big Data pipeline  
✅ Deploy hoàn chỉnh với Docker Compose  
✅ Đạt yêu cầu bài tập: Stream + Spark + Real-time display  

### Bài Học Kinh Nghiệm

- **Network Protocol Design**: Thiết kế TCP protocol với header/payload chuẩn
- **Spark RDD**: Hiểu cách hoạt động của RDD transformation & action
- **Containerization**: Quản lý multi-container system với Docker Compose
- **Real-time Processing**: Xử lý latency và throughput trong streaming system



---

<div align="center">

**Made with ❤️ by Trần Nguyễn Đức Trung**

*IE212 - Big Data Technologies - UIT 2024-2025*

---

📧 **Contact:** 23521687@gm.uit.edu.vn  
🔗 **GitHub:** [Trunguit1122](https://github.com/Trunguit1122)

</div>
