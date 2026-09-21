import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

st.set_page_config(page_title="Propiedades — SIGE", page_icon="\U0001F4CB", layout="wide")
ui.inject_css()
ui.title("Propiedades", "Listado completo del portfolio, con filtros.")
ui.mock_banner()

df = db.read_properties()
if df.empty:
    st.info("Todavia no hay propiedades cargadas. Anda al Home para sembrar datos de ejemplo.")
    st.stop()

with st.container(border=True):
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1.4])
    with f1:
        busqueda = st.text_input("Buscar por codigo o direccion", "")
    with f2:
        fuente_filtro = st.selectbox("Fuente", ["Todas", "carga manual (legacy)", "automatizacion OCR"])
    with f3:
        estado_filtro = st.selectbox("Esquematico", ["Todos", "Con esquematico", "Pendiente"])
    with f4:
        rango_superficie = st.slider(
            "Superficie (m2)", 0, int(max(1400, df["superficie_m2"].max())),
            (0, int(max(1400, df["superficie_m2"].max()))),
        )

vista = df.copy()
if busqueda:
    vista = vista[
        vista["codigo"].astype(str).str.contains(busqueda, case=False)
        | vista["direccion"].str.contains(busqueda, case=False, na=False)
    ]
if fuente_filtro != "Todas":
    vista = vista[vista["fuente"] == fuente_filtro]
if estado_filtro != "Todos":
    esperado = estado_filtro == "Con esquematico"
    vista = vista[vista["esquematico_generado"] == esperado]
vista = vista[
    (vista["superficie_m2"] >= rango_superficie[0]) & (vista["superficie_m2"] <= rango_superficie[1])
]

st.caption(f"{len(vista)} de {len(df)} propiedades")

export_col, _ = st.columns([1, 3])
with export_col:
    import io
    buffer = io.BytesIO()
    vista.drop(columns=["esquematico_generado"], errors="ignore").to_excel(buffer, index=False)
    st.download_button(
        "\u2b07\ufe0f Exportar a Excel (vista filtrada)",
        data=buffer.getvalue(),
        file_name="propiedades_sige.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

vista_mostrar = vista.copy()
vista_mostrar["Estado"] = vista_mostrar["esquematico_generado"].map({True: "Con esquematico", False: "Pendiente"})
cols_mostrar = [
    "codigo", "direccion", "superficie_m2", "capacidad_personas",
    "plazas_estacionamiento", "anio_construccion", "salas",
    "Estado", "fuente", "ultima_actualizacion",
]


def _resaltar_fuente(val):
    if val == "automatizacion OCR":
        return "background-color: #E4ECF2; color: #2B5D8C; font-weight: 600;"
    if val == "carga manual (legacy)":
        return "background-color: #F6EBDC; color: #B8752B; font-weight: 600;"
    return ""


tabla = vista_mostrar[cols_mostrar].rename(columns={
    "codigo": "Codigo", "direccion": "Direccion", "superficie_m2": "Superficie (m2)",
    "capacidad_personas": "Capacidad", "plazas_estacionamiento": "Plazas est.",
    "anio_construccion": "Ano constr.", "salas": "Salas",
    "fuente": "Fuente", "ultima_actualizacion": "Ult. actualizacion",
})
st.dataframe(
    tabla.style.applymap(_resaltar_fuente, subset=["Fuente"]).format({"Superficie (m2)": "{:.1f}"}),
    use_container_width=True, hide_index=True, height=380,
)

st.divider()
st.markdown('<div class="sige-dim-label">Ver ficha completa</div>', unsafe_allow_html=True)
if vista.empty:
    st.caption("Ningun resultado con los filtros actuales.")
else:
    codigo_sel = st.selectbox(
        "Elegir propiedad",
        vista["codigo"].astype(str).tolist(),
        format_func=lambda c: f"{c} — {vista[vista['codigo'].astype(str) == c]['direccion'].iloc[0]}",
    )
    if st.button("\u2192 Ver ficha completa", type="primary"):
        st.session_state["sige_codigo_detalle"] = codigo_sel
        st.switch_page("pages/2_Detalle_Propiedad.py")
