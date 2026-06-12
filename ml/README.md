# AI Occupancy Estimation Subsystem (ML)

This directory contains the machine learning pipelines, inference abstractions, and training wrappers for estimated warehouse utilization analysis.

---

## Model Strategy & Architecture

To optimize performance and avoid cold-start issues, this platform relies entirely on **Transfer Learning** using a pre-trained semantic segmentation model.

### 1. Selected Model Hierarchy
1. **SegFormer-B0 (Preferred)**: Transformer-based model. High accuracy, exceptionally fast, and lightweight parameters making it suitable for live edge-based hourly polling.
2. **DeepLabV3+ ResNet50**: Strong convolutional baseline using atrous spatial pyramid pooling.
3. **U-Net with Pretrained Encoder (e.g., ResNet34)**: Flexible and fast baseline, useful for custom dataset resolutions.

### 2. Class Labels
* **0: Background** (walls, empty floor space, ceiling, forklifts, humans, fixtures)
* **1: Storage Material** (pallets, boxes, crates, raw inventory, cargo containers)

### 3. Inference Logic
1. **Connect & Capture**: Retrieve snapshot frame from the RTSP stream.
2. **Segmentation**: Feed the image to the SegFormer model. The model outputs a pixel-level classification mask where:
   - `Mask == 0` for background.
   - `Mask == 1` for storage material.
3. **Occupancy Calculation**:
   $$\text{Occupancy Percentage} = \left( \frac{\text{Count of pixels classified as 1}}{\text{Total pixels in camera field of view}} \right) \times 100$$
4. **Aggregation**: The backend reads percentages from active storage cameras and averages them to calculate the warehouse's current occupancy.

---

## Future Training & Fine-Tuning Pipeline

1. **Data Collection**: Save snapshots from the camera streams periodically.
2. **Labeling**: Annotate masks using tools like LabelStudio or CVAT (marking storage materials as class `1`).
3. **Fine-Tuning**: Run training scripts with HuggingFace `Trainer` or PyTorch loops to adapt pretrained SegFormer weights (`nvidia/mit-b0`) to specific warehouse camera angles and illumination conditions.
