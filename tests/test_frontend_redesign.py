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
                "full_name": "Cuenta de pruebas",
                "email": "demo@example.com",
            }
        elif path == "/auth/login":
            response_data = {"access_token": "jwt-test"}
        elif method == "GET" and path in {
            "/capture/clientes", "/capture/proyectos", "/capture/solicitudes",
            "/logistica/bandeja", "/logistica/ordenes", "/campo/elegibles",
            "/campo/aplicadores", "/campo/aplicaciones",
            "/calidad/bandeja", "/calidad/expedientes",
            "/revision/bandeja",
        }:
            response_data = []
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


def test_login_page_renders_without_real_credentials(api):
    app = AppTest.from_file(APP_FILE, default_timeout=20).run()
    assert not app.exception
    assert len(app.text_input) >= 2


def test_client_has_eleven_real_pages_and_lazy_loads(api):
    received, roles = api
    app = _open_app()
    assert roles["role"] == "cliente"
    assert list(app.radio[0].options) == CLIENT_PAGES
    assert ("GET", "/capture/clientes") in received
    assert ("GET", "/capture/proyectos") in received
    assert ("GET", "/capture/solicitudes") in received
    assert ("GET", "/calidad/expedientes") not in received
    received.clear()
    app.radio[0].set_value("Control de calidad").run()
    assert not app.exception
    assert ("GET", "/calidad/expedientes") in received
    assert ("GET", "/capture/clientes") not in received
    assert ("GET", "/capture/proyectos") not in received
    assert ("GET", "/capture/solicitudes") not in received


@pytest.mark.parametrize("page", CLIENT_PAGES)
def test_every_client_module_renders_without_data(api, page):
    app = _open_app()
    app.radio[0].set_value(page).run()
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
    assert list(app.radio[0].options) == [
        "Reservas", "Órdenes y despachos", "Aplicadores y campo",
    ]
    assert ("GET", "/logistica/bandeja") in received
    assert ("GET", "/logistica/ordenes") not in received
    assert ("GET", "/campo/aplicaciones") not in received

    received.clear()
    app.radio[0].set_value("Órdenes y despachos").run()
    assert not app.exception
    assert ("GET", "/logistica/ordenes") in received
    assert ("GET", "/logistica/bandeja") not in received

    received.clear()
    app.radio[0].set_value("Aplicadores y campo").run()
    assert not app.exception
    assert ("GET", "/campo/aplicaciones") in received
    assert ("GET", "/campo/elegibles") in received
    assert ("GET", "/campo/aplicadores") in received
    assert ("GET", "/logistica/ordenes") not in received


def test_inspector_queue_and_history_use_the_same_authorized_read_api(api):
    received, roles = api
    roles["role"] = "calidad"
    app = _open_app()
    assert list(app.radio[0].options) == [
        "Inspecciones pendientes", "Historial de dictámenes",
    ]
    assert ("GET", "/calidad/bandeja") in received
    assert ("GET", "/calidad/expedientes") in received

    received.clear()
    app.radio[0].set_value("Historial de dictámenes").run()
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
    assert '--cl-bg: #F5F7FB;' in emitted_html[0]
    emitted_html.clear()
    design.apply_design_system(True)
    assert len(emitted_html) == 1
    assert 'id="cl-theme-dark"' in emitted_html[0]
    assert '--cl-bg: #0A1221;' in emitted_html[0]
