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
            st.session_state.pagina = "wrapped"
            st.rerun() 

    with col2:
        if st.button("🎯 Recomendador", use_container_width=True):
            st.session_state.pagina = "recomendador"
            st.rerun()

    with col3:
        if st.button("🎤 Karaoke", use_container_width=True):
            st.session_state.pagina = "karaoke"
            st.rerun()

    with col4:
        if st.button("🤖 Chatbot", use_container_width=True):
            st.session_state.pagina = "chatbot"
            st.rerun()

# ------------------ PANTALLA WRAPPED ------------------
elif st.session_state.pagina == "wrapped":

    df = st.session_state.data_procesada

    col1, col2 = st.columns([6, 2])

    with col1:
        st.markdown("## 📊 Spotify Wrapped")

    with col2:
        st.write("")  # ayuda a alinear
        if st.button("⬅️Menú principal"):
            st.session_state.pagina = "app"
            st.rerun()

    st.markdown("#### 📅 Filtrar por fechas")

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    rango_fechas = st.date_input(
        "Selecciona un rango de fechas",
        value=(fecha_min, fecha_max)
    )

    if len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas

        df_filtrado = df[
            (df["fecha"] >= fecha_inicio) &
            (df["fecha"] <= fecha_fin)
        ]

    else:
        df_filtrado = df
    
    df_tracks = construir_tabla_tracks(df_filtrado)
    df_artistas = construir_tabla_artistas(df_filtrado)
    df_usuario_track = construir_tabla_usuario_track(df_filtrado)
    df_usuarios_resumen = construir_tabla_usuarios_resumen(df_filtrado, df_usuario_track)
    df_pref_periodo = construir_preferencias_periodo_dia(df_filtrado)
    df_pref_dia = construir_preferencias_dia_semana(df_filtrado)
    df_pref_contexto_track = construir_preferencias_contexto_track(df_filtrado)
    df_escuchas = construir_tabla_escuchas(df_filtrado)
    df_matriz_usuario_track = construir_matriz_usuario_track(df_usuario_track)

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
        visualizacion_artistas(df_artistas)

    elif st.session_state.seccion_wrapped == "Canciones":
        st.markdown("## 🎧 Métricas de Canciones")

    elif st.session_state.seccion_wrapped == "Generos":
        st.markdown("## 🎼 Métricas de Géneros")
    
    elif st.session_state.seccion_wrapped == "Tipo_oyente":
        st.markdown("## 🎯 Tipo de oyente")