import os # para carpetas y arhivos del drive
import re
import json # para leer json
import logging # para mensajes de seguimiento.
import warnings # para controlar avisos
from pathlib import Path # para facilitar la salida de carpetas

import numpy as np
import pandas as pd
import streamlit as st

TIMEZONE = "Europe/Madrid"

# Umbrales de negocio
UMBRAL_SKIP_TEMPRANO_SEG = 15
UMBRAL_ESCUCHA_VALIDA_SEG = 30
UMBRAL_COMPLETA_HEURISTICA_SEG = 180   # 3 min, heurística si no tenemos duración real
UMBRAL_MS_MAX_EVENTO = 86_400_000      # 24h, para marcar anomalías

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("spotify_preprocessing")


# =============================================================================
# 2. UTILIDADES
# =============================================================================

def normalizar_texto(x):
    if pd.isna(x):
        return np.nan
    x = str(x).strip()
    return x if x else np.nan


def normalizar_bool(x):
    """
    [B2-FIX] Añadidos np.bool_ y np.integer para robustez con arrays numpy.
    En Python 3 np.bool_ hereda de bool, pero se hace explícito para claridad
    y compatibilidad con distintas versiones de numpy/pandas.
    """
    if pd.isna(x):
        return 0
    if isinstance(x, (bool, np.bool_)):
        return int(x)
    if isinstance(x, (int, float, np.integer, np.floating)):
        return int(bool(x))
    if isinstance(x, str):
        x = x.strip().lower()
        if x in {"true", "1", "yes", "y", "si", "sí"}:
            return 1
        if x in {"false", "0", "no", "n"}:
            return 0
    return 0


def simplificar_plataforma_valor(x):
    if pd.isna(x):
        return "desconocido"
    x = str(x).lower()
    if "android" in x:
        return "android"
    elif "iphone" in x or "ios" in x:
        return "ios"
    elif "windows" in x:
        return "windows"
    elif "mac" in x:
        return "mac"
    elif "linux" in x:
        return "linux"
    elif "web" in x:
        return "web"
    elif "cast" in x or "chromecast" in x:
        return "cast"
    elif "tablet" in x:
        return "tablet"
    else:
        return "other"


def obtener_estacion(mes):
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"


def obtener_periodo_dia(hora):
    if 6 <= hora < 13:
        return "mañana"
    elif 13 <= hora < 20:
        return "tarde"
    elif 20 <= hora < 24:
        return "noche"
    else:
        return "madrugada"


def extraer_track_id_desde_uri(uri):
    """Extrae el ID puro de una URI tipo spotify:track:xxxxx"""
    if pd.isna(uri):
        return np.nan
    uri = str(uri).strip()
    m = re.match(r"^spotify:track:([A-Za-z0-9]+)$", uri)
    return m.group(1) if m else np.nan


def crear_track_clave(track_id, nombre_cancion, nombre_artista):
    """
    Clave robusta:
    - si hay track_id, usamos track_id (más estable)
    - si no, usamos nombre_cancion + artista normalizados
    """
    if pd.notna(track_id):
        return str(track_id)
    nc = "" if pd.isna(nombre_cancion) else str(nombre_cancion).strip().lower()
    na = "" if pd.isna(nombre_artista) else str(nombre_artista).strip().lower()
    if nc == "" and na == "":
        return np.nan
    return f"{nc}||{na}"


# =============================================================================
# 3. CARGA DE DATOS
# =============================================================================

def listar_json_audio(ruta_carpeta):
    """
    [B1-FIX] Versión anterior filtraba con 'Audio' in f (case-sensitive) y
    perdía archivos con naming alternativo. La nueva estrategia:
      - Carga todos los .json de la carpeta.
      - Excluye explícitamente los archivos de Podcasts/Episodes/Video.
      - Acepta cualquier JSON que contenga 'audio' (case-insensitive) en el nombre
        O que no sea un archivo de contenido no-musical conocido.
    Esto cubre las distintas convenciones de exportación de Spotify.
    """
    if not os.path.exists(ruta_carpeta):
        log.warning(f"No existe la carpeta: {ruta_carpeta}")
        return []

    EXCLUIDOS = {"podcast", "episode", "video", "video_history"}

    archivos = []
    for f in os.listdir(ruta_carpeta):
        if not f.endswith(".json"):
            continue
        nombre_lower = f.lower()
        # Excluir archivos de contenido no musical
        if any(exc in nombre_lower for exc in EXCLUIDOS):
            continue
        # Incluir si parece audio o streaming history
        if "audio" in nombre_lower or "streaming_history" in nombre_lower:
            archivos.append(f)

    archivos.sort()
    return archivos


