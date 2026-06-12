"""
Camera Health Service

Scheduled every 5 minutes by APScheduler. For each active camera it:
  1. Attempts a lightweight RTSP connection (single-frame probe).
  2. Updates camera_status → ONLINE | OFFLINE | ERROR.
  3. Sets last_successful_capture on success.

Exposed function:
    run_health_checks_job()  — entry-point for the scheduler
    check_camera_health()    — testable per-camera logic
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import cv2
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.camera import Camera

if TYPE_CHECKING:
    pass  # avoid circular imports at runtime

logger = logging.getLogger(__name__)

# Status constants
STATUS_ONLINE  = "ONLINE"
STATUS_OFFLINE = "OFFLINE"
STATUS_ERROR   = "ERROR"

# How long (seconds) to wait for a single RTSP frame before declaring OFFLINE
PROBE_TIMEOUT_SECONDS: float = 5.0


def check_camera_health(db: Session, camera: Camera) -> str:
    """
    Probe a single camera's RTSP stream and persist the result.

    Args:
        db:     Active SQLAlchemy session.
        camera: Camera ORM instance to check.

    Returns:
        One of "ONLINE", "OFFLINE", or "ERROR".
    """
    rtsp_url: str = camera.rtsp_url
    new_status = STATUS_ERROR

    # Mock / localhost URLs — always treat as ONLINE (no real network needed)
    if rtsp_url.startswith("mock://") or "localhost" in rtsp_url or "127.0.0.1" in rtsp_url:
        logger.debug(
            f"Camera Health: Camera '{camera.camera_name}' (ID {camera.id}) "
            "uses mock URL — marking ONLINE."
        )
        new_status = STATUS_ONLINE
        camera.last_successful_capture = datetime.now(timezone.utc)
        camera.camera_status = new_status
        db.add(camera)
        db.commit()
        return new_status

    # Real RTSP probe using OpenCV
    try:
        cap = cv2.VideoCapture(rtsp_url)
        # Give OpenCV time to open the stream
        start = time.monotonic()
        opened = False
        while (time.monotonic() - start) < PROBE_TIMEOUT_SECONDS:
            if cap.isOpened():
                opened = True
                break
            time.sleep(0.2)

        if opened:
            ret, _ = cap.read()
            if ret:
                new_status = STATUS_ONLINE
                camera.last_successful_capture = datetime.now(timezone.utc)
                logger.info(
                    f"Camera Health: Camera '{camera.camera_name}' (ID {camera.id}) → {STATUS_ONLINE}"
                )
            else:
                new_status = STATUS_OFFLINE
                logger.warning(
                    f"Camera Health: Camera '{camera.camera_name}' (ID {camera.id}) stream opened "
                    "but frame read failed → OFFLINE"
                )
        else:
            new_status = STATUS_OFFLINE
            logger.warning(
                f"Camera Health: Camera '{camera.camera_name}' (ID {camera.id}) could not open stream "
                "within timeout → OFFLINE"
            )

        cap.release()

    except Exception as exc:
        new_status = STATUS_ERROR
        logger.error(
            f"Camera Health: Exception while probing camera ID {camera.id} "
            f"('{camera.camera_name}'): {exc}",
            exc_info=False,
        )

    camera.camera_status = new_status
    db.add(camera)
    db.commit()
    return new_status


def run_health_checks_job() -> None:
    """
    APScheduler entry-point.

    Iterates over all active cameras and calls check_camera_health() for each.
    Uses its own DB session that is always closed in the finally block.
    """
    logger.info("Camera Health Job: Starting 5-minute health check run...")
    db: Session = SessionLocal()
    try:
        cameras: list[Camera] = (
            db.query(Camera)
            .filter(Camera.is_active == True)  # noqa: E712
            .all()
        )
        logger.info(f"Camera Health Job: Probing {len(cameras)} active camera(s).")

        online = offline = errors = 0
        for camera in cameras:
            status = check_camera_health(db, camera)
            if status == STATUS_ONLINE:
                online += 1
            elif status == STATUS_OFFLINE:
                offline += 1
            else:
                errors += 1

        logger.info(
            f"Camera Health Job: Completed. "
            f"ONLINE={online}, OFFLINE={offline}, ERROR={errors}."
        )
    except Exception as exc:
        logger.error(f"Camera Health Job: Unexpected error — {exc}", exc_info=True)
    finally:
        db.close()
