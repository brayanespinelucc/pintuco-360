"""Premium UI v2: structural, safety, accessibility and navigation checks."""
import ast
from pathlib import Path

import pytest

from frontend import design

ROOT = Path(__file__).resolve().parents[1]
APP_SRC = (ROOT / "frontend" / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "premium.css").read_text(encoding="utf-8")


def _html(monkeypatch):
    seen = []
    monkeypatch.setattr(design.st, "html", lambda value: seen.append(value))
    return seen


def test_premium_visual_tokens_cover_both_themes():
    for token in ("--cl-bg", "--cl-panel", "--cl-border", "--cl-primary",
                  "--cl-turquoise", "--cl-text", "--cl-heading", "--cl-muted"):
        assert CSS.count(token) >= 2
    assert "--cl-bg:#F4F5FA;" in CSS
    assert "--cl-bg:#0B1020;" in CSS
    assert "Outfit" in CSS and "DM Sans" in CSS
    assert "prefers-reduced-motion:reduce" in CSS
    assert "focus-visible" in CSS
    assert "max-width:500px" in CSS and "max-width:780px" in CSS
    assert '[data-testid="stForm"]' in CSS
    assert '[data-testid="stDataFrame"]' in CSS
    assert '[data-testid="stTabs"]' in CSS


def test_premium_layout_has_no_inert_fake_buttons(monkeypatch):
    emitted = _html(monkeypatch)
    design.auth_showcase()
    design.auth_form_heading()
    assert len(emitted) == 2
    assert "cl-auth-showcase" in emitted[0]
    assert "cl-auth-form-header" in emitted[1]
    assert "<button" not in "".join(emitted)
    assert "<script" not in "".join(emitted)


def test_user_data_is_html_escaped_in_shared_components(monkeypatch):
    emitted = _html(monkeypatch)
    design.user_identity('<svg onload="x">', "cliente")
    design.page_hero("CAPTURA", "<img src=x>", "Texto <b>no seguro</b>", chip="CLIENTE")
    design.record_cards(
        [{"nombre_empresa": "<script>alert(1)</script>", "ciudad": "Bogotá & alrededores",
          "estado": "radicada"}],
        title_field="nombre_empresa", detail_field="ciudad", state_field="estado",
    )
    assert len(emitted) == 3
    joined = "".join(emitted)
    assert "<script>alert(1)</script>" not in joined
    assert "&lt;script&gt;" in joined
    assert "&lt;img src=x&gt;" in joined
    assert "Bogotá &amp; alrededores" in joined
    assert '&lt;svg onload=&quot;x&quot;&gt;' in joined


def test_empty_state_and_workflow_hint_render_no_actions(monkeypatch):
    emitted = _html(monkeypatch)
    design.empty_state("Sin expedientes", "No hay registros asociados.")
    design.journey_hint("INSPECCIÓN", "Verifica cada criterio", "Usa la información existente.")
    assert "cl-empty-state" in emitted[0]
    assert "cl-journey-hint" in emitted[1]
    assert "<button" not in "".join(emitted)


def test_every_existing_client_page_has_context_and_grouped_navigation():
    syntax = ast.parse(APP_SRC)
    assignments = [
        a for a in syntax.body if isinstance(a, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "WORKSPACE_GUIDANCE"
                for target in a.targets)
    ]
    assert len(assignments) == 1
    guides = ast.literal_eval(assignments[0].value)
    labels = [p[0] for p in design.PAGES]
    assert set(guides) == set(labels)
    assert len(labels) == 11
    assert 'navigation_group(label)' in APP_SRC
    for page in ("Mi panel", "Solicitudes", "Control de calidad"):
        assert f'"{page}"' in APP_SRC
    assert "cl_nav_" in APP_SRC and 'on_click=lambda chosen=page' in APP_SRC


def test_all_roles_retain_existing_frontend_presentation():
    assert 'elif profile["role"] == "logistica":' in APP_SRC
    assert 'elif profile["role"] == "calidad":' in APP_SRC
    assert 'elif profile["role"] == "aplicador":' in APP_SRC
    assert '"especialista_tecnico"' in APP_SRC
    assert '"administrador"' in APP_SRC
    assert 'if profile.get("can_switch_roles"):' in APP_SRC
    assert '"POST", "/auth/evaluator/role"' in APP_SRC
    assert 'with st.form("login")' in APP_SRC
    assert 'with st.form("register")' in APP_SRC
    assert 'with st.form("crear_cliente")' in APP_SRC
    assert 'with st.form("crear_proyecto")' in APP_SRC
    assert 'with st.form("crear_solicitud")' in APP_SRC
    assert 'with st.form("resolver_revision")' in APP_SRC
    assert 'with st.form("rf08_dictamen")' in APP_SRC


def test_module_cards_are_noninteractive_and_original_tables_remain(monkeypatch):
    emitted = _html(monkeypatch)
    design.record_cards([
        {"nombre_proyecto": "Torre A", "estado": "en_aplicacion"}
    ], title_field="nombre_proyecto", state_field="estado")
    assert len(emitted) == 1
    assert 'role="button"' not in emitted[0]
    assert "<button" not in emitted[0]
    assert "Torre A" in emitted[0]
    assert "st.dataframe(" in APP_SRC


def test_premium_design_still_injects_styles_with_streamlit_html(monkeypatch):
    emitted = _html(monkeypatch)
    design.apply_design_system(False)
    design.apply_design_system(True)
    assert len(emitted) == 2
    assert 'id="cl-theme-light"' in emitted[0]
    assert 'id="cl-theme-dark"' in emitted[1]
    assert CSS in emitted[0]
    assert CSS in emitted[1]
    assert "<style>" in emitted[0]
