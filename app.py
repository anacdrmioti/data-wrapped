import streamlit as st
import datetime
from preparacion_datos.pipeline_limpieza_datos import pipeline_carga_y_limpieza_datos
from preparacion_datos.limpieza_datos import construir_tabla_tracks, construir_tabla_artistas, construir_tabla_usuario_track, construir_tabla_usuarios_resumen, construir_preferencias_periodo_dia, construir_preferencias_dia_semana, construir_preferencias_contexto_track, construir_tabla_escuchas, construir_matriz_usuario_track
from wrapped.visualizaciones import visualizacion_artistas


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
        if st.button("🎤 Karaoke", use_container_width=True):
            st.session_state.pagina = "karaoke"
            st.rerun()

    with col4:
        if st.button("🤖 Chatbot", use_container_width=True):
            st.session_state.pagina = "chatbot"
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
        st.markdown("## Métricas Generales")

    elif st.session_state.seccion_wrapped == "Artistas":
        st.markdown("## 🎤 Métricas de Artistas")
        visualizacion_artistas(st.session_state.df_artistas)

    elif st.session_state.seccion_wrapped == "Canciones":
        st.markdown("## 🎧 Métricas de Canciones")

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
    Además, el sistema va a tener en cuenta tu estado de ánimo actual. En la siguiente pantalla se te harán algunas preguntas sencillas sobre cómo te sientes o qué tipo de música te apetece escuchar en este momento, con el objetivo de ajustar aún más las recomendaciones a tu contexto actual.
    """)

    if st.button("Ir al recomendador personal"):
        st.session_state.pagina = "recomendador_personal"
        st.session_state.fecha_inicio_recomendador_personal = fecha_inicio
        st.session_state.fecha_fin_recomendador_personal = fecha_fin
        st.session_state.generacion_tablas_recomendador_personal = True
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

            st.session_state.generacion_tablas_recomendador_personal = False

            st.rerun()

    col1, col2, col3 = st.columns([6, 2, 2])

    with col1:
        st.markdown("## 🎯 Recomendador Personal")

    with col2:
        if st.button("⬅️ Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()
    
    with col3:
        if st.button("⬅️ Configuración"):
            st.session_state.pagina = "recomendadores_config"
            st.rerun()
    
    print(st.session_state.df_tracks_recomendador.head())
    print(st.session_state.df_pref_contexto_track_recomendador.head())
        
