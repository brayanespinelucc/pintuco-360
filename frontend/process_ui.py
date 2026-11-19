"""Read-only process experience components built from existing COLORLINK API states.

No business state changes, API calls, permission overrides, or invented timestamps.
The stepper is an orientation guide, not a new workflow engine.
"""
from __future__ import annotations

from collections import Counter
from html import escape
from typing import Mapping

import streamlit as st

STAGES = (
    ("Solicitud", "Cliente", "files"),
    ("Análisis", "Cliente", "sparkles"),
    ("Revisión técnica", "Especialista técnico", "clipboard-check"),
    ("Logística", "Logística", "truck"),
    ("Aplicación", "Aplicador", "paintbrush"),
    ("Calidad", "Inspector", "shield-check"),
    ("Cierre", "Cliente", "check"),
)

# Every entry corresponds to an actual persisted public.solicitudes.estado value.
STAGE_FOR_STATUS = {
    "radicada": 0,
    "en_validacion": 0,
    "en_analisis": 1,
    "pendiente_informacion": 2,
    "en_revision_tecnica": 2,
    "cotizada": 2,
    "aprobada": 2,
    "en_logistica": 3,
    "en_aplicacion": 4,
    "en_calidad": 5,
    "finalizada": 6,
}

STATUS_COPY = {
    "radicada": ("Solicitud radicada", "Adjunta las evidencias necesarias y continúa con el análisis.", "Solicitudes", "Gestionar evidencias"),
    "en_validacion": ("En validación", "Consulta las observaciones de la solicitud y las evidencias registradas.", "Solicitudes", "Ver solicitud"),
    "en_analisis": ("En análisis", "Revisa el análisis inteligente y el cálculo técnico de materiales.", "Análisis con Gemini", "Ver análisis"),
    "pendiente_informacion": ("Información solicitada", "El especialista necesita una aclaración o corrección para continuar.", "Revisión técnica", "Responder al especialista"),
    "en_revision_tecnica": ("En revisión técnica", "Un especialista debe emitir una decisión; consulta el expediente.", "Revisión técnica", "Consultar revisión"),
    "cotizada": ("Cotizada", "Consulta el resultado técnico y los siguientes pasos del expediente.", "Revisión técnica", "Ver revisión"),
    "aprobada": ("Aprobada técnicamente", "La solicitud está lista para que logística gestione materiales.", "Seguimiento logístico", "Ver logística"),
    "en_logistica": ("En logística", "La reserva, preparación o despacho están en gestión.", "Seguimiento logístico", "Seguir despacho"),
    "en_aplicacion": ("En aplicación", "Consulta los avances y evidencias del equipo de campo.", "Aplicación en campo", "Ver ejecución"),
    "en_calidad": ("En control de calidad", "El inspector revisa los criterios y evidencias del trabajo.", "Control de calidad", "Ver inspecciones"),
    "finalizada": ("Finalizada", "El proceso terminó; puedes consultar el dictamen de calidad.", "Control de calidad", "Consultar cierre"),
    "cancelada": ("Cancelada", "El proceso fue cancelado. Consulta los detalles de la solicitud.", "Solicitudes", "Ver expediente"),
}

# Module map for events that belong to *one* existing account / role only.
# No link ever bypasses the actual backend role authorization.
ROLE_ACTIONS = {
    "cliente": {
        "radicada": "Solicitudes",
        "en_validacion": "Solicitudes",
        "en_analisis": "Análisis con Gemini",
        "pendiente_informacion": "Revisión técnica",
        "en_revision_tecnica": "Revisión técnica",
        "cotizada": "Revisión técnica",
        "aprobada": "Seguimiento logístico",
        "en_logistica": "Seguimiento logístico",
        "en_aplicacion": "Aplicación en campo",
        "en_calidad": "Control de calidad",
        "finalizada": "Control de calidad",
        "cancelada": "Solicitudes",
    }
}


def clean(value: object) -> str:
    """Treat all request/project data as untrusted before HTML interpolation."""
    return escape(str(value) if value is not None else "", quote=True)


def readable_date(value: object) -> str:
    """Show a date only when the actual persisted value is present."""
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return ""


def request_state(status: object) -> tuple[str, str, str, str]:
    """Return honest, user-facing status without fabricating a state."""
    state = str(status or "").lower()
    return STATUS_COPY.get(
        state,
        (str(status or "Estado no informado").replace("_", " ").capitalize(),
         "Consulta el expediente para obtener más información.",
         "Solicitudes", "Ver expediente"),
    )


def stage_index(status: object) -> int | None:
    return STAGE_FOR_STATUS.get(str(status or "").lower())


def stage_views(status: object) -> list[dict[str, object]]:
    """Previous/present/future navigation cues, not fabricated audit events."""
    state = str(status or "").lower()
    active = stage_index(state)
    results: list[dict[str, object]] = []
    for i, (name, actor, icon) in enumerate(STAGES):
        position = (
            "detenida" if state == "cancelada" else
            "indeterminada" if active is None else
            "actual" if i == active else
            "anterior" if i < active else "pendiente"
        )
        results.append({"name": name, "actor": actor, "icon": icon, "state": position})
    return results


