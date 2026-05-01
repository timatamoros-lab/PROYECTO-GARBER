import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
from collections import Counter

# 1. ESTILO "AI INTERFACE"
st.set_page_config(page_title="Universal AI PDF Scanner", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #00FF41; }
    .stTabs [data-baseweb="tab"] { color: #00FF41 !important; }
    .css-1r6slb0 { background-color: #0a0a0a; border: 1px solid #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0 0 10px #00FF41; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE INTELIGENCIA UNIVERSAL
def motor_universal(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_por_pagina = []
    texto_total = ""
    
    for i, pagina in enumerate(doc):
        t = pagina.get_text("text")
        texto_por_pagina.append(t)
        texto_total += t + "\n"

    # --- ANÁLISIS DINÁMICO DE CONTENIDO ---
    
    # Identificar Entidades (Palabras que parecen datos clave)
    # Buscamos: Fechas, Montos, RFCs/IDs, y Correos
    entidades = {
        "FECHAS": list(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', texto_total))),
        "MONTO_MONEDA": list(set(re.findall(r'\$\s?[\d,.]+', texto_total))),
        "IDENTIFICADORES": list(set(re.findall(r'[A-Z]{3,4}[0-9]{6}[A-Z0-9]{3}|[A-Z0-9]{10,20}', texto_total))),
        "EMAILS": list(set(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', texto_total)))
    }

    # Intentar detectar Tablas (Cualquier línea que tenga múltiples datos seguidos)
    lineas = texto_total.split('\n')
    posibles_filas = []
    for line in lineas:
        partes = re.split(r'\s{2,}|,', line) # Divide por 2 espacios o comas
        if len(partes) > 2:
            posibles_filas.append(partes)
    
    df_tabla = pd.DataFrame(posibles_filas) if posibles_filas else pd.DataFrame()

    return texto_total, entidades, df_tabla, len(doc)

# 3. INTERFAZ DE USUARIO
st.title("🧠 UNIVERSAL AI PDF DECODER")
st.write("Sube cualquier documento. El sistema analizará su estructura y extraerá la información relevante.")

archivos = st.sidebar.file_uploader("📂 CARGA MASIVA DE PDFs", type=["pdf"], accept_multiple_files=True)

if archivos:
    for f in archivos:
        with st.expander(f"📄 ANÁLISIS DE: {f.name}", expanded=True):
            texto, datos, tabla, pags = motor_universal(f)
            
            # Pestañas para organizar la info de CUALQUIER PDF
            tab1, tab2, tab3 = st.tabs(["📊 Datos Clave", "📋 Tabla Detectada", "📝 Texto Completo"])
            
            with tab1:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("PÁGINAS", pags)
                col2.metric("DATOS ENCONTRADOS", sum(len(v) for v in datos.values()))
                
                # Mostrar entidades encontradas dinámicamente
                for categoria, valores in datos.items():
                    if valores:
                        st.write(f"**{categoria}:**")
                        st.info(", ".join(valores[:15])) # Limitar a 15 para no saturar

            with tab2:
                if not tabla.empty:
                    st.write("Se detectó la siguiente estructura de datos:")
                    st.dataframe(tabla, use_container_width=True)
                    st.download_button(f"📥 Exportar Tabla de {f.name}", tabla.to_csv(index=False), f"tabla_{f.name}.csv")
                else:
                    st.warning("No se detectó una estructura de tabla clara en este archivo.")

            with tab3:
                st.text_area("Contenido extraído:", texto, height=300)
    
    # BOTÓN PARA CONSOLIDAR TODO (Si son varios archivos)
    if len(archivos) > 1:
        st.sidebar.success("Modo Masivo Activo")
        st.sidebar.button("Generar Reporte Maestro de todos los PDFs")
else:
    st.info("Sistema Universal listo. Sube pedimentos, facturas, contratos o reportes.")