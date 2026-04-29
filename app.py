import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. ESTILO "COMMAND CENTER" (Alto contraste, sin opacidad)
st.set_page_config(page_title="Customs PDF Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    .css-1r6slb0 { background-color: #0a0a0a; border: 1px solid #00FF41; padding: 20px; border-radius: 10px; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New', Courier, monospace; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE EXTRACCIÓN CORRELACIONADA
def analizar_pdf_estructurado(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_total = ""
    for pagina in doc:
        texto_total += pagina.get_text()

    # Buscamos todos los datos con RegEx
    rfcs = re.findall(r'[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}', texto_total)
    pedimentos = re.findall(r'\d{2}  \d{2}  \d{4}  \d{7}', texto_total)
    fechas = re.findall(r'\d{2}/\d{2}/\d{4}', texto_total)
    
    # Intentamos crear una estructura de tabla (Filas)
    # Si el PDF es un reporte con varios registros, intentamos emparejarlos
    max_len = max(len(rfcs), len(pedimentos), len(fechas))
    
    # Rellenamos con "N/A" para que la tabla no falle si falta algún dato
    datos_limpios = []
    for i in range(max_len):
        fila = {
            "ID_OPERACION": i + 1,
            "PEDIMENTO": pedimentos[i] if i < len(pedimentos) else "No detectado",
            "RFC_CLIENTE": rfcs[i] if i < len(rfcs) else "No detectado",
            "FECHA_PAGO": fechas[i] if i < len(fechas) else "No detectada"
        }
        datos_limpios.append(fila)
    
    return pd.DataFrame(datos_limpios), texto_total

# 3. INTERFAZ
st.title("⚡ PDF DATA EXTRACTOR PRO")
st.write("---")

archivo = st.sidebar.file_uploader("Sube el PDF del Pedimento o Factura", type=["pdf"])

if archivo:
    df_resultado, texto_bruto = analizar_pdf_estructurado(archivo)
    
    # MÉTRICAS RESUMIDAS (Cuadros de valor)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("REGISTROS DETECTADOS", len(df_resultado))
    with col2:
        st.metric("PÁGINAS PROCESADAS", "Completo")

    st.write("### 📋 VISTA ESTRUCTURADA (DATOS CORRELACIONADOS)")
    # Aquí es donde ocurre la magia: ya no son cuadros sueltos, es una tabla
    st.table(df_resultado) # Usamos table para que sea más "sólida" visualmente

    # OPCIÓN DE DESCARGA
    csv = df_resultado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DESCARGAR ESTA EXTRACCIÓN A EXCEL/CSV", csv, "extraccion_pdf.csv", "text/csv")

    with st.expander("🔍 VER AUDITORÍA DE TEXTO (RAW DATA)"):
        st.text(texto_bruto)
else:
    st.info("💡 Sube un PDF para convertir sus datos en una tabla estructurada.")