# Multi-Warehouse Occupancy Estimation Platform

A production-ready, modular, and scalable platform to estimate space utilization across multiple warehouses using RTSP camera streams, scheduling pipelines, and an abstract AI inference engine interface.

---

## Folder Structure

```
warehouse-occupancy/
├── backend/                  # FastAPI Backend Application
│   ├── app/
│   │   ├── api/              # Routers (Warehouses, Cameras, Occupancy)
│   │   ├── config/           # Pydantic Configuration loading (.env)
│   │   ├── database/         # SQLAlchemy engine and session dependency
│   │   ├── models/           # SQLAlchemy DB models (Warehouse, Camera, Occupancy)
│   │   ├── occupancy/        # Swappable AI Occupancy Engines (SegFormer, DeepLab, U-Net)
│   │   ├── scheduler/        # Background hourly polling runner (APScheduler)
│   │   ├── schemas/          # Pydantic Input/Output validation schemas
│   │   ├── services/         # Encapsulated Business & CRUD logic (Warehouse, Camera, RTSP)
│   │   └── utils/
│   ├── tests/                # Automated pytest integration suites
│   ├── main.py               # Entrypoint, logging, database init, lifespan hooks
│   └── requirements.txt      # Python dependencies
│
├── dashboard/                # Streamlit Analytics Dashboard Application
│   ├── components/           # Shared UI helpers and API client
│   ├── pages/                # Streamlit subviews (Warehouses, Cameras, Analytics)
│   └── Dashboard.py          # Dashboard entrypoint & main KPIs overview
│
├── ml/                       # Machine Learning and AI assets
│   └── README.md             # Model fine-tuning, labeling, and transfer learning documentation
│
├── docker/                   # Docker deployment configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml    # Composed local/production stack
│
└── README.md                 # Project README
```

---

## Getting Started (Local Setup)

### 1. Requirements
* Python 3.10+
* SQLite (default fallback) or PostgreSQL database.

### 2. Installation
Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Run Verification Tests
Verify all API routers, CRUD operations, relationships, cascade deletions, and scheduler connection triggers using pytest:
```bash
source .venv/bin/activate
PYTHONPATH=backend pytest backend/tests/
```

### 4. Run the Backend API
Start the FastAPI server:
```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```
* **Swagger API Documentation** is available at: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation** is available at: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Run the Streamlit Dashboard
Open a new terminal session, activate the virtual environment, and launch the dashboard:
```bash
source .venv/bin/activate
streamlit run dashboard/Dashboard.py --server.port=8501
```
The dashboard will open automatically in your browser at [http://localhost:8501](http://localhost:8501).

---

## Deployment (Docker Compose)

To spin up the database (PostgreSQL), backend server, and dashboard containers simultaneously:

```bash
# From the project root
docker compose -f docker/docker-compose.yml up --build
```

---

## Core Architecture Highlights

1. **RTSP Stream Layer**: Connects to surveillance feeds (supports CP Plus cameras) using OpenCV and captures live video frame buffers on schedule.
2. **AI Inference Interface**: Encapsulates prediction routines inside `BaseOccupancyModel` to allow hot-swapping or fine-tuning models (SegFormer, U-Net, DeepLab) without modifying upstream business logic.
3. **Hourly Scheduler**: Executes an hourly task in the background, connects to cameras, triggers semantic segmentation calculations, and writes utilization logs.
