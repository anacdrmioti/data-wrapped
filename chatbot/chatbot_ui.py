import streamlit as st
from datetime import datetime

from chatbot.context_builder import build_user_context, build_multi_user_context
from chatbot.llm_client import ask_groq
from chatbot.prompts import SYSTEM_PROMPT


def render_chatbot(data: dict, persona_id: str):
    """
    Renderiza la interfaz del chatbot en Streamlit.

    Args:
        data: diccionario con todos los DataFrames del proyecto
        persona_id: nombre del usuario activo en la sesión
    """
    st.markdown("## 🤖 Asistente Musical")
    st.markdown("Pregúntame sobre tus gustos, pídeme recomendaciones o crea playlists grupales.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    ahora = datetime.now()
    dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    dia_semana = dias_es[ahora.weekday()]

    col1, col2 = st.columns([3, 1])
    with col1:
        modo = st.radio("Modo de recomendación", ["Individual", "Grupal"], horizontal=True)
    with col2:
        if st.button("🗑️ Limpiar chat"):
            st.session_state.chat_history = []
            st.rerun()

    personas_seleccionadas = [persona_id]
    if modo == "Grupal":
        if "usuarios_resumen" in data:
            todos_usuarios = data["usuarios_resumen"]["persona_id"].tolist()
        else:
            todos_usuarios = [persona_id]

        personas_seleccionadas = st.multiselect(
            "Selecciona los usuarios para la playlist grupal",
            options=todos_usuarios,
            default=[persona_id],
            help="Selecciona al menos dos usuarios para generar recomendaciones grupales"
        )
        if len(personas_seleccionadas) < 2:
            st.warning("Selecciona al menos dos usuarios para el modo grupal.")

    with st.expander("ℹ️ Contexto actual"):
        st.write(f"**Usuario:** {persona_id}")
        st.write(f"**Hora:** {ahora.strftime('%H:%M')} ({_hora_a_periodo_label(ahora.hour)})")
        st.write(f"**Día:** {dia_semana.capitalize()}")
        if modo == "Grupal":
            st.write(f"**Usuarios en grupo:** {', '.join(personas_seleccionadas)}")

    st.divider()

    for mensaje in st.session_state.chat_history:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    placeholder = (
        "¿Qué quieres escuchar esta tarde? ¿Me recomiendas algo para trabajar?"
        if modo == "Individual"
        else "¿Qué música le gustaría a todos?"
    )

    if user_input := st.chat_input(placeholder):

        if modo == "Grupal" and len(personas_seleccionadas) >= 2:
            perfil_context = build_multi_user_context(data, personas_seleccionadas)
            cabecera = (
                f"Modo: recomendación grupal\n"
                f"Usuarios: {', '.join(personas_seleccionadas)}\n"
                f"Hora actual: {ahora.strftime('%H:%M')} ({dia_semana})"
            )
        else:
            perfil_context = build_user_context(
                data,
                persona_id,
                hora_actual=ahora.hour,
                dia_semana=dia_semana
            )
            cabecera = (
                f"Modo: recomendación individual\n"
                f"Usuario: {persona_id}\n"
                f"Hora actual: {ahora.strftime('%H:%M')} ({dia_semana})"
            )

        system_completo = f"{SYSTEM_PROMPT}\n\n--- CONTEXTO ACTUAL ---\n{cabecera}\n\n{perfil_context}"

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                historial_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history
                ]
                try:
                    respuesta = ask_groq(system_completo, user_input, historial_api)
                except Exception as e:
                    respuesta = f"Lo siento, ha ocurrido un error al conectar con el asistente: {e}"

            st.write(respuesta)

        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})


def _hora_a_periodo_label(hora: int) -> str:
    if 6 <= hora < 13:
        return "mañana"
    elif 13 <= hora < 20:
        return "tarde"
    elif 20 <= hora < 24:
        return "noche"
    else:
        return "madrugada"