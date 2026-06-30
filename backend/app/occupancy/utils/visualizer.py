"""
Visualization utilities for semantic segmentation masks.
Used for visual debugging and verification of SegFormer outputs.
"""

import os
import cv2
import numpy as np
from typing import Tuple

# A basic colour palette for ADE20K classes to map class IDs to distinct colours
# We can use a randomized colormap for a general preview.
np.random.seed(42)
COLOR_PALETTE = np.random.randint(0, 255, size=(150, 3), dtype=np.uint8)
# Let's set some specific colors for our empty classes to make them distinct
ADE20K_EMPTY_CLASSES = {0, 1, 2, 3, 5, 6, 8, 11, 13, 14}
for cls_id in ADE20K_EMPTY_CLASSES:
    COLOR_PALETTE[cls_id] = [0, 0, 0]  # Black for empty/structural space


def generate_mask_preview(segmentation_map: np.ndarray) -> np.ndarray:
    """
    Converts a 2D segmentation map of class IDs into a 3D BGR color image.
    """
    color_mask = COLOR_PALETTE[segmentation_map]
    return color_mask


def overlay_segmentation_mask(image: np.ndarray, color_mask: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    Blends the original BGR image with the color mask.
    Both images must have the same shape.
    """
    if image.shape != color_mask.shape:
        raise ValueError(f"Image shape {image.shape} and mask shape {color_mask.shape} do not match.")
    
    overlay = cv2.addWeighted(image, 1.0 - alpha, color_mask, alpha, 0)
    return overlay


def save_visualization(image: np.ndarray, mask: np.ndarray, overlay: np.ndarray, output_dir: str, prefix: str = "test") -> None:
    """
    Saves the original image, color mask, and overlay to the specified directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    cv2.imwrite(os.path.join(output_dir, f"{prefix}_original.jpg"), image)
    cv2.imwrite(os.path.join(output_dir, f"{prefix}_mask.jpg"), mask)
    cv2.imwrite(os.path.join(output_dir, f"{prefix}_overlay.jpg"), overlay)
