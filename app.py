import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Dashboard de Atenciones Médicas - MSP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS avanzados para un entorno institucional y limpio
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid #0284c7; }
    h1 { color: #1e3a8a; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    h2, h3 { color: #0f766e; font-family: 'Segoe UI', sans-serif; }
    div.stButton > button:first-child { background-color: #0284c7; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 Control y Productividad de Atenciones Médicas (OneDrive API)")
st.markdown("Monitoreo institucional automatizado conectado en tiempo real con tu matriz de Excel en línea.")

# 2. CONEXIÓN EN DIRECTO CON ONEDRIVE (MÉTODO API SIN ERROR 401)
URL_COMPARTIDA = "https://1drv.ms/x/c/c16d224ec509db16/IQBmdL8Yo16yTorHBVOsBuNXAZXQNJejA86OCrqf9Eme1d4?e=o8TI7O"

@st.cache_data(ttl=300)  # Almacena los datos en caché por 5 minutos para optimizar la velocidad
def cargar_datos_desde_onedrive(url):
    try:
        # Algoritmo de Microsoft para transformar enlaces compartidos '1drv.ms' en descargas directas de la API
        base_url = url.split('?')[0]
        data_bytes = base_url.encode("utf-8")
        base64_bytes = base64.b64encode(data_bytes)
        base64_string = base64_bytes.decode("utf-8").replace('=', '').replace('/', '_').replace('+', '-')
        
        # Generar URL de la API pública de OneDrive
        url_directa = f"https://api.onedrive.com/v1.0/shares/u!{base64_string}/root/content"
        
        # Leer el archivo Excel binario directamente desde el flujo de la API
        df = pd.read_excel(url_directa)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la API de OneDrive: {e}")
        return None

df_raw = cargar_datos_desde_onedrive(URL_COMPARTIDA)

# Mecanismo de contingencia por si expira el enlace de OneDrive
if df_raw is None:
    st.warning("⚠️ No se pudo sincronizar automáticamente con OneDrive. Verifica que el archivo esté compartido públicamente como 'Cualquier persona con el enlace puede ver'.")
    uploaded_file = st.file_uploader("Puedes subir una copia local de tu archivo Excel (.xlsx) aquí mientras tanto:", type=["xlsx"])
    if uploaded_file is not None:
        df_raw = pd.read_excel(uploaded_file)

if df_raw is not None:
    # Limpieza de los nombres de columnas (elimina espacios ocultos al inicio o final)
    df_raw.columns = df_raw.columns.str.strip()
    
    # 3. BARRA LATERAL - FILTROS INTERACTIVOS
    st.sidebar.header("🔍 Filtros de Visualización")
    
    # Filtro: Tipo de Centro de Salud
    if 'TIPO DE CENTRO DE SALUD' in df_raw.columns:
        tipos_disponibles = ["Todos"] + list(df_raw['TIPO DE CENTRO DE SALUD'].dropna().unique())
        selected_tipo = st.sidebar.selectbox("Tipo de Centro de Salud", tipos_disponibles)
    else:
        selected_tipo = "Todos"
        
    df_intermedio = df_raw.copy()
    if selected_tipo != "Todos":
        df_intermedio = df_intermedio[df_intermedio['TIPO DE CENTRO DE SALUD'] == selected_tipo]
        
    # Filtro: Nombre del Centro de Salud específico
    if 'NOMBRE DE CENTRO DE SALUD' in df_raw.columns:
        centros_disponibles = ["Todos"] + list(df_intermedio['NOMBRE DE CENTRO DE SALUD'].dropna().unique())
        selected_centro = st.sidebar.selectbox("Establecimiento de Salud", centros_disponibles)
    else:
        selected_centro = "Todos"
        
    # Filtro: Tipo de Atención
    if 'ATENCION' in df_raw.columns:
        atencion_disponibles = ["Todos"] + list(df_intermedio['ATENCION'].dropna().unique())
        selected_atencion = st.sidebar.selectbox("Modalidad de Atención (Intra/Extramural)", atencion_disponibles)
    else:
        selected_atencion = "Todos"

    # Aplicación definitiva de filtros al conjunto de datos
    df_filtrado = df_raw.copy()
    if selected_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['TIPO DE CENTRO DE SALUD'] == selected_tipo]
    if selected_centro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['NOMBRE DE CENTRO DE SALUD'] == selected_centro]
    if selected_atencion != "Todos":
        df_filtrado = df_filtrado[df_filtrado['ATENCION'] == selected_atencion]

    # 4. TARJETAS DE MÉTRICAS PRINCIPALES (KPIs)
    total_atenciones = len(df_filtrado)
    profesionales_unicos = df_filtrado['PROFESIONAL'].nunique() if 'PROFESIONAL' in df_filtrado.columns else 0
    diagnosticos_unicos = df_filtrado['DIAGNOSTICO'].nunique() if 'DIAGNOSTICO' in df_filtrado.columns else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric(label="Total de Atenciones", value=f"{total_atenciones:,}")
    with kpi2:
        st.metric(label="Personal Médico Registrado", value=profesionales_unicos)
    with kpi3:
        st.metric(label="Diagnósticos Únicos Registrados", value=diagnosticos_unicos)
        
    st.markdown("---")

    # 5. BLOQUES GRÁFICOS DINÁMICOS (PLOTLY INTERACTIVO)
    
    # Fila 1: Centros de Salud y Tipos de Establecimiento
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏥 Atenciones por Centro de Salud")
        if 'NOMBRE DE CENTRO DE SALUD' in df_filtrado.columns:
            data_centro = df_filtrado['NOMBRE DE CENTRO DE SALUD'].value_counts().reset_index()
            data_centro.columns = ['Centro de Salud', 'Atenciones']
            fig_centro = px.bar(data_centro, x='Atenciones', y='Centro de Salud', orientation='h',
                                color='Atenciones', color_continuous_scale='Blues',
                                labels={'Atenciones': 'N° de Atenciones'})
            fig_centro.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_centro, use_container_width=True)

    with col2:
        st.subheader("🏢 Distribución por Tipo de Centro")
        if 'TIPO DE CENTRO DE SALUD' in df_filtrado.columns:
            data_tipo = df_filtrado['TIPO DE CENTRO DE SALUD'].value_counts().reset_index()
            data_tipo.columns = ['Tipo de Centro', 'Atenciones']
            fig_tipo = px.pie(data_tipo, names='Tipo de Centro', values='Atenciones',
                              color_discrete_sequence=px.colors.qualitative.Teal)
            fig_tipo.update_traces(textinfo='percent+value')
            st.plotly_chart(fig_tipo, use_container_width=True)

    # Fila 2: Personal Médico y Clasificación de Diagnósticos
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("👨‍⚕️ Atenciones por Nombre del Profesional (Top 15)")
        if 'PROFESIONAL' in df_filtrado.columns:
            data_prof = df_filtrado['PROFESIONAL'].value_counts().head(15).reset_index()
            data_prof.columns = ['Profesional', 'Atenciones']
            fig_prof = px.bar(data_prof, x='Atenciones', y='Profesional', orientation='h',
                               color='Atenciones', color_continuous_scale='GnBu')
            fig_prof.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_prof, use_container_width=True)

    with col4:
        st.subheader("📋 Volumen de Casos por Diagnóstico (Top 15)")
        if 'DIAGNOSTICO' in df_filtrado.columns:
            data_diag = df_filtrado['DIAGNOSTICO'].value_counts().head(15).reset_index()
            data_diag.columns = ['Diagnóstico', 'Atenciones']
            fig_diag = px.bar(data_diag, x='Diagnóstico', y='Atenciones',
                               color='Atenciones', color_continuous_scale='Purples')
            st.plotly_chart(fig_diag, use_container_width=True)

    # Fila 3: Cronología de la consulta y Tipo de Atención
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("⏳ Análisis por Cronología")
        if 'CRONOLOGIA' in df_filtrado.columns:
            data_crono = df_filtrado['CRONOLOGIA'].value_counts().reset_index()
            data_crono.columns = ['Cronología', 'Atenciones']
            fig_crono = px.pie(data_crono, names='Cronología', values='Atenciones',
                                color_discrete_sequence=px.colors.sequential.Magenta)
            fig_crono.update_traces(textinfo='percent+value')
            st.plotly_chart(fig_crono, use_container_width=True)

    with col6:
        st.subheader("📍 Tipo / Modalidad de la Atención")
        if 'ATENCION' in df_filtrado.columns:
            data_aten = df_filtrado['ATENCION'].value_counts().reset_index()
            data_aten.columns = ['Modalidad', 'Atenciones']
            fig_aten = px.bar(data_aten, x='Modalidad', y='Atenciones',
                              color='Modalidad', color_discrete_sequence=['#0284c7', '#10b981'])
            st.plotly_chart(fig_aten, use_container_width=True)

    # 6. TABLA CON LOS REGISTROS FILTRADOS
    st.subheader("🔍 Tabla Desglosada de Registros")
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón manual en la barra lateral para refrescar el caché antes de los 5 minutos establecidos
    if st.sidebar.button("🔄 Sincronizar con OneDrive ahora"):
        st.cache_data.clear()
        st.rerun()
else:
    st.info("Configuración completa. Esperando que el servidor de OneDrive autorice la descarga de datos.")
