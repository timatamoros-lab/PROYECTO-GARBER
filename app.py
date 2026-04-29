import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. ESTILO TERMINAL DE ALTO CONTRASTE
st.set_page_config(page_title="Customs PDF Scanner Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; }
    [data-testid="stMetric"] { background-color: #050505; border: 1px solid #00FF41; }
    h1, h2, h3 { color: #00FF41 !important; }
    .stDataFrame { border: 1px solid #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE LIMPIEZA Y EXTRACCIÓN
def analizar_aduana_pro(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_limpio = ""
    
    for pagina in doc:
        # Extraemos texto ignorando elementos gráficos pequeños (donde suelen estar QR/Barcodes)
        texto_limpio += pagina.get_text("text")

    # --- FILTROS DE SEGURIDAD (Ignorar códigos de barras/QR) ---
    # Los códigos de barras suelen ser cadenas de más de 20 números seguidos. Los borramos.
    texto_procesado = re.sub(r'\d{20,}', '', texto_limpio)

    # --- EXTRACCIÓN POR ANCLAJE (REGEX AVANZADO) ---
    # Buscamos patrones específicos del formato de pedimento mexicano
    patrones = {
        # Formato: 24  47  3956  4001234 (con o sin espacios)
        "PEDIMENTO": re.findall(r'\d{2}\s{1,2}\d{2}\s{1,2}\d{4}\s{1,2}\d{7}', texto_procesado),
        # RFC: 3-4 letras, 6 números, 3 alfanuméricos
        "RFC": re.findall(r'[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}', texto_procesado),
        # Valor Aduana: Buscamos el número que sigue a la palabra clave
        "VALOR_ADUANA": re.findall(r'(?:VALOR ADUANA|VAL\. ADUANA)[:\s]*([\d,]+)', texto_procesado, re.IGNORECASE)
    }

    # --- ORDENAMIENTO DE DATOS ---
    # Creamos una lista de diccionarios asegurando que los datos se alineen
    max_filas = max(len(patrones["PEDIMENTO"]), len(patrones["RFC"]), 1)
    tabla = []
    
    for i in range(max_filas):
        fila = {
            "PEDIMENTO": patrones["PEDIMENTO"][i] if i < len(patrones["PEDIMENTO"]) else "N/A",
            "RFC_DETECTADO": patrones["RFC"][i] if i < len(patrones["RFC"]) else "N/A",
            "VALOR_APROX": patrones["VALOR_ADUANA"][i] if i < len(patrones["VALOR_ADUANA"]) else "Ver en PDF"
        }
        # Solo agregamos si la fila no está vacía de datos reales
        if fila["PEDIMENTO"] != "N/A" or fila["RFC_DETECTADO"] != "N/A":
            tabla.append(fila)

    return pd.DataFrame(tabla), texto_procesado

# 3. INTERFAZ DE USUARIO
st.title("🖥️ MOTOR DE EXTRACCIÓN ADUANERA V3")
st.write("Filtro de códigos de barras y QR activado.")

archivo = st.sidebar.file_uploader("Cargar Pedimento PDF", type=["pdf"])

if archivo:
    with st.spinner('Analizando estructura del documento...'):
        df, texto_raw = analizar_aduana_pro(archivo)
        
        if not df.empty:
            st.success("Extracción completada con éxito.")
            
            # Buscador sobre los datos extraídos
            busqueda = st.text_input("🔍 Buscar dentro de lo extraído:")
            if busqueda:
                df = df[df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
            
            st.write("### 📋 RESULTADOS ORDENADOS")
            st.dataframe(df, use_container_width=True)
            
            # Botón de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Exportar a Excel (CSV)", csv, "aduana_clean.csv", "text/csv")
        else:
            st.warning("No se detectaron patrones de pedimento claros. Revisa la calidad del PDF.")

        with st.expander("Ver Auditoría de Texto (Limpieza de códigos aplicada)"):
            st.text(texto_raw)
else:
    st.info("Esperando archivo... El sistema ignorará automáticamente los códigos de barras y QR para evitar ruido.")