"""
ml/occupancy_experiment.py — Experimental Occupancy Estimation Module

This script is for experimental validation of occupancy using semantic segmentation
classes within a specified Region of Interest (ROI).
It is deliberately decoupled from the production scheduler.
"""

import sys
import os
import cv2
import numpy as np

# Add the backend package to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.roi_service import validate_polygon, crop_to_roi, draw_polygon
from app.occupancy.models.segformer_model import SegFormerOccupancyModel, ADE20K_EMPTY_CLASSES
from app.occupancy.utils.visualizer import generate_mask_preview, overlay_segmentation_mask, save_visualization

def run_experiment(image_path: str, roi_points: list):
    """
    Run an occupancy experiment on a specific image and ROI.
    """
    print(f"\n🧪 Running Occupancy Experiment on {os.path.basename(image_path)}")
    print("-" * 60)

    # 1. Load Image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not load image at {image_path}")
        return

    # 2. Validate and Apply ROI
    if not validate_polygon(roi_points):
        print("Error: Invalid ROI polygon provided.")
        return

    roi_cropped_frame = crop_to_roi(frame, roi_points)
    
    # Visualization of ROI (Optional)
    roi_visual = draw_polygon(frame.copy(), roi_points, color=(0, 255, 0), thickness=2)

    # 3. Load Model and Predict
    print("Loading model and generating prediction...")
    model = SegFormerOccupancyModel()
    model.load_model()
    
    # We will run inference on the cropped frame. The pixels outside ROI are black.
    # We need to explicitly ignore the black pixels outside the ROI during calculation.
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
    import torch
    
    processor = SegformerImageProcessor.from_pretrained(model.checkpoint)
    hf_model = SegformerForSemanticSegmentation.from_pretrained(model.checkpoint)
    hf_model.eval()
    
    rgb_frame = cv2.cvtColor(roi_cropped_frame, cv2.COLOR_BGR2RGB)
    inputs = processor(images=rgb_frame, return_tensors="pt")
    
    with torch.no_grad():
        outputs = hf_model(**inputs)
        
    logits = outputs.logits
    upsampled_logits = torch.nn.functional.interpolate(logits, size=rgb_frame.shape[:2], mode="bilinear", align_corners=False)
    segmentation_map = upsampled_logits.argmax(dim=1).squeeze().cpu().numpy()

    # 4. Calculate Occupancy based ONLY on ROI
    # We create a mask for the ROI region by checking which pixels are non-black in the cropped frame
    # A simple way is to check if sum across channels > 0
    roi_pixel_mask = np.sum(roi_cropped_frame, axis=2) > 0
    total_roi_pixels = np.sum(roi_pixel_mask)
    
    # Create mask for empty classes
    empty_mask = np.isin(segmentation_map, list(ADE20K_EMPTY_CLASSES))
    
    # Consider only empty pixels that are inside the ROI
    empty_pixels_in_roi = np.sum(empty_mask & roi_pixel_mask)
    
    occupied_pixels_in_roi = total_roi_pixels - empty_pixels_in_roi
    
    occupancy_estimate = (occupied_pixels_in_roi / max(total_roi_pixels, 1)) * 100.0
    
    print("\n📊 Experiment Results")
    print(f"Total ROI Pixels   : {total_roi_pixels}")
    print(f"Occupied Pixels    : {occupied_pixels_in_roi}")
    print(f"Empty Pixels       : {empty_pixels_in_roi}")
    print(f"Estimated Occupancy: {occupancy_estimate:.2f}%")
    
    # 5. Visuals
    color_mask = generate_mask_preview(segmentation_map)
    # Mask out the segmentation map outside the ROI so it's clear
    color_mask[~roi_pixel_mask] = [0, 0, 0]
    
    overlay = overlay_segmentation_mask(roi_cropped_frame, color_mask, alpha=0.5)
    
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    base = os.path.splitext(os.path.basename(image_path))[0]
    cv2.imwrite(os.path.join(output_dir, f"{base}_experiment_roi.jpg"), roi_visual)
    cv2.imwrite(os.path.join(output_dir, f"{base}_experiment_overlay.jpg"), overlay)
    
    print(f"Outputs saved to {output_dir}/")

if __name__ == "__main__":
    # If there are test images, use the first one, else use a placeholder logic
    test_dir = os.path.join(os.path.dirname(__file__), "test_images")
    images = [f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png'))] if os.path.exists(test_dir) else []
    
    if images:
        img_path = os.path.join(test_dir, images[0])
        # Simple rectangle ROI for test
        roi = [
            {"x": 100, "y": 100},
            {"x": 540, "y": 100},
            {"x": 540, "y": 380},
            {"x": 100, "y": 380}
        ]
        run_experiment(img_path, roi)
    else:
        print("No test images found in ml/test_images/. Please add an image to run the experiment.")
