import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. ESTILO "COMMAND CENTER" (Visualización de Datos Profesional)
st.set_page_config(page_title="AI Data Analytics - Garber", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #00FF41; }
    [data-testid="stMetric"] { 
        background-color: #111; 
        border-left: 5px solid #00FF41; 
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0, 255, 65, 0.2);
    }
    .stTabs [data-baseweb="tab"] { color: #00FF41 !important; font-size: 18px; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New'; text-transform: uppercase; }
    .stDataFrame { border: 1px solid #00FF41; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE PROCESAMIENTO ANALÍTICO
def analizar_pdf_avanzado(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_total = ""
    paginas = []
    for pagina in doc:
        t = pagina.get_text("text")
        texto_total += t + "\n"
        paginas.append(t)

    # --- EXTRACCIÓN DE ENCABEZADO ---
    def extraer(patron, txt):
        match = re.search(patron, txt, re.IGNORECASE)
        return match.group(1).replace('"', '').strip() if match else "N/A"

    pedimento = extraer(r'NUM\. PEDIMENTO:?[\s"\\n]*([\d\s]{15,})', texto_total).replace(" ", "")
    rfc = extraer(r'RFC:?[\s"\\n]*([A-Z0-9]{12,13})', texto_total)
    val_aduana = extraer(r'VALOR ADUANA:?[\s"\\n]*([\d,]+)', texto_total).replace(",", "")
    val_comercial = extraer(r'VALOR COMERCIAL:?[\s"\\n]*([\d,]+)', texto_total).replace(",", "")
    peso = extraer(r'PESO BRUTO:?[\s"\\n]*([\d,.]+)', texto_total).replace(",", "")
    tc = extraer(r'TIPO DE CAMBIO:?[\s"\\n]*([\d.]+)', texto_total)

    # --- DESGLOSE DE PARTIDAS (Cualquier PDF con estructura de tabla) ---
    # Capturamos Factura, Parte y PO
    items_raw = re.findall(r'FACTURA:\s*(\S+)\s*NO\.\s*PARTE:\s*(\S+)\s*PO:\s*(\d+)', texto_total)
    fracciones = re.findall(r'\n(\d{8})\n', texto_total)

    filas = []
    for i, item in enumerate(items_raw):
        filas.append({
            "N_PEDIMENTO": pedimento,
            "FECHA": extraer(r'FECHA DE PAGO\s*(\d{2}/\d{2}/\d{4})', texto_total),
            "FACTURA": item[0],
            "NUM_PARTE": item[1],
            "P.O.": item[2],
            "FRACCION": fracciones[i] if i < len(fracciones) else "N/A",
            "IMPORTADOR": rfc
        })

    # Si no detectó estructura de pedimento, buscamos cualquier tabla genérica
    if not filas:
        lineas = texto_total.split('\n')
        for line in lineas:
            partes = re.split(r'\s{2,}', line.strip())
            if len(partes) > 2:
                filas.append({f"COL_{j}": p for j, p in enumerate(partes)})

    return pd.DataFrame(filas), {
        "ped": pedimento, "rfc": rfc, "val": val_aduana, "peso": peso, "tc": tc, "val_com": val_comercial
    }

# 3. INTERFAZ DE USUARIO (DASHBOARD)
st.title("📟 GARBER ANALYTICS COMMAND")
st.write("### Sistema de Análisis y Consolidación Masiva de Datos")

archivos = st.sidebar.file_uploader("📂 CARGAR PDFs (Cualquier tipo)", type=["pdf"], accept_multiple_files=True)

if archivos:
    df_maestro = pd.DataFrame()
    resumenes = []

    for f in archivos:
        df_temp, info_temp = analizar_pdf_avanzado(f)
        df_maestro = pd.concat([df_maestro, df_temp], ignore_index=True)
        resumenes.append(info_temp)

    # --- DASHBOARD DE MÉTRICAS ---
    st.write("## 💹 VISTA GENERAL")
    c1, c2, c3, c4 = st.columns(4)
    
    total_val = sum([float(r['val']) for r in resumenes if r['val'].replace('.','').isdigit()])
    total_peso = sum([float(r['peso']) for r in resumenes if r['peso'].replace('.','').isdigit()])
    
    c1.metric("ARCHIVOS PROCESADOS", len(archivos))
    c2.metric("TOTAL PARTIDAS", len(df_maestro))
    c3.metric("VALOR ADUANA TOTAL", f"${total_val:,.2f}")
    c4.metric("PESO BRUTO TOTAL", f"{total_peso:,.2f} KG")

    # --- TABS DE VISUALIZACIÓN ---
    tab_reporte, tab_auditoria, tab_busqueda = st.tabs(["📊 REPORTE DE EXPORTACIÓN", "🔍 AUDITORÍA DE DATOS", "🔎 BUSCADOR FILTRADO"])

    with tab_reporte:
        st.write("Esta tabla contiene toda la información cruzada de los PDFs:")
        st.dataframe(df_maestro, use_container_width=True, hide_index=True)
        
        # EXPORTACIÓN LIMPIA
        csv = df_maestro.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR MASTER EXCEL (CSV)", csv, "reporte_consolidado.csv", "text/csv")

    with tab_auditoria:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**ENCABEZADOS DETECTADOS:**")
            st.json(resumenes)
        with col_b:
            st.write("**DISTRIBUCIÓN POR ARCHIVO:**")
            st.bar_chart(df_maestro['FACTURA'].value_counts() if 'FACTURA' in df_maestro.columns else [0])

    with tab_busqueda:
        target = st.text_input("🔍 ESCANEO RÁPIDO: Escribe un Número de Parte, PO o Factura:")
        if target:
            resultado = df_maestro[df_maestro.astype(str).apply(lambda x: x.str.contains(target, case=False)).any(axis=1)]
            st.write(f"Resultados para: {target}")
            st.dataframe(resultado, use_container_width=True)

else:
    st.info("SISTEMA LISTO. Sube uno o varios archivos para comenzar el desglose masivo.")
    st.image("https://img.icons8.com/nolan/128/data-configuration.png")