def cargar_jsons_usuario(persona_id, ruta_carpeta):
    archivos = listar_json_audio(ruta_carpeta)
    if not archivos:
        log.warning(f"[{persona_id}] No se encontraron JSON de Audio.")
        return pd.DataFrame()

    dfs = []
    for archivo in archivos:
        ruta = os.path.join(ruta_carpeta, archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                log.warning(f"[{persona_id}] {archivo} no contiene una lista JSON válida.")
                continue

            df_temp = pd.DataFrame(data)
            df_temp["persona_id"] = persona_id
            df_temp["archivo_origen"] = archivo
            dfs.append(df_temp)

            log.info(f"[{persona_id}] Cargado {archivo}: {len(df_temp)} filas")
        except Exception as e:
            log.warning(f"[{persona_id}] Error leyendo {archivo}: {e}")

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    log.info(f"[{persona_id}] Total filas cargadas: {len(df)}")
    return df


def cargar_todos_los_usuarios(usuarios_dict):
    dfs = []
    for persona_id, ruta in usuarios_dict.items():
        df_user = cargar_jsons_usuario(persona_id, ruta)
        if not df_user.empty:
            dfs.append(df_user)

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    log.info(f"Total registros cargados: {len(df)}")
    return df


# =============================================================================
# 4. LIMPIEZA Y NORMALIZACIÓN
# =============================================================================

def limpiar_y_renombrar_columnas(df):
    columnas_eliminar = [
        "episode_name",
        "episode_show_name",
        "spotify_episode_uri",
        "audiobook_title",
        "audiobook_uri",
        "audiobook_chapter_uri",
        "audiobook_chapter_title",
        "incognito_mode",
        "offline_timestamp",
        "ip_addr"
    ]
    df = df.drop(columns=[c for c in columnas_eliminar if c in df.columns], errors="ignore")

    mapa = {
        "ts": "fecha_finalizacion_utc",
        "platform": "plataforma",
        "ms_played": "milisegundos_reproducidos",
        "conn_country": "pais_conexion",
        "master_metadata_track_name": "nombre_cancion",
        "master_metadata_album_artist_name": "nombre_artista",
        "master_metadata_album_album_name": "nombre_album",
        "spotify_track_uri": "track_uri",
        "reason_start": "razon_inicio",
        "reason_end": "razon_fin",
        "shuffle": "reproduccion_aleatoria",
        "skipped": "saltada",
        "offline": "reproduccion_offline",
    }
    mapa = {k: v for k, v in mapa.items() if k in df.columns}
    df = df.rename(columns=mapa)

    # Añadir columnas esperadas si faltan (compatibilidad con exportaciones antiguas)
    columnas_esperadas = [
        "fecha_finalizacion_utc", "plataforma", "milisegundos_reproducidos",
        "pais_conexion", "nombre_cancion", "nombre_artista", "nombre_album",
        "track_uri", "razon_inicio", "razon_fin", "reproduccion_aleatoria",
        "saltada", "reproduccion_offline"
    ]
    for col in columnas_esperadas:
        if col not in df.columns:
            df[col] = np.nan

    return df


def normalizar_columnas(df):
    columnas_texto = [
        "plataforma", "pais_conexion", "nombre_cancion", "nombre_artista",
        "nombre_album", "track_uri", "razon_inicio", "razon_fin"
    ]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_texto)

    # [B2-FIX] Los booleanos del JSON de Spotify se cargan como bool nativos de
    # Python, pero al concatenar DataFrames pueden convertirse a object dtype.
    # normalizar_bool ahora maneja todos los casos.
    for col in ["reproduccion_aleatoria", "saltada", "reproduccion_offline"]:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_bool)

    df["milisegundos_reproducidos"] = pd.to_numeric(
        df["milisegundos_reproducidos"], errors="coerce"
    )
    df["plataforma"] = df["plataforma"].apply(simplificar_plataforma_valor)

    return df


