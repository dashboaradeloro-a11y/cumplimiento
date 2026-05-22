import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la interfaz
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
st.markdown("Sube tu archivo de Excel. Los filtros de la barra lateral se actualizarán automáticamente según tus selecciones.")

# 2. Carga del archivo Excel
uploaded_file = st.sidebar.file_uploader("📂 Cargar archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        
        if 'FECHA_ATENCION' in df.columns:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
        else:
            st.error("❌ No se encontró la columna requerida: 'FECHA_ATENCION'")
            st.stop()

        # --- 3. LÓGICA DE FILTROS EN CASCADA (DEPENDIENTES) ---
        st.sidebar.header("🔍 Filtros Dinámicos")

        # Filtro 1: Cantón (Base inicial)
        opciones_canton = sorted(df['CANTON'].dropna().unique()) if 'CANTON' in df.columns else []
        selected_cantones = st.sidebar.multiselect("1. Cantón", opciones_canton)

        # Aplicamos filtro de Cantón para el siguiente paso
        df_canton = df[df['CANTON'].isin(selected_cantones)] if selected_cantones else df

        # Filtro 2: Entidad / Distrito (Depende del Cantón)
        opciones_entidad = sorted(df_canton['ENTIDAD'].dropna().unique()) if 'ENTIDAD' in df_canton.columns else []
        selected_entidades = st.sidebar.multiselect("2. Entidad (Distrito)", opciones_entidad)

        # Aplicamos filtro de Entidad
        df_entidad = df_canton[df_canton['ENTIDAD'].isin(selected_entidades)] if selected_entidades else df_canton

        # Filtro 3: Tipo de Centro de Salud (Depende de Entidad/Cantón)
        opciones_tipo = sorted(df_entidad['TIPO_CENTRO_SALUD'].dropna().unique()) if 'TIPO_CENTRO_SALUD' in df_entidad.columns else []
        selected_tipos = st.sidebar.multiselect("3. Tipo de Centro de Salud", opciones_tipo)

        # Aplicamos filtro de Tipo de Centro
        df_tipo = df_entidad[df_entidad['TIPO_CENTRO_SALUD'].isin(selected_tipos)] if selected_tipos else df_entidad

        # Filtro 4: Centro de Salud (¡Solo saldrán los centros del tipo/cantón seleccionado!)
        opciones_centro = sorted(df_tipo['CENTRO_SALUD'].dropna().unique()) if 'CENTRO_SALUD' in df_tipo.columns else []
        selected_centros = st.sidebar.multiselect("4. Centro de Salud / Establecimiento", opciones_centro)

        # Aplicamos filtro de Centro de Salud
        df_centro = df_tipo[df_tipo['CENTRO_SALUD'].isin(selected_centros)] if selected_centros else df_tipo

        # Filtro 5: Profesional (¡Solo saldrán los médicos que pertenezcan a los centros filtrados!)
        opciones_profesional = sorted(df_centro['PROFESIONAL'].dropna().unique()) if 'PROFESIONAL' in df_centro.columns else []
        selected_profesionales = st.sidebar.multiselect("5. Profesional Médico", opciones_profesional)

        # Aplicamos filtro de Profesional
        df_prof = df_centro[df_centro['PROFESIONAL'].isin(selected_profesionales)] if selected_profesionales else df_centro

        # Filtro 6: Código de Atención CIE-10
        opciones_atencion = sorted(df_prof['ATENCION'].dropna().unique()) if 'ATENCION' in df_prof.columns else []
        selected_atenciones = st.sidebar.multiselect("6. Código de Atención (CIE-10)", opciones_atencion)

        # Filtro 7: Rango de Fechas (Mantiene el contexto de lo filtrado)
        min_date = df_prof['FECHA_ATENCION'].min().date() if not df_prof['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        max_date = df_prof['FECHA_ATENCION'].max().date() if not df_prof['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        date_range = st.sidebar.date_input("7. Rango de Fechas", [min_date, max_date])

        # --- 4. DATA FINAL FILTRADA CONSOLIDADA ---
        df_filtered = df_prof.copy()
        if selected_atenciones: 
            df_filtered = df_filtered[df_filtered['ATENCION'].isin(selected_atenciones)]
        if len(date_range) == 2:
            df_filtered = df_filtered[(df_filtered['FECHA_ATENCION'].dt.date >= date_range[0]) & (df_filtered['FECHA_ATENCION'].dt.date <= date_range[1])]

        # --- 5. TARJETAS DE INDICADORES (KPIs) ---
        total_atenciones = len(df_filtered)
        top_diag = df_filtered['DIAGNOSTICO'].value_counts().index[0] if 'DIAGNOSTICO' in df_filtered.columns and not df_filtered['DIAGNOSTICO'].empty else "N/A"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='metric-box'><small style='color: #7f8c8d; font-weight: bold;'>TOTAL DE ATENCIONES FILTRADAS</small><h2 style='margin: 0; color: #2980b9;'>{total_atenciones:,}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-box' style='border-left: 5px solid #27ae60;'><small style='color: #7f8c8d; font-weight: bold;'>DIAGNÓSTICO MÁS FRECUENTE</small><h4 style='margin: 0; color: #27ae60; font-size: 16px;'>{top_diag}</h4></div>", unsafe_allow_html=True)

        # --- 6. GRÁFICOS DE BARRAS COMPARATIVOS ---
        st.subheader("📊 Análisis Comparativo Operativo")
        g1, g2 = st.columns(2)
        
        with g1:
            if 'TIPO_ATENCION' in df_filtered.columns:
                fig_tipo = px.bar(df_filtered['TIPO_ATENCION'].value_counts().reset_index(), x='TIPO_ATENCION', y='count', title="Distribución por Tipo de Atención (Intramural / Extramural)", labels={'count':'Cantidad', 'TIPO_ATENCION': 'Modalidad'}, color='TIPO_ATENCION', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_tipo.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_tipo, use_container_width=True)

        with g2:
            if 'CRONOLOGIA' in df_filtered.columns:
                fig_crono = px.bar(df_filtered['CRONOLOGIA'].value_counts().reset_index(), x='CRONOLOGIA', y='count', title="Distribución por Cronología (Primera / Subsecuente)", labels={'count':'Cantidad', 'CRONOLOGIA': 'Evolución'}, color='CRONOLOGIA', color_discrete_sequence=px.colors.qualitative.Safe)
                fig_crono.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_crono, use_container_width=True)

        # --- 7. TABLA DE REGISTROS ---
        st.subheader("📋 Registros Detallados")
        with st.expander("Expandir para auditar la tabla de datos completa"):
            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"🚨 Error general de procesamiento: {e}")
else:
    st.info("💡 Por favor, carga el archivo Excel en el panel izquierdo para activar los filtros dependientes.")
