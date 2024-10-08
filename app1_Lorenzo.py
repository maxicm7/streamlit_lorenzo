import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Función para conectar a MySQL
def connect_to_mysql(server, database, username, password):
    try:
        conn = mysql.connector.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        return conn
    except Exception as e:
        st.error(f"Error al conectar al servidor MySQL: {e}")
        return None

# Función para cargar datos desde MySQL
def load_data_from_mysql(query, server, database, username, password):
    conn = connect_to_mysql(server, database, username, password)
    if conn:
        try:
            df = pd.read_sql(query, conn)
            conn.close()  # Cerrar la conexión después de la consulta
            return df
        except Exception as e:
            st.error(f"Error al ejecutar la consulta SQL: {e}")
            return None
    else:
        return None

# Debug: Verificar si los secretos están cargados correctamente
st.write(st.secrets)  # Esto mostrará todos los secretos y ayudará a verificar si se están cargando correctamente

# Cargar la configuración desde secrets de Streamlit o variables de entorno
server = st.secrets["mysql"]["MYSQL_SERVER"]
database = st.secrets["mysql"]["MYSQL_DATABASE"]
username = st.secrets["mysql"]["MYSQL_USER"]
password = st.secrets["mysql"]["MYSQL_PASSWORD"]

# Inicializa el estado para almacenar el DataFrame concatenado
if 'df_concatenado' not in st.session_state:
    st.session_state['df_concatenado'] = None

# Título en la barra lateral para la navegación
st.sidebar.title("Configuración de Conexión")

# Selección de la página
pagina = st.sidebar.selectbox("Seleccione una página", ["Carga de Datos", "Visualización", "Gráfico"])

# Página 1: Carga de datos
if pagina == "Carga de Datos":
    st.title("Carga de Datos desde MySQL")

    # Consulta SQL para cargar los datos
    query = st.text_area("Ingresa la consulta SQL:", "SELECT `ID publicación`, `Fecha`, `visits`, `health`, `Origen`, `Título` FROM visitas_salud") 

    if st.button("Cargar Datos"):
        df_concatenado = load_data_from_mysql(query, server, database, username, password)
        if df_concatenado is not None:
            st.session_state['df_concatenado'] = df_concatenado
            st.write("Datos cargados desde MySQL:")
            st.dataframe(df_concatenado)

# Página 2: Visualización de datos
elif pagina == "Visualización":
    st.title("Visualización de Información")

    if st.session_state['df_concatenado'] is not None:
        df_concatenado = st.session_state['df_concatenado']
        st.write("Datos concatenados:")
        st.write("Columnas disponibles:", df_concatenado.columns.tolist())

        # Asegurarse de que 'Fecha' sea una columna datetime
        if 'Fecha' in df_concatenado.columns:
            df_concatenado['Fecha'] = pd.to_datetime(df_concatenado['Fecha'], errors='coerce')

        # Crear filtros para las columnas deseadas
        fecha_inicio = st.date_input("Fecha de inicio")
        fecha_fin = st.date_input("Fecha de fin")

        # Filtro por 'Título'
        if 'Título' in df_concatenado.columns:
            titulos_unicos = df_concatenado['Título'].unique()
            titulo = st.selectbox("Título", titulos_unicos)
        else:
            st.warning("La columna 'Título' no está disponible en los datos.")

        # Filtro por 'Origen'
        if 'Origen' in df_concatenado.columns:
            origenes_unicos = df_concatenado['Origen'].unique()
            origen = st.selectbox("Origen", origenes_unicos)
        else:
            st.warning("La columna 'Origen' no está disponible en los datos.")

        # Filtros por rangos para 'health' y 'visits'
        health_min, health_max = st.slider("Rango de Health", 
                                             min_value=float(df_concatenado['health'].min()), 
                                             max_value=float(df_concatenado['health'].max()), 
                                             value=(float(df_concatenado['health'].min()), float(df_concatenado['health'].max())))

        visits_min, visits_max = st.slider("Rango de Visits", 
                                             min_value=int(df_concatenado['visits'].min()), 
                                             max_value=int(df_concatenado['visits'].max()), 
                                             value=(int(df_concatenado['visits'].min()), int(df_concatenado['visits'].max())))

        # Aplicar filtros
        if 'Fecha' in df_concatenado.columns:
            if fecha_inicio:
                df_concatenado = df_concatenado[df_concatenado['Fecha'] >= pd.to_datetime(fecha_inicio)]
            if fecha_fin:
                df_concatenado = df_concatenado[df_concatenado['Fecha'] <= pd.to_datetime(fecha_fin)]
        
        if 'Título' in df_concatenado.columns and titulo:
            df_concatenado = df_concatenado[df_concatenado['Título'] == titulo]
        
        if 'Origen' in df_concatenado.columns and origen:
            df_concatenado = df_concatenado[df_concatenado['Origen'] == origen]

        # Filtrar por rangos de health y visits
        df_concatenado = df_concatenado[(df_concatenado['health'] >= health_min) & (df_concatenado['health'] <= health_max)]
        df_concatenado = df_concatenado[(df_concatenado['visits'] >= visits_min) & (df_concatenado['visits'] <= visits_max)]

        # Agrupa por 'ID publicación' y 'Fecha' después de filtrar
        df_filtrado = df_concatenado.groupby(['ID publicación', 'Fecha']).agg({
            'visits': 'sum',
            'health': 'mean',
            'Origen': 'first',
            'Título': 'first'
        }).reset_index()

        st.dataframe(df_filtrado)
    else:
        st.warning("No se ha cargado ningún archivo. Ve a la sección 'Carga de Datos' para hacerlo.")

