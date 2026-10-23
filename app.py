import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Bitácora Hogar", page_icon="💰", layout="wide")

st.title("💰 Control de Gastos del Hogar")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_google_sheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

try:
    gc = conectar_google_sheets()
    sheet_id = "1-I1JW43ULPH-Ql7vLXUUOQmxb9X-NXrk1rY-ho0Sb3U"
    sh = gc.open_by_key(sheet_id)

    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    mes_seleccionado = st.selectbox("Selecciona el Mes:", meses)

    worksheet = sh.worksheet(mes_seleccionado)

    # Obtenemos todos los datos puros sin formato de texto
    data = worksheet.get_all_values(value_render_option="UNFORMATTED_VALUE")

    items = []
    # En tu Excel, los ítems de gasto van exactamente de la fila 4 a la 15
    # (En índices de lista Python es de r = 3 hasta r = 14)
    for r in range(3, 15):
        if r < len(data):
            desc = data[r][1] if len(data[r]) > 1 else "" # Columna B (Descripción)
            presupuesto_val = data[r][3] if len(data[r]) > 3 else 0 # Columna D (Presupuesto)
            gasto_real_val = data[r][5] if len(data[r]) > 5 else 0 # Columna F (Gasto Real)

            def convertir_a_numero(val):
                if val is None or val == "":
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val)
                # Si llega formateado como texto
                val_str = str(val).replace("$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
                try:
                    return float(val_str)
                except ValueError:
                    return 0.0

            # Solo agregar si la celda de descripción no está vacía
            if desc and str(desc).strip():
                items.append({
                    "Fila_Sheet": r + 1, # Guarda el número de fila exacto en Sheets (4, 5, 6...)
                    "Descripción": str(desc).strip(),
                    "Presupuesto contemplado": convertir_a_numero(presupuesto_val),
                    "Gasto Real": convertir_a_numero(gasto_real_val)
                })

    df_gastos = pd.DataFrame(items)

    st.subheader(f"📋 Gastos de {mes_seleccionado}")

    if not df_gastos.empty:
        # Tabla interactiva con columnas bien distribuidas
        df_editado = st.data_editor(
            df_gastos[["Descripción", "Presupuesto contemplado", "Gasto Real"]],
            use_container_width=True,
            disabled=["Descripción", "Presupuesto contemplado"],
            column_config={
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Presupuesto contemplado": st.column_config.NumberColumn("Presupuesto ($)", format="$ %.0f"),
                "Gasto Real": st.column_config.NumberColumn("Gasto Real ($)", format="$ %.0f")
            },
            hide_index=True
        )

        if st.button("💾 Guardar en Google Sheets", type="primary"):
            with st.spinner("Guardando cambios en Google Sheets..."):
                for idx, row in df_editado.iterrows():
                    fila_real = int(df_gastos.loc[idx, "Fila_Sheet"])
                    nuevo_valor = float(row["Gasto Real"])
                    # Actualiza la celda exacta en la Columna F (6)
                    worksheet.update_cell(fila_real, 6, nuevo_valor)

            st.success(f"¡Gastos de {mes_seleccionado} guardados correctamente en Google Sheets!")
    else:
        st.info(f"No se encontraron conceptos de gastos en el mes de {mes_seleccionado}.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