def render_stepper(status: object, *, compact: bool = False) -> None:
    """Status-based visual orientation. Never pretends events were timestamped."""
    try:
        from .design import icon_svg  # packaged import from tests
    except ImportError:
        from design import icon_svg  # Streamlit entrypoint runs as sibling module

    state = str(status or "")
    if state == "cancelada":
        st.error("Esta solicitud está cancelada. No hay etapas activas.")
        return
    if stage_index(state) is None:
        st.caption(f"Estado de proceso: {request_state(state)[0]}. No hay un mapa de etapas para este estado.")
        return
    parts: list[str] = []
    for p in stage_views(state):
        status_label = {
            "anterior": "Etapa anterior",
            "actual": "Etapa actual",
            "pendiente": "Etapa pendiente",
        }.get(str(p["state"]), "Sin confirmar")
        parts.append(
            '<li class="cl-step cl-step-' + clean(p["state"]) + '" '
            'aria-current="' + ("step" if p["state"] == "actual" else "false") + '">'
            '<span class="cl-step-icon">' + icon_svg(str(p["icon"]), 17) + '</span>'
            '<span class="cl-step-content"><span class="cl-step-name">'
            + clean(p["name"]) + '</span>'
            + ('<span class="cl-step-owner">' + clean(p["actor"]) + '</span>'
               if not compact else '')
            + '<span class="cl-step-state">' + status_label + '</span>'
            '</span></li>'
        )
    st.html(
        '<div class="cl-process-scroll" role="region" '
        'aria-label="Etapas del proceso, desplázate horizontalmente si es necesario" tabindex="0">'
        '<ol class="cl-process-steps">' + "".join(parts) + '</ol></div>',
    )


def render_request_panel(
    request: Mapping[str, object], projects_by_id: Mapping[str, str] | None = None,
    *, title: str = "Seguimiento de la solicitud", detail: bool = False,
) -> None:
    """Centralized overview sourced only from returned request and project fields."""
    status = str(request.get("estado") or "")
    name, explanation, _, _ = request_state(status)
    rid = str(request.get("id", ""))
    project_name = (projects_by_id or {}).get(str(request.get("proyecto_id", "")), "")
    date = readable_date(request.get("created_at"))
    secondary = " · ".join(p for p in (
        f"Solicitud #{rid[:8].upper()}" if rid else "",
        project_name, f"Creada el {date}" if date else "",
    ) if p)
    state_class = (
        "blocked" if status in ("cancelada", "pendiente_informacion") else
        "done" if status == "finalizada" else "active"
    )
    st.html(
        '<article class="cl-process-summary" aria-label="'
        + clean(title) + '">'
        '<div class="cl-process-summary-top">'
        '<div><p class="cl-process-eyebrow">' + clean(title) + '</p>'
        '<h3 class="cl-process-summary-title">' + clean(name) + '</h3>'
        '<p class="cl-process-summary-meta">' + clean(secondary) + '</p></div>'
        '<span class="cl-status-pill cl-status-' + state_class + '">'
        + clean(name) + '</span></div>'
        '<p class="cl-process-hint">' + clean(explanation) + '</p></article>',
    )
    render_stepper(status)
    if detail:
        if request.get("descripcion_libre"):
            with st.expander("Descripción registrada de la solicitud", expanded=False):
                st.write(str(request["descripcion_libre"]))
        if request.get("updated_at"):
            st.caption("Última actualización de la solicitud: " + readable_date(request.get("updated_at")))


def render_stage_explorer(status: object, *, key: str) -> None:
    """Interactive, read-only step inspector; cannot skip a business stage."""
    current = stage_index(status)
    if current is None:
        return
    with st.expander("Explorar las etapas del proceso", expanded=False):
        names = [x[0] for x in STAGES]
        selected = st.selectbox(
            "Etapa que deseas consultar", names,
            index=current, key=key,
        )
        idx = names.index(selected)
        stage_name, actor, _ = STAGES[idx]
        if idx < current:
            progress = "Etapa anterior según el estado actual"
        elif idx == current:
            progress = "Etapa actual de la solicitud"
        else:
            progress = "Etapa posterior, aún no alcanzada"
        st.markdown(f"**{stage_name}** · Responsable: **{actor}**")
        st.caption(progress)
        st.caption("Esta vista es informativa; no modifica estados ni permite saltar validaciones.")


def render_state_distribution(requests: list[dict]) -> None:
    """Real counts: group by persisted states; no invented percentages."""
    counts = Counter(str(r.get("estado") or "sin_estado") for r in requests)
    if not counts:
        st.caption("Las solicitudes que registres aparecerán aquí con su estado.")
        return
    rows = sorted(
        ((request_state(k)[0], k, v) for k, v in counts.items()),
        key=lambda x: (-x[2], x[0]),
    )
    st.html(
        '<div class="cl-state-list" aria-label="Solicitudes por estado">'
        + "".join(
            '<div class="cl-state-item"><span class="cl-state-count">'
            + clean(n) + '</span><span class="cl-state-name">'
            + clean(label) + '</span></div>'
            for label, _, n in rows
        ) + '</div>',
    )


def render_field_progress(value: object, *, label: str = "Avance registrado") -> None:
    """Only persisted RF-07 avance_pct values, never process-wide estimates."""
    if isinstance(value, bool):
        return
    try:
        progress = float(value)
    except (TypeError, ValueError):
        return
    if not (0 <= progress <= 100):
        return
    st.progress(int(progress), text=f"{label}: {progress:g} %")
