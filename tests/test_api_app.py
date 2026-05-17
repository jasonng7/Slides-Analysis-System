import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.app import app


def test_health_endpoint_returns_system_summary():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "slide_count" in payload
    assert "cleanup_policy" in payload


def test_missing_job_returns_404():
    client = TestClient(app)

    response = client.get("/api/jobs/not-a-real-job")

    assert response.status_code == 404
