import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Paleta 
GREEN = "#1DB954"
BLACK = "#0a0a0a"
CARD_BG = "#111111"
LIGHT_GRAY = "#B3B3B3"
WHITE = "#FFFFFF"
GOLD = "#FFD166"
SILVER = "#C0C0C0"
BRONZE = "#CD7F32"

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Sep.", 10: "Oct.", 11: "Nov.", 12: "Dic."
}

# CSS
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
}

.podium-wrap{
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:14px;
    margin:20px 0 10px 0;
}

.podium-card{
    background:#111111;
    border-radius:22px;
    padding:20px 18px;
    border:1px solid #1f1f1f;
    text-align:center;
    transition:0.2s;
}

.podium-card:hover{
    border-color:#1DB954;
    transform:translateY(-2px);
}

.podium-card.gold{ border-color:#FFD166; }
.podium-card.silver{ border-color:#C0C0C0; }
.podium-card.bronze{ border-color:#CD7F32; }

.podium-rank{
    color:#1DB954;
    font-size:0.75rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:1px;
}

.podium-name{
    color:white;
    font-size:1.25rem;
    font-weight:900;
    margin-top:10px;
}

.podium-mins{
    color:#1DB954;
    font-size:1.05rem;
    font-weight:900;
    margin-top:12px;
}

.podium-repro{
    color:#B3B3B3;
    margin-top:4px;
    font-size:0.82rem;
}

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

.obsesion-card{
    background:#111111;
    border-radius:18px;
    border:1px solid #1f1f1f;
    padding:18px;
    text-align:center;
    height:100%;
}

.obsesion-mes{
    color:#1DB954;
    font-size:0.72rem;
    text-transform:uppercase;
    letter-spacing:1px;
    font-weight:700;
    margin-bottom:8px;
}

.obsesion-name{
    color:white;
    font-size:1.1rem;
    font-weight:900;
    margin-top:6px;
}

.obsesion-mins{
    color:#B3B3B3;
    font-size:0.85rem;
    margin-top:6px;
}
</style>
"""

# Auxiliares
def safe(v, default=0):
    return default if pd.isna(v) else v

def safe_col(df, *cols):
    for c in cols:
        if c in df.columns:
            return c
    return None

# Funciones de wrapped artistas
def _top_artistas(df_artistas: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if df_artistas is None or df_artistas.empty:
        return pd.DataFrame()
    mins_col = safe_col(df_artistas, "minutos_totales")
    reps_col = safe_col(df_artistas, "reproducciones_totales")
    if mins_col is None or reps_col is None:
        return df_artistas.head(n).reset_index(drop=True) if df_artistas is not None else pd.DataFrame()
    return (
        df_artistas
        .sort_values([mins_col, reps_col], ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

def _artista_sin_skips(df_escuchas: pd.DataFrame, min_repros: int = 3):
    """
    Artista con el menor porcentaje de skips (idealmente 0%).
    Esto significa que cuando escuchas sus canciones, NUNCA las saltas.
    """
    if df_escuchas is None or df_escuchas.empty:
        return None
    
    # Porque me ha dado error en algunas personas que tienen la misma columna nombrada de diferente forma:
    saltada_col = None
    if "saltada" in df_escuchas.columns:
        saltada_col = "saltada"
    elif "pct_saltada" in df_escuchas.columns:
        saltada_col = "pct_saltada"
    else:
        return None
    
    needed = {"artista_clave", "nombre_artista", "escucha_id"}
    if not needed.issubset(df_escuchas.columns):
        return None
    
    df = (
        df_escuchas
        .groupby(["artista_clave", "nombre_artista"])
        .agg(
            reproducciones=("escucha_id", "count"),
            pct_skip=(saltada_col, "mean"),
        )
        .reset_index()
    )
    
    df = df[df["reproducciones"] >= min_repros]
    if df.empty:
        return None
    
    # El artista con menor porcentaje de skips
    return df.sort_values("pct_skip", ascending=True).iloc[0]

def _descubrimiento_por_mes(df_escuchas: pd.DataFrame) -> pd.DataFrame:
    if df_escuchas is None or df_escuchas.empty:
        return pd.DataFrame()
    needed = {"artista_clave", "nombre_artista", "fecha"}
    if not needed.issubset(df_escuchas.columns):
        return pd.DataFrame()
    df = df_escuchas.sort_values("fecha").copy()
    primera = (
        df.groupby(["artista_clave", "nombre_artista"])
        .agg(primera_escucha=("fecha", "min"))
        .reset_index()
    )
    primera["mes_desc"] = pd.to_datetime(primera["primera_escucha"]).dt.to_period("M").astype(str)
    agr = (
        primera.groupby("mes_desc")
        .agg(nuevos=("artista_clave", "count"))
        .reset_index()
    )
    return agr.sort_values("mes_desc")

# Función Render principal
def render_artistas_wrapped(df_artistas: pd.DataFrame, df_escuchas: pd.DataFrame) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    top10 = _top_artistas(df_artistas, 5)
    if top10.empty:
        st.info("No hay datos de artistas disponibles.")
        return

    mins_col = safe_col(top10, "minutos_totales")
    reps_col = safe_col(top10, "reproducciones_totales")
    name_col = safe_col(top10, "nombre_artista")

    if mins_col is None or name_col is None:
        st.error("Faltan columnas necesarias en df_artistas.")
        return

    st.subheader("👑 Top artista")

    top1 = top10.iloc[0]
    horas = safe(top1.get(mins_col, 0)) / 60
    reps = int(safe(top1.get(reps_col, 0)))

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">Tu #1 absoluto</div>
        <div class="big-fact-title">{top1.get(name_col, "Desconocido")}</div>
        <div class="big-fact-sub">
            🎧 {reps:,} reproducciones · ⏱ {horas:.0f} horas escuchadas
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🏆 Tu podio")

    podium_html = '<div class="podium-wrap">'
    podium_classes = ["silver", "gold", "bronze"]
    emojis = ["🥈", "🥇", "🥉"]

    for i in range(min(3, len(top10))):
        artista = top10.iloc[i]
        nombre = str(artista.get(name_col, "Desconocido"))
        mins = safe(artista.get(mins_col, 0))
        reps_i = int(safe(artista.get(reps_col, 0)))
        cls = podium_classes[i]
        emoji = emojis[i]
        podium_html += f"""
        <div class="podium-card {cls}">
            <div class="podium-rank">Top #{i+1}</div>
            <div class="podium-name">{emoji} {nombre}</div>
            <div class="podium-mins">{mins:,.0f} min</div>
            <div class="podium-repro">🎧 {reps_i:,} reproducciones</div>
        </div>
        """
    podium_html += "</div>"
    st.html(podium_html)

    st.subheader("🎧 Tus artistas más escuchados")

    list_html = ""
    for i, (_, row) in enumerate(top10.iterrows(), 1):
        nombre = str(row.get(name_col, "Desconocido"))
        mins = safe(row.get(mins_col, 0))
        reps_i = int(safe(row.get(reps_col, 0)))
        list_html += f"""
        <div class="banner-card">
            <div class="banner-kicker">Top #{i}</div>
            <div class="banner-title">{nombre}</div>
            <div class="banner-sub">{mins:,.0f} minutos · 🎧 {reps_i:,} reproducciones</div>
        </div>
        """
    st.html(list_html)

    st.subheader("💚 Tu artista más fiel (sin skips)")

    fiel = _artista_sin_skips(df_escuchas)
    if fiel is not None:
        pct_skip = fiel["pct_skip"] * 100 if "pct_skip" in fiel else 0
        st.markdown(f"""
        <div class="big-fact">
            <div class="big-fact-kicker">El que nunca saltas</div>
            <div class="big-fact-title">{fiel['nombre_artista']}</div>
            <div class="big-fact-sub">
                🎧 {int(fiel['reproducciones']):,} reproducciones · 
                ⏭️ Solo {pct_skip:.1f}% skipeado (¡casi nunca lo saltas!)
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No hay datos suficientes para calcular tu artista más fiel.")

    st.subheader("🆕 Nuevos artistas descubiertos")

    desc = _descubrimiento_por_mes(df_escuchas)
    if not desc.empty:
        mejor_mes = desc.loc[desc["nuevos"].idxmax()]
        c1, c2 = st.columns(2)
        with c1:
            st.metric("📅 Mes más explorador", str(mejor_mes["mes_desc"]))
        with c2:
            st.metric("🎵 Nuevos artistas", int(mejor_mes["nuevos"]))

        fig_desc = go.Figure(go.Bar(
            x=desc["mes_desc"],
            y=desc["nuevos"],
            marker_color=GREEN
        ))
        fig_desc.update_layout(
            paper_bgcolor=BLACK,
            plot_bgcolor=CARD_BG,
            font=dict(color=WHITE),
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Mes",
            yaxis_title="Artistas nuevos",
        )
        st.plotly_chart(fig_desc, use_container_width=True)

    if df_escuchas is not None and not df_escuchas.empty and {"mes", "nombre_artista", "minutos_reproducidos"}.issubset(df_escuchas.columns):
        st.subheader("📀 Tu obsesión según el mes")

        obsesion_mes = (
            df_escuchas
            .groupby(["mes", "nombre_artista"])
            .agg(minutos=("minutos_reproducidos", "sum"))
            .reset_index()
        )
        obsesion_mes = (
            obsesion_mes.sort_values(["mes", "minutos"], ascending=[True, False])
            .groupby("mes")
            .head(1)
            .reset_index(drop=True)
        )
        obsesion_mes["mes_nombre"] = obsesion_mes["mes"].map(MESES_ES)

        obsesion_html = '<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-top:18px;">'
        for _, row in obsesion_mes.iterrows():
            mes_nombre = row["mes_nombre"]
            nombre_artista = row["nombre_artista"]
            mins = row["minutos"]
            obsesion_html += f"""
            <div class="obsesion-card">
                <div class="obsesion-mes">{mes_nombre}</div>
                <div class="obsesion-name">{nombre_artista}</div>
                <div class="obsesion-mins">{mins:,.0f} minutos</div>
            </div>
            """
        obsesion_html += "</div>"
        st.html(obsesion_html)