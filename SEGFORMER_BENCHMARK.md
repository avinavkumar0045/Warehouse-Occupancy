# SegFormer Performance Benchmark

This document details the performance metrics of the integrated `nvidia/segformer-b0-finetuned-ade-512-512` model running purely on CPU inference.

## Test Environment
- **Device**: CPU (Mac ARM64)
- **Model**: SegFormer-B0
- **Image Size**: 640x480 (resized internally by processor to 512x512)
- **Execution Mode**: `torch.no_grad()`, `model.eval()`

## Benchmark Results

| Test Size | Total Time (s) | Avg Inference Time (ms) | Peak Memory Usage (MB) | Memory Delta (MB) |
|---|---|---|---|---|
| 1 image | 0.45 s | 452.85 ms | 412.12 MB | -42.34 MB |
| 10 images | 4.35 s | 434.61 ms | 348.59 MB | -63.53 MB |
| 50 images | 20.07 s | 401.44 ms | 397.86 MB | 48.98 MB |
| 100 images | 41.36 s | 413.59 ms | 301.17 MB | -97.03 MB |

## Analysis & Recommendations

1. **Inference Latency**: The model averages ~400-450 ms per frame on CPU. Since our production APScheduler job polls cameras every hour, this latency is highly acceptable. Even with 100 active cameras, a full warehouse sweep would take less than a minute.
2. **Memory Footprint**: Memory usage remained stable around ~300-400 MB after loading the weights. Memory delta fluctuated slightly but there are no memory leaks observed over 100 iterations.
3. **CPU Utilisation**: Single-threaded CPU inference is sufficient for our current scale.
4. **Future Optimizations**: If the number of cameras scales drastically (e.g., >1000 per server), we recommend migrating inference to a dedicated GPU worker pool using ONNX Runtime or TensorRT.
