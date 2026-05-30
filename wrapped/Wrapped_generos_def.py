import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# CSS
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

# Función Render principal

def render_generos_wrapped(df_usuario_track, df_escuchas):

    st.markdown(_CSS, unsafe_allow_html=True)

    if df_usuario_track is None or df_usuario_track.empty:
        st.warning("No hay datos")
        return

    # Cargamos los datos de las canciones clasificadas por la API
    df_generos = pd.read_csv("data/canciones_clasificadas.csv")

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

    # 1. Identidad musical
    top_genre = genre_df.iloc[0]

    st.markdown("## 🧬 Tu identidad musical")

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">Tu ADN sonoro</div>
        <div class="big-fact-title">🎧 {top_genre["genero"]}</div>
        <div class="big-fact-sub">
            Este género te define con <b>{int(top_genre["peso"]):,}</b> escuchas.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Universo y podio 
    st.markdown("## 🎼 Tu universo de géneros")

    top = genre_df.head(5)

    first = top.iloc[0]
    second = top.iloc[1]
    third = top.iloc[2]
    others = top.iloc[3:5]

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

    # 3. Género sorpresa 
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


    # 4. Radar

    st.markdown("## 🎯 Tu perfil musical")

    # Voy a poner una breve explicación de cómo leer el gráfico, ya que tiene que ser fácil de interpretar para
        # cualquier persona
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


    # 6. Estaciones musicales

    st.markdown("## 🌦️ Tus estaciones musicales")

    st.markdown("""
    <div class="section-sub">
    Cada estación tiene un sonido distinto en tu historial.
    Este fue tu género dominante en cada época del año.
    </div>
    """, unsafe_allow_html=True)

    # merge de la tabla escuchas con la de clasificadas géneros
    df_estaciones = df_escuchas.merge(
        df_generos,
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    df_estaciones["fecha"] = pd.to_datetime(df_estaciones["fecha"], errors="coerce")

    def obtener_estacion(mes):
        if mes in [12, 1, 2]:
            return "Invierno"
        elif mes in [3, 4, 5]:
            return "Primavera"
        elif mes in [6, 7, 8]:
            return "Verano"
        else:
            return "Otoño"

    df_estaciones["mes"] = df_estaciones["fecha"].dt.month
    df_estaciones["estacion"] = df_estaciones["mes"].apply(obtener_estacion)

    # limpiar nulos
    df_estaciones = df_estaciones.dropna(
        subset=["estacion", "genero"]
    )

    # Peso
    peso_col = "minutos_reproducidos"

    # Top de género para las estaciones

    ranking = (
        df_estaciones
        .groupby(["estacion", "genero"])[peso_col]
        .sum()
        .reset_index()
    )

    idx = ranking.groupby("estacion")[peso_col].idxmax()

    top_estaciones = ranking.loc[idx]

    # Descripciones y emojis para cada estación 

    descripciones = {
        "Primavera": "Tu época más fresca y equilibrada.",
        "Verano": "Aquí aparece tu lado más energético.",
        "Otoño": "Momentos más emocionales y nostálgicos.",
        "Invierno": "Tu versión más introspectiva y chill."
    }

    emojis = {
        "Primavera": "🌸",
        "Verano": "☀️",
        "Otoño": "🍂",
        "Invierno": "❄️"
    }

    import streamlit.components.v1 as components


    col1, col2 = st.columns(2)

    cards = top_estaciones.to_dict("records")

    for i, row in enumerate(cards):

        estacion = row["estacion"]

        card_html = f"""
        <div style="
            background: rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            padding:18px;
            border-radius:18px;
            margin-bottom:14px;
            color:white;
            font-family: Arial;
        ">

            <div style="
                font-size:22px;
                font-weight:900;
                color:#1DB954;
            ">
                {emojis.get(estacion, "🎵")} {estacion}
            </div>

            <div style="
                font-size:20px;
                font-weight:800;
                margin-top:10px;
                color:white;
            ">
                🎧 {row["genero"]}
            </div>

            <div style="
                color:#B3B3B3;
                margin-top:8px;
            ">
                {int(row[peso_col]):,} minutos escuchados
            </div>

            <div style="
                margin-top:10px;
                color:#cfcfcf;
                line-height:1.5;
            ">
                {descripciones.get(estacion, "")}
            </div>

        </div>
        """

        if i < 2:
            components.html(card_html, scrolling = False, height=180)
        else:
            components.html(card_html, scrolling = False, height=180)