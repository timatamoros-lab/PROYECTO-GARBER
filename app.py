import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. CONFIGURACIÓN DE INTERFAZ PROFESIONAL
st.set_page_config(page_title="Garber Customs Ultra-Extractor", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #111; border: 1px solid #00FF41; box-shadow: 0 0 10px #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New'; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_texto_extremo(t):
    """Elimina ruido de tablas, comillas y saltos de línea para normalizar el texto"""
    return t.replace('"', '').replace('\n', ' ').replace(',', '').replace('\\n', ' ')

def extractor_total_power(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_bruto = ""
    for pagina in doc:
        texto_bruto += pagina.get_text("text") + "\n"
    
    # Normalizamos el texto para que las búsquedas sean infalibles
    texto_norm = limpiar_texto_extremo(texto_bruto)

    # --- DICCIONARIO DE PATRONES (Mapeo Inteligente) ---
    def buscar(etiqueta, patron):
        # Busca la etiqueta y captura lo que sigue, ignorando basura visual
        match = re.search(f"{etiqueta}\s*[:\-]*\s*({patron})", texto_norm, re.IGNORECASE)
        return match.group(1).strip() if match else "N/A"

    # Campos de Encabezado
    data_head = {
        "PEDIMENTO": buscar("NUM. PEDIMENTO", r"[\d\s]{15,17}"),
        "RFC": buscar("RFC", r"[A-Z0-9]{12,13}"),
        "VALOR_ADUANA": buscar("VALOR ADUANA", r"[\d\.]+"),
        "TIPO_CAMBIO": buscar("TIPO DE CAMBIO", r"[\d\.]+"),
        "FECHA_PAGO": buscar("FECHA DE PAGO", r"\d{2}/\d{2}/\d{4}"),
        "PESO_BRUTO": buscar("PESO BRUTO", r"[\d\.]+")
    }

    # --- EXTRACCIÓN DE PARTIDAS (EL DESGLOSE) ---
    # Buscamos la tríada Factura + Parte + PO
    bloques_partidas = re.findall(r'FACTURA:\s*(\S+)\s*NO\.\s*PARTE:\s*(\S+)\s*PO:\s*(\d+)', texto_bruto)
    
    # Buscamos Fracciones Arancelarias (8 dígitos solos en una línea)
    fracciones = re.findall(r'\n(\d{8})\n', texto_bruto)

    lista_final = []
    if bloques_partidas:
        for i, b in enumerate(bloques_partidas):
            item = {
                "ARCHIVO": archivo.name,
                "PEDIMENTO": data_head["PEDIMENTO"].replace(" ", ""),
                "RFC_CLIENTE": data_head["RFC"],
                "VALOR_ADUANA_TOT": data_head["VALOR_ADUANA"],
                "FECHA": data_head["FECHA_PAGO"],
                "FACTURA_ITEM": b[0],
                "NUM_PARTE": b[1],
                "P.O.": b[2],
                "FRACCION": fracciones[i] if i < len(fracciones) else "N/A"
            }
            lista_final.append(item)
    else:
        # Si no hay partidas, registramos el encabezado solo
        lista_final.append({**{"ARCHIVO": archivo.name}, **data_head, **{"AVISO": "Sin partidas detectadas"}})

    return lista_final

# --- INTERFAZ ---
st.title("⚓ GARBER ULTRA-EXTRACTOR V5")
st.write("Carga masiva y desglose automático de pedimentos.")

archivos = st.sidebar.file_uploader("📂 SUBIR PDFS", type=["pdf"], accept_multiple_files=True)

if archivos:
    datos_consolidados = []
    for f in archivos:
        try:
            datos_consolidados.extend(extractor_total_power(f))
        except Exception as e:
            st.error(f"Error en {f.name}: {e}")
    
    df = pd.DataFrame(datos_consolidados)

    # Métricas de Poder
    m1, m2, m3 = st.columns(3)
    m1.metric("ARCHIVOS", len(archivos))
    m2.metric("TOTAL LINEAS", len(df))
    m3.metric("CLIENTES", df['RFC'].nunique() if 'RFC' in df.columns else 0)

    st.markdown("---")
    
    # Buscador Universal
    filtro = st.text_input("🔍 BUSCADOR INTELIGENTE (Filtra facturas, partes, RFC o pedimentos...)")
    if filtro:
        df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]

    # Tabla Maestra
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Exportación masiva
    st.download_button(
        "📥 DESCARGAR BASE DE DATOS (CSV/EXCEL)",
        df.to_csv(index=False).encode('utf-8'),
        "aduana_consolidado.csv",
        "text/csv"
    )
else:
    st.info("Sistema listo. Esperando archivos para el desglose masivo.")