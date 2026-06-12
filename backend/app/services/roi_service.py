"""
ROI (Region of Interest) Service

Provides utilities for working with polygon-based regions of interest
on camera frames. Polygons are stored as JSON lists of {x, y} points.

Functions:
    validate_polygon    — Check that a polygon has ≥3 valid points
    draw_polygon        — Draw the ROI boundary on an image (in-place copy)
    crop_to_roi         — Zero-out pixels outside the polygon mask
    calculate_roi_area  — Return ROI area as a fraction of the total frame
"""

from __future__ import annotations

import logging
from typing import List

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# A point is expected to be {"x": float, "y": float}
Point = dict  # {"x": float|int, "y": float|int}


# ── Validation ────────────────────────────────────────────────────────────────

def validate_polygon(points: List[Point]) -> bool:
    """
    Validate that a polygon has at least 3 well-formed points.

    Args:
        points: List of dicts with "x" and "y" keys (pixel coordinates).

    Returns:
        True if the polygon is valid, False otherwise.
    """
    if not isinstance(points, list) or len(points) < 3:
        logger.warning("ROI Service: Polygon validation failed – fewer than 3 points provided.")
        return False

    for i, pt in enumerate(points):
        if not isinstance(pt, dict) or "x" not in pt or "y" not in pt:
            logger.warning(f"ROI Service: Point {i} is malformed: {pt}")
            return False
        try:
            float(pt["x"])
            float(pt["y"])
        except (TypeError, ValueError):
            logger.warning(f"ROI Service: Point {i} has non-numeric coordinates: {pt}")
            return False

    logger.debug(f"ROI Service: Polygon with {len(points)} points is valid.")
    return True


# ── Drawing ───────────────────────────────────────────────────────────────────

def draw_polygon(
    image: np.ndarray,
    points: List[Point],
    color: tuple = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw the ROI polygon boundary onto a copy of the image.

    Args:
        image:     Input frame (H, W, C) numpy array.
        points:    List of {x, y} dicts defining the polygon.
        color:     BGR colour tuple for the outline (default: green).
        thickness: Line thickness in pixels.

    Returns:
        A new numpy array with the polygon drawn. The original is unchanged.
    """
    if not validate_polygon(points):
        logger.warning("ROI Service: draw_polygon called with invalid polygon – returning original frame.")
        return image.copy()

    output = image.copy()
    pts = np.array([[int(p["x"]), int(p["y"])] for p in points], dtype=np.int32)
    cv2.polylines(output, [pts], isClosed=True, color=color, thickness=thickness)
    logger.debug(f"ROI Service: Drew polygon with {len(points)} vertices.")
    return output


# ── Masking / Cropping ────────────────────────────────────────────────────────

def crop_to_roi(image: np.ndarray, points: List[Point]) -> np.ndarray:
    """
    Zero out all pixels outside the ROI polygon.

    Args:
        image:  Input frame (H, W, C) numpy array.
        points: List of {x, y} dicts defining the polygon.

    Returns:
        A new numpy array where only pixels inside the polygon are preserved;
        all others are set to black (0). Returns a copy of the original if
        the polygon is invalid.
    """
    if not validate_polygon(points):
        logger.warning("ROI Service: crop_to_roi called with invalid polygon – returning original frame.")
        return image.copy()

    h, w = image.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array([[int(p["x"]), int(p["y"])] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)

    # Apply mask: keep only ROI pixels
    output = cv2.bitwise_and(image, image, mask=mask)
    logger.debug(f"ROI Service: Applied polygon mask to frame of shape {image.shape}.")
    return output


# ── Area Calculation ──────────────────────────────────────────────────────────

def calculate_roi_area(points: List[Point], img_shape: tuple) -> float:
    """
    Calculate the ROI polygon area as a fraction (0.0–1.0) of the total image.

    Args:
        points:    List of {x, y} dicts defining the polygon.
        img_shape: Tuple (H, W) or (H, W, C) of the image.

    Returns:
        Area fraction in [0.0, 1.0]. Returns 0.0 if polygon is invalid.
    """
    if not validate_polygon(points):
        logger.warning("ROI Service: calculate_roi_area called with invalid polygon – returning 0.0.")
        return 0.0

    h, w = img_shape[:2]
    total_pixels = h * w
    if total_pixels == 0:
        return 0.0

    pts = np.array([[int(p["x"]), int(p["y"])] for p in points], dtype=np.float32)
    # Shoelace formula via OpenCV's contour area
    roi_area = cv2.contourArea(pts)
    fraction = float(roi_area) / float(total_pixels)
    fraction = max(0.0, min(1.0, fraction))

    logger.debug(
        f"ROI Service: ROI area = {roi_area:.1f}px² / {total_pixels}px² = {fraction:.4f} ({fraction*100:.2f}%)"
    )
    return round(fraction, 6)
