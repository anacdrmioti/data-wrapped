import streamlit as st
import datetime
from preparacion_datos.pipeline_limpieza_datos import pipeline_carga_y_limpieza_datos
from preparacion_datos.limpieza_datos import construir_tabla_tracks, construir_tabla_artistas, construir_tabla_usuario_track, construir_tabla_usuarios_resumen, construir_preferencias_periodo_dia, construir_preferencias_dia_semana, construir_preferencias_contexto_track, construir_tabla_escuchas, construir_matriz_usuario_track
from recomendador.recomendador_personal import generador_embeddings_canciones, recomendador_historico_escuchas
from recomendador.codificador_canciones import song_to_text
from wrapped.Wrapped_artistas_def import render_artistas_wrapped
from wrapped.Wrapped_metricasgral import render_metricas_generales
from wrapped.Wrapped_canciones_def import render_canciones_wrapped
from karaoke.karaoke_ui import render_karaoke

import pandas as pd


def goto(page: str, **kwargs):
    """Navigate to a page and optionally set extra session state."""
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.session_state.pagina = page
    st.rerun()


# =========================================================================
# GLOBAL THEME  (premium dark · matches landing aesthetic)
# =========================================================================
st.set_page_config(page_title="Spotify Analyzer", page_icon="🎧", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    /* ===== Base ===== */
    .stApp {
        background:
            radial-gradient(1100px 600px at 8% -10%, rgba(29,185,84,.18), transparent 60%),
            radial-gradient(1000px 600px at 100% 0%, rgba(139,92,246,.18), transparent 60%),
            radial-gradient(900px 700px at 50% 110%, rgba(236,72,153,.10), transparent 60%),
            #0a0a0c;
        color:#fff;
        font-family:'Inter', sans-serif;
    }
    .block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }

    /* Headings */
    h1, h2, h3, h4 {
        font-family:'Space Grotesk', sans-serif !important;
        color:#fff !important;
        letter-spacing:-.02em !important;
    }
    p, label, .stMarkdown, .stCaption { color: rgba(255,255,255,.78) !important; }

    /* ===== Hero (shared) ===== */
    .sa-hero {
        position:relative; padding: 28px 0 22px; margin-bottom: 22px;
        border-bottom: 1px solid rgba(255,255,255,.06);
    }
    .sa-eyebrow {
        display:inline-flex; align-items:center; gap:8px;
        padding: 6px 14px; border-radius:999px;
        background: rgba(29,185,84,.10);
        border: 1px solid rgba(29,185,84,.32);
        color:#1ED760; font-size:.72rem; font-weight:600;
        text-transform:uppercase; letter-spacing:.14em;
        backdrop-filter: blur(8px);
    }
    .sa-eyebrow .dot {
        width:7px; height:7px; border-radius:50%; background:#1ED760;
        box-shadow:0 0 12px #1ED760;
        animation: sa-pulse 1.8s ease-in-out infinite;
    }
    @keyframes sa-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(1.4)} }
    .sa-title {
        font-family:'Space Grotesk',sans-serif;
        font-size: clamp(2.1rem, 4vw, 3.2rem);
        font-weight:700; line-height:1.05; letter-spacing:-.03em;
        margin: 14px 0 10px; color:#fff;
    }
    .sa-title .grad {
        background: linear-gradient(120deg,#1DB954 0%,#1ED760 35%,#8B5CF6 75%,#EC4899 100%);
        background-size: 200% 200%;
        -webkit-background-clip:text; background-clip:text;
        -webkit-text-fill-color:transparent;
        animation: sa-shimmer 6s ease-in-out infinite;
    }
    @keyframes sa-shimmer { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
    .sa-sub { color: rgba(255,255,255,.62); font-size:1.02rem; max-width: 760px; margin: 0; }

    .sa-section-label {
        display:inline-block; font-size:.72rem; font-weight:700;
        text-transform:uppercase; letter-spacing:.16em;
        color:#1ED760; margin: 22px 0 8px;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        font-family:'Inter',sans-serif; font-weight:600;
        background: rgba(255,255,255,.05);
        color:#fff;
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 12px;
        padding: 10px 18px;
        transition: all .25s cubic-bezier(.2,.8,.2,1);
        backdrop-filter: blur(8px);
    }
    .stButton > button:hover {
        background: rgba(255,255,255,.09);
        border-color: rgba(255,255,255,.22);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#1ED760,#1DB954);
        color:#0a0a0a; border:none;
        box-shadow: 0 12px 30px -10px rgba(29,185,84,.55);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 40px -10px rgba(29,185,84,.7);
    }

    /* ===== Inputs ===== */
    .stTextInput input, .stTextArea textarea,
    .stMultiSelect div[data-baseweb="select"] > div,
    .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        background: rgba(255,255,255,.04) !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        color: #fff !important;
        border-radius: 12px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(29,185,84,.55) !important;
        box-shadow: 0 0 0 2px rgba(29,185,84,.15) !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] section {
        background: rgba(255,255,255,.04);
        border: 1.5px dashed rgba(255,255,255,.14);
        border-radius: 16px;
        padding: 18px;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(29,185,84,.55);
        background: rgba(29,185,84,.05);
    }

    /* Slider */
    .stSlider [role="slider"] { background:#1ED760 !important; box-shadow:0 0 0 4px rgba(29,185,84,.18); }
    .stSlider > div > div > div > div { background: linear-gradient(90deg,#1DB954,#8B5CF6) !important; }

    /* Containers / cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(160deg, rgba(255,255,255,.05), rgba(255,255,255,.015)) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 18px !important;
        backdrop-filter: blur(12px);
        transition: all .3s cubic-bezier(.2,.8,.2,1);
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(255,255,255,.16) !important;
        transform: translateY(-2px);
        box-shadow: 0 24px 60px -20px rgba(0,0,0,.55);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family:'Space Grotesk',sans-serif !important;
        color:#1ED760 !important; font-weight:700;
    }
    [data-testid="stMetricLabel"] {
        text-transform:uppercase; letter-spacing:.12em;
        font-size:.7rem !important; color: rgba(255,255,255,.55) !important;
    }

    /* Status / spinner */
    [data-testid="stStatusWidget"], div[data-testid="stStatus"] {
        background: rgba(255,255,255,.04) !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        border-radius: 14px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d10, #0a0a0c) !important;
        border-right: 1px solid rgba(255,255,255,.06);
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%; text-align:left;
        background: rgba(255,255,255,.03);
        border: 1px solid rgba(255,255,255,.06);
        margin-bottom: 6px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, rgba(29,185,84,.18), rgba(139,92,246,.18));
        border-color: rgba(29,185,84,.35);
    }

    /* Multiselect chips */
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, rgba(29,185,84,.22), rgba(139,92,246,.22)) !important;
        border: 1px solid rgba(29,185,84,.4) !important;
        color: #fff !important;
        border-radius: 999px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title_html: str, subtitle: str = "", eyebrow: str | None = None):
    """Render a premium page hero matching the landing aesthetic."""
    eyebrow_html = (
        f'<span class="sa-eyebrow"><span class="dot"></span>{eyebrow}</span>'
        if eyebrow else ""
    )
    sub = f'<p class="sa-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="sa-hero">
          {eyebrow_html}
          <h1 class="sa-title">{title_html}</h1>
          {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def back_bar(*buttons):
    """Render a right-aligned bar of back buttons. Each tuple = (label, target_page)."""
    cols = st.columns([6] + [2] * len(buttons))
    for i, (label, target) in enumerate(buttons):
        with cols[i + 1]:
            if st.button(label, key=f"back_{target}_{i}"):
                st.session_state.pagina = target
                st.rerun()


# =========================================================================
# PAGE: inicio (landing / upload)
# =========================================================================
def page_inicio():
    # ----- Premium landing styles (scoped) -----
    st.markdown(
        """
        <style>
        .landing-wrap {
    position: relative;
    padding: 90px 0 8px;  /* 👈 ESTO LO BAJA Y CENTRA TODO */
    isolation: isolate;
}
        .landing-wrap::before, .landing-wrap::after {
            content:""; position:absolute; border-radius:50%; filter: blur(90px);
            opacity:.55; z-index:-1; animation: floaty 14s ease-in-out infinite;
        }
        .landing-wrap::before { width:520px; height:520px;
            background: radial-gradient(circle, #1DB954 0%, transparent 70%);
            top:-180px; left:-120px; }
        .landing-wrap::after  { width:480px; height:480px;
            background: radial-gradient(circle, #8B5CF6 0%, transparent 70%);
            bottom:-200px; right:-120px; animation-delay:-7s; }
        @keyframes floaty {
            0%,100% { transform: translate(0,0) scale(1); }
            50%     { transform: translate(20px,-30px) scale(1.08); }
        }
        .landing-title {
            font-family:'Space Grotesk',sans-serif;
            font-size: clamp(2.6rem, 6vw, 4.6rem); line-height:1.02;
            font-weight:700; letter-spacing:-.03em; margin:18px 0 14px;
            color:#fff;
        }
        .landing-title .grad {
            background: linear-gradient(120deg,#1DB954 0%,#1ED760 35%,#8B5CF6 75%,#EC4899 100%);
            background-size: 200% 200%;
            -webkit-background-clip:text; background-clip:text;
            -webkit-text-fill-color:transparent;
            animation: shimmer 6s ease-in-out infinite;
        }
        @keyframes shimmer { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
        .landing-sub {
            font-family:'Inter',sans-serif; font-size:1.08rem; line-height:1.65;
            color: rgba(255,255,255,.72); max-width: 560px; margin-bottom: 28px;
        }
        .eq { display:inline-flex; gap:5px; align-items:flex-end; height:28px;
              margin-left:14px; vertical-align:middle; }
        .eq span { width:4px; background:linear-gradient(180deg,#1DB954,#8B5CF6);
                   border-radius:3px; animation: eq 1.1s ease-in-out infinite; }
        .eq span:nth-child(1){height:60%;animation-delay:-.2s}
        .eq span:nth-child(2){height:90%;animation-delay:-.5s}
        .eq span:nth-child(3){height:45%;animation-delay:-.1s}
        .eq span:nth-child(4){height:75%;animation-delay:-.7s}
        .eq span:nth-child(5){height:55%;animation-delay:-.3s}
        @keyframes eq { 0%,100%{transform:scaleY(.4)} 50%{transform:scaleY(1.1)} }
        .glass-card h3 {
            font-family:'Space Grotesk',sans-serif; color:#fff;
            font-size:1.25rem; margin:0 0 4px; font-weight:700;
        }
        .glass-card .ghint {
            font-family:'Inter',sans-serif; color:rgba(255,255,255,.55);
            font-size:.88rem; margin-bottom:18px;
        }
        .steps { margin: 4px 0 4px; }
        .step { display:flex; gap:14px; align-items:flex-start; padding: 10px 0;
                border-top:1px dashed rgba(255,255,255,.08); }
        .step:first-child { border-top:none; }
        .step .num {
            flex:none; width:30px; height:30px; border-radius:50%;
            display:grid; place-items:center; font-family:'Space Grotesk',sans-serif;
            font-weight:700; color:#0b0b0b;
            background: linear-gradient(135deg,#1ED760,#1DB954);
            box-shadow: 0 6px 16px -4px rgba(29,185,84,.6);
        }
        .step .t { font-family:'Inter',sans-serif; color:#fff; font-weight:600; font-size:.95rem; }
        .step .d { font-family:'Inter',sans-serif; color:rgba(255,255,255,.55); font-size:.82rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)

    left, _, right = st.columns([1, 0.23, 0.85], gap="large")

    with left:
        st.markdown(
            """
           <h1 class="landing-title">
            <span class="grad">
                Tu música,<br/>
                descifrada
            </span>
            <span class="eq">
                <span></span><span></span><span></span><span></span><span></span>
            </span>
            </h1>
            <p class="landing-sub">
              Sube tu historial de Spotify y desbloquea un análisis profundo de tu
              identidad sonora.
            </p>
            <div class="steps">
              <div class="step"><div class="num">1</div>
                <div><div class="t">Solicita tus datos</div>
                <div class="d">Spotify › Cuenta › Privacidad › Descargar datos.</div></div></div>
              <div class="step"><div class="num">2</div>
                <div><div class="t">Sube el ZIP</div>
                <div class="d">Lo procesamos al instante, todo en local.</div></div></div>
              <div class="step"><div class="num">3</div>
                <div><div class="t">Explora</div>
                <div class="d">Wrapped, recomendador IA, chatbot y karaoke.</div></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div style="margin-bottom:28px;"></div>

            <h3 style="text-align:center;">
                <span class="grad">¡Comienza la aventura!</span>
            </h3>

            <div class="ghint" style="text-align:center; margin-bottom:35px;">
                Empieza tu viaje sonoro en menos de un minuto.
            </div>
            """,
            unsafe_allow_html=True
        )
        nombre = st.text_input("Tu nombre", placeholder="¿Cómo te llamas?", label_visibility="visible")
        uploaded_file = st.file_uploader(
            "Archivo ZIP de Spotify",
            type=["zip"],
            help="Solicita tus datos en Spotify › Cuenta › Privacidad.",
        )
        st.write("")
        st.write("")
        if st.button("Entrar a mi universo  →", type="primary", use_container_width=True):
            if nombre and uploaded_file:
                st.session_state.nombre = nombre
                st.session_state.zip = uploaded_file
                goto("app")
            else:
                st.warning("Completa tu nombre y sube tu ZIP para continuar.")
        st.markdown(
            '<div style="font-family:Inter,sans-serif;font-size:.75rem;'
            'color:rgba(255,255,255,.45);text-align:center;margin-top:14px;">'
            '🔒 Tus datos se procesan localmente. Nada se almacena.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

# ------------------ PANTALLA INICIO ------------------
if st.session_state.pagina == "inicio":

    page_inicio()

# ------------------ PANTALLA APP ------------------
elif st.session_state.pagina == "app":

    # =========================================================
    # PROCESAMIENTO  (backend intacto)
    # =========================================================
    if "data_procesada" not in st.session_state:

        zip_file = st.session_state.zip

        with st.status(
            "🎧 Analizando tu universo musical...",
            expanded=True
        ) as status:

            st.write("📦 Descomprimiendo historial de Spotify...")
            st.write("🧹 Limpiando y estructurando datos...")
            st.write("🧠 Generando perfil musical...")
            st.write("✨ Preparando experiencia personalizada...")

            st.session_state.data_procesada = pipeline_carga_y_limpieza_datos(
                zip_file,
                st.session_state.nombre
            )

            status.update(
                label="Perfil musical generado correctamente ✨",
                state="complete"
            )

    hero(
        f'<span class="grad">Bienvenido, {st.session_state.nombre}.</span>',
        "Elige una experiencia para comenzar a explorar tu identidad musical.",
        eyebrow="✦ Tu panel personal",
    )

    st.markdown(
        """
        <style>
        .sa-exp-icon {
            width:52px;height:52px;border-radius:14px;display:flex;
            align-items:center;justify-content:center;font-size:24px;
            margin-bottom:14px;
            background:linear-gradient(135deg,var(--g1),var(--g2));
            box-shadow:0 8px 22px -8px var(--g1);
        }
        .sa-exp-title{font-family:'Space Grotesk',sans-serif;font-weight:700;
            font-size:1.35rem;color:#fff;margin:0 0 6px;}
        .sa-exp-desc{color:rgba(255,255,255,.6);font-size:.92rem;line-height:1.5;margin:0 0 14px;}
        .sa-exp-tag{display:inline-block;font-size:.65rem;font-weight:600;letter-spacing:.14em;
            text-transform:uppercase;color:rgba(255,255,255,.6);padding:4px 10px;border-radius:999px;
            background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);}
        </style>
        """,
        unsafe_allow_html=True,
    )

    menu = [
        ("📊", "Wrapped", "Tus métricas, artistas y canciones favoritas.",
         "wrapped_config", "#1DB954", "#1ED760"),
        ("🎯", "Recomendador", "Playlists basadas en tu historial y tu mood.",
         "recomendadores_config", "#8B5CF6", "#EC4899"),
        ("🤖", "Chatbot", "Pregunta lo que quieras sobre tus escuchas.",
         "chatbot", "#06B6D4", "#3B82F6"),
        ("🎤", "Karaoke", "Canta cualquier tema con letra sincronizada.",
         "karaoke", "#F59E0B", "#EF4444"),
    ]

    cols = st.columns(2, gap="large")
    for i, (icon, title, desc, target, g1, g2) in enumerate(menu):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="--g1:{g1};--g2:{g2};padding:6px 4px 0;">
                      <div class="sa-exp-icon">{icon}</div>
                      <div class="sa-exp-title">{title}</div>
                      <div class="sa-exp-desc">{desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Abrir {title}  →", key=f"menu_{target}",
                             use_container_width=True):
                    goto(target)

# ------------------ PANTALLA WRAPPED CONFIG ------------------
elif st.session_state.pagina == "wrapped_config":

    back_bar(("⬅️ Menú principal", "app"))

    hero(
        '📊 <span class="grad"> Spotify Wrapped</span>',
        "Explora tus métricas personalizadas basadas en tu historial real de escucha.",
        eyebrow="✦ Configuración",
    )

    st.markdown("""
    En la siguiente pantalla podrás **seleccionar un rango de fechas** para filtrar tu historial.
    Esto permitirá que las estadísticas y visualizaciones se basen únicamente en el periodo
    que desees analizar (por ejemplo, el último año o los últimos meses).

    Si no seleccionas un rango, se mostrarán las métricas basadas en **todo tu historial** disponible.

    En cualquier momento podrás ajustar este filtro y se volverán a generar todas las métricas
    y visualizaciones basadas en el nuevo rango de fechas.
    """)

    st.write("")
    if st.button("Ir a Spotify Wrapped  →", key="wrapped_btn"):
        st.session_state.pagina = "wrapped"
        st.rerun()

# ------------------ PANTALLA WRAPPED ------------------
elif st.session_state.pagina == "wrapped":

    df = st.session_state.data_procesada

    if "fecha_inicio_wrapped" not in st.session_state:
        st.session_state.fecha_inicio_wrapped = df["fecha"].min()
        st.session_state.fecha_fin_wrapped = df["fecha"].max()
        st.session_state.generacion_tablas_wrapped = True

    print(st.session_state.generacion_tablas_wrapped)

    if st.session_state.generacion_tablas_wrapped == True:

        with st.status(" Generando todas las tablas necesarias con el filtrado de fechas establecido...", expanded=True) as status:

            fecha_inicio = st.session_state.fecha_inicio_wrapped
            fecha_fin = st.session_state.fecha_fin_wrapped

            df_filtrado = df[
                (df["fecha"] >= fecha_inicio) &
                (df["fecha"] <= fecha_fin)
            ]

            st.session_state.df_tracks = construir_tabla_tracks(df_filtrado)
            st.write("Tabla de tracks generada ✅")

            st.session_state.df_artistas = construir_tabla_artistas(df_filtrado)
            st.write("Tabla de artistas generada ✅")

            st.session_state.df_usuario_track = construir_tabla_usuario_track(df_filtrado)
            st.write("Tabla usuario-track generada ✅")

            st.session_state.df_usuarios_resumen = construir_tabla_usuarios_resumen(df_filtrado, st.session_state.df_usuario_track)
            st.write("Tabla de resumen de usuario generada ✅")

            st.session_state.df_pref_periodo = construir_preferencias_periodo_dia(df_filtrado)
            st.write("Tabla de preferencias por periodo del día generada ✅")

            st.session_state.df_pref_dia = construir_preferencias_dia_semana(df_filtrado)
            st.write("Tabla de preferencias por día de la semana generada ✅")

            st.session_state.df_pref_contexto_track = construir_preferencias_contexto_track(df_filtrado)
            st.write("Tabla de preferencias por contexto de escucha generada ✅")

            st.session_state.df_escuchas = construir_tabla_escuchas(df_filtrado)
            st.write("Tabla de escuchas generada ✅")

            st.session_state.generacion_tablas_wrapped = False

            st.rerun()

    back_bar(("⬅️ Menú principal", "app"))

    hero(
        '📊 <span class="grad">Spotify Wrapped</span>',
        "Tu historial de escucha, transformado en métricas e insights.",
        eyebrow="✦ Dashboard",
    )

    st.markdown('<div class="sa-section-label">📅 Filtrar por fechas</div>', unsafe_allow_html=True)

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.date_input(
        f"Selecciona un rango de fechas (historial disponible: {fecha_min} - {fecha_max})",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    if st.button("🔄 Actualizar métricas"):
        if len(rango_fechas) == 2:
            fecha_inicio, fecha_fin = rango_fechas
        else:
            fecha_inicio, fecha_fin = fecha_min, fecha_max

        if (st.session_state.fecha_inicio_wrapped != fecha_inicio or st.session_state.fecha_fin_wrapped != fecha_fin):

            st.session_state.fecha_inicio_wrapped = fecha_inicio
            st.session_state.fecha_fin_wrapped = fecha_fin
            st.session_state.generacion_tablas_wrapped = True

            st.rerun()

    if "seccion_wrapped" not in st.session_state:
        st.session_state.seccion_wrapped = "General"

    with st.sidebar:
        st.markdown(
            '<div style="font-family:Space Grotesk,sans-serif;font-weight:700;'
            'font-size:1.1rem;color:#fff;padding:8px 6px 14px;">🎧 Wrapped</div>',
            unsafe_allow_html=True,
        )

        if st.button("📊 Métricas Generales"):
            st.session_state.seccion_wrapped = "General"

        if st.button("🎤 Artistas"):
            st.session_state.seccion_wrapped = "Artistas"

        if st.button("🎧 Canciones"):
            st.session_state.seccion_wrapped = "Canciones"

        if st.button("🎼 Géneros"):
            st.session_state.seccion_wrapped = "Generos"

        if st.button("🎯 Tipo de oyente"):
            st.session_state.seccion_wrapped = "Tipo_oyente"


    if st.session_state.seccion_wrapped == "General":

        render_metricas_generales(
            st.session_state.df_usuarios_resumen,
            st.session_state.df_pref_periodo,
            st.session_state.df_pref_dia,
            st.session_state.df_escuchas,
            st.session_state.df_artistas,
            st.session_state.df_tracks
        )

    elif st.session_state.seccion_wrapped == "Artistas":
        st.markdown("## 🎤 Métricas de Artistas")
        render_artistas_wrapped(
            st.session_state.df_artistas,
            st.session_state.df_escuchas)

    elif st.session_state.seccion_wrapped == "Canciones":
        render_canciones_wrapped(
            st.session_state.df_tracks,
            st.session_state.df_escuchas
        )

    elif st.session_state.seccion_wrapped == "Generos":
        st.markdown("## 🎼 Métricas de Géneros")

    elif st.session_state.seccion_wrapped == "Tipo_oyente":
        st.markdown("## 🎯 Tipo de oyente")

elif st.session_state.pagina == "recomendadores_config":

    df = st.session_state.data_procesada

    back_bar(("⬅️ Menú principal", "app"))

    hero(
        '🎯 <span class="grad">Recomendador personal</span>',
        "Playlists generadas a partir de tu historial real y tu mood actual.",
        eyebrow="✦ Configuración",
    )

    st.markdown("""
    El sistema se basa **exclusivamente en tu historial de Spotify**, por lo que todas las
    recomendaciones están personalizadas según tu comportamiento real de escucha.

    Para construir tu perfil musical, el modelo tiene en cuenta:
    - La frecuencia con la que escuchas cada canción
    - El tiempo total de reproducción
    - Si sueles saltar o finalizar las canciones
    - El comportamiento de escucha en distintos momentos del día y días de la semana

    Antes de generar las recomendaciones, puedes seleccionar un rango de fechas para filtrar
    tu historial. Si deseas modificar este rango, deberás volver a esta página de configuración.
    """)

    st.markdown('<div class="sa-section-label">📅 Filtrar por fechas</div>', unsafe_allow_html=True)

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.date_input(
        "Selecciona un rango de fechas",
        value=(fecha_min, fecha_max)
    )

    if len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio, fecha_fin = fecha_min, fecha_max

    st.markdown("""
    Además, el sistema también tiene en cuenta tu **estado de ánimo y contexto actual** de escucha.

    En la siguiente pantalla podrás escribir libremente cómo te sientes o qué tipo de música te apetece.
    """)

    st.write("")
    if st.button("Ir al recomendador personal  →"):
        st.session_state.pagina = "recomendador_personal"
        st.session_state.fecha_inicio_recomendador_personal = fecha_inicio
        st.session_state.fecha_fin_recomendador_personal = fecha_fin
        st.session_state.generacion_tablas_recomendador_personal = True
        st.session_state.mostrar_metricas = False
        st.rerun()

elif st.session_state.pagina == "recomendador_personal":

    df = st.session_state.data_procesada
    fecha_inicio = st.session_state.fecha_inicio_recomendador_personal
    fecha_fin = st.session_state.fecha_fin_recomendador_personal

    if st.session_state.generacion_tablas_recomendador_personal == True:
        with st.status(" Generando todas las tablas necesarias con el filtrado de fechas establecido...", expanded=True) as status:

            df_filtrado = df[
                (df["fecha"] >= fecha_inicio) &
                (df["fecha"] <= fecha_fin)
            ]

            st.session_state.df_tracks_recomendador = construir_tabla_tracks(df_filtrado)
            st.write("Tabla de tracks generada ✅")

            path_canciones_clasificadas = "data/canciones_clasificadas.csv"
            st.session_state.df_embeddings_canciones = generador_embeddings_canciones(st.session_state.df_tracks_recomendador, path_canciones_clasificadas)
            st.write("Embeddings de canciones generados ✅")

            st.session_state.generacion_tablas_recomendador_personal = False

            st.rerun()

    back_bar(("⬅️ Menú principal", "app"), ("⬅️ Config Fechas", "recomendadores_config"))

    hero(
        '🎯 <span class="grad">Tu playlist inteligente</span>',
        "Combinamos tu historial con tu mood actual para recomendarte la música perfecta.",
        eyebrow="✦ Recomendador",
    )

    st.markdown('<div class="sa-section-label">🎧 Personaliza tu recomendación</div>', unsafe_allow_html=True)

    if st.button("Actualizar métricas"):
        st.session_state.mostrar_metricas = True
        st.rerun()

    if st.session_state.mostrar_metricas:

        GENEROS = [
            "pop", "rock", "indie", "alternativo",
            "hip-hop", "rap", "trap", "drill",
            "electronic", "house", "techno", "edm",
            "reggaeton", "latin", "urbano",
            "r&b", "soul", "funk",
            "jazz", "blues",
            "classical", "instrumental",
            "folk", "acoustic", "singer-songwriter",
            "metal", "punk",
            "ambient", "lofi",
            "soundtrack", "other"
        ]

        generos_usuario = st.multiselect(
            "Selecciona géneros",
            GENEROS
        )

        MOODS = [
            "feliz", "alegre", "euforico",
            "triste", "melancolico", "nostalgico",
            "romantico", "amoroso",
            "relajado", "calmado", "chill",
            "energico", "motivador", "epico",
            "agresivo", "oscuro", "intenso",
            "sensual", "suave",
            "dramatico", "profundo",
            "divertido", "fiestero",
            "other"
        ]

        moods_usuario = st.multiselect(
            "¿Qué mood buscas?",
            MOODS
        )

        CONTEXTOS = [
            "fiesta", "discoteca",
            "gym", "entrenar",
            "estudiar", "trabajar",
            "conducir", "viajar",
            "casa", "relax",
            "noche", "madrugada",
            "mañana", "tarde",
            "verano", "invierno",
            "romance", "cita",
            "tristeza", "desamor",
            "concentracion",
            "social", "amigos",
            "other"
        ]

        contextos_usuario = st.multiselect(
            "¿En qué contexto escucharás música?",
            CONTEXTOS
        )

        st.markdown('<div class="sa-section-label">⚡ Características musicales</div>', unsafe_allow_html=True)

        energia_usuario = st.slider(
            "Nivel de energía",
            min_value=0.0,
            max_value=1.0,
            value=0.5
        )

        danceability_usuario = st.slider(
            "Nivel de baile",
            min_value=0.0,
            max_value=1.0,
            value=0.5
        )

        valencia_usuario = st.slider(
            "Valencia emocional",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = triste/melancólico · 1 = alegre/feliz"
        )

        instrumentalidad_usuario = st.slider(
            "Nivel instrumental",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = canciones centradas en la voz · 1 = canciones centradas en la instrumentación"
        )

        intensidad_usuario = st.slider(
            "Intensidad emocional",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = suave/relajado · 1 = intenso/explosivo"
        )

        idioma_usuario = st.multiselect(
            "Idioma",
            ["espanol", "ingles", "frances", "coreano", "japones"],
            help="Filtra canciones por idioma"
        )

        if st.button("Obtener mi playlist personalizada  →"):

            query = song_to_text(
                moods_usuario,
                generos_usuario,
                contextos_usuario,
                energia_usuario,
                valencia_usuario,
                danceability_usuario,
                instrumentalidad_usuario,
                intensidad_usuario
            )

            recomendaciones_historico = recomendador_historico_escuchas(
                query,
                idioma_usuario,
                st.session_state.df_tracks_recomendador,
                st.session_state.df_embeddings_canciones
            )

            st.session_state.recomendaciones_historico = recomendaciones_historico

            st.session_state.mostrar_metricas = False
            st.rerun()


    # Mostrar playlist si existe
    if "recomendaciones_historico" in st.session_state:

        st.markdown('<div class="sa-section-label">🎧 Tu playlist recomendada</div>', unsafe_allow_html=True)

        st.markdown(
            """
            <style>
            .sa-rank {
                width:42px;height:42px;border-radius:12px;display:flex;align-items:center;
                justify-content:center;font-family:'Space Grotesk',sans-serif;font-weight:700;
                font-size:1.1rem;color:#0a0a0a;
                background:linear-gradient(135deg,#1ED760,#1DB954);
                box-shadow:0 8px 22px -8px rgba(29,185,84,.6);
            }
            .sa-song {font-family:'Space Grotesk',sans-serif;font-weight:700;
                font-size:1.05rem;color:#fff;margin:0;line-height:1.25;}
            .sa-artist {color:rgba(255,255,255,.6);font-size:.88rem;margin-top:2px;}
            </style>
            """,
            unsafe_allow_html=True,
        )

        for i, row in enumerate(st.session_state.recomendaciones_historico.itertuples(), 1):

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns([0.6, 5, 1.2, 1])

                with col1:
                    st.markdown(f'<div class="sa-rank">{i}</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown(
                        f'<div class="sa-song">{row.nombre_cancion}</div>'
                        f'<div class="sa-artist">{row.nombre_artista}</div>',
                        unsafe_allow_html=True,
                    )

                with col3:
                    st.metric(
                        label="Match",
                        value=f"{row.score_recomendacion:.3f}"
                    )

                with col4:

                    if st.button("▶️", key=f"play_{i}"):

                        st.session_state.cancion_karaoke = {
                            "cancion": row.nombre_cancion,
                            "artista": row.nombre_artista
                        }

                        st.session_state.pagina = "karaoke_recomendacion"

                        st.rerun()

elif st.session_state.pagina == "karaoke_recomendacion":

    back_bar(
        ("⬅️ Menú principal", "app"),
        ("⬅️ Recomendaciones", "recomendador_personal"),
    )

    hero(
        '🎤 Karaoke de tu <span class="grad">recomendación</span>',
        "Canta tu próxima canción favorita con la letra sincronizada.",
        eyebrow="✦ Inmersivo",
    )

    render_karaoke(
        st.session_state.cancion_karaoke["cancion"],
        st.session_state.cancion_karaoke["artista"]
    )


# ------------------ PANTALLA CHATBOT ------------------
elif st.session_state.pagina == "chatbot":

    back_bar(("⬅️ Menú principal", "app"))

    hero(
        '🤖 <span class="grad">Chatbot musical</span>',
        "Pregunta lo que quieras sobre tus escuchas y tu perfil sonoro.",
        eyebrow="✦ Conversacional",
    )

    from chatbot.chatbot_ui import render_chatbot
    from preparacion_datos.limpieza_datos import (
        construir_tabla_artistas,
        construir_tabla_usuario_track,
        construir_tabla_usuarios_resumen,
        construir_preferencias_periodo_dia,
        construir_preferencias_dia_semana,
    )

    if "data_chatbot" not in st.session_state:
        with st.spinner("Preparando datos para el chatbot..."):
            df_raw = st.session_state.data_procesada

            df_ut = construir_tabla_usuario_track(df_raw)
            df_art = construir_tabla_artistas(df_raw)
            df_res = construir_tabla_usuarios_resumen(df_raw, df_ut)
            df_per = construir_preferencias_periodo_dia(df_raw)
            df_dia = construir_preferencias_dia_semana(df_raw)

            def _primer_valor(x):
                v = x.dropna()
                return v.iloc[0] if len(v) > 0 else None

            df_art_chatbot = (
                df_raw.groupby(["persona_id", "artista_clave"])
                .agg(
                    nombre_artista=("nombre_artista", _primer_valor),
                    minutos_totales=("minutos_reproducidos", "sum"),
                    reproducciones_totales=("track_clave", "count"),
                )
                .reset_index()
            )

            st.session_state.data_chatbot = {
                "usuario_track": df_ut,
                "artistas": df_art_chatbot,
                "usuarios_resumen": df_res,
                "preferencias_periodo_dia": df_per,
                "preferencias_dia_semana": df_dia,
            }

    render_chatbot(st.session_state.data_chatbot, st.session_state.nombre)

# ------------------ PANTALLA KARAOKE ------------------
elif st.session_state.pagina == "karaoke":
    st.markdown("""
    <style>
    .lyric-box {
        background: black; padding: 30px; border-radius: 20px;
        border: 3px solid #1DB954; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    back_bar(("⬅️ Menú principal", "app"))

    hero(
        '🎤 <span class="grad">Karaoke</span>',
        "Elige una canción y deja que la letra te lleve.",
        eyebrow="✦ Inmersivo",
    )

    col1, col2 = st.columns(2)
    with col1:
        cancion = st.text_input("🎵 Canción", placeholder="Ej: Ni borracho")
    with col2:
        artista = st.text_input("🎤 Artista", placeholder="Ej: Quevedo")

    if st.button("🚀 PREPARAR ESCENARIO", type="primary"):
        render_karaoke(cancion, artista)
