"""Read-only process visualization and status mapping regression tests."""
from pathlib import Path
from unittest.mock import patch

import pytest

from frontend import process_ui

STATES = {
    "radicada": 0, "en_validacion": 0,
    "en_analisis": 1,
    "pendiente_informacion": 2, "en_revision_tecnica": 2,
    "cotizada": 2, "aprobada": 2,
    "en_logistica": 3, "en_aplicacion": 4,
    "en_calidad": 5, "finalizada": 6,
}


@pytest.mark.parametrize("status,stage", list(STATES.items()))
def test_all_actual_solicitud_states_have_a_process_stage(status, stage):
    assert process_ui.stage_index(status) == stage
    timeline = process_ui.stage_views(status)
    assert len(timeline) == 7
    assert timeline[stage]["state"] == "actual"
    assert len([step for step in timeline if step["state"] == "actual"]) == 1
    assert all(x["state"] == "anterior" for x in timeline[:stage])
    assert all(x["state"] == "pendiente" for x in timeline[stage+1:])


def test_unknown_and_cancelled_states_do_not_claim_progress():
    assert process_ui.stage_index("cancelada") is None
    assert process_ui.stage_index("nuevo_estado_servidor") is None
    assert not any(x["state"] == "actual" for x in process_ui.stage_views("cancelada"))
    assert not any(x["state"] == "anterior" for x in process_ui.stage_views("otro"))


@pytest.mark.parametrize("status,page", [
    ("radicada", "Solicitudes"),
    ("en_analisis", "Análisis con Gemini"),
    ("pendiente_informacion", "Revisión técnica"),
    ("en_logistica", "Seguimiento logístico"),
    ("en_aplicacion", "Aplicación en campo"),
    ("en_calidad", "Control de calidad"),
    ("finalizada", "Control de calidad"),
])
def test_contextual_actions_target_existing_client_pages_only(status, page):
    assert process_ui.request_state(status)[2] == page


def test_request_panel_escapes_malicious_user_supplied_fields(monkeypatch):
    rendered = []
    monkeypatch.setattr(process_ui.st, "html", lambda x: rendered.append(x))
    process_ui.render_request_panel({
        "id": "abc12345", "estado": "radicada",
        "proyecto_id": "project-id", "created_at": "2026-11-18T12:00:00Z",
    }, {"project-id": '<img src=x onerror=alert(1)>'})
    assert len(rendered) == 2
    assert "&lt;img src=x onerror=alert(1)&gt;" in rendered[0]
    assert "<img src=x onerror" not in rendered[0]
    assert "2026-11-18" in rendered[0]
    assert "aria-current=\"step\"" in rendered[1]
    assert "tabindex=\"0\"" in rendered[1]
    assert "Etapa actual" in rendered[1]


def test_real_counts_not_invented_percentages(monkeypatch):
    rendered = []
    monkeypatch.setattr(process_ui.st, "html", lambda x: rendered.append(x))
    process_ui.render_state_distribution([
        {"estado": "radicada"}, {"estado": "radicada"},
        {"estado": "finalizada"}
    ])
    assert len(rendered) == 1
    assert "Solicitud radicada" in rendered[0]
    assert "Finalizada" in rendered[0]
    assert "cl-state-count" in rendered[0]
    assert "%" not in rendered[0]


@pytest.mark.parametrize("progress", [None, "", "desconocido", -1, 101, True])
def test_invalid_field_progress_is_not_rendered(monkeypatch, progress):
    progress_bars = []
    monkeypatch.setattr(process_ui.st, "progress", lambda *a, **kw: progress_bars.append((a,kw)))
    process_ui.render_field_progress(progress)
    assert not progress_bars


def test_field_progress_uses_persisted_percentage(monkeypatch):
    progress_bars = []
    monkeypatch.setattr(process_ui.st, "progress", lambda *a, **kw: progress_bars.append((a,kw)))
    process_ui.render_field_progress(77)
    assert progress_bars == [((77,), {"text": "Avance registrado: 77 %"})]


def test_visualization_is_frontend_only_and_does_not_mutate_contracts():
    root = Path(__file__).resolve().parents[1]
    source = (root / "frontend" / "process_ui.py").read_text(encoding="utf-8")
    assert "httpx." not in source
    assert "st.session_state" not in source
    assert '"POST"' not in source
    assert "supabase_rest" not in source
    assert 'from .design import icon_svg' in source
