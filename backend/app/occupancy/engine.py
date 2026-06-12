"""
Occupancy Engine

Central factory module for AI occupancy models.

Exports:
    get_occupancy_model(model_type)  — returns a ready-to-use model instance
    PredictionResult                 — the structured result dataclass

Supported model_type values: "segformer" | "deeplab" | "unet"
"""

from __future__ import annotations

import logging

from app.occupancy.models.base_model import BaseOccupancyModel, PredictionResult
from app.occupancy.models.segformer_model import SegFormerOccupancyModel
from app.occupancy.models.deeplab_model import DeepLabOccupancyModel
from app.occupancy.models.unet_model import UNetOccupancyModel

logger = logging.getLogger(__name__)

# Re-export for downstream convenience
__all__ = ["get_occupancy_model", "BaseOccupancyModel", "PredictionResult"]

# ── Model Registry ─────────────────────────────────────────────────────────────
_MODEL_REGISTRY: dict[str, type[BaseOccupancyModel]] = {
    "segformer": SegFormerOccupancyModel,
    "deeplab":   DeepLabOccupancyModel,
    "unet":      UNetOccupancyModel,
}

_DEFAULT_MODEL = "segformer"


def get_occupancy_model(model_type: str = _DEFAULT_MODEL) -> BaseOccupancyModel:
    """
    Factory function — return a fully initialised occupancy model.

    Calls load_model() on the instance before returning so any lazy
    weight-loading is complete before the first predict() call.

    Args:
        model_type: One of "segformer", "deeplab", "unet" (case-insensitive).

    Returns:
        A ready-to-use BaseOccupancyModel instance.
    """
    key = model_type.strip().lower()
    cls = _MODEL_REGISTRY.get(key)

    if cls is None:
        logger.warning(
            f"Occupancy Engine: Unknown model type '{model_type}'. "
            f"Defaulting to '{_DEFAULT_MODEL}'."
        )
        cls = _MODEL_REGISTRY[_DEFAULT_MODEL]

    logger.info(f"Occupancy Engine: Instantiating model '{key}' ({cls.__name__}).")
    instance = cls()
    instance.load_model()
    return instance
