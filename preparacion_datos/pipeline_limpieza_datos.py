from preparacion_datos.carga_datos import cargar_datos
from preparacion_datos.limpieza_datos import limpieza_datos

def pipeline_carga_y_limpieza_datos(uploaded_file, nombre):
    df = cargar_datos(uploaded_file)
    return limpieza_datos(df, nombre)