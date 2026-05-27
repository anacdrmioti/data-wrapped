"""
TIPOS DE OYENTE — SISTEMA DE CLASIFICACIÓN

Este sistema:
1. Une df_tracks con df_generos
2. Calcula el perfil musical del usuario
3. Compara ese perfil con distintos prototipos
4. Devuelve el TOP 3 de tipos de oyente
   con probabilidad (%) usando reproducciones reales
"""

import pandas as pd
import numpy as np
import streamlit as st


# =========================================================
# FEATURES
# =========================================================

FEATURES = [
    "energia",
    "valencia",
    "danceability",
    "instrumentalidad",
    "intensidad"
]


# =========================================================
# TIPOS DE OYENTE
# =========================================================

TIPOS_OYENTE = {

    "gym_beast": {
        "nombre": "🔥 Gym Beast",
        "descripcion": "Trap, gym, energía máxima y motivación constante.",
        "energia": 0.95,
        "valencia": 0.6,
        "danceability": 0.95,
        "instrumentalidad": 0.1,
        "intensidad": 0.95,
    },

    "cora_blandito": {
        "nombre": "💔 Cora Blandito",
        "descripcion": "Música emocional, melancólica y romántica.",
        "energia": 0.3,
        "valencia": 0.3,
        "danceability": 0.2,
        "instrumentalidad": 0.5,
        "intensidad": 0.5,
    },

    "rey_fiesta": {
        "nombre": "🎉 Rey de la Fiesta",
        "descripcion": "Hits virales, reggaetón y fiesta constante.",
        "energia": 0.95,
        "valencia": 0.9,
        "danceability": 0.95,
        "instrumentalidad": 0.1,
        "intensidad": 0.9,
    },

    "chill_master": {
        "nombre": "🧘 Chill Master",
        "descripcion": "Relax, lo-fi y música tranquila.",
        "energia": 0.2,
        "valencia": 0.5,
        "danceability": 0.3,
        "instrumentalidad": 0.95,
        "intensidad": 0.2,
    },

    "explorador_global": {
        "nombre": "🌍 Explorador Global",
        "descripcion": "Muchos géneros, artistas e idiomas distintos.",
        "energia": 0.55,
        "valencia": 0.55,
        "danceability": 0.55,
        "instrumentalidad": 0.55,
        "intensidad": 0.55,
    },

    "nostalgico": {
        "nombre": "📼 Nostálgico",
        "descripcion": "Canciones emocionales y recuerdos musicales.",
        "energia": 0.4,
        "valencia": 0.3,
        "danceability": 0.4,
        "instrumentalidad": 0.6,
        "intensidad": 0.4,
    },

    "hyperactivo": {
        "nombre": "⚡ Hyperactivo Musical",
        "descripcion": "Muchísima variedad y cambios constantes.",
        "energia": 0.9,
        "valencia": 0.7,
        "danceability": 0.85,
        "instrumentalidad": 0.2,
        "intensidad": 0.95,
    },

    "fan_artista": {
        "nombre": "⭐ Fan de Artista",
        "descripcion": "Escucha intensiva de pocos artistas favoritos.",
        "energia": 0.5,
        "valencia": 0.5,
        "danceability": 0.5,
        "instrumentalidad": 0.5,
        "intensidad": 0.5,
    }
}


# =========================================================
# MERGE TRACKS + FEATURES
# =========================================================

df_generos = pd.read_csv("data/canciones_clasificadas.csv")

def preparar_dataset(df_tracks, df_generos):

    df = df_tracks.merge(
        df_generos,
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    return df


# =========================================================
# PERFIL DEL USUARIO
# =========================================================

def calcular_perfil_usuario(df):

    perfil = {}

    # =====================================================
    # PESOS SEGÚN REPRODUCCIONES
    # =====================================================

    pesos = df["reproducciones_totales"].fillna(1)

    # =====================================================
    # FEATURES PONDERADAS
    # =====================================================

    for f in FEATURES:

        perfil[f] = np.average(
            df[f].fillna(df[f].mean()),
            weights=pesos
        )

    # =====================================================
    # DIVERSIDAD DE GÉNEROS
    # =====================================================

    perfil["n_generos"] = (
        df["genero"]
        .astype(str)
        .nunique()
    )

    # =====================================================
    # ARTISTA DOMINANTE
    # =====================================================

    top_artist_ratio = (
        df["nombre_artista"]
        .value_counts(normalize=True)
        .iloc[0]
    )

    perfil["top_artist_ratio"] = top_artist_ratio

    # =====================================================
    # SKIPS
    # =====================================================

    if "pct_saltada" in df.columns:

        perfil["skip_rate"] = df["pct_saltada"].mean()

    else:

        perfil["skip_rate"] = 0

    return perfil


# =========================================================
# SCORE NUMÉRICO
# =========================================================

def score_numerico(usuario, tipo):

    score = 0

    for f in FEATURES:

        diff = abs(usuario[f] - tipo[f])

        score += (1 - diff)

    return score / len(FEATURES)


# =========================================================
# BONUS
# =========================================================

def calcular_bonus(nombre_tipo, perfil):

    bonus = 0

    # explorador global
    if nombre_tipo == "explorador_global":

        bonus += perfil["n_generos"] * 0.02

    # fan de artista
    if nombre_tipo == "fan_artista":

        bonus += perfil["top_artist_ratio"] * 0.5

    # hyperactivo musical
    if nombre_tipo == "hyperactivo":

        bonus += perfil["skip_rate"] * 0.4

    return bonus


# =========================================================
# CALCULAR TOP TIPOS
# =========================================================

def calcular_tipos_oyente(df):

    perfil = calcular_perfil_usuario(df)

    resultados = []

    for key, tipo in TIPOS_OYENTE.items():

        score = (
            score_numerico(perfil, tipo)
            + calcular_bonus(key, perfil)
        )

        resultados.append({
            "tipo": tipo["nombre"],
            "descripcion": tipo["descripcion"],
            "score": score
        })

    # ordenar
    resultados = sorted(
        resultados,
        key=lambda x: x["score"],
        reverse=True
    )

    # top 3
    top3 = resultados[:3]

    # =====================================================
    # NORMALIZAR A %
    # =====================================================

    total = sum(x["score"] for x in top3)

    for x in top3:

        x["probabilidad"] = round(
            (x["score"] / total) * 100,
            2
        )

    return top3


# =========================================================
# STREAMLIT
# =========================================================

def render_tipos_oyente(df_tracks):

    df_generos = pd.read_csv("data/canciones_clasificadas.csv")
    st.markdown("## 🎧 Tu Tipo de Oyente")

    # merge
    df = preparar_dataset(df_tracks,df_generos)

    # calcular top 3
    top3 = calcular_tipos_oyente(df)

    for t in top3:
        st.markdown(f"""
        <div style="
            background:rgba(255,255,255,0.04);
            padding:16px;
            border-radius:14px;
            margin-bottom:12px;
            border:1px solid rgba(255,255,255,0.08);
        ">
            <div style="font-weight:900; color:#1DB954;">
                {t['tipo']} — {t['probabilidad']:.2f}%
            </div>
            <div style="color:#ccc; margin-top:6px;">
                {t['descripcion']}
            </div>
        </div>
        """, unsafe_allow_html=True)

