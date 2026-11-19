import os
from datetime import date, timedelta

import httpx
import streamlit as st
from dotenv import load_dotenv
from design import (
    PAGES, ROLE_PAGES, ROLE_LABELS,
    apply_design_system, brand, user_identity, page_hero,
    metric_cards, section_intro, navigation_group, workspace_breadcrumb,
    auth_showcase, auth_form_heading, auth_security_note, module_flag,
)
from process_ui import (
    render_request_panel, render_stage_explorer,
    render_state_distribution, render_stepper, render_field_progress,
    render_event_timeline, request_state,
)

load_dotenv()
API = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(
    page_title="COLORLINK · Espacio de trabajo",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Apariencia local de esta sesión. No se persiste ni modifica dato de negocio.
apply_design_system(bool(st.session_state.get("cl_dark", False)))


def call(method, path, *, json=None, files=None, data=None):
    token = st.session_state.get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = httpx.request(method, f"{API}/api/v1{path}", headers=headers,
                                 json=json, files=files, data=data, timeout=95)
    except httpx.RequestError:
        st.error("No hay conexión con el backend FastAPI.")
        return None
    if response.status_code == 401:
        if path == "/auth/login":
            st.error("No fue posible iniciar sesión. Revisa el correo y la contraseña.")
        else:
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


def foto_campo(path):
    token = st.session_state.get("access_token")
    if not token:
        return None
    try:
        res = httpx.get(
            f"{API}/api/v1{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=40,
        )
    except httpx.RequestError:
        st.error("No se pudo conectar para leer la fotografía.")
        return None
    if res.status_code != 200:
        st.error(f"No se pudo abrir la fotografía ({res.status_code}).")
        return None
    if res.headers.get("content-type", "").split(";")[0] not in ("image/png", "image/jpeg"):
        st.error("El servidor devolvió un formato de fotografía inválido.")
        return None
    return res.content


def mostrar_bitacora_campo(app):
    if not app.get("bitacora"):
        st.caption("Todavía no hay actividades registradas.")
        return
    for entrada in app["bitacora"]:
        with st.expander(
            f"{entrada['created_at'][:19]} · {entrada['tipo']} · "
            f"{entrada['avance_pct']}%",
            expanded=False,
        ):
            st.write(entrada["observaciones"])
            if entrada.get("foto_path"):
                if st.button(
                    "Ver fotografía privada",
                    key=f"rf07_foto_{entrada['id']}",
                ):
                    contenido = foto_campo(
                        f"/campo/aplicaciones/{app['id']}/evidencias/"
                        f"{entrada['id']}/imagen"
                    )
                    if contenido:
                        st.image(contenido, caption="Evidencia fotográfica de campo")


if not st.session_state.get("access_token"):
    showcase, login_center = st.columns(
        [1.1, 0.9], gap="large", vertical_alignment="center"
    )
    with showcase:
        auth_showcase()
    with login_center:
        auth_form_heading()
        entry, sign_up = st.tabs(["Iniciar sesión", "Crear cuenta"])
        with entry:
            st.caption("Ingresa con tu cuenta autorizada para continuar.")
            with st.form("login"):
                email = st.text_input("Correo electrónico")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button(
                    "Ingresar a mi espacio", type="primary", use_container_width=True
                )
            if submitted:
                print("COLORLINK_UI_LOGIN_SUBMIT: formulario enviado", flush=True)
                if not email.strip() or not password:
                    st.warning("Completa el correo y la contraseña.")
                else:
                    with st.spinner("Validando acceso..."):
                        result = call(
                            "POST", "/auth/login",
                            json={"email": email.strip(), "password": password},
                        )
                    if result and result.get("access_token"):
                        st.session_state["access_token"] = result["access_token"]
                        st.rerun()
                    elif result is None:
                        st.caption(
                            "Si el problema continúa, comunícalo al administrador de COLORLINK."
                        )
        with sign_up:
            st.caption("Crea una cuenta con tu propio correo electrónico.")
            with st.form("register"):
                full_name = st.text_input("Nombre completo", key="register_name")
                register_email = st.text_input(
                    "Correo para registro", key="register_email"
                )
                register_password = st.text_input(
                    "Crear contraseña (mínimo 8 caracteres)",
                    type="password", key="register_password"
                )
                confirm_password = st.text_input(
                    "Confirmar contraseña", type="password",
                    key="register_confirm_password"
                )
                accept_signup = st.checkbox(
                    "Confirmo que utilizaré mi propia cuenta para acceder."
                )
                create_account = st.form_submit_button(
                    "Crear mi cuenta", type="primary", use_container_width=True
                )
            if create_account:
                if len(full_name.strip()) < 2 or len(register_email.strip()) < 5:
                    st.warning("Completa tu nombre y un correo electrónico válido.")
                elif len(register_password) < 8:
                    st.warning("La contraseña debe tener al menos 8 caracteres.")
                elif register_password != confirm_password:
                    st.warning("Las contraseñas no coinciden.")
                elif not accept_signup:
                    st.warning("Confirma que deseas crear tu cuenta.")
                else:
                    with st.spinner("Registrando cuenta..."):
                        result = call(
                            "POST", "/auth/register",
                            json={
                                "full_name": full_name.strip(),
                                "email": register_email.strip().lower(),
                                "password": register_password,
                            }
                        )
                    if result:
                        st.success(result["message"])
                        st.info(
                            "Ingresa en la pestaña Iniciar sesión después "
                            "de confirmar el correo si se te solicita."
                        )
            st.caption(
                "Las nuevas cuentas comienzan como Cliente. "
                "El acceso al selector de roles requiere autorización del administrador."
            )
        auth_security_note()
    st.stop()

profile = call("GET", "/auth/me")
if not profile:
    if st.button("Volver al inicio de sesión"):
        st.session_state.pop("access_token", None)
        st.rerun()
    st.stop()

with st.sidebar:
    brand()
    user_identity(
        profile.get("full_name") or profile.get("email") or "Cuenta COLORLINK",
        profile["role"],
    )
    if profile["role"] == "cliente":
        # Navigation is a grouped command menu; st.session_state remains the
        # sole source for client_page so existing quick links still work.
        allowed_client_pages = {page[0] for page in PAGES}
        if st.session_state.get("cl_page") not in allowed_client_pages:
            st.session_state["cl_page"] = "Mi panel"
        client_page = st.session_state["cl_page"]
        menu_groups = (
            ("GENERAL", ("Mi panel", "Mi empresa", "Proyectos")),
            ("SOLICITUDES", ("Solicitudes", "Análisis con Gemini", "Cálculo técnico", "Inventario")),
            ("SEGUIMIENTO", (
                "Revisión técnica", "Seguimiento logístico",
                "Aplicación en campo", "Control de calidad",
            )),
        )
        for label, pages in menu_groups:
            navigation_group(label)
            for page in pages:
                st.button(
                    page,
                    key=f"cl_nav_{next(i for i,p in enumerate(PAGES) if p[0] == page)}",
                    type="primary" if client_page == page else "secondary",
                    use_container_width=True,
                    on_click=lambda chosen=page: st.session_state.update(
                        {"cl_page": chosen}
                    ),
                )
    elif profile["role"] == "logistica":
        logistic_pages = ("Reservas", "Órdenes y despachos", "Aplicadores y campo")
        if st.session_state.get("cl_logistics_page") not in logistic_pages:
            st.session_state["cl_logistics_page"] = logistic_pages[0]
        logistics_page = st.session_state["cl_logistics_page"]
        navigation_group("CENTRO DE OPERACIONES")
        for i, page in enumerate(logistic_pages):
            st.button(
                page, key=f"cl_log_nav_{i}",
                type="primary" if logistics_page == page else "secondary",
                use_container_width=True,
                on_click=lambda chosen=page: st.session_state.update(
                    {"cl_logistics_page": chosen}
                ),
            )
    elif profile["role"] == "calidad":
        quality_pages = ("Inspecciones pendientes", "Historial de dictámenes")
        if st.session_state.get("cl_quality_page") not in quality_pages:
            st.session_state["cl_quality_page"] = quality_pages[0]
        quality_page = st.session_state["cl_quality_page"]
        navigation_group("CENTRO DE INSPECCIONES")
        for i, page in enumerate(quality_pages):
            st.button(
                page, key=f"cl_quality_nav_{i}",
                type="primary" if quality_page == page else "secondary",
                use_container_width=True,
                on_click=lambda chosen=page: st.session_state.update(
                    {"cl_quality_page": chosen}
                ),
            )
    else:
        navigation_group("TU ESPACIO")
        st.caption("Las herramientas de esta cuenta se muestran en la vista principal.")
    if profile.get("can_switch_roles"):
        st.divider()
        st.markdown(
            '<p class="cl-nav-label">Modo evaluador</p>',
            unsafe_allow_html=True,
        )
        evaluator_roles = [
            "cliente", "especialista_tecnico", "logistica", "aplicador", "calidad",
        ]
        selected_role = st.selectbox(
            "Probar funcionalidades como",
            evaluator_roles,
            index=evaluator_roles.index(profile["role"])
                  if profile["role"] in evaluator_roles else 0,
            format_func=lambda role: ROLE_LABELS.get(role, role),
            key="cl_evaluator_role",
        )
        if selected_role != profile["role"]:
            if st.button(
                "Cambiar al rol seleccionado", key="cl_evaluator_switch",
                type="primary", use_container_width=True
            ):
                result = call(
                    "POST", "/auth/evaluator/role",
                    json={"role": selected_role},
                )
                if result and result.get("role") == selected_role:
                    for key in (
                        "cl_page", "cl_logistics_page", "cl_quality_page",
                        "cl_evaluator_role",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()
        st.caption("Solo para cuentas autorizadas. Los cambios quedan registrados.")
    st.divider()
    st.toggle("Modo oscuro", key="cl_dark", help="Preferencia visual de esta sesión.")
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.pop("access_token", None)
        st.session_state.pop("cl_page", None)
        st.rerun()
    st.caption("COLORLINK · Gestión integral de proyectos")

workspace_page = (
    client_page if profile["role"] == "cliente" else
    logistics_page if profile["role"] == "logistica" else
    quality_page if profile["role"] == "calidad" else
    ROLE_PAGES.get(profile["role"], ("", "Espacio de trabajo", ""))[1]
)
workspace_breadcrumb(
    ROLE_LABELS.get(profile["role"], "COLORLINK"), workspace_page
)

if profile["role"] == "cliente":
    page_meta = next(p for p in PAGES if p[0] == client_page)
    page_hero(page_meta[1], page_meta[2], page_meta[3], chip="ESPACIO CLIENTE")
elif profile["role"] == "logistica":
    descriptions = {
        "Reservas": "Consulta solicitudes aprobadas y gestiona la reserva de materiales.",
        "Órdenes y despachos": "Gestiona la preparación, el despacho y la trazabilidad de cada orden.",
        "Aplicadores y campo": "Asigna aplicadores y da seguimiento a sus trabajos de campo.",
    }
    page_hero(
        "CENTRO DE OPERACIONES", logistics_page, descriptions[logistics_page],
        chip="LOGÍSTICA",
    )
elif profile["role"] == "calidad":
    page_hero(
        "CENTRO DE INSPECCIONES", quality_page,
        "Consulta expedientes, evidencias y decisiones humanas auditables.",
        chip="CONTROL DE CALIDAD",
    )
else:
    section, title, description = ROLE_PAGES.get(
        profile["role"],
        ("Plataforma", "Espacio de trabajo", "Herramientas disponibles para tu cuenta."),
    )
    page_hero(section, title, description, chip=ROLE_LABELS.get(profile["role"], "COLORLINK"))
if profile["role"] == "logistica":
    st.subheader("Gestión logística")
    st.caption("Gestiona reservas, órdenes y trazabilidad de materiales.")
    if st.session_state.pop("rf06_exito", False):
        st.success("Operación registrada en Supabase y sujeta a auditoría.")
    st.caption(
        "Se puede reservar solo una solicitud aprobada. "
        "La secuencia es RESERVAR → PREPARAR → DESPACHAR. "
        "Una reserva puede cancelarse antes de despachar."
    )
    if logistics_page == "Reservas":
        pendientes_logistica = call("GET", "/logistica/bandeja") or []
        st.metric("Pendientes de reserva", len(pendientes_logistica))
        st.subheader("Solicitudes aprobadas por reservar")
        if pendientes_logistica:
            st.dataframe(pendientes_logistica, use_container_width=True, hide_index=True)
            opciones_pendientes = {
                f"{p['nombre_empresa']} · {p['nombre_proyecto']} · "
                f"{p['envases_requeridos']} envases": p["solicitud_id"]
                for p in pendientes_logistica
            }
            seleccion_pendiente = st.selectbox(
                "Solicitud aprobada", list(opciones_pendientes), key="rf06_solicitud"
            )
            solicitud_logistica_id = opciones_pendientes[seleccion_pendiente]
            actual_pendiente = next(
                p for p in pendientes_logistica
                if p["solicitud_id"] == solicitud_logistica_id
            )
            st.write(
                f"**Envases requeridos:** {actual_pendiente['envases_requeridos']} · "
                f"**Disponibles ahora:** {actual_pendiente['disponibles_ahora']}"
            )
            render_stepper(actual_pendiente.get("estado", "aprobada"), compact=True)
            if actual_pendiente["disponibles_ahora"] < actual_pendiente["envases_requeridos"]:
                st.warning("No alcanza el stock actual. No se permitirá una reserva parcial.")
            with st.form("rf06_reservar"):
                observacion_reserva = st.text_area(
                    "Observación de reserva",
                    value="Reserva de materiales para la solicitud aprobada.",
                    max_chars=1000, height=100,
                )
                enviar_reserva = st.form_submit_button(
                    "Reservar envases", type="primary"
                )
            if enviar_reserva:
                result = call(
                    "POST", f"/logistica/solicitudes/{solicitud_logistica_id}/reservar",
                    json={"observaciones": observacion_reserva.strip()},
                )
                if result:
                    st.session_state["rf06_exito"] = True
                    st.rerun()
        else:
            st.info("No hay solicitudes aprobadas pendientes de reserva.")
    elif logistics_page == "Órdenes y despachos":
        st.subheader("Órdenes logísticas y trazabilidad")
        ordenes_activas = call("GET", "/logistica/ordenes") or []
        estado_ordenes = {
            key: sum(o.get("estado") == key for o in ordenes_activas)
            for key in ("reservada", "preparada", "despachada")
        }
        m1, m2, m3 = st.columns(3)
        m1.metric("Reservadas", estado_ordenes["reservada"])
        m2.metric("Preparadas", estado_ordenes["preparada"])
        m3.metric("Despachadas", estado_ordenes["despachada"])
        if ordenes_activas:
            etiquetas_ordenes = {
                f"{o['nombre_empresa']} · {o['id'][:8]} · {o['estado']}": o["id"]
                for o in ordenes_activas
            }
            nombre_orden = st.selectbox(
                "Seleccionar orden", list(etiquetas_ordenes), key="rf06_orden"
            )
            orden_id = etiquetas_ordenes[nombre_orden]
            orden = next(o for o in ordenes_activas if o["id"] == orden_id)
            st.write(
                f"**Estado:** {orden['estado']} · "
                f"**Envases:** {orden['envases_requeridos']} · "
                f"**Solicitud:** {orden['estado_solicitud']}"
            )
            render_stepper(orden["estado_solicitud"], compact=True)
            if orden.get("referencia_despacho"):
                st.write("**Referencia de despacho:**", orden["referencia_despacho"])
            if orden.get("lotes"):
                st.write("**Lotes asociados**")
                st.dataframe(orden["lotes"], use_container_width=True, hide_index=True)
            if orden.get("eventos"):
                st.write("**Historial de operaciones**")
                render_event_timeline(orden["eventos"])
                with st.expander("Ver todos los datos del historial"):
                    st.dataframe(orden["eventos"], use_container_width=True, hide_index=True)

            acciones_posibles = {
                "reservada": {"Preparar envases": "preparar", "Cancelar reserva": "cancelar"},
                "preparada": {"Confirmar despacho": "despachar", "Cancelar reserva": "cancelar"},
            }.get(orden["estado"], {})
            if acciones_posibles:
                nombre_accion = st.selectbox(
                    "Siguiente operación", list(acciones_posibles), key="rf06_accion"
                )
                accion_logistica = acciones_posibles[nombre_accion]
                with st.form("rf06_operacion"):
                    observacion_accion = st.text_area(
                        "Observaciones de la operación",
                        value="Se registra la operación logística con trazabilidad de la orden.",
                        max_chars=1000, height=100,
                    )
                    ejecutar_accion = st.form_submit_button(
                        "Registrar operación", type="primary"
                    )
                if ejecutar_accion:
                    resultado = call(
                        "POST", f"/logistica/ordenes/{orden_id}/accion",
                        json={
                            "accion": accion_logistica,
                            "observaciones": observacion_accion.strip(),
                        },
                    )
                    if resultado:
                        st.session_state["rf06_exito"] = True
                        st.rerun()
            elif orden["estado"] == "despachada":
                st.success("Despacho registrado. La solicitud continúa a ejecución en campo.")
            else:
                st.info("La reserva fue cancelada; se puede crear otra si la solicitud está aprobada.")
        else:
            st.info("Todavía no hay órdenes de logística registradas.")
    else:
        st.subheader("Asignación de trabajos de campo")
        st.caption(
            "Asigna las solicitudes con despacho confirmado a una cuenta aplicador. "
            "Selecciona el aplicador responsable para continuar con el seguimiento."
        )
        elegibles_campo = call("GET", "/campo/elegibles") or []
        usuarios_aplicadores = call("GET", "/campo/aplicadores") or []
        st.metric("Solicitudes listas para asignar", len(elegibles_campo))
        if not usuarios_aplicadores:
            st.info("Crea una cuenta con rol aplicador para habilitar las asignaciones.")
        if elegibles_campo and usuarios_aplicadores:
            st.dataframe(elegibles_campo, use_container_width=True, hide_index=True)
            opciones_trabajo = {
                f"{c['nombre_empresa']} · {c['nombre_proyecto']} · {c['solicitud_id'][:8]}":
                    c["solicitud_id"]
                for c in elegibles_campo
            }
            opciones_aplicador = {
                f"{a['nombre']} · {a['id'][:8]}": a["id"]
                for a in usuarios_aplicadores
            }
            with st.form("rf07_asignar"):
                caso_asignar_label = st.selectbox(
                    "Solicitud despachada", list(opciones_trabajo), key="rf07_solicitud_asignar"
                )
                usuario_aplicar_label = st.selectbox(
                    "Aplicador responsable", list(opciones_aplicador)
                )
                nota_asignacion = st.text_area(
                    "Observaciones de la asignación",
                    value="Asignación del responsable para el seguimiento de la aplicación en campo.",
                    max_chars=1500, height=95,
                )
                enviar_asignacion = st.form_submit_button(
                    "Asignar al aplicador", type="primary"
                )
            if enviar_asignacion:
                asignado = call(
                    "POST",
                    f"/campo/solicitudes/{opciones_trabajo[caso_asignar_label]}/asignar",
                    json={
                        "aplicador_id": opciones_aplicador[usuario_aplicar_label],
                        "observaciones": nota_asignacion.strip(),
                    },
                )
                if asignado:
                    st.session_state["rf07_asignacion_exitosa"] = True
                    st.rerun()
        elif not elegibles_campo:
            st.info("No hay nuevas solicitudes despachadas pendientes de asignación.")
        if st.session_state.pop("rf07_asignacion_exitosa", False):
            st.success("Aplicador asignado y evento registrado en Supabase.")
        trabajos_campo_logistica = call("GET", "/campo/aplicaciones") or []
        if trabajos_campo_logistica:
            st.write("**Seguimiento de los aplicadores**")
            for trabajo in trabajos_campo_logistica:
                with st.expander(
                    f"{trabajo['nombre_proyecto']} · {trabajo['aplicador']} · "
                    f"{trabajo['estado']} · {trabajo['avance_pct']}%",
                    expanded=False,
                ):
                    render_field_progress(trabajo["avance_pct"])
                    mostrar_bitacora_campo(trabajo)
    st.stop()

if profile["role"] == "calidad":
    st.subheader("Inspecciones y control de calidad")
    if st.session_state.pop("rf08_dictamen_exitoso", False):
        st.success("Dictamen humano de calidad registrado con trazabilidad.")
    expedientes_calidad = call("GET", "/calidad/expedientes") or []
    st.metric("Expedientes en seguimiento", len(expedientes_calidad))
    if quality_page == "Inspecciones pendientes":
        bandeja_calidad = call("GET", "/calidad/bandeja") or []
        st.metric("Inspecciones pendientes", len(bandeja_calidad))
        st.subheader("Bandeja pendiente de inspección")
        if not bandeja_calidad:
            st.info("No hay aplicaciones pendientes de evaluación.")
        else:
            st.dataframe(bandeja_calidad, hide_index=True, use_container_width=True)
            opciones_calidad = {
                f"{r['nombre_empresa']} · {r['nombre_proyecto']} · "
                f"{r['aplicacion_id'][:8]}": r["aplicacion_id"]
                for r in bandeja_calidad
            }
            nombre_caso = st.selectbox(
                "Aplicación para inspeccionar", list(opciones_calidad),
                key="rf08_inspeccion_caso"
            )
            aplicacion_calidad_id = opciones_calidad[nombre_caso]
            expediente = next(
                (e for e in expedientes_calidad
                 if e["aplicacion_id"] == aplicacion_calidad_id),
                None,
            )
            if expediente:
                st.write(
                    f"**Empresa:** {expediente['nombre_empresa']} · "
                    f"**Proyecto:** {expediente['nombre_proyecto']}"
                )
                st.write(
                    f"**Aplicador:** {expediente['aplicador']} · "
                    f"**Avance:** {expediente['avance_pct']} %"
                )
                st.write(
                    f"**Superficie:** {expediente['tipo_superficie']} · "
                    f"**Ambiente:** {expediente['ambiente']}"
                )
                st.write("**Condición reportada:**", expediente["condicion"])
                st.write("**Referencia de despacho:**", expediente["referencia_despacho"])
                st.subheader("Evidencias, incidencias y actividades")
                st.caption(
                    "Revisa las actividades y abre las fotografías privadas antes "
                    "de registrar el checklist."
                )
                mostrar_bitacora_campo({
                    "id": expediente["aplicacion_id"],
                    "bitacora": expediente["bitacora"],
                })
                if expediente.get("inspecciones"):
                    st.write("**Dictámenes anteriores (inmutables)**")
                    render_event_timeline(
                        expediente["inspecciones"], event_key="decision",
                    )
                    st.dataframe(
                        expediente["inspecciones"], hide_index=True,
                        use_container_width=True,
                    )
                st.divider()
                st.subheader("Lista de verificación y dictamen")
                st.caption(
                    "Marca únicamente los criterios verificados en el expediente. "
                    "Una aprobación requiere cinco criterios cumplidos y evidencia."
                )
                with st.form("rf08_dictamen"):
                    superficie_ok = st.checkbox(
                        "La preparación de superficie es satisfactoria",
                        value=False,
                    )
                    cobertura_ok = st.checkbox(
                        "La cobertura es adecuada", value=False
                    )
                    acabado_ok = st.checkbox(
                        "El acabado es uniforme", value=False
                    )
                    evidencias_ok = st.checkbox(
                        "Se revisaron las evidencias fotográficas", value=False
                    )
                    incidencias_ok = st.checkbox(
                        "Las incidencias están gestionadas", value=False
                    )
                    decision_calidad_label = st.selectbox(
                        "Decisión del inspector",
                        [
                            "Solicitar correcciones",
                            "Aprobar calidad",
                            "Rechazar inspección",
                        ],
                    )
                    observacion_calidad = st.text_area(
                        "Justificación detallada del dictamen",
                        max_chars=2000, height=150,
                        placeholder="Describe hallazgos, criterios revisados y decisión...",
                    )
                    confirmo_evaluacion = st.checkbox(
                        "Confirmo que este dictamen corresponde al expediente revisado "
                        "y que mi evaluación corresponde a los criterios registrados."
                    )
                    enviar_dictamen = st.form_submit_button(
                        "Registrar dictamen humano", type="primary"
                    )
                if enviar_dictamen:
                    decision_calidad = {
                        "Solicitar correcciones": "solicitar_correccion",
                        "Aprobar calidad": "aprobar",
                        "Rechazar inspección": "rechazar",
                    }[decision_calidad_label]
                    criterios_enviados = {
                        "superficie_preparada": superficie_ok,
                        "cobertura_adecuada": cobertura_ok,
                        "acabado_uniforme": acabado_ok,
                        "evidencias_verificadas": evidencias_ok,
                        "incidencias_gestionadas": incidencias_ok,
                    }
                    if not confirmo_evaluacion:
                        st.warning("Confirma que revisaste el expediente.")
                    elif len(observacion_calidad.strip()) < 15:
                        st.warning("Justifica el dictamen en al menos 15 caracteres.")
                    elif decision_calidad == "aprobar" and not all(criterios_enviados.values()):
                        st.warning("La aprobación requiere todos los criterios cumplidos.")
                    elif decision_calidad != "aprobar" and all(criterios_enviados.values()):
                        st.warning("Señala al menos un criterio incumplido.")
                    else:
                        resultado = call(
                            "POST",
                            f"/calidad/aplicaciones/{aplicacion_calidad_id}/resolver",
                            json={
                                "decision": decision_calidad,
                                "criterios": criterios_enviados,
                                "observaciones": observacion_calidad.strip(),
                            },
                        )
                        if resultado:
                            st.session_state["rf08_dictamen_exitoso"] = True
                            st.rerun()
    else:
        st.subheader("Histórico de expedientes de calidad")
        if expedientes_calidad:
            for e in expedientes_calidad:
                with st.expander(
                    f"{e['nombre_proyecto']} · {e['estado_solicitud']} · "
                    f"{len(e.get('inspecciones') or [])} inspecciones",
                    expanded=False,
                ):
                    st.write("**Estado de aplicación:**", e["estado_aplicacion"])
                    st.write("**Avance original:**", f"{e['avance_pct']} %")
                    if e.get("inspecciones"):
                        render_event_timeline(e["inspecciones"], event_key="decision")
                        st.dataframe(
                            e["inspecciones"], hide_index=True, use_container_width=True
                        )
                    else:
                        st.caption("Sin decisiones de calidad registradas.")
        else:
            st.info("Aún no hay expedientes en control de calidad.")
    st.stop()

if profile["role"] == "aplicador":
    st.subheader("Ejecución y seguimiento en campo")
    if st.session_state.pop("rf07_evento_exitoso", False):
        st.success("Actividad registrada en Supabase.")
    trabajos = call("GET", "/campo/aplicaciones") or []
    st.metric("Trabajos asignados", len(trabajos))
    if not trabajos:
        st.info("Todavía no tienes trabajos asignados por logística.")
    else:
        opciones_trabajos = {
            f"{t['nombre_proyecto']} · {t['estado']} · {t['id'][:8]}": t["id"]
            for t in trabajos
        }
        trabajo_label = st.selectbox(
            "Trabajo asignado", list(opciones_trabajos), key="rf07_trabajo_aplicador"
        )
        trabajo_id = opciones_trabajos[trabajo_label]
        trabajo = next(t for t in trabajos if t["id"] == trabajo_id)
        st.write(
            f"**Empresa:** {trabajo['nombre_empresa']} · "
            f"**Proyecto:** {trabajo['nombre_proyecto']}"
        )
        st.write("**Estado:**", trabajo["estado"])
        st.write("**Referencia de despacho:**", trabajo["referencia_despacho"])
        render_field_progress(trabajo["avance_pct"])
        if trabajo["estado"] == "asignada":
            st.subheader("Iniciar actividad")
            with st.form("rf07_inicio"):
                nota_inicio = st.text_area(
                    "Observaciones de inicio",
                    value="Inicio de actividades; revisión visual de la superficie y materiales.",
                    max_chars=1500, height=100,
                )
                iniciar = st.form_submit_button("Registrar inicio", type="primary")
            if iniciar:
                result = call(
                    "POST", f"/campo/aplicaciones/{trabajo_id}/eventos",
                    json={
                        "tipo": "inicio", "avance_pct": None,
                        "observaciones": nota_inicio.strip(),
                    },
                )
                if result:
                    st.session_state["rf07_evento_exitoso"] = True
                    st.rerun()
        elif trabajo["estado"] == "en_ejecucion":
            st.subheader("Registrar actividad de campo")
            acciones = {"Registrar avance": "avance", "Reportar incidencia": "incidencia"}
            if trabajo["avance_pct"] > 0:
                acciones["Finalizar y enviar a calidad"] = "finalizacion"
            if trabajo["avance_pct"] >= 99:
                acciones.pop("Registrar avance", None)
            accion_label = st.selectbox("Actividad", list(acciones), key="rf07_tipo_evento")
            tipo_accion = acciones[accion_label]
            with st.form("rf07_actividad"):
                progreso_nuevo = None
                if tipo_accion == "avance":
                    progreso_nuevo = st.number_input(
                        "Porcentaje de avance acumulado",
                        min_value=trabajo["avance_pct"] + 1,
                        max_value=99,
                        value=min(99, max(trabajo["avance_pct"] + 10, 1)),
                        step=1,
                    )
                nota_actividad = st.text_area(
                    "Descripción y observaciones",
                    placeholder="Describe el trabajo realizado, incidencias o comprobaciones...",
                    max_chars=1500, height=140,
                )
                registrar_actividad = st.form_submit_button(
                    "Guardar actividad", type="primary"
                )
            if registrar_actividad:
                respuesta = call(
                    "POST", f"/campo/aplicaciones/{trabajo_id}/eventos",
                    json={
                        "tipo": tipo_accion, "avance_pct": progreso_nuevo,
                        "observaciones": nota_actividad.strip(),
                    },
                )
                if respuesta:
                    st.session_state["rf07_evento_exitoso"] = True
                    st.rerun()

            st.divider()
            st.subheader("Añadir fotografía de campo (opcional)")
            with st.form("rf07_evidencia"):
                foto = st.file_uploader(
                    "Fotografía JPG o PNG (máx. 5 MB)",
                    type=["jpg", "jpeg", "png"], key="rf07_foto_subir"
                )
                nota_foto = st.text_area(
                    "Descripción de la evidencia",
                    max_chars=1500, height=100,
                )
                guardar_foto = st.form_submit_button("Guardar fotografía")
            if guardar_foto:
                if foto is None:
                    st.warning("Selecciona primero una fotografía.")
                elif len(nota_foto.strip()) < 10:
                    st.warning("Describe la fotografía en al menos 10 caracteres.")
                else:
                    guardada = call(
                        "POST", f"/campo/aplicaciones/{trabajo_id}/evidencias",
                        files={"archivo": (
                            foto.name, foto.getvalue(), foto.type or "image/jpeg"
                        )},
                        data={"observaciones": nota_foto.strip()},
                    )
                    if guardada:
                        st.session_state["rf07_evento_exitoso"] = True
                        st.rerun()
        elif trabajo["estado"] == "en_correccion":
            st.warning(
                "Calidad solicitó correcciones. El 100 % corresponde al trabajo "
                "original, NO a su aprobación técnica. Documenta la subsanación "
                "antes de devolver el expediente a inspección."
            )
            docs_calidad = call("GET", "/calidad/expedientes") or []
            expediente_app = next(
                (e for e in docs_calidad if e["aplicacion_id"] == trabajo_id), None
            )
            if expediente_app and expediente_app.get("inspecciones"):
                ultima = expediente_app["inspecciones"][-1]
                st.write("**Última observación del inspector:**", ultima["observaciones"])
                st.write("**Lista de verificación anterior:**")
                st.json(ultima["criterios"])
            st.subheader("Adjuntar una foto de corrección (opcional)")
            with st.form("rf08_foto_correccion"):
                foto_correccion = st.file_uploader(
                    "Fotografía de subsanación JPG o PNG (máx. 5 MB)",
                    type=["jpg", "jpeg", "png"], key="rf08_foto_subsanacion"
                )
                nota_foto_correccion = st.text_area(
                    "Explicación de la fotografía", max_chars=1500, height=100
                )
                subir_correccion = st.form_submit_button("Adjuntar fotografía de corrección")
            if subir_correccion:
                if foto_correccion is None or len(nota_foto_correccion.strip()) < 10:
                    st.warning("Selecciona una fotografía y describe su contenido.")
                else:
                    uploaded = call(
                        "POST", f"/campo/aplicaciones/{trabajo_id}/evidencias",
                        files={"archivo": (
                            foto_correccion.name, foto_correccion.getvalue(),
                            foto_correccion.type or "image/jpeg"
                        )},
                        data={"observaciones": nota_foto_correccion.strip()},
                    )
                    if uploaded:
                        st.session_state["rf07_evento_exitoso"] = True
                        st.rerun()

            st.subheader("Subsanación y nueva inspección")
            with st.form("rf08_subsanar"):
                nota_subsanacion = st.text_area(
                    "Describe las acciones correctivas",
                    placeholder="Detalla qué puntos del dictamen se atendieron.",
                    max_chars=1500, height=130,
                )
                enviar_subsanacion = st.form_submit_button(
                    "Enviar correcciones a calidad", type="primary"
                )
            if enviar_subsanacion:
                result = call(
                    "POST", f"/campo/aplicaciones/{trabajo_id}/subsanar",
                    json={"observaciones": nota_subsanacion.strip()},
                )
                if result:
                    st.session_state["rf07_evento_exitoso"] = True
                    st.rerun()
        elif trabajo["estado"] == "pendiente_calidad":
            st.info("Trabajo completado al 100 %. Pendiente de revisión de calidad.")
        elif trabajo["estado"] == "calidad_aprobada":
            st.success("La inspección de calidad fue aprobada.")
        elif trabajo["estado"] == "calidad_rechazada":
            st.error("La inspección fue rechazada. Consulta el expediente.")
        else:
            st.info("Estado no disponible para nuevas actividades.")
        st.divider()
        st.subheader("Bitácora cronológica")
        mostrar_bitacora_campo(trabajo)
    st.stop()

if profile["role"] in {"asesor", "especialista_tecnico", "administrador"}:
    st.subheader("Bandeja de revisión técnica")
    st.caption(
        "Revisa antecedentes y deja una decisión humana auditable. "
        "Ninguna aprobación reserva inventario ni genera despachos."
    )
    bandeja_asesor = call("GET", "/revision/bandeja") or []
    if not bandeja_asesor:
        st.success("No hay solicitudes pendientes en la bandeja.")
    else:
        st.metric("Solicitudes por revisar", len(bandeja_asesor))
        st.dataframe(bandeja_asesor, hide_index=True, use_container_width=True)
        opciones_asesor = {
            f"{s['nombre_empresa']} · {s['nombre_proyecto']} · {s['solicitud_id'][:8]}":
                s["solicitud_id"] for s in bandeja_asesor
        }
        caso_asesor = st.selectbox(
            "Solicitud que vas a revisar", list(opciones_asesor), key="asesor_solicitud"
        )
        solicitud_id_asesor = opciones_asesor[caso_asesor]
        detalle_asesor = call(
            "GET", f"/revision/solicitudes/{solicitud_id_asesor}/detalle"
        )
        if detalle_asesor:
            s = detalle_asesor["solicitud"]
            st.write(f"**Estado actual:** {s['estado']} · **Descripción:** {s['descripcion_libre']}")
            render_stepper(s["estado"], compact=True)
            st.write("**Proyecto y condiciones**")
            st.json(detalle_asesor["proyecto"])
            st.write("**Último análisis de Gemini**")
            if detalle_asesor["analisis"]:
                st.json(detalle_asesor["analisis"]["resultado"])
            else:
                st.warning("No existe análisis de Gemini para este caso.")
            st.write("**Último cálculo técnico**")
            if detalle_asesor["calculo"]:
                st.json(detalle_asesor["calculo"])
            else:
                st.warning("No hay cálculo técnico para este caso.")
            st.write("**Evaluación de inventario**")
            if detalle_asesor["inventario"]:
                st.json(detalle_asesor["inventario"])
            else:
                st.info("Aún no hay evaluación de disponibilidad.")
            if detalle_asesor.get("respuestas_cliente"):
                st.write("**Respuestas enviadas por el cliente**")
                for respuesta_cliente in detalle_asesor["respuestas_cliente"]:
                    with st.expander(
                        f"{respuesta_cliente['created_at'][:19]} · "
                        f"{respuesta_cliente['estado_nuevo']}",
                        expanded=True,
                    ):
                        st.write(respuesta_cliente["respuesta"])
                        st.caption("Respuesta vinculada a la revisión: "
                                   + respuesta_cliente["revision_id"][:8])
            if detalle_asesor["revisiones"]:
                with st.expander("Historial de decisiones humanas"):
                    render_event_timeline(
                        detalle_asesor["revisiones"], event_key="decision",
                    )
                    st.dataframe(
                        detalle_asesor["revisiones"],
                        use_container_width=True, hide_index=True,
                    )
            st.divider()
            st.subheader("Registrar decisión humana")
            opciones_decision = {
                "Aprobar técnicamente": "aprobar",
                "Rechazar solicitud": "rechazar",
                "Solicitar más información": "solicitar_informacion",
                "Solicitar corrección de un parámetro": "solicitar_correccion",
            }
            decision_label = st.selectbox(
                "Decisión", list(opciones_decision), key="decision_humana"
            )
            decision = opciones_decision[decision_label]
            with st.form("resolver_revision"):
                observaciones = st.text_area(
                    "Justificación técnica (obligatoria)",
                    height=160,
                    max_chars=2000,
                )
                correccion = None
                if decision == "solicitar_correccion":
                    campo = st.selectbox(
                        "Campo que requiere corrección",
                        ["area_m2", "tipo_superficie", "condicion", "ambiente", "color_requerido"],
                    )
                    valor = st.text_input(
                        "Valor propuesto", help="Se registra la propuesta; NO se cambia el proyecto automáticamente."
                    )
                    correccion = {"campo": campo, "valor_propuesto": valor.strip()}
                st.caption(
                    "La aprobación no autoriza logística; cualquier parámetro corregido "
                    "deberá verificarse y recalcularse antes de continuar."
                )
                aceptar = st.form_submit_button(
                    "Registrar decisión", type="primary",
                )
            if aceptar:
                body = {
                    "decision": decision,
                    "observaciones": observaciones.strip(),
                    "correccion_propuesta": correccion,
                }
                resultado_humano = call(
                    "POST",
                    f"/revision/solicitudes/{solicitud_id_asesor}/resolver",
                    json=body,
                )
                if resultado_humano:
                    st.success(
                        f"Decisión registrada: {resultado_humano['decision']}. "
                        f"Nuevo estado: {resultado_humano['estado_nuevo']}."
                    )
                    st.rerun()
    st.stop()
if profile["role"] != "cliente":
    st.info("Este rol aún no tiene una pantalla operativa.")
    st.stop()

# Una sola página por vez: evita cargar 11 módulos y sus peticiones en paralelo.
# Los formularios, claves y llamadas originales permanecen intactos.

if client_page == "Mi empresa":
    section_intro("PERFIL", "Tus empresas", "Crea y consulta organizaciones vinculadas a tu cuenta.")
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

if client_page == "Proyectos":
    section_intro("PLANIFICACIÓN", "Proyectos", "Organiza nuevos proyectos y consulta sus condiciones registradas.")
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

if client_page == "Solicitudes":
    section_intro("CAPTURA", "Solicitudes y evidencias", "Radica necesidades y adjunta fotografías a tus solicitudes.")
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
        selected_request = next(
            row for row in solicitudes if row["id"] == by_request[seleccionado]
        )
        project_names = {p["id"]: p["nombre_proyecto"] for p in proyectos}
        render_request_panel(
            selected_request, project_names,
            title="Expediente de solicitud", detail=True,
        )
        render_stage_explorer(
            selected_request.get("estado"), key="cl_request_stage",
        )
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

if client_page == "Mi panel":
    section_intro(
        "VISTA GENERAL", "Tu actividad en un vistazo",
        "Datos reales de las empresas, proyectos y solicitudes de esta cuenta.",
    )
    clientes = call("GET", "/capture/clientes") or []
    proyectos = call("GET", "/capture/proyectos") or []
    solicitudes = call("GET", "/capture/solicitudes") or []
    metric_cards([
        ("Empresas", len(clientes), "Organizaciones registradas", "building-2"),
        ("Proyectos", len(proyectos), "Proyectos vinculados", "folder-kanban"),
        ("Solicitudes", len(solicitudes), "Solicitudes radicadas", "files"),
    ])
    section_intro(
        "SEGUIMIENTO", "El recorrido de tus solicitudes",
        "Consulta el estado real de cada expediente y la próxima sección de interés.",
    )
    render_state_distribution(solicitudes)
    if solicitudes:
        dashboard_project_names = {p["id"]: p["nombre_proyecto"] for p in proyectos}
        dashboard_request_ids = {
            f"#{row['id'][:8].upper()} · "
            f"{dashboard_project_names.get(row.get('proyecto_id'), 'Proyecto')} · "
            f"{request_state(row.get('estado'))[0]}": row["id"]
            for row in solicitudes
        }
        dashboard_selected_label = st.selectbox(
            "Solicitud a seguir", list(dashboard_request_ids),
            key="cl_dashboard_request",
        )
        dashboard_selected_id = dashboard_request_ids[dashboard_selected_label]
        dashboard_request = next(
            row for row in solicitudes if row["id"] == dashboard_selected_id
        )
        render_request_panel(
            dashboard_request, dashboard_project_names,
            title="Detalle de seguimiento", detail=True,
        )
        render_stage_explorer(
            dashboard_request.get("estado"), key="cl_dashboard_stage",
        )
        _, _, next_page, action_label = request_state(
            dashboard_request.get("estado")
        )
        st.button(
            action_label, type="primary",
            use_container_width=True, key="cl_next_client_action",
            on_click=lambda page=next_page: st.session_state.update(
                {"cl_page": page}
            ),
        )
    else:
        st.info(
            "Todavía no hay solicitudes. Registra una empresa, crea un proyecto "
            "y radica tu primera solicitud para empezar su seguimiento."
        )
        if proyectos:
            st.button(
                "Crear primera solicitud", type="primary",
                key="cl_create_first_request",
                on_click=lambda: st.session_state.update({"cl_page": "Solicitudes"}),
            )
        else:
            st.button(
                "Comenzar con mi empresa", type="primary",
                key="cl_create_first_company",
                on_click=lambda: st.session_state.update({"cl_page": "Mi empresa"}),
            )
    section_intro(
        "ACCESOS DIRECTOS", "¿Qué necesitas hacer?",
        "Continúa en el módulo correspondiente sin recorrer las demás secciones.",
    )
    q1, q2, q3 = st.columns(3)
    with q1:
        st.button(
            "Gestionar proyectos", key="cl_quick_projects",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"cl_page": "Proyectos"}),
        )
    with q2:
        st.button(
            "Ver solicitudes", key="cl_quick_requests",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"cl_page": "Solicitudes"}),
        )
    with q3:
        st.button(
            "Seguimiento de calidad", key="cl_quick_quality",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"cl_page": "Control de calidad"}),
        )
    st.caption(
        "Los indicadores reflejan exclusivamente los registros de la sesión actual. "
        "Selecciona una sección del menú lateral para continuar."
    )


