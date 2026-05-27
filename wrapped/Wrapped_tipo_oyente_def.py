"""
TIPO DE OYENTE – SISTEMA DE CLASIFICACIÓN PERSONALIZADA

Este módulo implementa un sistema de clasificación del usuario en distintos
“perfiles de oyente” musicales basados en su comportamiento de escucha.

El objetivo es transformar el historial de reproducción (df_tracks) en un
perfil agregado del usuario y compararlo con prototipos de oyentes definidos
manualmente (TIPOS_OYENTE).

──────────────────────────────────────────────
1. CONSTRUCCIÓN DEL PERFIL DEL USUARIO
──────────────────────────────────────────────
Se calcula un perfil simplificado a partir del dataset:
- Se utilizan variables proxy (como reproducciones_totales) para estimar energía.
- Otras dimensiones emocionales (valencia, danceability, instrumentalidad,
  intensidad) se fijan de forma heurística cuando no están disponibles en el dataset.
- Se extrae información agregada:
    • Distribución de artistas (artista dominante)
    • Diversidad de géneros (si está disponible)

──────────────────────────────────────────────
2. TIPOS DE OYENTE (PROTOTIPOS)
──────────────────────────────────────────────
Se definen varios perfiles musicales teóricos como vectores de características:
- Ej: “El Gym Beast”, “El Chill Master”, “El Explorador Global”, etc.
Cada uno incluye:
    • Rasgos numéricos (energía, valencia, etc.)
    • Preferencias de mood y contexto
    • Descripción interpretativa del perfil

──────────────────────────────────────────────
3. SISTEMA DE SIMILITUD
──────────────────────────────────────────────
Se calcula un score de similitud entre el usuario y cada perfil:
- score_numerico: compara distancia entre vectores de características
- score_categorico: ampliable (actualmente no utilizado)
- bonus: añade incentivos según diversidad o patrones específicos

──────────────────────────────────────────────
4. RESULTADO FINAL
──────────────────────────────────────────────
- Se ordenan los perfiles por score descendente
- Se selecciona el TOP 3 de tipos de oyente
- Se normalizan los resultados para obtener porcentajes interpretables

El resultado final permite mostrar al usuario un “arquetipo musical”
que describe su comportamiento de escucha de forma visual y narrativa.
"""



import pandas as pd
from collections import Counter


FEATURES = [
    "energia",
    "valencia",
    "danceability",
    "instrumentalidad",
    "intensidad"
]


TIPOS_OYENTE = {

    "cora_blandito": {
        "nombre": "💔 Cora Blandito",
        "descripcion": "Escucha música emocional, romántica y melancólica.",
        "energia": 0.3,
        "valencia": 0.3,
        "danceability": 0.2,
        "instrumentalidad": 0.4,
        "intensidad": 0.5,
        "moods": ["triste", "melancolico", "amoroso"],
        "contextos": ["casa", "relax", "romance"]
    },

    "gym_beast": {
        "nombre": "🔥 Gym Beast",
        "descripcion": "Alta energía, reggaetón duro, trap y beats agresivos.",
        "energia": 0.95,
        "valencia": 0.6,
        "danceability": 0.95,
        "instrumentalidad": 0.1,
        "intensidad": 0.95,
        "moods": ["energico", "motivador"],
        "contextos": ["gym", "entrenar", "fiesta"]
    },

    "conductor_nocturno": {
        "nombre": "🌃 Conductor Nocturno",
        "descripcion": "Música para la noche, coche y ambiente urbano.",
        "energia": 0.5,
        "valencia": 0.4,
        "danceability": 0.5,
        "instrumentalidad": 0.5,
        "intensidad": 0.4,
        "moods": ["relajado", "melancolico"],
        "contextos": ["coche", "noche", "viajar"]
    },

    "drama_queen_king": {
        "nombre": "🎭 Drama Queen / King",
        "descripcion": "Intensidad emocional alta, amor y desamor extremo.",
        "energia": 0.6,
        "valencia": 0.2,
        "danceability": 0.4,
        "instrumentalidad": 0.3,
        "intensidad": 0.95,
        "moods": ["triste", "amoroso", "melancolico"],
        "contextos": ["romance", "casa"]
    },

    "buen_rollo": {
        "nombre": "☀️ Buen Rollo",
        "descripcion": "Pop alegre y música positiva.",
        "energia": 0.7,
        "valencia": 0.95,
        "danceability": 0.85,
        "instrumentalidad": 0.2,
        "intensidad": 0.6,
        "moods": ["feliz", "motivador"],
        "contextos": ["fiesta", "amigos", "playa"]
    },

    "lluvia_cafe": {
        "nombre": "🌧️ Lluvia y Café",
        "descripcion": "Indie, acústico y chill para estudiar o reflexionar.",
        "energia": 0.25,
        "valencia": 0.45,
        "danceability": 0.2,
        "instrumentalidad": 0.85,
        "intensidad": 0.3,
        "moods": ["relajado", "melancolico"],
        "contextos": ["casa", "estudiar", "relax"]
    },

    "rey_fiesta": {
        "nombre": "🎉 Rey de la Fiesta",
        "descripcion": "Reggaetón, electrónica y hits virales.",
        "energia": 0.95,
        "valencia": 0.85,
        "danceability": 0.95,
        "instrumentalidad": 0.1,
        "intensidad": 0.9,
        "moods": ["energico", "feliz"],
        "contextos": ["fiesta", "discoteca"]
    },

    "explorador_global": {
        "nombre": "🌍 Explorador Global",
        "descripcion": "Escucha muchos idiomas y géneros variados.",
        "energia": 0.55,
        "valencia": 0.55,
        "danceability": 0.55,
        "instrumentalidad": 0.55,
        "intensidad": 0.55,
        "moods": [],
        "contextos": []
    },

    "chill_master": {
        "nombre": "🧘 Chill Master",
        "descripcion": "Lo-fi, ambient y música relajada.",
        "energia": 0.2,
        "valencia": 0.5,
        "danceability": 0.3,
        "instrumentalidad": 0.95,
        "intensidad": 0.2,
        "moods": ["relajado"],
        "contextos": ["relax", "casa", "estudiar"]
    },

    "fan_artistas": {
        "nombre": "⭐ Fan de Artistas",
        "descripcion": "Escucha pocos artistas de forma muy intensiva.",
        "energia": 0.5,
        "valencia": 0.5,
        "danceability": 0.5,
        "instrumentalidad": 0.4,
        "intensidad": 0.6,
        "moods": [],
        "contextos": []
    },

    "hyperactivo_musical": {
        "nombre": "⚡ Hyperactivo Musical",
        "descripcion": "Muchos cambios, skips frecuentes y géneros muy variados.",
        "energia": 0.9,
        "valencia": 0.6,
        "danceability": 0.8,
        "instrumentalidad": 0.3,
        "intensidad": 0.9,
        "moods": ["energico", "impulsivo"],
        "contextos": ["cualquier"]
    },

    "nostalgico": {
        "nombre": "📼 Nostálgico",
        "descripcion": "Escucha música antigua o de etapas pasadas.",
        "energia": 0.4,
        "valencia": 0.3,
        "danceability": 0.4,
        "instrumentalidad": 0.6,
        "intensidad": 0.4,
        "moods": ["melancolico", "triste"],
        "contextos": ["recuerdos"]
    },

    "atmosferico": {
        "nombre": "🌌 Atmosférico",
        "descripcion": "Ambient, instrumental y música experimental.",
        "energia": 0.3,
        "valencia": 0.5,
        "danceability": 0.2,
        "instrumentalidad": 0.95,
        "intensidad": 0.4,
        "moods": ["relajado"],
        "contextos": ["concentracion", "relax"]
    }
}


