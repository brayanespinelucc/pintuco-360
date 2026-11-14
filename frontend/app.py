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
                        st.image(contenido, caption="Evidencia de campo académica")


st.markdown('<span class="brand">COLORLINK · PINTUCO 360</span>', unsafe_allow_html=True)
st.caption("Plataforma académica · No es un portal oficial de Pintuco · Interfaz 0.9.0")

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
if profile["role"] == "logistica":
    st.subheader("RF-06 · Logística académica")
    st.warning(
        "Simulación con bodegas y lotes DEMOSTRATIVOS. "
        "Las reservas y despachos modificarán únicamente los saldos de prueba."
    )
    if st.session_state.pop("rf06_exito", False):
        st.success("Operación registrada en Supabase y sujeta a auditoría.")
    st.caption(
        "Se puede reservar solo una solicitud aprobada. "
        "La secuencia es RESERVAR → PREPARAR → DESPACHAR. "
        "Una reserva puede cancelarse antes de despachar."
    )

    pendientes_logistica = call("GET", "/logistica/bandeja") or []
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
        if actual_pendiente["disponibles_ahora"] < actual_pendiente["envases_requeridos"]:
            st.warning("No alcanza el stock actual. No se permitirá una reserva parcial.")
        with st.form("rf06_reservar"):
            observacion_reserva = st.text_area(
                "Observación de reserva",
                value="Reserva académica de materiales para la solicitud aprobada.",
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

    st.divider()
    st.subheader("Órdenes logísticas y trazabilidad")
    ordenes_activas = call("GET", "/logistica/ordenes") or []
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
        if orden.get("referencia_despacho"):
            st.write("**Referencia de despacho simulada:**", orden["referencia_despacho"])
        if orden.get("lotes"):
            st.write("**Lotes asociados**")
            st.dataframe(orden["lotes"], use_container_width=True, hide_index=True)
        if orden.get("eventos"):
            with st.expander("Historial de eventos"):
                st.dataframe(orden["eventos"], use_container_width=True, hide_index=True)

        acciones_posibles = {
            "reservada": {"Preparar envases": "preparar", "Cancelar reserva": "cancelar"},
            "preparada": {"Despachar (simulado)": "despachar", "Cancelar reserva": "cancelar"},
        }.get(orden["estado"], {})
        if acciones_posibles:
            nombre_accion = st.selectbox(
                "Siguiente operación", list(acciones_posibles), key="rf06_accion"
            )
            accion_logistica = acciones_posibles[nombre_accion]
            with st.form("rf06_operacion"):
                observacion_accion = st.text_area(
                    "Observaciones de la operación",
                    value="Se registra la operación logística académica con trazabilidad.",
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
            st.success("Despacho académico finalizado; la solicitud pasa a RF-07.")
        else:
            st.info("La reserva fue cancelada; se puede crear otra si la solicitud está aprobada.")
    else:
        st.info("Todavía no hay órdenes de logística registradas.")

    st.divider()
    st.subheader("RF-07 · Asignación de trabajos de campo")
    st.caption(
        "Asigna las solicitudes con despacho confirmado a una cuenta aplicador. "
        "La asignación es académica y no constituye programación de una visita real."
    )
    elegibles_campo = call("GET", "/campo/elegibles") or []
    usuarios_aplicadores = call("GET", "/campo/aplicadores") or []
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
                value="Asignación académica para seguimiento y aplicación en campo simulado.",
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
                st.progress(trabajo["avance_pct"] / 100)
                mostrar_bitacora_campo(trabajo)
    st.stop()

if profile["role"] == "calidad":
    st.subheader("RF-08 · Control de calidad académico")
    st.warning(
        "Los dictámenes se registran como ejercicios universitarios. "
        "No equivalen a una inspección certificada ni una aprobación comercial."
    )
    if st.session_state.pop("rf08_dictamen_exitoso", False):
        st.success("Dictamen humano de calidad registrado con trazabilidad.")
    bandeja_calidad = call("GET", "/calidad/bandeja") or []
    expedientes_calidad = call("GET", "/calidad/expedientes") or []
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
            st.write("**Despacho simulado:**", expediente["referencia_despacho"])
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
                st.dataframe(
                    expediente["inspecciones"], hide_index=True,
                    use_container_width=True,
                )
            st.divider()
            st.subheader("Lista de verificación y dictamen")
            st.caption(
                "Marca solo criterios que verificaste en el escenario académico. "
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
                    "y que es exclusivamente académico."
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
                    st.warning("Confirma que revisaste el expediente académico.")
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
    st.divider()
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
                    st.dataframe(
                        e["inspecciones"], hide_index=True, use_container_width=True
                    )
                else:
                    st.caption("Sin decisiones de calidad registradas.")
    else:
        st.info("Aún no hay expedientes en control de calidad.")
    st.stop()


if profile["role"] == "aplicador":
    st.subheader("RF-07 · Ejecución y seguimiento en campo")
    st.warning(
        "Este flujo representa una simulación universitaria. No reemplaza "
        "inspecciones, instrucciones de seguridad ni aplicación técnica real."
    )
    if st.session_state.pop("rf07_evento_exitoso", False):
        st.success("Actividad registrada en Supabase.")
    trabajos = call("GET", "/campo/aplicaciones") or []
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
        st.write("**Despacho académico:**", trabajo["referencia_despacho"])
        st.metric("Avance registrado", f"{trabajo['avance_pct']} %")
        st.progress(trabajo["avance_pct"] / 100)
        if trabajo["estado"] == "asignada":
            st.subheader("Iniciar actividad")
            with st.form("rf07_inicio"):
                nota_inicio = st.text_area(
                    "Observaciones de inicio",
                    value="Inicio académico de actividades; revisión visual de la superficie y materiales.",
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
            st.info("Trabajo completado al 100 %. Pendiente de dictamen humano RF-08.")
        elif trabajo["estado"] == "calidad_aprobada":
            st.success("La inspección académica de calidad fue aprobada.")
        elif trabajo["estado"] == "calidad_rechazada":
            st.error("La inspección académica fue rechazada. Consulta el expediente.")
        else:
            st.info("Estado no disponible para nuevas actividades.")
        st.divider()
        st.subheader("Bitácora cronológica")
        mostrar_bitacora_campo(trabajo)
    st.stop()

if profile["role"] in {"asesor", "especialista_tecnico", "administrador"}:
    st.subheader("RF-05 · Bandeja del asesor técnico")
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

tab_dashboard, tab_revision, tab_cliente, tab_proyectos, tab_solicitudes, tab_ia, tab_tecnico, tab_inventario, tab_seguimiento, tab_campo, tab_calidad = st.tabs(
    ["Mi panel", "Revisión técnica", "Mi empresa", "Proyectos", "Solicitudes y fotografías",
     "Análisis con Gemini", "Cálculo técnico", "Inventario / Disponibilidad",
     "Seguimiento logístico", "Aplicación en campo", "Control de calidad"]
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


with tab_inventario:
    st.subheader("RF-04 · Disponibilidad por bodegas y lotes")
    st.info(
        "Consulta existencias en Supabase y propone lotes por fecha de vencimiento. "
        "NO reserva ni descuenta stock. Los lotes iniciales son académicos."
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
            st.info("Primero realiza el cálculo en la pestaña RF-03.")
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
                st.caption(
                    "Propuesta PROVISIONAL: no representa reserva. "
                    "Inventario demostrativo, no oficial de Pintuco."
                )
                if ultima["propuestas_lotes"]:
                    st.write("**Lotes propuestos — FEFO**")
                    st.dataframe(
                        ultima["propuestas_lotes"], use_container_width=True, hide_index=True
                    )
                with st.expander("Historial de disponibilidad"):
                    st.dataframe(historial, use_container_width=True, hide_index=True)



with tab_revision:
    st.subheader("RF-05 · Revisión técnica y respuesta al especialista")
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



with tab_seguimiento:
    st.subheader("RF-06 · Seguimiento logístico de mis solicitudes")
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
                st.write("**Envases:**", mi_orden["envases_requeridos"])
                if mi_orden.get("referencia_despacho"):
                    st.write(
                        "**Referencia de despacho de prueba:**",
                        mi_orden["referencia_despacho"],
                    )
                if mi_orden.get("lotes"):
                    st.dataframe(
                        mi_orden["lotes"], use_container_width=True, hide_index=True
                    )
                if mi_orden.get("eventos"):
                    st.write("**Eventos registrados**")
                    st.dataframe(
                        mi_orden["eventos"], use_container_width=True, hide_index=True
                    )
                st.warning(
                    "Operación únicamente académica: sin transportadora, "
                    "guía oficial ni inventario comercial de Pintuco."
                )



with tab_campo:
    st.subheader("RF-07 · Seguimiento de la aplicación de mis proyectos")
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
                st.metric("Avance", f"{trabajo_cliente['avance_pct']} %")
                st.progress(trabajo_cliente["avance_pct"] / 100)
                if trabajo_cliente["estado"] == "pendiente_calidad":
                    st.info("Aplicación finalizada; pendiente de revisión de calidad RF-08.")
                mostrar_bitacora_campo(trabajo_cliente)



with tab_calidad:
    st.subheader("RF-08 · Control de calidad de mis proyectos")
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
                st.write("**Aplicador asignado:**", e["aplicador"])
                if e["estado_aplicacion"] == "pendiente_calidad":
                    st.info("Caso pendiente de revisión por un inspector.")
                elif e["estado_aplicacion"] == "en_correccion":
                    st.warning("Calidad solicitó una subsanación al aplicador.")
                elif e["estado_aplicacion"] == "calidad_aprobada":
                    st.success("Dictamen académico de calidad aprobado.")
                elif e["estado_aplicacion"] == "calidad_rechazada":
                    st.error("Dictamen académico de calidad rechazado.")
                if e.get("inspecciones"):
                    for i in e["inspecciones"]:
                        st.write(
                            f"**Dictamen {i['numero_inspeccion']}: {i['decision']}** "
                            f"· {i['created_at'][:19]}"
                        )
                        st.write("**Observaciones:**", i["observaciones"])
                        st.json(i["criterios"])
                else:
                    st.caption("Aún no hay dictámenes registrados.")
                st.caption(
                    "Esta evaluación es académica y no constituye certificación "
                    "de obra ni control de calidad oficial de Pintuco."
                )
