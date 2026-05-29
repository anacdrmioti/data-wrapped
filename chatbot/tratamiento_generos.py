import pandas as pd
from collections import Counter


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: enriquecer y resumir
# ─────────────────────────────────────────────────────────────

def enriquecer_con_generos(df_usuario_track: pd.DataFrame,
                           df_generos: pd.DataFrame,
                           persona_id: str,
                           top_n: int = 5) -> str:
    """
    Cruza las canciones del usuario con la tabla de géneros y
    devuelve un texto listo para añadir al contexto del LLM.

    Args:
        df_usuario_track: tabla usuario_track completa (todos los usuarios)
        df_generos: tabla de géneros cargada por genre_loader.cargar_csv_generos()
        persona_id: nombre del usuario activo
        top_n: cuántos géneros/moods mostrar en el resumen

    Returns:
        String con el resumen musical enriquecido, o string vacío si no hay datos.
    """

    # 1. Filtrar solo las canciones de este usuario
    df_user = df_usuario_track[df_usuario_track["persona_id"] == persona_id].copy()

    if df_user.empty:
        return ""

    # 2. Normalizar las claves de cruce (minúsculas, sin espacios)
    df_user["_cancion_norm"] = df_user["nombre_cancion"].str.lower().str.strip()
    df_user["_artista_norm"] = df_user["nombre_artista"].str.lower().str.strip()

    # 3. Hacer el merge con el CSV de géneros
    #    Cruzamos por cancion + artista normalizados
    df_merged = df_user.merge(
        df_generos,
        on=["_cancion_norm", "_artista_norm"],
        how="left",          # left: mantenemos TODAS las canciones del usuario
        suffixes=("", "_csv")
    )

    # 4. Separar canciones con y sin información de géneros
    df_con_genero = df_merged[df_merged["genero"].notna() &
                               df_merged["genero"].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    df_sin_genero = df_merged[~df_merged.index.isin(df_con_genero.index)]

    total_canciones = len(df_user)
    canciones_con_datos = len(df_con_genero)
    cobertura_pct = (canciones_con_datos / total_canciones * 100) if total_canciones > 0 else 0

    # Si la cobertura es muy baja, avisamos pero no fallamos
    if canciones_con_datos == 0:
        return (
            "INFORMACIÓN MUSICAL ADICIONAL:\n"
            "No se encontraron datos de géneros para las canciones de este usuario en la base de datos.\n"
            "Las recomendaciones se basarán únicamente en el historial de escucha."
        )

    partes = []
    partes.append(
        f"COBERTURA DE DATOS MUSICALES: {canciones_con_datos} de {total_canciones} "
        f"canciones tienen información de géneros ({cobertura_pct:.0f}%)"
    )

    # 5. Calcular géneros favoritos ponderados por score_interes
    partes.append(_resumen_generos(df_con_genero, top_n))

    # 6. Calcular moods predominantes ponderados por score_interes
    partes.append(_resumen_moods(df_con_genero, top_n))

    # 7. Calcular contextos de escucha frecuentes
    partes.append(_resumen_contextos(df_con_genero, top_n=3))

    # 8. Características musicales medias (energia, valencia, etc.)
    partes.append(_resumen_caracteristicas(df_con_genero))

    # 9. Idioma predominante
    partes.append(_resumen_idioma(df_con_genero))

    # 10. Canciones representativas por género (las de mayor interés)
    partes.append(_canciones_por_genero(df_con_genero, top_n=3))

    # Filtrar partes vacías y unir
    return "\n\n".join(p for p in partes if p)


# ─────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES DE RESUMEN
# ─────────────────────────────────────────────────────────────

def _resumen_generos(df: pd.DataFrame, top_n: int) -> str:
    """
    Calcula los géneros más frecuentes ponderando por score_interes.
    Un score alto = más peso en el ranking.
    """
    conteo = Counter()

    for _, row in df.iterrows():
        generos = row.get("genero", [])
        if not isinstance(generos, list):
            continue
        # El peso es el score de interés (entre 0 y 1)
        peso = float(row.get("score_interes", 0.5) or 0.5)
        for g in generos:
            conteo[g] += peso

    if not conteo:
        return ""

    top = conteo.most_common(top_n)
    lista = ", ".join(f"{g} ({v:.1f}pts)" for g, v in top)
    return f"GÉNEROS FAVORITOS (ponderados por interés):\n  {lista}"


def _resumen_moods(df: pd.DataFrame, top_n: int) -> str:
    """
    Calcula los moods predominantes ponderando por score_interes.
    """
    conteo = Counter()

    for _, row in df.iterrows():
        moods = row.get("mood", [])
        if not isinstance(moods, list):
            continue
        peso = float(row.get("score_interes", 0.5) or 0.5)
        for m in moods:
            conteo[m] += peso

    if not conteo:
        return ""

    top = conteo.most_common(top_n)
    lista = ", ".join(f"{m} ({v:.1f}pts)" for m, v in top)
    return f"MOODS PREDOMINANTES (ponderados por interés):\n  {lista}"


def _resumen_contextos(df: pd.DataFrame, top_n: int) -> str:
    """
    Calcula los contextos de escucha más frecuentes.
    """
    conteo = Counter()

    for _, row in df.iterrows():
        contextos = row.get("contexto", [])
        if not isinstance(contextos, list):
            continue
        peso = float(row.get("score_interes", 0.5) or 0.5)
        for c in contextos:
            conteo[c] += peso

    if not conteo:
        return ""

    top = conteo.most_common(top_n)
    lista = ", ".join(c for c, _ in top)
    return f"CONTEXTOS DE ESCUCHA HABITUALES:\n  {lista}"


def _resumen_caracteristicas(df: pd.DataFrame) -> str:
    """
    Calcula medias de las características numéricas ponderadas por score_interes.
    Las canciones con mayor interés pesan más en el promedio.
    """
    cols = ["energia", "valencia", "danceability", "instrumentalidad", "intensidad"]
    disponibles = [c for c in cols if c in df.columns]

    if not disponibles:
        return ""

    # Ponderar por score_interes para que las canciones favoritas
    # influyan más en el perfil musical
    pesos = df["score_interes"].fillna(0.5).clip(0.01, 1.0)

    medias = {}
    for col in disponibles:
        valores = pd.to_numeric(df[col], errors="coerce").fillna(0.5)
        medias[col] = (valores * pesos).sum() / pesos.sum()

    # Interpretar los valores en texto
    energia_txt = _nivel(medias.get("energia", 0.5))
    valencia_txt = _nivel(medias.get("valencia", 0.5))
    dance_txt = _nivel(medias.get("danceability", 0.5))
    inst_txt = _nivel(medias.get("instrumentalidad", 0.5))

    lineas = [
        f"  - Energía: {medias.get('energia', 0):.2f}/1.0 ({energia_txt})",
        f"  - Positividad (valencia): {medias.get('valencia', 0):.2f}/1.0 ({valencia_txt})",
        f"  - Bailabilidad: {medias.get('danceability', 0):.2f}/1.0 ({dance_txt})",
        f"  - Instrumentalidad: {medias.get('instrumentalidad', 0):.2f}/1.0 ({inst_txt})",
    ]

    return "CARACTERÍSTICAS MUSICALES MEDIAS:\n" + "\n".join(lineas)


def _resumen_idioma(df: pd.DataFrame) -> str:
    """
    Indica en qué idioma escucha principalmente el usuario.
    """
    if "idioma" not in df.columns:
        return ""

    conteo = df["idioma"].value_counts()
    if conteo.empty:
        return ""

    principal = conteo.index[0]
    pct = conteo.iloc[0] / conteo.sum() * 100
    return f"IDIOMA PREDOMINANTE: {principal} ({pct:.0f}% de canciones con datos)"


def _canciones_por_genero(df: pd.DataFrame, top_n: int) -> str:
    """
    Para cada uno de los géneros más escuchados, muestra las canciones
    más representativas (mayor score_interes).
    """
    # Primero calculamos los géneros principales
    conteo = Counter()
    for _, row in df.iterrows():
        generos = row.get("genero", [])
        if not isinstance(generos, list):
            continue
        peso = float(row.get("score_interes", 0.5) or 0.5)
        for g in generos:
            conteo[g] += peso

    if not conteo:
        return ""

    top_generos = [g for g, _ in conteo.most_common(3)]
    lineas = []

    for genero in top_generos:
        # Filtrar canciones de este género
        mascara = df["genero"].apply(
            lambda x: isinstance(x, list) and genero in x
        )
        sub = df[mascara].sort_values("score_interes", ascending=False).head(top_n)

        if sub.empty:
            continue

        canciones = ", ".join(
            f"{r['nombre_cancion']} ({r['nombre_artista']})"
            for _, r in sub.iterrows()
        )
        lineas.append(f"  [{genero.upper()}]: {canciones}")

    if not lineas:
        return ""

    return "CANCIONES REPRESENTATIVAS POR GÉNERO:\n" + "\n".join(lineas)


def _nivel(valor: float) -> str:
    """Convierte un valor 0-1 en descripción textual."""
    if valor >= 0.7:
        return "alto"
    elif valor >= 0.4:
        return "medio"
    else:
        return "bajo"
