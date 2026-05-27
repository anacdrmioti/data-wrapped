import io
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

from chatbot.context_builder import build_user_context, build_multi_user_context
from chatbot.llm_client import ask_groq, transcribir_audio
from chatbot.prompts import SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────
# UTILIDADES COMUNES
# ─────────────────────────────────────────────────────────────

def _hora_a_periodo_label(hora: int) -> str:
    if 6 <= hora < 13:
        return "mañana"
    elif 13 <= hora < 20:
        return "tarde"
    elif 20 <= hora < 24:
        return "noche"
    else:
        return "madrugada"


def _get_canciones_escuchadas(data: dict, persona_id: str) -> set:
    canciones = set()
    if "usuario_track" in data:
        df = data["usuario_track"]
        user_df = df[df["persona_id"] == persona_id]
        if "nombre_cancion" in user_df.columns:
            canciones.update(user_df["nombre_cancion"].dropna().str.lower().tolist())
    return canciones


def _get_artistas_escuchados(data: dict, persona_id: str) -> set:
    artistas = set()
    if "artistas" in data:
        df = data["artistas"]
        user_df = df[df["persona_id"] == persona_id]
        if "nombre_artista" in user_df.columns:
            artistas.update(user_df["nombre_artista"].dropna().str.lower().tolist())
    return artistas


def _enviar_mensaje(system_completo: str, user_input: str):
    """Llama al LLM y gestiona historial. Devuelve la respuesta."""
    historial_api = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.chat_history
    ]
    try:
        respuesta = ask_groq(system_completo, user_input, historial_api)
    except Exception as e:
        respuesta = f"Lo siento, ha ocurrido un error al conectar con el asistente: {e}"

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
    return respuesta


# ─────────────────────────────────────────────────────────────
# CARGA DE LA TABLA GLOBAL DE USUARIOS (para modo grupal)
# ─────────────────────────────────────────────────────────────

@st.cache_data
def _cargar_tabla_usuarios() -> pd.DataFrame:
    """
    Carga la tabla completa usuario_track desde data/.
    Se cachea para no leer el CSV en cada interacción.
    La primera fila puede estar corrupta (problema conocido del CSV), se limpia aquí.
    """
    try:
        df = pd.read_csv("data/usuario_track.csv")
        # Eliminar filas donde persona_id contiene comas (fila corrupta del CSV)
        df = df[~df["persona_id"].str.contains(",", na=False)]
        df = df.dropna(subset=["persona_id", "nombre_cancion", "nombre_artista"])
        df["persona_id"] = df["persona_id"].str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame()


def _get_todos_usuarios(df_global: pd.DataFrame) -> list:
    """Lista de todos los usuarios registrados en la app."""
    if df_global.empty or "persona_id" not in df_global.columns:
        return []
    return sorted(df_global["persona_id"].unique().tolist())


# ─────────────────────────────────────────────────────────────
# LÓGICA DE RECOMENDACIÓN GRUPAL (sin géneros)
# ─────────────────────────────────────────────────────────────

