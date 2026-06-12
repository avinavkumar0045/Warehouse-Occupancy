"""
ml/test_segformer.py — SegFormer Pipeline Verification Script

Run this script from the project root to verify the end-to-end
occupancy inference pipeline without needing a live RTSP feed.

Usage:
    cd /path/to/warehouse-occupancy
    python -m ml.test_segformer

What it does:
  1. Generates a synthetic warehouse-like test frame (640×480 BGR).
  2. Instantiates the SegFormerOccupancyModel (simulation mode).
  3. Runs predict() and prints the full PredictionResult.
  4. Exercises the ROI service: validates a polygon, crops the frame,
     and calculates the covered area fraction.
  5. Exits with code 0 on success, 1 on failure.
"""

from __future__ import annotations

import sys
import time
import numpy as np

# Add the backend package to sys.path so imports work when run standalone
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def generate_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Create a synthetic BGR warehouse scene for testing."""
    import cv2
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Dark background
    cv2.rectangle(frame, (0, 0), (width, height), (20, 20, 25), -1)
    # Grey floor
    cv2.rectangle(frame, (0, int(height * 0.45)), (width, height), (65, 65, 70), -1)
    # Storage crates (brownish rectangles)
    cv2.rectangle(frame, (80,  150), (220, 360), (110, 75, 45), -1)
    cv2.rectangle(frame, (280, 180), (420, 360), (125, 85, 50), -1)
    cv2.rectangle(frame, (460, 130), (580, 360), (105, 70, 40), -1)
    # Blue stacked pallets
    cv2.rectangle(frame, (100, 80), (200, 155), (160, 40, 40), -1)
    # Text overlay
    cv2.putText(
        frame, "TEST FRAME - SIMULATED WAREHOUSE",
        (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 80), 2,
    )
    return frame


def run_inference_test(frame: np.ndarray) -> bool:
    """Run SegFormer inference and validate the PredictionResult."""
    from app.occupancy.models.segformer_model import SegFormerOccupancyModel

    print("\n" + "=" * 60)
    print("  SEGFORMER INFERENCE TEST")
    print("=" * 60)

    model = SegFormerOccupancyModel(checkpoint="nvidia/mit-b0")
    model.load_model()

    t0     = time.monotonic()
    result = model.predict(frame)
    elapsed = (time.monotonic() - t0) * 1000

    print(f"\n  Frame shape      : {frame.shape}")
    print(f"  Occupancy        : {result.occupancy_percentage:.2f}%")
    print(f"  Confidence Score : {result.confidence_score:.4f}")
    print(f"  Model Version    : {result.model_version}")
    print(f"  Inference Time   : {result.processing_time_ms} ms  (wall: {elapsed:.1f} ms)")
    print(f"  Metadata         : {result.metadata}")

    # Sanity assertions
    assert 0.0 <= result.occupancy_percentage <= 100.0, "Occupancy out of range!"
    assert 0.0 <= result.confidence_score     <= 1.0,   "Confidence out of range!"
    assert result.model_version,                         "Model version missing!"
    assert result.processing_time_ms >= 0,               "Negative processing time!"
    print("\n  ✅ All inference assertions passed.")
    return True


def run_roi_test(frame: np.ndarray) -> bool:
    """Run ROI service tests on the test frame."""
    from app.services.roi_service import (
        validate_polygon, draw_polygon, crop_to_roi, calculate_roi_area
    )

    print("\n" + "=" * 60)
    print("  ROI SERVICE TEST")
    print("=" * 60)

    # Define a simple rectangular ROI covering the centre of the frame
    roi_points = [
        {"x": 50,  "y": 100},
        {"x": 590, "y": 100},
        {"x": 590, "y": 400},
        {"x": 50,  "y": 400},
    ]

    # 1. Validate
    valid = validate_polygon(roi_points)
    print(f"\n  Polygon valid       : {valid}")
    assert valid, "Valid polygon flagged as invalid!"

    # 2. Draw
    drawn = draw_polygon(frame, roi_points, color=(0, 255, 0), thickness=2)
    assert drawn.shape == frame.shape, "draw_polygon changed frame shape!"
    print(f"  draw_polygon        : OK (shape={drawn.shape})")

    # 3. Crop
    cropped = crop_to_roi(frame, roi_points)
    assert cropped.shape == frame.shape, "crop_to_roi changed frame shape!"
    # Outside-ROI pixels should be zeroed
    assert int(cropped[5, 5].sum()) == 0, "Pixels outside ROI should be black!"
    print(f"  crop_to_roi         : OK (outside pixels zeroed)")

    # 4. Area fraction
    area_fraction = calculate_roi_area(roi_points, frame.shape)
    print(f"  ROI area fraction   : {area_fraction:.4f} ({area_fraction*100:.2f}% of frame)")
    assert 0.0 < area_fraction <= 1.0, "Area fraction out of range!"

    # Test with invalid polygon
    bad_valid = validate_polygon([{"x": 0, "y": 0}])  # Only 1 point
    assert not bad_valid, "Invalid polygon should return False!"
    print(f"  Invalid polygon test: correctly rejected (validate returned False)")

    print("\n  ✅ All ROI assertions passed.")
    return True


def run_all_model_tests(frame: np.ndarray) -> bool:
    """Smoke-test DeepLab and UNet placeholder models."""
    from app.occupancy.models.deeplab_model import DeepLabOccupancyModel
    from app.occupancy.models.unet_model    import UNetOccupancyModel

    print("\n" + "=" * 60)
    print("  DEEPLAB & UNET PLACEHOLDER MODEL TESTS")
    print("=" * 60)

    for ModelClass in [DeepLabOccupancyModel, UNetOccupancyModel]:
        model  = ModelClass()
        result = model.predict(frame)
        print(f"\n  [{model.__class__.__name__}]")
        print(f"    Occupancy  : {result.occupancy_percentage:.2f}%")
        print(f"    Confidence : {result.confidence_score:.4f}")
        print(f"    Version    : {result.model_version}")
        assert 0.0 <= result.occupancy_percentage <= 100.0
        assert 0.0 <= result.confidence_score     <= 1.0

    print("\n  ✅ All model placeholder assertions passed.")
    return True


def main() -> None:
    print("\n🏭  Warehouse Occupancy Platform — ML Pipeline Verification")
    print("━" * 60)

    frame = generate_test_frame()
    print(f"\nGenerated synthetic test frame: {frame.shape[1]}×{frame.shape[0]} px")

    results = []
    for test_fn in [run_inference_test, run_roi_test, run_all_model_tests]:
        try:
            ok = test_fn(frame)
            results.append(ok)
        except AssertionError as ae:
            print(f"\n  ❌ ASSERTION FAILED: {ae}")
            results.append(False)
        except Exception as exc:
            print(f"\n  ❌ EXCEPTION: {exc}")
            results.append(False)

    print("\n" + "=" * 60)
    if all(results):
        print("  🎉 ALL TESTS PASSED — Pipeline is ready.")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        failed = results.count(False)
        print(f"  ⚠️  {failed}/{len(results)} TEST(S) FAILED.")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
