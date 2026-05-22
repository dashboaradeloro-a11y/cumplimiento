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
st.markdown("Sube tu archivo de Excel. Los filtros principales operan en una cascada jerárquica estricta.")

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

        # --- 3. LÓGICA DE FILTROS EN CASCADA JERÁRQUICA ---
        st.sidebar.header("🔍 Jerarquía de Filtros (Cascada)")

        # PASO 1: Entidad (Distrito) - Muestra todo el universo inicial
        opciones_entidad = sorted(df['ENTIDAD'].dropna().unique()) if 'ENTIDAD' in df.columns else []
        selected_entidades = st.sidebar.multiselect("1. Entidad (Distrito)", opciones_entidad)

        # Aplicamos filtro de Entidad para el siguiente paso
        df_paso1 = df[df['ENTIDAD'].isin(selected_entidades)] if selected_entidades else df

        # PASO 2: Tipo de Centro de Salud (Depende exclusivamente de la Entidad elegida)
        opciones_tipo = sorted(df_paso1['TIPO_CENTRO_SALUD'].dropna().unique()) if 'TIPO_CENTRO_SALUD' in df_paso1.columns else []
        selected_tipos = st.sidebar.multiselect("2. Tipo de Centro de Salud", opciones_tipo)

        # Aplicamos filtro de Tipo de Centro para el siguiente paso
        df_paso2 = df_paso1[df_paso1['TIPO_CENTRO_SALUD'].isin(selected_tipos)] if selected_tipos else df_paso1

        # PASO 3: Establecimiento / Centro de Salud (Depende de Entidad + Tipo de Centro)
        opciones_centro = sorted(df_paso2['CENTRO_SALUD'].dropna().unique()) if 'CENTRO_SALUD' in df_paso2.columns else []
        selected_centros = st.sidebar.multiselect("3. Establecimiento (Centro de Salud)", opciones_centro)

        # Aplicamos filtro de Establecimiento para el siguiente paso
        df_paso3 = df_paso2[df_paso2['CENTRO_SALUD'].isin(selected_centros)] if selected_centros else df_paso2

        # PASO 4: Profesional (Depende de todo lo anterior: Entidad + Tipo + Establecimiento)
        opciones_profesional = sorted(df_paso3['PROFESIONAL'].dropna().unique()) if 'PROFESIONAL' in df_paso3.columns else []
        selected_profesionales = st.sidebar.multiselect("4. Profesional Médico", opciones_profesional)

        # Aplicamos filtro de Profesional
        df_paso4 = df_paso3[df_paso3['PROFESIONAL'].isin(selected_profesionales)] if selected_profesionales else df_paso3

        # --- FILTROS ADICIONALES DE SEGMENTACIÓN ---
        st.sidebar.markdown("---")
        st.sidebar.header("📌 Segmentación Opcional")
        
        # Cantón, Atenciones y Fechas heredan el estado de lo filtrado en la cascada
        opciones_canton = sorted(df_paso4['CANTON'].dropna().unique()) if 'CANTON' in df_paso4.columns else []
        selected_cantones = st.sidebar.multiselect("Cantón", opciones_canton)
        if selected_cantones:
            df_paso4 = df_paso4[df_paso4['CANTON'].isin(selected_cantones)]

        opciones_atencion = sorted(df_paso4['ATENCION'].dropna().unique()) if 'ATENCION' in df_paso4.columns else []
        selected_atenciones = st.sidebar.multiselect("Código de Atención (CIE-10)", opciones_atencion)
        if selected_atenciones:
            df_paso4 = df_paso4[df_paso4['ATENCION'].isin(selected_atenciones)]

        # Rango de Fechas
        min_date = df_paso4['FECHA_ATENCION'].min().date() if not df_paso4['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        max_date = df_paso4['FECHA_ATENCION'].max().date() if not df_paso4['FECHA_ATENCION'].isnull().all() else pd.Timestamp.today().date()
        date_range = st.sidebar.date_input("Rango de Fechas", [min_date, max_date])

        # --- 4. CONSOLIDACIÓN FINAL DEL DATAFRAME ---
        df_filtered = df_paso4.copy()
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
    st.info("💡 Por favor, carga el archivo Excel para activar el flujo en cascada jerárquica.")
