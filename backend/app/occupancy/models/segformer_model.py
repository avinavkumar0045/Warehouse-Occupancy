"""
SegFormer Occupancy Model

MVP implementation: uses brightness-based pixel analysis to simulate
the output of a SegFormer-B0 semantic segmentation model.

Future path:
  1. Load HuggingFace SegFormerForSemanticSegmentation in load_model().
  2. Replace the brightness heuristic in predict() with real inference.
"""

from __future__ import annotations

import logging

import numpy as np

from app.occupancy.models.base_model import BaseOccupancyModel, PredictionResult

logger = logging.getLogger(__name__)

MODEL_VERSION = "segformer-b0-v1.0.0"


class SegFormerOccupancyModel(BaseOccupancyModel):
    """
    SegFormer-B0 wrapper for occupancy estimation.

    MVP behaviour: brightness-ratio simulation constrained to [40, 80]%.
    Production path: real HuggingFace SegFormer inference (see load_model).
    """

    def __init__(self, checkpoint: str = "nvidia/mit-b0") -> None:
        self.checkpoint = checkpoint
        self._model = None  # populated by load_model() when real weights available
        logger.info(f"SegFormer: Initialized with checkpoint='{checkpoint}' (MVP simulation mode).")

    def load_model(self) -> None:
        """
        Placeholder for loading real SegFormer weights.

        When the HuggingFace model is available, replace the pass with:
            from transformers import SegformerForSemanticSegmentation, SegformerFeatureExtractor
            self._feature_extractor = SegformerFeatureExtractor.from_pretrained(self.checkpoint)
            self._model = SegformerForSemanticSegmentation.from_pretrained(self.checkpoint)
        """
        logger.info(
            "SegFormer: load_model() called — real weights not loaded in MVP. "
            "Will use brightness simulation."
        )

    def predict(self, frame: np.ndarray) -> PredictionResult:
        """
        Estimate occupancy using a brightness-ratio heuristic.

        Future flow (commented):
            inputs  = self._feature_extractor(images=frame, return_tensors="pt")
            outputs = self._model(**inputs)
            logits  = outputs.logits
            mask    = logits.argmax(dim=1).squeeze().numpy()
            pct     = float((mask == STORAGE_CLASS_ID).sum() / mask.size * 100)
        """
        t_start = self._time_ms()
        logger.info(f"SegFormer: Running inference on frame shape={frame.shape}.")

        # ── MVP Simulation ──────────────────────────────────────────────────
        gray = np.mean(frame, axis=2)
        bright_pixels = int(np.sum(gray > 40))
        total_pixels = int(gray.size)
        raw_ratio = bright_pixels / total_pixels * 100.0

        # Constrain to realistic warehouse occupancy window
        occupancy = round(max(40.0, min(80.0, raw_ratio)), 2)

        # Confidence: how many pixels were comfortably above the threshold
        very_bright = int(np.sum(gray > 80))
        confidence = round(min(1.0, very_bright / max(total_pixels, 1) + 0.6), 4)
        # ────────────────────────────────────────────────────────────────────

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
                "bright_pixels": bright_pixels,
                "total_pixels": total_pixels,
                "mode": "brightness_simulation",
            },
        )

    def get_model_version(self) -> str:
        return MODEL_VERSION
