# Multi-Warehouse Occupancy Estimation Platform — Architecture

## Overview

This document describes the complete technical architecture of the platform — a production-ready,
modular system for estimating warehouse storage utilisation using CP Plus CCTV streams and AI
semantic segmentation models.

---

## System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT DASHBOARD (Port 8501)                │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐   │
│  │  Home Page  │  │  Camera Mgmt     │  │  Occupancy Analytics   │   │
│  │  KPI Cards  │  │  Registration    │  │  Weighted Charts       │   │
│  │  Quick Run  │  │  Health Status   │  │  Confidence Metrics    │   │
│  └──────┬──────┘  └────────┬─────────┘  └───────────┬────────────┘   │
└─────────│─────────────────│────────────────────────│────────────────┘
          │   HTTP REST      │                        │
          ▼                  ▼                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (Port 8000)                       │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐  │
│  │  Warehouses  │  │   Cameras    │  │       Occupancy            │  │
│  │  Router/API  │  │  Router/API  │  │      Router/API            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────────┘  │
│         │                 │                      │                    │
│  ┌──────▼─────────────────▼──────────────────────▼─────────────────┐ │
│  │               Service Layer (SOLID Principles)                   │ │
│  │  WarehouseService  CameraService  OccupancyService               │ │
│  │  RTSPService       ROIService     CameraHealthService            │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                             │                                         │
│  ┌──────────────────────────▼───────────────────────────────────────┐ │
│  │                   APScheduler (Background)                       │ │
│  │   Job 1: poll_cameras_job      — every hour (RTSP + AI Engine)   │ │
│  │   Job 2: run_health_checks_job — every 5 minutes (RTSP probe)   │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                             │                                         │
│  ┌──────────────────────────▼───────────────────────────────────────┐ │
│  │               AI Occupancy Engine                                │ │
│  │  BaseOccupancyModel (ABC)                                        │ │
│  │   ├── SegFormerOccupancyModel   ← Default (simulation mode)      │ │
│  │   ├── DeepLabOccupancyModel     ← Architecture placeholder       │ │
│  │   └── UNetOccupancyModel        ← Architecture placeholder       │ │
│  │  Returns: PredictionResult (occ%, confidence, version, time_ms) │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│               SQLite / PostgreSQL Database                            │
│  ┌──────────────┐  ┌───────────────────┐  ┌────────────────────────┐ │
│  │  warehouse   │  │      camera       │  │   occupancy_reading    │ │
│  │  id          │  │  id               │  │  id                    │ │
│  │  name        │  │  warehouse_id(FK) │  │  warehouse_id (FK)     │ │
│  │  location    │  │  camera_name      │  │  camera_id (FK)        │ │
│  │  description │  │  rtsp_url         │  │  occupancy_percentage  │ │
│  │  created_at  │  │  is_storage_cam   │  │  confidence_score      │ │
│  └──────────────┘  │  is_active        │  │  processing_time_ms    │ │
│                    │  coverage_weight  │  │  model_version         │ │
│                    │  roi_polygon      │  │  captured_at           │ │
│                    │  camera_status    │  └────────────────────────┘ │
│                    │  last_successful_ │                              │
│                    │  capture          │                              │
│                    │  notes            │                              │
│                    └───────────────────┘                              │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Database Layer (`backend/app/database/`)

| Component | Description |
|---|---|
| `session.py` | SQLAlchemy engine, `SessionLocal` factory, `Base` declarative class, `get_db()` FastAPI dependency |
| `alembic/` | Database migration scripts managed by Alembic |
| SQLite (dev) | Zero-dependency local development via `sqlite:///./warehouse_db.db` |
| PostgreSQL (prod) | Production-grade DB via `postgresql://...` in `.env` |

**Migration workflow:**
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "describe_change"
# Apply all pending migrations
alembic upgrade head
```

---

### 2. Database Models (`backend/app/models/`)

#### `Warehouse`
Core entity representing a physical warehouse facility.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(255) | Unique warehouse name |
| `location` | String(500) | Physical address/zone |
| `description` | Text | Optional notes |
| `created_at` | DateTime | Server-set timestamp |

#### `Camera` (Phase 6 Enhanced)
Represents one CCTV camera stream within a warehouse.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `warehouse_id` | FK → Warehouse | CASCADE delete |
| `camera_name` | String(255) | Human-readable label |
| `rtsp_url` | String(2048) | CP Plus RTSP endpoint |
| `is_storage_camera` | Boolean | Whether to include in occupancy |
| `is_active` | Boolean | Whether scheduler polls this camera |
| `coverage_weight` | Float | Weight for weighted average (default 1.0) |
| `roi_polygon` | JSON | List of `{x, y}` polygon points |
| `camera_status` | String(20) | ONLINE / OFFLINE / ERROR |
| `last_successful_capture` | DateTime | Timestamp of last successful RTSP read |
| `notes` | Text | Operator notes |
| `created_at` | DateTime | Server-set timestamp |

#### `OccupancyReading` (Phase 6 Enhanced)
Persists each AI estimation event.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `warehouse_id` | FK → Warehouse | CASCADE delete |
| `camera_id` | FK → Camera | CASCADE delete |
| `occupancy_percentage` | Float | Estimated occupancy 0–100 |
| `confidence_score` | Float | Model confidence 0–1 |
| `processing_time_ms` | Integer | Inference wall time |
| `model_version` | String(50) | e.g. `segformer-b0-v1.0.0` |
| `captured_at` | DateTime | Server-set timestamp |

---

### 3. API Layer (`backend/app/api/`)

All endpoints are prefixed `/api`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/warehouses` | List all warehouses |
| POST | `/api/warehouses` | Register warehouse |
| GET | `/api/cameras` | List cameras (optional `warehouse_id` filter) |
| POST | `/api/cameras` | Register camera |
| GET | `/api/occupancy` | List all readings |
| GET | `/api/occupancy/{warehouse_id}` | Readings for one warehouse |
| GET | `/api/occupancy/camera/{camera_id}` | Readings for one camera |
| POST | `/api/occupancy/trigger` | Trigger polling job immediately |
| GET | `/` | Health check |

