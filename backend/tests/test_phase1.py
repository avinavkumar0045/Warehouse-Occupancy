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



def test_warehouse_crud():
    # 1. Create Warehouse
    response = client.post(
        "/api/warehouses",
        json={"name": "Delhi Warehouse", "location": "Delhi NCR", "description": "Main hub for northern region"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Delhi Warehouse"
    assert data["location"] == "Delhi NCR"
    assert "id" in data
    warehouse_id = data["id"]

    # 2. Get Warehouse by ID
    response = client.get(f"/api/warehouses/{warehouse_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Delhi Warehouse"

    # 3. Get all Warehouses
    response = client.get("/api/warehouses")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 4. Update Warehouse
    response = client.put(
        f"/api/warehouses/{warehouse_id}",
        json={"name": "Delhi Super Warehouse", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Delhi Super Warehouse"
    assert response.json()["location"] == "Delhi NCR"  # should remain same

    # 5. Create Camera under this warehouse
    response = client.post(
        "/api/cameras",
        json={
            "warehouse_id": warehouse_id,
            "camera_name": "Gate Camera 1",
            "rtsp_url": "rtsp://192.168.1.100/stream1",
            "is_storage_camera": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    camera_data = response.json()
    assert camera_data["camera_name"] == "Gate Camera 1"
    camera_id = camera_data["id"]

    # 6. Read Cameras
    response = client.get(f"/api/cameras?warehouse_id={warehouse_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == camera_id

    # 7. Delete Camera
    response = client.delete(f"/api/cameras/{camera_id}")
    assert response.status_code == 204

    # Verify camera is deleted
    response = client.get(f"/api/cameras/{camera_id}")
    assert response.status_code == 404

    # 8. Create another Camera to test cascade deletion
    response = client.post(
        "/api/cameras",
        json={
            "warehouse_id": warehouse_id,
            "camera_name": "Storage Camera 2",
            "rtsp_url": "rtsp://192.168.1.101/stream1",
            "is_storage_camera": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    cascade_camera_id = response.json()["id"]

    # Delete Warehouse
    response = client.delete(f"/api/warehouses/{warehouse_id}")
    assert response.status_code == 204

    # Verify Warehouse is deleted
    response = client.get(f"/api/warehouses/{warehouse_id}")
    assert response.status_code == 404

    # Verify Camera is cascade deleted (associated with deleted warehouse)
    response = client.get(f"/api/cameras/{cascade_camera_id}")
    assert response.status_code == 404
