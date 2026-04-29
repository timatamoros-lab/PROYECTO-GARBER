=import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. ESTILO "GARBER COMMAND CENTER"
st.set_page_config(page_title="Garber Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #0a0a0a; border: 1px solid #00FF41; padding: 15px; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New'; text-shadow: 0 0 5px #00FF41; }
    .stDataFrame { border: 1px solid #00FF41; background-color: #000; }
    /* Estilo para que las tablas se vean verdes */
    div[data-testid="stTable"] { background-color: #000; color: #00FF41; border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

def motor_extraccion_estructurada(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_sucio = ""
    for pagina in doc:
        texto_sucio += pagina.get_text("text") + "\n"

    # Limpieza de firmas y certificados largos para evitar errores
    texto_limpio = re.sub(r'[A-Za-z0-9+/]{50,}', '', texto_sucio)
    texto_limpio = re.sub(r'\d{15,}', '', texto_limpio)

    # EXTRACCIÓN DE ENCABEZADO
    # Usamos búsqueda por ancla para los datos principales
    pedimento_match = re.search(r'NUM\. PEDIMENTO:\s*([\d\s]{15,})', texto_limpio)
    rfc_match = re.search(r'Clave en el RFC:\s*([A-Z0-9]{12,13})', texto_limpio)
    valor_aduana_match = re.search(r'VALOR ADUANA:\s*([\d,]+)', texto_limpio)
    fecha_pago_match = re.search(r'FECHA DE PAGO\s*(\d{2}/\d{2}/\d{4})', texto_limpio)

    # EXTRACCIÓN DE PARTIDAS (Agrupando Factura, Parte y PO)
    # Buscamos el bloque específico que me mostraste en la imagen
    bloques_partidas = re.findall(r'FACTURA:\s*(\S+)\s*NO\.\s*PARTE:\s*(\S+)\s*PO:\s*(\d+)', texto_limpio)
    
    # También buscamos las Fracciones Arancelarias (8 dígitos solos)
    fracciones = re.findall(r'\n(\d{8})\n', texto_limpio)

    # Construcción de la tabla
    filas = []
    for i in range(len(bloques_partidas)):
        filas.append({
            "ITEM": i + 1,
            "FACTURA": bloques_partidas[i][0],
            "NO. PARTE": bloques_partidas[i][1],
            "P.O.": bloques_partidas[i][2],
            "FRACCION": fracciones[i] if i < len(fracciones) else "Ver PDF"
        })
    
    resumen = {
        "pedimento": pedimento_match.group(1).replace(" ", "") if pedimento_match else "No detectado",
        "rfc": rfc_match.group(1) if rfc_match else "No detectado",
        "valor": valor_aduana_match.group(1) if valor_aduana_match else "0",
        "fecha": fecha_pago_match.group(1) if fecha_pago_match else "No detectada"
    }

    return pd.DataFrame(filas), resumen, texto_limpio

# --- INTERFAZ STREAMLIT ---
st.title("🖥️ MOTOR ADUANERO GARBER PRO")
st.markdown("---")

archivo = st.sidebar.file_uploader("📂 SUBIR PEDIMENTO PDF", type=["pdf"])

if archivo:
    with st.spinner('Procesando estructura del pedimento...'):
        df_partidas, info, texto_audit = motor_extraccion_estructurada(archivo)
        
        # Panel Superior: Métricas