if client_page == "Análisis con Gemini":
    st.subheader("Clasificación inteligente de solicitudes")
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


if client_page == "Cálculo técnico":
    st.subheader("Cálculo técnico de materiales")
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
            st.caption("Rendimiento de referencia. Verifica la ficha técnica antes de comprar materiales.")
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
                st.caption("Estimación basada en valores de referencia. Confirma las especificaciones del producto.")
            with st.expander("Historial de cálculos"):
                st.dataframe(records, use_container_width=True, hide_index=True)


if client_page == "Inventario":
    st.subheader("Disponibilidad de materiales por bodegas y lotes")
    st.info(
        "Consulta existencias y propone lotes por fecha de vencimiento. "
        "Esta consulta no reserva ni descuenta existencias."
    )
    solicitudes_stock = call("GET", "/capture/solicitudes") or []
    if not solicitudes_stock:
        st.warning("Primero registra una solicitud y calcula materiales.")
    else:
        opciones_solicitudes = {
            f"{s['created_at'][:10]} · {s['id'][:8]}": s["id"]
            for s in solicitudes_stock
        }
        seleccion = st.selectbox("Solicitud", list(opciones_solicitudes), key="stock_request")
        solicitud_stock_id = opciones_solicitudes[seleccion]
        calculos_stock = call("GET", f"/tecnico/solicitudes/{solicitud_stock_id}/calculos") or []
        if not calculos_stock:
            st.info("Primero realiza el cálculo en la sección Cálculo técnico.")
        else:
            opciones_calculo = {
                f"{c['created_at'][:16]} · {c['envases']} envases de {c['presentacion_litros']} L": c["id"]
                for c in calculos_stock
            }
            seleccionado = st.selectbox(
                "Cálculo técnico", list(opciones_calculo), key="stock_calc"
            )
            calculo_id = opciones_calculo[seleccionado]
            if st.button("Consultar disponibilidad", type="primary"):
                propuesta = call(
                    "POST", f"/inventario/solicitudes/{solicitud_stock_id}/evaluar",
                    json={"calculo_id": calculo_id},
                )
                if propuesta:
                    st.success("Disponibilidad consultada y evaluación registrada.")
            historial = call(
                "GET", f"/inventario/solicitudes/{solicitud_stock_id}/evaluaciones"
            ) or []
            if historial:
                ultima = historial[0]
                st.subheader("Última evaluación")
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Envases requeridos", ultima["envases_requeridos"])
                col_b.metric("Envases disponibles", ultima["envases_disponibles"])
                col_c.metric("Envases propuestos", ultima["envases_propuestos"])
                col_d.metric("Envases faltantes", ultima["envases_faltantes"])
                if ultima["decision"] == "inventario_disponible":
                    st.success("Stock suficiente para proponer asignación de lotes.")
                else:
                    st.warning("Inventario insuficiente: evaluar producción o reposición.")
                if ultima["requiere_revision_humana"]:
                    st.warning("El caso requiere revisión técnica previa a aprobación o despacho.")
                st.caption("Propuesta de asignación de lotes. No constituye una reserva de inventario.")
                if ultima["propuestas_lotes"]:
                    st.write("**Lotes propuestos — FEFO**")
                    st.dataframe(
                        ultima["propuestas_lotes"], use_container_width=True, hide_index=True
                    )
                with st.expander("Historial de disponibilidad"):
                    st.dataframe(historial, use_container_width=True, hide_index=True)



