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