def _construir_contexto_grupal(df_global: pd.DataFrame, personas: list) -> str:
    """
    Construye el contexto textual para el LLM a partir de la tabla global,
    filtrando solo los usuarios seleccionados.
    No depende del CSV de géneros — trabaja solo con nombre_cancion,
    nombre_artista, score_interes y num_reproducciones.
    """
    if df_global.empty:
        return "No hay datos disponibles de los usuarios seleccionados."

    partes = []

    # ── Perfil individual de cada usuario ──────────────────────
    for persona in personas:
        df_p = df_global[df_global["persona_id"] == persona].copy()
        if df_p.empty:
            partes.append(f"\n[{persona.upper()}]: Sin datos disponibles.")
            continue

        top_canciones = (df_p.sort_values("score_interes", ascending=False)
                         .head(15)[["nombre_cancion", "nombre_artista", "score_interes"]])

        top_artistas = (df_p.groupby("nombre_artista")
                        .agg(total_min=("minutos_totales", "sum"),
                             n_canciones=("nombre_cancion", "nunique"))
                        .sort_values("total_min", ascending=False)
                        .head(10)
                        .reset_index())

        canciones_txt = "\n".join(
            f"  - {r['nombre_cancion']} ({r['nombre_artista']})"
            for _, r in top_canciones.iterrows()
        )
        artistas_txt = "\n".join(
            f"  - {r['nombre_artista']} ({int(r['total_min'])} min, {int(r['n_canciones'])} canciones)"
            for _, r in top_artistas.iterrows()
        )

        partes.append(
            f"\n{'='*45}\n"
            f"PERFIL DE {persona.upper()}\n"
            f"Total canciones escuchadas: {len(df_p)}\n"
            f"Top canciones por interés:\n{canciones_txt}\n"
            f"Top artistas por minutos:\n{artistas_txt}"
        )

    # ── Canciones comunes entre todos los usuarios ──────────────
    sets_canciones = [
        set(df_global[df_global["persona_id"] == p]["nombre_cancion"].str.lower())
        for p in personas
    ]
    comunes = sets_canciones[0]
    for s in sets_canciones[1:]:
        comunes = comunes & s

    if comunes:
        partes.append(
            f"\n{'='*45}\n"
            f"CANCIONES QUE TODOS CONOCEN ({len(comunes)} en común):\n"
            + "\n".join(f"  - {c}" for c in sorted(comunes)[:20])
        )
    else:
        partes.append(
            f"\n{'='*45}\n"
            "CANCIONES EN COMÚN: Ninguna canción exacta en común entre todos los usuarios seleccionados."
        )

    # ── Artistas comunes ────────────────────────────────────────
    sets_artistas = [
        set(df_global[df_global["persona_id"] == p]["nombre_artista"].str.lower())
        for p in personas
    ]
    artistas_comunes = sets_artistas[0]
    for s in sets_artistas[1:]:
        artistas_comunes = artistas_comunes & s

    if artistas_comunes:
        partes.append(
            f"ARTISTAS QUE TODOS ESCUCHAN:\n"
            + "\n".join(f"  - {a}" for a in sorted(artistas_comunes)[:15])
        )

    # ── Canciones que uno conoce y el otro no ──────────────────
    if len(personas) == 2:
        p1, p2 = personas[0], personas[1]
        df_p1 = df_global[df_global["persona_id"] == p1]
        df_p2 = df_global[df_global["persona_id"] == p2]

        canciones_p1 = set(df_p1["nombre_cancion"].str.lower())
        canciones_p2 = set(df_p2["nombre_cancion"].str.lower())

        solo_p1 = canciones_p1 - canciones_p2
        solo_p2 = canciones_p2 - canciones_p1

        if solo_p1:
            top_para_p2 = (df_p1[df_p1["nombre_cancion"].str.lower().isin(solo_p1)]
                           .sort_values("score_interes", ascending=False)
                           .head(8))
            txt = "\n".join(f"  - {r['nombre_cancion']} ({r['nombre_artista']})"
                            for _, r in top_para_p2.iterrows())
            partes.append(
                f"TOP CANCIONES DE {p1.upper()} QUE {p2.upper()} AÚN NO CONOCE:\n{txt}"
            )

        if solo_p2:
            top_para_p1 = (df_p2[df_p2["nombre_cancion"].str.lower().isin(solo_p2)]
                           .sort_values("score_interes", ascending=False)
                           .head(8))
            txt = "\n".join(f"  - {r['nombre_cancion']} ({r['nombre_artista']})"
                            for _, r in top_para_p1.iterrows())
            partes.append(
                f"TOP CANCIONES DE {p2.upper()} QUE {p1.upper()} AÚN NO CONOCE:\n{txt}"
            )

    partes.append(f"{'='*45}")
    return "\n\n".join(partes)


