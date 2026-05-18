"""
genre_loader.py
---------------
Carga el CSV de géneros/mood/características y lo prepara para
cruzarlo con los datos del usuario.

Este módulo se usa desde context_builder.py.
No modifica ningún otro fichero del proyecto.
"""

import ast
import pandas as pd


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: cargar y limpiar el CSV
# ─────────────────────────────────────────────────────────────

def cargar_csv_generos(ruta: str) -> pd.DataFrame:
    """
    Lee el CSV de géneros y devuelve un DataFrame limpio y listo
    para hacer merge con los datos del usuario.

    El CSV tiene estas columnas:
      nombre_cancion, nombre_artista, genero, mood, contexto,
      energia, valencia, danceability, instrumentalidad, intensidad, idioma

    'genero', 'mood' y 'contexto' vienen como strings tipo "['rock', 'pop']".
    Esta función los convierte en listas Python reales.

    Args:
        ruta: ruta al fichero CSV (p.ej. "data/canciones_clasificadas.csv")

    Returns:
        DataFrame limpio con columnas 'genero', 'mood', 'contexto' como listas,
        y columnas '_cancion_norm' y '_artista_norm' para el merge.
    """
    df = pd.read_csv(ruta)

    # --- Limpiar espacios extra y caracteres raros en los nombres ---
    # Hay casos como "3 PECADOS DESPUES\xa0" (non-breaking space al final)
    df["nombre_cancion"] = df["nombre_cancion"].str.strip()
    df["nombre_artista"] = df["nombre_artista"].str.strip()

    # --- Columnas normalizadas para hacer el merge sin fallar por mayúsculas ---
    # Usamos minúsculas y sin espacios extra en los extremos
    df["_cancion_norm"] = df["nombre_cancion"].str.lower().str.strip()
    df["_artista_norm"] = df["nombre_artista"].str.lower().str.strip()

    # --- Convertir strings tipo "['rock', 'pop']" a listas Python reales ---
    for col in ["genero", "mood", "contexto"]:
        df[col] = df[col].apply(_parse_lista)

    # --- Normalizar el idioma (hay "inglés" e "ingles" por ejemplo) ---
    df["idioma"] = df["idioma"].str.strip().str.lower()
    df["idioma"] = df["idioma"].replace({
        "ingles": "inglés",
        "espanol": "español",
        "otros": "other",
    })

    return df


# ─────────────────────────────────────────────────────────────
# FUNCIÓN AUXILIAR: parsear listas guardadas como string
# ─────────────────────────────────────────────────────────────

def _parse_lista(valor) -> list:
    """
    Convierte un string tipo "['rock', 'pop']" en una lista Python.
    Si falla o el valor es nulo, devuelve lista vacía.
    """
    if pd.isna(valor):
        return []
    try:
        resultado = ast.literal_eval(str(valor))
        # Asegurarnos de que es una lista
        if isinstance(resultado, list):
            return [str(x).strip().lower() for x in resultado]
        else:
            return [str(resultado).strip().lower()]
    except Exception:
        return []
