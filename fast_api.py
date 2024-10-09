from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import pandas as pd
from fastapi.responses import JSONResponse
import streamlit as st

app = FastAPI()

# Modelo para los datos (opcional, dependiendo de tus necesidades)
class Data(BaseModel):
    ID_publicacion: str
    Fecha: str
    visits: int
    health: float
    Origen: str
    Titulo: str

# Conectar a la base de datos
def connect_to_mysql():
    try:
        # Accediendo a los secretos de Streamlit
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            database=st.secrets["mysql"]["database"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"]
        )
        return conn
    except Error as e:
        print(f"Error al conectar: {e}")
        return None

# Endpoint para obtener datos
@app.get("/datos")
def obtener_datos():
    conn = connect_to_mysql()
    if conn:
        query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
        df = pd.read_sql(query, conn)
        conn.close()
        return JSONResponse(content=df.to_dict(orient="records"))  # Convertir dataframe a JSON
    else:
        return {"error": "No se pudo conectar a la base de datos"}


