import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Pintuco 360 | Plataforma académica",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"], [data-testid="stApp"] { font-family: 'Montserrat', sans-serif; }
      [data-testid="stApp"] { background: #f7f9fd; }
      h1, h2, h3 { color: #0A1E8C; letter-spacing: -0.02em; }
      div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
        background: #FFDD00; color: #0A1E8C; border: none; font-weight: 800;
      }
      div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {
        background: #f5d200; color: #0A1E8C; border: none;
      }
      .brand-label { display:inline-block; background:#0A1E8C; color:white; padding:7px 12px;
        border-radius:8px; font-weight:800; letter-spacing:0.04em; }
      .subtle { color:#5d6881; font-size:0.9rem; }
      .notice { padding:15px; background:#fffbe2; border-left:4px solid #FFDD00;
        border-radius:8px; color:#3b4360; }
    </style>
    """,
    unsafe_allow_html=True,
)


def request_api(method: str, path: str, token: str | None = None, **kwargs) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.request(method, f"{API_BASE_URL}/api/v1{path}", headers=headers, timeout=15.0, **kwargs)


st.markdown('<span class="brand-label">PINTUCO 360</span>', unsafe_allow_html=True)
st.title("Portal de gestión")
st.caption("Proyecto académico · No es un portal oficial de Pintuco")

token = st.session_state.get("access_token")
if token:
    try:
        response = request_api("GET", "/auth/me", token=token)
        if response.status_code == 401:
            st.session_state.pop("access_token", None)
            st.warning("Tu sesión expiró. Ingresa nuevamente.")
            st.rerun()
        response.raise_for_status()
        profile = response.json()
    except httpx.HTTPError:
        st.error("No fue posible verificar tu sesión con el servidor.")
    else:
        st.success("Sesión verificada con Supabase Auth")
        st.subheader(f"Bienvenido, {profile.get('full_name') or profile.get('email') or 'usuario'}")
        st.write(f"**Rol asignado:** {profile['role'].replace('_', ' ').title()}")
        st.info("La autenticación es la primera funcionalidad real implementada. Los módulos operativos se agregarán en fases posteriores.")
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.pop("access_token", None)
        st.rerun()
else:
    st.markdown('<p class="subtle">Accede con la cuenta creada en Supabase Auth.</p>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)
    if submitted:
        if not email.strip() or not password:
            st.warning("Completa el correo y la contraseña.")
        else:
            try:
                response = request_api("POST", "/auth/login", json={"email": email.strip(), "password": password})
                if response.is_error:
                    try:
                        message = response.json().get("detail", "No fue posible iniciar sesión.")
                    except ValueError:
                        message = "No fue posible iniciar sesión."
                    st.error(message)
                else:
                    st.session_state["access_token"] = response.json()["access_token"]
                    st.rerun()
            except httpx.HTTPError:
                st.error("No hay conexión con el backend. Verifica que FastAPI esté en ejecución.")

st.divider()
st.markdown(
    '<div class="notice"><b>Estado actual:</b> base del portal y API. '
    'Los 15 procesos del reto transversal están documentados, pero aún no están implementados.</div>',
    unsafe_allow_html=True,
)
