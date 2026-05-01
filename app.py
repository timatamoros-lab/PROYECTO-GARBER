import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re

# 1. ESTILO "NEURO-INTERFACE" (Más limpio y profesional)
st.set_page_config(page_title="Universal Data Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; }
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Segoe UI', sans-serif; }
    .stDataFrame { border: 1px solid #30363d; }
    .stExpander { background-color: #161b22; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE ANÁLISIS ESTRUCTURAL UNIVERSAL
def motor_inteligente_universal(archivo):
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    texto_completo = ""
    paginas_data = []

    for i, pagina in enumerate(doc):
        # Extraemos texto con "bloques" para identificar tablas
        bloques = pagina.get_text("blocks")
        texto_completo += pagina.get_text("text") + "\n"
        
        for b in bloques:
            # Si el bloque tiene texto y parece una fila de datos
            contenido = b[4].strip()
            if len(contenido) > 3:
                paginas_data.append(contenido)

    # --- MINERÍA DE DATOS SIN REGLAS FIJAS ---
    # Buscamos patrones universales de información
    entidades = {
        "FECHAS_DETECTADAS": sorted(list(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{2,4}', texto_completo)))),
        "VALORES_MONETARIOS": sorted(list(set(re.findall(r'\$?\s?[\d,]{2,}\.\d{2}', texto_completo)))),
        "IDENTIFICADORES_ALFA": sorted(list(set(re.findall(r'[A-Z0-9-]{7,25}', texto_completo)))),
        "EMAILS_Y_CONTACTOS": sorted(list(set(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', texto_completo))))
    }

    # --- RECONSTRUCCIÓN DE TABLAS DINÁMICAS ---
    filas_tabla = []
    for linea in texto_completo.split('\n'):
        # Dividimos por múltiples espacios, tabuladores o comas
        columnas = re.split(r'\s{2,}|\t|(?<=\w),(?=\w)', linea.strip())
        if len(columnas) > 1: # Si tiene más de una columna, es un dato útil
            filas_tabla.append(columnas)
    
    # Creamos un DataFrame dinámico (se ajusta al ancho del PDF)
    df_dinamico = pd.DataFrame(filas_tabla).dropna(how='all')

    return entidades, df_dinamico, texto_completo

# 3. INTERFAZ DE USUARIO
st.title("🧠 UNIVERSAL DATA ANALYZER")
st.write("Sube cualquier PDF (Facturas, Pedimentos, Contratos, Listas) para extraer su estructura lógica.")

archivos = st.sidebar.file_uploader("📂 CARGA MASIVA", type=["pdf"], accept_multiple_files=True)

if archivos:
    # Contenedor para la gran base de datos consolidada
    datos_consolidados = []

    for f in archivos:
        with st.expander(f"🔍 ANÁLISIS DEL ARCHIVO: {f.name}", expanded=True):
            entidades, df, raw = motor_inteligente_universal(f)
            
            # --- DASHBOARD POR ARCHIVO ---
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.write("### 📌 Resumen de Datos")
                for cat, vals in entidades.items():
                    if vals:
                        st.write(f"**{cat.replace('_', ' ')}**")
                        st.caption(", ".join(vals[:10]))
            
            with c2:
                st.write("### 📋 Estructura Detectada")
                if not df.empty:
                    # Limpiamos filas que parecen ruido (firmas largas)
                    df_limpio = df[df.apply(lambda x: x.astype(str).str.len().max() < 100, axis=1)]
                    st.dataframe(df_limpio.head(50), use_container_width=True)
                    
                    # Botón para descargar el Excel de este archivo específico
                    csv = df_limpio.to_csv(index=False).encode('utf-8')
                    st.download_button(f"📥 Bajar Excel de {f.name[:15]}...", csv, f"data_{f.name}.csv")
                else:
                    st.warning("No se detectaron tablas claras.")

    st.sidebar.markdown("---")
    st.sidebar.write("### Configuración de Inteligencia")
    sensibilidad = st.sidebar.slider("Sensibilidad de tabla", 1, 5, 2)
    st.sidebar.info("El sistema está analizando patrones de columnas dinámicamente.")

else:
    st.info("Sistema listo. El motor extraerá tablas y datos clave de cualquier PDF que subas.")