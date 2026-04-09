import os
import zipfile
import json
import pandas as pd
import shutil

def cargar_datos(uploaded_file):

    temp_path = "temp_data"

    # Crear carpeta temporal
    os.makedirs(temp_path, exist_ok=True)

    try:
        # Descomprimir ZIP
        if uploaded_file is not None:
            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                zip_ref.extractall(temp_path)

        # Leer JSON
        data = []

        for root, dirs, files in os.walk(temp_path):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)

                    with open(path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        data.extend(content)

        df = pd.DataFrame(data)
        return df

    finally:
        # LIMPIEZA SIEMPRE (aunque haya error)
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)