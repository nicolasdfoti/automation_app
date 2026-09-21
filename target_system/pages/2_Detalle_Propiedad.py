import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

st.set_page_config(page_title="Ficha de Propiedad — SIGE", page_icon="\U0001F3E2", layout="wide")
ui.inject_css()

df = db.read_properties()
if df.empty:
    st.info("Todavia no hay propiedades cargadas.")
    st.stop()

codigo = st.session_state.get("sige_codigo_detalle") or st.query_params.get("codigo")

st.page_link("pages/1_Propiedades.py", label="\u2190 Volver al listado")

if not codigo or codigo not in df["codigo"].astype(str).values:
    st.subheader("Elegir una propiedad")
    codigo = st.selectbox("Codigo", df["codigo"].astype(str).tolist())
    if not st.button("Ver ficha"):
        st.stop()
    st.session_state["sige_codigo_detalle"] = codigo

st.query_params["codigo"] = codigo
fila = df[df["codigo"].astype(str) == codigo].iloc[0]

ui.title(f"Propiedad {fila['codigo']}", fila["direccion"])
ui.mock_banner()

automatizada = fila["fuente"] == "automatizacion OCR"
st.markdown(
    ui.stamp("REV \u00b7 CORREGIDO POR AUTOMATIZACION", "ok") if automatizada else ui.stamp("LEGACY \u00b7 SIN CORREGIR", "warn"),
    unsafe_allow_html=True,
)
st.caption(f"Ultima actualizacion: {fila['ultima_actualizacion']}")

ui.dim_divider("DATOS TECNICOS")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Superficie", f"{fila['superficie_m2']} m2")
    st.metric("Capacidad", f"{int(fila['capacidad_personas'])} pers.")
with c2:
    st.metric("Plazas de estacionamiento", int(fila["plazas_estacionamiento"]))
    st.metric("Ano de construccion", int(fila["anio_construccion"]))
with c3:
    st.metric("Salas / ambientes", int(fila["salas"]))
    st.metric("Esquematico", "Generado" if fila["esquematico_generado"] else "Pendiente")

ui.dim_divider("ESQUEMATICO")
if fila["esquematico_generado"] and fila["archivo_esquematico"]:
    pdf_path = db.SCHEMATICS_DIR / fila["archivo_esquematico"]
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            st.download_button("\u2b07\ufe0f Descargar PDF del esquematico", data=f.read(),
                                file_name=pdf_path.name, mime="application/pdf")
    else:
        st.caption(f"Deberia estar en {pdf_path}, pero no se encontro el archivo.")
else:
    st.caption("Esta propiedad todavia no tiene esquematico generado.")
