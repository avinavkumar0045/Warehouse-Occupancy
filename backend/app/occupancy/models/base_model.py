"""
BaseOccupancyModel — Abstract interface for all AI occupancy models.

Every concrete model must:
  - implement predict(frame) → PredictionResult
  - implement get_model_version() → str
  - optionally override load_model() for lazy model loading

PredictionResult is a typed dataclass that carries richer output than a
bare float, enabling confidence scoring and processing-time tracking.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class PredictionResult:
    """
    Structured output returned by every occupancy model.

    Attributes:
        occupancy_percentage: Estimated occupancy in [0.0, 100.0].
        confidence_score:     Model confidence in [0.0, 1.0].
        model_version:        Semantic version string of the model.
        processing_time_ms:   Wall-clock inference time in milliseconds.
        metadata:             Optional dict for model-specific extras.
    """
    occupancy_percentage: float
    confidence_score: float = 1.0
    model_version: str = "1.0.0"
    processing_time_ms: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Clamp values to valid ranges
        self.occupancy_percentage = round(max(0.0, min(100.0, self.occupancy_percentage)), 2)
        self.confidence_score = round(max(0.0, min(1.0, self.confidence_score)), 4)
        self.processing_time_ms = max(0, self.processing_time_ms)


class BaseOccupancyModel(ABC):
    """
    Abstract Base Class for all AI occupancy estimation models.

    Concrete implementations are swappable at runtime via the factory
    function in engine.py, enabling seamless model versioning.
    """

    def load_model(self) -> None:
        """
        Optional hook for loading model weights/checkpoints lazily.
        Called by the factory before the first predict() call.
        Subclasses may override this for heavy initialisation.
        """
        pass  # default: no-op (model is stateless or already loaded)

    @abstractmethod
    def predict(self, frame: np.ndarray) -> PredictionResult:
        """
        Estimate occupancy from a single camera frame.

        Args:
            frame: NumPy array of shape (H, W, C) – BGR uint8.

        Returns:
            A PredictionResult instance with occupancy % and metadata.
        """
        ...

    @abstractmethod
    def get_model_version(self) -> str:
        """Return the semantic version string of this model."""
        ...

    # ── Convenience timing helper ──────────────────────────────────────────

    @staticmethod
    def _time_ms() -> int:
        """Return current monotonic time in milliseconds."""
        return int(time.monotonic() * 1000)
