import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# Configuración visual de alto impacto
st.set_page_config(page_title="Garber Customs Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #0a0a0a; border: 1px solid #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

def procesar_pedimento_garber(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto = ""
    for pagina in doc:
        texto += pagina.get_text("text") + "\n"

    # 1. Extraer Encabezado [cite: 3, 6, 10]
    pedimento = re.search(r'NUM\. PEDIMENTO:\s*([\d\s]{15,})', texto)
    rfc = re.search(r'RFC:\s*([A-Z0-9]{12,13})', texto)
    val_aduana = re.search(r'VALOR ADUANA:\s*([\d,]+)', texto)
    tipo_cambio = re.search(r'TIPO DE CAMBIO:\s*([\d.]+)', texto)

    # 2. Extraer Partidas Correlacionadas (Factura + Parte + PO) [cite: 189, 206, 224]
    # Este patrón busca específicamente el bloque que vimos en tu imagen
    bloques = re.findall(r'FACTURA:\s*(\S+)\s*NO\.\s*PARTE:\s*(\S+)\s*PO:\s*(\d+)', texto)
    
    # 3. Extraer Fracciones (8 dígitos aislados) [cite: 164, 190, 271]
    fracciones = re.findall(r'\n(\d{8})\n', texto)

    # Limpiamos la lista de fracciones para quitar duplicados de cabecera si los hay
    fracciones = [f for f in fracciones if not f.startswith('0000')]

    # Crear filas para la tabla
    filas = []
    for i, b in enumerate(bloques):
        filas.append({
            "ITEM": i + 1,
            "FACTURA": b[0],
            "NÚMERO DE PARTE": b[1],
            "P.O. (ORDEN)": b[2],
            "FRACCIÓN": fracciones[i] if i < len(fracciones) else "Ver PDF"
        })
    
    resumen = {
        "pedimento": pedimento.group(1).strip() if pedimento else "No detectado",
        "rfc": rfc.group(1) if rfc else "No detectado",
        "valor": val_aduana.group(1) if val_aduana else "0",
        "tc": tipo_cambio.group(1) if tipo_cambio else "1.0"
    }
    
    return pd.DataFrame(filas), resumen, texto

st.title("🖥️ SISTEMA DE CONTROL GARBER V3")

archivo_subido = st.sidebar.file_uploader("Cargar PDF", type=["pdf"])

if archivo_subido:
    df, info, raw = procesar_pedimento_garber(archivo_subido)
    
    # Métricas Principales [cite: 3, 6, 10]
    c1, c2, c3 = st.columns(3)
    c1.metric("PEDIMENTO", info["pedimento"])
    c2.metric("RFC IMPORTADOR", info["rfc"])
    c3.metric("VALOR ADUANA (MXN)", f"${info['valor']}")

    st.markdown("---")
    st.subheader("📋 PARTIDAS ESTRUCTURADAS")
    
    if not df.empty:
        # Buscador dinámico que filtra toda la tabla
        query = st.text_input("🔍 BUSCADOR UNIVERSAL (Filtra por cualquier dato de la tabla):")
        if query:
            df = df[df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)]
        
        # Despliegue de la tabla profesional
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botón para descargar a Excel
        st.download_button("📥 EXPORTAR A EXCEL", df.to_csv(index=False), "reporte_aduana.csv")
    else:
        st.warning("No se encontraron partidas con el formato FACTURA/PARTE/PO.")

    with st.expander("Ver Texto Original del PDF"):
        st.text(raw)
else:
    st.info("Favor de subir el Pedimento para procesar la tabla.")