if client_page == "Revisión técnica":
    st.subheader("Revisión técnica y respuesta al especialista")
    st.caption(
        "El cliente responde aquí a las solicitudes de información. "
        "Solo el especialista puede aprobar o rechazar."
    )
    solicitudes_revision = call("GET", "/capture/solicitudes") or []
    if not solicitudes_revision:
        st.info("Registra tu primera solicitud para consultar su revisión.")
    else:
        opciones_revision = {
            f"{s['created_at'][:10]} · {s['id'][:8]} · {s['estado']}": s["id"]
            for s in solicitudes_revision
        }
        seleccion_revision = st.selectbox(
            "Solicitud", list(opciones_revision), key="cliente_revision"
        )
        solicitud_revision_id = opciones_revision[seleccion_revision]
        detalle = call(
            "GET", f"/revision/solicitudes/{solicitud_revision_id}/detalle"
        )
        if detalle:
            estado_actual = detalle["solicitud"]["estado"]
            st.write("**Estado actual:**", estado_actual)
            render_stepper(estado_actual, compact=True)
            revisiones = detalle.get("revisiones") or []
            ultima_revision = revisiones[0] if revisiones else None
            pendiente = (
                estado_actual == "pendiente_informacion"
                and ultima_revision is not None
                and ultima_revision.get("decision") in (
                    "solicitar_informacion", "solicitar_correccion"
                )
            )

            if st.session_state.pop("respuesta_revision_exito", False):
                st.success("Respuesta registrada y enviada a revisión técnica.")

            # El formulario aparece INMEDIATAMENTE después del estado, antes del historial.
            if pendiente:
                st.subheader("Responder al especialista técnico")
                st.warning("El especialista espera tu respuesta para continuar la revisión.")
                st.write("**Información solicitada:**", ultima_revision["observaciones"])
                if ultima_revision["decision"] == "solicitar_correccion":
                    st.caption(
                        "La respuesta no altera automáticamente el proyecto, el área "
                        "ni los cálculos anteriores."
                    )
                    if ultima_revision.get("correccion_propuesta"):
                        st.json(ultima_revision["correccion_propuesta"])
                with st.form("respuesta_revision_cliente"):
                    texto_respuesta = st.text_area(
                        "Mi respuesta o aclaración",
                        placeholder="Explica la información solicitada por el especialista...",
                        max_chars=3000,
                        height=150,
                    )
                    enviado = st.form_submit_button(
                        "Enviar respuesta al especialista", type="primary"
                    )
                if enviado:
                    if len(texto_respuesta.strip()) < 10:
                        st.warning("Escribe al menos 10 caracteres de información.")
                    else:
                        guardado = call(
                            "POST",
                            f"/revision/solicitudes/{solicitud_revision_id}/responder",
                            json={"respuesta": texto_respuesta.strip()},
                        )
                        if guardado:
                            st.session_state["respuesta_revision_exito"] = True
                            st.rerun()
            elif estado_actual == "en_revision_tecnica":
                st.info("La solicitud está en revisión técnica; no hay una respuesta pendiente.")
            else:
                st.info(
                    "El formulario de respuesta solo se habilita cuando el especialista "
                    "solicita información y la solicitud queda pendiente."
                )

            if revisiones:
                st.write("**Historial de decisiones del especialista**")
                render_event_timeline(revisiones, event_key="decision")
                for revision in revisiones:
                    with st.expander(
                        f"{revision['created_at'][:19]} · "
                        f"{revision['decision']} · {revision['estado_nuevo']}",
                        expanded=False,
                    ):
                        st.write(revision["observaciones"])
                        if revision.get("correccion_propuesta"):
                            st.json(revision["correccion_propuesta"])
            else:
                st.caption("Todavía no hay decisiones de revisión registradas.")

            respuestas = detalle.get("respuestas_cliente") or []
            if respuestas:
                st.write("**Mis respuestas enviadas**")
                for respuesta in respuestas:
                    with st.expander(
                        f"{respuesta['created_at'][:19]} · Enviada al especialista",
                        expanded=False,
                    ):
                        st.write(respuesta["respuesta"])
                        st.caption(
                            "Revisión relacionada: " + respuesta["revision_id"][:8]
                        )