def _cancion_que_mas_une(df_global: pd.DataFrame, personas: list) -> pd.DataFrame:
    """
    Devuelve las canciones que más unen al grupo:
    canciones escuchadas por el mayor número de personas,
    ordenadas por score_interes medio entre ellas.
    """
    df_sel = df_global[df_global["persona_id"].isin(personas)]
    agg = (df_sel.groupby(["nombre_cancion", "nombre_artista"])
           .agg(
               n_usuarios=("persona_id", "nunique"),
               score_medio=("score_interes", "mean"),
               min_totales=("minutos_totales", "sum"),
           )
           .reset_index()
           .sort_values(["n_usuarios", "score_medio"], ascending=[False, False])
           .head(10))
    return agg


# ─────────────────────────────────────────────────────────────
# SUGERENCIAS DE PREGUNTAS
# ─────────────────────────────────────────────────────────────

SUGERENCIAS_INDIVIDUAL = [
    "🎵 Recomiéndame canciones para estudiar",
    "🎶 Recomiéndame canciones parecidas a La Macarena",
    "🎤 Recomiéndame canciones del artista Beethoven",
    "🌙 ¿Qué debería escuchar esta noche?",
    "⚡ Dame música energética para entrenar",
]

SUGERENCIAS_GRUPAL = [
    "🎧 Danos una playlist de mínimo 10 canciones que nos gusten a todos",
    "❤️ ¿Cuál es la canción que más nos une?",
    "🔀 Recomiéndame canciones que escucha mi amigo/a y que yo no conozca",
    "🎯 ¿En qué géneros o estilos coincidimos más?",
    "🎉 Haz una playlist perfecta para una fiesta con los dos",
]


def _chips_sugerencias(sugerencias: list, key_prefix: str):
    """
    Renderiza botones de sugerencia en fila.
    Al pulsar uno, lo inyecta en el input del chat como si lo hubiera escrito el usuario.
    """
    cols = st.columns(len(sugerencias))
    for i, (col, texto) in enumerate(zip(cols, sugerencias)):
        with col:
            if st.button(texto, key=f"{key_prefix}_sug_{i}", use_container_width=True):
                st.session_state[f"{key_prefix}_sugerencia_activa"] = texto


def _render_voz(key_prefix: str):
    """
    Muestra un grabador de audio y transcribe lo grabado con Groq Whisper.
    Si la transcripción tiene éxito, la inyecta en session_state como si
    el usuario la hubiera escrito, igual que hacen las sugerencias.

    Streamlit renderiza st.audio_input como un botón de micrófono compacto.
    Lo colocamos en la misma línea visual que el chat_input usando columnas.
    """
    audio = st.audio_input(
        "🎙️",
        key=f"{key_prefix}_audio_input",
        help="Pulsa para grabar. Pulsa de nuevo para detener. Se transcribirá automáticamente.",
        label_visibility="collapsed",   # solo se ve el icono del micro
    )


    if audio is not None:
        # IMPORTANTE: usar getvalue() no read().
        # st.audio_input devuelve un UploadedFile cuyo cursor interno puede
        # estar ya al final (read() devolvería 0 bytes). getvalue() siempre
        # devuelve el contenido completo independientemente del cursor.
        audio_bytes = audio.getvalue()

        print(f"[DEBUG] audio bytes: {len(audio_bytes)}")

        # Evitar transcribir el mismo audio dos veces cuando Streamlit rerenderiza
        ultimo_hash = st.session_state.get(f"{key_prefix}_ultimo_audio_hash")
        nuevo_hash = hashlib.md5(audio_bytes).hexdigest()

        if nuevo_hash != ultimo_hash and len(audio_bytes) > 1000:
            # len > 1000 descarta grabaciones vacías o demasiado cortas (<0.1s)
            print("[DEBUG] Audio nuevo detectado, voy a transcribir")
            st.session_state[f"{key_prefix}_ultimo_audio_hash"] = nuevo_hash

            st.audio(audio_bytes, format="audio/webm")

            with open("debug_audio.webm", "wb") as f:
                f.write(audio_bytes)

            with st.spinner("Transcribiendo..."):
                texto = transcribir_audio(audio_bytes)
            print(f"[DEBUG] texto transcrito: {repr(texto)}")

            if texto:
                st.session_state[f"{key_prefix}_sugerencia_activa"] = texto
                st.rerun()
            else:
                st.warning("No se pudo transcribir el audio. Inténtalo de nuevo.")
        else:
            print("[DEBUG] No transcribo: mismo audio o audio demasiado corto")
            print(f"[DEBUG] ultimo_hash={ultimo_hash}")
            print(f"[DEBUG] nuevo_hash={nuevo_hash}")
            print(f"[DEBUG] len={len(audio_bytes)}")