# ─────────────────────────────────────────
# PERFIL USUARIO (adaptado a df_tracks)
# ─────────────────────────────────────────
def calcular_perfil_usuario(df):

    perfil = {}

    # 🔹 no tienes audio features → usamos proxies del DF
    perfil["energia"] = df["reproducciones_totales"].mean() / df["reproducciones_totales"].max()
    perfil["valencia"] = 0.5
    perfil["danceability"] = 0.5
    perfil["instrumentalidad"] = 0.5
    perfil["intensidad"] = 0.5

    # género (si existe en tu df posterior)
    if "genero" in df.columns:
        generos = df["genero"].value_counts().to_dict()
        perfil["generos"] = generos
        perfil["n_generos"] = len(generos)
    else:
        perfil["generos"] = {}
        perfil["n_generos"] = 0

    # artista dominante
    if "nombre_artista" in df.columns:
        top_artist_ratio = df["nombre_artista"].value_counts(normalize=True).iloc[0]
    else:
        top_artist_ratio = 0

    perfil["top_artist_ratio"] = top_artist_ratio

    return perfil


# ─────────────────────────────────────────
def score_numerico(usuario, objetivo):
    score = 0
    for f in FEATURES:
        diff = abs(usuario[f] - objetivo[f])
        score += (1 - diff)
    return score / len(FEATURES)


def score_categorico(usuario, objetivo):
    return 0


def bonus(nombre, usuario):
    if nombre == "explorador_global":
        return usuario.get("n_generos", 0) * 0.3
    return 0


# ─────────────────────────────────────────
def calcular_tipos_oyente(df):

    perfil = calcular_perfil_usuario(df)

    resultados = []

    for key, tipo in TIPOS_OYENTE.items():

        score = (
            score_numerico(perfil, tipo)
            + score_categorico(perfil, tipo)
            + bonus(key, perfil)
        )

        resultados.append({
            "key": key,
            "nombre": tipo["nombre"],
            "descripcion": tipo["descripcion"],
            "score": score
        })

    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)

    top3 = resultados[:3]

    total = sum(x["score"] for x in top3) or 1

    for x in top3:
        x["porcentaje"] = round(x["score"] / total * 100, 1)

    return top3


# ─────────────────────────────────────────
# FUNCIÓN QUE TE FALTABA (IMPORT ERROR)
# ─────────────────────────────────────────
def render_tipos_oyente(df):

    import streamlit as st

    top3 = calcular_tipos_oyente(df)

    st.markdown("## 🎧 Tu tipo de oyente")

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
                {t['nombre']} — {t['porcentaje']}%
            </div>
            <div style="color:#ccc; margin-top:6px;">
                {t['descripcion']}
            </div>
        </div>
        """, unsafe_allow_html=True)