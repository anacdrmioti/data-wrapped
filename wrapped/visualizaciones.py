import streamlit as st
import pandas as pd

def visualizacion_artistas(df_artistas: pd.DataFrame):

    st.markdown("## 🎤 Visualización de Artistas")

    # ─────────────────────────────
    # 📊 MÉTRICAS GENERALES
    # ─────────────────────────────
    total_artistas = df_artistas["artista_clave"].nunique()
    total_minutos = df_artistas["minutos_totales"].sum()
    total_tracks = df_artistas["tracks_unicos"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("🎤 Artistas", total_artistas)
    col2.metric("⏱ Minutos totales", f"{total_minutos:,.0f}")
    col3.metric("🎵 Tracks únicos", total_tracks)

    st.divider()

    # ─────────────────────────────
    # 🏆 TOP ARTISTAS (POR MINUTOS)
    # ─────────────────────────────
    st.subheader("🏆 Top artistas por minutos escuchados")

    top_minutos = df_artistas.sort_values(
        "minutos_totales",
        ascending=False
    ).head(10)

    st.dataframe(
        top_minutos[
            ["nombre_artista", "minutos_totales", "reproducciones_totales"]
        ],
        use_container_width=True
    )

    # ─────────────────────────────
    # 🎵 ARTISTAS MÁS ESCUCHADOS
    # ─────────────────────────────
    st.subheader("🎧 Top artistas por reproducciones")

    top_reproducciones = df_artistas.sort_values(
        "reproducciones_totales",
        ascending=False
    ).head(10)

    st.dataframe(
        top_reproducciones[
            ["nombre_artista", "reproducciones_totales", "minutos_totales"]
        ],
        use_container_width=True
    )

    # ─────────────────────────────
    # 🎶 ARTISTAS MÁS VARIADOS
    # ─────────────────────────────
    st.subheader("🎶 Artistas con más variedad de canciones")

    top_variedad = df_artistas.sort_values(
        "tracks_unicos",
        ascending=False
    ).head(10)

    st.dataframe(
        top_variedad[
            ["nombre_artista", "tracks_unicos", "reproducciones_totales"]
        ],
        use_container_width=True
    )

    # ─────────────────────────────
    # 🧠 SCORE (afinidad)
    # ─────────────────────────────
    if "score_medio" in df_artistas.columns:

        st.subheader("🔥 Artistas con mayor afinidad (score medio)")

        top_score = df_artistas.sort_values(
            "score_medio",
            ascending=False
        ).head(10)

        st.dataframe(
            top_score[
                ["nombre_artista", "score_medio", "minutos_totales"]
            ],
            use_container_width=True
        )

    # ─────────────────────────────
    # 📅 TIEMPO DE RELACIÓN CON ARTISTAS
    # ─────────────────────────────
    st.subheader("📅 Historial de escucha")

    historial = df_artistas.copy()
    historial["dias_activos"] = (
        pd.to_datetime(historial["ultima_escucha"]) -
        pd.to_datetime(historial["primera_escucha"])
    ).dt.days

    st.dataframe(
        historial[
            ["nombre_artista", "primera_escucha", "ultima_escucha", "dias_activos"]
        ].sort_values("dias_activos", ascending=False),
        use_container_width=True
    )

    # ─────────────────────────────
    # 📈 GRÁFICO SIMPLE
    # ─────────────────────────────
    st.subheader("📊 Minutos por artista (Top 10)")

    chart = df_artistas.sort_values("minutos_totales", ascending=False).head(10)
    st.bar_chart(chart.set_index("nombre_artista")["minutos_totales"])