# ─────────────────────────────────────────────────────────────
# MODO INDIVIDUAL
# ─────────────────────────────────────────────────────────────

def _render_individual(data: dict, persona_id: str, ahora: datetime, dia_semana: str):
    st.markdown("#### 💡 Sugerencias de preguntas")
    _chips_sugerencias(SUGERENCIAS_INDIVIDUAL, key_prefix="ind")

    st.divider()

    # Mostrar historial
    for mensaje in st.session_state.chat_history:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    # Comprobar si hay sugerencia activa pendiente de enviar
    sugerencia = st.session_state.pop("ind_sugerencia_activa", None)

    # ── Input de texto + micrófono ──────────────────────────────
    # st.chat_input ocupa todo el ancho de forma nativa.
    # Colocamos el micrófono justo encima, alineado a la derecha,
    # para que visualmente quede "al lado" del campo de texto.
    col_mic, col_info = st.columns([1, 8])
    with col_mic:
        _render_voz(key_prefix="ind")
    with col_info:
        st.caption("🎙️ Habla o escribe tu pregunta")

    user_input = st.chat_input("¿Qué quieres escuchar ahora? ¿Estoy en bucle con una canción, recomiéndame algo parecido...")

    # La sugerencia tiene prioridad sobre el input manual
    mensaje_a_enviar = sugerencia or user_input

    if mensaje_a_enviar:
        perfil_context = build_user_context(
            data, persona_id,
            hora_actual=ahora.hour,
            dia_semana=dia_semana
        )
        cabecera = (
            f"Modo: recomendación individual\n"
            f"Usuario: {persona_id}\n"
            f"Hora actual: {ahora.strftime('%H:%M')} ({dia_semana})"
        )

        canciones_escuchadas = _get_canciones_escuchadas(data, persona_id)
        artistas_escuchados = _get_artistas_escuchados(data, persona_id)

        if canciones_escuchadas:
            lista = ", ".join(sorted(canciones_escuchadas)[:80])
            cabecera += f"\n\nCANCIONES QUE YA CONOCE (NO recomendar estas): {lista}"

        if artistas_escuchados:
            lista = ", ".join(sorted(artistas_escuchados)[:50])
            cabecera += f"\n\nARTISTAS QUE YA ESCUCHA (prioriza artistas NUEVOS): {lista}"

        system_completo = f"{SYSTEM_PROMPT}\n\n--- CONTEXTO ACTUAL ---\n{cabecera}\n\n{perfil_context}"

        with st.chat_message("user"):
            st.write(mensaje_a_enviar)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                respuesta = _enviar_mensaje(system_completo, mensaje_a_enviar)
            st.write(respuesta)

        st.rerun()


# ─────────────────────────────────────────────────────────────
# MODO GRUPAL
# ─────────────────────────────────────────────────────────────

