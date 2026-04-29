import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# Configuración de estilo "Matrix High-Contrast"
st.set_page_config(page_title="Garber Customs Intelligence", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #0a0a0a; border: 1px solid #00FF41; padding: 15px; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New'; }
    .stDataFrame { border: 1px solid #00FF41; background-color: #000; }
    </style>
    """, unsafe_allow_html=True)

def motor_garber_pdf(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_sucio = ""
    for pagina in doc:
        texto_sucio += pagina.get_text("text") + "\n"

    # --- LIMPIEZA DE "RUIDO" (Firmas, Certificados, Códigos de Barras) ---
    # 1. Eliminamos firmas electrónicas (cadenas larguísimas de caracteres)
    texto_limpio = re.sub(r'[A-Za-z0-9+/]{50,}', '', texto_sucio)
    # 2. Eliminamos números de serie de certificados (cadenas de 20 dígitos)
    texto_limpio = re.sub(r'\d{15,}', '', texto_limpio)

    # --- EXTRACCIÓN DE DATOS CLAVE ---
    datos = {
        "PEDIMENTO": re.findall(r'(\d{2}\s\d{2}\s\d{4}\s\d{7})', texto_limpio),
        "RFC_IMPORT": re.findall(r'RFC:\s([A-Z0-9]{12,13})', texto_limpio),
        "VALOR_ADUANA": re.findall(r'VALOR ADUANA:\s*"?([\d,]+)"?', texto_limpio),
        "TIPO_CAMBIO": re.findall(r'TIPO DE CAMBIO:\s*([\d.]+)', texto_limpio),
        "FECHA_PAGO": re.findall(r'FECHA DE PAGO:\s*(\d{2}/\d{2}/\d{4})', texto_limpio)
    }

    # --- ESTRUCTURACIÓN ---
    # Tomamos el primer pedimento encontrado como principal
    ped_principal = datos["PEDIMENTO"][0] if datos["PEDIMENTO"] else "No detectado"
    rfc_principal = datos["RFC_IMPORT"][0] if datos["RFC_IMPORT"] else "No detectado"
    valor_aduana = datos["VALOR_ADUANA"][0] if datos["VALOR_ADUANA"] else "No detectado"
    fecha = datos["FECHA_PAGO"][0] if datos["FECHA_PAGO"] else "No detectada"

    # También buscamos las PARTIDAS (Cualquier cosa que parezca fracción arancelaria de 8 dígitos)
    partidas = re.findall(r'\n(\d{8})\n', texto_limpio)
    
    resumen = pd.DataFrame([{
        "PEDIMENTO": ped_principal,
        "RFC_IMPORTADOR": rfc_principal,
        "VALOR_ADUANA_MN": valor_aduana,
        "FECHA_PAGO": fecha,
        "TOTAL_PARTIDAS": len(partidas)
    }])

    return resumen, texto_limpio, partidas

# INTERFAZ
st.title("⚓ GARBER DATA COMMAND")
archivo = st.sidebar.file_uploader("Subir Pedimento PDF", type=["pdf"])

if archivo:
    df, texto_audit, fracciones = motor_garber_pdf(archivo)
    
    st.write("### 💎 Resumen de Operación Detectada")
    st.table(df) # Vista limpia y ordenada
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 📦 Fracciones Detectadas")
        st.write(list(set(fracciones)))
    
    with col2:
        st.write("### 🛠️ Herramientas")
        st.download_button("Exportar a CSV", df.to_csv(index=False), "pedimento_extraido.csv")

    with st.expander("🔍 Ver texto procesado (Sin códigos de barras ni firmas)"):
        st.text(texto_audit)
else:
    st.info("Sube el PDF para iniciar el escaneo especializado.")