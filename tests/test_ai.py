from fastapi.testclient import TestClient
from fastapi import HTTPException
from backend.app.main import app
from backend.app.api import capture
from backend.app.services.gemini import Clasificacion, apply_business_guards

client = TestClient(app)
REQUEST_ID = "2ffb5eb8-47c6-43e5-9322-0086510e2dbc"


def test_requires_auth():
    response = client.get(f"/api/v1/ia/solicitudes/{REQUEST_ID}/analisis")
    assert response.status_code == 401


def test_consent_required():
    async def user_override():
        return {"id": REQUEST_ID, "role": "cliente"}, "jwt"
    app.dependency_overrides[capture.current_user] = user_override
    try:
        response = client.post(f"/api/v1/ia/solicitudes/{REQUEST_ID}/analizar",
                               json={"autorizo_envio_a_gemini": False})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_non_customer_forbidden():
    async def other_role():
        return {"id": REQUEST_ID, "role": "logistica"}, "jwt"
    app.dependency_overrides[capture.current_user] = other_role
    try:
        response = client.post(f"/api/v1/ia/solicitudes/{REQUEST_ID}/analizar",
                               json={"autorizo_envio_a_gemini": True})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_humidity_forces_human_review():
    result = Clasificacion(
        categoria_necesidad="recubrimiento exterior",
        tipo_superficie="concreto",
        ambiente="exterior",
        condiciones_reportadas=[],
        observaciones_visuales=[],
        hipotesis_no_confirmadas=[],
        informacion_faltante=[],
        requiere_revision_humana=False,
        confianza_cualitativa="media",
        resumen="Cliente solicita pintura para exterior."
    )
    checked = apply_business_guards(result, "Fachada con humedad y fisuras.", {"condicion": "humedad"})
    assert checked.requiere_revision_humana is True


def test_no_calculation_fields_in_schema():
    from backend.app.services.gemini import SCHEMA
    assert "litros" not in SCHEMA["properties"]
    assert "precio" not in SCHEMA["properties"]
    assert "rendimiento" not in SCHEMA["properties"]



def test_successful_analysis_persists_structured_record(monkeypatch):
    from backend.app.api import ai
    from backend.app.services.gemini import Clasificacion

    calls = []

    async def user_override():
        return {"id": REQUEST_ID, "role": "cliente"}, "jwt"

    async def fake_rest(method, table, token, *, params=None, json=None):
        calls.append((method, table, json))
        if table == "solicitudes":
            return [{"id": REQUEST_ID, "proyecto_id": REQUEST_ID, "descripcion_libre": "Fachada con humedad y fisuras."}]
        if table == "proyectos":
            return [{"id": REQUEST_ID, "nombre_proyecto": "Fachada", "tipo_superficie": "concreto",
                     "condicion": "humedad y fisuras", "ambiente": "exterior", "color_requerido": "gris",
                     "area_m2": 85, "fecha_requerida": None}]
        if table == "analisis_ia" and method == "POST":
            return [{"id": "894be8f8-d957-4204-8d47-19fc0c7281d9", **json}]
        raise AssertionError(f"Llamada inesperada {table} / {method}")

    async def fake_photos(*args):
        return [("image/jpeg", b"\xff\xd8\xff\xd9")]

    async def fake_gemini(**kwargs):
        return (Clasificacion(
            categoria_necesidad="recubrimiento exterior",
            tipo_superficie="concreto", ambiente="exterior",
            condiciones_reportadas=["humedad", "fisuras"],
            observaciones_visuales=[], hipotesis_no_confirmadas=[],
            informacion_faltante=["inspección"],
            requiere_revision_humana=True, confianza_cualitativa="media",
            resumen="Se requiere visita técnica previa a la elección de recubrimiento."
        ), "gemini-3.5-flash-lite")

    app.dependency_overrides[capture.current_user] = user_override
    monkeypatch.setattr(ai, "supabase_rest", fake_rest)
    monkeypatch.setattr(ai, "_load_photos", fake_photos)
    monkeypatch.setattr(ai, "classify_with_gemini", fake_gemini)
    try:
        response = client.post(f"/api/v1/ia/solicitudes/{REQUEST_ID}/analizar",
                               json={"autorizo_envio_a_gemini": True})
        assert response.status_code == 201
        assert response.json()["resultado"]["requiere_revision_humana"] is True
        assert response.json()["numero_imagenes"] == 1
        assert any(method == "POST" and table == "analisis_ia" for method, table, _ in calls)
    finally:
        app.dependency_overrides.clear()



def test_provider_404_has_actionable_message(monkeypatch):
    """Una denegación del modelo no se confunde con un error genérico del portal."""
    import asyncio
    from types import SimpleNamespace

    import httpx
    import pytest
    from backend.app.services import gemini

    class Google404:
        status_code = 404
        is_error = True

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return Google404()

    monkeypatch.setattr(gemini, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="test-key-do-not-use",
        gemini_model="gemini-2.5-flash",
    ))
    monkeypatch.setattr(gemini.httpx, "AsyncClient", FakeClient)

    with pytest.raises(HTTPException) as error:
        asyncio.run(gemini.classify_with_gemini(
            description="Pintar fachada de concreto con humedad",
            project={"ambiente": "exterior", "condicion": "humedad"},
            images=[],
        ))
    assert error.value.status_code == 502
    assert "gemini-3.5-flash-lite" in error.value.detail
    assert "GEMINI_MODEL" in error.value.detail
