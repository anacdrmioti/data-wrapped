import streamlit as st
import pandas as pd
import numpy as np
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

from recomendador.codificador_canciones import song_to_text


def generador_embeddings_canciones(df_track, path_csv):

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

def recomendador_historico_escuchas(query, idiomas_usuario, df_tracks, df_embeddings_canciones):

    # Primero, vamos a calcular el embedding del usuario basado en sus preferencias
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query])[0]

    df_filtrado = df_embeddings_canciones[
        df_embeddings_canciones["idioma"].isin(idiomas_usuario)
    ]

    df = df_tracks.copy()
    df = df.merge(
        df_filtrado[["nombre_cancion", "nombre_artista"]],
        on=["nombre_cancion", "nombre_artista"],
        how="inner"
    )

    # Sabemos que existen features que tienen que ser bajas para que la canción sea recomendada, como el porcentaje de saltada y skip temprano. 
    # Por lo tanto, vamos a invertir estas features para que el modelo pueda aprender mejor.

    df["no_skip"] = 1 - df_tracks["pct_saltada"]
    df["no_skip_temprano"] = 1 - df_tracks["pct_skip_temprano"]

    # Y también queremos que de más pesos a aquellas canciones que se han escuchado recientemente:

    df["ultima_escucha"] = pd.to_datetime(df["ultima_escucha"]).dt.tz_localize(None)
    df["recencia"] = (pd.Timestamp.now() - df["ultima_escucha"]).dt.days
    # Más peso a las canciones que se han escuchado más recientemente (0 días → 1.0, 30 días → ~0.37, 100 días → casi 0)
    df["recencia_score"] = np.exp(-df["recencia"] / 30)

    # Peso para definir al usuario

    df["peso"] = (
        0.5 * df["score_medio"] +
        0.2 * df["recencia_score"] +
        0.2 * np.log(df["reproducciones_totales"] + 1) +
        0.1 * df["no_skip"]
    )

    # Agregamos a df el embedding y quitamos posibles canciones repetidas o que no tengan embedding definido:

    df = df.merge(
        df_embeddings_canciones[
            ["nombre_cancion", "nombre_artista", "embedding"]
        ],
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    df = df.drop_duplicates(
        subset=["nombre_cancion", "nombre_artista"]
    ).copy()

    df = df[~df["embedding"].isna()]

    # Y ahora ya generamos el embedding del usuario pero simplemente en base al historial

    embeddings = np.vstack(df["embedding"].values)

    embedding_usuario_historico = np.sum(
        df["peso"].values.reshape(-1,1) * embeddings,
        axis=0
    ) / np.sum(df["peso"])

    
    # Y por tanto ahora el embedding del usuario en este momento va a ser el embedding del historico + query embedding

    embedding_final = (
        0 * embedding_usuario_historico
        + 1 * query_embedding
    )

    # Y este ya si que lo comparamos contra toda la base de datos:

    all_embeddings = np.vstack(
        df_filtrado["embedding"].values
    )

    similaridades = cosine_similarity(
        all_embeddings,
        embedding_final.reshape(1, -1)
    ).flatten()

    df_filtrado["score_recomendacion"] = similaridades

    recomendaciones = df_filtrado.sort_values(
        "score_recomendacion",
        ascending=False
    ).head(5)

    return recomendaciones[["nombre_cancion", "nombre_artista", "score_recomendacion"]]


def convertir_preferencias_a_embeddings(df_pref_contexto_track):

    df = df_pref_contexto_track.copy()

    # Para cada usuario, vamos a calcular la media de sus preferencias en cada contexto. 
    # Esto nos dará una idea de qué contextos prefiere cada usuario.

    features_contexto = [
        "pref_escuchar_solo",
        "pref_escuchar_con_amigos",
        "pref_escuchar_en_fiesta",
        "pref_escuchar_en_coche",
        "pref_escuchar_en_gym",
        "pref_escuchar_para_relajarse"
    ]

    X = df[features_contexto]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, scaler