Interactive docs: **http://localhost:8000/docs**

---

### 4. RTSP Layer (`backend/app/services/rtsp_service.py`)

Handles CP Plus CCTV stream connections using OpenCV.

**Behaviour:**
- If the RTSP URL contains `mock://`, `localhost`, or `127.0.0.1` → mock mode (no real connection).
- Real RTSP: `cv2.VideoCapture(rtsp_url)` → single frame captured → stream released.
- On connection failure → falls back to mock mode (generates synthetic frame), never crashes the job.

**Mock frame:** 640×480 BGR image with simulated boxes, floor, and text overlay. Used for development and testing without physical cameras.

---

### 5. ROI Service (`backend/app/services/roi_service.py`)

Manages polygon-based Region of Interest masking on camera frames.

```python
from app.services.roi_service import validate_polygon, draw_polygon, crop_to_roi, calculate_roi_area

roi = [{"x": 50, "y": 100}, {"x": 590, "y": 100}, {"x": 590, "y": 400}, {"x": 50, "y": 400}]

validate_polygon(roi)          # → True
draw_polygon(frame, roi)       # → frame copy with green border drawn
crop_to_roi(frame, roi)        # → frame with pixels outside ROI zeroed
calculate_roi_area(roi, shape) # → 0.742 (fraction of total frame)
```

**Storage:** `camera.roi_polygon` column stores the JSON list of `{x, y}` dicts.

---

### 6. Camera Health Service (`backend/app/services/camera_health_service.py`)

Runs every **5 minutes** via APScheduler.

**Per-camera logic:**
1. Mock URLs → always `ONLINE`, `last_successful_capture` updated.
2. Real URLs → `cv2.VideoCapture` probe with `PROBE_TIMEOUT_SECONDS = 5.0`.
3. Frame read success → `ONLINE`, timestamp updated.
4. Stream opened but no frame → `OFFLINE`.
5. Stream not opened within timeout → `OFFLINE`.
6. Exception → `ERROR`.

All status changes are committed to the database immediately.

---

### 7. AI Occupancy Engine (`backend/app/occupancy/`)

#### Class Hierarchy

```
BaseOccupancyModel (ABC)  ← app/occupancy/models/base_model.py
  ├── SegFormerOccupancyModel  ← default; brightness simulation in MVP
  ├── DeepLabOccupancyModel    ← placeholder; ~58.5% simulated
  └── UNetOccupancyModel       ← placeholder; ~62.4% simulated
```

#### PredictionResult Dataclass

```python
@dataclass
class PredictionResult:
    occupancy_percentage: float   # 0.0–100.0
    confidence_score:     float   # 0.0–1.0
    model_version:        str     # e.g. "segformer-b0-v1.0.0"
    processing_time_ms:   int     # wall-clock inference time
    metadata:             dict    # model-specific extras
```

#### Factory

```python
model = get_occupancy_model("segformer")  # | "deeplab" | "unet"
result = model.predict(frame)             # → PredictionResult
```

#### Future SegFormer Integration Path

When real HuggingFace weights are available:
1. In `SegFormerOccupancyModel.load_model()`: load `SegformerForSemanticSegmentation`.
2. In `predict()`: replace the brightness heuristic with real forward pass + argmax mask.
3. Map `STORAGE_CLASS_ID` to the appropriate semantic class for racking/pallets.
4. Update `MODEL_VERSION = "segformer-b0-finetuned-v2.0.0"`.

---

### 8. Scheduler (`backend/app/scheduler/scheduler_service.py`)

Uses **APScheduler 3.x** with a `BackgroundScheduler`.

| Job | Trigger | Description |
|---|---|---|
| `poll_cameras_job` | CronTrigger (minute=0) | Every hour — RTSP capture + AI inference + DB persist |
| `run_health_checks_job` | IntervalTrigger (minutes=5) | Every 5 min — RTSP probe + status update |

