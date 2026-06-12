"""
DeepLabV3+ Occupancy Model — Architecture Placeholder

Structural stub that conforms to the BaseOccupancyModel interface.
Returns a simulated reading until real DeepLabV3+ weights are integrated.
"""

from __future__ import annotations

import logging
import random

import numpy as np

from app.occupancy.models.base_model import BaseOccupancyModel, PredictionResult

logger = logging.getLogger(__name__)

MODEL_VERSION = "deeplab-v3plus-resnet50-v1.0.0"


class DeepLabOccupancyModel(BaseOccupancyModel):
    """
    DeepLabV3+ with ResNet-50 backbone — architecture placeholder.

    Future path:
        Load torchvision.models.segmentation.deeplabv3_resnet50 in load_model()
        and run real forward passes in predict().
    """

    def load_model(self) -> None:
        logger.info("DeepLab: load_model() called — placeholder; no weights loaded.")

    def predict(self, frame: np.ndarray) -> PredictionResult:
        t_start = self._time_ms()
        logger.info(f"DeepLab: Running placeholder inference on frame shape={frame.shape}.")

        # Deterministic simulation: slight frame-dependent noise around 58.5%
        seed = int(np.mean(frame)) % 100
        occupancy = round(58.5 + (seed % 7 - 3), 2)
        confidence = round(0.72 + random.uniform(-0.05, 0.05), 4)

        elapsed_ms = self._time_ms() - t_start
        logger.info(f"DeepLab: occupancy={occupancy}%, confidence={confidence}, time={elapsed_ms}ms.")
        return PredictionResult(
            occupancy_percentage=occupancy,
            confidence_score=confidence,
            model_version=self.get_model_version(),
            processing_time_ms=elapsed_ms,
            metadata={"mode": "placeholder_simulation"},
        )

    def get_model_version(self) -> str:
        return MODEL_VERSION
