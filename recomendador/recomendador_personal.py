# Importamos las librerias:

import streamlit as st
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer
import ast


# Para quitar los warnings:
import logging
from transformers.utils import logging as hf_logging
# transformers
hf_logging.set_verbosity_error()
# sentence-transformers
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
# huggingface hub
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
# requests/httpx
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

from Recomendador.Codificador_canciones import song_to_text
from Recomendador.Clasificador import clasificacion_skip


def generador_embeddings_canciones(df_track, path_csv):

    """
    Crea embeddings (vectores) de canciones para poder compararlas.

    Qué hace:
    - Carga las canciones desde un CSV
    - Se queda solo con las canciones que están en df_track
    - Convierte cada canción en un texto usando song_to_text (definido en Codificador_canciones)
    - Usa un modelo de SentenceTransformers para pasar ese texto a un vector (embedding)
    - Devuelve cada canción con su embedding

    Esto sirve para comparar canciones y hacer recomendaciones.
    """

    df_catalogo = pd.read_csv(path_csv)

    # nos quedamos solo con canciones del historial en las fechas establecidas
    df = df_catalogo.merge(
        df_track[["nombre_cancion", "nombre_artista"]],
        on=["nombre_cancion", "nombre_artista"],
        how="inner"
    )

    # texto para embeddings
    df["text_embedding"] = df.apply(
        lambda row: song_to_text(
            mood=row["mood"],
            genero=row["genero"],
            contexto=row["contexto"],
            energia=row["energia"],
            valencia=row["valencia"],
            danceability=row["danceability"],
            instrumentalidad=row["instrumentalidad"],
            intensidad=row["intensidad"]
        ),
        axis=1
    )

    # modelo
    model = SentenceTransformer('all-MiniLM-L6-v2')

    embeddings = model.encode(
        df["text_embedding"].tolist(),
        batch_size=32,
        show_progress_bar=True
    )

    df["embedding"] = list(embeddings)

    return df[["nombre_cancion", "nombre_artista", "embedding", "idioma"]]


def recomendador_historico_escuchas(query, idiomas_usuario, df_tracks, df_escuchas, df_embeddings_canciones):

    """
    Recomendador de canciones basado en el historial del usuario y una búsqueda (query).

    Qué hace:
    - Entrena/aplica un modelo para estimar qué canciones el usuario puede saltarse (skip) basado en el contexto temporal
    - Usa el historial de escuchas para crear un perfil del usuario
    - Convierte la query del usuario en un embedding (vector)
    - Combina el perfil del usuario + la query actual
    - Busca canciones similares usando embeddings
    - Devuelve las mejores recomendaciones

    Idea:
    ------
    Recomienda canciones que encajen con:
    - lo que el usuario ha escuchado antes
    - lo que está buscando ahora
    - evitando canciones que probablemente se salten

    Retorna:
    --------
    DataFrame con las canciones recomendadas y su puntuación.
    """

    # Cargamos dataset con info de canciones
    canciones_clasificadas = pd.read_csv("data/canciones_clasificadas.csv")

    # Entrenamos/aplicamos modelo para predecir probabilidad de skip
    df_tracks = clasificacion_skip(df_tracks, df_escuchas, canciones_clasificadas)

    # Embedding de la consulta del usuario (lo que está buscando)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query])[0]

    # Filtramos canciones según idioma del usuario
    df_filtrado = df_embeddings_canciones[
        df_embeddings_canciones["idioma"].isin(idiomas_usuario)
    ]

    # Nos quedamos solo con canciones válidas del catálogo
    df = df_tracks.copy()
    df = df.merge(
        df_filtrado[["nombre_cancion", "nombre_artista"]],
        on=["nombre_cancion", "nombre_artista"],
        how="inner"
    )

    # Invertimos métricas de skip (menos skip = mejor)
    df["no_skip"] = 1 - df_tracks["pct_saltada"]
    df["no_skip_temprano"] = 1 - df_tracks["pct_skip_temprano"]

    # Calculamos recencia (cuánto hace que se escuchó cada canción)
    df["ultima_escucha"] = pd.to_datetime(df["ultima_escucha"]).dt.tz_localize(None)
    df["recencia"] = (pd.Timestamp.now() - df["ultima_escucha"]).dt.days

    # Convertimos recencia en un score (más reciente = más peso)
    df["recencia_score"] = np.exp(-df["recencia"] / 30)

    # Construimos un peso que representa la importancia de cada canción en el usuario
    df["peso"] = (
        0.5 * df["score_medio"] +                  # gusto general
        0.2 * df["recencia_score"] +              # recientes
        0.2 * np.log(df["reproducciones_totales"] + 1) +  # frecuencia
        0.1 * df["no_skip"]                       # calidad (no skip)
    )

    # Penalizamos canciones con alta probabilidad de skip
    df["peso"] = df["peso"] * (1 - df["proba_skip"])

    # Añadimos embeddings de las canciones
    df = df.merge(
        df_embeddings_canciones[
            ["nombre_cancion", "nombre_artista", "embedding"]
        ],
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    # Eliminamos duplicados y canciones sin embedding
    df = df.drop_duplicates(subset=["nombre_cancion", "nombre_artista"]).copy()
    df = df[~df["embedding"].isna()]

    # Convertimos embeddings a matriz
    embeddings = np.vstack(df["embedding"].values)

    # Creamos embedding del usuario basado en su historial (ponderado)
    embedding_usuario_historico = np.sum(
        df["peso"].values.reshape(-1, 1) * embeddings,
        axis=0
    ) / np.sum(df["peso"])

    # Mezclamos historial + mood del usuario (query)
    embedding_final = (
        0.2 * embedding_usuario_historico +
        0.8 * query_embedding
    )

    # Calculamos similitud entre usuario y todas las canciones
    all_embeddings = np.vstack(df_filtrado["embedding"].values)

    similaridades = cosine_similarity(
        all_embeddings,
        embedding_final.reshape(1, -1)
    ).flatten()

    df_filtrado["score_recomendacion"] = similaridades

    # Ordenamos y nos quedamos con las mejores canciones
    recomendaciones = df_filtrado.sort_values(
        "score_recomendacion",
        ascending=False
    ).head(5)

    return recomendaciones[["nombre_cancion", "nombre_artista", "score_recomendacion"]]