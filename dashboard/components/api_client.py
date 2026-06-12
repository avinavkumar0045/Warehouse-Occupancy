"""
API Client — HTTP wrapper for the FastAPI backend.
Used by all Streamlit dashboard pages.
"""

import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Backend base URL — override via environment variable for different deployments
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api")


class APIClient:
    """HTTP client for interacting with the FastAPI backend."""

    # ── Warehouses ──────────────────────────────────────────────────────────

    @staticmethod
    def get_warehouses() -> List[Dict]:
        try:
            response = requests.get(f"{BACKEND_URL}/warehouses", timeout=5)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Failed to fetch warehouses: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error fetching warehouses: {e}")
        return []

    @staticmethod
    def create_warehouse(
        name: str, location: str, description: Optional[str] = None
    ) -> Optional[Dict]:
        try:
            payload = {"name": name, "location": location, "description": description}
            response = requests.post(f"{BACKEND_URL}/warehouses", json=payload, timeout=5)
            if response.status_code == 201:
                return response.json()
            logger.error(f"Failed to create warehouse: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error creating warehouse: {e}")
        return None

    # ── Cameras ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_cameras(warehouse_id: Optional[int] = None) -> List[Dict]:
        try:
            url = f"{BACKEND_URL}/cameras"
            params = {}
            if warehouse_id is not None:
                params["warehouse_id"] = warehouse_id
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Failed to fetch cameras: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error fetching cameras: {e}")
        return []

    @staticmethod
    def create_camera(
        warehouse_id: int,
        camera_name: str,
        rtsp_url: str,
        is_storage_camera: bool = True,
        is_active: bool = True,
        coverage_weight: float = 1.0,
        notes: Optional[str] = None,
    ) -> Optional[Dict]:
        try:
            payload = {
                "warehouse_id": warehouse_id,
                "camera_name": camera_name,
                "rtsp_url": rtsp_url,
                "is_storage_camera": is_storage_camera,
                "is_active": is_active,
                "coverage_weight": coverage_weight,
                "notes": notes,
            }
            response = requests.post(f"{BACKEND_URL}/cameras", json=payload, timeout=5)
            if response.status_code == 201:
                return response.json()
            logger.error(f"Failed to create camera: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error creating camera: {e}")
        return None

    # ── Occupancy ────────────────────────────────────────────────────────────

    @staticmethod
    def get_occupancy(warehouse_id: Optional[int] = None) -> List[Dict]:
        try:
            if warehouse_id is not None:
                url = f"{BACKEND_URL}/occupancy/{warehouse_id}"
            else:
                url = f"{BACKEND_URL}/occupancy"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Failed to fetch occupancy: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error fetching occupancy: {e}")
        return []

    @staticmethod
    def get_camera_occupancy(camera_id: int) -> List[Dict]:
        try:
            response = requests.get(
                f"{BACKEND_URL}/occupancy/camera/{camera_id}", timeout=5
            )
            if response.status_code == 200:
                return response.json()
            logger.error(
                f"Failed to fetch camera occupancy: {response.status_code} {response.text}"
            )
        except Exception as e:
            logger.error(f"Error fetching camera occupancy: {e}")
        return []

    @staticmethod
    def trigger_polling() -> bool:
        try:
            response = requests.post(f"{BACKEND_URL}/occupancy/trigger", timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error triggering polling: {e}")
            return False
