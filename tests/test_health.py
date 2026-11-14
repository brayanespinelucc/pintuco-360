from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "service": "pintuco-360-api", "version": "0.6.1"
    }


def test_profile_requires_authentication():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_validates_input():
    response = client.post("/api/v1/auth/login", json={"email": "", "password": ""})
    assert response.status_code == 422
