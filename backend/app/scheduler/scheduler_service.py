"""
APScheduler Service — manages all background jobs.

Jobs registered:
  1. poll_cameras_job          — every hour on the hour (occupancy estimation)
  2. run_health_checks_job     — every 5 minutes (camera RTSP health probe)

The scheduler is a module-level singleton started by FastAPI's lifespan handler.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.camera_service import CameraService
from app.services.occupancy_service import OccupancyService
from app.schemas.occupancy import OccupancyReadingCreate

logger = logging.getLogger(__name__)

# Module-level scheduler singleton
scheduler = BackgroundScheduler()


# ── Job 1: Hourly Occupancy Estimation ───────────────────────────────────────

def poll_cameras_job() -> None:
    """
    Background job — runs every hour.

    Steps:
      1. Fetch all active cameras.
      2. Capture a frame via RTSPService.
      3. Run AI occupancy prediction (returns PredictionResult).
      4. Apply ROI crop if the camera has an roi_polygon configured.
      5. Persist the enriched OccupancyReading to the database.
    """
    from app.services.rtsp_service import RTSPService
    from app.services.roi_service import crop_to_roi, validate_polygon
    from app.occupancy.engine import get_occupancy_model

    logger.info("Hourly Job: Starting camera occupancy estimation...")

    db: Session = SessionLocal()
    try:
        active_cameras = CameraService.get_active_cameras(db)
        logger.info(f"Hourly Job: {len(active_cameras)} active camera(s) found.")

        if not active_cameras:
            logger.info("Hourly Job: No active cameras — skipping.")
            return

        model = get_occupancy_model("segformer")

        for camera in active_cameras:
            try:
                logger.info(
                    f"Hourly Job: Processing camera '{camera.camera_name}' (ID {camera.id})."
                )

                # 1. Capture frame
                rtsp = RTSPService()
                rtsp.connect(camera.rtsp_url)
                frame = rtsp.capture_frame()
                rtsp.disconnect()

                # 2. Apply ROI mask if configured
                roi = camera.roi_polygon  # JSON list of {x,y} dicts or None
                if roi and validate_polygon(roi):
                    logger.info(
                        f"Hourly Job: Applying ROI polygon to camera ID {camera.id}."
                    )
                    frame = crop_to_roi(frame, roi)

                # 3. Run inference — returns PredictionResult
                result = model.predict(frame)

                # 4. Persist reading
                reading_schema = OccupancyReadingCreate(
                    warehouse_id=camera.warehouse_id,
                    camera_id=camera.id,
                    occupancy_percentage=result.occupancy_percentage,
                    confidence_score=result.confidence_score,
                    processing_time_ms=result.processing_time_ms,
                    model_version=result.model_version,
                )
                reading = OccupancyService.create_reading(db, reading_schema)
                logger.info(
                    f"Hourly Job: Saved reading ID {reading.id} — "
                    f"{result.occupancy_percentage}% occupancy, "
                    f"confidence={result.confidence_score}, "
                    f"model={result.model_version}, "
                    f"time={result.processing_time_ms}ms "
                    f"(camera='{camera.camera_name}', weight={camera.coverage_weight})."
                )

            except Exception as cam_exc:
                logger.error(
                    f"Hourly Job: Error processing camera ID {camera.id}: {cam_exc}",
                    exc_info=True,
                )
                continue  # don't abort the whole job if one camera fails

        logger.info("Hourly Job: Occupancy estimation task completed.")

    except Exception as exc:
        logger.error(f"Hourly Job: Unexpected error — {exc}", exc_info=True)
    finally:
        db.close()


# ── Scheduler Lifecycle ────────────────────────────────────────────────────────

def start_scheduler() -> None:
    """
    Start the APScheduler and register all background jobs.
    Called once from FastAPI's lifespan startup handler.
    """
    from app.services.camera_health_service import run_health_checks_job

    if scheduler.running:
        logger.warning("Scheduler: start_scheduler() called but scheduler already running.")
        return

    # Job 1: Hourly occupancy estimation
    scheduler.add_job(
        poll_cameras_job,
        trigger=CronTrigger(minute=0),   # every hour on the :00
        id="hourly_camera_occupancy_polling",
        name="Poll active cameras for occupancy hourly",
        replace_existing=True,
    )

    # Job 2: 5-minute camera health checks
    scheduler.add_job(
        run_health_checks_job,
        trigger=IntervalTrigger(minutes=5),
        id="five_min_camera_health_check",
        name="Camera RTSP health check every 5 minutes",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "APScheduler started. Jobs registered: "
        "[hourly_occupancy_polling, 5min_camera_health_check]."
    )


def shutdown_scheduler() -> None:
    """
    Gracefully shut down the APScheduler.
    Called from FastAPI's lifespan shutdown handler.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down successfully.")
