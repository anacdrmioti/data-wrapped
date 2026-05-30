import os
import zipfile
import json
import pandas as pd
import shutil

def cargar_datos(uploaded_file):
    """
    Carga datos desde un archivo ZIP con JSON dentro.

    Qué hace:
    - Descomprime el archivo ZIP en una carpeta temporal
    - Busca todos los archivos .json dentro
    - Los lee y los convierte en un DataFrame
    - Borra la carpeta temporal al final
    """

    temp_path = "temp_data"

    # Creamos carpeta temporal
    os.makedirs(temp_path, exist_ok=True)

    try:
        # Descomprimimos el ZIP
        if uploaded_file is not None:
            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                zip_ref.extractall(temp_path)

        data = []

        # Recorremos todos los archivos del zip
        for root, dirs, files in os.walk(temp_path):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)

                    # Leemos cada JSON
                    with open(path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        data.extend(content)

        # Convertimos todo a DataFrame
        df = pd.DataFrame(data)
        return df

    finally:
        # Limpiamos carpeta temporal siempre
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)