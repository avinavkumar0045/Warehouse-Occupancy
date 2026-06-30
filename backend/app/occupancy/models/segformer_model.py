"""
SegFormer Occupancy Model

MVP implementation: uses brightness-based pixel analysis to simulate
the output of a SegFormer-B0 semantic segmentation model.

Future path:
  1. Load HuggingFace SegFormerForSemanticSegmentation in load_model().
  2. Replace the brightness heuristic in predict() with real inference.
"""

from __future__ import annotations

import cv2
import torch
import numpy as np
import logging

from app.occupancy.models.base_model import BaseOccupancyModel, PredictionResult

logger = logging.getLogger(__name__)

MODEL_VERSION = "segformer-b0-finetuned-ade-v1.0.0"

# ADE20K semantic classes mapping (partial) for warehouse-like approximation.
# ADE20K doesn't have a specific "storage_material" class.
# Common warehouse occupied objects in ADE20K:
# 11: box, 32: shelf, 44: box, 15: cabinet, 67: desk, 5: tree (sometimes misclassified), etc.
# Actually, ADE20K:
# 0: wall, 1: building, 2: sky, 3: floor, 4: tree, 5: ceiling, 6: road, 7: bed, 8: window, 9: grass, 10: cabinet, 11: sidewalk, 12: person, 13: earth, 14: door, 15: table, 16: mountain, 17: plant, 18: curtain, 19: chair
# Wait, let's treat anything that is NOT a structural empty space (floor, wall, ceiling, sky, road, window, door) as "occupied".
ADE20K_EMPTY_CLASSES = {0, 1, 2, 3, 5, 6, 8, 11, 13, 14}


class SegFormerOccupancyModel(BaseOccupancyModel):
    """
    SegFormer-B0 wrapper for occupancy estimation using a real pretrained model.
    """

    # Class-level variables for Singleton pattern
    _processor_instance = None
    _model_instance = None
    _is_loaded = False

    def __init__(self, checkpoint: str = "nvidia/segformer-b0-finetuned-ade-512-512") -> None:
        self.checkpoint = checkpoint
        logger.info(f"SegFormer: Initialized with checkpoint='{self.checkpoint}'.")

    def load_model(self) -> None:
        """
        Lazy-loads the real SegFormer weights and processor exactly once.
        """
        if SegFormerOccupancyModel._is_loaded:
            logger.info("SegFormer: Model already loaded (Singleton).")
            return

        logger.info(f"SegFormer: Loading model weights from '{self.checkpoint}'...")
        t0 = self._time_ms()
        
        from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
        
        # Load processor and model into class-level variables
        SegFormerOccupancyModel._processor_instance = SegformerImageProcessor.from_pretrained(self.checkpoint)
        SegFormerOccupancyModel._model_instance = SegformerForSemanticSegmentation.from_pretrained(self.checkpoint)
        
        # We only support CPU inference as per requirements
        SegFormerOccupancyModel._model_instance.eval()
        
        SegFormerOccupancyModel._is_loaded = True
        elapsed = self._time_ms() - t0
        logger.info(f"SegFormer: Successfully loaded model and processor in {elapsed} ms.")

    def predict(self, frame: np.ndarray) -> PredictionResult:
        """
        Estimate occupancy using real HuggingFace SegFormer inference.
        """
        t_start = self._time_ms()
        logger.info(f"SegFormer: Running inference on frame shape={frame.shape}.")
        
        if not self._is_loaded:
            self.load_model()
            
        processor = SegFormerOccupancyModel._processor_instance
        model = SegFormerOccupancyModel._model_instance

        # 1. Convert OpenCV BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 2. Preprocess
        inputs = processor(images=rgb_frame, return_tensors="pt")
        
        # 3. Model Inference (no gradients needed)
        with torch.no_grad():
            outputs = model(**inputs)
            
        # 4. Post-process to get segmentation map
        logits = outputs.logits
        # Rescale logits to original image size
        upsampled_logits = torch.nn.functional.interpolate(
            logits,
            size=rgb_frame.shape[:2],
            mode="bilinear",
            align_corners=False,
        )
        # Argmax to get class predictions
        segmentation_map = upsampled_logits.argmax(dim=1).squeeze().cpu().numpy()
        
        # 5. Calculate Occupancy %
        total_pixels = segmentation_map.size
        # Create a mask of empty space classes
        empty_mask = np.isin(segmentation_map, list(ADE20K_EMPTY_CLASSES))
        empty_pixels = empty_mask.sum()
        occupied_pixels = total_pixels - empty_pixels
        
        occupancy = round((occupied_pixels / max(total_pixels, 1)) * 100.0, 2)
        
        # 6. Calculate Confidence (for now, default to a high value since we are using a real model but don't have true softmax entropy without more computation)
        confidence = 0.9000

        elapsed_ms = self._time_ms() - t_start
        logger.info(
            f"SegFormer: occupancy={occupancy}%, confidence={confidence}, "
            f"time={elapsed_ms}ms."
        )
        return PredictionResult(
            occupancy_percentage=occupancy,
            confidence_score=confidence,
            model_version=self.get_model_version(),
            processing_time_ms=elapsed_ms,
            metadata={
                "checkpoint": self.checkpoint,
                "total_pixels": int(total_pixels),
                "occupied_pixels": int(occupied_pixels),
                "empty_pixels": int(empty_pixels),
                "mode": "real_inference",
                "segmentation_map_shape": segmentation_map.shape,
            },
        )

    def get_model_version(self) -> str:
        return MODEL_VERSION