def _render_grupal(data: dict, persona_id: str, ahora: datetime, dia_semana: str):
    """Renderiza el modo grupal completo."""

    # Cargar tabla global de todos los usuarios
    df_global = _cargar_tabla_usuarios()
    todos_usuarios = _get_todos_usuarios(df_global)

    if not todos_usuarios:
        st.error(
            "No se encontró la tabla `data/usuario_track.csv` con los datos de usuarios. "
            "Asegúrate de que el fichero existe en la carpeta `data/`."
        )
        return

    # ── Buscar y seleccionar amigos ─────────────────────────────
    st.markdown("### 👥 Seleccionar usuarios")

    col_buscar, col_invitar = st.columns([3, 1])

    with col_buscar:
        busqueda = st.text_input(
            "🔍 Buscar usuario por nombre",
            placeholder="Escribe un nombre...",
            help="Busca entre los usuarios registrados en la app"
        )

    with col_invitar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📨 Invitar amigo", use_container_width=True):
            st.session_state.mostrar_invitar = not st.session_state.get("mostrar_invitar", False)

    # Panel de invitación
    if st.session_state.get("mostrar_invitar", False):
        with st.container(border=True):
            st.markdown("#### 📨 Invita a un amigo a la app")
            st.markdown(
                "Para que tu amigo pueda unirse, necesita descargar sus datos de Spotify "
                "y subirlos a la aplicación."
            )
            st.markdown(
                "**Paso 1:** Tu amigo debe ir a su cuenta de Spotify y solicitar sus datos:\n\n"
                "👉 [Descargar datos de Spotify](https://www.spotify.com/es/account/privacy/)"
            )
            st.markdown(
                "**Paso 2:** Una vez descargados (~30 días de espera), que abra esta app, "
                "introduzca su nombre y suba el ZIP con sus datos."
            )
            st.info(
                "💡 Una vez que tu amigo suba sus datos, aparecerá automáticamente "
                "en el buscador de usuarios."
            )
            if st.button("✕ Cerrar"):
                st.session_state.mostrar_invitar = False
                st.rerun()

    # Filtrar usuarios según búsqueda
    usuarios_filtrados = todos_usuarios
    if busqueda:
        usuarios_filtrados = [u for u in todos_usuarios if busqueda.lower() in u.lower()]

    # Excluir al usuario actual de la lista de selección (ya se incluye siempre)
    usuarios_para_seleccionar = [u for u in usuarios_filtrados if u != persona_id]

    if not usuarios_para_seleccionar:
        st.warning("No se encontraron otros usuarios con ese nombre.")
        amigos_seleccionados = []
    else:
        amigos_seleccionados = st.multiselect(
            f"Usuarios encontrados ({len(usuarios_para_seleccionar)} en la app):",
            options=usuarios_para_seleccionar,
            default=st.session_state.get("amigos_seleccionados_prev", []),
            help="Puedes seleccionar varios amigos a la vez"
        )
        st.session_state.amigos_seleccionados_prev = amigos_seleccionados

    # Grupo completo = usuario actual + amigos seleccionados
    grupo = [persona_id] + amigos_seleccionados

    if len(grupo) < 2:
        st.info("👆 Selecciona al menos un amigo para empezar el chat grupal.")
        return

    # ── Panel de afinidad ──────────────────────────────────────
    st.markdown(f"### 🎵 Grupo: {' · '.join(grupo)}")

    with st.expander("🔗 Ver canciones que os unen", expanded=False):
        df_une = _cancion_que_mas_une(df_global, grupo)
        if df_une.empty or df_une["n_usuarios"].max() < 2:
            st.info("No hay canciones que todos hayáis escuchado. ¡Quizás sea el momento de descubrirlas juntos!")
        else:
            df_une_comunes = df_une[df_une["n_usuarios"] >= 2]
            if df_une_comunes.empty:
                st.info("No hay canciones compartidas entre todos los usuarios del grupo.")
            else:
                st.markdown(f"**{len(df_une_comunes)} canciones en común** entre los miembros del grupo:")
                for _, r in df_une_comunes.iterrows():
                    usuarios_str = f"{int(r['n_usuarios'])}/{len(grupo)} usuarios"
                    st.markdown(
                        f"🎵 **{r['nombre_cancion']}** — {r['nombre_artista']} "
                        f"&nbsp;|&nbsp; {usuarios_str}"
                    )

    # ── Sugerencias de preguntas ───────────────────────────────
    st.markdown("#### 💡 Sugerencias de preguntas grupales")
    _chips_sugerencias(SUGERENCIAS_GRUPAL, key_prefix="grp")

    st.divider()

    # ── Historial del chat ─────────────────────────────────────
    for mensaje in st.session_state.chat_history:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    # Sugerencia activa pendiente
    sugerencia = st.session_state.pop("grp_sugerencia_activa", None)

    # ── Input de texto + micrófono ──────────────────────────────
    col_mic, col_info = st.columns([1, 8])
    with col_mic:
        _render_voz(key_prefix="grp")
    with col_info:
        st.caption("🎙️ Habla o escribe tu pregunta")

    user_input = st.chat_input("Pregunta algo sobre el grupo...")
    mensaje_a_enviar = sugerencia or user_input

    if mensaje_a_enviar:
        # Construir contexto grupal desde la tabla global
        contexto_grupal = _construir_contexto_grupal(df_global, grupo)

        cabecera = (
            f"Modo: recomendación grupal\n"
            f"Usuarios del grupo: {', '.join(grupo)}\n"
            f"Hora actual: {ahora.strftime('%H:%M')} ({dia_semana})\n\n"
            f"INSTRUCCIÓN ESPECIAL: Recomienda únicamente artistas y canciones que NINGUNO "
            f"de los usuarios del grupo haya escuchado ya (no aparezcan en sus perfiles). "
            f"Usa los datos de afinidad para justificar las recomendaciones."
        )

        system_completo = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- CONTEXTO DEL GRUPO ---\n{cabecera}\n\n"
            f"{contexto_grupal}"
        )

        with st.chat_message("user"):
            st.write(mensaje_a_enviar)

        with st.chat_message("assistant"):
            with st.spinner("Analizando gustos del grupo..."):
                respuesta = _enviar_mensaje(system_completo, mensaje_a_enviar)
            st.write(respuesta)

        st.rerun()


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────

