"""Regresiones visuales de RF-05.1: el formulario debe estar visible para clientes."""
from pathlib import Path

SOURCE = Path("frontend/app.py").read_text(encoding="utf-8")


def test_reply_tab_is_second_to_be_easy_to_find():
    assert '"Mi panel", "Revisión técnica", "Mi empresa"' in SOURCE


def test_form_is_available_for_pending_customer_review():
    review_section = SOURCE.split("with tab_revision:", 1)[1]
    assert '"pendiente_informacion"' in review_section
    assert '"solicitar_informacion", "solicitar_correccion"' in review_section
    assert 'st.subheader("Responder al especialista técnico")' in review_section
    assert 'with st.form("respuesta_revision_cliente")' in review_section
    assert '"Enviar respuesta al especialista"' in review_section
    assert review_section.index('st.subheader("Responder al especialista técnico")') < (
        review_section.index('st.write("**Historial de decisiones del especialista**")')
    )


def test_version_label_and_compatible_textarea():
    assert "Interfaz 0.6.2" in SOURCE
    assert "min_height=" not in SOURCE
