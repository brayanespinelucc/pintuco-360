from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import capture

client = TestClient(app)


def test_capture_requires_login():
    assert client.get("/api/v1/capture/clientes").status_code == 401
    assert client.post("/api/v1/capture/solicitudes", json={
        "proyecto_id": "2ffb5eb8-47c6-43e5-9322-0086510e2dbc",
        "descripcion_libre": "Solicito pintura para una fachada de concreto.",
    }).status_code == 401


def test_only_customer_can_create():
    async def fake_profile():
        return {"id":"2ffb5eb8-47c6-43e5-9322-0086510e2dbc", "role":"logistica"}, "jwt"

    app.dependency_overrides[capture.current_user] = fake_profile
    try:
        r = client.post("/api/v1/capture/clientes", json={
            "nombre_empresa":"Constructora Horizonte","ciudad":"Medellín"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_validation_area():
    payload = {
      "cliente_id":"2ffb5eb8-47c6-43e5-9322-0086510e2dbc",
      "nombre_proyecto":"Fachada de concreto",
      "area_m2":"0.00", "tipo_superficie":"concreto",
      "condicion":"humedad y fisuras", "ambiente":"exterior",
      "color_requerido":"gris",
    }
    assert client.post("/api/v1/capture/proyectos", json=payload).status_code == 422
