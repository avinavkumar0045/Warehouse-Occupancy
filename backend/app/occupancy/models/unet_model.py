"""
U-Net Occupancy Model — Architecture Placeholder

Structural stub that conforms to the BaseOccupancyModel interface.
Returns a simulated reading until real U-Net weights are integrated.
"""

from __future__ import annotations

import logging
import random

import numpy as np

from app.occupancy.models.base_model import BaseOccupancyModel, PredictionResult

logger = logging.getLogger(__name__)

MODEL_VERSION = "unet-efficientnet-b4-v1.0.0"


class UNetOccupancyModel(BaseOccupancyModel):
    """
    U-Net with EfficientNet-B4 encoder — architecture placeholder.

    Future path:
        Load segmentation_models_pytorch.Unet in load_model() and run real
        forward passes in predict().
    """

    def load_model(self) -> None:
        logger.info("UNet: load_model() called — placeholder; no weights loaded.")

    def predict(self, frame: np.ndarray) -> PredictionResult:
        t_start = self._time_ms()
        logger.info(f"UNet: Running placeholder inference on frame shape={frame.shape}.")

        # Deterministic simulation: centred around 62.4%
        seed = int(np.std(frame)) % 100
        occupancy = round(62.4 + (seed % 9 - 4), 2)
        confidence = round(0.68 + random.uniform(-0.05, 0.05), 4)

        elapsed_ms = self._time_ms() - t_start
        logger.info(f"UNet: occupancy={occupancy}%, confidence={confidence}, time={elapsed_ms}ms.")
        return PredictionResult(
            occupancy_percentage=occupancy,
            confidence_score=confidence,
            model_version=self.get_model_version(),
            processing_time_ms=elapsed_ms,
            metadata={"mode": "placeholder_simulation"},
        )

    def get_model_version(self) -> str:
        return MODEL_VERSION
