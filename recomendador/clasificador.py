# Importamos las librerías:

import pandas as pd
import numpy as np

from catboost import CatBoostClassifier, Pool

from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

# Función encargada de entrenar el modelo de clasificación:

def clasificacion_skip(df_tracks, df_escuchas, canciones_clasificadas):

    """
    Predice la probabilidad de que una canción sea saltada por el usuario
    teniendo en cuenta tanto el contexto de escucha como las características
    musicales de cada track.

    El modelo se entrena en tiempo real utilizando el histórico de escuchas
    del usuario y posteriormente genera una probabilidad de skip para cada
    canción candidata del recomendador.

    Parámetros
    ----------
    df_tracks : DataFrame
        Canciones sobre las que queremos calcular la probabilidad de skip.

    df_escuchas : DataFrame
        Histórico de escuchas del usuario.

    canciones_clasificadas : DataFrame
        Información enriquecida de las canciones
        (género, mood, energía, idioma, etc.).

    Returns
    -------
    DataFrame
        DataFrame original con una nueva columna:
        - proba_skip -> probabilidad estimada de que el usuario salte la canción.
    """

    # Unimos el histórico con la información musical de cada canción
    df_final = df_escuchas.merge(
        canciones_clasificadas,
        on=["nombre_cancion", "nombre_artista"],
        how="left"
    )

    # Variable objetivo:
    # 1 -> canción saltada
    # 0 -> canción escuchada 
    y = df_final["saltada"].astype(int)

    # Variables que ayudan al modelo a entender en qué contexto suele escuchar música el usuario
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

    # Variables categóricas
    cat_cols = [
        "periodo_dia",
        "plataforma",
        "genero",
        "mood",
        "contexto",
        "idioma"
    ]

    # Convertimos a string para evitar problemas con categorías vacías o valores nulos
    for c in cat_cols:
        X[c] = X[c].astype(str).fillna("unknown")

    X = X.fillna(0)

    # Separación train / validación
    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    train_pool = Pool(X_train, y_train, cat_features=cat_cols)
    val_pool = Pool(X_val, y_val, cat_features=cat_cols)

    # CatBoost funciona bastante bien mezclando variables numéricas y categóricas sin demasiado preprocesado
    model = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.05,
        loss_function="Logloss",
        verbose=False
    )

    model.fit(train_pool, eval_set=val_pool)

    val_proba = model.predict_proba(X_val)[:, 1]

    # threshold estándar
    val_pred = (val_proba >= 0.5).astype(int)

    accuracy = accuracy_score(y_val, val_pred)
    precision = precision_score(y_val, val_pred)
    recall = recall_score(y_val, val_pred)
    f1 = f1_score(y_val, val_pred)
    auc = roc_auc_score(y_val, val_proba)

    print("\nMÉTRICAS DEL MODELO")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC AUC:   {auc:.4f}")

    # Obtenemos el contexto temporal actual
    now = pd.Timestamp.now()

    hora = now.hour
    dia_semana = now.dayofweek
    fin_de_semana = 1 if dia_semana >= 5 else 0

    # Clasificación sencilla del momento del día
    if 5 <= hora < 12:
        periodo_dia = "mañana"
    elif 12 <= hora < 18:
        periodo_dia = "tarde"
    elif 18 <= hora < 22:
        periodo_dia = "noche"
    else:
        periodo_dia = "madrugada"

    probs = []

    # Calculamos la probabilidad de skip canción a canción
    for nombre_cancion in df_tracks["nombre_cancion"]:

        info = canciones_clasificadas[
            canciones_clasificadas["nombre_cancion"] == nombre_cancion
        ]

        # Si no tenemos información de una canción, usamos valores neutros
        if info.empty:
            row = {
                "genero": "unknown",
                "mood": "unknown",
                "contexto": "unknown",
                "energia": 0,
                "valencia": 0,
                "danceability": 0,
                "instrumentalidad": 0,
                "intensidad": 0,
                "idioma": "unknown"
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

        # Probabilidad estimada de skip
        proba = model.predict_proba(nuevo)[:, 1][0]
        probs.append(proba)

    df_tracks = df_tracks.copy()
    df_tracks["proba_skip"] = probs

    return df_tracks