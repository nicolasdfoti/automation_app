import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

from target_system.backend.services.dashboard import compute_dashboard_stats, recent_activity

st.set_page_config(page_title="SIGE — Sistema de Gestion Edilicia", page_icon="\U0001F4D0", layout="wide")
ui.inject_css()

ui.title("SIGE — Sistema de Gestion Edilicia",
          "Plataforma para administrar el relevamiento tecnico del portfolio de propiedades: "
          "superficie, capacidad, estacionamiento y demas datos edilicios.")
ui.mock_banner()

df = db.read_properties()

with st.sidebar:
    st.subheader("Panel de demostracion")
    if df.empty:
        st.caption("El sistema todavia no tiene propiedades cargadas.")
        n = st.number_input("Cantidad a sembrar", min_value=1, max_value=200, value=20)
        if st.button("Sembrar propiedades", type="primary", use_container_width=True):
            import seed as seed_module
            seed_module.seed(int(n))
            st.rerun()
    else:
        st.caption(f"{len(df)} propiedades cargadas.")
        with st.expander("Sembrar mas"):
            n = st.number_input("Cantidad", min_value=1, max_value=200, value=10, key="extra_seed")
            if st.button("Agregar", key="btn_extra_seed"):
                import seed as seed_module
                seed_module.seed(int(n))
                st.rerun()
    st.divider()
    auto = st.checkbox("Auto-refrescar (cada 4s)", value=False,
                        help="Util para ver en vivo como la automatizacion va corrigiendo propiedades.")

if df.empty:
    st.info("Sembra algunas propiedades desde la barra lateral para ver el panel.")
    st.stop()

# --- KPIs como fichas tipo plano ---
stats = compute_dashboard_stats(df)
pendientes = stats["pendientes"]
corregidas = stats["corregidas"]
superficie_total = stats["superficie_total"]
capacidad_total = stats["capacidad_total"]

kpis = [
    ("PROPIEDADES", f"{len(df)}"),
    ("SUPERFICIE TOTAL", f"{superficie_total:,.0f} m2"),
    ("CAPACIDAD TOTAL", f"{capacidad_total:,} pers."),
    ("PENDIENTES DE ESQUEMATICO", f"{pendientes}"),
    ("CORREGIDAS POR AUTOMATIZACION", f"{corregidas}"),
]
cols = st.columns(len(kpis))
for col, (label, value) in zip(cols, kpis):
    with col:
        st.markdown(
            f'<div class="sige-card"><div class="sige-dim-label">{label}</div>'
            f'<div style="font-size:1.6rem; font-weight:700; font-family:\'Space Grotesk\',sans-serif; margin-top:0.2rem;">{value}</div></div>',
            unsafe_allow_html=True,
        )

ui.dim_divider("ACTIVIDAD Y ACCESOS")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.markdown("**Actividad reciente**")
    st.caption("Ultimas propiedades actualizadas, mas nuevas primero.")

    reciente = recent_activity(df)

    prev_map = st.session_state.get("sige_prev_fuente", {})
    curr_map = dict(zip(df["codigo"].astype(str), df["fuente"]))

    for _, fila in reciente.iterrows():
        codigo = str(fila["codigo"])
        automatizada = fila["fuente"] == "automatizacion OCR"
        recien_cambiada = codigo in prev_map and prev_map[codigo] != fila["fuente"] and automatizada
        sello = ui.stamp("REV \u00b7 AUTOMATIZADO", "ok") if automatizada else ui.stamp("LEGACY", "warn")
        clase = "sige-feed-row sige-sweep" if recien_cambiada else "sige-feed-row"
        st.markdown(
            f'<div class="{clase}"><div><span class="codigo">{codigo}</span> — {fila["direccion"]}</div>'
            f'<div>{sello} &nbsp; <span style="color:#5b665f; font-family:\'IBM Plex Mono\',monospace; font-size:0.78rem;">{fila["ultima_actualizacion"]}</span></div></div>',
            unsafe_allow_html=True,
        )

    st.session_state["sige_prev_fuente"] = curr_map

with col_der:
    st.markdown("**Accesos rapidos**")
    st.page_link("pages/1_Propiedades.py", label="Ver todas las propiedades", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Distribucion por fuente**")
    st.bar_chart(df["fuente"].value_counts())

if auto:
    time.sleep(4)
    st.rerun()
