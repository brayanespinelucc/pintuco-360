"""RF-08: quality authorization, checklist contracts, field rework, client tracking."""
from fastapi.testclient import TestClient
from backend.app.api import capture
from backend.app.main import app

client = TestClient(app)
APP_ID = "3bf10e32-4c2e-49a5-9a46-6a38eb176003"
ALL_OK = {
    "superficie_preparada": True,
    "cobertura_adecuada": True,
    "acabado_uniforme": True,
    "evidencias_verificadas": True,
    "incidencias_gestionadas": True,
}
COMMENT = "Se verifican los hallazgos documentados durante la inspección académica."


def _role(role):
    async def fake_user():
        return {"id": APP_ID, "role": role}, "jwt"
    return fake_user


def test_unauthenticated_qa_is_denied():
    assert client.get("/api/v1/calidad/bandeja").status_code == 401
    assert client.get("/api/v1/calidad/expedientes").status_code == 401
    assert client.post(
        f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
        json={"decision": "aprobar", "criterios": ALL_OK, "observaciones": COMMENT},
    ).status_code == 401


def test_customer_can_only_read_reports_not_inspect(monkeypatch):
    from backend.app.api import quality

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert method == "POST" and table == "rpc/expedientes_calidad"
        return [{"aplicacion_id": APP_ID, "estado_solicitud": "en_calidad"}]

    app.dependency_overrides[capture.current_user] = _role("cliente")
    monkeypatch.setattr(quality, "supabase_rest", fake_rest)
    try:
        assert client.get("/api/v1/calidad/expedientes").status_code == 200
        assert client.get("/api/v1/calidad/bandeja").status_code == 403
        resp = client.post(
            f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
            json={"decision": "aprobar", "criterios": ALL_OK, "observaciones": COMMENT},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_applicator_and_logistics_cannot_inspect():
    for role in ("aplicador", "logistica", "especialista_tecnico"):
        app.dependency_overrides[capture.current_user] = _role(role)
        try:
            assert client.get("/api/v1/calidad/bandeja").status_code == 403
            assert client.post(
                f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
                json={"decision": "aprobar", "criterios": ALL_OK, "observaciones": COMMENT},
            ).status_code == 403
        finally:
            app.dependency_overrides.clear()


def test_inspector_reads_and_approves_with_complete_checklist(monkeypatch):
    from backend.app.api import quality

    calls = []

    async def fake_rest(method, table, token, *, params=None, json=None):
        calls.append((table, json))
        if table == "rpc/bandeja_calidad":
            return [{"aplicacion_id": APP_ID, "evidencias": 1}]
        if table == "rpc/expedientes_calidad":
            return [{"aplicacion_id": APP_ID, "bitacora": []}]
        if table == "rpc/resolver_calidad":
            assert json["p_aplicacion_id"] == APP_ID
            assert json["p_decision"] == "aprobar"
            assert json["p_criterios"] == ALL_OK
            assert json["p_observaciones"] == COMMENT
            return {
                "aplicacion_id": APP_ID,
                "decision": "aprobar",
                "estado_aplicacion": "calidad_aprobada",
                "estado_solicitud": "finalizada",
            }
        raise AssertionError(table)

    app.dependency_overrides[capture.current_user] = _role("calidad")
    monkeypatch.setattr(quality, "supabase_rest", fake_rest)
    try:
        assert client.get("/api/v1/calidad/bandeja").status_code == 200
        assert client.get("/api/v1/calidad/expedientes").status_code == 200
        resp = client.post(
            f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
            json={"decision": "aprobar", "criterios": ALL_OK, "observaciones": COMMENT},
        )
        assert resp.status_code == 201
        assert resp.json()["estado_solicitud"] == "finalizada"
        assert len(calls) == 3
    finally:
        app.dependency_overrides.clear()


def test_reject_or_correction_requires_failed_criteria():
    app.dependency_overrides[capture.current_user] = _role("calidad")
    try:
        failed = dict(ALL_OK)
        failed["acabado_uniforme"] = False
        for decision, criteria, expected in (
            ("aprobar", failed, 422),
            ("solicitar_correccion", ALL_OK, 422),
            ("rechazar", ALL_OK, 422),
            ("destruir", failed, 422),
        ):
            resp = client.post(
                f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
                json={"decision": decision, "criterios": criteria, "observaciones": COMMENT},
            )
            assert resp.status_code == expected, resp.text
        unexpected = dict(ALL_OK)
        unexpected["aprobacion_automatica"] = True
        resp = client.post(
            f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
            json={"decision": "aprobar", "criterios": unexpected, "observaciones": COMMENT},
        )
        assert resp.status_code == 422
        short = client.post(
            f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
            json={"decision": "aprobar", "criterios": ALL_OK, "observaciones": "   "},
        )
        assert short.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_valid_correction_decision_is_forwarded(monkeypatch):
    from backend.app.api import quality

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/resolver_calidad"
        assert json["p_decision"] == "solicitar_correccion"
        assert json["p_criterios"]["acabado_uniforme"] is False
        return {"aplicacion_id": APP_ID, "decision": "solicitar_correccion",
                "estado_aplicacion": "en_correccion"}

    app.dependency_overrides[capture.current_user] = _role("calidad")
    monkeypatch.setattr(quality, "supabase_rest", fake_rest)
    try:
        criteria = dict(ALL_OK)
        criteria["acabado_uniforme"] = False
        resp = client.post(
            f"/api/v1/calidad/aplicaciones/{APP_ID}/resolver",
            json={"decision": "solicitar_correccion", "criterios": criteria,
                  "observaciones": "Se observa acabado no uniforme; requiere corrección técnica."},
        )
        assert resp.status_code == 201
        assert resp.json()["estado_aplicacion"] == "en_correccion"
    finally:
        app.dependency_overrides.clear()


def test_only_applicator_can_submit_correction(monkeypatch):
    from backend.app.api import field

    async def fake_rest(method, table, token, *, params=None, json=None):
        assert table == "rpc/subsanar_calidad"
        assert json["p_aplicacion_id"] == APP_ID
        return {"aplicacion_id": APP_ID, "estado_aplicacion": "pendiente_calidad",
                "estado_solicitud": "en_calidad"}

    monkeypatch.setattr(field, "supabase_rest", fake_rest)
    for role in ("cliente", "logistica", "calidad"):
        app.dependency_overrides[capture.current_user] = _role(role)
        try:
            assert client.post(
                f"/api/v1/campo/aplicaciones/{APP_ID}/subsanar",
                json={"observaciones": "Se atienden los puntos del inspector académico."},
            ).status_code == 403
        finally:
            app.dependency_overrides.clear()
    app.dependency_overrides[capture.current_user] = _role("aplicador")
    try:
        resp = client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/subsanar",
            json={"observaciones": "Se atienden los puntos del inspector académico."},
        )
        assert resp.status_code == 201
        assert resp.json()["estado_solicitud"] == "en_calidad"
        assert client.post(
            f"/api/v1/campo/aplicaciones/{APP_ID}/subsanar",
            json={"observaciones": "  "},
        ).status_code == 422
    finally:
        app.dependency_overrides.clear()