if client_page == "Seguimiento logístico":
    st.subheader("Seguimiento logístico de mis solicitudes")
    st.caption(
        "Solo se muestran las órdenes de tus solicitudes. "
        "La reserva y el despacho requieren un operador autorizado."
    )
    mis_ordenes = call("GET", "/logistica/ordenes") or []
    if not mis_ordenes:
        st.info("No tienes órdenes logísticas registradas. El proceso empieza tras la aprobación.")
    else:
        for mi_orden in mis_ordenes:
            with st.expander(
                f"{mi_orden['nombre_proyecto']} · {mi_orden['estado']} · "
                f"{mi_orden['created_at'][:16]}",
                expanded=(mi_orden == mis_ordenes[0]),
            ):
                st.write("**Estado de logística:**", mi_orden["estado"])
                render_stepper(mi_orden["estado_solicitud"], compact=True)
                st.write("**Envases:**", mi_orden["envases_requeridos"])
                if mi_orden.get("referencia_despacho"):
                    st.write(
                        "**Referencia de despacho:**",
                        mi_orden["referencia_despacho"],
                    )
                if mi_orden.get("lotes"):
                    st.dataframe(
                        mi_orden["lotes"], use_container_width=True, hide_index=True
                    )
                if mi_orden.get("eventos"):
                    st.write("**Eventos registrados**")
                    render_event_timeline(mi_orden["eventos"])
                    st.dataframe(
                        mi_orden["eventos"], use_container_width=True, hide_index=True
                    )



