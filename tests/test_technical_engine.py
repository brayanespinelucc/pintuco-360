from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import capture
from backend.app.services.technical_engine import (
    calcular_materiales, motivos_revision, validar_compatibilidad,
)

client = TestClient(app)
REQUEST_ID = "2ffb5eb8-47c6-43e5-9322-0086510e2dbc"
PRODUCT_ID = "d4b29936-e985-4b6d-af82-d675a06a1233"


def test_caso_base_85_metros():
    resultado = calcular_materiales(
        area_m2="85.00",
        rendimiento_m2_litro_mano="10.000",
        manos=2,
        desperdicio_pct="15.00",
        presentacion_litros="4.000",
    )
    assert Decimal(resultado["litros_teoricos"]) == Decimal("17.000")
    assert Decimal(resultado["litros_con_desperdicio"]) == Decimal("19.550")
    assert resultado["envases"] == 5
    assert Decimal(resultado["litros_comerciales"]) == Decimal("20.000")


def test_redondeo_envases_antes_de_redondear_litros():
    resultado = calcular_materiales(
        area_m2="20.0001", rendimiento_m2_litro_mano=10,
        manos=1, desperdicio_pct=0, presentacion_litros=2,
    )
    assert resultado["envases"] == 2


def test_area_invalida():
    with pytest.raises(HTTPException) as exc:
        calcular_materiales(
            area_m2=0, rendimiento_m2_litro_mano=10,
            manos=2, desperdicio_pct=15, presentacion_litros=4,
        )
    assert exc.value.status_code == 422


def test_producto_incompatible():
    with pytest.raises(HTTPException) as exc:
        validar_compatibilidad(
            {"tipo_superficie": "madera", "ambiente": "interior"},
            {"superficie": "concreto", "ambiente": "exterior"},
        )
    assert exc.value.status_code == 422


def test_revision_tecnica_no_delegada_a_gemini():
    motivos = motivos_revision("Necesitamos reparar fisuras", {"condicion": "humedad"}, False)
    assert len(motivos) >= 1


def test_catalogo_requiere_login():
    assert client.get("/api/v1/tecnico/catalogo").status_code == 401


def test_logistica_no_puede_calcular():
    async def fake_user():
        return {"id": REQUEST_ID, "role": "logistica"}, "jwt"

    app.dependency_overrides[capture.current_user] = fake_user
    try:
        response = client.post(
            f"/api/v1/tecnico/solicitudes/{REQUEST_ID}/calcular",
            json={"producto_id": PRODUCT_ID},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_api_con_guarda_cantidades_del_catalogo(monkeypatch):
    from backend.app.api import technical

    async def fake_user():
        return {"id": REQUEST_ID, "role": "cliente"}, "jwt"

    async def fake_request(request_id, token):
        return (
            {"id": str(request_id), "descripcion_libre": "Fachada con humedad y fisuras"},
            {"id": REQUEST_ID, "area_m2": "85.00",
             "tipo_superficie": "Concreto", "condicion": "humedad y fisuras",
             "ambiente": "exterior"},
        )

    async def fake_rest(method, table, token, *, params=None, json=None):
        if table == "catalogo_productos_tecnicos":
            return [{
                "id": PRODUCT_ID, "nombre": "Recubrimiento DEMOSTRATIVO",
                "superficie": "concreto", "ambiente": "exterior",
                "rendimiento_m2_litro_mano": "10.000",
                "manos_recomendadas": 2,
                "desperdicio_pct": "15.00",
                "presentacion_litros": "4.000",
                "es_demostrativo": True,
            }]
        if table == "analisis_ia":
            return [{"resultado": {"requiere_revision_humana": True}}]
        if table == "calculos_materiales" and method == "POST":
            return [{"id": REQUEST_ID, **json}]
        raise AssertionError(f"Llamada inesperada: {table} / {method}")

    app.dependency_overrides[capture.current_user] = fake_user
    monkeypatch.setattr(technical, "_find_request", fake_request)
    monkeypatch.setattr(technical, "supabase_rest", fake_rest)
    try:
        response = client.post(
            f"/api/v1/tecnico/solicitudes/{REQUEST_ID}/calcular",
            json={"producto_id": PRODUCT_ID},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["envases"] == 5
        assert data["requiere_revision_humana"] is True
        assert data["es_demostrativo"] is True
        assert Decimal(data["litros_comerciales"]) == Decimal("20.000")
    finally:
        app.dependency_overrides.clear()
