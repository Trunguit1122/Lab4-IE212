import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import zipfile
import os
import shutil
from spark_processor import SparkImageProcessor

st.set_page_config(
    page_title="Lab04 - BgRemover",
    layout="wide"
)

@st.cache_resource
def get_spark_processor():
    return SparkImageProcessor()

spark_processor = get_spark_processor()

INPUT_FOLDER = "input_images"
OUTPUT_FOLDER = "output_images"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Header
st.title("Lab04 - BgRemover")
st.markdown("---")

# Session state
if 'processed_images' not in st.session_state:
    st.session_state.processed_images = []
if 'original_images' not in st.session_state:
    st.session_state.original_images = []
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'processing_results' not in st.session_state:
    st.session_state.processing_results = None
if 'camera_images' not in st.session_state:
    st.session_state.camera_images = []

# Clear button
col_title, col_clear = st.columns([4, 1])
with col_title:
    st.subheader("1. Chon Nguon Anh")
with col_clear:
    st.write("")
    if st.button("Clear All", type="secondary"):
        st.session_state.processed_images = []
        st.session_state.original_images = []
        st.session_state.selected_images = []
        st.session_state.current_session_id = None
        st.session_state.processing_results = None
        st.session_state.camera_images = []
        st.rerun()

# Tab để chọn nguồn ảnh
tab_upload, tab_camera = st.tabs(["📁 Upload File", "📷 Chup Tu Webcam"])

uploaded_files = []