if client_page == "Aplicación en campo":
    st.subheader("Seguimiento de la aplicación de mis proyectos")
    st.caption(
        "Consulta el avance, las incidencias y las fotografías del aplicador asignado. "
        "No puedes modificar los reportes del personal de campo."
    )
    mis_trabajos = call("GET", "/campo/aplicaciones") or []
    if not mis_trabajos:
        st.info(
            "Tu solicitud está despachada; la asignación del aplicador "
            "se registrará en esta sección cuando logística la realice."
        )
    else:
        for trabajo_cliente in mis_trabajos:
            with st.expander(
                f"{trabajo_cliente['nombre_proyecto']} · "
                f"{trabajo_cliente['estado']} · {trabajo_cliente['avance_pct']}%",
                expanded=(trabajo_cliente == mis_trabajos[0]),
            ):
                st.write("**Aplicador:**", trabajo_cliente["aplicador"])
                st.write("**Estado de campo:**", trabajo_cliente["estado"])
                st.write("**Referencia de despacho:**", trabajo_cliente["referencia_despacho"])
                render_field_progress(trabajo_cliente["avance_pct"])
                if trabajo_cliente["estado"] == "pendiente_calidad":
                    st.info("Aplicación finalizada; pendiente de revisión de calidad.")
                mostrar_bitacora_campo(trabajo_cliente)