**Polling job flow:**
```
For each active camera:
  1. RTSPService.connect(rtsp_url)
  2. RTSPService.capture_frame()
  3. RTSPService.disconnect()
  4. If roi_polygon set → crop_to_roi(frame, roi)
  5. model.predict(frame) → PredictionResult
  6. OccupancyService.create_reading(db, schema with all Phase 6 fields)
```

---

### 9. Logging (`backend/app/utils/logger.py`)

Centralized rotating log system with 4 channels:

| File | Content |
|---|---|
| `logs/application.log` | General app lifecycle |
| `logs/scheduler.log` | APScheduler job activity |
| `logs/occupancy.log` | AI model output events |
| `logs/camera.log` | RTSP and health check events |

**Configuration:** 10 MB per file, 5 rotated backups, UTF-8 encoding.

Call `setup_logging()` once at application startup (already integrated into `main.py`).

---

### 10. Weighted Occupancy Formula

The Streamlit occupancy dashboard computes the **weighted average** across all active storage cameras:

$$\text{Warehouse Occupancy} = \frac{\sum_{i=1}^{N} w_i \times o_i}{\sum_{i=1}^{N} w_i}$$

Where:
- $w_i$ = `camera.coverage_weight` for camera $i$
- $o_i$ = latest `occupancy_percentage` reading for camera $i$
- $N$ = number of active storage cameras with readings

This allows operators to assign higher weights to cameras covering larger storage zones.

---

## Directory Structure

```
warehouse-occupancy/
├── backend/
│   ├── main.py                          # FastAPI app entry-point
│   ├── .env                             # Environment config (DB URL, etc.)
│   ├── alembic.ini                      # Alembic config
│   ├── alembic/versions/                # Auto-generated migration scripts
│   ├── logs/                            # Rotating log files (auto-created)
│   └── app/
│       ├── api/                         # FastAPI routers
│       │   ├── warehouses.py
│       │   ├── cameras.py
│       │   └── occupancy.py
│       ├── config/config.py             # Pydantic settings
│       ├── database/session.py          # SQLAlchemy engine + Base
│       ├── models/                      # ORM models
│       │   ├── warehouse.py
│       │   ├── camera.py                # Phase 6: weight, ROI, status
│       │   └── occupancy.py             # Phase 6: confidence, version, time
│       ├── schemas/                     # Pydantic request/response schemas
│       ├── services/
│       │   ├── warehouse_service.py
│       │   ├── camera_service.py
│       │   ├── occupancy_service.py
│       │   ├── rtsp_service.py          # OpenCV RTSP + mock mode
│       │   ├── roi_service.py           # Phase 6: polygon masking
│       │   └── camera_health_service.py # Phase 6: 5-min health probe
│       ├── occupancy/
│       │   ├── engine.py                # Model factory
│       │   └── models/
│       │       ├── base_model.py        # ABC + PredictionResult
│       │       ├── segformer_model.py   # Phase 6: default model
│       │       ├── deeplab_model.py     # Phase 6: placeholder
│       │       └── unet_model.py        # Phase 6: placeholder
│       ├── scheduler/
│       │   └── scheduler_service.py     # APScheduler jobs
│       └── utils/
│           └── logger.py               # Phase 6: rotating logger
├── dashboard/
│   ├── Dashboard.py                     # Streamlit home page
│   ├── components/api_client.py         # HTTP client
│   └── pages/
│       ├── 1_Warehouses.py
│       ├── 2_Cameras.py                # Phase 6: health, weight, notes
│       └── 3_Occupancy_Dashboard.py    # Phase 6: weighted avg, confidence
├── ml/
│   └── test_segformer.py               # Phase 6: pipeline test script
├── docker/                             # Docker configs (future)
└── docs/
    └── ARCHITECTURE.md                 # This document
```

---

## Development Quickstart

### Prerequisites
- Python 3.10+
- Virtual environment (`.venv/`)

### Start Backend
```bash
cd backend
alembic upgrade head          # apply DB migrations
uvicorn main:app --reload --port 8000
```

### Start Dashboard
```bash
cd dashboard
streamlit run Dashboard.py --server.port 8501
```

### Run ML Pipeline Test
```bash
cd warehouse-occupancy
python -m ml.test_segformer
```

### Switch Database
Edit `backend/.env`:
```env
# SQLite (development — zero-dependency)
DATABASE_URL=sqlite:///./warehouse_db.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:pass@localhost:5432/warehouse_db
```

---

## Scaling Considerations

| Concern | Current Approach | Future Path |
|---|---|---|
| Multi-warehouse | All warehouses in single DB | Partition by warehouse_id; read-replicas |
| Camera count | Sequential polling in scheduler | Concurrent workers (ThreadPoolExecutor) |
| AI model | Single SegFormer instance | Model pool per GPU; async inference queue |
| Storage | SQLite/PostgreSQL | TimescaleDB for time-series occupancy data |
| Deployment | Local uvicorn | Docker + Kubernetes; Gunicorn workers |
| Image archiving | Not implemented | S3/GCS with lifecycle policies |

---

*Document version: Phase 6 — Production Readiness & AI Integration Preparation*