with tab_upload:
    uploaded_files = st.file_uploader(
        "Chon cac file anh",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    if uploaded_files:
        st.info(f"Da chon {len(uploaded_files)} anh tu file")

with tab_camera:
    st.write("**Chup anh truc tiep tu webcam:**")
    
    # Camera input - chụp ảnh live
    camera_image = st.camera_input("Chup anh")
    
    if camera_image is not None:
        # Thêm ảnh vào danh sách
        if st.button("➕ Them anh vua chup", type="primary"):
            # Đọc ảnh từ camera
            img_bytes = camera_image.getvalue()
            img = Image.open(io.BytesIO(img_bytes))
            
            # Tạo tên file với timestamp
            import time
            filename = f"camera_{int(time.time())}.jpg"
            
            st.session_state.camera_images.append({
                'name': filename,
                'data': img_bytes,
                'image': img
            })
            st.success(f"Da them anh: {filename}")
            st.rerun()
    
    # Hiển thị ảnh đã chụp
    if st.session_state.camera_images:
        st.write(f"**Danh sach anh da chup ({len(st.session_state.camera_images)} anh):**")
        
        cols = st.columns(4)
        for idx, cam_img in enumerate(st.session_state.camera_images):
            with cols[idx % 4]:
                st.image(cam_img['image'], caption=cam_img['name'], width=150)
                if st.button(f"🗑️ Xoa", key=f"del_cam_{idx}"):
                    st.session_state.camera_images.pop(idx)
                    st.rerun()
        
        if st.button("🗑️ Xoa tat ca anh da chup"):
            st.session_state.camera_images = []
            st.rerun()

# Tổng hợp tất cả ảnh (upload + camera)
all_images = []
if uploaded_files:
    for f in uploaded_files:
        all_images.append(('file', f))
if st.session_state.camera_images:
    for cam_img in st.session_state.camera_images:
        all_images.append(('camera', cam_img))

if all_images:
    st.markdown("---")
    st.info(f"Tong cong: {len(all_images)} anh (Upload: {len(uploaded_files) if uploaded_files else 0}, Camera: {len(st.session_state.camera_images)})")
    
    # Xu ly
    st.markdown("###")
    st.subheader("2. Xu Ly")
    if st.button("🚀 Bat Dau Xu Ly", type="primary"):
        # Tao session moi
        session_id = spark_processor.create_session_id()
        st.session_state.current_session_id = session_id
        
        # Tao thu muc session
        session_input_folder = os.path.join(INPUT_FOLDER, session_id)
        os.makedirs(session_input_folder, exist_ok=True)
        
        # Luu cac file
        status_text = st.empty()
        status_text.text("Dang luu anh...")
        
        for img_type, img_data in all_images:
            if img_type == 'file':
                # Upload file
                file_path = os.path.join(session_input_folder, img_data.name)
                with open(file_path, 'wb') as f:
                    f.write(img_data.getbuffer())
            else:
                # Camera image
                file_path = os.path.join(session_input_folder, img_data['name'])
                with open(file_path, 'wb') as f:
                    f.write(img_data['data'])
        
        # Xu ly voi Spark
        status_text.text("Dang xu ly voi Spark...")
        
        with st.spinner("Dang xu ly..."):
            results = spark_processor.process_images_batch(
                INPUT_FOLDER, 
                OUTPUT_FOLDER, 
                session_id
            )
        
        st.session_state.processing_results = results
        
        # Load anh da xu ly de hien thi
        st.session_state.processed_images = []
        st.session_state.original_images = []
        st.session_state.selected_images = []
        
        session_output_folder = os.path.join(OUTPUT_FOLDER, session_id)
        
        for input_path, output_path, status in results:
            if status == "Success" and output_path and os.path.exists(output_path):
                # Load anh goc
                original_img = cv2.imread(input_path)
                original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
                
                # Load anh da xu ly
                processed_img = cv2.imread(output_path)
                processed_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                
                filename = os.path.basename(input_path)
                
                st.session_state.original_images.append({
                    'name': filename,
                    'image': original_rgb,
                    'path': input_path
                })
                st.session_state.processed_images.append({
                    'name': filename,
                    'image': processed_rgb,
                    'path': output_path
                })
                st.session_state.selected_images.append(True)
        
        status_text.text("")
        st.success(f"Hoan thanh! Da xu ly {len(results)} anh")
        
        # Clear camera images sau khi xử lý
        st.session_state.camera_images = []

# Hien thi ket qua
if st.session_state.processed_images:
    st.markdown("---")
    st.subheader("3. Ket Qua")
    
    # Hien thi cac anh
    for idx, (original_data, processed_data) in enumerate(zip(st.session_state.original_images, st.session_state.processed_images)):
        st.write(f"**{processed_data['name']}**")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.write("Anh goc")
            st.image(original_data['image'], width=250)
        with col2:
            st.write("Da xu ly")
            st.image(processed_data['image'], width=250)
        with col3:
            st.write("")
            st.write("")
            st.session_state.selected_images[idx] = st.checkbox(
                "Chon",
                value=st.session_state.selected_images[idx],
                key=f"select_{idx}"
            )
        
        st.markdown("---")
    
    # Tai xuong
    selected_count = sum(st.session_state.selected_images)
    
    if selected_count > 0:
        st.write(f"Da chon {selected_count} anh")
        
        col1, col2 = st.columns(2)
        with col1:
            download_format = st.selectbox("Dinh dang", ["PNG", "JPEG"])
        with col2:
            st.write("")
            st.write("")
            if st.button("Tai Xuong ZIP", type="primary"):
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, is_selected in enumerate(st.session_state.selected_images):
                        if is_selected:
                            processed_data = st.session_state.processed_images[idx]
                            
                            pil_image = Image.fromarray(processed_data['image'])
                            
                            img_buffer = io.BytesIO()
                            if download_format == "PNG":
                                pil_image.save(img_buffer, format='PNG')
                                file_ext = '.png'
                            else:
                                if pil_image.mode == 'RGBA':
                                    pil_image = pil_image.convert('RGB')
                                pil_image.save(img_buffer, format='JPEG', quality=95)
                                file_ext = '.jpg'
                            
                            img_buffer.seek(0)
                            
                            original_name = processed_data['name'].rsplit('.', 1)[0]
                            new_name = f"{original_name}_no_bg{file_ext}"
                            zip_file.writestr(new_name, img_buffer.getvalue())
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="Click de tai",
                    data=zip_buffer,
                    file_name="processed_images.zip",
                    mime="application/zip"
                )
    else:
        st.warning("Vui long chon it nhat mot anh")
