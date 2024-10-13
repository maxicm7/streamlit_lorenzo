import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import timedelta

# Función para conectar a MySQL
def connect_to_mysql():
    try:
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

# App FastAPI
app = FastAPI()

@app.get("/datos")
async def obtener_datos():
    conn = connect_to_mysql()
    if conn:
        query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Configurar TTL para el caché
        ttl = timedelta(minutes=10)
        return JSONResponse(content=df.to_dict(orient="records"), headers={"Cache-Control": f"max-age={ttl.total_seconds()}"})
    else:
        return JSONResponse(content={"error": "No se pudo conectar a la base de datos"}, status_code=500)

# Función para generar el gráfico
def generar_grafico(df):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        visitas_por_fecha = df.groupby('Fecha')['visits'].sum()
        
        origen = st.selectbox("Origen", df['Origen'].unique()) if 'Origen' in df.columns else None
        
        if origen:
            df_origen = df[df['Origen'] == origen]
            visitas_por_fecha_origen = df_origen.groupby('Fecha')['visits'].sum()
            
            ax.plot(visitas_por_fecha.index, visitas_por_fecha.values, label=f'Todas las fuentes')
            ax.plot(visitas_por_fecha_origen.index, visitas_por_fecha_origen.values, label=f'{origen}')
            
            ax.legend()
        
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Visitas")
        ax.set_title("Visitas por Fecha")
        
        date_format = mdates.DateFormatter('%Y-%m-%d')
        ax.xaxis.set_major_formatter(date_format)
        ax.xaxis.set_major_locator(mdates.DayLocator())
        
        fig.autofmt_xdate()
        
        return fig
    
    return None

# Función para generar el DataFrame filtrado
def generar_dataframe_filtrado(df, fecha_inicio, fecha_fin, titulo, origen, health_min, health_max, visits_min, visits_max):
    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]
    
    if 'Título' in df.columns and titulo:
        df = df[df['Título'] == titulo]
    
    if 'Origen' in df.columns and origen:
        df = df[df['Origen'] == origen]
    
    df = df[(df['health'] >= health_min) & (df['health'] <= health_max)]
    df = df[(df['visits'] >= visits_min) & (df['visits'] <= visits_max)]
    
    return df

# Función para mostrar el DataFrame filtrado
def mostrar_dataframe_filtrado(df):
    if not df.empty:
        st.subheader("DataFrame filtrado")
        st.dataframe(df)
    else:
        st.info("No hay datos que coincidan con los criterios de filtro")

# Función para mostrar el gráfico
def mostrar_grafico(fig):
    if fig:
        st.subheader("Grafico de Visitas por Fecha")
        st.pyplot(fig)
    else:
        st.info("No hay suficiente información para generar el gráfico")

# Función para mostrar el mensaje de error
def mostrar_error(error):
    st.error(error)

# Función para mostrar el mensaje de advertencia
def mostrar_advertencia(mensaje):
    st.warning(mensaje)

# Función para mostrar el mensaje de éxito
def mostrar_exito(mensaje):
    st.success(mensaje)

# Función principal de Streamlit
def main():
    st.title("App de Análisis de Datos de Salud")

    # Barra lateral para selección de página
    pagina = st.sidebar.selectbox("Seleccione una página", ["Carga de Datos", "Visualización", "Gráfico"])

    if pagina == "Carga de Datos":
        st.title("Carga de Datos desde la API")
        
        if st.button("Cargar Datos"):
            conn = connect_to_mysql()
            if conn:
                query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
                df = pd.read_sql(query, conn)
                conn.close()
                
                if not df.empty:
                    st.session_state['df_concatenado'] = df
                    st.write("Datos cargados desde la API:")
                    st.dataframe(df)
                else:
                    mostrar_error("No se obtuvieron datos de la API.")
            else:
                mostrar_error("Error al conectar a la base de datos.")
    elif pagina == "Visualización":
        if 'df_concatenado' in st.session_state:
            df_concatenado = st.session_state['df_concatenado']
            mostrar_dataframe_filtrado(generar_dataframe_filtrado(df_concatenado, *st.date_input_values(), *st.selectbox_values(), *st.slider_values()))
        else:
            mostrar_advertencia("No se ha cargado ningún archivo. Ve a la sección 'Carga de Datos' para hacerlo.")
    elif pagina == "Gráfico":
        fig = generar_grafico(st.session_state['df_concatenado']) if 'df_concatenado' in st.session_state else None
        mostrar_grafico(fig)

if __name__ == "__main__":
    main()