# =============================================================================
# 5. VARIABLES TEMPORALES Y CONTEXTUALES
# =============================================================================

def crear_variables_temporales(df, timezone=TIMEZONE):
    df["fecha_finalizacion_utc"] = pd.to_datetime(
        df["fecha_finalizacion_utc"], utc=True, errors="coerce"
    )

    # [B3-FIX] El flag se calcula aquí y se conserva explícitamente.
    # En el código original se creaba pero luego se perdía en el .copy() del filtrado.
    n_invalidos = int(df["fecha_finalizacion_utc"].isna().sum())
    if n_invalidos > 0:
        log.warning(f"Timestamps inválidos descartados: {n_invalidos}")

    df = df[df["fecha_finalizacion_utc"].notna()].copy()

    df["fecha_finalizacion_local"] = df["fecha_finalizacion_utc"].dt.tz_convert(timezone)
    df["fecha"] = df["fecha_finalizacion_local"].dt.date
    df["anio"] = df["fecha_finalizacion_local"].dt.year
    df["mes"] = df["fecha_finalizacion_local"].dt.month
    df["dia"] = df["fecha_finalizacion_local"].dt.day
    df["dia_semana"] = df["fecha_finalizacion_local"].dt.dayofweek
    df["nombre_dia_semana"] = df["dia_semana"].map({
        0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
        4: "viernes", 5: "sábado", 6: "domingo"
    })
    df["hora"] = df["fecha_finalizacion_local"].dt.hour
    df["semana_del_anio"] = df["fecha_finalizacion_local"].dt.isocalendar().week.astype(int)
    df["trimestre"] = df["fecha_finalizacion_local"].dt.quarter
    df["fin_de_semana"] = df["dia_semana"].isin([5, 6]).astype(int)
    df["es_laborable"] = (1 - df["fin_de_semana"]).astype(int)
    df["estacion"] = df["mes"].apply(obtener_estacion)
    df["periodo_dia"] = df["hora"].apply(obtener_periodo_dia)

    return df


# =============================================================================
# 6. VARIABLES DE ESCUCHA
# =============================================================================

def crear_variables_escucha(df):
    df["flag_ms_played_invalido"] = (
        df["milisegundos_reproducidos"].isna() |
        (df["milisegundos_reproducidos"] <= 0)
    ).astype(int)

    df["segundos_reproducidos"] = df["milisegundos_reproducidos"] / 1000
    df["minutos_reproducidos"] = df["milisegundos_reproducidos"] / 60000

    df["skip_temprano"] = (df["segundos_reproducidos"] < UMBRAL_SKIP_TEMPRANO_SEG).astype(int)
    df["escucha_valida"] = (df["segundos_reproducidos"] >= UMBRAL_ESCUCHA_VALIDA_SEG).astype(int)

    # Sin API no conocemos duración real del track → heurístico
    df["duracion_track_ms"] = np.nan
    df["duracion_relativa_escucha"] = np.nan
    df["completa_aprox"] = (df["segundos_reproducidos"] >= UMBRAL_COMPLETA_HEURISTICA_SEG).astype(int)

    df["fin_natural"] = (df["razon_fin"] == "trackdone").astype(int)
    df["salto_manual"] = df["razon_fin"].isin(["fwdbtn", "backbtn"]).astype(int)
    df["inicio_manual"] = df["razon_inicio"].isin(["clickrow", "playbtn", "remote"]).astype(int)
    df["anomalia_duracion_extrema"] = (df["milisegundos_reproducidos"] > UMBRAL_MS_MAX_EVENTO).astype(int)

    return df


# =============================================================================
# 7. IDS ANALÍTICOS
# =============================================================================

