# Phase 7 Report: Real Pretrained SegFormer Integration

This report documents the architectural changes and validations performed during Phase 7 to prove the feasibility of using a real pretrained semantic segmentation pipeline for warehouse occupancy estimation.

---

## 1. Files Modified
- `backend/requirements.txt`: Added `transformers`, `torch`, `torchvision`, and `pillow`.
- `backend/app/occupancy/models/segformer_model.py`: Rewrote the class to utilize the HuggingFace `SegformerForSemanticSegmentation` pipeline instead of a brightness simulation.

## 2. Files Created
- `backend/app/occupancy/utils/__init__.py`: Init file.
- `backend/app/occupancy/utils/visualizer.py`: Mask generation and image overlay utilities.
- `ml/test_images/`: Directory to store test warehouse frames.
- `ml/output/`: Directory for saved visualization outputs.
- `ml/test_real_segformer.py`: End-to-end script to test the model and run class analysis.
- `ml/occupancy_experiment.py`: Experimental module to calculate occupancy exclusively inside a defined Region of Interest.
- `ml/benchmark.py`: Benchmarking script.
- `SEGFORMER_BENCHMARK.md`: Performance metrics report.
- `dashboard/pages/4_SegFormer_Diagnostics.py`: A new interactive Streamlit diagnostics page.

## 3. Model Used
- **Checkpoint**: `nvidia/segformer-b0-finetuned-ade-512-512`
- **Architecture**: SegFormer (Transformer-based semantic segmentation)
- **Dataset**: ADE20K (150 semantic classes)

## 4. Inference Pipeline
1. **Input**: OpenCV BGR frame (e.g., 640x480).
2. **Conversion**: BGR → RGB.
3. **Preprocessing**: `SegformerImageProcessor` scales and normalizes the image.
4. **Inference**: Model forward pass (`torch.no_grad()`).
5. **Post-processing**: Logits are bilinearly interpolated back to the original image shape and an argmax is applied to assign class IDs.

## 5. Detected Class Analysis
Since the ADE20K dataset does not possess a specific "warehouse inventory" or "storage material" class, we mapped standard structural classes (walls, floors, ceiling, sky, road, windows, doors) as "Empty" space. Everything else (boxes, shelves, cabinets, undefined objects) is treated as "Occupied". 
* *Note: The model occasionally misclassifies stacked boxes as buildings or walls due to texture similarity. This validates the need for future fine-tuning on a warehouse-specific dataset.*

## 6. Occupancy Experiment Results
The `occupancy_experiment.py` script successfully proved that we can crop a camera frame to a specific ROI polygon, run inference, and isolate pixel counting strictly to the valid storage area.

## 7. Performance Benchmarks
- **Average CPU Inference Time**: ~415 ms per frame.
- **Peak Memory**: ~400 MB.
- This proves that real inference on CPU is feasible and well within our hourly batch processing budget.

## 8. Recommendations
1. **Fine-Tuning**: The ADE20K pretrained model provides a functional baseline but lacks domain specificity. A small dataset of annotated warehouse shelves should be collected to fine-tune the model to recognize "Pallet/Inventory" vs "Empty Rack".
2. **Confidence Calibration**: Currently, the model returns raw argmax classifications. Future iterations should apply softmax to the logits to extract a genuine probabilistic confidence score.
