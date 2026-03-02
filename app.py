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
    
    st.subheader("Vista previa de los datos")
    st.dataframe(df.head())
    
    # Estadísticas básicas
    st.subheader("Estadísticas básicas")
    st.write(df.describe())

    # Detectar columnas numéricas y categóricas
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(include='object').columns.tolist()

    # Gráficas automáticas de columnas numéricas
    if num_cols:
        st.subheader("Gráficas de variables numéricas")
        col_num = st.selectbox("Selecciona columna para gráfica", num_cols)
        fig = px.histogram(df, x=col_num, nbins=20, title=f"Distribución de {col_num}")
        st.plotly_chart(fig, use_container_width=True)

        # Boxplot
        fig2 = px.box(df, y=col_num, title=f"Boxplot de {col_num}")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Gráficas automáticas de columnas categóricas
    if cat_cols:
        st.subheader("Top categorías")
        col_cat = st.selectbox("Selecciona columna categórica", cat_cols)
        top_cat = df[col_cat].value_counts().nlargest(10)
        fig3 = px.bar(top_cat, x=top_cat.index, y=top_cat.values, title=f"Top 10 de {col_cat}")
        st.plotly_chart(fig3, use_container_width=True)

    # Insights automáticos simples
    st.subheader("Insights rápidos")
    if num_cols:
        max_col = df[num_cols].mean().idxmax()
        st.write(f"- La variable con mayor media es **{max_col}**: {df[max_col].mean():.2f}")
        min_col = df[num_cols].mean().idxmin()
        st.write(f"- La variable con menor media es **{min_col}**: {df[min_col].mean():.2f}")

    if cat_cols:
        for c in cat_cols:
            top_value = df[c].value_counts().idxmax()
            st.write(f"- En **{c}**, la categoría más frecuente es **{top_value}**")