if client_page == "Control de calidad":
    section_intro("CONTROL DE CALIDAD", "Historial de calidad", "Consulta los dictámenes y el estado de cada expediente.")
    st.caption(
        "Consulta las decisiones del inspector y las correcciones solicitadas. "
        "Solo el área de calidad puede aprobar o rechazar."
    )
    mis_expedientes_calidad = call("GET", "/calidad/expedientes") or []
    if not mis_expedientes_calidad:
        st.info("No hay aún un expediente de aplicación asociado a tus proyectos.")
    else:
        for e in mis_expedientes_calidad:
            with st.expander(
                f"{e['nombre_proyecto']} · {e['estado_solicitud']} · "
                f"{e['estado_aplicacion']}",
                expanded=(e == mis_expedientes_calidad[0]),
            ):
                st.write("**Estado de calidad:**", e["estado_aplicacion"])
                st.write("**Estado de la solicitud:**", e["estado_solicitud"])
                render_stepper(e["estado_solicitud"], compact=True)
                st.write("**Aplicador asignado:**", e["aplicador"])
                if e["estado_aplicacion"] == "pendiente_calidad":
                    st.info("Caso pendiente de revisión por un inspector.")
                elif e["estado_aplicacion"] == "en_correccion":
                    st.warning("Calidad solicitó una subsanación al aplicador.")
                elif e["estado_aplicacion"] == "calidad_aprobada":
                    st.success("Dictamen de calidad aprobado.")
                elif e["estado_aplicacion"] == "calidad_rechazada":
                    st.error("Dictamen de calidad rechazado.")
                if e.get("inspecciones"):
                    render_event_timeline(e["inspecciones"], event_key="decision")
                    for i in e["inspecciones"]:
                        st.write(
                            f"**Dictamen {i['numero_inspeccion']}: {i['decision']}** "
                            f"· {i['created_at'][:19]}"
                        )
                        st.write("**Observaciones:**", i["observaciones"])
                        st.json(i["criterios"])
                else:
                    st.caption("Aún no hay dictámenes registrados.")
