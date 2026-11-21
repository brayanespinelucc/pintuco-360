"""RF-07: roles, contracts, transitions, tracking and photo access."""
from fastapi.testclient import TestClient
from fastapi import HTTPException

from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
CASE = "c3eff887-7320-4e96-bee5-ab0208aabc61"
APP_ID = "6e69acf1-976a-4f6a-b890-202a32a42191"
EVENT_ID = "98e408ad-a910-4d4c-a8de-ff48b1fbdc8d"
WORKER = "d99d9b63-54a7-4b8b-adb8-15a8e7c6adc1"


def test_authentication_required():
    assert client.get("/api/v1/campo/aplicaciones").status_code == 401
    assert client.get("/api/v1/campo/aplicadores").status_code == 401
    assert client.get("/api/v1/campo/elegibles").status_code == 401


def test_customer_cannot_assign_or_record_activity():
    async def customer():
        return {"id": CASE, "role": "cliente"}, "jwt"
    app.dependency_overrides[capture.current_user] = customer
    try:
        assert client.get("/api/v1/campo/elegibles").status_code == 403
        assert client.get("/api/v1/campo/aplicadores").status_code == 403
        a = client.post(
            f"/api/v1/campo/solicitudes/{CASE}/asignar",
            json={"aplicador_id": WORKER, "observaciones": "Un cliente no puede asignar trabajos."},
        )
        assert a.status_code == 403
        b = client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/eventos",
            json={"tipo": "inicio", "observaciones": "Un cliente no puede iniciar trabajos."},
        )
        assert b.status_code == 403
        c = client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/evidencias",
            data={"observaciones": "No puede subir fotos."},
            files={"archivo": ("prueba.png", b"not image", "image/png")},
        )
        assert c.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_logistics_assigns_authorized_applicator(monkeypatch):
    from backend.app.api import field

    async def logistics():
        return {"id": CASE, "role": "logistica"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert method == "POST"
        if table == "rpc/campo_aplicadores":
            return [{"id": WORKER, "nombre": "Aplicador académico"}]
        if table == "rpc/campo_elegibles":
            return [{"solicitud_id": CASE, "nombre_proyecto": "Fachada"}]
        if table == "rpc/campo_asignar":
            assert json == {
                "p_solicitud_id": CASE,
                "p_aplicador_id": WORKER,
                "p_observaciones": "Asignación de trabajo posterior a despacho académico.",
            }
            return {"id": APP_ID, "solicitud_id": CASE, "aplicador_id": WORKER, "estado": "asignada"}
        raise AssertionError(table)

    app.dependency_overrides[capture.current_user] = logistics
    monkeypatch.setattr(field, "supabase_rest", fake_rest)
    try:
        assert client.get("/api/v1/campo/aplicadores").status_code == 200
        assert client.get("/api/v1/campo/elegibles").status_code == 200
        resp = client.post(
            f"/api/v1/campo/solicitudes/{CASE}/asignar",
            json={
                "aplicador_id": WORKER,
                "observaciones": "Asignación de trabajo posterior a despacho académico.",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["estado"] == "asignada"
    finally:
        app.dependency_overrides.clear()


def test_applicator_records_progress_and_incident(monkeypatch):
    from backend.app.api import field

    async def applicator():
        return {"id": WORKER, "role": "aplicador"}, "jwt"

    seen = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/campo_evento"
        seen.append(json)
        return {
            "estado_aplicacion": "en_ejecucion",
            "avance_pct": json["p_avance_pct"] if json["p_avance_pct"] is not None else 35,
        }

    app.dependency_overrides[capture.current_user] = applicator
    monkeypatch.setattr(field, "supabase_rest", fake_rest)
    try:
        a = client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/eventos",
            json={"tipo": "avance", "avance_pct": 35,
                  "observaciones": "Se preparó la superficie y se registró un avance parcial."},
        )
        assert a.status_code == 201
        b = client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/eventos",
            json={"tipo": "incidencia",
                  "observaciones": "Se detectó una zona húmeda que debe inspeccionarse."},
        )
        assert b.status_code == 201
        assert seen[0]["p_tipo"] == "avance"
        assert seen[0]["p_avance_pct"] == 35
        assert seen[1]["p_tipo"] == "incidencia"
        assert seen[1]["p_avance_pct"] is None
    finally:
        app.dependency_overrides.clear()


def test_progress_validation():
    async def applicator():
        return {"id": WORKER, "role": "aplicador"}, "jwt"
    app.dependency_overrides[capture.current_user] = applicator
    try:
        bad = [
            {"tipo": "avance", "observaciones": "Sin porcentaje no es válido."},
            {"tipo": "inicio", "avance_pct": 5, "observaciones": "Inicio con porcentaje es inválido."},
            {"tipo": "avance", "avance_pct": 100,
             "observaciones": "El cien por ciento requiere finalización."},
            {"tipo": "incidencia", "observaciones": "    "},
        ]
        for payload in bad:
            resp = client.post(f"/api/v1/campo/aplicaciones/{APP_ID}/eventos", json=payload)
            assert resp.status_code == 422, resp.text
    finally:
        app.dependency_overrides.clear()


def test_tracking_is_only_for_allowed_roles_and_database_scopes(monkeypatch):
    from backend.app.api import field

    async def customer():
        return {"id": CASE, "role": "cliente"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/campo_listar"
        return [{"id": APP_ID, "estado": "en_ejecucion", "avance_pct": 35, "bitacora": []}]

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(field, "supabase_rest", fake_rest)
    try:
        resp = client.get("/api/v1/campo/aplicaciones")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_private_photo_rejects_unlisted_and_wrong_roles(monkeypatch):
    from backend.app.api import field

    async def customer():
        return {"id": CASE, "role": "cliente"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/campo_listar"
        return []

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(field, "supabase_rest", fake_rest)
    try:
        resp = client.get(f"/api/v1/campo/aplicaciones/{APP_ID}/evidencias/{EVENT_ID}/imagen")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()
