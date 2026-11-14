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
