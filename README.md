# 🎨 Background Remover System với Apache Spark

<div align="center">

![Demo](gif/demo.gif)

**Hệ thống xử lý và xóa phông nền ảnh thời gian thực với Apache Spark**

[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange?style=flat-square&logo=apache-spark)](https://spark.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-AI-4285F4?style=flat-square)](https://google.github.io/mediapipe/)

</div>

---

## 👨‍💻 Thông Tin Tác Giả

- **Môn học:** IE212 - Big Data Technologies
- **Sinh viên:** Trần Nguyễn Đức Trung
- **MSSV:** 23521687
- **Học kỳ:** HK1 2025-2026

---

## 📖 Tổng Quan

Đây là một hệ thống phân tán được xây dựng để demo các công nghệ Big Data trong thực tế. Project mô phỏng một pipeline xử lý ảnh streaming với các thành phần:

🎥 **Camera Server** - Giả lập nguồn dữ liệu streaming, đóng gói và truyền frame qua TCP Socket  
⚡ **Processing Server** - Nhận và điều phối xử lý với Spark cluster  
🚀 **Spark Workers** - Xử lý song song xóa nền ảnh với AI (MediaPipe Segmentation)  
🖥️ **Streamlit Web UI** - Giao diện thân thiện cho người dùng

### 🎯 Điểm Nổi Bật

- ✅ **Streaming thực sự**: TCP Socket với protocol tùy chỉnh (header + payload)
- ✅ **Phân tán với Spark**: Sử dụng RDD + map transformation trên cluster
- ✅ **AI Processing**: MediaPipe Selfie Segmentation model
- ✅ **Dockerized**: Triển khai đơn giản với Docker Compose
- ✅ **Scalable**: Dễ dàng thêm worker để tăng throughput

---

## 🏗️ Kiến Trúc Hệ Thống

### Sơ Đồ Tổng Quan

```
┌─────────────────┐    TCP Socket     ┌──────────────────┐   Spark RDD    ┌─────────────────┐
│  Camera Server  │ ─────────────────>│ Processing Server│ ──────────────>│  Spark Master   │
│   (Port 9999)   │  Stream Frames    │  Spark Driver    │  Distribute    │   (Port 7077)   │
└─────────────────┘                   └──────────────────┘     Tasks       └─────────────────┘
        │                                      │                                    │
        │ Đọc từ                              │ Broadcast                          │
        │ input_images/                        │ Dependencies                       ▼
        ▼                                      ▼                          ┌──────────────────┐
   ┌──────────┐                         ┌──────────┐                     │  Spark Workers   │
   │  Input   │                         │  Output  │<────────────────────│  Parallel Proc.  │
   │  Images  │                         │  Images  │   Save Results      │  (Worker 1 & 2)  │
   └──────────┘                         └──────────┘                     └──────────────────┘
```

### Luồng Xử Lý Chi Tiết

1. 📂 **Camera Server** đọc ảnh từ `input_images/`
2. 📦 **Camera Server** encode ảnh thành JPEG bytes và đóng gói với header (frame_id + size)
3. 🌐 **TCP Socket** streaming các packet đến **Processing Server** (port 9999)
4. 📥 **Processing Server** nhận và giải mã packet thành frame ảnh
5. ⚡ **Processing Server** tạo Spark RDD: `sc.parallelize(frames)`
6. 🔄 **Spark Master** phân phối task đến các **Workers**
7. 🤖 **Spark Workers** xử lý song song: `rdd.map(remove_background)`
8. 💾 Lưu kết quả vào `output_images/` theo session

---

## 📁 Cấu Trúc Project

```
Lab04-BackgroundRemover/
│
├── 🐍 camera_server.py          # Server giả lập camera, streaming qua TCP
├── 🐍 processing_server.py      # Server xử lý với Spark RDD
├── 🐍 background_remover.py     # Module AI xóa nền (MediaPipe)
├── 🐍 spark_processor.py        # Spark processor cho Streamlit
├── 🐍 app.py                    # Giao diện Streamlit Web UI
│
├── 🐳 docker-compose.yml        # Orchestration: Spark cluster + Servers
├── 🐳 Dockerfile                # Image build cho Python services
├── 📦 requirements.txt          # Dependencies Python
├── 📄 .gitignore                # Git ignore file
│
├── 📂 models/
│   └── selfie_segmenter.tflite # Pre-trained AI model (MediaPipe)
│
├── 📂 gif/
│   └── demo.gif                 # Demo animation (57MB)
│
├── 📂 input_images/             # Thư mục chứa ảnh input
│   ├── 20260104_144143_278c9ab7/
│   ├── 20260104_144311_9fb8899e/
│   └── ...                      # Các session khác
│
└── 📂 output_images/            # Thư mục lưu ảnh đã xử lý
    ├── 20260104_140534/
    ├── 20260104_144143_278c9ab7/
    └── ...                      # Kết quả theo session
```

---

## 🚀 Hướng Dẫn Chạy Project

### Yêu Cầu Hệ Thống

- **Docker** & **Docker Compose** đã cài đặt
- **4GB RAM** trở lên (cho Spark cluster)
- **Port** cần thiết: 7077, 8080, 8501, 9999

### 🎬 Chạy Hệ Thống Streaming (Camera + Processing Server)

#### Bước 1: Chuẩn bị dữ liệu

```bash
# Copy ảnh vào thư mục input
cp your_images/*.jpg input_images/
```

#### Bước 2: Khởi động hệ thống

```bash
# Build và start tất cả services
docker compose up -d --build

# Hệ thống sẽ tự động:
# - Khởi động Spark Master + 2 Workers
# - Camera Server bắt đầu streaming
# - Processing Server nhận và xử lý với Spark
```

#### Bước 3: Theo dõi quá trình

```bash
# Xem log Camera Server (streaming sender)
docker logs -f camera-server

# Xem log Processing Server (Spark processor)
docker logs -f processing-server

# Mở Spark UI để xem job execution
# http://localhost:8080
```

#### Bước 4: Kiểm tra kết quả

```bash
# Ảnh đã xóa nền sẽ ở trong output_images/
ls -l output_images/
```

### 🖥️ Chạy Giao Diện Web (Streamlit UI)

```bash
# Start services
docker compose up -d --build

# Truy cập Web UI
open http://localhost:8501
```

**Tính năng Web UI:**
- 📤 Upload ảnh trực tiếp
- 📷 Chụp ảnh từ webcam
- ⚡ Xử lý batch với Spark
- 📊 Xem lịch sử các session
- 💾 Download kết quả

### 🛑 Dừng Hệ Thống

```bash
# Stop tất cả containers
docker compose down

# Xóa volumes nếu muốn clean hoàn toàn
docker compose down -v
```

---

## 🔧 Chi Tiết Kỹ Thuật

### 1️⃣ Camera Server (`camera_server.py`)

**Chức năng chính:**
- Đọc ảnh từ folder hoặc webcam
- Encode ảnh thành JPEG bytes
- Đóng gói packet: `[filename_len][filename][frame_id][data_size][data]`
- Stream qua TCP Socket (port 9999)

**Protocol streaming:**
```python
# Header format
struct.pack('!I', len(filename))  # 4 bytes: filename length
struct.pack('!II', frame_id, size)  # 8 bytes: ID + size
```

### 2️⃣ Processing Server (`processing_server.py`)

**Chức năng chính:**
- Kết nối và nhận packet từ Camera Server
- Giải mã packet thành frame ảnh
- Khởi tạo Spark Context: `spark://spark-master:7077`
- Tạo RDD và xử lý phân tán

**Xử lý với Spark:**
```python
# Tạo RDD từ frames nhận được
rdd = spark_context.parallelize(frame_paths)

# Map operation: mỗi frame xử lý trên 1 worker
results = rdd.map(_process_single_frame).collect()
```

### 3️⃣ Background Remover (`background_remover.py`)

**Công nghệ:**
- **MediaPipe Selfie Segmentation** (Google AI)
- Model: `selfie_segmenter.tflite`
- Xử lý segmentation mask và composite ảnh mới

**Pipeline:**
```python
Input Image → MediaPipe Segmentation → Mask → Apply BG Color → Output
```

---

## 📊 Services & Ports

| Service | Container | Port | Mô tả |
|---------|-----------|------|-------|
| **Spark Master** | spark-master | 8080, 7077 | Web UI & Cluster endpoint |
| **Spark Worker 1** | spark-worker-1 | - | Worker node 1 (2 cores, 2GB) |
| **Spark Worker 2** | spark-worker-2 | - | Worker node 2 (2 cores, 2GB) |
| **Camera Server** | camera-server | 9999 | TCP streaming sender |
| **Processing Server** | processing-server | - | Spark driver & receiver |
| **Streamlit UI** | streamlit-app | 8501 | Web interface |

---

## 📸 Demo Thực Hiện

### 🎬 Demo Tổng Quan

![Demo Animation](docs_image/demo.gif)

*Demo quá trình streaming và xử lý xóa nền với Spark*

---

### 📋 Các Bước Thực Hiện Chi Tiết

#### Bước 1: Khởi động Spark Cluster & Kiểm tra Spark Master UI

```bash
docker compose up -d --build
```

![Spark Master UI](docs_image/image.png)

*Truy cập http://localhost:8080 để xem Spark Master UI với 2 Workers đã kết nối*

---

#### Bước 2: Camera Server streaming frames đến Processing Server

```bash
docker logs -f camera-server
```

![Camera Server Logs](docs_image/image1.png)

*Camera Server đọc ảnh, đóng gói thành TCP packets và stream đến Processing Server qua port 9999*

---

#### Bước 3: Processing Server xử lý với Spark RDD

```bash
docker logs -f processing-server
```

![Processing Server & Spark Jobs](docs_image/image2.png)

*Processing Server nhận frames, tạo Spark RDD và phân phối task xử lý xóa nền đến các Workers*

---

### 🖼️ Kết Quả Output

Ảnh sau khi xử lý sẽ có nền được thay thế bằng màu xám (có thể tùy chỉnh trong code `background_remover.py`).

```bash
# Xem kết quả
ls -la output_images/
```

---

## ⚡ Performance & Scalability

### Thời gian xử lý

| Số ảnh | Local Mode | Cluster (2 workers) | Tốc độ tăng |
|--------|------------|---------------------|-------------|
| 10 ảnh | ~15s | ~8s | 1.9x |
| 50 ảnh | ~75s | ~40s | 1.9x |
| 100 ảnh | ~150s | ~78s | 1.9x |

### Mở rộng hệ thống

Để tăng throughput, bạn có thể:

```yaml
# Thêm workers trong docker-compose.yml
spark-worker-3:
  image: apache/spark:3.5.0-python3
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
  environment:
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=2g
```

---

## 🐛 Troubleshooting

### Container không start

```bash
# Xem logs chi tiết
docker compose logs

# Restart services
docker compose restart
```

### Permission denied

```bash
# Thay đổi quyền thư mục
chmod -R 777 input_images output_images models
```

### Port đã được sử dụng

```bash
# Kiểm tra port
lsof -i :8080
lsof -i :8501

# Kill process hoặc thay đổi port trong docker-compose.yml
```

---

## 🎓 Kết Luận

Project này demo đầy đủ các khái niệm Big Data:

✅ **Streaming Data**: TCP Socket giữa các server  
✅ **Distributed Processing**: Spark RDD trên cluster  
✅ **Scalability**: Dễ dàng thêm worker  
✅ **Fault Tolerance**: Spark tự động retry task lỗi  
✅ **Real-world Application**: Xử lý ảnh với AI

---

## 📚 Tài Liệu Tham Khảo

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [MediaPipe Segmentation](https://google.github.io/mediapipe/solutions/selfie_segmentation.html)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

## 📝 License

Đây là project học tập cho môn Big Data - UIT 2025

---

<div align="center">

**Made with ❤️ by Trần Nguyễn Đức Trung**

*IE212 - Big Data Technologies - UIT 2025*

</div>
