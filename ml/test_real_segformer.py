"""
ml/test_real_segformer.py — Real Pretrained SegFormer Test Script

Tests the real SegFormer pipeline, performs class analysis, and generates visualization.
"""

import sys
import os
import cv2
import numpy as np

# Add the backend package to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.occupancy.models.segformer_model import SegFormerOccupancyModel
from app.occupancy.utils.visualizer import generate_mask_preview, overlay_segmentation_mask, save_visualization

# Mapping ADE20K indices to some names for diagnostics
ADE20K_CLASSES = {
    0: "wall", 1: "building", 2: "sky", 3: "floor", 4: "tree", 5: "ceiling",
    6: "road", 7: "bed", 8: "window", 9: "grass", 10: "cabinet", 11: "sidewalk",
    12: "person", 13: "earth", 14: "door", 15: "table", 16: "mountain", 17: "plant",
    18: "curtain", 19: "chair", 20: "car", 32: "shelf", 44: "box"
}


def generate_synthetic_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Create a synthetic BGR warehouse scene for testing if no real image exists."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Dark background (wall/ceiling)
    cv2.rectangle(frame, (0, 0), (width, height), (20, 20, 25), -1)
    # Grey floor
    cv2.rectangle(frame, (0, int(height * 0.45)), (width, height), (65, 65, 70), -1)
    # Storage crates (brownish rectangles)
    cv2.rectangle(frame, (80,  150), (220, 360), (110, 75, 45), -1)
    cv2.rectangle(frame, (280, 180), (420, 360), (125, 85, 50), -1)
    # Text overlay
    cv2.putText(
        frame, "TEST FRAME",
        (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 80), 2,
    )
    return frame


def main():
    print("\n🏭 Warehouse Occupancy - Real SegFormer Test")
    print("=" * 60)

    # 1. Load an image or generate one
    test_dir = os.path.join(os.path.dirname(__file__), "test_images")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    
    images = [f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png'))] if os.path.exists(test_dir) else []
    
    if images:
        img_path = os.path.join(test_dir, images[0])
        print(f"Loading real image: {img_path}")
        frame = cv2.imread(img_path)
        prefix = os.path.splitext(images[0])[0]
    else:
        print("No test images found in ml/test_images/. Generating synthetic frame.")
        frame = generate_synthetic_test_frame()
        prefix = "synthetic"

    # 2. Run SegFormer
    print("\nLoading Real SegFormer Model (this will take a moment)...")
    model = SegFormerOccupancyModel()
    model.load_model()
    
    print("Running Inference...")
    result = model.predict(frame)
    
    print("\n" + "=" * 60)
    print("  INFERENCE RESULTS")
    print("=" * 60)
    print(f"Occupancy Percentage : {result.occupancy_percentage}%")
    print(f"Confidence Score     : {result.confidence_score}")
    print(f"Inference Time       : {result.processing_time_ms} ms")
    
    # 3. Class Analysis
    # We need to re-run the pipeline slightly here to get the raw mask for analysis,
    # as the current predict() returns only the PredictionResult.
    # Alternatively, we could store the segmentation map in metadata. Oh, we did!
    print("\n  CLASS ANALYSIS")
    print("-" * 60)
    total_pixels = result.metadata["total_pixels"]
    print(f"Total Pixels: {total_pixels}")
    
    # Let's extract the actual mask for visualization (re-run manually for the test script to show classes)
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
    import torch
    
    processor = SegformerImageProcessor.from_pretrained(model.checkpoint)
    hf_model = SegformerForSemanticSegmentation.from_pretrained(model.checkpoint)
    hf_model.eval()
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    inputs = processor(images=rgb_frame, return_tensors="pt")
    with torch.no_grad():
        outputs = hf_model(**inputs)
    logits = outputs.logits
    upsampled_logits = torch.nn.functional.interpolate(logits, size=rgb_frame.shape[:2], mode="bilinear", align_corners=False)
    segmentation_map = upsampled_logits.argmax(dim=1).squeeze().cpu().numpy()
    
    unique_classes, counts = np.unique(segmentation_map, return_counts=True)
    
    print("Detected Classes:")
    for cls_id, count in zip(unique_classes, counts):
        cls_name = ADE20K_CLASSES.get(cls_id, f"Unknown ({cls_id})")
        pct = (count / total_pixels) * 100
        print(f"  - ID: {cls_id:03d} | Name: {cls_name:<12} | Pixels: {count:<8} | Coverage: {pct:.2f}%")

    # 4. Generate Visualizations
    print("\nGenerating Visualizations...")
    color_mask = generate_mask_preview(segmentation_map)
    overlay = overlay_segmentation_mask(frame, color_mask, alpha=0.6)
    
    save_visualization(frame, color_mask, overlay, output_dir, prefix=prefix)
    print(f"Outputs saved to {output_dir}/ ({prefix}_original.jpg, {prefix}_mask.jpg, {prefix}_overlay.jpg)")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
