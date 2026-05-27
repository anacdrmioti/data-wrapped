import pandas as pd
import numpy as np
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split

def clasificacion_skip_2(df_tracks, df_escuchas, canciones_clasificadas):

    # =================================================
    # 1. TRAIN MODEL EN DIRECTO
    # =================================================

    df_final = df_escuchas.merge(
        canciones_clasificadas,
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    y = df_final["saltada"].astype(int)

    X = df_final[
        [
            "hora",
            "periodo_dia",
            "dia_semana",
            "fin_de_semana",
            "plataforma",
            "reproduccion_aleatoria",
            "milisegundos_reproducidos",
            "genero",
            "mood",
            "contexto",
            "energia",
            "valencia",
            "danceability",
            "instrumentalidad",
            "intensidad",
            "idioma"
        ]
    ].copy()

    cat_cols = ["periodo_dia","plataforma","genero","mood","contexto","idioma"]

    for c in cat_cols:
        X[c] = X[c].astype(str).fillna("unknown")

    X = X.fillna(0)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    train_pool = Pool(X_train, y_train, cat_features=cat_cols)
    val_pool = Pool(X_val, y_val, cat_features=cat_cols)

    model = CatBoostClassifier(
        iterations=300,   # 👈 menos para streamlit
        depth=6,
        learning_rate=0.05,
        loss_function="Logloss",
        verbose=False
    )

    model.fit(train_pool, eval_set=val_pool)

    # =================================================
    # 2. PREDECIR TRACKS
    # =================================================

    now = pd.Timestamp.now()

    hora = now.hour
    dia_semana = now.dayofweek
    fin_de_semana = 1 if dia_semana >= 5 else 0

    if 5 <= hora < 12:
        periodo_dia = "mañana"
    elif 12 <= hora < 18:
        periodo_dia = "tarde"
    elif 18 <= hora < 22:
        periodo_dia = "noche"
    else:
        periodo_dia = "madrugada"

    probs = []

    for nombre_cancion in df_tracks["nombre_cancion"]:

        info = canciones_clasificadas[
            canciones_clasificadas["nombre_cancion"] == nombre_cancion
        ]

        if info.empty:
            row = {
                "genero":"unknown",
                "mood":"unknown",
                "contexto":"unknown",
                "energia":0,
                "valencia":0,
                "danceability":0,
                "instrumentalidad":0,
                "intensidad":0,
                "idioma":"unknown"
            }
        else:
            row = info.iloc[0]

        nuevo = pd.DataFrame([{
            "hora": hora,
            "periodo_dia": periodo_dia,
            "dia_semana": dia_semana,
            "fin_de_semana": fin_de_semana,
            "plataforma": "mobile",
            "reproduccion_aleatoria": 1,
            "milisegundos_reproducidos": 0,
            "genero": row["genero"],
            "mood": row["mood"],
            "contexto": row["contexto"],
            "energia": row["energia"],
            "valencia": row["valencia"],
            "danceability": row["danceability"],
            "instrumentalidad": row["instrumentalidad"],
            "intensidad": row["intensidad"],
            "idioma": row["idioma"]
        }])

        proba = model.predict_proba(nuevo)[:, 1][0]
        probs.append(proba)

    df_tracks = df_tracks.copy()
    df_tracks["proba_skip"] = probs

    return df_tracks