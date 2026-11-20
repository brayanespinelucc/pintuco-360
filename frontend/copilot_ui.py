"""Modal de chat premium, aislado de flujos transaccionales de COLORLINK."""
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
    else:
        if st.button("↻ Nueva conversación", key="cl_copilot_new_chat"):
            st.session_state["cl_copilot_history"] = []
            st.rerun(scope="fragment")
    transcript = st.container(height=390, border=False)
    with transcript:
        for message in history:
            with st.chat_message(
                "user" if message["role"] == "user" else "assistant",
                avatar="👤" if message["role"] == "user" else "🎨",
            ):
                # st.markdown usa el renderer seguro de Streamlit; no permitimos HTML.
                st.markdown(message["content"], unsafe_allow_html=False)
    prompt = st.chat_input("Escribe tu pregunta… (Shift + Enter para nueva línea)",
                           key="cl_copilot_prompt", max_chars=1500)
    if prompt:
        _send(api_call, prompt)
        st.rerun(scope="fragment")
    st.caption("Asesoría orientativa por IA; revisa fichas técnicas y condiciones reales de la obra.")


def _send(api_call, question: str) -> None:
    history = st.session_state.setdefault("cl_copilot_history", [])
    transcript = [{"role": m["role"], "content": m["content"][:2500]}
                  for m in history[-12:]]
    with st.spinner("COLORLINK está analizando tu consulta…"):
        result = api_call("POST", "/copiloto/chat", json={
            "message": question[:1500],
            "history": transcript,
        })
    if result and isinstance(result.get("answer"), str):
        history.extend([
            {"role": "user", "content": question[:1500]},
            {"role": "assistant", "content": result["answer"]},
        ])
        # Mantener memoria acotada por sesión; jamás compartir entre identidades.
        st.session_state["cl_copilot_history"] = history[-24:]
