import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Data Wrapped", layout="wide")
st.title("📊 Data Wrapped — Mini Wrapped Interactivo")

# Subida del CSV
uploaded_file = st.file_uploader("Sube tu archivo CSV")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("## 🎵 Data Wrapped Dashboard")
        st.markdown("---")
        page = st.radio("📊 Sección", [
            "🏆 Wrapped", "🎵 Top 5", "📈 Evolución Temporal",
            "🎸 Géneros", "👥 Comparativa", "🎯 Recomendaciones"
        ])
        st.markdown("---")
        st.markdown("<p style='color:#666;font-size:0.75rem;text-align:center'>TFM · Análisis de Datos</p>", unsafe_allow_html=True)
    
    # --- Contenido según página ---
    if page == "🏆 Wrapped":
        st.subheader("Vista previa de los datos")
        st.dataframe(df.head())

        st.subheader("Estadísticas básicas")
        st.write(df.describe())

        st.subheader("Insights rápidos")
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        if num_cols:
            max_col = df[num_cols].mean().idxmax()
            st.write(f"- La variable con mayor media es **{max_col}**: {df[max_col].mean():.2f}")
            min_col = df[num_cols].mean().idxmin()
            st.write(f"- La variable con menor media es **{min_col}**: {df[min_col].mean():.2f}")

        if cat_cols:
            for c in cat_cols:
                top_value = df[c].value_counts().idxmax()
                st.write(f"- En **{c}**, la categoría más frecuente es **{top_value}**")
    
    elif page == "🎵 Top 5":
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        if cat_cols:
            st.subheader("Top categorías (Top 5)")
            for c in cat_cols:
                top5 = df[c].value_counts().nlargest(5)
                fig = px.bar(top5, x=top5.index, y=top5.values, title=f"Top 5 de {c}")
                st.plotly_chart(fig, use_container_width=True)

    elif page == "📈 Evolución Temporal":
        st.write("Aquí puedes poner tus gráficos de evolución temporal por mes o fecha")

    elif page == "🎸 Géneros":
        st.write("Aquí podrías poner análisis por categorías especiales, como 'Géneros'")

    elif page == "👥 Comparativa":
        st.write("Comparativa entre usuarios, meses o categorías")

    elif page == "🎯 Recomendaciones":
        st.write("Recomendaciones automáticas basadas en tus datos")
