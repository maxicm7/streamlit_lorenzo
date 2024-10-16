import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Función para conectar a MySQL
def connect_to_mysql(host, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            port=st.secrets["mysql"]["port"],
            database=database,
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"]
        )
        st.success(f"Conexión a {database} en {host} exitosa")
        return conn
    except Error as e:
        st.error(f"Error al conectar: {e}")
        return None

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
            
            ax.plot(visitas_por_fecha.index, visitas_por_fecha.values, label='Todas las fuentes', color='blue')
            ax.plot(visitas_por_fecha_origen.index, visitas_por_fecha_origen.values, label=origen, color='orange')
            
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
        st.subheader("Gráfico de Visitas por Fecha")
        st.pyplot(fig)
    else:
        st.info("No hay suficiente información para generar el gráfico")

# Función principal de Streamlit
def main():
    st.title("App de Visitas y Salud de Publicaciones - Lorenzo Automotores")

    # Conexión a la base de datos remota
    conn = connect_to_mysql(st.secrets["mysql"]["host_remote"], st.secrets["mysql"]["database"])

    if conn:
        # Cargar datos
        query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
        df = pd.read_sql(query, conn)
        conn.close()

        # Mostrar los datos en la app
        st.subheader("Datos de la base de datos:")
        st.dataframe(df)

        # Filtros para el DataFrame
        st.subheader("Filtrar Datos")
        fecha_inicio = st.date_input("Fecha inicio")
        fecha_fin = st.date_input("Fecha fin")
        titulo = st.text_input("Título")
        origen = st.selectbox("Origen", df['Origen'].unique().tolist() + [''], label="Seleccione origen (opcional)")
        health_min = st.number_input("Salud mínima", min_value=0, value=0)
        health_max = st.number_input("Salud máxima", min_value=0, value=100)
        visits_min = st.number_input("Visitas mínimas", min_value=0, value=0)
        visits_max = st.number_input("Visitas máximas", min_value=0, value=1000)

        if st.button("Aplicar Filtros"):
            df_filtrado = generar_dataframe_filtrado(df, fecha_inicio, fecha_fin, titulo, origen, health_min, health_max, visits_min, visits_max)
            mostrar_dataframe_filtrado(df_filtrado)

            # Generar gráfico
            fig = generar_grafico(df_filtrado)
            mostrar_grafico(fig)

if __name__ == "__main__":
    main()
