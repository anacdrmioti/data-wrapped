"""
wrapped_metricas_generales.py
─────────────────────────────
Versión visual mejorada y segura del apartado "Métricas Generales"
del Spotify Wrapped.

✔ Diseño más moderno
✔ Menos gráficos estadísticos
✔ Más storytelling
✔ Cards visuales y divertidas
✔ Compatible con Streamlit
✔ Sin HTML roto
✔ Misma paleta del apartado Artistas
✔ Sin errores por columnas inexistentes
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────
# PALETA
# ─────────────────────────────────────────────────────────────

GREEN        = "#1DB954"
GREEN_LIGHT  = "#1ED760"
GREEN_DARK   = "#0d4a21"

BLACK        = "#0a0a0a"
CARD_BG      = "#111111"

LIGHT_GRAY   = "#B3B3B3"
WHITE        = "#FFFFFF"

EMOJI_PERIODO = {
    "mañana": "☀️",
    "tarde": "🌤️",
    "noche": "🌙",
    "madrugada": "🌃"
}

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────

_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
}

/* ───────── HERO ───────── */

.hero-wrap {
    background: radial-gradient(circle at top left, #0d2b18 0%, #0a0a0a 70%);
    border-radius: 28px;
    padding: 50px 36px;
    border: 1px solid #1DB95433;
    margin-bottom: 35px;
    position: relative;
    overflow: hidden;
}

.hero-wrap::after{
    content:"🎧";
    position:absolute;
    right:30px;
    top:20px;
    font-size:6rem;
    opacity:0.08;
}

.hero-year{
    font-size:5rem;
    font-weight:900;
    color:#1DB954;
    line-height:1;
}

.hero-title{
    font-size:2rem;
    font-weight:800;
    color:white;
    margin-top:8px;
}

.hero-sub{
    color:#B3B3B3;
    margin-top:10px;
    font-size:0.95rem;
}

/* ───────── TITULOS ───────── */

.sec-title{
    font-size:1.45rem;
    font-weight:900;
    color:white;
    margin-top:42px;
    margin-bottom:20px;
    display:flex;
    align-items:center;
    gap:12px;
}

.sec-title::after{
    content:"";
    flex:1;
    height:1px;
    background:linear-gradient(to right,#1DB954,transparent);
}

/* ───────── METRICAS ───────── */

.metric-card{
    background:#111111;
    border-radius:20px;
    padding:24px 18px;
    border:1px solid #1f1f1f;
    text-align:center;
    height:100%;
    transition:0.2s;
}

.metric-card:hover{
    border-color:#1DB954;
    transform:translateY(-2px);
}

.metric-value{
    font-size:2.2rem;
    font-weight:900;
    color:#1DB954;
}

.metric-label{
    font-size:0.78rem;
    color:#B3B3B3;
    text-transform:uppercase;
    letter-spacing:1px;
    margin-top:6px;
}

.metric-sub{
    font-size:0.74rem;
    color:#666;
    margin-top:5px;
}

/* ───────── BIG FACT ───────── */

.big-fact{
    background:linear-gradient(135deg,#0d2b18 0%, #111111 100%);
    border:1px solid #1DB954;
    border-radius:24px;
    padding:30px;
    margin-top:18px;
    position:relative;
    overflow:hidden;
}

.big-fact::after{
    content:"✨";
    position:absolute;
    right:25px;
    top:15px;
    font-size:4rem;
    opacity:0.08;
}

.big-fact-kicker{
    color:#1DB954;
    font-size:0.75rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:1px;
}

.big-fact-title{
    color:white;
    font-size:2rem;
    font-weight:900;
    margin-top:6px;
}

.big-fact-sub{
    color:#B3B3B3;
    margin-top:8px;
    line-height:1.6;
}

/* ───────── MINI FACT ───────── */

.fact-card{
    background:#111111;
    border-radius:18px;
    padding:18px;
    border:1px solid #1f1f1f;
    text-align:center;
    height:100%;
}

.fact-emoji{
    font-size:2rem;
}

.fact-title{
    color:#1DB954;
    font-size:0.72rem;
    text-transform:uppercase;
    letter-spacing:1px;
    margin-top:10px;
}

.fact-value{
    color:white;
    font-size:1.2rem;
    font-weight:800;
    margin-top:4px;
}

.fact-sub{
    color:#B3B3B3;
    font-size:0.75rem;
    margin-top:4px;
}

/* ───────── BANNER ───────── */

.banner-card{
    background:#111111;
    border-left:4px solid #1DB954;
    border-radius:18px;
    padding:22px;
    margin-bottom:14px;
}

.banner-kicker{
    color:#1DB954;
    font-size:0.72rem;
    text-transform:uppercase;
    letter-spacing:1px;
    font-weight:700;
}

.banner-title{
    color:white;
    font-size:1.4rem;
    font-weight:900;
    margin-top:4px;
}

.banner-sub{
    color:#B3B3B3;
    margin-top:4px;
    font-size:0.85rem;
}

/* ───────── TRACKS ───────── */

.track-card{
    background:#111111;
    border-radius:18px;
    padding:18px 20px;
    border:1px solid #1f1f1f;
    margin-bottom:12px;
}

.track-top{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:10px;
}

.track-name{
    color:white;
    font-weight:800;
    font-size:1rem;
}

.track-rank{
    color:#1DB954;
    font-weight:900;
}

.track-sub{
    color:#B3B3B3;
    margin-top:6px;
    font-size:0.82rem;
}

</style>
"""

