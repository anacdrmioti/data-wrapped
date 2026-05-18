import streamlit as st
import datetime
from preparacion_datos.pipeline_limpieza_datos import pipeline_carga_y_limpieza_datos
from preparacion_datos.limpieza_datos import construir_tabla_tracks, construir_tabla_artistas, construir_tabla_usuario_track, construir_tabla_usuarios_resumen, construir_preferencias_periodo_dia, construir_preferencias_dia_semana, construir_preferencias_contexto_track, construir_tabla_escuchas, construir_matriz_usuario_track
from recomendador.recomendador_personal import generador_embeddings_canciones, recomendador_historico_escuchas
from recomendador.codificador_canciones import song_to_text
from wrapped.Wrapped_artistas_def import render_artistas_wrapped
from wrapped.Wrapped_metricasgral import render_metricas_generales
from wrapped.Wrapped_canciones_def import render_canciones_wrapped
from karaoke.karaoke_ui import render_karaoke

import pandas as pd


if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

# ------------------ PANTALLA INICIO ------------------
if st.session_state.pagina == "inicio":

    st.markdown("## 🎧 Spotify Analyzer")

    nombre = st.text_input("Introduce tu nombre")
    uploaded_file = st.file_uploader(
        "Sube tu archivo ZIP con los datos de Spotify Wrapped",
        type=["zip"]
    )

    if st.button("Continuar"):
        if nombre and uploaded_file:
            st.session_state.nombre = nombre
            st.session_state.zip = uploaded_file
            st.session_state.pagina = "app"
            st.rerun()
        else:
            st.warning("Completa todos los campos ⚠️")

# ------------------ PANTALLA APP ------------------
elif st.session_state.pagina == "app":

    if "data_procesada" not in st.session_state:

        zip_file = st.session_state.zip

        with st.status(" Realizando el preprocesamiento de los datos...", expanded=True) as status:
    
            st.write("📦 Descomprimiendo archivo...")
            st.write("🧹 Limpiando datos...")
            
            st.session_state.data_procesada = pipeline_carga_y_limpieza_datos(
                zip_file,
                st.session_state.nombre
            )

            status.update(label="Datos procesados correctamente ✅", state="complete")

    st.markdown(f"## Bienvenido, {st.session_state.nombre} 🎧")

    st.markdown("### ¿Qué quieres hacer?")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        if st.button("📊 Wrapped", use_container_width=True):
            st.session_state.pagina = "wrapped_config"
            st.rerun() 

    with col2:
        if st.button("🎯 Recomendador", use_container_width=True):
            st.session_state.pagina = "recomendadores_config"
            st.rerun()


    with col3:
        if st.button("🤖 Chatbot", use_container_width=True):
            st.session_state.pagina = "chatbot"
            st.rerun()

    with col4:
        if st.button("🎤 Karaoke", use_container_width=True):
            st.session_state.pagina = "karaoke"
            st.rerun()


# ------------------ PANTALLA WRAPPED CONFIG ------------------
elif st.session_state.pagina == "wrapped_config":

    st.markdown("## 📊 Spotify Wrapped")

    st.markdown("""
    En esta sección podrás explorar tus métricas personalizadas de Spotify Wrapped basadas en tu historial de escucha.
                
    Como vas a observar en siguiente pantalla, en la parte superior vas a poder seleccionar un rango de fechas para filtrar tu historial de escucha. Esto permitirá que las estadísticas y visualizaciones se basen únicamente en el periodo de tiempo que desees analizar (por ejemplo, el último año o los últimos meses).

    Si no seleccionas un rango de fechas, se mostrarán las métricas basadas en todo tu historial de escucha disponible.
                
    En cualquier momento que lo desees, podrás ajustar este filtro de las fechas. Y se te volverán a generar todas las métricas y visualizaciones basadas en el nuevo rango de fechas que hayas seleccionado.
    """)

    if st.button("Ir a Spotify Wrapped"):
        st.session_state.pagina = "wrapped"
        st.rerun()

