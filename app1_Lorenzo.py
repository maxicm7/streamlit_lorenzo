import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# URL del API de FastAPI (cambiar si es necesario)
api_url = "http://192.168.1.38:3306/datos"  # Cambia la URL según la dirección de tu FastAPI

# Título en la barra lateral para la navegación
st.sidebar.title("Configuración de Conexión")

# Selección de la página
pagina = st.sidebar.selectbox("Seleccione una página", ["Carga de Datos", "Visualización", "Gráfico"])

# Página 1: Carga de datos
if pagina == "Carga de Datos":
    st.title("Carga de Datos desde la API")

    if st.button("Cargar Datos"):
        # Hacer la petición a la API de FastAPI
        response = requests.get(api_url)
        if response.status_code == 200:
            df_concatenado = pd.DataFrame(response.json())
            st.session_state['df_concatenado'] = df_concatenado
            st.write("Datos cargados desde la API:")
            st.dataframe(df_concatenado)
        else:
            st.error("Error al cargar datos desde la API")

# Página 2: Visualización de datos
elif pagina == "Visualización":
    st.title("Visualización de Información")

    if 'df_concatenado' in st.session_state:
        df_concatenado = st.session_state['df_concatenado']
        st.write("Datos concatenados:")
        st.write("Columnas disponibles:", df_concatenado.columns.tolist())

        # Asegurarse de que 'Fecha' sea una columna datetime
        if 'Fecha' in df_concatenado.columns:
            df_concatenado['Fecha'] = pd.to_datetime(df_concatenado['Fecha'], errors='coerce')

        # Crear filtros para las columnas deseadas
        fecha_inicio = st.date_input("Fecha de inicio", pd.to_datetime(df_concatenado['Fecha'].min()).date())
        fecha_fin = st.date_input("Fecha de fin", pd.to_datetime(df_concatenado['Fecha'].max()).date())

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

    if 'df_concatenado' in st.session_state:
        df_concatenado = st.session_state['df_concatenado']

        if 'Fecha' in df_concatenado.columns:
            df_concatenado['Fecha'] = pd.to_datetime(df_concatenado['Fecha'], errors='coerce')

            # Crear filtros
            fecha_inicio = st.date_input("Fecha de inicio", pd.to_datetime(df_concatenado['Fecha'].min()).date())
            fecha_fin = st.date_input("Fecha de fin", pd.to_datetime(df_concatenado['Fecha'].max()).date())

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
