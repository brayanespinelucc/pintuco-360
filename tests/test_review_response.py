"""RF-05.1: respuesta del cliente, permisos y traspaso a asesor."""
from fastapi.testclient import TestClient

from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
CASE = "2ffb5eb8-47c6-43e5-9322-0086510e2dbc"


def test_anonymous_cannot_send_customer_response():
    response = client.post(
        f"/api/v1/revision/solicitudes/{CASE}/responder",
        json={"respuesta": "Envío las mediciones pendientes de la fachada."},
    )
    assert response.status_code == 401


def test_specialist_cannot_impersonate_customer():
    async def specialist():
        return {"id": CASE, "role": "especialista_tecnico"}, "jwt"

    app.dependency_overrides[capture.current_user] = specialist
    try:
        response = client.post(
            f"/api/v1/revision/solicitudes/{CASE}/responder",
            json={"respuesta": "Intento de responder como especialista técnico."},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_client_response_requires_nontrivial_text():
    async def owner():
        return {"id": CASE, "role": "cliente"}, "jwt"

    app.dependency_overrides[capture.current_user] = owner
    try:
        response = client.post(
            f"/api/v1/revision/solicitudes/{CASE}/responder",
            json={"respuesta": "   dato   "},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_client_response_calls_secure_rpc_and_returns_new_state(monkeypatch):
    from backend.app.api import review

    async def owner():
        return {"id": CASE, "role": "cliente"}, "jwt"

    calls = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        calls.append((method, table, json))
        assert table == "rpc/responder_revision_tecnica"
        assert json == {
            "p_solicitud_id": CASE,
            "p_respuesta": "La fachada está expuesta al agua desde la cubierta.",
        }
        return {
            "id": "21989b13-4d65-41ad-a55f-56baf8e54bde",
            "solicitud_id": CASE,
            "revision_id": "2334ab60-847b-47fb-9fe7-c8d6bc1490b1",
            "respuesta": json["p_respuesta"],
            "estado_anterior": "pendiente_informacion",
            "estado_nuevo": "en_revision_tecnica",
        }

    app.dependency_overrides[capture.current_user] = owner
    monkeypatch.setattr(review, "supabase_rest", fake_rest)
    try:
        response = client.post(
            f"/api/v1/revision/solicitudes/{CASE}/responder",
            json={"respuesta": "  La fachada está expuesta al agua desde la cubierta.  "},
        )
        assert response.status_code == 201, response.text
        assert response.json()["estado_nuevo"] == "en_revision_tecnica"
        assert len(calls) == 1
    finally:
        app.dependency_overrides.clear()


def test_other_customer_data_not_accessible_from_detail(monkeypatch):
    from backend.app.api import review
    from fastapi import HTTPException

    async def other_client():
        return {"id": "862b6b9f-c37b-4bc1-9bb3-8829db33f5c7", "role": "cliente"}, "jwt"

    async def fake_denied(*args, **kwargs):
        raise HTTPException(status_code=403, detail="No tienes permisos.")

    app.dependency_overrides[capture.current_user] = other_client
    monkeypatch.setattr(review, "supabase_rest", fake_denied)
    try:
        response = client.get(f"/api/v1/revision/solicitudes/{CASE}/detalle")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
