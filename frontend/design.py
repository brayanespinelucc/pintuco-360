"""COLORLINK visual design system.

Presentation-only primitives: no API clients, role mutations, persistence or data models.
Compatible with the existing Streamlit application and its native form controls.
"""
from __future__ import annotations

from html import escape
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
    """Render isolated CSS overrides for Streamlit, with a proper dark palette."""
    marker = "cl-theme-dark" if dark else "cl-theme-light"
    css = r"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
[data-testid="stApp"] {
  --cl-bg: #F5F7FB;
  --cl-panel: #FFFFFF;
  --cl-panel-soft: #F8FAFD;
  --cl-text: #172238;
  --cl-heading: #111D36;
  --cl-muted: #64748B;
  --cl-border: #E5EAF2;
  --cl-primary: #2959D6;
  --cl-primary-hover: #2149B4;
  --cl-primary-weak: #EAF0FF;
  --cl-turquoise: #0E948D;
  --cl-success: #13845A;
  --cl-shadow: 0 4px 22px rgba(20, 39, 83, .045), 0 1px 2px rgba(20, 39, 83, .025);
  font-family: "DM Sans", system-ui, -apple-system, sans-serif;
  color: var(--cl-text);
}
[data-testid="stApp"]:has(#cl-theme-dark) {
  --cl-bg: #0A1221;
  --cl-panel: #121D31;
  --cl-panel-soft: #18253C;
  --cl-text: #DAE4F3;
  --cl-heading: #F1F5FD;
  --cl-muted: #A7B5C9;
  --cl-border: #2A3952;
  --cl-primary: #80A4FF;
  --cl-primary-hover: #9DB7FF;
  --cl-primary-weak: #1B3151;
  --cl-turquoise: #4EDFD1;
  --cl-success: #60D8A2;
  --cl-shadow: 0 8px 30px rgba(0,0,0,.16);
}
html, body, [data-testid="stApp"], [data-testid="stApp"] button, [data-testid="stApp"] input,
[data-testid="stApp"] textarea, [data-testid="stApp"] select {
  font-family: "DM Sans", system-ui, sans-serif;
}
[data-testid="stAppViewContainer"], [data-testid="stApp"] { background: var(--cl-bg); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] {
  max-width: 1390px; padding-top: 1.35rem; padding-bottom: 4.5rem;
  padding-left: clamp(1rem,3.4vw,3.3rem); padding-right: clamp(1rem,3.4vw,3.3rem);
}
[data-testid="stSidebar"] {
  background: var(--cl-panel);
  border-right: 1px solid var(--cl-border);
}
[data-testid="stSidebar"] > div:first-child { padding-top: .6rem; }
[data-testid="stSidebar"] .stRadio > label p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: var(--cl-muted); }
[data-testid="stSidebar"] div[role="radiogroup"] { gap: .16rem; }
[data-testid="stSidebar"] div[role="radiogroup"] > label {
  border-radius: 11px; padding: .57rem .67rem;
  min-height: 39px; transition: background .16s ease, transform .16s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: var(--cl-panel-soft); }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: var(--cl-primary-weak);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
  color: var(--cl-primary); font-weight: 800;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label p {
  color: var(--cl-text); font-size: .875rem; font-weight: 600;
}
[data-testid="stSidebar"] .stDivider { margin-top: .8rem; margin-bottom: .65rem; }
h1,h2,h3,h4,h5,h6,
[data-testid="stHeadingWithActionElements"] * {
  font-family: "Manrope","DM Sans",system-ui,sans-serif;
  color: var(--cl-heading);
  letter-spacing: -.025em;
}
h1 { font-size: clamp(1.65rem, 3vw, 2.25rem) !important; font-weight: 800 !important; }
h2 { font-size: 1.5rem !important; font-weight: 800 !important; }
h3 { font-size: 1.16rem !important; font-weight: 750 !important; }
[data-testid="stCaptionContainer"] p, .stCaption p { color: var(--cl-muted); }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { line-height: 1.65; }
[data-testid="stMarkdownContainer"] strong { color: var(--cl-heading); }
[data-testid="stForm"] {
  border: 1px solid var(--cl-border); background: var(--cl-panel);
  border-radius: 18px; padding: clamp(1rem,2vw,1.55rem);
  box-shadow: var(--cl-shadow);
}
[data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {
  border-radius: 16px;
}
[data-testid="stMetric"] {
  background: var(--cl-panel); border: 1px solid var(--cl-border);
  border-radius: 16px; padding: 1rem 1.2rem; box-shadow: var(--cl-shadow);
}
[data-testid="stMetricValue"] { color: var(--cl-heading); font-weight: 800; }
[data-testid="stMetricLabel"] { color: var(--cl-muted); font-weight: 600; }
[data-testid="stDataFrame"] {
  border: 1px solid var(--cl-border); border-radius: 14px;
  overflow: hidden; background: var(--cl-panel);
}
[data-testid="stExpander"] {
  background: var(--cl-panel); border: 1px solid var(--cl-border);
  border-radius: 14px; overflow: hidden;
}
[data-testid="stExpander"] details { border: 0; }
[data-testid="stExpander"] summary:hover { background: var(--cl-panel-soft); }
[data-testid="stFileUploader"] {
  background: var(--cl-panel-soft); border-radius: 14px;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
  border-radius: 11px !important;
  background: var(--cl-panel) !important; color: var(--cl-text) !important;
  border-color: var(--cl-border) !important;
}
[data-testid="stWidgetLabel"] p { color: var(--cl-text); font-weight: 650; }
div.stButton > button, div.stFormSubmitButton > button {
  border-radius: 11px; min-height: 2.6rem; font-weight: 750;
  transition: box-shadow .16s ease, transform .16s ease, background .16s ease;
  border-color: var(--cl-border);
  background: var(--cl-panel); color: var(--cl-text);
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
  border-color: var(--cl-primary); color: var(--cl-primary);
  box-shadow: 0 6px 14px rgba(38,91,196,.11); transform: translateY(-1px);
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
  background: #2959D6; color: #fff; border-color: #2959D6;
  box-shadow: 0 3px 9px rgba(41,89,214,.15);
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
  background: #2149B4; border-color: #2149B4; color: #fff;
}
div.stButton > button:disabled,
div.stFormSubmitButton > button:disabled { opacity: .5; transform: none; box-shadow: none; }
button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="radio"]:focus-visible, [tabindex]:focus-visible {
  outline: 3px solid var(--cl-turquoise) !important; outline-offset: 3px !important;
}
[data-testid="stAlert"] { border-radius: 13px; }
[data-testid="stProgressBar"] > div > div { background: #16A5A1 !important; }
hr { border-color: var(--cl-border); }
.cl-brand {
  display: flex; gap: .72rem; align-items: center; margin: .35rem 0 1.1rem;
}
.cl-mark {
  width: 37px; height: 37px; display: grid; place-items: center;
  border-radius: 11px; background: linear-gradient(135deg,#255AD7,#0DA7A0);
  color: white; flex-shrink: 0; box-shadow: 0 6px 12px rgba(37,90,215,.14);
}
.cl-brand-title { color: var(--cl-heading); font: 800 1.12rem/1.2 "Manrope",sans-serif; letter-spacing: -.04em; }
.cl-brand-sub { display: block; color: var(--cl-muted); font-size: .68rem; font-weight: 750; letter-spacing: .12em; margin-top: 2px; }
.cl-user-card { border-radius: 13px; background: var(--cl-panel-soft);
  border: 1px solid var(--cl-border); padding: .85rem .9rem; margin: 0 0 1.2rem; }
.cl-user-name { color: var(--cl-heading); font-weight: 800; font-size: .88rem; overflow-wrap: anywhere; }
.cl-user-role { color: var(--cl-muted); font-size: .76rem; padding-top: .2rem; font-weight: 600; }
.cl-nav-label { color: var(--cl-muted); font-size: .68rem; text-transform: uppercase;
  letter-spacing: .17em; font-weight: 800; margin: .3rem 0 .6rem; }
.cl-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(112deg,#172A50 0%,#213D70 58%,#176C81 100%);
  border-radius: 22px; padding: clamp(1.25rem,3vw,2.15rem) clamp(1.25rem,3vw,2.4rem);
  margin: .65rem 0 1.45rem; isolation: isolate;
  box-shadow: 0 11px 25px rgba(14,34,72,.1); min-height: 142px;
}
.cl-hero::before, .cl-hero::after { content: ""; position: absolute; z-index: -1;
  border: 1px solid rgba(255,255,255,.17); border-radius: 50%; }
.cl-hero::before { width: 270px; height: 270px; right: -50px; top: -170px; }
.cl-hero::after { width: 190px; height: 190px; right: 100px; bottom: -175px; }
.cl-hero-kicker {
  color: #A4E9E4; font-size: .69rem; letter-spacing: .18em;
  text-transform: uppercase; font-weight: 800; margin: 0 0 .55rem;
}
.cl-hero-title {
  color: #FFF !important; font: 800 clamp(1.55rem,3vw,2.25rem)/1.2 "Manrope",sans-serif !important;
  letter-spacing: -.035em; margin: 0 0 .65rem; max-width: 750px;
}
.cl-hero-desc { color: #DDEAF9; line-height: 1.62; font-size: .9rem; max-width: 700px; margin: 0; }
.cl-hero-chip { position: absolute; top: 1.3rem; right: 1.4rem; padding: .32rem .72rem;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
  color: #fff; border-radius: 30px; font-size: .7rem; font-weight: 700;
  backdrop-filter: blur(8px); }
.cl-metric-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
  gap: 1rem; margin: .6rem 0 1.5rem; }
.cl-metric-card { background: var(--cl-panel); border:1px solid var(--cl-border);
  border-radius:17px; padding: 1.25rem 1.3rem; box-shadow:var(--cl-shadow); }
.cl-metric-head { display:flex; align-items:center; gap:.65rem; color:var(--cl-muted);
  font-size: .8rem; font-weight:700; }
.cl-metric-icon { display:grid; place-items:center; height:34px; width:34px;
  background:var(--cl-primary-weak); color:var(--cl-primary); border-radius:10px; }
.cl-metric-value { color:var(--cl-heading); font:800 2rem/1.25 "Manrope",sans-serif;
  letter-spacing:-.05em; margin:.62rem 0 .2rem; }
.cl-metric-foot { color:var(--cl-muted); font-size:.73rem; }
.cl-section-eyebrow { text-transform: uppercase; font-size: .7rem; font-weight: 800;
  letter-spacing: .15em; color: var(--cl-turquoise); }
.cl-section-head { margin:1.45rem 0 .4rem; color:var(--cl-heading);
  font:800 1.2rem/1.3 "Manrope",sans-serif; letter-spacing:-.03em; }
.cl-section-text { color:var(--cl-muted); font-size:.84rem; margin:0 0 1rem; }
.cl-login-mark { display:flex; justify-content:center; margin: 1.5rem auto .7rem; }
.cl-login-intro { color: var(--cl-muted); text-align:center; margin:0 auto 1.5rem;
 max-width: 32rem; font-size:.94rem; line-height:1.65; }
.cl-footnote { font-size: .72rem; color:var(--cl-muted); line-height:1.6; margin-top:1rem; }
[data-testid="stApp"]:has(#cl-theme-dark) .cl-hero {
 background:linear-gradient(115deg,#20345A,#1B3856 70%,#15494E); box-shadow:0 13px 30px rgba(0,0,0,.18);
}
[data-testid="stApp"]:has(#cl-theme-dark) [data-testid="stDataFrame"] {
 filter: brightness(.91);
}


.cl-event-timeline {
  list-style:none; margin:.8rem 0 1.35rem; padding:0 0 0 .7rem;
  border-left:2px solid var(--cl-border);
}
.cl-event-item { position:relative; padding:0 0 1rem 1.35rem; }
.cl-event-item:last-child { padding-bottom:0; }
.cl-event-dot {
  position:absolute; left:-.43rem; top:.32rem; height:.72rem; width:.72rem;
  background:var(--cl-turquoise); border-radius:50%;
  border:3px solid var(--cl-panel); box-shadow:0 0 0 2px var(--cl-border);
}
.cl-event-body { padding:.1rem 0 .2rem; }
.cl-event-head {
  display:flex; align-items:baseline; justify-content:space-between;
  gap:.65rem; flex-wrap:wrap;
}
.cl-event-head strong { color:var(--cl-heading); font-size:.88rem; font-weight:800; }
.cl-event-head time { color:var(--cl-muted); font-size:.72rem; }
.cl-event-body p {
  color:var(--cl-text); font-size:.8rem; line-height:1.55;
  margin:.4rem 0 0; white-space:pre-wrap; overflow-wrap:anywhere;
}

/* Process-first components: passive HTML, native Streamlit for all actions. */
.cl-process-summary {
  border:1px solid var(--cl-border); background:var(--cl-panel);
  box-shadow:var(--cl-shadow); border-radius:20px; padding:1.35rem 1.5rem;
  margin:.6rem 0 1rem; position:relative; overflow:hidden;
}
.cl-process-summary::before {
  content:""; position:absolute; left:0; top:0; bottom:0; width:4px;
  background:linear-gradient(180deg,var(--cl-primary),var(--cl-turquoise));
}
.cl-process-summary-top {
  display:flex; align-items:flex-start; justify-content:space-between;
  gap:1rem; flex-wrap:wrap;
}
.cl-process-eyebrow {
  color:var(--cl-turquoise); font-size:.69rem; font-weight:800;
  text-transform:uppercase; letter-spacing:.13em; margin:0 0 .35rem;
}
.cl-process-summary-title {
  color:var(--cl-heading); font:800 1.25rem/1.35 "Manrope",sans-serif;
  margin:0 0 .25rem;
}
.cl-process-summary-meta {
  font-size:.76rem; color:var(--cl-muted); margin:0;
  overflow-wrap:anywhere;
}
.cl-process-hint {
  font-size:.875rem; color:var(--cl-text); line-height:1.6; margin:.95rem 0 0;
}
.cl-status-pill {
  display:inline-flex; align-items:center; flex-shrink:0;
  font-size:.74rem; font-weight:800; border-radius:99px;
  padding:.4rem .75rem; border:1px solid var(--cl-border);
  background:var(--cl-primary-weak); color:var(--cl-primary);
}
.cl-status-pill::before {
  content:""; width:.45rem; height:.45rem; background:currentColor;
  border-radius:100%; margin-right:.5rem;
}
.cl-status-done { color:var(--cl-success); background:var(--cl-panel-soft); }
.cl-status-blocked { color:#B55B2C; background:var(--cl-panel-soft); }
.cl-process-scroll { max-width:100%; overflow-x:auto; overflow-y:hidden; margin:0 0 1.45rem;
  padding:.4rem .15rem .7rem; scrollbar-width:thin; }
.cl-process-scroll:focus-visible { outline:3px solid var(--cl-turquoise); outline-offset:3px; }
.cl-process-steps {
  list-style:none; display:flex; gap:.48rem;
  min-width:760px; padding:0; margin:0;
}
.cl-step {
  position:relative; flex:1 1 0; min-width:96px;
  display:flex; align-items:flex-start; gap:.55rem;
  background:var(--cl-panel); border:1px solid var(--cl-border);
  border-radius:12px; padding:.74rem .7rem; color:var(--cl-muted);
  transition:background .16s ease, border-color .16s ease;
}
.cl-step:not(:last-child)::after {
  content:""; position:absolute; width:.48rem; height:2px;
  top:50%; left:100%; background:var(--cl-border);
}
.cl-step-icon {
  width:29px; height:29px; flex-shrink:0; border-radius:9px;
  display:grid; place-items:center; background:var(--cl-panel-soft);
  color:var(--cl-muted);
}
.cl-step-content { display:flex; min-width:0; flex-direction:column; gap:.22rem; }
.cl-step-name { font-size:.77rem; font-weight:800; line-height:1.3; color:var(--cl-text); }
.cl-step-owner { font-size:.66rem; line-height:1.25; color:var(--cl-muted); }
.cl-step-state { font-size:.65rem; line-height:1.25; color:var(--cl-muted); }
.cl-step-anterior { border-color:color-mix(in srgb,var(--cl-success) 35%,var(--cl-border)); }
.cl-step-anterior .cl-step-icon { background:var(--cl-panel-soft); color:var(--cl-success); }
.cl-step-actual {
  background:var(--cl-primary-weak); border-color:var(--cl-primary);
  box-shadow:0 0 0 1px color-mix(in srgb,var(--cl-primary) 18%,transparent);
}
.cl-step-actual .cl-step-icon { background:var(--cl-primary); color:var(--cl-panel); }
.cl-step-actual .cl-step-name, .cl-step-actual .cl-step-state { color:var(--cl-primary); }
.cl-step-pendiente { opacity:.8; }
.cl-state-list { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.55rem;
  margin:.6rem 0 1.25rem; }
.cl-state-item { background:var(--cl-panel); border:1px solid var(--cl-border);
  border-radius:12px; padding:.7rem .85rem; display:flex; gap:.8rem; align-items:center; }
.cl-state-count { font:800 1.2rem/1 "Manrope",sans-serif; color:var(--cl-primary); }
.cl-state-name { color:var(--cl-text); font-size:.76rem; font-weight:650; }
@media (max-width:900px) { .cl-state-list { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:600px) {
 .cl-process-summary { padding:1.05rem 1.1rem; }
 .cl-process-summary-title { font-size:1.1rem; }
 .cl-process-steps { min-width:700px; }
 .cl-step { padding:.6rem; gap:.35rem; }
 .cl-step-icon { width:24px; height:24px; }
 .cl-state-list { grid-template-columns:1fr; }
}

@media (max-width:800px) {
 [data-testid="stMainBlockContainer"] { padding-top: .65rem; padding-left: 1rem; padding-right: 1rem; }
 .cl-hero { border-radius: 17px; min-height: 0; padding: 1.35rem 1.2rem; }
 .cl-hero-chip { position: static; display:inline-block; margin-top: .85rem; }
 .cl-metric-grid { grid-template-columns: 1fr; gap: .7rem; }
 .cl-metric-card { padding: 1.05rem; }
 .cl-metric-value { font-size:1.7rem; }
 div.stButton > button { min-height:2.85rem; }
}

/* COLORLINK STUDIO / Premium editorial design language, 2026.
   Single source of truth for all Streamlit native controls and role screens. */
[data-testid="stApp"] {
  --cl-bg:#F0F3F7;
  --cl-panel:#FFFFFF;
  --cl-panel-soft:#F6F8FB;
  --cl-text:#28354B;
  --cl-heading:#0A1730;
  --cl-muted:#596B82;
  --cl-border:#DFE5EE;
  --cl-primary:#2861E7;
  --cl-primary-hover:#174ECC;
  --cl-primary-weak:#ECF2FF;
  --cl-turquoise:#00786F;
  --cl-success:#137E5A;
  --cl-shadow:0 8px 36px rgba(18,36,67,.055), 0 1px 3px rgba(18,36,67,.025);
  background:
    radial-gradient(ellipse 900px 540px at 94% -9%,rgba(48,132,226,.11),transparent 70%),
    radial-gradient(ellipse 610px 520px at 0% 99%,rgba(13,167,158,.045),transparent 70%),
    var(--cl-bg);
}
[data-testid="stApp"]:has(#cl-theme-dark) {
  --cl-bg:#080F1D; --cl-panel:#101C2D; --cl-panel-soft:#17253B;
  --cl-text:#CAD6EA; --cl-heading:#F6F8FE; --cl-muted:#9BABBF;
  --cl-border:#273750; --cl-primary:#93B5FF; --cl-primary-hover:#B1C9FF;
  --cl-primary-weak:#203551; --cl-turquoise:#74E2D1; --cl-success:#76E0B1;
  --cl-shadow:0 16px 48px rgba(0,0,0,.16);
  background:
    radial-gradient(ellipse 850px 620px at 95% -5%,rgba(41,96,188,.14),transparent 73%),var(--cl-bg);
}
[data-testid="stAppViewContainer"] {background:transparent;}
[data-testid="stHeader"] {height:2.25rem; background:transparent;}
[data-testid="stMainBlockContainer"] {
  max-width:1470px !important;
  padding:1.05rem clamp(1.2rem,3.8vw,4.3rem) 5rem !important;
}
[data-testid="stSidebar"] {
  background:var(--cl-panel);
  border-right:1px solid var(--cl-border);
  box-shadow:7px 0 35px rgba(17,42,79,.018);
}
[data-testid="stSidebar"] > div:first-child {padding-top:1.3rem;}
[data-testid="stSidebar"] div[role="radiogroup"] {gap:.2rem;}
[data-testid="stSidebar"] div[role="radiogroup"] > label {
  position:relative; padding:.7rem .88rem;
  border-radius:12px; transition:background .18s ease,color .18s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){
  background:var(--cl-primary-weak); box-shadow:inset 0 0 0 1px rgba(73,121,218,.08);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::before{
  content:"";position:absolute;left:0;top:24%;bottom:24%;
  width:3px;border-radius:0 3px 3px 0;background:var(--cl-primary);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label p {font-weight:620;letter-spacing:-.01em;}
.cl-brand {gap:.75rem;margin:.1rem 0 1.7rem;}
.cl-mark {
  border-radius:14px;width:44px;height:44px;
  background:linear-gradient(145deg,#17295A 3%,#2861E7 57%,#00A99D);
  box-shadow:0 10px 22px rgba(35,91,205,.20);
}
.cl-brand-title{font-size:1.23rem;letter-spacing:-.055em;}
.cl-brand-sub{font-size:.61rem;letter-spacing:.19em;}
.cl-user-card{
  background:linear-gradient(125deg,var(--cl-panel-soft),var(--cl-panel));
  border:1px solid var(--cl-border);border-radius:15px;
  padding:1rem 1.05rem;margin:0 0 1.45rem;
}
.cl-user-role{display:flex;gap:.35rem;align-items:center;}
.cl-user-role::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--cl-success);}
.cl-nav-label{font-size:.64rem;letter-spacing:.19em;margin:1rem 0 .5rem;}
/* App header: different information hierarchy from Streamlit's generic headings. */
.cl-workspace-bar{
 display:flex;align-items:center;justify-content:space-between;gap:1rem;
 padding:.3rem 0 1rem;border-bottom:1px solid var(--cl-border);margin-bottom:1.3rem;
}
.cl-crumb{display:flex;align-items:center;gap:.62rem;color:var(--cl-muted);
 font-size:.76rem;flex-wrap:wrap;}
.cl-crumb strong{color:var(--cl-heading);font-weight:750;}
.cl-crumb-sep{color:var(--cl-muted);opacity:.5;}
.cl-workspace-status{
 display:inline-flex;align-items:center;gap:.48rem;
 color:var(--cl-muted);font-size:.73rem;font-weight:700;
 border:1px solid var(--cl-border);background:var(--cl-panel);padding:.43rem .72rem;border-radius:50px;
}
.cl-workspace-status::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--cl-success);}
.cl-hero{
  min-height:190px;margin:.1rem 0 1.7rem;
  background:
    radial-gradient(ellipse 320px 250px at 85% 0%,rgba(104,191,228,.32),transparent 70%),
    linear-gradient(118deg,#101D39 0%,#19345D 54%,#0C6475 115%);
  border:1px solid rgba(255,255,255,.1);
  border-radius:23px;padding:clamp(1.45rem,3vw,2.25rem) clamp(1.5rem,3.3vw,2.65rem);
  box-shadow:0 16px 45px rgba(19,39,73,.14);
}
.cl-hero::before{width:390px;height:390px;right:-100px;top:-220px;border-color:rgba(255,255,255,.13);}
.cl-hero::after{width:280px;height:280px;right:65px;bottom:-245px;border-color:rgba(255,255,255,.09);}
.cl-hero-kicker{font-size:.65rem;letter-spacing:.23em;color:#81E5DB;}
.cl-hero-title{font-size:clamp(1.85rem,3.1vw,2.7rem)!important;max-width:780px;letter-spacing:-.05em!important;}
.cl-hero-desc{font-size:.93rem;max-width:660px;color:#DEEAF7;}
.cl-hero-chip{background:rgba(18,174,161,.20);border-color:rgba(159,243,225,.26);font-size:.63rem;letter-spacing:.065em;}
/* Every module adopts this typography and compositional rhythm. */
.cl-section-head{font-size:1.3rem;letter-spacing:-.045em;margin-top:1.7rem;}
.cl-section-eyebrow{color:var(--cl-turquoise);letter-spacing:.19em;}
h1,h2,h3,h4,h5,h6{letter-spacing:-.04em!important;}
[data-testid="stForm"] {
 background:var(--cl-panel);
 border:1px solid var(--cl-border);
 border-radius:20px;
 padding:clamp(1.15rem,2.1vw,1.8rem);
 box-shadow:var(--cl-shadow);
}
[data-testid="stForm"]:focus-within{border-color:color-mix(in srgb,var(--cl-primary) 43%,var(--cl-border));}
[data-testid="stWidgetLabel"] p{font-weight:660;}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"]>div {
 border-radius:12px!important; min-height:2.7rem;
 border:1px solid var(--cl-border)!important;
 transition:border-color .16s ease,box-shadow .16s ease;
}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus{
 border-color:var(--cl-primary)!important;
 box-shadow:0 0 0 3px color-mix(in srgb,var(--cl-primary) 13%,transparent)!important;
}
div.stButton > button,div.stFormSubmitButton > button {
 border-radius:12px;min-height:2.85rem;font-weight:720;
 transition:transform .17s ease,background .17s ease,box-shadow .17s ease;
}
div.stButton > button[kind="primary"],div.stFormSubmitButton > button[kind="primary"]{
 background:linear-gradient(115deg,#1D50D7,#3478ED);
 border-color:#235BD8;color:white;box-shadow:0 7px 17px rgba(38,96,217,.20);
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
 background:linear-gradient(115deg,#1847C2,#2068E5);transform:translateY(-1px);
 box-shadow:0 12px 22px rgba(38,96,217,.24);color:white;
}
[data-testid="stAlert"]{border:1px solid var(--cl-border);border-radius:15px;}
[data-testid="stMetric"]{border-radius:17px;box-shadow:var(--cl-shadow);}
[data-testid="stMetricValue"]{font-size:clamp(1.35rem,2.3vw,1.85rem);}
[data-testid="stDataFrame"]{border-radius:16px;box-shadow:var(--cl-shadow);}
[data-testid="stExpander"]{border-radius:15px;box-shadow:var(--cl-shadow);}
[data-testid="stTabs"] [role="tablist"] {
 border-bottom:1px solid var(--cl-border);gap:.7rem;
}
[data-testid="stTabs"] button[role="tab"]{font-weight:720;padding:.75rem 1.1rem;letter-spacing:-.01em;}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--cl-primary)!important;}
[data-testid="stFileUploader"]{border:1px dashed var(--cl-border);padding:.45rem;border-radius:15px;}
.cl-metric-grid{gap:.9rem;}
.cl-metric-card{border-radius:18px;padding:1.3rem;box-shadow:var(--cl-shadow);}
.cl-metric-icon{border-radius:12px;width:39px;height:39px;}
.cl-metric-value{font-size:2.1rem;}
.cl-process-summary{border-radius:19px;padding:1.65rem;}
.cl-process-summary::before{width:5px;}
.cl-step{border-radius:13px;}
.cl-step-actual{background:var(--cl-primary-weak);}
.cl-state-item{border-radius:13px;box-shadow:var(--cl-shadow);}
.cl-event-timeline{margin-top:1.1rem;}
/* Premium split-screen login and self-service registration. */
.cl-auth-showcase{
 position:relative;isolation:isolate;overflow:hidden;
 min-height:645px;padding:clamp(2rem,4vw,3.5rem);
 border:1px solid rgba(255,255,255,.11);
 border-radius:26px;
 background:
  radial-gradient(circle at 88% 22%,rgba(74,204,202,.34),transparent 28%),
  radial-gradient(circle at 13% 91%,rgba(34,97,239,.34),transparent 34%),
  linear-gradient(140deg,#0B1831 0%,#182D53 58%,#074E61 115%);
 box-shadow:0 22px 60px rgba(10,26,60,.19); color:white;
 display:flex;flex-direction:column;justify-content:space-between;
}
.cl-auth-showcase::before{
 content:"";position:absolute;z-index:-1;right:-165px;top:105px;
 width:510px;height:510px;border-radius:50%;
 border:1px solid rgba(255,255,255,.16);
 box-shadow:0 0 0 45px rgba(255,255,255,.026),0 0 0 100px rgba(255,255,255,.018);
}
.cl-auth-eyebrow{font-size:.7rem;letter-spacing:.26em;font-weight:750;color:#A3E7E2;text-transform:uppercase;}
.cl-auth-headline{
 font:800 clamp(2.5rem,4.2vw,4.4rem)/1.11 "Manrope",sans-serif;
 max-width:580px;letter-spacing:-.067em;margin:1.15rem 0 1.4rem;color:#FFF;
}
.cl-auth-headline em{font-style:normal;color:#80E0D7;}
.cl-auth-sub{color:#D3DFEE;font-size:1.05rem;line-height:1.7;max-width:490px;}
.cl-auth-badges{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:2rem;}
.cl-auth-badges span{
 padding:.65rem .84rem;border-radius:10px;color:#EAF6FF;
 background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.14);
 font-size:.73rem;font-weight:700;
}
.cl-auth-bottom{font-size:.72rem;color:#AEC0DA;font-weight:600;letter-spacing:.05em;}
.cl-auth-form-eyebrow{text-transform:uppercase;letter-spacing:.18em;
 font-size:.68rem;color:var(--cl-turquoise);font-weight:800;}
.cl-auth-form-title{font:800 clamp(1.7rem,2.7vw,2.35rem)/1.18 "Manrope",sans-serif;
 letter-spacing:-.055em;color:var(--cl-heading);margin:.7rem 0 .6rem;}
.cl-auth-form-sub{font-size:.84rem;color:var(--cl-muted);line-height:1.65;margin:0 0 1.6rem;}
[data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) {
  max-width:1480px!important;
  padding-top:1rem!important;
}
[data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) [data-testid="stVerticalBlock"]{
  min-width:0;
}
[data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) [data-testid="stTabs"]{background:var(--cl-panel);padding:1rem 1.35rem 1.3rem;
 border:1px solid var(--cl-border);border-radius:19px;box-shadow:var(--cl-shadow);}
[data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) [data-testid="stForm"]{box-shadow:none;border:none;padding:.7rem 0;background:transparent;}


/* Accessible touch targets and focus states across all native role controls. */
[data-testid="stApp"] button:focus-visible,
[data-testid="stApp"] [role="tab"]:focus-visible,
[data-testid="stApp"] [role="radio"]:focus-visible,
[data-testid="stApp"] [data-baseweb="select"] :focus-visible {
  outline:3px solid var(--cl-turquoise)!important;
  outline-offset:3px!important;
}
[data-testid="stSidebar"] [role="radiogroup"]>label {min-height:44px;}
[data-testid="stTabs"] button[role="tab"]{min-height:44px;}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]{
  border-radius:13px;min-height:90px;
  background:var(--cl-panel-soft);
}
[data-testid="stApp"] :is(.cl-record-card,.cl-step-intro,.cl-metric-card,.cl-auth-showcase) {
  overflow-wrap:anywhere;
}

/* Shared content primitives — entity lists, cards, guided forms. */
.cl-record-gallery-heading{
 display:flex;justify-content:space-between;align-items:center;gap:.7rem;
 margin:1.45rem 0 .8rem;flex-wrap:wrap;
}
.cl-record-gallery-heading strong{
 color:var(--cl-heading);font:800 1rem/1.3 "Manrope",sans-serif;letter-spacing:-.025em;
}
.cl-record-gallery-heading span{font-size:.75rem;color:var(--cl-muted);}
.cl-record-grid{
 display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;
 margin-bottom:1.1rem;
}
.cl-record-card{
 min-height:174px;border:1px solid var(--cl-border);border-radius:18px;
 background:var(--cl-panel);padding:1.25rem 1.35rem;
 box-shadow:var(--cl-shadow);
 transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
 overflow:hidden;
}
.cl-record-card:hover{
 transform:translateY(-2px);
 border-color:color-mix(in srgb,var(--cl-primary) 42%,var(--cl-border));
 box-shadow:0 14px 38px rgba(12,35,70,.085);
}
.cl-record-top{display:flex;justify-content:space-between;align-items:center;}
.cl-record-monogram{
 display:grid;place-items:center;
 width:36px;height:36px;border-radius:12px;
 background:var(--cl-primary-weak);color:var(--cl-primary);
 font:800 1rem/1 "Manrope",sans-serif;
}
.cl-record-badge{
 font-size:.66rem;font-weight:750;color:var(--cl-primary);
 background:var(--cl-primary-weak);padding:.36rem .64rem;border-radius:100px;
 max-width:65%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.cl-record-card h3{
 margin:.9rem 0 .25rem;font-size:.97rem!important;
 line-height:1.38;letter-spacing:-.025em;
 overflow-wrap:anywhere;
}
.cl-record-description{
 font-size:.77rem;color:var(--cl-muted);line-height:1.45;margin:0 0 .6rem;
 overflow-wrap:anywhere;
}
.cl-record-footer{
 border-top:1px solid var(--cl-border);padding-top:.7rem;
 margin-top:.85rem;display:flex;gap:1rem;flex-wrap:wrap;
}
.cl-record-meta{display:flex;flex-direction:column;gap:.15rem;font-size:.7rem;min-width:0;}
.cl-record-meta small{font-size:.65rem;color:var(--cl-muted);}
.cl-record-meta strong{font-size:.73rem;color:var(--cl-heading);overflow-wrap:anywhere;}
.cl-record-more{font-size:.75rem;color:var(--cl-muted);}
.cl-step-intro{
 display:flex;align-items:center;gap:1rem;margin:1.25rem 0 1rem;
 background:var(--cl-panel);border:1px solid var(--cl-border);
 border-radius:17px;padding:1.05rem 1.25rem;
}
.cl-step-number{
 flex-shrink:0;width:38px;height:38px;display:grid;place-items:center;
 background:var(--cl-primary-weak);color:var(--cl-primary);
 border-radius:12px;font:800 .85rem/1 "Manrope",sans-serif;
}
.cl-step-intro h3{font-size:.94rem!important;margin:0 0 .25rem;}
.cl-step-intro p{font-size:.76rem;color:var(--cl-muted);margin:0;line-height:1.5;}
@media(max-width:1050px){.cl-record-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media(max-width:650px){
 .cl-record-grid{grid-template-columns:1fr;}
 .cl-record-card{min-height:0;}
 .cl-step-intro{padding:.9rem;}
}


/* Visual QA regression: real browser showed default Streamlit heading ink in
   the dark hero despite the class-specific heading declaration. */
[data-testid="stApp"] .cl-hero h1.cl-hero-title {
  color:#FFFFFF!important;
  -webkit-text-fill-color:#FFFFFF!important;
}
/* Streamlit developer/Deploy chrome is not part of the customer product.
   Keep the sidebar expand/collapse control in the separate stSidebar header. */
/* Preserve the toolbar shell: Streamlit places the mobile sidebar opener there. */
[data-testid="stDeployButton"], #MainMenu, [data-testid="stMainMenu"] {
  display:none!important;
}
[data-testid="stDecoration"] {display:none!important;}
@media(max-width:750px){
  [data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) {
    padding-top:.4rem!important;
  }
  .cl-auth-showcase {
    min-height:245px;
    padding:1.1rem 1.25rem;
  }
  .cl-auth-headline {font-size:1.9rem;line-height:1.1;margin:.75rem 0;}
  .cl-auth-sub {font-size:.84rem;line-height:1.5;margin:0;}
  .cl-auth-badges {margin-top:.75rem;gap:.35rem;}
  .cl-auth-badges span {padding:.38rem .55rem;font-size:.62rem;}
  .cl-auth-bottom {display:none;}
}

/* Reduced motion takes priority over decorative transitions. */
@media(max-width:1000px){
 .cl-auth-showcase{min-height:420px;padding:2rem;}
 .cl-auth-headline{font-size:2.7rem;}
}
@media(max-width:750px){
 [data-testid="stMainBlockContainer"]{padding:1rem 1rem 4rem!important;}
 .cl-workspace-bar{align-items:flex-start;}
 .cl-workspace-status{font-size:.67rem;}
 .cl-hero{border-radius:17px;min-height:0;padding:1.4rem 1.3rem;}
 .cl-hero-chip{position:static;display:inline-block;margin-top:1rem;}
 .cl-auth-showcase{min-height:330px;padding:1.5rem;border-radius:19px;}
 .cl-auth-headline{font-size:2.2rem;max-width:425px;}
 .cl-auth-sub{font-size:.9rem;}
 .cl-auth-badges{margin-top:1.2rem;}

 [data-testid="stMainBlockContainer"]:has(.cl-auth-showcase) [data-testid="stTabs"]{padding:.75rem;}
 .cl-metric-card{padding:1.08rem;}
}
@media(prefers-reduced-motion:reduce){
 *,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important;}
}

@media (prefers-reduced-motion:reduce) {
 *, *::before,*::after { animation-duration:.01ms !important;
 transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
"""
    # st.markdown interpreta HTML inline mezclado con <style> como Markdown.
    # st.html aplica los estilos sin mostrar CSS como texto en la página.
    # La etiqueta del tema sigue dentro del mismo árbol DOM de Streamlit.
    st.html(
        f'<span id="{marker}" aria-hidden="true" style="display:none"></span>'
        f'<style>{css}</style>'
    )


def brand(compact: bool = False) -> None:
    label = "GESTIÓN DE PROYECTOS" if not compact else "PLATAFORMA COLORLINK"
    st.markdown(
        '<div class="cl-brand">'
        f'<div class="cl-mark">{icon_svg("layers", 22)}</div>'
        '<div><span class="cl-brand-title">COLORLINK</span>'
        f'<span class="cl-brand-sub">{label}</span></div></div>',
        unsafe_allow_html=True,
    )


def user_identity(name: str, role: str) -> None:
    st.markdown(
        '<div class="cl-user-card">'
        f'<div class="cl-user-name">{escape(str(name))}</div>'
        f'<div class="cl-user-role">{escape(ROLE_LABELS.get(role, role.replace("_", " ").title()))}'
        ' · Sesión protegida</div></div>',
        unsafe_allow_html=True,
    )


def page_hero(eyebrow: str, title: str, description: str, *, chip: str = "COLORLINK") -> None:
    st.markdown(
        '<section class="cl-hero" aria-label="Encabezado de página">'
        f'<p class="cl-hero-kicker">{escape(eyebrow)}</p>'
        f'<h1 class="cl-hero-title">{escape(title)}</h1>'
        f'<p class="cl-hero-desc">{escape(description)}</p>'
        f'<span class="cl-hero-chip">{escape(chip)}</span>'
        '</section>',
        unsafe_allow_html=True,
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
    st.markdown('<div class="cl-metric-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)


def section_intro(eyebrow: str, title: str, description: str = "") -> None:
    st.markdown(
        f'<span class="cl-section-eyebrow">{escape(eyebrow)}</span>'
        f'<h2 class="cl-section-head">{escape(title)}</h2>'
        f'<p class="cl-section-text">{escape(description)}</p>',
        unsafe_allow_html=True,
    )



def premium_welcome() -> None:
    """Editorial left-hand login surface; purely presentational HTML."""
    st.html(
        '<section class="cl-auth-showcase" aria-label="Presentación COLORLINK">'
        '<div><p class="cl-auth-eyebrow">COLORLINK / WORKSPACE</p>'
        '<h1 class="cl-auth-headline">Cada proyecto.<br>'
        'Cada etapa.<br><em>Todo conectado.</em></h1>'
        '<p class="cl-auth-sub">Una experiencia integral para planificar, '
        'coordinar y dar seguimiento a tus proyectos, '
        'desde la primera solicitud hasta su cierre.</p>'
        '<div class="cl-auth-badges">'
        '<span>01 / Planifica</span><span>02 / Coordina</span>'
        '<span>03 / Supervisa</span></div></div>'
        '<p class="cl-auth-bottom">INTELIGENCIA · OPERACIONES · TRAZABILIDAD</p>'
        '</section>'
    )


def premium_login_heading() -> None:
    """Clear authentication hierarchy without touching Streamlit forms."""
    st.html(
        '<section aria-label="Acceder a COLORLINK">'
        '<p class="cl-auth-form-eyebrow">UN ESPACIO PARA TU TRABAJO</p>'
        '<h2 class="cl-auth-form-title">Tu espacio comienza aquí.</h2>'
        '<p class="cl-auth-form-sub">Inicia sesión o crea una cuenta '
        'para gestionar tus proyectos y avanzar con tu equipo.</p>'
        '</section>'
    )


def workspace_header(role: str, current: str) -> None:
    """Accessible, truthful location breadcrumb, never a duplicate navigation route."""
    from html import escape as safe
    friendly_role = ROLE_LABELS.get(role, str(role).replace("_", " ").title())
    st.html(
        '<nav class="cl-workspace-bar" aria-label="Ubicación actual">'
        '<div class="cl-crumb"><span>COLORLINK</span>'
        '<span class="cl-crumb-sep" aria-hidden="true">/</span>'
        '<span>' + safe(friendly_role) + '</span>'
        '<span class="cl-crumb-sep" aria-hidden="true">/</span>'
        '<strong aria-current="page">' + safe(str(current)) + '</strong></div>'
        '<span class="cl-workspace-status">Espacio de trabajo</span>'
        '</nav>'
    )
