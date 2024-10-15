import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
            ax.plot(visitas_por_fecha_origen.index, visitas_por_fecha_origen.values, label=f'{origen}', color='orange')
            
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

# Función principal de Streamlit
def main():
    st.title("App de Visitas y Estado de Salud de las Publicaciones en Mercado Libre")

    # Barra lateral para selección de página
    pagina = st.sidebar.selectbox("Seleccione una página", ["Carga de Datos", "Visualización", "Gráfico"])

    if pagina == "Carga de Datos":
        st.title("Carga de Datos desde la Base de Datos")
        
        if st.button("Cargar Datos"):
            conn = connect_to_mysql()
            if conn:
                query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
                df = pd.read_sql(query, conn)
                conn.close()
                
                if not df.empty:
                    st.session_state['df_concatenado'] = df
                    st.write("Datos cargados desde la base de datos:")
                    st.dataframe(df)
                else:
                    st.error("No se obtuvieron datos de la base de datos.")
            else:
                st.error("Error al conectar a la base de datos.")
    
    elif pagina == "Visualización":
        if 'df_concatenado' in st.session_state:
            df_concatenado = st.session_state['df_concatenado']
            # Puedes agregar filtros aquí para el DataFrame
            st.dataframe(df_concatenado)  # Muestra el DataFrame completo por ahora
        else:
            st.warning("No se ha cargado ningún archivo. Ve a la sección 'Carga de Datos' para hacerlo.")
    
    elif pagina == "Gráfico":
        if 'df_concatenado' in st.session_state:
            fig = generar_grafico(st.session_state['df_concatenado'])
            if fig:
                st.subheader("Gráfico de Visitas por Fecha")
                st.pyplot(fig)
            else:
                st.info("No hay suficiente información para generar el gráfico.")
        else:
            st.warning("No se ha cargado ningún archivo. Ve a la sección 'Carga de Datos' para hacerlo.")

if __name__ == "__main__":
    main()