# ─────────────────────────────────────────────────────────────
# AUXILIARES
# ─────────────────────────────────────────────────────────────

def _sec(title):
    st.markdown(
        f'<div class="sec-title">{title}</div>',
        unsafe_allow_html=True
    )

def _metric(value, label, sub=""):
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """

def _fact(emoji, title, value, sub=""):
    return f"""
    <div class="fact-card">
        <div class="fact-emoji">{emoji}</div>
        <div class="fact-title">{title}</div>
        <div class="fact-value">{value}</div>
        <div class="fact-sub">{sub}</div>
    </div>
    """

# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────

def render_metricas_generales(
    df_usuarios_resumen,
    df_pref_periodo,
    df_pref_dia,
    df_escuchas,
    df_artistas,
    df_tracks,
):

    st.markdown(_CSS, unsafe_allow_html=True)

    if df_usuarios_resumen.empty:
        st.warning("No hay datos disponibles.")
        return

    resumen = df_usuarios_resumen.iloc[0]

    def safe(v, default=0):
        return default if pd.isna(v) else v

    anio = pd.to_datetime(resumen.get("fecha_ultima_escucha", pd.Timestamp.today())).year

    horas_totales = safe(resumen.get("minutos_totales_escuchados", 0)) / 60
    dias_musica = horas_totales / 24

    reproducciones = int(safe(resumen.get("total_escuchas", 0)))
    artistas = int(safe(resumen.get("artistas_unicos", 0)))
    tracks = int(safe(resumen.get("tracks_unicos", 0)))

    # ─────────────────────────────────────────
    # HERO (FIX: todo en un solo markdown)
    # ─────────────────────────────────────────

    st.markdown(f"""
    <div class="hero-wrap">
        <div class="hero-year">¡Bienvenido!</div>
        <div class="hero-title">Descubre cómo ha sido tu vida en música</div>
        <div class="hero-sub">Has vivido este periodo con muchísimo soundtrack.</div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # MÉTRICAS
    # ─────────────────────────────────────────

    st.markdown("## 📊 Tus números")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(_metric(f"{horas_totales:,.0f}h", "Escuchadas", f"{dias_musica:.1f} días"), unsafe_allow_html=True)

    with c2:
        st.markdown(_metric(f"{reproducciones:,}", "Reproducciones", "vibes"), unsafe_allow_html=True)

    with c3:
        st.markdown(_metric(f"{artistas:,}", "Artistas", "acompañándote"), unsafe_allow_html=True)

    with c4:
        st.markdown(_metric(f"{tracks:,}", "Canciones", "diferentes"), unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # TOP ARTISTA (FIX KEY ERRORS)
    # ─────────────────────────────────────────

    if not df_artistas.empty and "minutos_totales" in df_artistas.columns:

        top_artista = df_artistas.sort_values("minutos_totales", ascending=False).iloc[0]

        nombre_artista = top_artista.get("nombre_artista", "Desconocido")
        minutos = safe(top_artista.get("minutos_totales", 0))
        reps = int(safe(top_artista.get("reproducciones_totales", 0)))

        st.markdown(f"""
        <div class="big-fact">
            <div class="big-fact-kicker">Tu obsesión máxima</div>
            <div class="big-fact-title">{nombre_artista}</div>
            <div class="big-fact-sub">
                Lo escuchaste <b>{minutos:,.0f} minutos</b> y
                <b>{reps:,} veces</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # HORAS (FIX SAFE COLUMN CHECK)
    # ─────────────────────────────────────────

    st.markdown("## 🕒 Tu momento más musical")

    if not df_escuchas.empty and "hora" in df_escuchas.columns:

        hora_df = df_escuchas.groupby("hora").size().reset_index(name="escuchas")

        hora_top = hora_df.sort_values("escuchas", ascending=False).iloc[0]
        hora = int(hora_top["hora"])

        st.markdown(f"""
        <div class="big-fact">
            <div class="big-fact-kicker">Tu hora favorita</div>
            <div class="big-fact-title">🌙 {hora:02d}:00 h</div>
            <div class="big-fact-sub">
                Registraste <b>{int(hora_top['escuchas']):,}</b> escuchas.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # PERIODOS
    # ─────────────────────────────────────────

    st.markdown("## 🌅 Tu ritmo musical")

    col1, col2 = st.columns(2)

    with col1:
        if not df_pref_periodo.empty:

            periodo = df_pref_periodo.sort_values("minutos", ascending=False).iloc[0]

            st.markdown(f"""
            <div class="banner-card">
                <div class="banner-kicker">Tu franja favorita</div>
                <div class="banner-title">🌤️ {periodo.get('periodo_dia','').capitalize()}</div>
                <div class="banner-sub">{periodo.get('minutos',0):,.0f} minutos</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if not df_pref_dia.empty:

            dia = df_pref_dia.sort_values("minutos", ascending=False).iloc[0]

            st.markdown(f"""
            <div class="banner-card">
                <div class="banner-kicker">Tu día favorito</div>
                <div class="banner-title">📅 {dia.get('nombre_dia_semana','').capitalize()}</div>
                <div class="banner-sub">Tu día más musical</div>
            </div>
            """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # CURIOSES
    # ─────────────────────────────────────────

    st.markdown("## ✨ Curiosidades")

    pct_shuffle = safe(resumen.get("pct_shuffle", 0)) * 100
    pct_skip = safe(resumen.get("pct_saltada", 0)) * 100
    pct_finish = safe(resumen.get("pct_fin_natural", 0)) * 100

    dias_activos = safe(resumen.get("dias_activos", 0))

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🔥 Días activos", dias_activos)
    c2.metric("💚 Terminadas", f"{pct_finish:.0f}%")
    c3.metric("🔀 Shuffle", f"{pct_shuffle:.0f}%")
    c4.metric("⏭️ Skips", f"{pct_skip:.0f}%")

    # ─────────────────────────────────────────
    # TOP TRACKS (FIX KEY ERROR)
    # ─────────────────────────────────────────

    st.markdown("## 🎵 Canciones más repetidas")

    if not df_tracks.empty:

        top_tracks = df_tracks.sort_values(
            "reproducciones_totales",
            ascending=False
        ).head(5)

        for i, (_, row) in enumerate(top_tracks.iterrows(), 1):

            nombre = row.get("nombre_cancion", "Sin nombre")
            reps = int(safe(row.get("reproducciones_totales", 0)))

            st.markdown(f"""
            <div class="banner-card">
                <div class="banner-kicker">TOP #{i}</div>
                <div class="banner-title">{nombre}</div>
                <div class="banner-sub">🎧 {reps:,} reproducciones</div>
            </div>
            """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────

    st.markdown("""
    <div style="text-align:center;color:#666;margin-top:40px;font-size:0.8rem;">
        Hecho con ❤️ y demasiada música
    </div>
    """, unsafe_allow_html=True)