"""
Occupancy package — re-export engine utilities for convenience.
"""
from app.occupancy.engine import get_occupancy_model, BaseOccupancyModel, PredictionResult

__all__ = ["get_occupancy_model", "BaseOccupancyModel", "PredictionResult"]
