import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA (Estética Dark/Modern)
st.set_page_config(page_title="Customs Intelligence Hub", layout="wide", page_icon="🚀")

# CSS para darle "sabor" (Gradientes y bordes redondeados)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(to right, #ece9e6, #ffffff); }
    .main-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stMetric { border-left: 5px solid #1f77b4; background: #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. LÓGICA DE DETECCIÓN INTELIGENTE
def detectar_columnas(df):
    """Intenta mapear columnas comunes de aduanas aunque cambien los nombres"""
    mapeo = {
        'valor': next((c for c in df.columns if 'valor' in c.lower() or 'monto' in c.lower() or 'usd' in c.lower()), None),
        'cliente': next((c for c in df.columns if 'cliente' in c.lower() or 'nombre' in c.lower() or 'importador' in c.lower()), None),
        'identificador': next((c for c in df.columns if 'pedimento' in c.lower() or 'id' in c.lower() or 'referencia' in c.lower()), None),
        'status': next((c for c in df.columns if 'semaforo' in c.lower() or 'estado' in c.lower() or 'estatus' in c.lower()), None)
    }
    return mapeo

# 3. INTERFAZ LATERAL
with st.sidebar:
    st.title("⚓ Customs Engine")
    st.markdown("---")
    archivo = st.file_uploader("📂 Arrastra cualquier reporte aduanero", type=["xlsx", "csv"])
    if archivo:
        st.success("¡Documento detectado!")

# 4. CUERPO PRINCIPAL
if archivo:
    try:
        # Leer archivo
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        df = df.fillna("N/A") # Evitar valores vacíos feos
        
        # Mapeo inteligente
        columnas = detectar_columnas(df)
        
        # BUSCADOR UNIVERSAL (El "Sabor")
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        query = st.text_input("🔍 Buscador Inteligente (Escribe cualquier Pedimento, RFC o Cliente...)", placeholder="Ejemplo: 2401234...")
        
        if query:
            # Filtra en todas las columnas al mismo tiempo
            mask = df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_display = df[mask]
        else:
            df_display = df

        # MÉTRICAS DINÁMICAS (Se adaptan a lo que encuentre)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Registros Encontrados", len(df_display))
        with col2:
            if columnas['valor']:
                total = df_display[columnas['valor']].replace('[$,]', '', regex=True).astype(float).sum()
                st.metric("Valor Acumulado", f"${total:,.2f}")
        with col3:
            st.metric("Columnas Analizadas", len(df.columns))
        st.markdown('</div>', unsafe_allow_html=True)

        # GRÁFICAS DINÁMICAS (Solo aparecen si detecta datos relevantes)
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("📍 Visualización de Datos")
            # Si hay una columna de valor y una de cliente, hacemos gráfica
            if columnas['valor'] and columnas['cliente']:
                fig = px.bar(df_display.head(20), x=columnas['cliente'], y=columnas['valor'], 
                             color=columnas['cliente'], title="Top 20 por Valor")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 Tip: Si tu Excel tiene columnas de 'Valor' y 'Cliente', aquí verás una gráfica.")

        with c2:
            st.subheader("📋 Acciones")
            st.download_button("📥 Exportar Vista Actual", df_display.to_csv(index=False), "busqueda_aduanas.csv")
            if st.button("🚀 Limpiar Filtros"):
                st.rerun()

        # TABLA ESTILIZADA
        st.subheader("Datos del Reporte")
        st.dataframe(df_display, use_container_width=True, height=400)

    except Exception as e:
        st.error(f"⚠️ No pude procesar este archivo: {e}")

else:
    # Pantalla inicial con diseño "Limpio"
    st.markdown("""
        <div style="text-align: center; padding: 100px;">
            <h1 style="font-size: 50px;">🛳️</h1>
            <h2>Listo para analizar cualquier reporte</h2>
            <p style="color: gray;">Sube un Excel para empezar a buscar datos sin restricciones.</p>
        </div>
        """, unsafe_allow_html=True)