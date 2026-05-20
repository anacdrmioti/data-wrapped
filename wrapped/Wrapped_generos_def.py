import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# CSS GLOBAL (Wrapped Style)
# ─────────────────────────────────────────────
_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}

h1, h2, h3, h4 {
    color: white;
}

/* BIG FACT */
.big-fact{
    background:linear-gradient(135deg,#0d2b18 0%, #111111 100%);
    border:1px solid #1DB954;
    border-radius:24px;
    padding:30px;
    margin:20px 0;
}

.big-fact-title{
    color:white;
    font-size:2rem;
    font-weight:900;
}

.big-fact-kicker{
    color:#1DB954;
    font-size:0.75rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:1px;
}

.big-fact-sub{
    color:#B3B3B3;
    margin-top:10px;
}

/* GENRE CARD */
.genre-card{
    background:#111111;
    border-radius:18px;
    padding:16px;
    border:1px solid #1f1f1f;
    margin-bottom:10px;
}

.genre-name{
    color:white;
    font-weight:900;
}

.genre-badge{
    background:#1DB954;
    color:black;
    font-weight:900;
    padding:5px 10px;
    border-radius:999px;
    font-size:12px;
}

/* BAR */
.progress-bar{
    height:6px;
    background:#1f1f1f;
    border-radius:999px;
    overflow:hidden;
    margin-top:8px;
}

.progress-fill{
    height:100%;
    background:#1DB954;
}

.section-sub{
    color:#B3B3B3;
    margin-bottom:20px;
}

.genre-card,
.genre-card * {
    color: white !important;
}

</style>
"""

# ─────────────────────────────────────────────
# FUNCIÓN
# ─────────────────────────────────────────────
def render_generos_wrapped(df_usuario_track):

    st.markdown(_CSS, unsafe_allow_html=True)

    if df_usuario_track is None or df_usuario_track.empty:
        st.warning("No hay datos")
        return

    # ─────────────────────────────────────────────
    # CARGA DATA CLASIFICADA
    # ─────────────────────────────────────────────
    df_generos = pd.read_csv(
        r"C:\Users\elena\Desktop\Master\TFM\canciones_clasificadas_miguel.csv"
    )

    # ─────────────────────────────────────────────
    # CLAVE MERGE
    # ─────────────────────────────────────────────
    def norm(x):
        return str(x).lower().strip()

    df_usuario_track["key"] = (
        df_usuario_track["nombre_cancion"].apply(norm)
        + "||"
        + df_usuario_track["nombre_artista"].apply(norm)
    )

    df_generos["key"] = (
        df_generos["nombre_cancion"].apply(norm)
        + "||"
        + df_generos["nombre_artista"].apply(norm)
    )

    df = df_usuario_track.merge(df_generos, on="key", how="left")

    # limpiar géneros
    df["genero"] = df["genero"].astype(str).str.replace("[","").str.replace("]","").str.replace("'","")

    # peso
    peso_col = "minutos_totales" if "minutos_totales" in df.columns else "num_reproducciones"

    genre_df = (
        df.groupby("genero")[peso_col]
        .sum()
        .reset_index()
        .rename(columns={peso_col:"peso"})
        .sort_values("peso", ascending=False)
    )

    # ─────────────────────────────────────────────
    # 1. IDENTIDAD MUSICAL
    # ─────────────────────────────────────────────
    top_genre = genre_df.iloc[0]

    st.markdown("## 🧬 Tu identidad musical")

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">Tu ADN sonoro</div>
        <div class="big-fact-title">🎧 {top_genre["genero"]}</div>
        <div class="big-fact-sub">
            Este género define tu año con <b>{int(top_genre["peso"]):,}</b> escuchas.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # 2. UNIVERSO + PODIO
    # ─────────────────────────────────────────────
    st.markdown("## 🎼 Tu universo de géneros")

    top = genre_df.head(5)

    first = top.iloc[0]
    second = top.iloc[1]
    third = top.iloc[2]
    others = top.iloc[3:5]

    # ─────────────────────────────────────────────
    # 🏆 PODIO REAL (STREAMLIT SAFE)
    # ─────────────────────────────────────────────
    col2, col1, col3 = st.columns([1, 1.2, 1])

    with col1:
        st.markdown(f"""
        <div class="genre-card" style="text-align:center; border:1px solid #1DB954;">
            <div style="color:#1DB954; font-weight:900;">👑 1º lugar</div>
            <div style="font-size:18px; font-weight:900; color:white; margin-top:8px;">
                {first["genero"]}
            </div>
            <div style="color:#B3B3B3; margin-top:6px;">
                🎧 {int(first["peso"]):,}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="genre-card" style="text-align:center;">
            <div style="color:#C0C0C0; font-weight:900;">🥈 2º lugar</div>
            <div style="font-size:16px; font-weight:900; color:white; margin-top:8px;">
                {second["genero"]}
            </div>
            <div style="color:#B3B3B3; margin-top:6px;">
                🎧 {int(second["peso"]):,}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="genre-card" style="text-align:center;">
            <div style="color:#CD7F32; font-weight:900;">🥉 3º lugar</div>
            <div style="font-size:16px; font-weight:900; color:white; margin-top:8px;">
                {third["genero"]}
            </div>
            <div style="color:#B3B3B3; margin-top:6px;">
                🎧 {int(third["peso"]):,}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # 3. GÉNERO SORPRESA
    # ─────────────────────────────────────────────
    st.markdown("## 🎲 Tu género sorpresa")

    surprise_pool = genre_df.iloc[3:10]
    surprise = surprise_pool.sample(1).iloc[0]

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">No te lo esperabas</div>
        <div class="big-fact-title">✨ {surprise["genero"]}</div>
        <div class="big-fact-sub">
            Aparece más de lo que crees: <b>{int(surprise["peso"]):,}</b> escuchas
        </div>
    </div>
    """, unsafe_allow_html=True)


    # ─────────────────────────────────────────────
    # 5. RADAR
    # ─────────────────────────────────────────────
    st.markdown("## 🎯 Tu perfil musical")

    st.markdown("""
    <div class="section-sub">
    Este gráfico resume cómo suena tu música.  
    Cuanto más se acerca un punto al borde, más presente está esa característica en lo que escuchas.
    </div>
    """, unsafe_allow_html=True)

    cols = ["energia","valencia","danceability","instrumentalidad","intensidad"]
    available = [c for c in cols if c in df.columns]

    if len(available) >= 3:
        radar = df[available].mean().reset_index()
        radar.columns = ["feature","value"]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatterpolar(
            r=radar["value"],
            theta=radar["feature"],
            fill="toself"
        ))

        fig2.update_layout(
            paper_bgcolor="#0a0a0a",
            font_color="white"
        )

        st.plotly_chart(fig2, use_container_width=True)


    # ─────────────────────────────────────────────
    # 6. ESTACIONES (VISUAL)
    # ─────────────────────────────────────────────
    st.markdown("## 🌦️ Tu año por estaciones")

    st.markdown("""
    <div class="section-sub">
    Tu música cambia con el tiempo: cada estación tiene su propio sonido.
    </div>
    """, unsafe_allow_html=True)

    # simulación simple (si no tienes fechas aún)
    estaciones = {
        "🌸 Primavera": "Pop, indie, sonidos suaves",
        "☀️ Verano": "Reggaeton, urbano, hits",
        "🍂 Otoño": "Rock, indie melancólico",
        "❄️ Invierno": "Baladas, acústico, chill"
    }

    col1, col2 = st.columns(2)

    items = list(estaciones.items())

    with col1:
        for k, v in items[:2]:
            st.markdown(f"""
            <div class="genre-card">
                <div class="genre-name">{k}</div>
                <div style="color:#B3B3B3; margin-top:6px; font-size:0.85rem;">
                    {v}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        for k, v in items[2:]:
            st.markdown(f"""
            <div class="genre-card">
                <div class="genre-name">{k}</div>
                <div style="color:#B3B3B3; margin-top:6px; font-size:0.85rem;">
                    {v}
                </div>
            </div>
            """, unsafe_allow_html=True)