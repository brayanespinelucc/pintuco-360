import os
from datetime import date, timedelta

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="COLORLINK | Pintuco 360", page_icon="🎨", layout="wide")
st.markdown(
    """<style>
      @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
      html,body,[data-testid="stApp"] {font-family:Montserrat,sans-serif;}
      [data-testid="stApp"] {background:#f7f9fd;}
      h1,h2,h3 {color:#0A1E8C;}
      div.stButton>button[kind="primary"],div.stFormSubmitButton>button[kind="primary"]{
      background:#FFDD00;color:#0A1E8C;border:0;font-weight:800;}
      .brand {background:#0A1E8C;color:white;border-radius:8px;padding:8px 14px;font-weight:800;}
    </style>""",
    unsafe_allow_html=True,
)


def call(method, path, *, json=None, files=None):
    token = st.session_state.get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = httpx.request(method, f"{API}/api/v1{path}", headers=headers,
                                 json=json, files=files, timeout=95)
    except httpx.RequestError:
        st.error("No hay conexión con el backend FastAPI.")
        return None
    if response.status_code == 401:
        st.session_state.pop("access_token", None)
        st.error("Tu sesión expiró. Ingresa nuevamente.")
        return None
    if response.is_error:
        try:
            detail = response.json().get("detail", "Error desconocido")
        except ValueError:
            detail = "El servidor devolvió una respuesta inválida."
        st.error(f"Error ({response.status_code}): {detail}")
        return None
    return response.json()


st.markdown('<span class="brand">COLORLINK · PINTUCO 360</span>', unsafe_allow_html=True)
st.caption("Plataforma académica · No es un portal oficial de Pintuco")

