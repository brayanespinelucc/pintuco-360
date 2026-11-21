"""RF-04: permisos y contrato de evaluación de disponibilidad."""
from fastapi.testclient import TestClient

from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
REQUEST_ID = "2ffb5eb8-47c6-43e5-9322-0086510e2dbc"
CALC_ID = "fe703536-07ad-44f1-b4d3-331a835591a1"


def test_anonymous_cannot_see_evaluations():
    assert client.get(
        f"/api/v1/inventario/solicitudes/{REQUEST_ID}/evaluaciones"
    ).status_code == 401


def test_logistica_cannot_invoke_client_evaluation():
    async def logistica():
        return {"id": REQUEST_ID, "role": "logistica"}, "jwt"

    app.dependency_overrides[capture.current_user] = logistica
    try:
        response = client.post(
            f"/api/v1/inventario/solicitudes/{REQUEST_ID}/evaluar",
            json={"calculo_id": CALC_ID},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_evaluation_checks_calculation_belongs_to_request(monkeypatch):
    from backend.app.api import inventory

    async def customer():
        return {"id": REQUEST_ID, "role": "cliente"}, "jwt"

    async def fake_find(request_id, token):
        return {"id": str(request_id)}, {"id": REQUEST_ID}

    queries = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        queries.append((method, table, json))
        if table == "calculos_materiales":
            return []
        raise AssertionError(f"No debe consultar RPC si no existe cálculo: {table}")

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(inventory, "_find_request", fake_find)
    monkeypatch.setattr(inventory, "supabase_rest", fake_rest)
    try:
        response = client.post(
            f"/api/v1/inventario/solicitudes/{REQUEST_ID}/evaluar",
            json={"calculo_id": CALC_ID},
        )
        assert response.status_code == 404
        assert len(queries) == 1
    finally:
        app.dependency_overrides.clear()


def test_evaluation_returns_persisted_fefo_proposal(monkeypatch):
    from backend.app.api import inventory

    async def customer():
        return {"id": REQUEST_ID, "role": "cliente"}, "jwt"

    async def fake_find(request_id, token):
        return {"id": str(request_id)}, {"id": REQUEST_ID}

    queries = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        queries.append((method, table, json))
        if table == "calculos_materiales":
            return [{"id": CALC_ID, "solicitud_id": REQUEST_ID, "envases": 5}]
        if table == "rpc/evaluar_disponibilidad_calculo":
            assert json == {"p_calculo_id": CALC_ID}
            return {
                "id": "e4e8a23c-0f2e-4519-9405-572e0e4e4ed0",
                "calculo_id": CALC_ID,
                "solicitud_id": REQUEST_ID,
                "decision": "inventario_disponible",
                "envases_requeridos": 5,
                "envases_disponibles": 7,
                "envases_propuestos": 5,
                "envases_faltantes": 0,
                "es_provisional": True,
                "requiere_revision_humana": True,
                "propuestas_lotes": [
                    {"codigo_lote": "LOT-DEMO-MDE-01", "envases_propuestos": 3},
                    {"codigo_lote": "LOT-DEMO-BEL-02", "envases_propuestos": 2},
                ],
            }
        raise AssertionError(table)

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(inventory, "_find_request", fake_find)
    monkeypatch.setattr(inventory, "supabase_rest", fake_rest)
    try:
        response = client.post(
            f"/api/v1/inventario/solicitudes/{REQUEST_ID}/evaluar",
            json={"calculo_id": CALC_ID},
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["envases_propuestos"] == 5
        assert payload["envases_faltantes"] == 0
        assert payload["es_provisional"] is True
        assert all(table not in ("lotes_inventario", "bodegas") for _, table, _ in queries)
    finally:
        app.dependency_overrides.clear()