def crear_ids_analiticos(df):
    df["track_id"] = df["track_uri"].apply(extraer_track_id_desde_uri)

    df["track_clave"] = df.apply(
        lambda r: crear_track_clave(
            r.get("track_id"),
            r.get("nombre_cancion"),
            r.get("nombre_artista")
        ),
        axis=1
    )

    df["artista_clave"] = df["nombre_artista"].fillna("").astype(str).str.strip().str.lower()
    df["album_clave"] = (
        df["nombre_album"].fillna("").astype(str).str.strip().str.lower()
        + "||"
        + df["nombre_artista"].fillna("").astype(str).str.strip().str.lower()
    )

    df["flag_track_uri_invalida"] = (df["track_uri"].notna() & df["track_id"].isna()).astype(int)
    df["flag_track_metadata_incompleta"] = (
        df["nombre_cancion"].isna() | df["nombre_artista"].isna()
    ).astype(int)

    return df


# =============================================================================
# 8. LIMPIEZA DE REGISTROS
# =============================================================================

def limpiar_registros(df):
    """
    [B4-FIX] La deduplicación original tenía un fallo sutil: cuando track_uri,
    nombre_cancion o nombre_artista son NaN, pandas considera que NaN != NaN,
    por lo que dos filas con NaN en la misma columna NUNCA se detectaban como
    duplicadas. Solución: rellenar NaN con "" solo para la comparación de
    duplicados, sin modificar los datos originales.
    """
    informe = {}
    n_inicial = len(df)

    # Eliminar timestamp inválido (ya filtrado antes, pero por seguridad)
    mask_timestamp = df["fecha_finalizacion_utc"].isna()
    informe["timestamp_invalidos_eliminados"] = int(mask_timestamp.sum())
    df = df[~mask_timestamp].copy()

    # Eliminar ms_played no válido
    mask_ms = df["milisegundos_reproducidos"].isna() | (df["milisegundos_reproducidos"] <= 0)
    informe["ms_played_invalidos_eliminados"] = int(mask_ms.sum())
    df = df[~mask_ms].copy()

    # Eliminar filas sin ninguna identificación musical mínima
    mask_sin_identidad = (
        df["track_uri"].isna() &
        df["nombre_cancion"].isna() &
        df["nombre_artista"].isna()
    )
    informe["filas_sin_identidad_musical_eliminadas"] = int(mask_sin_identidad.sum())
    df = df[~mask_sin_identidad].copy()

    # [B4-FIX] Duplicados exactos: rellenar NaN con "" solo para la comparación
    columnas_dup = [
        "persona_id", "fecha_finalizacion_utc",
        "track_uri", "nombre_cancion", "nombre_artista",
        "milisegundos_reproducidos"
    ]
    columnas_dup = [c for c in columnas_dup if c in df.columns]

    # Crear df auxiliar solo para la comparación (sin modificar df)
    df_para_dup = df[columnas_dup].copy()
    for col in ["track_uri", "nombre_cancion", "nombre_artista"]:
        if col in df_para_dup.columns:
            df_para_dup[col] = df_para_dup[col].fillna("")

    mask_dup = df_para_dup.duplicated(keep="first")
    informe["duplicados_exactos_eliminados"] = int(mask_dup.sum())
    df = df[~mask_dup].copy()

    n_final = len(df)
    informe["filas_iniciales"] = int(n_inicial)
    informe["filas_finales"] = int(n_final)
    informe["filas_eliminadas"] = int(n_inicial - n_final)

    return df.reset_index(drop=True), informe


# =============================================================================
# 9. SCORE DE INTERÉS
# =============================================================================

def calcular_score_evento(df):
    """
    Score por evento de escucha.
    Sin duración real del track, se basa en señales observables.
    Saturación a 4 minutos para normalizar segundos_reproducidos.
    """
    segundos_norm = np.clip(df["segundos_reproducidos"] / 240, 0, 1)

    df["score_evento_interes"] = (
        0.35 * segundos_norm +
        0.25 * df["escucha_valida"] +
        0.20 * df["fin_natural"] +
        0.10 * (1 - df["skip_temprano"]) +
        0.10 * (1 - df["saltada"])
    ).clip(0, 1)

    return df

