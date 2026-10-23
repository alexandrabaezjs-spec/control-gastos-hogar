import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Bitácora Hogar", page_icon="💰", layout="centered")

EXCEL_FILE = 'BITACORA HOGAR.xlsx'

st.title("💰 Control de Gastos del Hogar")

meses = ["Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
mes_seleccionado = st.selectbox("Selecciona el Mes:", meses)

# Función para cargar datos del Excel
def cargar_datos(mes):
    if os.path.exists(EXCEL_FILE):
        try:
            xls = pd.ExcelFile(EXCEL_FILE)
            if mes in xls.sheet_names:
                df = pd.read_excel(EXCEL_FILE, sheet_name=mes)
                # Asegurar columnas esperadas
                for col in ["Descripcion", "Presupuesto contemplado", "Gasto Real"]:
                    if col not in df.columns:
                        df[col] = 0.0 if "Gasto" in col or "Presupuesto" in col else ""
                return df
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
    # Si no existe el archivo o la pestaña, creamos un DataFrame base con los conceptos comunes
    conceptos = ["Agua", "Gas", "Luz", "Administracion", "cuota de credito", "internet", "Neflix", "gatos", "spotify", "cuota Apartamento", "Mercado", "impuesto", "otros"]
    return pd.DataFrame({
        "Descripcion": conceptos,
        "Presupuesto contemplado": [0.0] * len(conceptos),
        "Gasto Real": [0.0] * len(conceptos)
    })

df_actual = cargar_datos(mes_seleccionado)

st.subheader(f" Tabla de Gastos - {mes_seleccionado}")
st.info("💡 Edita los valores de 'Gasto Real' directamente en la tabla y presiona 'Guardar Cambios'.")

# Editor interactivo de tabla
df_editado = st.data_editor(
    df_actual,
    use_container_width=True,
    num_rows="dynamic", # Permite agregar nuevas filas desde la interfaz
    column_config={
        "Descripcion": st.column_config.TextColumn("Descripción", required=True),
        "Presupuesto contemplado": st.column_config.NumberColumn("Presupuesto ($)", format="$ %.0f"),
        "Gasto Real": st.column_config.NumberColumn("Gasto Real ($)", format="$ %.0f")
    }
)

# Botón para guardar todos los cambios
if st.button(" Guardar Cambios en Excel", type="primary"):
    try:
        # Calcular/Actualizar columnas si se requiere
        if os.path.exists(EXCEL_FILE):
            with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_editado.to_excel(writer, sheet_name=mes_seleccionado, index=False)
        else:
            with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                df_editado.to_excel(writer, sheet_name=mes_seleccionado, index=False)
        st.success(f"¡Cambios de {mes_seleccionado} guardados correctamente!")
    except Exception as e:
        st.error(f"No se pudo guardar. Si tienes el archivo Excel abierto en tu computadora, ciérralo e intenta de nuevo. Error: {e}")
