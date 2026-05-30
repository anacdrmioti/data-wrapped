from Preprocesamiento_datos.Carga_datos import cargar_datos
from Preprocesamiento_datos.Limpieza_datos import limpieza_datos

def pipeline_carga_y_limpieza_datos(uploaded_file, nombre):
    """
    Carga un archivo y lo limpia para dejarlo listo para usar.
    """

    df = cargar_datos(uploaded_file)
    df_limpio = limpieza_datos(df, nombre)

    return df_limpio