# =============================================================================
# 10. TABLAS FINALES
# =============================================================================

def construir_tabla_escuchas(df):
    """
    [B9-FIX] Se añade "flag_timestamp_invalido" a la lista de columnas de salida.
    En el código original se calculaba en crear_variables_temporales pero no se
    incluía en el subset final de construir_tabla_escuchas.
    Como ahora la creación del flag es parte del log y el filtrado, se añade
    una columna constante 0 (todos los registros que llegan aquí son válidos).
    """
    df = df.copy().reset_index(drop=True)
    df["escucha_id"] = ["E_" + str(i).zfill(10) for i in range(1, len(df) + 1)]

    # Los registros que llegan aquí ya tienen timestamp válido (filtrado previo)
    df["flag_timestamp_invalido"] = 0

    columnas = [
        "escucha_id", "persona_id", "archivo_origen",
        "fecha_finalizacion_utc", "fecha_finalizacion_local",
        "fecha", "anio", "mes", "dia", "trimestre", "semana_del_anio",
        "dia_semana", "nombre_dia_semana", "hora", "periodo_dia", "estacion",
        "fin_de_semana", "es_laborable",
        "pais_conexion", "plataforma",
        "track_uri", "track_id", "track_clave",
        "artista_clave", "album_clave",
        "nombre_cancion", "nombre_artista", "nombre_album",
        "milisegundos_reproducidos", "segundos_reproducidos", "minutos_reproducidos",
        "duracion_track_ms", "duracion_relativa_escucha", "completa_aprox",
        "razon_inicio", "razon_fin",
        "inicio_manual", "salto_manual", "fin_natural",
        "reproduccion_aleatoria", "saltada", "reproduccion_offline",
        "skip_temprano", "escucha_valida",
        "score_evento_interes",
        "anomalia_duracion_extrema",
        "flag_timestamp_invalido", "flag_ms_played_invalido",
        "flag_track_uri_invalida", "flag_track_metadata_incompleta"
    ]
    columnas = [c for c in columnas if c in df.columns]
    return df[columnas].copy()


def construir_tabla_tracks(df):
    base_cols = [
        "track_clave", "track_id", "track_uri",
        "nombre_cancion", "nombre_artista", "nombre_album"
    ]
    base_cols = [c for c in base_cols if c in df.columns]

    # Ordenar para que drop_duplicates keep="first" sea determinista
    df_tracks = (
        df[base_cols]
        .sort_values("track_clave")
        .drop_duplicates(subset=["track_clave"], keep="first")
        .reset_index(drop=True)
    )

    agg = (
        df.groupby("track_clave")
        .agg(
            reproducciones_totales=("track_clave", "count"),
            usuarios_unicos=("persona_id", "nunique"),
            minutos_totales=("minutos_reproducidos", "sum"),
            score_medio=("score_evento_interes", "mean"),
            pct_saltada=("saltada", "mean"),
            pct_skip_temprano=("skip_temprano", "mean"),
            pct_escucha_valida=("escucha_valida", "mean"),
            pct_fin_natural=("fin_natural", "mean"),
            primera_escucha=("fecha_finalizacion_utc", "min"),
            ultima_escucha=("fecha_finalizacion_utc", "max"),
        )
        .reset_index()
    )

    df_tracks = df_tracks.merge(agg, on="track_clave", how="left")
    return df_tracks


def construir_tabla_artistas(df):
    """
    [B7-FIX] La lambda llamaba x.dropna() dos veces. Simplificado con una sola llamada.
    """
    def primer_valor_no_nulo(x):
        valores = x.dropna()
        return valores.iloc[0] if len(valores) > 0 else np.nan

    df_artistas = (
        df.groupby("artista_clave")
        .agg(
            nombre_artista=("nombre_artista", primer_valor_no_nulo),
            reproducciones_totales=("track_clave", "count"),
            tracks_unicos=("track_clave", "nunique"),
            usuarios_unicos=("persona_id", "nunique"),
            minutos_totales=("minutos_reproducidos", "sum"),
            score_medio=("score_evento_interes", "mean"),
            primera_escucha=("fecha_finalizacion_utc", "min"),
            ultima_escucha=("fecha_finalizacion_utc", "max"),
        )
        .reset_index()
    )
    return df_artistas


