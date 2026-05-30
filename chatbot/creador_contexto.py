import pandas as pd
from datetime import datetime

# Importamos los módulos de géneros que hemos creado
from chatbot.cargar_generos import cargar_csv_generos
from chatbot.tratamiento_generos import enriquecer_con_generos

# CARGA DEL CSV DE GÉNEROS (se hace una sola vez al importar)

_RUTA_CSV_GENEROS = "data/canciones_clasificadas.csv"

_df_generos = None


def _get_df_generos() -> pd.DataFrame:
    """
    Carga el CSV de géneros la primera vez y lo guarda en memoria.
    Las llamadas siguientes reutilizan el DataFrame ya cargado.
    """
    global _df_generos
    if _df_generos is None:
        try:
            _df_generos = cargar_csv_generos(_RUTA_CSV_GENEROS)
        except FileNotFoundError:
            # Si el CSV no está, el chatbot sigue funcionando sin géneros
            _df_generos = pd.DataFrame()
    return _df_generos


# ─────────────────────────────────────────────────────────────
# UTILIDAD: convertir hora a periodo del día
# ─────────────────────────────────────────────────────────────

def _hora_a_periodo(hora: int) -> str:
    """Convierte una hora del día (0-23) en el periodo correspondiente."""
    if 6 <= hora < 13:
        return "mañana"
    elif 13 <= hora < 20:
        return "tarde"
    elif 20 <= hora < 24:
        return "noche"
    else:
        return "madrugada"


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: construir contexto de un usuario
# ─────────────────────────────────────────────────────────────

def build_user_context(data: dict, persona_id: str,
                       hora_actual: int = None,
                       dia_semana: str = None) -> str:
    """
    Construye un resumen textual completo del perfil del usuario
    para enviarlo al LLM como contexto.

    Incluye:
    - Estadísticas generales de escucha
    - Top artistas y canciones
    - Hábitos temporales
    - Géneros, moods y características musicales (si hay datos)

    Args:
        data: diccionario con los DataFrames del proyecto
        persona_id: nombre del usuario activo
        hora_actual: hora del día (0-23). Si None, usa la hora actual.
        dia_semana: nombre del día en español. Si None, usa el día actual.

    Returns:
        String con el contexto completo listo para el LLM.
    """
    # Valores por defecto: hora y día actuales
    if hora_actual is None:
        hora_actual = datetime.now().hour
    if dia_semana is None:
        dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        dia_semana = dias_es[datetime.now().weekday()]

    context_parts = []

    #  1. Perfil general del usuario 
    if "usuarios_resumen" in data:
        df = data["usuarios_resumen"]
        usuario = df[df["persona_id"] == persona_id]
        if not usuario.empty:
            u = usuario.iloc[0]
            context_parts.append(f"""PERFIL GENERAL DE {persona_id}:
- Total escuchas registradas: {int(u['total_escuchas']):,}
- Artistas únicos escuchados: {int(u['artistas_unicos'])}
- Canciones únicas escuchadas: {int(u['tracks_unicos'])}
- Minutos totales escuchados: {u['minutos_totales_escuchados']:.0f}
- Hora media de escucha: {u['hora_media']:.1f}h
- Score de interés medio: {u['score_interes_medio']:.3f} (de 0 a 1)
- Porcentaje de canciones en shuffle: {u['pct_shuffle']*100:.1f}%
- Porcentaje de canciones completadas: {u['pct_fin_natural']*100:.1f}%
- Porcentaje de canciones saltadas: {u['pct_saltada']*100:.1f}%""")

    # 2. Top 10 artistas por minutos 
    if "artistas" in data:
        df = data["artistas"]
        top = (df[df["persona_id"] == persona_id]
               .sort_values("minutos_totales", ascending=False)
               .head(10))
        if not top.empty:
            lista = "\n".join(
                f"  {i+1}. {r['nombre_artista']} ({r['minutos_totales']:.0f} min)"
                for i, (_, r) in enumerate(top.iterrows())
            )
            context_parts.append(f"TOP 10 ARTISTAS POR MINUTOS ESCUCHADOS:\n{lista}")

    #  3. Top 10 canciones por score de interés
    if "usuario_track" in data:
        df = data["usuario_track"]
        top = (df[df["persona_id"] == persona_id]
               .sort_values("score_interes", ascending=False)
               .head(10))
        if not top.empty:
            lista = "\n".join(
                f"  {i+1}. {r['nombre_cancion']} — {r['nombre_artista']} (score: {r['score_interes']:.3f})"
                for i, (_, r) in enumerate(top.iterrows())
            )
            context_parts.append(f"TOP 10 CANCIONES CON MAYOR INTERÉS:\n{lista}")

    #  4. Hábito por periodo del día actual 
    if "preferencias_periodo_dia" in data:
        df = data["preferencias_periodo_dia"]
        periodo_actual = _hora_a_periodo(hora_actual)
        pref = df[(df["persona_id"] == persona_id) & (df["periodo_dia"] == periodo_actual)]
        if not pref.empty:
            p = pref.iloc[0]
            context_parts.append(
                f"HÁBITO EN {periodo_actual.upper()} (ahora son las {hora_actual}h): "
                f"suele escuchar {int(p['escuchas'])} canciones, "
                f"con score medio de {p['score_medio']:.3f}"
            )

    # ── 5. Hábito por día de la semana ──────────────────────────
    if "preferencias_dia_semana" in data:
        df = data["preferencias_dia_semana"]
        pref = df[(df["persona_id"] == persona_id) & (df["nombre_dia_semana"] == dia_semana)]
        if not pref.empty:
            d = pref.iloc[0]
            context_parts.append(
                f"HÁBITO LOS {dia_semana.upper()}: "
                f"suele escuchar {int(d['escuchas'])} canciones "
                f"(score medio: {d['score_medio']:.3f})"
            )

    # 6. Géneros, moods y características musicales 
    # Esta es la parte nueva: cruzamos con el CSV externo
    if "usuario_track" in data:
        df_generos = _get_df_generos()

        if not df_generos.empty:
            resumen_generos = enriquecer_con_generos(
                df_usuario_track=data["usuario_track"],
                df_generos=df_generos,
                persona_id=persona_id
            )
            if resumen_generos:
                context_parts.append(resumen_generos)

    return "\n\n".join(context_parts)


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PARA RECOMENDACIONES GRUPALES
# ─────────────────────────────────────────────────────────────

def build_multi_user_context(data: dict, personas: list) -> str:
    """
    Construye el contexto combinado de varios usuarios
    para recomendaciones grupales.

    Args:
        data: diccionario con los DataFrames del proyecto
        personas: lista de nombres de usuario

    Returns:
        String con los perfiles de todos los usuarios.
    """
    parts = []
    for persona in personas:
        parts.append(f"{'='*50}")
        parts.append(f"PERFIL DE {persona.upper()}:")
        parts.append(build_user_context(data, persona))

    parts.append(f"{'='*50}")
    parts.append(
        "OBJETIVO GRUPAL: Encuentra canciones o artistas que gusten a todos los usuarios.\n"
        "Prioriza géneros y moods que aparezcan en los perfiles de varios usuarios.\n"
        "Si los gustos son muy distintos, indícalo y sugiere un punto medio."
    )
    return "\n\n".join(parts)
