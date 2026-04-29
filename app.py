import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Portal TI - Gestión Aduanera",
    page_icon="⚓",
    layout="wide"
)

# Estilos CSS para mejorar la apariencia
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #1f77b4; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1f77b4; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2271/2271068.png", width=100)
    st.title("Panel de Control")
    st.info("Sube el reporte diario de operaciones para comenzar el análisis.")
    
    archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx", "csv"])
    
    st.markdown("---")
    st.write("v1.0.0 - Soporte TI")

# 3. LÓGICA PRINCIPAL
if archivo:
    try:
        # Carga de datos
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)

        # Limpieza básica: Eliminar filas vacías
        df = df.dropna(how='all')

        # --- VALIDACIÓN DE COLUMNAS ---
        # Definimos nombres estándar, si no existen, la app avisará
        columnas_esperadas = ['Pedimento', 'Cliente', 'RFC', 'Valor_Aduana', 'Semaforo']
        faltantes = [col for col in columnas_esperadas if col not in df.columns]

        if faltantes:
            st.error(f"❌ El archivo no tiene las columnas: {', '.join(faltantes)}")
            st.info("Asegúrate de que los encabezados coincidan exactamente.")
            st.stop()

        # --- MÉTRICAS SUPERIORES ---
        st.title("📊 Dashboard Operativo Aduanero")
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric("Total Operaciones", len(df))
        with m2:
            verdes = len(df[df['Semaforo'].str.contains('Verde', case=False, na=False)])
            st.metric("Semaforo Verde", verdes)
        with m3:
            errores_rfc = df['RFC'].isna().sum()
            st.metric("RFCs Faltantes", errores_rfc, delta=f"{errores_rfc} críticos", delta_color="inverse")
        with m4:
            total_valor = df['Valor_Aduana'].sum()
            st.metric("Valor Aduana Total", f"${total_valor:,.2f}")

        st.markdown("---")

        # --- FILTROS Y GRÁFICAS ---
        col_grafica, col_datos = st.columns([1, 1])

        with col_grafica:
            st.subheader("Distribución por Cliente")
            fig = px.pie(df, names='Cliente', values='Valor_Aduana', hole=0.4,
                         title="Participación de Valor por Cliente",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)

        with col_datos:
            st.subheader("Resumen de Semáforo")
            fig2 = px.bar(df, x='Semaforo', color='Semaforo', 
                          title="Conteo de Desaduanamiento",
                          color_discrete_map={'Verde': '#28a745', 'Rojo': '#dc3545'})
            st.plotly_chart(fig2, use_container_width=True)

        # --- TABLA INTERACTIVA ---
        st.subheader("📋 Detalle de la Operación")
        
        # Buscador dinámico
        busqueda = st.text_input("🔍 Buscar por cualquier campo (Pedimento, Cliente, etc.):")
        if busqueda:
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        # Resaltar filas con errores en la tabla
        st.dataframe(df.style.highlight_null(color="#ffcccc"), use_container_width=True)

        # --- EXPORTACIÓN ---
        st.download_button(
            label="📥 Descargar Reporte Depurado (CSV)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='reporte_aduanero_limpio.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
else:
    # Pantalla de bienvenida cuando no hay archivo
    st.title("⚓ Bienvenido al Portal de TI")
    st.write("### Por favor, carga un archivo en el panel izquierdo para visualizar los datos.")
    st.image("https://img.freepik.com/free-vector/data-report-concept-illustration_114360-883.jpg", width=500)