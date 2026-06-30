"""
4_SegFormer_Diagnostics.py — Dashboard Diagnostics Page

Provides visual verification of the real pretrained SegFormer model behavior.
Displays original image, segmentation mask, overlay, and class analysis.
"""

import streamlit as st
import numpy as np
import cv2
import time
import os
import sys

# Add backend to path to allow importing models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.occupancy.models.segformer_model import SegFormerOccupancyModel, ADE20K_EMPTY_CLASSES
from app.occupancy.utils.visualizer import generate_mask_preview, overlay_segmentation_mask

# Helper dictionary for class names
ADE20K_CLASSES = {
    0: "wall", 1: "building", 2: "sky", 3: "floor", 4: "tree", 5: "ceiling",
    6: "road", 7: "bed", 8: "window", 9: "grass", 10: "cabinet", 11: "sidewalk",
    12: "person", 13: "earth", 14: "door", 15: "table", 16: "mountain", 17: "plant",
    18: "curtain", 19: "chair", 20: "car", 32: "shelf", 44: "box"
}

st.set_page_config(
    page_title="SegFormer Diagnostics",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    .page-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 22px 28px; border-radius: 14px; margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .header-title { color: #fff; font-size: 24px; font-weight: 700; margin: 0; }
    .header-sub   { color: #94a3b8; font-size: 14px; margin: 4px 0 0 0; }
    
    .metric-box {
        background: rgba(30,41,59,0.5);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 12px; padding: 16px;
        text-align: center;
    }
</style>
<div class="page-header">
    <h2 class="header-title">🧠 SegFormer Diagnostics</h2>
    <p class="header-sub">Visual verification of pretrained semantic segmentation on warehouse images</p>
</div>
""", unsafe_allow_html=True)

# 1. Model Loading
@st.cache_resource(show_spinner=False)
def load_cached_model():
    model = SegFormerOccupancyModel()
    model.load_model()
    return model

with st.spinner("Loading SegFormer Model... (This may take a minute)"):
    model = load_cached_model()

# 2. File Uploader for Test Image
uploaded_file = st.file_uploader("Upload a warehouse image for testing", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert uploaded file to OpenCV format
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, 1)
    
    # Run Prediction
    with st.spinner("Running Inference..."):
        result = model.predict(frame)
        
        # To get the raw mask for visualization, we need to access the processor and model directly
        from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
        import torch
        
        processor = model._processor_instance
        hf_model = model._model_instance
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inputs = processor(images=rgb_frame, return_tensors="pt")
        with torch.no_grad():
            outputs = hf_model(**inputs)
        logits = outputs.logits
        upsampled_logits = torch.nn.functional.interpolate(logits, size=rgb_frame.shape[:2], mode="bilinear", align_corners=False)
        segmentation_map = upsampled_logits.argmax(dim=1).squeeze().cpu().numpy()
        
        color_mask = generate_mask_preview(segmentation_map)
        overlay = overlay_segmentation_mask(frame, color_mask, alpha=0.6)

    # 3. Display Results
    st.subheader("Inference Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-box"><h3>{result.occupancy_percentage:.1f}%</h3><p>Estimated Occupancy</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><h3>{result.confidence_score:.2f}</h3><p>Confidence Score</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><h3>{result.processing_time_ms} ms</h3><p>Inference Time</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # 4. Image Visuals
    img_col1, img_col2, img_col3 = st.columns(3)
    with img_col1:
        st.write("Original Image")
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_column_width=True)
    with img_col2:
        st.write("Segmentation Mask")
        st.image(cv2.cvtColor(color_mask, cv2.COLOR_BGR2RGB), use_column_width=True)
    with img_col3:
        st.write("Overlay")
        st.image(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB), use_column_width=True)

    st.markdown("---")
    
    # 5. Class Analysis
    st.subheader("Detected Classes Analysis")
    
    unique_classes, counts = np.unique(segmentation_map, return_counts=True)
    total_pixels = result.metadata["total_pixels"]
    
    class_data = []
    for cls_id, count in zip(unique_classes, counts):
        cls_name = ADE20K_CLASSES.get(cls_id, f"Unknown (ID: {cls_id})")
        pct = (count / total_pixels) * 100
        category = "Empty (Structural)" if cls_id in ADE20K_EMPTY_CLASSES else "Occupied (Object)"
        class_data.append({
            "Class ID": cls_id,
            "Name": cls_name,
            "Pixels": count,
            "Coverage (%)": f"{pct:.2f}%",
            "Category": category
        })
    
    import pandas as pd
    df = pd.DataFrame(class_data).sort_values("Pixels", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Upload an image to run the SegFormer diagnostics pipeline.")