# ------------------ PANTALLA WRAPPED ------------------
elif st.session_state.pagina == "wrapped":
    
    df = st.session_state.data_procesada

    if "fecha_inicio_wrapped" not in st.session_state:
        st.session_state.fecha_inicio_wrapped = df["fecha"].min()
        st.session_state.fecha_fin_wrapped = df["fecha"].max()
        st.session_state.generacion_tablas_wrapped = True
    
    print(st.session_state.generacion_tablas_wrapped)

    if st.session_state.generacion_tablas_wrapped == True:

        with st.status(" Generando todas las tablas necesarias con el filtrado de fechas establecido...", expanded=True) as status:

            fecha_inicio = st.session_state.fecha_inicio_wrapped
            fecha_fin = st.session_state.fecha_fin_wrapped

            df_filtrado = df[
                (df["fecha"] >= fecha_inicio) &
                (df["fecha"] <= fecha_fin)
            ]

            st.session_state.df_tracks = construir_tabla_tracks(df_filtrado)
            st.write("Tabla de tracks generada ✅")

            st.session_state.df_artistas = construir_tabla_artistas(df_filtrado)
            st.write("Tabla de artistas generada ✅")

            st.session_state.df_usuario_track = construir_tabla_usuario_track(df_filtrado)
            st.write("Tabla usuario-track generada ✅")

            st.session_state.df_usuarios_resumen = construir_tabla_usuarios_resumen(df_filtrado, st.session_state.df_usuario_track)
            st.write("Tabla de resumen de usuario generada ✅")

            st.session_state.df_pref_periodo = construir_preferencias_periodo_dia(df_filtrado)
            st.write("Tabla de preferencias por periodo del día generada ✅")

            st.session_state.df_pref_dia = construir_preferencias_dia_semana(df_filtrado)
            st.write("Tabla de preferencias por día de la semana generada ✅")

            st.session_state.df_pref_contexto_track = construir_preferencias_contexto_track(df_filtrado)
            st.write("Tabla de preferencias por contexto de escucha generada ✅")

            st.session_state.df_escuchas = construir_tabla_escuchas(df_filtrado)
            st.write("Tabla de escuchas generada ✅")

            # df_matriz_usuario_track = construir_matriz_usuario_track(df_usuario_track) Esta creo que no es necesaria pq es igual que la de df_usuario_track

            st.session_state.generacion_tablas_wrapped = False

            st.rerun()

    col1, col2= st.columns([6, 2])

    with col1:
        st.markdown("## 📊 Spotify Wrapped")

    with col2:
        if st.button("⬅️ Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()
    
    st.markdown("#### 📅 Filtrar por fechas")

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.date_input(
        f"Selecciona un rango de fechas (historial disponible: {fecha_min} - {fecha_max})",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    if st.button("🔄 Actualizar métricas"):
        if len(rango_fechas) == 2:
            fecha_inicio, fecha_fin = rango_fechas
        else:
            fecha_inicio, fecha_fin = fecha_min, fecha_max

        if (st.session_state.fecha_inicio_wrapped != fecha_inicio or st.session_state.fecha_fin_wrapped != fecha_fin):

            st.session_state.fecha_inicio_wrapped = fecha_inicio
            st.session_state.fecha_fin_wrapped = fecha_fin
            st.session_state.generacion_tablas_wrapped = True

            st.rerun()   
        
    if "seccion_wrapped" not in st.session_state:
        st.session_state.seccion_wrapped = "General"
    
    with st.sidebar:

        if st.button("📊 Métricas Generales"):
            st.session_state.seccion_wrapped = "General"

        if st.button("🎤 Artistas"):
            st.session_state.seccion_wrapped = "Artistas"

        if st.button("🎧 Canciones"):
            st.session_state.seccion_wrapped = "Canciones"

        if st.button("🎼 Géneros"):
            st.session_state.seccion_wrapped = "Generos"  

        if st.button("🎯 Tipo de oyente"):
            st.session_state.seccion_wrapped = "Tipo_oyente"  
    
    
    if st.session_state.seccion_wrapped == "General":

        render_metricas_generales(
            st.session_state.df_usuarios_resumen,
            st.session_state.df_pref_periodo,
            st.session_state.df_pref_dia,
            st.session_state.df_escuchas,
            st.session_state.df_artistas,
            st.session_state.df_tracks
        )

    elif st.session_state.seccion_wrapped == "Artistas":
        st.markdown("## 🎤 Métricas de Artistas")
        render_artistas_wrapped(
            st.session_state.df_artistas,
            st.session_state.df_escuchas)

    elif st.session_state.seccion_wrapped == "Canciones":
        render_canciones_wrapped(
            st.session_state.df_tracks,
            st.session_state.df_escuchas
        )

    elif st.session_state.seccion_wrapped == "Generos":
        st.markdown("## 🎼 Métricas de Géneros")
    
    elif st.session_state.seccion_wrapped == "Tipo_oyente":
        st.markdown("## 🎯 Tipo de oyente")

elif st.session_state.pagina == "recomendadores_config":
    
    # Cargamos el dataframe procesado 
    df = st.session_state.data_procesada

    st.markdown("## 🎯 Recomendador Personal")

    st.markdown("""
    ### Instrucciones para el recomendador personal

    Este es tu recomendador personal.

    El sistema se basa exclusivamente en tu historial de música escuchada en Spotify, por lo que todas las recomendaciones están personalizadas según tu comportamiento real de escucha.

    Para construir tu perfil musical, el modelo tiene en cuenta diferentes factores como:
    - La frecuencia con la que escuchas cada canción
    - El tiempo total de reproducción
    - Si sueles saltar o finalizar las canciones
    - El comportamiento de escucha en distintos momentos del día y días de la semana

    Antes de generar las recomendaciones, puedes seleccionar un rango de fechas para filtrar tu historial. Esto permite que el sistema se base únicamente en el periodo de tiempo que desees analizar (por ejemplo, el último año o los últimos meses).

    Si deseas modificar este rango de fechas, deberás volver a esta página de configuración.
    """)

    st.markdown("#### 📅 Filtrar por fechas")

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.date_input(
        "Selecciona un rango de fechas",
        value=(fecha_min, fecha_max)
    )

    if len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas

    else:
        fecha_inicio, fecha_fin = fecha_min, fecha_max

    st.markdown("""
    Además, el sistema también tiene en cuenta tu estado de ánimo y contexto actual de escucha.

    En la siguiente pantalla podrás escribir libremente una frase sobre cómo te sientes o qué tipo de música te apetece escuchar en este momento, por ejemplo: “hoy me apetece escuchar música energética para entrenar”, “quiero algo tranquilo para estudiar” o “estoy en mood de fiesta”.

    El objetivo es ajustar aún más las recomendaciones a tu contexto inmediato, combinando tu historial musical con la intención de escucha que expreses en ese momento.
    """)

    if st.button("Ir al recomendador personal"):
        st.session_state.pagina = "recomendador_personal"
        st.session_state.fecha_inicio_recomendador_personal = fecha_inicio
        st.session_state.fecha_fin_recomendador_personal = fecha_fin
        st.session_state.generacion_tablas_recomendador_personal = True
        st.session_state.mostrar_metricas = False
        st.rerun()

elif st.session_state.pagina == "recomendador_personal":

    df = st.session_state.data_procesada
    fecha_inicio = st.session_state.fecha_inicio_recomendador_personal
    fecha_fin = st.session_state.fecha_fin_recomendador_personal

    if st.session_state.generacion_tablas_recomendador_personal == True:
        with st.status(" Generando todas las tablas necesarias con el filtrado de fechas establecido...", expanded=True) as status:

            df_filtrado = df[
                (df["fecha"] >= fecha_inicio) &
                (df["fecha"] <= fecha_fin)
            ]

            st.session_state.df_tracks_recomendador = construir_tabla_tracks(df_filtrado)
            st.write("Tabla de tracks generada ✅")

            st.session_state.df_pref_contexto_track_recomendador = construir_preferencias_contexto_track(df_filtrado)
            st.write("Tabla de preferencias por contexto de escucha generada ✅")

            path_canciones_clasificadas = "data/canciones_clasificadas.csv"
            st.session_state.df_embeddings_canciones = generador_embeddings_canciones(st.session_state.df_tracks_recomendador, path_canciones_clasificadas)
            st.write("Embeddings de canciones generados ✅")

            st.session_state.generacion_tablas_recomendador_personal = False

            st.rerun()

    col1, col2, col3 = st.columns([6, 2, 2])

    with col1:
        st.markdown("## 🎯 Generación de Playlists en función de tu estado de ánimo y del historial de reproducciones")

    with col2:
        if st.button("⬅️ Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()
    
    with col3:
        if st.button("⬅️ Configuración Fechas"):
            st.session_state.pagina = "recomendadores_config"
            st.rerun()
    
    st.subheader("🎧 Personaliza tu recomendación musical")

    if st.button("Actualizar métricas"):
        st.session_state.mostrar_metricas = True
        st.rerun()
    
    print("a")
    
    if st.session_state.mostrar_metricas:

        GENEROS = [
            "pop", "rock", "indie", "alternativo",
            "hip-hop", "rap", "trap", "drill",
            "electronic", "house", "techno", "edm",
            "reggaeton", "latin", "urbano",
            "r&b", "soul", "funk",
            "jazz", "blues",
            "classical", "instrumental",
            "folk", "acoustic", "singer-songwriter",
            "metal", "punk",
            "ambient", "lofi",
            "soundtrack", "other"
        ]

        generos_usuario = st.multiselect(
            "Selecciona géneros",
            GENEROS
        )

        MOODS = [
            "feliz", "alegre", "euforico",
            "triste", "melancolico", "nostalgico",
            "romantico", "amoroso",
            "relajado", "calmado", "chill",
            "energico", "motivador", "epico",
            "agresivo", "oscuro", "intenso",
            "sensual", "suave",
            "dramatico", "profundo",
            "divertido", "fiestero",
            "other"
        ]

        moods_usuario = st.multiselect(
            "¿Qué mood buscas?",
            MOODS
        )

        CONTEXTOS = [
            "fiesta", "discoteca",
            "gym", "entrenar",
            "estudiar", "trabajar",
            "conducir", "viajar",
            "casa", "relax",
            "noche", "madrugada",
            "mañana", "tarde",
            "verano", "invierno",
            "romance", "cita",
            "tristeza", "desamor",
            "concentracion",
            "social", "amigos",
            "other"
        ]

        contextos_usuario = st.multiselect(
            "¿En qué contexto escucharás música?",
            CONTEXTOS
        )

        st.markdown("### ⚡ Características musicales")

        energia_usuario = st.slider(
            "Nivel de energía",
            min_value=0.0,
            max_value=1.0,
            value=0.5
        )

        danceability_usuario = st.slider(
            "Nivel de baile",
            min_value=0.0,
            max_value=1.0,
            value=0.5
        )

        valencia_usuario = st.slider(
            "Valencia emocional",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = triste/melancólico · 1 = alegre/feliz"
        )

        instrumentalidad_usuario = st.slider(
            "Nivel instrumental",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = canciones centradas en la voz · 1 = canciones centradas en la instrumentación"
        )

        intensidad_usuario = st.slider(
            "Intensidad emocional",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0 = suave/relajado · 1 = intenso/explosivo"
        )
        
        idioma_usuario = st.multiselect(
            "Idioma",
            ["espanol", "ingles", "frances", "coreano", "japones"],
            help="Filtra canciones por idioma"
        )

        if st.button("Obtener mi playlist personalizada"):

            query = song_to_text(
                moods_usuario,
                generos_usuario,
                contextos_usuario,
                energia_usuario,
                valencia_usuario,
                danceability_usuario,
                instrumentalidad_usuario,
                intensidad_usuario
            )

            recomendaciones_historico = recomendador_historico_escuchas(
                query,
                idioma_usuario,
                st.session_state.df_tracks_recomendador,
                st.session_state.df_embeddings_canciones
            )

            # Guardamos recomendaciones
            st.session_state.recomendaciones_historico = recomendaciones_historico
        
            st.session_state.mostrar_metricas = False
            st.rerun()


    # Mostrar playlist si existe
    if "recomendaciones_historico" in st.session_state:

        st.markdown("## 🎧 Tu playlist recomendada")

        for i, row in enumerate(st.session_state.recomendaciones_historico.itertuples(), 1):

            with st.container(border=True):

                col1, col2, col3 = st.columns([5, 1, 1])

                with col1:
                    st.markdown(
                        f"""
                        ### {i}. {row.nombre_cancion}
                        **{row.nombre_artista}**
                        """
                    )

                with col2:
                    st.metric(
                        label="Score",
                        value=f"{row.score_recomendacion:.3f}"
                    )

                with col3:

                    if st.button("▶️", key=f"play_{i}"):

                        st.session_state.cancion_karaoke = {
                            "cancion": row.nombre_cancion,
                            "artista": row.nombre_artista
                        }

                        st.session_state.pagina = "karaoke_recomendacion"

                        st.rerun()

elif st.session_state.pagina == "karaoke_recomendacion":

    col1, col2, col3 = st.columns([6, 2, 2])

    with col1:
        st.markdown("## Karoke de tu canción recomendada")

    with col2:
        if st.button("⬅️ Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()
    
    with col3:
        if st.button("⬅️ Recomendaciones canciones"):
            st.session_state.pagina = "recomendador_personal"
            st.rerun()


    render_karaoke(
        st.session_state.cancion_karaoke["cancion"],
        st.session_state.cancion_karaoke["artista"]
    )
                       


# ------------------ PANTALLA CHATBOT ------------------
elif st.session_state.pagina == "chatbot":
 
    if st.button("← Volver"):
        st.session_state.pagina = "app"
        st.rerun()
 
    from chatbot.chatbot_ui import render_chatbot
    from preparacion_datos.limpieza_datos import (
        construir_tabla_artistas,
        construir_tabla_usuario_track,
        construir_tabla_usuarios_resumen,
        construir_preferencias_periodo_dia,
        construir_preferencias_dia_semana,
    )
 
    # Construir el dict de tablas si no está ya en sesión
    if "data_chatbot" not in st.session_state:
        with st.spinner("Preparando datos para el chatbot..."):
            df_raw = st.session_state.data_procesada
 
            df_ut = construir_tabla_usuario_track(df_raw)
            df_art = construir_tabla_artistas(df_raw)
            df_res = construir_tabla_usuarios_resumen(df_raw, df_ut)
            df_per = construir_preferencias_periodo_dia(df_raw)
            df_dia = construir_preferencias_dia_semana(df_raw)
 
            # Tabla de artistas desglosada por persona_id para el chatbot.
            # df_art agrupa solo por artista (sin persona_id), así que la
            # construimos desde df_raw directamente.
            def _primer_valor(x):
                v = x.dropna()
                return v.iloc[0] if len(v) > 0 else None
 
            df_art_chatbot = (
                df_raw.groupby(["persona_id", "artista_clave"])
                .agg(
                    nombre_artista=("nombre_artista", _primer_valor),
                    minutos_totales=("minutos_reproducidos", "sum"),
                    reproducciones_totales=("track_clave", "count"),
                )
                .reset_index()
            )
 
            st.session_state.data_chatbot = {
                "usuario_track": df_ut,
                "artistas": df_art_chatbot,  # ← sustituido, ahora tiene persona_id
                "usuarios_resumen": df_res,
                "preferencias_periodo_dia": df_per,
                "preferencias_dia_semana": df_dia,
            }
 
    render_chatbot(st.session_state.data_chatbot, st.session_state.nombre)

# ------------------ PANTALLA KARAOKE ------------------
elif st.session_state.pagina == "karaoke":
    st.markdown("""
    <style>
    .lyric-box {
        background: black; padding: 30px; border-radius: 20px; 
        border: 3px solid #1DB954; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("## 🎤 Karaoke")
    with col2:
        if st.button("⬅️ Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        cancion = st.text_input("🎵 Canción", placeholder="Ej: Ni borracho")
    with col2:
        artista = st.text_input("🎤 Artista", placeholder="Ej: Quevedo")

    if st.button("🚀 PREPARAR ESCENARIO"):
        render_karaoke(cancion, artista)