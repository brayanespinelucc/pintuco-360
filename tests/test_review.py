"""RF-05: permisos, contrato y validación de revisión humana."""
from fastapi.testclient import TestClient

from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
CASE = "2ffb5eb8-47c6-43e5-9322-0086510e2dbc"


def test_anonymous_cannot_access_review():
    assert client.get("/api/v1/revision/bandeja").status_code == 401
    assert client.get(f"/api/v1/revision/solicitudes/{CASE}/detalle").status_code == 401


def test_customer_cannot_approve_or_list_queue():
    async def customer():
        return {"id": CASE, "role": "cliente"}, "jwt"
    app.dependency_overrides[capture.current_user] = customer
    try:
        assert client.get("/api/v1/revision/bandeja").status_code == 403
        r = client.post(f"/api/v1/revision/solicitudes/{CASE}/resolver", json={
            "decision": "aprobar",
            "observaciones": "He estudiado y revisado mi propia solicitud.",
        })
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_advisor_can_read_queue_and_detail(monkeypatch):
    from backend.app.api import review

    async def advisor():
        return {"id": CASE, "role": "especialista_tecnico"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        if table == "rpc/bandeja_revision_tecnica":
            return [{"solicitud_id": CASE, "estado": "radicada", "nombre_empresa": "Horizonte",
                     "nombre_proyecto": "Fachada", "descripcion_libre": "Humedad"}]
        if table == "rpc/detalle_revision_tecnica":
            return {"solicitud": {"id": CASE, "estado": "radicada"},
                    "proyecto": {}, "analisis": {}, "calculo": {},
                    "inventario": {}, "revisiones": []}
        raise AssertionError(table)

    app.dependency_overrides[capture.current_user] = advisor
    monkeypatch.setattr(review, "supabase_rest", fake_rest)
    try:
        inbox = client.get("/api/v1/revision/bandeja")
        assert inbox.status_code == 200
        assert len(inbox.json()) == 1
        detail = client.get(f"/api/v1/revision/solicitudes/{CASE}/detalle")
        assert detail.status_code == 200
        assert detail.json()["solicitud"]["id"] == CASE
    finally:
        app.dependency_overrides.clear()


def test_advisor_registers_decision(monkeypatch):
    from backend.app.api import review
    calls = []

    async def advisor():
        return {"id": CASE, "role": "asesor"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        calls.append(json)
        assert table == "rpc/resolver_revision_tecnica"
        assert json["p_decision"] == "solicitar_correccion"
        assert json["p_correccion_propuesta"]["campo"] == "area_m2"
        return {"solicitud_id": CASE, "decision": "solicitar_correccion",
                "estado_nuevo": "pendiente_informacion"}

    app.dependency_overrides[capture.current_user] = advisor
    monkeypatch.setattr(review, "supabase_rest", fake_rest)
    try:
        r = client.post(f"/api/v1/revision/solicitudes/{CASE}/resolver", json={
            "decision": "solicitar_correccion",
            "observaciones": "Revisar la medición total de la fachada.",
            "correccion_propuesta": {
                "campo": "area_m2", "valor_propuesto": "90.00"
            },
        })
        assert r.status_code == 201
        assert r.json()["estado_nuevo"] == "pendiente_informacion"
        assert len(calls) == 1
    finally:
        app.dependency_overrides.clear()


def test_missing_correction_is_invalid():
    async def advisor():
        return {"id": CASE, "role": "asesor"}, "jwt"
    app.dependency_overrides[capture.current_user] = advisor
    try:
        r = client.post(f"/api/v1/revision/solicitudes/{CASE}/resolver", json={
            "decision": "solicitar_correccion",
            "observaciones": "Se necesita revisar el área por fisuras y humedad.",
        })
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_correction_not_allowed_during_approval():
    async def advisor():
        return {"id": CASE, "role": "asesor"}, "jwt"
    app.dependency_overrides[capture.current_user] = advisor
    try:
        r = client.post(f"/api/v1/revision/solicitudes/{CASE}/resolver", json={
            "decision": "aprobar",
            "observaciones": "Se revisaron los antecedentes y datos de la superficie.",
            "correccion_propuesta": {"campo": "area_m2", "valor_propuesto": "90.00"},
        })
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_client_may_read_detail_if_owned(monkeypatch):
    from backend.app.api import review

    async def customer():
        return {"id": CASE, "role": "cliente"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/detalle_revision_tecnica"
        return {"solicitud": {"id": CASE, "estado": "aprobada"},
                "revisiones": [{"decision": "aprobar", "observaciones": "Revisado"}]}

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(review, "supabase_rest", fake_rest)
    try:
        r = client.get(f"/api/v1/revision/solicitudes/{CASE}/detalle")
        assert r.status_code == 200
        assert r.json()["solicitud"]["estado"] == "aprobada"
    finally:
        app.dependency_overrides.clear()