def construir_tabla_usuario_track(df):
    """
    [B5-FIX] normalizar_por_usuario usaba asignación directa sobre un slice del
    groupby (grupo["score_interes"] = ...). En pandas >= 1.5 esto genera
    SettingWithCopyWarning, y en pandas 3.x con Copy-on-Write puede no propagarse
    la asignación. Corregido usando .assign() que devuelve una copia nueva.

    [B6-FIX] dias_activos_track usaba "nunique" como string en named aggregation.
    Aunque funciona, se hace explícito con pd.Series.nunique para mayor claridad
    y compatibilidad.
    """
    def primer_valor_no_nulo(x):
        valores = x.dropna()
        return valores.iloc[0] if len(valores) > 0 else np.nan

    agg = (
        df.groupby(["persona_id", "track_clave"])
        .agg(
            track_id=("track_id", primer_valor_no_nulo),
            track_uri=("track_uri", primer_valor_no_nulo),
            nombre_cancion=("nombre_cancion", primer_valor_no_nulo),
            nombre_artista=("nombre_artista", primer_valor_no_nulo),
            nombre_album=("nombre_album", primer_valor_no_nulo),
            num_reproducciones=("track_clave", "count"),
            minutos_totales=("minutos_reproducidos", "sum"),
            segundos_totales=("segundos_reproducidos", "sum"),
            score_evento_medio=("score_evento_interes", "mean"),
            n_saltadas=("saltada", "sum"),
            n_skip_temprano=("skip_temprano", "sum"),
            n_escuchas_validas=("escucha_valida", "sum"),
            n_fin_natural=("fin_natural", "sum"),
            primera_escucha=("fecha_finalizacion_utc", "min"),
            ultima_escucha=("fecha_finalizacion_utc", "max"),
            # [B6-FIX] Uso de función explícita para fecha (objeto date)
            dias_activos_track=("fecha", pd.Series.nunique),
        )
        .reset_index()
    )

    agg["proporcion_saltadas"] = agg["n_saltadas"] / agg["num_reproducciones"]
    agg["proporcion_skip_temprano"] = agg["n_skip_temprano"] / agg["num_reproducciones"]
    agg["proporcion_escucha_valida"] = agg["n_escuchas_validas"] / agg["num_reproducciones"]
    agg["proporcion_fin_natural"] = agg["n_fin_natural"] / agg["num_reproducciones"]

    agg["repeat_factor"] = (np.log1p(agg["num_reproducciones"]) / np.log(11)).clip(0, 1)

    agg["score_interes_raw"] = (
        0.35 * agg["repeat_factor"] +
        0.25 * agg["score_evento_medio"] +
        0.20 * agg["proporcion_escucha_valida"] +
        0.15 * agg["proporcion_fin_natural"] +
        0.05 * (1 - agg["proporcion_skip_temprano"])
    ).clip(0, 1)

    # [B5-FIX] En pandas 3.x, groupby().apply() elimina la columna de agrupación
    # (persona_id) del resultado, causando KeyError en pasos posteriores.
    # Solución: usar transform(), que opera columna a columna y preserva el
    # índice y todas las columnas del DataFrame original.
    min_score = agg.groupby("persona_id")["score_interes_raw"].transform("min")
    max_score = agg.groupby("persona_id")["score_interes_raw"].transform("max")
    rango = (max_score - min_score).replace(0, np.nan)
    agg["score_interes"] = ((agg["score_interes_raw"] - min_score) / rango).fillna(0.5)
    agg = agg.drop(columns=["score_interes_raw"])

    return agg.reset_index(drop=True)


