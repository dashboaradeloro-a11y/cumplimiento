
import streamlit as pd
import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Atenciones de Salud - El Oro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para un look profesional y limpio (Sector Salud)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    h1 { color: #1e3a8a; font-family: 'Helvetica Neue', sans-serif; }
    h2 { color: #0f766e; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Control de Atenciones Médicas - Distrito de Salud")
st.markdown("Este dashboard interactivo permite analizar la productividad y distribución de las atenciones médicas según los registros institucionales.")

# Carga de datos
@st.cache_data
def load_data():
    try:
        # Reemplaza 'datos_salud.csv' por la ruta de tu archivo o súbelo dinámicamente
        df = pd.read_csv('datos_salud.csv')
        return df
    except:
        return None

df = load_data()

# Si el usuario no tiene el archivo en la misma carpeta, le damos la opción de subirlo
if df is None:
    uploaded_file = st.file_uploader("📂 Sube tu archivo Excel o CSV exportado", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
else:
    st.sidebar.success("✅ Archivo base 'datos_salud.csv' cargado con éxito.")

if df is not None:
    # --- FILTROS DE LA BARRA LATERAL ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Filtro por Cantón
    canton_opt = ["Todos"] + list(df['CANTON'].unique())
    selected_canton = st.sidebar.selectbox("Cantón Unidad", canton_opt)
    
    # Filtro por Centro de Salud
    if selected_canton != "Todos":
        df_filtered = df[df['CANTON'] == selected_canton]
    else:
        df_filtered = df
        
    centro_opt = ["Todos"] + list(df_filtered['NOMBRE DE CENTRO DE SALUD'].unique())
    selected_centro = st.sidebar.selectbox("Centro de Salud", centro_opt)
    
    # Aplicar filtros encadenados
    if selected_centro != "Todos":
        df_filtered = df_filtered[df_filtered['NOMBRE DE CENTRO DE SALUD'] == selected_centro]
        
    # Filtro por Tipo de Atención
    tipo_atencion_opt = ["Todos"] + list(df_filtered['ATENCION'].unique())
    selected_tipo_atencion = st.sidebar.selectbox("Tipo de Atención (Intra/Extramural)", tipo_atencion_opt)
    if selected_tipo_atencion != "Todos":
        df_filtered = df_filtered[df_filtered['ATENCION'] == selected_tipo_atencion]

    # --- KPI METRICS PRINCIPALES ---
    total_atenciones = len(df_filtered)
    total_profesionales = df_filtered['PROFESIONAL'].nunique()
    total_centros = df_filtered['NOMBRE DE CENTRO DE SALUD'].nunique()
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Total de Atenciones", value=f"{total_atenciones:,}")
    with m2:
        st.metric(label="Profesionales Activos", value=total_profesionales)
    with m3:
        st.metric(label="Centros con Registros", value=total_centros)
        
    st.markdown("---")

    # --- BLOQUE 1: GRÁFICOS POR CENTRO Y TIPO ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏥 Atenciones por Centro de Salud")
        centro_counts = df_filtered['NOMBRE DE CENTRO DE SALUD'].value_counts().reset_index()
        centro_counts.columns = ['Centro de Salud', 'Atenciones']
        fig_centro = px.bar(centro_counts, x='Atenciones', y='Centro de Salud', orientation='h',
                            color='Atenciones', color_continuous_scale='Blues',
                            labels={'Atenciones': 'N° de Atenciones'})
        fig_centro.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_centro, use_container_width=True)
        
    with g2:
        st.subheader("🏢 Por Tipo de Centro de Salud")
        tipo_counts = df_filtered['TIPO DE CENTRO DE SALUD'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo de Centro', 'Atenciones']
        fig_tipo = px.pie(tipo_counts, names='Tipo de Centro', values='Atenciones',
                          color_discrete_sequence=px.colors.qualitative.Teal)
        fig_tipo.update_traces(textinfo='percent+value')
        st.plotly_chart(fig_tipo, use_container_width=True)

    # --- BLOQUE 2: PROFESIONALES Y DIAGNÓSTICOS ---
    g3, g4 = st.columns(2)
    
    with g3:
        st.subheader("👨‍⚕️ Top Profesionales por Volumen de Atención")
        prof_counts = df_filtered['PROFESIONAL'].value_counts().head(10).reset_index()
        prof_counts.columns = ['Profesional', 'Atenciones']
        fig_prof = px.bar(prof_counts, x='Atenciones', y='Profesional', orientation='h',
                           color='Atenciones', color_continuous_scale='Mint',
                           labels={'Atenciones': 'N° de Atenciones'})
        fig_prof.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_prof, use_container_width=True)
        
    with g4:
        st.subheader("📋 Distribución por Diagnóstico")
        diag_counts = df_filtered['DIAGNOSTICO'].value_counts().reset_index()
        diag_counts.columns = ['Diagnóstico', 'Atenciones']
        fig_diag = px.bar(diag_counts, x='Diagnóstico', y='Atenciones',
                           color='Diagnóstico', color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_diag, use_container_width=True)

    # --- BLOQUE 3: CRONOLOGÍA Y TIPO DE ATENCIÓN ---
    g5, g6 = st.columns(2)
    
    with g5:
        st.subheader("⏳ Cronología de la Atención")
        crono_counts = df_filtered['CRONOLOGIA'].value_counts().reset_index()
        crono_counts.columns = ['Cronología', 'Atenciones']
        fig_crono = px.pie(crono_counts, names='Cronología', values='Atenciones',
                            color_discrete_sequence=px.colors.sequential.Burg)
        fig_crono.update_traces(textinfo='percent+value')
        st.plotly_chart(fig_crono, use_container_width=True)
        
    with g6:
        st.subheader("📍 Modalidad de Atención")
        aten_counts = df_filtered['ATENCION'].value_counts().reset_index()
        aten_counts.columns = ['Modalidad', 'Atenciones']
        fig_aten = px.bar(aten_counts, x='Modalidad', y='Atenciones',
                          color='Modalidad', color_discrete_sequence=['#2563eb', '#10b981'])
        st.plotly_chart(fig_aten, use_container_width=True)

    # --- TABLA DE DATOS DETALLADA ---
    st.subheader("📋 Vista General de Datos Filtrados")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("💡 Por favor, sube un archivo Excel o CSV con las columnas correspondientes para renderizar los gráficos.")
