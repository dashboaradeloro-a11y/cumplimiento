import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la interfaz del Dashboard
st.set_page_config(
    page_title="Dashboard de Atenciones Médicas - MSP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales profesionales
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .metric-box {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 5px solid #1f77b4;
            margin-bottom: 20px;
        }
        h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard de Control y Análisis de Atenciones")
st.markdown("Sube tu archivo consolidado de Excel para filtrar, cruzar variables y analizar métricas clave en tiempo real.")

# 2. Componente de carga del archivo Excel
uploaded_file = st.sidebar.file_uploader("📂 Cargar archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Lectura de datos
        df = pd.read_excel(uploaded_file)
        
        # Limpieza por si acaso queden espacios en blanco en los extremos de los encabezados
        df.columns = df.columns.str.strip().str.upper()
        
        # Validación y conversión de la columna obligatoria de fecha
        if 'FECHA_ATENCION' in df.columns:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
        else:
            st.error("❌ No se encontró la columna requerida: 'FECHA_ATENCION'")
            st.stop()

        # 3. FILTROS EN LA BARRA LATERAL (Estructura oficial de columnas)
        st.sidebar.header("🔍 Filtros de Búsqueda")
        
        selected_centros = st.sidebar.multiselect("Centro de Salud", sorted(df['CENTRO_SALUD'].dropna().unique())) if 'CENTRO_SALUD' in df.columns else []
        selected_tipos = st.sidebar.multiselect("Tipo de Centro", sorted(df['TIPO_CENTRO_SALUD'].dropna().unique())) if 'TIPO_CENTRO_SALUD' in df.columns else []
        selected_cantones = st.sidebar.multiselect("Cantón", sorted(df['CANTON'].dropna().unique())) if 'CANTON' in df.columns else []
        selected_entidades = st.sidebar.multiselect("Entidad (Distrito)", sorted(df['ENTIDAD'].dropna().unique())) if 'ENTIDAD' in df.columns else []
        selected_profesionales = st.sidebar.multiselect("Profesional", sorted(df['PROFESIONAL'].dropna().unique())) if 'PROFESIONAL' in df.columns else []
        selected_atenciones = st.sidebar.multiselect("Código de Atención (CIE-10)", sorted(df['ATENCION'].dropna().unique())) if 'ATENCION' in df.columns else []
        
        # Filtro de Rango de Fechas
        min_date = df['FECHA_ATENCION'].min().date() if not df['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        max_date = df['FECHA_ATENCION'].max().date() if not df['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        date_range = st.sidebar.date_input("Rango de Fechas", [min_date, max_date])

        # 4. APLICACIÓN DE LOS FILTROS SELECCIONADOS
        df_filtered = df.copy()
        if selected_centros: df_filtered = df_filtered[df_filtered['CENTRO_SALUD'].isin(selected_centros)]
        if selected_tipos: df_filtered = df_filtered[df_filtered['TIPO_CENTRO_SALUD'].isin(selected_tipos)]
        if selected_cantones: df_filtered = df_filtered[df_filtered['CANTON'].isin(selected_cantones)]
        if selected_entidades: df_filtered = df_filtered[df_filtered['ENTIDAD'].isin(selected_entidades)]
        if selected_profesionales: df_filtered = df_filtered[df_filtered['PROFESIONAL'].isin(selected_profesionales)]
        if selected_atenciones: df_filtered = df_filtered[df_filtered['ATENCION'].isin(selected_atenciones)]
        if len(date_range) == 2:
            df_filtered = df_filtered[(df_filtered['FECHA_ATENCION'].dt.date >= date_range[0]) & (df_filtered['FECHA_ATENCION'].dt.date <= date_range[1])]

        # 5. TARJETAS DE INDICADORES (KPIs)
        total_atenciones = len(df_filtered)
        top_diag = df_filtered['DIAGNOSTICO'].value_counts().index[0] if 'DIAGNOSTICO' in df_filtered.columns and not df_filtered['DIAGNOSTICO'].empty else "N/A"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='metric-box'><small style='color: #7f8c8d; font-weight: bold;'>TOTAL DE ATENCIONES</small><h2 style='margin: 0; color: #2980b9;'>{total_atenciones:,}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-box' style='border-left: 5px solid #27ae60;'><small style='color: #7f8c8d; font-weight: bold;'>DIAGNÓSTICO MÁS FRECUENTE</small><h4 style='margin: 0; color: #27ae60; font-size: 16px;'>{top_diag}</h4></div>", unsafe_allow_html=True)

        # 6. GRÁFICOS DE BARRAS COMPARATIVOS (Requerimiento de Tipo de Atención y Cronología)
        st.subheader("📊 Análisis Comparativo Operativo")
        g1, g2 = st.columns(2)
        
        with g1:
            if 'TIPO_ATENCION' in df_filtered.columns:
                fig_tipo = px.bar(df_filtered['TIPO_ATENCION'].value_counts().reset_index(), x='TIPO_ATENCION', y='count', title="Tipo de Atención (Intramural / Extramural)", labels={'count':'Cantidad', 'TIPO_ATENCION': 'Modalidad'}, color='TIPO_ATENCION', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_tipo.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_tipo, use_container_width=True)
            else:
                st.info("Columna 'TIPO_ATENCION' no encontrada en el archivo.")

        with g2:
            if 'CRONOLOGIA' in df_filtered.columns:
                fig_crono = px.bar(df_filtered['CRONOLOGIA'].value_counts().reset_index(), x='CRONOLOGIA', y='count', title="Cronología de Atención (Primera / Subsecuente)", labels={'count':'Cantidad', 'CRONOLOGIA': 'Evolución'}, color='CRONOLOGIA', color_discrete_sequence=px.colors.qualitative.Safe)
                fig_crono.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_crono, use_container_width=True)
            else:
                st.info("Columna 'CRONOLOGIA' no encontrada en el archivo.")

        # 7. TABLA DE DATOS DETALLADOS AUDITABLE
        st.subheader("📋 Registros Filtrados")
        with st.expander("Expandir para auditar la tabla de datos completa"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"🚨 Ocurrió un error inesperado al procesar el archivo: {e}")
else:
    st.info("💡 Esperando archivo... Por favor, carga el nuevo Excel estructurado en la barra lateral izquierda.")
