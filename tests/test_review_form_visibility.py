"""Regresión RF-05.1: revisión técnica visible en la nueva navegación."""
from pathlib import Path

SOURCE = Path("frontend/app.py").read_text(encoding="utf-8")
DESIGN = Path("frontend/design.py").read_text(encoding="utf-8")


def test_review_remains_discoverable_in_sidebar_navigation():
    assert '"Revisión técnica"' in DESIGN
    assert '"Navegación principal"' in SOURCE
    assert 'if client_page == "Revisión técnica":' in SOURCE
    assert "st.radio(" in SOURCE


def test_form_is_available_for_pending_customer_review():
    review_section = SOURCE.split('if client_page == "Revisión técnica":', 1)[1]
    assert '"pendiente_informacion"' in review_section
    assert '"solicitar_informacion", "solicitar_correccion"' in review_section
    assert 'st.subheader("Responder al especialista técnico")' in review_section
    assert 'with st.form("respuesta_revision_cliente")' in review_section
    assert '"Enviar respuesta al especialista"' in review_section
    assert review_section.index('st.subheader("Responder al especialista técnico")') < (
        review_section.index('st.write("**Historial de decisiones del especialista**")')
    )


def test_design_system_and_compatible_textarea():
    assert "apply_design_system" in SOURCE
    assert "page_hero" in SOURCE
    assert "min_height=" not in SOURCE
