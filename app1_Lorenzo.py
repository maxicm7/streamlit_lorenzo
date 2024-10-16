import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt

# Función para conectar a MySQL
def connect_to_mysql(host_name, user_name, user_password, db_name):
    try:
        conn = mysql.connector.connect(
            host=host_name,
            user=user_name,
            password=user_password,
            database=db_name
        )
        st.write(f"Conexión exitosa a la base de datos: {db_name}")
        return conn
    except Error as e:
        st.write(f"Error al conectar: {e}")
        return None

# Conectar a las bases de datos
def connect_databases():
    # Conexión a la base de datos local
    conn_local = connect_to_mysql(
        st.secrets["mysql_local"]["host"],
        st.secrets["mysql_local"]["user"],
        st.secrets["mysql_local"]["password"],
        st.secrets["mysql_local"]["database"]
    )
    
    # Conexión a la base de datos remota
    conn_remote = connect_to_mysql(
        st.secrets["mysql_remote"]["host"],
        st.secrets["mysql_remote"]["user"],
        st.secrets["mysql_remote"]["password"],
        st.secrets["mysql_remote"]["database"]
    )
    
    return conn_local, conn_remote

# Función principal de Streamlit
def main():
    st.title("Visor de Datos - Lorenzo Automotores")

    # Conectar a las bases de datos local y remota
    conn_local, conn_remote = connect_databases()

    # Elegir qué base de datos usar
    db_option = st.selectbox("Seleccionar base de datos", ["Local", "Remota"])

    if db_option == "Local" and conn_local:
        conn = conn_local
    elif db_option == "Remota" and conn_remote:
        conn = conn_remote
    else:
        st.write("No se pudo conectar a la base de datos.")
        return
    
    # Consultar datos y mostrarlos en la app
    if conn:
        query = "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud"
        df = pd.read_sql(query, conn)
        st.write(df)

        # Mostrar gráfico de visitas por fecha
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            fig, ax = plt.subplots(figsize=(10, 5))
            visitas_por_fecha = df.groupby('Fecha')['visits'].sum()
            ax.plot(visitas_por_fecha.index, visitas_por_fecha.values, label="Visitas")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Visitas")
            ax.set_title("Visitas por Fecha")
            st.pyplot(fig)

if __name__ == "__main__":
    main()

