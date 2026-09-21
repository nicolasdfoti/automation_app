import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

from backend.services.automation import (
    already_automated_codes,
    apply_corrections,
    build_preview,
    filter_candidates,
    merge_ocr_data,
)

st.set_page_config(page_title="Automatizar — Demo", page_icon="\U0001F916", layout="wide")
ui.inject_css()
ui.breadcrumbs(["Demo", "Pipeline OCR + Automatizacion", "Automatizar"])
ui.page_header(
    "Automatizar la carga en SIGE",
    subtitle="Toma lo que extrajo el OCR y corrige el dato legacy de cada propiedad en SIGE. "
              "Solo pisa campos que el OCR pudo leer — nunca escribe un dato vacio encima de uno que ya existia.",
)

propiedades = db.read_properties()
ocr = db.read_ocr_output()

if propiedades.empty or ocr.empty:
    ui.empty_state(
        "\U0001F916", "Todavia no hay nada para automatizar",
        "Necesitas propiedades en SIGE y haber corrido el OCR sobre sus esquematicos.",
    )
    st.stop()

base = merge_ocr_data(propiedades, ocr)

if base.empty:
    ui.empty_state("\U0001F916", "No hay codigos en comun", "El OCR todavia no proceso ninguna propiedad que exista en SIGE.")
    st.stop()

ya_automatizadas = already_automated_codes(propiedades)

forzar = st.checkbox(
    "Reprocesar propiedades ya automatizadas antes", value=False,
    help="Por defecto solo se proponen correcciones para propiedades con datos legacy sin tocar.",
)
candidatas = filter_candidates(base, ya_automatizadas, forzar)

ui.metric_row([
    {"label": "Propiedades con OCR disponible", "value": len(base), "hint": "cruzan con SIGE"},
    {"label": "Ya corregidas antes", "value": len(ya_automatizadas), "hint": "fuente = automatizacion OCR"},
    {"label": "Candidatas a corregir ahora", "value": len(candidatas), "hint": "segun el filtro de arriba"},
])

if candidatas.empty:
    st.info("No hay propiedades candidatas con el filtro actual.")
    st.stop()

st.divider()
ui.section_label("Antes / despues (previsualizacion)")

filas_preview = build_preview(candidatas)

if not filas_preview:
    st.caption("Los valores del OCR coinciden con lo que ya tenia SIGE — nada para corregir.")
else:
    st.dataframe(pd.DataFrame(filas_preview), use_container_width=True, hide_index=True, height=320)

st.caption(f"{candidatas['codigo'].nunique()} propiedades, {len(filas_preview)} campos a corregir en total.")

if ui.button_primary(f"\u2705 Aplicar automatizacion a {len(candidatas)} propiedades", key="aplicar_auto"):
    resumen = apply_corrections(candidatas)
    ui.info_banner(
        f"Automatizacion aplicada: {resumen['corregidas']} propiedades corregidas, "
        f"{resumen['campos_corregidos']} campos actualizados en SIGE.",
        tone="success",
    )
    st.caption("Anda al panel de SIGE (target_system) para ver el antes/despues reflejado.")
    st.rerun()
