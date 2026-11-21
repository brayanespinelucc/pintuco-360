"""Chat de COLORLINK: muestra siempre preguntas, errores y opciones de reintento.

El historial vive exclusivamente en st.session_state y se separa por usuario.
Las llamadas remotas utilizan la autenticación existente del portal.
"""
from __future__ import annotations

import streamlit as st

SUGGESTIONS = (
    "¿Qué pintura necesito para una pared interior de cemento?",
    "Quiero calcular cuántos litros de pintura comprar.",
    "¿Qué colores combinan con un piso gris?",
    "¿Cómo preparo una pared recién estucada?",
    "¿Qué materiales y herramientas debo utilizar?",
    "¿Qué acabado me conviene para una fachada exterior?",
)


def prepare_chat(user_id: str) -> None:
    if st.session_state.get("cl_copilot_owner") != user_id:
        st.session_state["cl_copilot_owner"] = user_id
        st.session_state["cl_copilot_history"] = []
        st.session_state.pop("cl_copilot_error", None)
        st.session_state.pop("cl_copilot_failed_prompt", None)


def _reset_chat() -> None:
    st.session_state["cl_copilot_history"] = []
    st.session_state.pop("cl_copilot_error", None)
    st.session_state.pop("cl_copilot_failed_prompt", None)


def _send(api_call, question: str, *, retry: bool = False) -> None:
    """Persist user message before remote call. Never mistake failures for answers."""
    history = st.session_state.setdefault("cl_copilot_history", [])
    st.session_state.pop("cl_copilot_error", None)
    st.session_state.pop("cl_copilot_failed_prompt", None)
    if retry:
        # The user prompt is already in history, exactly once.
        if not history or history[-1] != {"role": "user", "content": question}:
            st.session_state["cl_copilot_error"] = "No se encontró el mensaje pendiente."
            return
        context = history[:-1]
    else:
        context = history.copy()
        history.append({"role": "user", "content": question[:1500]})
        st.session_state["cl_copilot_history"] = history[-24:]

    payload = {
        "message": question[:1500],
        "history": [
            {"role": item["role"], "content": item["content"][:2500]}
            for item in context[-12:]
        ],
    }
    try:
        with st.spinner("COLORLINK está analizando tu consulta…"):
            result = api_call("POST", "/copiloto/chat", json=payload, return_errors=True)
    except Exception:
        # No publicar detalles técnicos ni credenciales en pantalla.
        result = {"_copilot_error": "No se pudo completar la consulta. Intenta de nuevo."}

    if isinstance(result, dict) and not result.get("_copilot_error"):
        answer = result.get("answer")
        if isinstance(answer, str) and answer.strip():
            assistant_message = {"role": "assistant", "content": answer[:6000]}
            if isinstance(result.get("calculation"), dict):
                assistant_message["calculation"] = result["calculation"]
            st.session_state["cl_copilot_history"].append(assistant_message)
            st.session_state["cl_copilot_history"] = st.session_state["cl_copilot_history"][-24:]
            return

    error = result.get("_copilot_error") if isinstance(result, dict) else None
    st.session_state["cl_copilot_error"] = str(
        error or "El servicio no devolvió una respuesta válida."
    )[:600]
    st.session_state["cl_copilot_failed_prompt"] = question[:1500]


@st.dialog("✦ COLORLINK · Copiloto inteligente", width="large")
def open_copilot(api_call) -> None:
    st.markdown(
        "Tu asesor de **pintura, acabados y colores**. Pregunta con naturalidad, "
        "compara opciones y calcula cantidades para tu proyecto."
    )
    history = st.session_state.setdefault("cl_copilot_history", [])
    if not history:
        st.info(
            "¡Hola! Soy tu copiloto de pintura y acabados. "
            "Puedo ayudarte a elegir materiales, combinar colores, preparar "
            "superficies y calcular cantidades. ¿Qué quieres hacer hoy?",
            icon="🎨",
        )
        first, second = st.columns(2)
        for index, label in enumerate(SUGGESTIONS):
            with first if index % 2 == 0 else second:
                if st.button(label, key=f"cl_copilot_suggestion_{index}",
                             use_container_width=True):
                    _send(api_call, label)
                    st.rerun(scope="fragment")
    elif st.button("↻ Nueva conversación", key="cl_copilot_new_chat"):
        _reset_chat()
        st.rerun(scope="fragment")

    transcript = st.container(height=390, border=False)
    with transcript:
        for message in history:
            with st.chat_message(
                "user" if message["role"] == "user" else "assistant",
                avatar="👤" if message["role"] == "user" else "🎨",
            ):
                st.markdown(message["content"], unsafe_allow_html=False)
                if message["role"] == "assistant" and isinstance(message.get("calculation"), dict):
                    calc = message["calculation"]
                    with st.expander("Ver desglose del cálculo", expanded=False):
                        st.metric("Pintura estimada", f"{calc['litros_estimados']:g} L")
                        st.write(f"Área neta: **{calc['area_neta_m2']:g} m²**")
                        st.write(f"Consumo base: **{calc['consumo_base_litros']:g} L**")
                        st.caption(
                            "Cálculo realizado por el motor matemático de COLORLINK, "
                            "independiente de la generación de texto."
                        )

    error = st.session_state.get("cl_copilot_error")
    if error:
        st.error(error, icon="⚠️")
        failed = st.session_state.get("cl_copilot_failed_prompt")
        if failed and st.button("↻ Reintentar mensaje", key="cl_copilot_retry",
                                use_container_width=True):
            _send(api_call, failed, retry=True)
            st.rerun(scope="fragment")

    prompt = st.chat_input("Escribe tu pregunta… (Shift + Enter para nueva línea)",
                           key="cl_copilot_prompt", max_chars=1500)
    if prompt and prompt.strip():
        _send(api_call, prompt.strip())
        st.rerun(scope="fragment")

    st.caption("Asesoría orientativa por IA; revisa fichas técnicas y condiciones reales de la obra.")
