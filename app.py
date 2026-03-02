import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Wrapped", layout="wide")

st.title("📊 Data Wrapped")

uploaded_file = st.file_uploader("Sube tu archivo CSV")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Vista previa de los datos")
    st.dataframe(df.head())

    st.subheader("Estadísticas básicas")
    st.write(df.describe())
