import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO "HIGH-CONTRAST"
st.set_page_config(page_title="Customs AI - TI Command", layout="wide", page_icon="⚡")

# CSS para inyectar colores vibrantes y quitar lo "opaco"
st.markdown("""
    <style>
    /* Fondo principal oscuro profundo */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Tarjetas de métricas con bordes de neón */
    [data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #00F2FF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 0px 10px rgba(0, 242, 255, 0.2);
    }
    
    /* Títulos con degradado */
    h1, h2, h3 {
        background: linear-gradient(to right, #00F2FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }

    /* Estilo para la tabla */
    .stDataFrame { border: 1px solid #30363D; border-radius: 10px; }
    
    /* Input de búsqueda resaltado */
    .stTextInput>div>div>input {
        background-color: #161B22;
        color: #00F2FF;
        border: 1px solid #7000FF;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIONES DE APOYO
def detect_data(df):
    """Mapeo inteligente para que no se pierda nada"""
    cols = {
        'val': next((c for c in df.columns if any(x in c.lower() for x in ['valor', 'monto', 'total', 'usd'])), None),
        'label': next((c for c in df.columns if any(x in c.lower() for x in ['cliente', 'nombre', 'razon', 'importador'])), None),
        'status': next((c for c in df.columns if any(x in c.lower() for x in ['semaforo', 'estatus', 'estado'])), None)
    }
    return cols

# 3. INTERFAZ LATERAL
with st.sidebar:
    st.title("🛡️ TI ADUANAS")
    st.markdown("---")
    archivo = st.file_uploader("🚀 CARGAR REPORTE", type=["xlsx", "csv"])
    st.markdown("---")
    st.write("Configuración de Interfaz")
    vibrante = st.toggle("Colores de alto impacto", value=True)

# 4. CUERPO PRINCIPAL
if archivo:
    try:
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        df = df.fillna("SIN DATOS")
        mapping = detect_data(df)
        
        # BUSCADOR TIPO GOOGLE (NEÓN)
        st.write("### 🔍 BUSCADOR UNIVERSAL")
        query = st.text_input("", placeholder="Escribe cualquier dato para filtrar el reporte completo...")
        
        if query:
            mask = df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_filtered = df[mask]
        else:
            df_filtered = df

        # MÉTRICAS CON COLOR
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("REGISTROS", len(df_filtered))
        with m2:
            if mapping['val']:
                # Limpiar y sumar valores
                try:
                    total = pd.to_numeric(df_filtered[mapping['val']].replace('[$,]', '', regex=True)).sum()
                    st.metric("VALOR TOTAL", f"${total:,.2f}", delta="USD")
                except: st.metric("VALOR TOTAL", "Error formato")
        with m3:
            st.metric("COLUMNAS", len(df.columns))

        st.markdown("---")

        # GRÁFICAS CON COLORES ELÉCTRICOS
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            if mapping['val'] and mapping['label']:
                st.write("### 🔥 ANÁLISIS DE VOLUMEN")
                fig = px.bar(df_filtered.head(15), x=mapping['label'], y=mapping['val'], 
                             color=mapping['val'], 
                             color_continuous_scale='Turbo') # Colores vibrantes
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            if mapping['status']:
                st.write("### 🚦 SEMÁFORO")
                fig2 = px.pie(df_filtered, names=mapping['status'], hole=0.6,
                              color_discrete_sequence=px.colors.sequential.Electric)
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig2, use_container_width=True)

        # TABLA DE DATOS CRUDA
        st.write("### 📦 DATOS DEL SISTEMA")
        st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Error en el motor de datos: {e}")

else:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; border: 2px dashed #7000FF; padding: 50px; border-radius: 20px;">
            <h1 style="font-size: 80px;">🚢</h1>
            <h2 style="color: #00F2FF;">CENTRO DE MANDO TI</h2>
            <p style="font-size: 20px; color: #888;">Sube un archivo para iniciar el escaneo de seguridad y logística.</p>
        </div>
        """, unsafe_allow_html=True)