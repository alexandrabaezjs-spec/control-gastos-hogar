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

    # Obtenemos todos los datos puros sin formatos
    data = worksheet.get_all_values(value_render_option="UNFORMATTED_VALUE")

    items = []
    
    # Función para convertir valores numéricos de forma limpia
    def parse_num(val):
        if val is None or val == "" or str(val).strip() == "":
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace("$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(val_str)
        except ValueError:
            return None

    # Recorremos desde la fila 2 (Balance Casa) hasta la fila 15 en Google Sheets
    # En índice Python es de r = 1 hasta r = 14
    for r in range(1, 15):
        if r < len(data):
            mes_txt = data[r][0] if len(data[r]) > 0 else "" # Columna A
            desc_txt = data[r][1] if len(data[r]) > 1 else "" # Columna B
            ingresos_val = parse_num(data[r][2]) if len(data[r]) > 2 else None # Columna C
            presupuesto_val = parse_num(data[r][3]) if len(data[r]) > 3 else None # Columna D
            restante_val = parse_num(data[r][4]) if len(data[r]) > 4 else None # Columna E
            gasto_real_val = parse_num(data[r][5]) if len(data[r]) > 5 else None # Columna F
            restante_real_val = parse_num(data[r][6]) if len(data[r]) > 6 else None # Columna G

            # Incluir si hay descripción en Columna B
            if desc_txt and str(desc_txt).strip():
                items.append({
                    "Fila_Sheet": r + 1, # Guarda número de fila en Sheets (2, 3, 4...)
                    "Mes": str(mes_txt).strip() if mes_txt else "",
                    "Descripción": str(desc_txt).strip(),
                    "Ingresos ($)": ingresos_val,
                    "Presupuesto ($)": presupuesto_val,
                    "Restante ($)": restante_val,
                    "Gasto Real ($)": gasto_real_val,
                    "Restante Real ($)": restante_real_val
                })

    df_gastos = pd.DataFrame(items)

    st.subheader(f"Tabla de Gastos - {mes_seleccionado}")
    st.info("💡 Edita los valores de 'Gasto Real ($)' directamente en la tabla y presiona 'Guardar en Google Sheets'.")

    if not df_gastos.empty:
        # Tabla interactiva con todas las columnas señaladas
        df_editado = st.data_editor(
            df_gastos[["Mes", "Descripción", "Ingresos ($)", "Presupuesto ($)", "Restante ($)", "Gasto Real ($)", "Restante Real ($)"]],
            use_container_width=True,
            # Bloqueamos todas las columnas excepto "Gasto Real ($)"
            disabled=["Mes", "Descripción", "Ingresos ($)", "Presupuesto ($)", "Restante ($)", "Restante Real ($)"],
            column_config={
                "Mes": st.column_config.TextColumn("Mes", width="small"),
                "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
                "Ingresos ($)": st.column_config.NumberColumn("Ingresos ($)", format="$ %.0f", width="small"),
                "Presupuesto ($)": st.column_config.NumberColumn("Presupuesto ($)", format="$ %.0f", width="small"),
                "Restante ($)": st.column_config.NumberColumn("Restante ($)", format="$ %.0f", width="small"),
                "Gasto Real ($)": st.column_config.NumberColumn("Gasto Real ($)", format="$ %.0f", width="small"),
                "Restante Real ($)": st.column_config.NumberColumn("Restante Real ($)", format="$ %.0f", width="small"),
            },
            hide_index=True
        )

        if st.button("💾 Guardar en Google Sheets", type="primary"):
            with st.spinner("Guardando cambios en Google Sheets..."):
                for idx, row in df_editado.iterrows():
                    fila_real = int(df_gastos.loc[idx, "Fila_Sheet"])
                    
                    # Evitamos sobreescribir la celda F2 (que es la fórmula de suma total del Balance)
                    if fila_real == 2:
                        continue

                    nuevo_valor = row["Gasto Real ($)"]
                    if pd.notnull(nuevo_valor):
                        worksheet.update_cell(fila_real, 6, float(nuevo_valor)) # Columna 6 = F

            st.success(f"¡Gastos de {mes_seleccionado} actualizados correctamente en Google Sheets!")
            st.rerun()
    else:
        st.warning(f"No se encontraron registros en el mes de {mes_seleccionado}.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
