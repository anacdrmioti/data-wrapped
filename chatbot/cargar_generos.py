import ast
import pandas as pd


# cargar y limpiar el CSV

def cargar_csv_generos(ruta: str) -> pd.DataFrame:
    """
    Lee el CSV de géneros y devuelve un DataFrame limpio y listo
    para hacer merge con los datos del usuario.

    El CSV tiene estas columnas:
      nombre_cancion, nombre_artista, genero, mood, contexto,
      energia, valencia, danceability, instrumentalidad, intensidad, idioma

    Args:
        ruta: ruta al fichero CSV (p.ej. "data/canciones_clasificadas.csv")

    Returns:
        DataFrame limpio con columnas 'genero', 'mood', 'contexto' como listas,
        y columnas '_cancion_norm' y '_artista_norm' para el merge.
    """
    df = pd.read_csv(ruta)

    # Limpiar espacios extra y caracteres raros en los nombres
    df["nombre_cancion"] = df["nombre_cancion"].str.strip()
    df["nombre_artista"] = df["nombre_artista"].str.strip()

    # Columnas normalizadas para hacer el merge sin fallar por mayúsculas
    # Usamos minúsculas y sin espacios extra en los extremos
    df["_cancion_norm"] = df["nombre_cancion"].str.lower().str.strip()
    df["_artista_norm"] = df["nombre_artista"].str.lower().str.strip()

    # Convertir  "['rock', 'pop']" a listas
    for col in ["genero", "mood", "contexto"]:
        df[col] = df[col].apply(_parse_lista)

    #  Normalizar el idioma 
    df["idioma"] = df["idioma"].str.strip().str.lower()
    df["idioma"] = df["idioma"].replace({
        "ingles": "inglés",
        "espanol": "español",
        "otros": "other",
    })

    return df


#  parsear listas guardadas como string

def _parse_lista(valor) -> list:
    """
    Convierte  "['rock', 'pop']" en una lista .
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