if not st.session_state.get("access_token"):
    st.title("Iniciar sesión")
    with st.form("login"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")
    if submitted:
        if not email.strip() or not password:
            st.warning("Completa el correo y la contraseña.")
        else:
            result = call("POST", "/auth/login", json={"email":email.strip(), "password": password})
            if result and result.get("access_token"):
                st.session_state["access_token"] = result["access_token"]
                st.rerun()
    st.stop()

profile = call("GET", "/auth/me")
if not profile:
    if st.button("Volver al inicio de sesión"):
        st.session_state.pop("access_token", None)
        st.rerun()
    st.stop()

with st.sidebar:
    st.header("COLORLINK")
    st.write(f"**Usuario:** {profile.get('full_name') or profile.get('email')}")
    st.write(f"**Rol:** {profile['role'].replace('_',' ').title()}")
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.pop("access_token", None)
        st.rerun()

st.title("Portal de gestión")
if profile["role"] != "cliente":
    st.info("Rol verificado correctamente. Su portal operativo se implementará en las siguientes etapas.")
    st.stop()

tab_dashboard, tab_cliente, tab_proyectos, tab_solicitudes, tab_ia, tab_tecnico, tab_inventario = st.tabs(
    ["Mi panel", "Mi empresa", "Proyectos", "Solicitudes y fotografías",
     "Análisis con Gemini", "Cálculo técnico", "Inventario / Disponibilidad"]
)

with tab_cliente:
    st.subheader("Registrar empresa")
    with st.form("crear_cliente"):
        nombre = st.text_input("Nombre de la empresa", max_chars=160)
        ciudad = st.text_input("Ciudad", max_chars=100)
        save_cliente = st.form_submit_button("Guardar empresa", type="primary")
    if save_cliente and nombre.strip() and ciudad.strip():
        if call("POST", "/capture/clientes", json={"nombre_empresa":nombre.strip(),"ciudad":ciudad.strip()}):
            st.success("Empresa registrada.")
            st.rerun()
    clientes = call("GET", "/capture/clientes") or []
    if clientes:
        st.dataframe(clientes, use_container_width=True, hide_index=True)
    else:
        st.info("Primero registra tu empresa para crear proyectos.")

with tab_proyectos:
    st.subheader("Mis proyectos")
    clientes = call("GET", "/capture/clientes") or []
    proyectos = call("GET", "/capture/proyectos") or []
    if clientes:
        by_name = {f"{c['nombre_empresa']} · {c['ciudad']}": c["id"] for c in clientes}
        with st.form("crear_proyecto"):
            empresa = st.selectbox("Empresa", list(by_name))
            nombre = st.text_input("Nombre del proyecto", max_chars=180)
            area = st.number_input("Área (m²)", min_value=0.01, value=85.0, step=1.0)
            superficie = st.text_input("Superficie", value="Concreto", max_chars=100)
            condicion = st.text_input("Condición", value="Humedad y fisuras", max_chars=300)
            ambiente = st.selectbox("Ambiente", ["exterior", "interior"])
            color = st.text_input("Color requerido", value="Gris", max_chars=100)
            fecha = st.date_input("Fecha requerida", value=date.today()+timedelta(days=20),
                                  min_value=date.today())
            save_project = st.form_submit_button("Crear proyecto", type="primary")
        if save_project:
            payload = {
                "cliente_id": by_name[empresa], "nombre_proyecto": nombre.strip(),
                "area_m2": f"{area:.2f}", "tipo_superficie": superficie.strip(),
                "condicion": condicion.strip(), "ambiente": ambiente,
                "color_requerido": color.strip(), "fecha_requerida": fecha.isoformat()
            }
            if call("POST", "/capture/proyectos", json=payload):
                st.success("Proyecto guardado.")
                st.rerun()
    else:
        st.info("Debes registrar una empresa antes de crear un proyecto.")
    if proyectos:
        st.dataframe(proyectos, use_container_width=True, hide_index=True)

with tab_solicitudes:
    st.subheader("Nueva solicitud")
    proyectos = call("GET", "/capture/proyectos") or []
    solicitudes = call("GET", "/capture/solicitudes") or []
    if proyectos:
        by_project = {f"{p['nombre_proyecto']} · {p['id'][:8]}":p["id"] for p in proyectos}
        with st.form("crear_solicitud"):
            seleccionado = st.selectbox("Proyecto", list(by_project))
            descripcion = st.text_area(
                "Descripción de la necesidad",
                placeholder="Describe la superficie, condiciones y trabajo requerido...",
                max_chars=4000,
            )
            save_request = st.form_submit_button("Radicar solicitud", type="primary")
        if save_request:
            if call("POST", "/capture/solicitudes",
                    json={"proyecto_id":by_project[seleccionado], "descripcion_libre":descripcion.strip()}):
                st.success("Solicitud radicada correctamente.")
                st.rerun()
    else:
        st.info("Primero debes crear un proyecto.")
    if solicitudes:
        st.subheader("Solicitudes registradas")
        st.dataframe(solicitudes, use_container_width=True, hide_index=True)
        by_request = {
            f"{s['id'][:8]} · {s['estado']} · {s['created_at'][:10]}": s["id"] for s in solicitudes
        }
        seleccionado = st.selectbox("Solicitud para adjuntar fotos", list(by_request))
        fotos = st.file_uploader("Fotografías JPG o PNG (máximo 5 MB cada una)",
                                 type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if st.button("Adjuntar fotografías", type="primary"):
            if not fotos:
                st.warning("Selecciona al menos una fotografía.")
            else:
                for foto in fotos:
                    if foto.size > 5 * 1024 * 1024:
                        st.error(f"{foto.name}: supera los 5 MB.")
                        continue
                    result = call("POST", f"/capture/solicitudes/{by_request[seleccionado]}/evidencias",
                                  files={"archivo": (foto.name, foto.getvalue(), foto.type)})
                    if result:
                        st.success(f"Fotografía almacenada: {foto.name}")
        evidencias = call("GET", f"/capture/solicitudes/{by_request[seleccionado]}/evidencias") or []
        if evidencias:
            st.dataframe(evidencias, use_container_width=True, hide_index=True)

with tab_dashboard:
    st.subheader("Resumen de mi actividad")
    clientes = call("GET", "/capture/clientes") or []
    proyectos = call("GET", "/capture/proyectos") or []
    solicitudes = call("GET", "/capture/solicitudes") or []
    c1, c2, c3 = st.columns(3)
    c1.metric("Empresas", len(clientes))
    c2.metric("Proyectos", len(proyectos))
    c3.metric("Solicitudes", len(solicitudes))
    st.info("RF-01 a RF-04 disponibles. Reservas y despacho aún están pendientes.")


with tab_ia:
    st.subheader("Clasificación inteligente de solicitudes — RF-02")
    st.info(
        "Gemini clasifica descripciones y fotografías; NO calcula cantidades, "
        "no aprueba soluciones técnicas ni modifica inventarios. "
        "Si hay humedad o fisuras, se requiere revisión humana."
    )
    solicitudes_ia = call("GET", "/capture/solicitudes") or []
    if not solicitudes_ia:
        st.warning("Primero debes registrar una solicitud.")
    else:
        opciones = {
            f"{s['id'][:8]} · {s['estado']} · {s['created_at'][:10]}": s["id"]
            for s in solicitudes_ia
        }
        seleccion_ia = st.selectbox("Selecciona una solicitud", list(opciones), key="ia_solicitud")
        solicitud_id = opciones[seleccion_ia]
        st.caption(
            "Los datos descriptivos y hasta 2 fotografías privadas de esta solicitud "
            "se enviarán al proveedor Google Gemini para su análisis."
        )
        consentimiento_ia = st.checkbox(
            "Autorizo el envío de la descripción y las fotografías de esta solicitud a Gemini.",
            key="consentimiento_gemini",
        )
        if st.button("Analizar con Gemini", type="primary", disabled=not consentimiento_ia):
            with st.spinner("Consultando Gemini y registrando el análisis..."):
                resultado_ia = call(
                    "POST", f"/ia/solicitudes/{solicitud_id}/analizar",
                    json={"autorizo_envio_a_gemini": consentimiento_ia},
                )
            if resultado_ia:
                st.success("Análisis estructurado guardado en Supabase.")
        historial_ia = call("GET", f"/ia/solicitudes/{solicitud_id}/analisis") or []
        if historial_ia:
            actual = historial_ia[0]
            st.write("**Última clasificación**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Modelo", actual["modelo"])
            c2.metric("Fotografías procesadas", actual["numero_imagenes"])
            c3.metric(
                "Revisión técnica",
                "Requerida" if actual["resultado"]["requiere_revision_humana"] else "No indicada",
            )
            st.json(actual["resultado"])
            st.caption(f"Registrado el {actual['created_at'][:19]} UTC. No equivale a diagnóstico técnico.")
        else:
            st.caption("Todavía no hay análisis para esta solicitud.")


with tab_tecnico:
    st.subheader("RF-03 · Cálculo técnico determinístico")
    st.caption(
        "El backend calcula los litros usando el área del proyecto y rendimientos "
        "del catálogo. La IA no realiza operaciones matemáticas."
    )
    technical_requests = call("GET", "/capture/solicitudes") or []
    technical_products = call("GET", "/tecnico/catalogo") or []
    if not technical_requests:
        st.info("Primero debes registrar una solicitud.")
    elif not technical_products:
        st.info("No hay productos técnicos activos en el catálogo.")
    else:
        requests_options = {
            f"{s['created_at'][:10]} · {s['id'][:8]}": s["id"]
            for s in technical_requests
        }
        selection = st.selectbox("Solicitud", list(requests_options), key="technical_request")
        request_id = requests_options[selection]
        catalog_options = {
            f"{p['nombre']} · {p['presentacion_litros']} litros": p["id"]
            for p in technical_products
        }
        label = st.selectbox("Producto y presentación", list(catalog_options), key="technical_product")
        product_id = catalog_options[label]
        product = next(p for p in technical_products if p["id"] == product_id)
        if product["es_demostrativo"]:
            st.warning(
                "Producto y rendimiento de PRUEBA, no oficiales de Pintuco. "
                "Estos valores no deben utilizarse para compras ni aplicaciones reales."
            )
        st.write(
            f"Rendimiento: **{product['rendimiento_m2_litro_mano']} m²/L por mano** · "
            f"Manos: **{product['manos_recomendadas']}** · "
            f"Desperdicio: **{product['desperdicio_pct']} %**"
        )
        if st.button("Calcular cantidades", type="primary"):
            result = call(
                "POST",
                f"/tecnico/solicitudes/{request_id}/calcular",
                json={"producto_id": product_id},
            )
            if result:
                st.success("Cálculo guardado en Supabase.")
                st.caption(result["advertencia"])
                if result["requiere_revision_humana"]:
                    st.warning("Requiere inspección técnica antes de aprobar una recomendación.")
                st.json(result)

        records = call("GET", f"/tecnico/solicitudes/{request_id}/calculos") or []
        if records:
            latest = records[0]
            st.subheader("Último cálculo registrado")
            a, b, c = st.columns(3)
            a.metric("Litros requeridos", f"{latest['litros_con_desperdicio']} L")
            b.metric("Envases", str(latest["envases"]))
            c.metric("Litros comerciales", f"{latest['litros_comerciales']} L")
            st.caption(
                "Fórmula: (área × manos / rendimiento por mano) × "
                "(1 + desperdicio / 100). Redondeo de envases por exceso."
            )
            if latest["requiere_revision_humana"]:
                st.warning("Revisión humana: " + "; ".join(latest["motivos_revision"]))
            if latest["es_demostrativo"]:
                st.warning("Resultado académico con datos ficticios, NO de producto comercial.")
            with st.expander("Historial de cálculos"):
                st.dataframe(records, use_container_width=True, hide_index=True)
