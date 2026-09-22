import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
from pdf_creator import generator, schema

from backend.services.schematics import build_numeric_overrides

st.set_page_config(page_title="Generador de Esquematicos", page_icon="\U0001F4C4", layout="wide")

st.markdown(
    """
    <style>
    :root { --pc-accent: #2f6f4f; --pc-accent-soft: #e7f2ec; }
    .pc-title { font-size: 1.7rem; font-weight: 800; color: var(--pc-accent); margin-bottom: 0.1rem; }
    .pc-subtitle { color: #6b7570; font-size: 0.92rem; margin-bottom: 1.1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="pc-title">Generador de Esquematicos</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pc-subtitle">Genera el PDF del esquematico para una propiedad que ya existe en SIGE. '
    'Los valores tecnicos que dibuja son el "dato correcto" — el sistema puede tener otra cosa cargada.</div>',
    unsafe_allow_html=True,
)

propiedades = db.read_properties()
if propiedades.empty:
    st.warning("Todavia no hay propiedades en el sistema. Sembra datos desde el panel de SIGE primero.")
    st.stop()

pendientes = db.propiedades_pendientes_de_esquematico()

c1, c2, c3 = st.columns(3)
c1.metric("Propiedades en el sistema", len(propiedades))
c2.metric("Pendientes de esquematico", len(pendientes))
c3.metric("Con esquematico ya generado", len(propiedades) - len(pendientes))

st.divider()
st.subheader("Generar uno puntual")

if pendientes.empty:
    st.info("No quedan propiedades pendientes de esquematico.")
else:
    codigo_sel = st.selectbox(
        "Propiedad (pendiente)",
        pendientes["codigo"].astype(str).tolist(),
        format_func=lambda c: f"{c} — {pendientes[pendientes['codigo'].astype(str) == c]['direccion'].iloc[0]}",
    )
    st.caption("Dejá vacío lo que quieras que se derive automáticamente de los datos actuales de la propiedad (la derivación es determinística por código y simula el relevamiento real).")
    with st.form("form_puntual"):
        fc1, fc2 = st.columns(2)
        with fc1:
            superficie = st.number_input("Superficie (m2)", min_value=0.0, step=10.0, value=0.0)
            capacidad = st.number_input("Capacidad (personas)", min_value=0, step=5, value=0)
            plazas = st.number_input("Plazas de estacionamiento", min_value=0, step=1, value=0)
        with fc2:
            anio = st.number_input("Ano de construccion", min_value=0, max_value=2026, step=1, value=0)
            salas = st.number_input("Salas / ambientes", min_value=0, step=1, value=0)
        submitted = st.form_submit_button("\U0001F4C4 Generar esquematico", type="primary", use_container_width=True)

    if submitted:
        overrides = build_numeric_overrides(
            superficie_m2=superficie,
            capacidad_personas=capacidad,
            plazas_estacionamiento=plazas,
            anio_construccion=anio,
            salas=salas,
        )
        pdf_path, record = generator.generate_for_property(codigo_sel, overrides)
        st.success(f"Esquematico generado para la propiedad {codigo_sel}.")
        with open(pdf_path, "rb") as f:
            st.download_button("\u2b07\ufe0f Descargar PDF", data=f.read(), file_name=pdf_path.name, mime="application/pdf")
        st.rerun()

st.divider()
st.subheader("Generar todas las pendientes")
st.caption(f"Genera de una los {len(pendientes)} esquematicos que todavia faltan, con valores correctos derivados de cada propiedad.")
if st.button(f"\u25B6\ufe0f Generar las {len(pendientes)} pendientes", disabled=pendientes.empty, use_container_width=True):
    with st.spinner("Generando..."):
        resultados = generator.generate_for_all_pending()
    st.success(f"{len(resultados)} esquematicos generados.")
    st.rerun()

st.divider()
st.subheader("Esquematicos ya generados")
generados = propiedades[propiedades["esquematico_generado"] == True]  # noqa: E712
if generados.empty:
    st.caption("Todavia no generaste ninguno.")
else:
    st.dataframe(
        generados[["codigo", "direccion", "archivo_esquematico"]],
        use_container_width=True, hide_index=True,
        column_config={"codigo": "Codigo", "direccion": "Direccion", "archivo_esquematico": "Archivo"},
    )
