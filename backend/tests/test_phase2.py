import os
import pytest
from fastapi.testclient import TestClient

# Set environment variable to use an isolated SQLite test database
os.environ["DATABASE_URL"] = "sqlite:///./test_warehouse_occupancy.db"

from app.database.session import Base, engine
from main import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Drop and recreate tables on the app engine to ensure a clean slate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_warehouse_occupancy.db"):
        try:
            os.remove("./test_warehouse_occupancy.db")
        except Exception:
            pass



def test_scheduler_polling_pipeline():
    # 1. Create a warehouse
    response = client.post(
        "/api/warehouses",
        json={"name": "Test Warehouse", "location": "Test Location", "description": "Verification warehouse"},
    )
    assert response.status_code == 201
    warehouse_id = response.json()["id"]

    # 2. Register an ACTIVE camera
    response = client.post(
        "/api/cameras",
        json={
            "warehouse_id": warehouse_id,
            "camera_name": "Active Cam 1",
            "rtsp_url": "rtsp://localhost/test",
            "is_storage_camera": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    camera_id = response.json()["id"]

    # Register an INACTIVE camera (should NOT get readings generated)
    response = client.post(
        "/api/cameras",
        json={
            "warehouse_id": warehouse_id,
            "camera_name": "Inactive Cam 2",
            "rtsp_url": "rtsp://localhost/test2",
            "is_storage_camera": True,
            "is_active": False,
        },
    )
    assert response.status_code == 201
    inactive_camera_id = response.json()["id"]

    # 3. Trigger manual occupancy polling job
    response = client.post("/api/occupancy/trigger")
    assert response.status_code == 200
    assert response.json()["message"] == "Occupancy polling job triggered and executed successfully."

    # 4. Fetch occupancy readings for warehouse
    response = client.get(f"/api/occupancy/{warehouse_id}")
    assert response.status_code == 200
    readings = response.json()
    
    # We should have exactly 1 reading (only for the active camera, not for the inactive one)
    assert len(readings) == 1
    reading = readings[0]
    assert reading["camera_id"] == camera_id
    assert reading["warehouse_id"] == warehouse_id
    assert 40.0 <= reading["occupancy_percentage"] <= 80.0

    # 5. Fetch readings for the inactive camera
    response = client.get(f"/api/occupancy/camera/{inactive_camera_id}")
    assert response.status_code == 200
    assert len(response.json()) == 0