def render_chatbot(data: dict, persona_id: str):
    """
    Punto de entrada principal. Renderiza el chatbot completo con
    modo individual y grupal.

    Args:
        data: diccionario con los DataFrames del proyecto (del usuario actual)
        persona_id: nombre del usuario activo en la sesión
    """
    st.markdown("## 🤖 Asistente Musical")
    st.markdown("Pregúntame sobre tus gustos, pídeme recomendaciones o crea playlists grupales.")

    # Inicializar historial
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    ahora = datetime.now()
    dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    dia_semana = dias_es[ahora.weekday()]

    # ── Cabecera: modo + limpiar ────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        modo = st.radio(
            "Modo",
            ["🎧 Individual", "👥 Grupal"],
            horizontal=True,
            help="Individual: recomendaciones solo para ti. Grupal: playlist para el grupo."
        )
    with col2:
        with st.expander("ℹ️ Contexto actual"):
            st.write(f"**Usuario:** {persona_id}")
            st.write(f"**Hora:** {ahora.strftime('%H:%M')} ({_hora_a_periodo_label(ahora.hour)})")
            st.write(f"**Día:** {dia_semana.capitalize()}")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Limpiar chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.pop("amigos_seleccionados_prev", None)
            st.rerun()

    st.divider()

    # ── Renderizar modo seleccionado ───────────
    if modo == "🎧 Individual":
        _render_individual(data, persona_id, ahora, dia_semana)
    else:
        _render_grupal(data, persona_id, ahora, dia_semana)
