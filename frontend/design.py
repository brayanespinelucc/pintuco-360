"""COLORLINK visual design system.

Presentation-only primitives: no API clients, role mutations, persistence or data models.
Compatible with the existing Streamlit application and its native form controls.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import streamlit as st


PAGES = (
    ("Mi panel", "Resumen", "Tu espacio de trabajo", "Indicadores y accesos directos a las tareas más comunes.", "layout-dashboard"),
    ("Mi empresa", "Organización", "Mi empresa", "Administra los datos de las empresas vinculadas a tu cuenta.", "building-2"),
    ("Proyectos", "Planificación", "Mis proyectos", "Organiza las superficies, necesidades y fechas de cada proyecto.", "folder-kanban"),
    ("Solicitudes", "Captura", "Solicitudes y evidencias", "Radica necesidades y gestiona las fotografías adjuntas.", "files"),
    ("Análisis con Gemini", "Inteligencia artificial", "Análisis de solicitudes", "Consulta el análisis inteligente con consentimiento explícito.", "sparkles"),
    ("Cálculo técnico", "Asistencia técnica", "Cálculo de materiales", "Explora estimaciones y cálculos asociados a tus solicitudes.", "calculator"),
    ("Inventario", "Disponibilidad", "Inventario y materiales", "Consulta la disponibilidad registrada para los proyectos.", "package"),
    ("Revisión técnica", "Supervisión", "Revisión técnica", "Responde a las observaciones del especialista y consulta sus decisiones.", "clipboard-check"),
    ("Seguimiento logístico", "Operaciones", "Seguimiento logístico", "Revisa reservas, preparación y despachos de tus solicitudes.", "truck"),
    ("Aplicación en campo", "Ejecución", "Aplicación en campo", "Sigue avances, incidencias y evidencias del trabajo asignado.", "paintbrush"),
    ("Control de calidad", "Validación", "Control de calidad", "Consulta los dictámenes y el historial completo de inspección.", "shield-check"),
)

ROLE_PAGES = {
    "logistica": ("Operaciones", "Logística y despacho", "Gestiona materiales, reservas y asignación de aplicadores."),
    "calidad": ("Inspección", "Control de calidad", "Evalúa evidencias y registra dictámenes con trazabilidad."),
    "aplicador": ("Ejecución", "Trabajo en campo", "Registra la actividad, incidencias y evidencias de tus trabajos."),
    "asesor": ("Revisión", "Asesoría técnica", "Consulta antecedentes y registra decisiones técnicas."),
    "especialista_tecnico": ("Revisión", "Asesoría técnica", "Consulta antecedentes y registra decisiones técnicas."),
    "administrador": ("Administración", "Gestión de solicitudes", "Revisa los expedientes con los permisos de tu cuenta."),
}
ROLE_LABELS = {
    "cliente": "Cliente",
    "logistica": "Logística",
    "calidad": "Control de calidad",
    "aplicador": "Aplicador",
    "asesor": "Asesor",
    "especialista_tecnico": "Especialista técnico",
    "administrador": "Administrador",
}


def icon_svg(name: str, size: int = 20) -> str:
    """Consistent, decorative Lucide-style line icon set; no remote assets."""
    paths = {
        "layout-dashboard": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
        "building-2": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01"/>',
        "folder-kanban": '<path d="M3 7V5a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M8 11v6M13 11v3M18 11v5"/>',
        "files": '<path d="M16 2H6a2 2 0 0 0-2 2v12"/><path d="M8 6h10l3 3v11a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/><path d="M17 6v4h4"/>',
        "sparkles": '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3zM5 3v4M3 5h4M20 16v5M17.5 18.5h5"/>',
        "calculator": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 7h8M8 12h1M12 12h1M16 12h1M8 17h1M12 17h1M16 17h1"/>',
        "package": '<path d="m12 2 9 5-9 5-9-5 9-5zM3 7v10l9 5 9-5V7M12 12v10M7.5 4.5l9 5"/>',
        "clipboard-check": '<rect x="5" y="4" width="14" height="18" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="m9 14 2 2 4-4"/>',
        "truck": '<path d="M3 5h12v12H3zM15 9h4l3 4v4h-7z"/><circle cx="7" cy="18" r="2"/><circle cx="19" cy="18" r="2"/>',
        "paintbrush": '<path d="m15 5 4 4M4 20a3 3 0 0 0 4-4l9-9a3 3 0 0 0-4-4L4 12c-2 2 1 5 0 8z"/>',
        "shield-check": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
        "arrow-right": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
        "layers": '<path d="m12 2 9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
    }
    path = paths.get(name, paths["layers"])
    return (
        f'<svg aria-hidden="true" width="{size}" height="{size}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f"{path}</svg>"
    )


def apply_design_system(dark: bool = False) -> None:
    """Load the single-source premium stylesheet without Markdown parsing."""
    marker = "cl-theme-dark" if dark else "cl-theme-light"
    css = (Path(__file__).resolve().parent / "premium.css").read_text(encoding="utf-8")
    st.html(
        f'<span id="{marker}" aria-hidden="true" style="display:none"></span>'
        f"<style>{css}</style>"
    )


def brand(compact: bool = False) -> None:
    subtitle = "GESTIÓN INTELIGENTE" if not compact else "UNA NUEVA FORMA DE GESTIONAR"
    st.html(
        '<div class="cl-brand" aria-label="COLORLINK">'
        f'<div class="cl-mark">{icon_svg("layers", 22)}</div>'
        '<div><span class="cl-brand-title">COLORLINK</span>'
        f'<span class="cl-brand-sub">{subtitle}</span></div></div>'
    )


def user_identity(name: str, role: str) -> None:
    safe = str(name or "Cuenta COLORLINK").strip()
    initial = escape((safe[:1] or "C").upper())
    role_title = escape(ROLE_LABELS.get(role, role.replace("_", " ").title()))
    st.html(
        '<div class="cl-user-card" aria-label="Usuario y rol actual">'
        f'<span class="cl-avatar" aria-hidden="true">{initial}</span>'
        '<span class="cl-user-details">'
        f'<span class="cl-user-name">{escape(safe)}</span>'
        f'<span class="cl-user-role">{role_title}</span></span></div>'
    )


def navigation_group(title: str) -> None:
    st.html(f'<p class="cl-nav-title">{escape(title)}</p>')


def workspace_breadcrumb(role_name: str, current_page: str) -> None:
    st.html(
        '<div class="cl-topbar">'
        '<div class="cl-crumbs" aria-label="Ubicación actual">'
        '<span>COLORLINK</span><span aria-hidden="true">/</span>'
        f'<span>{escape(role_name)}</span><span aria-hidden="true">/</span>'
        f'<strong>{escape(current_page)}</strong></div>'
        '<span class="cl-topbar-status">Espacio de trabajo</span>'
        '</div>'
    )


def page_hero(eyebrow: str, title: str, description: str, *, chip: str = "COLORLINK") -> None:
    st.html(
        '<section class="cl-hero" aria-label="Encabezado de página">'
        f'<p class="cl-hero-kicker">{escape(eyebrow)}</p>'
        f'<h1 class="cl-hero-title">{escape(title)}</h1>'
        f'<p class="cl-hero-desc">{escape(description)}</p>'
        f'<span class="cl-hero-chip">{escape(chip)}</span></section>'
    )


def metric_cards(items: list[tuple[str, int | float, str, str]]) -> None:
    cards = []
    for title, value, description, icon in items:
        cards.append(
            '<article class="cl-metric-card">'
            '<div class="cl-metric-head">'
            f'<span class="cl-metric-icon">{icon_svg(icon)}</span>{escape(str(title))}</div>'
            f'<div class="cl-metric-value">{escape(str(value))}</div>'
            f'<div class="cl-metric-foot">{escape(str(description))}</div></article>'
        )
    st.html('<div class="cl-metric-grid">' + "".join(cards) + "</div>")


def section_intro(eyebrow: str, title: str, description: str = "") -> None:
    st.html(
        f'<p class="cl-section-eyebrow">{escape(eyebrow)}</p>'
        f'<h2 class="cl-section-head">{escape(title)}</h2>'
        f'<p class="cl-section-text">{escape(description)}</p>'
    )


def module_flag(stage: str, hint: str) -> None:
    """Quiet, reusable section separator for all operating roles."""
    st.html(
        f'<p class="cl-section-flag">{escape(stage)}'
        f'<strong>{escape(hint)}</strong></p>'
    )


def auth_showcase() -> None:
    """Static visual storytelling; never suggests fictitious live activity."""
    st.html(
        '<div class="cl-auth-page"><section class="cl-auth-showcase">'
        '<div class="cl-auth-brand">COLORLINK <span style="color:#C8F18C">✳</span></div>'
        '<span class="cl-auth-tag">Tu operación, conectada</span>'
        '<h1 class="cl-auth-title">Cada proyecto.<br>'
        'Cada detalle.<br><em>Todo conectado.</em></h1>'
        '<p class="cl-auth-description">Una experiencia diseñada para llevar tus '
        'solicitudes desde el primer diagnóstico hasta la entrega final, '
        'con claridad en cada decisión.</p>'
        '<div class="cl-auth-journey" aria-label="Capacidades de COLORLINK">'
        '<div class="cl-auth-journey-item"><span class="cl-auth-journey-num">01</span>'
        '<span class="cl-auth-journey-text">Planifica proyectos y solicitudes</span></div>'
        '<div class="cl-auth-journey-item"><span class="cl-auth-journey-num">02</span>'
        '<span class="cl-auth-journey-text">Coordina revisión, materiales y ejecución</span></div>'
        '<div class="cl-auth-journey-item"><span class="cl-auth-journey-num">03</span>'
        '<span class="cl-auth-journey-text">Consulta el seguimiento y los dictámenes</span></div>'
        '</div></section></div>'
    )


def auth_form_heading() -> None:
    st.html(
        '<div class="cl-auth-form-header">'
        '<span class="cl-auth-form-eyebrow">Bienvenido a tu espacio</span>'
        '<h2 class="cl-auth-form-title">Tu trabajo empieza aquí.</h2>'
        '<p class="cl-auth-form-desc">Accede de forma segura o crea tu cuenta '
        'para comenzar a gestionar tus proyectos.</p></div>'
    )


def auth_security_note() -> None:
    st.html('<p class="cl-auth-security">Acceso protegido mediante tu cuenta personal</p>')



def record_cards(
    rows: list[dict], *, title_field: str, detail_field: str = "",
    state_field: str = "", limit: int = 3,
) -> None:
    """Accessible, informational record snapshots; original tables remain available."""
    if not isinstance(rows, list) or not rows:
        return
    cards: list[str] = []
    for row in rows[:max(1, min(limit, 6))]:
        if not isinstance(row, dict):
            continue
        raw_title = row.get(title_field)
        title = str(raw_title or "Registro sin título")
        if title_field == "id" and len(title) > 8:
            title = "#" + title[:8].upper()
        detail = str(row.get(detail_field) or "") if detail_field else ""
        status = str(row.get(state_field) or "") if state_field else ""
        cards.append(
            '<article class="cl-record-card">'
            '<span class="cl-record-ident" aria-hidden="true"></span>'
            f'<h4>{escape(title)}</h4>'
            + (f'<p>{escape(detail)}</p>' if detail else '')
            + (f'<span class="cl-record-status">{escape(status.replace("_", " "))}</span>'
               if status else '')
            + "</article>"
        )
    if cards:
        st.html('<div class="cl-record-grid" aria-label="Resumen de registros">'
                + "".join(cards) + '</div>')


def empty_state(title: str, description: str, *, icon: str = "files") -> None:
    """Presentational empty-state. Does not imply any record was created."""
    st.html(
        '<div class="cl-empty-state" role="status">'
        f'<span class="cl-empty-icon">{icon_svg(icon, 24)}</span>'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(description)}</p></div>'
    )


def journey_hint(label: str, title: str, details: str) -> None:
    """Contextual workflow guidance, not a fabricated persisted event."""
    st.html(
        '<aside class="cl-journey-hint">'
        '<span class="cl-journey-mark" aria-hidden="true">✳</span>'
        '<div class="cl-journey-copy">'
        f'<span>{escape(label)}</span>'
        f'<strong>{escape(title)}</strong>'
        f'<p>{escape(details)}</p></div>'
        '</aside>'
    )
