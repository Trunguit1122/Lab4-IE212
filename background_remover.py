import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Màu nền và mask
BG_COLOR = (192, 192, 192)  # xám
MASK_COLOR = (255, 255, 255)  # trắng

model_path = "models/selfie_segmenter.tflite"
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.ImageSegmenterOptions(base_options=base_options, output_category_mask=True)
segmenter = vision.ImageSegmenter.create_from_options(options)

def remove_background(image_frame: np.ndarray) -> np.ndarray:
    """Xóa nền ảnh sử dụng MediaPipe segmentation"""
    # Tạo MediaPipe image
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_frame)
    seg_result = segmenter.segment(mp_img)
    cat_mask = seg_result.category_mask

    # Xử lý xóa nền
    img_data = mp_img.numpy_view()
    fg_img = np.zeros(img_data.shape, dtype=np.uint8)
    fg_img[:] = MASK_COLOR
    bg_img = np.zeros(img_data.shape, dtype=np.uint8)
    bg_img[:] = BG_COLOR
    
    cond = np.stack((cat_mask.numpy_view(),) * 3, axis=-1) > 0.2
    output = np.where(cond, bg_img, img_data)

    return output
