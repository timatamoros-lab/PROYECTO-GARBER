import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

st.set_page_config(page_title="Garber Total Extractor", layout="wide")

# Interfaz estilo Terminal de Datos
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #0a0a0a; border: 1px solid #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0 0 5px #00FF41; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

def extraer_todo_el_pedimento(file_engine):
    doc = fitz.open(stream=file_engine.read(), filetype="pdf")
    texto = ""
    for pagina in doc:
        texto += pagina.get_text("text") + "\n"

    # --- EXTRACCIÓN DE ENCABEZADO (CAMPOS ÚNICOS) ---
    def buscar(patron, txt):
        res = re.search(patron, txt)
        return res.group(1).strip() if res else "N/A"

    pedimento = buscar(r'NUM\. PEDIMENTO:\s*([\d\s]{15,})', texto).replace(" ", "")
    rfc = buscar(r'RFC:\s*([A-Z0-9]{12,13})', texto)
    cve_ped = buscar(r'CVE\. PEDIMENTO:\s*([A-Z0-9]{2})', texto)
    regimen = buscar(r'REGIMEN:\s*([A-Z0-9]{3})', texto)
    aduana_es = buscar(r'ADUANA E/S:\s*(\d{3})', texto)
    tipo_cambio = buscar(r'TIPO DE CAMBIO:\s*([\d.]+)', texto)
    val_aduana = buscar(r'VALOR ADUANA:\s*([\d,]+)', texto)
    val_comercial = buscar(r'VALOR COMERCIAL:\s*([\d,]+)', texto)
    peso_bruto = buscar(r'PESO BRUTO:\s*([\d.]+)', texto)
    fecha_pago = buscar(r'FECHA DE PAGO\s*(\d{2}/\d{2}/\d{4})', texto)

    # --- EXTRACCIÓN DE PARTIDAS (MÚLTIPLES) ---
    # Buscamos el patrón repetitivo de FACTURA, PARTE y PO
    bloques = re.findall(r'FACTURA:\s*(\S+)\s*NO\.\s*PARTE:\s*(\S+)\s*PO:\s*(\d+)', texto)
    # Buscamos las fracciones arancelarias (8 dígitos)
    fracciones = re.findall(r'\n(\d{8})\n', texto)

    datos_finales = []
    
    # Si hay partidas, creamos una fila por cada una con TODO el encabezado repetido
    # Esto es lo que permite que al exportar a Excel puedas filtrar por cualquier campo
    if bloques:
        for i, b in enumerate(bloques):
            datos_finales.append({
                "ARCHIVO": file_engine.name,
                "NUM_PEDIMENTO": pedimento,
                "FECHA_PAGO": fecha_pago,
                "RFC_IMPORTADOR": rfc,
                "CVE_PED": cve_ped,
                "REGIMEN": regimen,
                "ADUANA": aduana_es,
                "TIPO_CAMBIO": tipo_cambio,
                "VALOR_ADUANA_TOTAL": val_aduana,
                "PESO_BRUTO_TOTAL": peso_bruto,
                "FACTURA_PARTIDA": b[0],
                "NUM_PARTE": b[1],
                "PO_ORDEN": b[2],
                "FRACCION_ARANCELARIA": fracciones[i] if i < len(fracciones) else "N/A"
            })
    else:
        # Si no hay partidas detectadas, al menos traemos los datos del encabezado
        datos_finales.append({
            "ARCHIVO": file_engine.name,
            "NUM_PEDIMENTO": pedimento,
            "FECHA_PAGO": fecha_pago,
            "RFC_IMPORTADOR": rfc,
            "VALOR_ADUANA_TOTAL": val_aduana,
            "FACTURA_PARTIDA": "N/A",
            "NUM_PARTE": "N/A",
            "PO_ORDEN": "N/A",
            "FRACCION_ARANCELARIA": "N/A"
        })

    return datos_finales

# --- INTERFAZ PRINCIPAL ---
st.title("⚓ GARBER ULTIMATE EXTRACTOR")
st.write("Sube uno o varios archivos para generar la base de datos completa de pedimentos.")

archivos = st.sidebar.file_uploader("Cargar PDFs", type=["pdf"], accept_multiple_files=True)

if archivos:
    maestro = []
    for f in archivos:
        maestro.extend(extraer_todo_el_pedimento(f))
    
    df = pd.DataFrame(maestro)

    # Mostrar métricas rápidas
    c1, c2, c3 = st.columns(3)
    c1.metric("PEDIMENTOS", df['NUM_PEDIMENTO'].nunique())
    c2.metric("TOTAL FILAS", len(df))
    c3.metric("VALOR ADUANA ACUM.", f"${df['VALOR_ADUANA_TOTAL'].iloc[0] if not df.empty else 0}")

    st.markdown("---")
    
    # Buscador Universal
    filtro = st.text_input("🔍 Filtro Maestro (Busca por Pedimento, RFC, Parte, Factura o PO):")
    if filtro:
        df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]

    st.subheader("📋 Vista de Datos Estructurada")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Exportación
    st.download_button(
        label="📥 EXPORTAR TODO A EXCEL (CSV)",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="reporte_aduanero_total.csv",
        mime="text/csv"
    )
else:
    st.info("Arrastra los PDFs aquí para extraer todos los campos ordenados.")