"""Smoke tests for the redesigned Streamlit UI with stubbed existing API responses.

No real credentials, Supabase changes or backend calls.
"""
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

APP_FILE = str(Path(__file__).resolve().parents[1] / "frontend" / "app.py")
CLIENT_PAGES = [
    "Mi panel", "Mi empresa", "Proyectos", "Solicitudes",
    "Análisis con Gemini", "Cálculo técnico", "Inventario",
    "Revisión técnica", "Seguimiento logístico",
    "Aplicación en campo", "Control de calidad",
]


@pytest.fixture
def api(monkeypatch):
    received = []
    active_role = {"role": "cliente"}

    def fake_request(method, url, **kwargs):
        path = url.split("/api/v1", 1)[1]
        received.append((method, path))
        if path == "/auth/me":
            response_data = {
                "id": "72afe3f6-08f3-42d4-825d-b09943f977f4",
                "role": active_role["role"],
                "can_switch_roles": active_role.get("evaluator", False),
                "full_name": "Cuenta de pruebas",
                "email": "demo@example.com",
            }
        elif path == "/auth/login":
            response_data = {"access_token": "jwt-test"}
        elif path == "/auth/evaluator/role" and method == "POST":
            selected = kwargs["json"]["role"]
            active_role["role"] = selected
            response_data = {"role": selected, "enabled": True}
        elif path == "/auth/register" and method == "POST":
            response_data = {
                "message": "Solicitud recibida. Revisa tu correo.",
                "requires_confirmation": True,
            }
        elif method == "GET" and path in {
            "/capture/clientes", "/capture/proyectos", "/capture/solicitudes",
            "/logistica/bandeja", "/logistica/ordenes", "/campo/elegibles",
            "/campo/aplicadores", "/campo/aplicaciones",
            "/calidad/bandeja", "/calidad/expedientes",
            "/revision/bandeja",
        }:
            response_data = active_role.get(path, [])
        else:
            # The tests check rendering with no data; no application mutation is allowed.
            if method == "POST" and path == "/auth/login":
                response_data = {"access_token": "jwt-test"}
            else:
                return httpx.Response(
                    404, json={"detail": "Sin registros de prueba"},
                    request=httpx.Request(method, url),
                )
        return httpx.Response(
            200, json=response_data, request=httpx.Request(method, url)
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    return received, active_role


def _open_app():
    app = AppTest.from_file(APP_FILE, default_timeout=20)
    app.session_state["access_token"] = "jwt-test"
    app.run()
    assert not app.exception, [str(e.message) for e in app.exception]
    return app


def _click_page(app, label):
    button = next(item for item in app.button if item.label == label)
    button.click().run()
    return app


def test_login_page_renders_without_real_credentials(api):
    app = AppTest.from_file(APP_FILE, default_timeout=20).run()
    assert not app.exception
    assert len(app.text_input) >= 2


def test_client_has_eleven_real_pages_and_lazy_loads(api):
    received, roles = api
    app = _open_app()
    assert roles["role"] == "cliente"
    assert all(any(b.label == page for b in app.button) for page in CLIENT_PAGES)
    assert ("GET", "/capture/clientes") in received
    assert ("GET", "/capture/proyectos") in received
    assert ("GET", "/capture/solicitudes") in received
    assert ("GET", "/calidad/expedientes") not in received
    received.clear()
    _click_page(app, "Control de calidad")
    assert not app.exception
    assert ("GET", "/calidad/expedientes") in received
    assert ("GET", "/capture/clientes") not in received
    assert ("GET", "/capture/proyectos") not in received
    assert ("GET", "/capture/solicitudes") not in received


@pytest.mark.parametrize("page", CLIENT_PAGES)
def test_every_client_module_renders_without_data(api, page):
    app = _open_app()
    _click_page(app, page)
    assert not app.exception, [str(e.message) for e in app.exception]


@pytest.mark.parametrize("role", ["logistica", "calidad", "aplicador", "especialista_tecnico"])
def test_role_workspaces_still_render(api, role):
    _, roles = api
    roles["role"] = role
    app = _open_app()
    assert not app.exception


def test_dark_theme_switch_does_not_change_api_or_role(api):
    received, _ = api
    app = _open_app()
    assert not app.exception
    base = list(received)
    assert app.toggle
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert ("GET", "/auth/me") in received
    assert app.session_state["cl_dark"] is True
    assert all(method == "GET" for method, path in received)


def test_logistics_navigation_lazily_loads_each_operational_stage(api):
    received, roles = api
    roles["role"] = "logistica"
    app = _open_app()
    assert all(
        any(b.label == page for b in app.button)
        for page in ("Reservas", "Órdenes y despachos", "Aplicadores y campo")
    )
    assert ("GET", "/logistica/bandeja") in received
    assert ("GET", "/logistica/ordenes") not in received
    assert ("GET", "/campo/aplicaciones") not in received

    received.clear()
    _click_page(app, "Órdenes y despachos")
    assert not app.exception
    assert ("GET", "/logistica/ordenes") in received
    assert ("GET", "/logistica/bandeja") not in received

    received.clear()
    _click_page(app, "Aplicadores y campo")
    assert not app.exception
    assert ("GET", "/campo/aplicaciones") in received
    assert ("GET", "/campo/elegibles") in received
    assert ("GET", "/campo/aplicadores") in received
    assert ("GET", "/logistica/ordenes") not in received


def test_inspector_queue_and_history_use_the_same_authorized_read_api(api):
    received, roles = api
    roles["role"] = "calidad"
    app = _open_app()
    assert all(
        any(b.label == page for b in app.button)
        for page in ("Inspecciones pendientes", "Historial de dictámenes")
    )
    assert ("GET", "/calidad/bandeja") in received
    assert ("GET", "/calidad/expedientes") in received

    received.clear()
    _click_page(app, "Historial de dictámenes")
    assert not app.exception
    assert ("GET", "/calidad/expedientes") in received
    assert ("GET", "/calidad/bandeja") not in received


def test_design_css_is_emitted_as_html_not_raw_markdown(monkeypatch):
    """Regression: a Markdown parser must never display the CSS as page text."""
    from frontend import design

    emitted_html = []
    monkeypatch.setattr(design.st, "html", lambda value: emitted_html.append(value))

    def no_markdown_for_css(*args, **kwargs):
        raise AssertionError("Do not inject <style> through st.markdown.")

    monkeypatch.setattr(design.st, "markdown", no_markdown_for_css)
    design.apply_design_system(False)
    assert len(emitted_html) == 1
    assert '<style>' in emitted_html[0] and '</style>' in emitted_html[0]
    assert 'id="cl-theme-light"' in emitted_html[0]
    assert '[data-testid="stApp"]' in emitted_html[0]
    assert '--cl-bg:#F4F5FA;' in emitted_html[0]
    emitted_html.clear()
    design.apply_design_system(True)
    assert len(emitted_html) == 1
    assert 'id="cl-theme-dark"' in emitted_html[0]
    assert '--cl-bg:#0B1020;' in emitted_html[0]



def test_client_facing_brand_copy_has_no_academic_demo_banners():
    """Keep operational safeguards, but avoid demo and academic banners in the UI."""
    import re
    sources = [
        Path(APP_FILE).read_text(encoding="utf-8"),
        Path(APP_FILE).with_name("design.py").read_text(encoding="utf-8"),
    ]
    prohibited = re.compile(
        r"acad[eé]mic|universit|"
        r"\bdemo\b|simulad|de prueba|fictici|"
        r"no oficiales|certificaci[oó]n|Pintuco",
        re.IGNORECASE,
    )
    for source in sources:
        assert not prohibited.search(source)
    # es_demostrativo is a backend response field, never rename the contract.
    assert '["es_demostrativo"]' in sources[0]
    assert 'No constituye una reserva' in sources[0]



def test_self_registration_screen_visible_to_public(api):
    app = AppTest.from_file(APP_FILE, default_timeout=20).run()
    assert not app.exception
    assert [t.label for t in app.tabs] == ["Iniciar sesión", "Crear cuenta"]
    assert any(x.label == "Correo para registro" for x in app.text_input)
    assert any(x.label == "Crear mi cuenta" for x in app.button)


def test_evaluator_can_change_role_and_return_without_impersonating_user(api):
    seen, role = api
    role["evaluator"] = True
    app = _open_app()
    assert not app.exception
    selector = next(x for x in app.selectbox if x.label == "Probar funcionalidades como")
    assert selector.options == [
        "Cliente", "Especialista técnico", "Logística", "Aplicador", "Control de calidad",
    ]
    selector.set_value("Control de calidad").run()
    assert not app.exception
    switch = next(x for x in app.button if x.label == "Cambiar al rol seleccionado")
    switch.click().run()
    assert not app.exception
    assert role["role"] == "calidad"
    assert ("POST", "/auth/evaluator/role") in seen
    assert any(b.label == "Inspecciones pendientes" for b in app.button)


def test_normal_user_does_not_have_any_role_changer(api):
    app = _open_app()
    assert not any(x.label == "Probar funcionalidades como" for x in app.selectbox)
    assert not any(x.label == "Cambiar al rol seleccionado" for x in app.button)



def test_dashboard_tracks_real_request_status_and_routes_next_action(api):
    """The user navigates to an existing module, without any new business writes."""
    seen, data = api
    rid = "e2b6a0cf-68f1-45e2-bfa8-281100a76ce0"
    pid = "97a55794-29e8-45f0-b9cc-529a7b9fd753"
    data["/capture/solicitudes"] = [{
        "id": rid, "proyecto_id": pid, "created_at": "2026-11-01T18:20:00Z",
        "updated_at": "2026-11-18T20:00:00Z",
        "estado": "pendiente_informacion", "descripcion_libre": "Faltan detalles de la superficie.",
    }]
    data["/capture/proyectos"] = [{
        "id": pid, "nombre_proyecto": "Proyecto Norte"
    }]
    app = _open_app()
    assert not app.exception
    assert any(x.label == "Solicitud a seguir" for x in app.selectbox)
    action = next(x for x in app.button if x.label == "Responder al especialista")
    seen.clear()
    action.click().run()
    assert not app.exception
    assert app.session_state["cl_page"] == "Revisión técnica"
    assert not any(method == "POST" for method, _ in seen)


def test_request_details_keep_original_upload_action_and_status_navigation(api):
    seen, data = api
    rid = "73b61241-00f4-4cb8-89bc-58a9b54820d4"
    pid = "833f6021-bc80-4ef5-9962-e80f514ece85"
    data["/capture/solicitudes"] = [{
        "id": rid, "proyecto_id": pid,
        "estado": "en_analisis", "created_at": "2026-11-10T12:30:00Z",
        "descripcion_libre": "Solicitud de revestimiento, aplicación exterior."
    }]
    data["/capture/proyectos"] = [{
        "id": pid, "nombre_proyecto": "Fachada norte"
    }]
    app = _open_app()
    seen.clear()
    _click_page(app, "Solicitudes")
    assert not app.exception
    assert any(x.label == "Solicitud para adjuntar fotos" for x in app.selectbox)
    assert any(x.label == "Adjuntar fotografías" for x in app.button)
    assert ("GET", "/capture/solicitudes") in seen
    assert not any(method == "POST" for method, _ in seen)
