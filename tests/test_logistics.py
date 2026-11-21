"""RF-06: autorización, RPC, reglas de reserva y flujo de operaciones."""
from fastapi.testclient import TestClient
from fastapi import HTTPException

from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
CASE_ID = "c3eff887-7320-4e96-bee5-ab0208aabc61"
ORDER_ID = "dced1d68-0d47-4fa1-961a-251c9995378e"


def test_requires_authentication():
    assert client.get("/api/v1/logistica/bandeja").status_code == 401
    assert client.get("/api/v1/logistica/ordenes").status_code == 401
    assert client.post(
        f"/api/v1/logistica/solicitudes/{CASE_ID}/reservar",
        json={"observaciones": "Reserva de prueba para validar autorización."},
    ).status_code == 401


def test_customer_cannot_reserve_or_dispatch():
    async def customer():
        return {"id": CASE_ID, "role": "cliente"}, "jwt"
    app.dependency_overrides[capture.current_user] = customer
    try:
        assert client.get("/api/v1/logistica/bandeja").status_code == 403
        resp = client.post(
            f"/api/v1/logistica/solicitudes/{CASE_ID}/reservar",
            json={"observaciones": "Intento inválido de reserva del cliente."},
        )
        assert resp.status_code == 403
        resp = client.post(
            f"/api/v1/logistica/ordenes/{ORDER_ID}/accion",
            json={"accion": "despachar", "observaciones": "Cliente no puede despachar."},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_specialist_has_no_logistics_privileges():
    async def specialist():
        return {"id": CASE_ID, "role": "especialista_tecnico"}, "jwt"
    app.dependency_overrides[capture.current_user] = specialist
    try:
        assert client.get("/api/v1/logistica/ordenes").status_code == 403
        assert client.get("/api/v1/logistica/bandeja").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_customer_can_track_only_own_orders_as_returned_from_rpc(monkeypatch):
    from backend.app.api import logistics

    async def customer():
        return {"id": CASE_ID, "role": "cliente"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/listar_ordenes_logisticas"
        return [{"id": ORDER_ID, "estado": "reservada", "envases_requeridos": 3}]

    app.dependency_overrides[capture.current_user] = customer
    monkeypatch.setattr(logistics, "supabase_rest", fake_rest)
    try:
        resp = client.get("/api/v1/logistica/ordenes")
        assert resp.status_code == 200
        assert resp.json()[0]["estado"] == "reservada"
    finally:
        app.dependency_overrides.clear()


def test_operator_can_reserve_and_process_order(monkeypatch):
    from backend.app.api import logistics

    async def operator():
        return {"id": CASE_ID, "role": "logistica"}, "jwt"

    calls = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        calls.append((table, json))
        if table == "rpc/bandeja_logistica":
            return [{"solicitud_id": CASE_ID, "envases_requeridos": 3}]
        if table == "rpc/reservar_logistica":
            assert json["p_solicitud_id"] == CASE_ID
            assert len(json["p_observaciones"]) >= 10
            return {"id": ORDER_ID, "solicitud_id": CASE_ID,
                    "estado": "reservada", "envases_requeridos": 3}
        if table == "rpc/accion_logistica":
            assert json["p_orden_id"] == ORDER_ID
            assert json["p_accion"] in ("preparar", "despachar", "cancelar")
            return {"id": ORDER_ID, "estado": "preparada"}
        raise AssertionError(table)

    app.dependency_overrides[capture.current_user] = operator
    monkeypatch.setattr(logistics, "supabase_rest", fake_rest)
    try:
        assert client.get("/api/v1/logistica/bandeja").status_code == 200
        r = client.post(
            f"/api/v1/logistica/solicitudes/{CASE_ID}/reservar",
            json={"observaciones": "Reserva académica del primer lote autorizado."},
        )
        assert r.status_code == 201
        assert r.json()["envases_requeridos"] == 3
        a = client.post(
            f"/api/v1/logistica/ordenes/{ORDER_ID}/accion",
            json={"accion": "preparar", "observaciones": "Se revisaron los tres envases."},
        )
        assert a.status_code == 200
        assert a.json()["estado"] == "preparada"
        assert len(calls) == 3
    finally:
        app.dependency_overrides.clear()


def test_validation_prevents_invalid_or_empty_operation():
    async def operator():
        return {"id": CASE_ID, "role": "logistica"}, "jwt"
    app.dependency_overrides[capture.current_user] = operator
    try:
        r = client.post(
            f"/api/v1/logistica/ordenes/{ORDER_ID}/accion",
            json={"accion": "transferir", "observaciones": "Operación no permitida."},
        )
        assert r.status_code == 422
        r = client.post(
            f"/api/v1/logistica/ordenes/{ORDER_ID}/accion",
            json={"accion": "preparar", "observaciones": "   "},
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_insufficient_stock_maps_to_conflict(monkeypatch):
    from backend.app.api import logistics

    async def operator():
        return {"id": CASE_ID, "role": "logistica"}, "jwt"

    async def fail_rest(method, table, token, *, params=None, json=None):
        raise HTTPException(status_code=409, detail="Estado incompatible")

    app.dependency_overrides[capture.current_user] = operator
    monkeypatch.setattr(logistics, "supabase_rest", fail_rest)
    try:
        resp = client.post(
            f"/api/v1/logistica/solicitudes/{CASE_ID}/reservar",
            json={"observaciones": "Intento de reserva sin cantidades suficientes."},
        )
        assert resp.status_code == 409
        assert "No se pudo reservar" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