def construir_tabla_usuarios_resumen(df, df_usuario_track):
    resumen = (
        df.groupby("persona_id")
        .agg(
            total_escuchas=("track_clave", "count"),
            tracks_unicos=("track_clave", "nunique"),
            artistas_unicos=("artista_clave", "nunique"),
            albums_unicos=("album_clave", "nunique"),
            minutos_totales_escuchados=("minutos_reproducidos", "sum"),
            segundos_totales_escuchados=("segundos_reproducidos", "sum"),
            dias_activos=("fecha", pd.Series.nunique),
            anios_activo=("anio", "nunique"),
            fecha_primera_escucha=("fecha_finalizacion_utc", "min"),
            fecha_ultima_escucha=("fecha_finalizacion_utc", "max"),
            pct_saltada=("saltada", "mean"),
            pct_skip_temprano=("skip_temprano", "mean"),
            pct_escucha_valida=("escucha_valida", "mean"),
            pct_fin_natural=("fin_natural", "mean"),
            pct_shuffle=("reproduccion_aleatoria", "mean"),
            pct_offline=("reproduccion_offline", "mean"),
            hora_media=("hora", "mean"),
            score_evento_medio=("score_evento_interes", "mean"),
        )
        .reset_index()
    )

    score_medio = (
        df_usuario_track.groupby("persona_id")["score_interes"]
        .mean()
        .reset_index()
        .rename(columns={"score_interes": "score_interes_medio"})
    )

    resumen = resumen.merge(score_medio, on="persona_id", how="left")

    resumen["escuchas_por_dia_activo"] = (
        resumen["total_escuchas"] / resumen["dias_activos"].replace(0, np.nan)
    )
    resumen["minutos_por_dia_activo"] = (
        resumen["minutos_totales_escuchados"] / resumen["dias_activos"].replace(0, np.nan)
    )
    resumen["diversidad_tracks"] = (
        resumen["tracks_unicos"] / resumen["total_escuchas"].replace(0, np.nan)
    )
    resumen["diversidad_artistas"] = (
        resumen["artistas_unicos"] / resumen["total_escuchas"].replace(0, np.nan)
    )

    return resumen


def construir_matriz_usuario_track(df_usuario_track):
    """
    Devuelve la matriz sin reset_index() para que persona_id sea el índice real.
    Si necesitas exportarla como CSV, usa reset_index() en el paso de guardado.
    """
    matriz = df_usuario_track.pivot_table(
        index="persona_id",
        columns="track_clave",
        values="score_interes",
        fill_value=0
    )
    return matriz  # índice = persona_id, columnas = track_clave


def construir_preferencias_periodo_dia(df):
    out = (
        df.groupby(["persona_id", "periodo_dia"])
        .agg(
            escuchas=("track_clave", "count"),
            minutos=("minutos_reproducidos", "sum"),
            tracks_unicos=("track_clave", "nunique"),
            score_medio=("score_evento_interes", "mean")
        )
        .reset_index()
    )
    return out


def construir_preferencias_dia_semana(df):
    out = (
        df.groupby(["persona_id", "nombre_dia_semana"])
        .agg(
            escuchas=("track_clave", "count"),
            minutos=("minutos_reproducidos", "sum"),
            tracks_unicos=("track_clave", "nunique"),
            score_medio=("score_evento_interes", "mean")
        )
        .reset_index()
    )
    return out


def construir_preferencias_contexto_track(df):
    """Útil para recomendación contextual por franja horaria y día."""
    out = (
        df.groupby(["persona_id", "track_clave", "periodo_dia", "nombre_dia_semana"])
        .agg(
            reproducciones=("track_clave", "count"),
            minutos=("minutos_reproducidos", "sum"),
            score_medio=("score_evento_interes", "mean")
        )
        .reset_index()
    )
    return out

@st.cache_data
def limpieza_datos(df, nombre):    # Limpieza base
    df = limpiar_y_renombrar_columnas(df)
    df = normalizar_columnas(df)

    # Tiempo
    df = crear_variables_temporales(df)

    # Variables de escucha
    df = crear_variables_escucha(df)

    # IDs analíticos
    df = crear_ids_analiticos(df)

    # Limpieza final
    df, informe_limpieza = limpiar_registros(df)

    # Score evento
    df = calcular_score_evento(df)
   
    df["persona_id"] = nombre
    
    return df