# Página 3: Gráfico
elif pagina == "Gráfico":
    st.title("Gráfico de Visitas por Fecha")

    if st.session_state['df_concatenado'] is not None:
        df_concatenado = st.session_state['df_concatenado']

        if 'Fecha' in df_concatenado.columns:
            df_concatenado['Fecha'] = pd.to_datetime(df_concatenado['Fecha'], errors='coerce')

            # Crear filtros
            fecha_inicio = st.date_input("Fecha de inicio")
            fecha_fin = st.date_input("Fecha de fin")

            # Filtro por 'Origen'
            if 'Origen' in df_concatenado.columns:
                origenes_unicos = df_concatenado['Origen'].unique()
                origen = st.selectbox("Origen", origenes_unicos)
            else:
                st.warning("La columna 'Origen' no está disponible en los datos.")

            # Aplicar filtros
            if fecha_inicio:
                df_concatenado = df_concatenado[df_concatenado['Fecha'] >= pd.to_datetime(fecha_inicio)]
            if fecha_fin:
                df_concatenado = df_concatenado[df_concatenado['Fecha'] <= pd.to_datetime(fecha_fin)]
            if 'Origen' in df_concatenado.columns and origen:
                df_concatenado = df_concatenado[df_concatenado['Origen'] == origen]

            # Agrupa por 'Fecha' y suma las visitas
            visitas_por_fecha = df_concatenado.groupby('Fecha')['visits'].sum()

            # Opción de acumulado
            acumulado = st.checkbox("Acumulado")

            # Crea el gráfico con matplotlib
            fig, ax = plt.subplots()

            if acumulado:
                ax.plot(visitas_por_fecha.index, visitas_por_fecha.cumsum())
                ax.set_ylabel("Visitas Acumuladas")
            else:
                ax.plot(visitas_por_fecha.index, visitas_por_fecha.values)
                ax.set_ylabel("Visitas")

            ax.set_xlabel("Fecha")
            ax.set_title("Visitas por Fecha")

            # Formato de fecha mejorado
            date_format = mdates.DateFormatter('%Y-%m-%d')
            ax.xaxis.set_major_formatter(date_format)
            ax.xaxis.set_major_locator(mdates.DayLocator())

            # Ajustar el gráfico para mejor legibilidad
            fig.autofmt_xdate()  # Rotar etiquetas de fecha para evitar solapamientos

            # Mostrar gráfico en Streamlit
            st.pyplot(fig)

    else:
        st.warning("No se ha cargado ningún archivo. Ve a la sección 'Carga de Datos' para hacerlo.")
