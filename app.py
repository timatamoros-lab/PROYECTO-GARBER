import streamlit as st
import pandas as pd
import plotly.express as px
import fitz  # PyMuPDF
import re

# 1. CONFIGURACIÓN E INTERFAZ "CYBER"
st.set_page_config(page_title="AI Customs Scanner", layout="wide", page_icon="🕵️‍♂️")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00FF41; } /* Estilo Terminal Matrix */
    [data-testid="stMetric"] { background-color: #111; border: 1px solid #00FF41; border-radius: 10px; }
    .stTextInput>div>div>input { background-color: #000; color: #00FF41; border: 1px solid #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0 0 10px #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE EXTRACCIÓN PDF
def extraer_datos_pdf(archivo):
    documento = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_completo = ""
    for pagina in documento:
        texto_completo += pagina.get_text()
    
    # Buscador de patrones (Ajusta estos según tus formatos)
    datos = {
        "RFC Detectados": list(set(re.findall(r'[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}', texto_completo))),
        "Posibles Pedimentos": list(set(re.findall(r'\d{2}  \d{2}  \d{4}  \d{7}', texto_completo))),
        "Fechas": list(set(re.findall(r'\d{2}/\d{2}/\d{4}', texto_completo)))
    }
    return texto_completo, datos

# 3. BARRA LATERAL
with st.sidebar:
    st.title("📟 AI SCANNER")
    archivo = st.file_uploader("SUBIR ARCHIVO (PDF o EXCEL)", type=["pdf", "xlsx", "csv"])
    st.markdown("---")
    st.write("Estado del Sistema: **ACTIVO**")

# 4. LÓGICA DE PROCESAMIENTO
if archivo:
    if archivo.type == "application/pdf":
        st.write("### 📂 Análisis de Documento PDF")
        texto, hallazgos = extraer_datos_pdf(archivo)
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("RFCs Encontrados", len(hallazgos["RFC Detectados"]))
            st.write("#### RFC Detectados:")
            st.write(hallazgos["RFC Detectados"])
            
        with c2:
            st.metric("Pedimentos Detectados", len(hallazgos["Posibles Pedimentos"]))
            st.write("#### Referencias:")
            st.write(hallazgos["Posibles Pedimentos"])
            
        with st.expander("Ver texto completo extraído"):
            st.text(texto)

    else:
        # Lógica para Excel (La que ya teníamos)
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        st.write("### 📊 Análisis de Base de Datos")
        
        # Buscador Universal
        busqueda = st.text_input("🔍 FILTRO DE SEGURIDAD")
        if busqueda:
            df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        st.metric("REGISTROS TOTALES", len(df))
        st.dataframe(df, use_container_width=True)
        
        # Gráfica Rápida si hay datos numéricos
        num_cols = df.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            fig = px.histogram(df, x=num_cols[0], title=f"Distribución de {num_cols[0]}", color_discrete_sequence=['#00FF41'])
            fig.update_layout(paper_bgcolor='black', plot_bgcolor='black', font_color="#00FF41")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.title("🕵️‍♂️ SISTEMA DE INTELIGENCIA ADUANERA")
    st.write("Esperando carga de archivos para escaneo de patrones...")