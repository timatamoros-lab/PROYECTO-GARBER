import streamlit as st
import pandas as pd

# Configuración visual de la app
st.set_page_config(page_title="Portal TI - Aduanas", page_icon="📦")

st.title("⚓ Sistema de Apoyo Aduanero")
st.subheader("Departamento de TI")

# Crear pestañas para organizar las herramientas
tab1, tab2 = st.tabs(["Validar Datos", "Calculadora Rápida"])

with tab1:
    st.write("### Validar Archivo de Operaciones")
    archivo = st.file_uploader("Sube tu Excel de Pedimentos", type=["xlsx"])

    if archivo:
        df = pd.read_excel(archivo)
        
        st.success("Archivo cargado correctamente")
        
        # Mostrar resumen rápido
        st.write(f"Total de registros: **{len(df)}**")
        
        # --- LÓGICA DE VALIDACIÓN ---
        # Supongamos que buscamos errores comunes:
        st.write("#### 🔍 Hallazgos de validación:")
        
        # 1. Buscar RFCs faltantes
        if 'RFC' in df.columns:
            faltantes = df['RFC'].isna().sum()
            if faltantes > 0:
                st.error(f"⚠️ Se encontraron {faltantes} registros sin RFC.")
                st.dataframe(df[df['RFC'].isna()])
            else:
                st.success("✅ Todos los registros tienen RFC.")
        
        # 2. Vista previa general
        st.write("#### Vista previa de los datos:")
        st.dataframe(df.head(20))

with tab2:
    st.write("### Calculadora de Contribuciones (Demo)")
    valor_aduana = st.number_input("Valor Aduana ($)", min_value=0.0)
    tasa_igi = st.number_input("Tasa IGI (%)", min_value=0.0, max_value=100.0)
    
    igi = valor_aduana * (tasa_igi / 100)
    st.info(f"El IGI estimado es: **${igi:,.2f}**")