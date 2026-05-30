import streamlit as st
import pandas as pd

def safe(v, default=0):
    return default if pd.isna(v) else v

def safe_col(df, *cols):
    for c in cols:
        if c in df.columns:
            return c
    return None

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
    margin-bottom:18px;
}

.podium-card{
    background:#111111;
    border:1px solid #1f1f1f;
    border-radius:22px;
    padding:20px 18px;
    text-align:center;
}

.podium-card.gold{ border-color:#d4af37; }
.podium-card.silver{ border-color:#bfc7d5; }
.podium-card.bronze{ border-color:#cd7f32; }

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

.podium-artist{
    color:#B3B3B3;
    margin-top:6px;
    font-size:0.85rem;
}

.podium-reps{
    color:#1DB954;
    font-size:1.4rem;
    font-weight:900;
    margin-top:14px;
}

.track-card{
    background:#111111;
    border-radius:18px;
    padding:18px 20px;
    border:1px solid #1f1f1f;
    margin-bottom:12px;
    transition:0.2s;
}

.track-card:hover{
    border-color:#1DB954;
    transform:translateY(-2px);
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
</style>
"""
# Función render principal

def render_canciones_wrapped(df_tracks, df_escuchas):

    st.markdown(_CSS, unsafe_allow_html=True)

    if df_tracks is None or df_tracks.empty:
        st.warning("No hay datos de canciones.")
        return

    col_name = safe_col(df_tracks, "nombre_cancion", "nombre_track")
    col_artist = safe_col(df_tracks, "nombre_artista")
    col_reps = safe_col(df_tracks, "reproducciones_totales")
    col_score = safe_col(df_tracks, "score_medio")
    col_skip = safe_col(df_tracks, "pct_saltada")

    if col_name is None or col_reps is None:
        st.error("Faltan columnas necesarias.")
        return

    st.header("🎧 Canciones")
    st.subheader("🔥 Top canciones")

    top = df_tracks.sort_values(col_reps, ascending=False).head(10).copy()
    top[col_reps] = top[col_reps].fillna(0)
    max_reps = float(top[col_reps].max()) if len(top) else 1

    top3 = top.head(3)
    rest = top.iloc[3:6]

    podium_html = '<div class="podium-wrap">'
    podium_classes = ["silver", "gold", "bronze"]

    for i, (_, row) in enumerate(top3.iterrows(), 1):
        nombre = str(row.get(col_name, "Sin nombre"))
        artista = str(row.get(col_artist, "Desconocido"))
        reps = int(safe(row.get(col_reps, 0)))
        cls = podium_classes[i - 1]
        podium_html += f"""
        <div class="podium-card {cls}">
            <div class="podium-rank">Top #{i}</div>
            <div class="podium-name">{nombre}</div>
            <div class="podium-artist">{artista}</div>
            <div class="podium-reps">🎧 {reps:,}</div>
        </div>
        """
    podium_html += "</div>"
    st.html(podium_html)

    st.subheader("📋 Del 4 al 6")

    list_html = ""
    for i, (_, row) in enumerate(rest.iterrows(), 4):
        nombre = str(row.get(col_name, "Sin nombre"))
        artista = str(row.get(col_artist, "Desconocido"))
        reps = int(safe(row.get(col_reps, 0)))
        pct = (reps / max_reps * 100) if max_reps else 0

        list_html += f"""
        <div class="track-card">
            <div class="track-top">
                <div>
                    <div class="track-name">#{i} · {nombre}</div>
                    <div class="track-sub">{artista}</div>
                </div>
                <div class="track-rank">🎧 {reps:,}</div>
            </div>
            <div style="margin-top:10px;height:6px;background:#1f1f1f;border-radius:999px;overflow:hidden;">
                <div style="width:{pct:.1f}%;height:100%;background:#1DB954;border-radius:999px;"></div>
            </div>
        </div>
        """
    st.html(list_html)

    st.subheader("⭐ Canción del momento")

    if col_score and col_score in df_tracks.columns and not df_tracks[col_score].isna().all():
        best = df_tracks.sort_values(col_score, ascending=False).iloc[0]
    else:
        best = df_tracks.sort_values(col_reps, ascending=False).iloc[0]

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">Tu hit del año</div>
        <div class="big-fact-title">{best.get(col_name, "Sin nombre")}</div>
        <div class="big-fact-sub">🎧 Tu canción más especial</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("⚠️ Guilty pleasure")

    if col_skip and col_skip in df_tracks.columns and not df_tracks[col_skip].isna().all():
        guilty = df_tracks.sort_values(col_skip, ascending=False).iloc[0]
    else:
        guilty = df_tracks.sort_values(col_reps, ascending=False).iloc[-1]

    st.markdown(f"""
    <div class="big-fact">
        <div class="big-fact-kicker">No te juzgamos 😏</div>
        <div class="big-fact-title">{guilty.get(col_name, "Sin nombre")}</div>
        <div class="big-fact-sub">⏭️ Muy saltada pero recurrente</div>
    </div>
    """, unsafe_allow_html=True)