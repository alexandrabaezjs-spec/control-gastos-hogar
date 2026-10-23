import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Bitácora Hogar", page_icon="💰", layout="centered")

st.title("💰 Control de Gastos del Hogar")

# Configuración de acceso a la API de Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_google_sheets():
    # Obtener credenciales desde los secretos de Streamlit Cloud
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

try:
    gc = conectar_google_sheets()
    
    # Abrir la hoja por la ID exacta del enlace recibido
    sheet_id = "1-I1JW43ULPH-Ql7vLXUUOQmxb9X-NXrk1rY-ho0Sb3U"
    sh = gc.open_by_key(sheet_id)

    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    mes_seleccionado = st.selectbox("Selecciona el Mes:", meses)

    worksheet = sh.worksheet(mes_seleccionado)

    # Leer todos los datos de la pestaña del mes
    data = worksheet.get_all_values()

    # Mapeo de filas 3 a 15 (índices 2 a 14 en lista Python)
    items = []
    for r in range(2, 15):
        if r < len(data):
            desc = data[r][1] if len(data[r]) > 1 else "" # Columna B
            presupuesto_str = data[r][3] if len(data[r]) > 3 else "0" # Columna D
            gasto_real_str = data[r][5] if len(data[r]) > 5 else "0" # Columna F

            # Limpiar formatos de texto/moneda
            def parse_monto(val):
                if not val:
                    return 0.0
                val_clean = str(val).replace("$", "").replace(".", "").replace(",", ".").strip()
                try:
                    return float(val_clean)
                except ValueError:
                    return 0.0

            if desc and desc.strip():
                items.append({
                    "Fila_Sheet": r + 1, # Número de fila en Google Sheets
                    "Descripción": desc.strip(),
                    "Presupuesto contemplado": parse_monto(presupuesto_str),
                    "Gasto Real": parse_monto(gasto_real_str)
                })

    df_gastos = pd.DataFrame(items)

    st.subheader(f"📋 Gastos de {mes_seleccionado}")

    if not df_gastos.empty:
        # Tabla interactiva
        df_editado = st.data_editor(
            df_gastos[["Descripción", "Presupuesto contemplado", "Gasto Real"]],
            use_container_width=True,
            disabled=["Descripción", "Presupuesto contemplado"],
            column_config={
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Presupuesto contemplado": st.column_config.NumberColumn("Presupuesto ($)", format="$ %.0f"),
                "Gasto Real": st.column_config.NumberColumn("Gasto Real ($)", format="$ %.0f")
            }
        )

        if st.button("💾 Guardar en Google Sheets", type="primary"):
            with st.spinner("Guardando cambios..."):
                # Actualiza únicamente la columna F (Gasto Real) en Google Sheets celda por celda
                for idx, row in df_editado.iterrows():
                    fila_real = int(df_gastos.loc[idx, "Fila_Sheet"])
                    nuevo_valor = float(row["Gasto Real"])
                    worksheet.update_cell(fila_real, 6, nuevo_valor) # Columna 6 = F

            st.success(f"¡Gastos de {mes_seleccionado} actualizados correctamente en Google Sheets!")
    else:
        st.info(f"No se encontraron items registrados en el mes de {mes_seleccionado}.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.info("Asegúrate de haber configurado las credenciales en 'Secrets' dentro de Streamlit Cloud y compartido el documento con la cuenta de servicio.")
