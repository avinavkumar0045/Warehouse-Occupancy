import sys
import os
import cv2
import time
import psutil

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.occupancy.models.segformer_model import SegFormerOccupancyModel

def generate_synthetic_test_frame(width: int = 640, height: int = 480):
    import numpy as np
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame, (0, 0), (width, height), (20, 20, 25), -1)
    cv2.rectangle(frame, (0, int(height * 0.45)), (width, height), (65, 65, 70), -1)
    cv2.rectangle(frame, (80,  150), (220, 360), (110, 75, 45), -1)
    return frame

def run_benchmark():
    frame = generate_synthetic_test_frame()
    model = SegFormerOccupancyModel()
    model.load_model()
    
    # Warmup
    model.predict(frame)
    
    test_cases = [1, 10, 50, 100]
    process = psutil.Process(os.getpid())
    
    print("SEGFORMER BENCHMARK RESULTS")
    print("===========================")
    
    for num_images in test_cases:
        start_mem = process.memory_info().rss / (1024 * 1024) # MB
        start_time = time.time()
        
        for _ in range(num_images):
            model.predict(frame)
            
        end_time = time.time()
        end_mem = process.memory_info().rss / (1024 * 1024) # MB
        
        total_time = end_time - start_time
        avg_time = (total_time / num_images) * 1000 # ms
        
        print(f"Test: {num_images} images")
        print(f"Total Time: {total_time:.2f} s")
        print(f"Avg Inference Time: {avg_time:.2f} ms")
        print(f"Memory Usage: {end_mem:.2f} MB (Delta: {end_mem - start_mem:.2f} MB)")
        print("-" * 20)

if __name__ == "__main__":
    run_benchmark()
