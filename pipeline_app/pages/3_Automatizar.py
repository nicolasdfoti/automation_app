import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

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

campos = db.NUMERIC_FIELDS
base = propiedades[["codigo", "direccion", "fuente"] + campos].merge(
    ocr[["codigo"] + campos], on="codigo", suffixes=("_legacy", "_ocr"), how="inner"
)

if base.empty:
    ui.empty_state("\U0001F916", "No hay codigos en comun", "El OCR todavia no proceso ninguna propiedad que exista en SIGE.")
    st.stop()

ya_automatizadas = set(propiedades[propiedades["fuente"] == "automatizacion OCR"]["codigo"].astype(str))

forzar = st.checkbox(
    "Reprocesar propiedades ya automatizadas antes", value=False,
    help="Por defecto solo se proponen correcciones para propiedades con datos legacy sin tocar.",
)
candidatas = base if forzar else base[~base["codigo"].astype(str).isin(ya_automatizadas)]

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

filas_preview = []
for _, row in candidatas.iterrows():
    for campo in campos:
        legacy, ocr_val = row[f"{campo}_legacy"], row[f"{campo}_ocr"]
        if pd.isna(ocr_val):
            continue  # el OCR no pudo leer este campo: no se toca
        if str(legacy) != str(ocr_val):
            filas_preview.append({
                "Codigo": row["codigo"], "Direccion": row["direccion"], "Campo": campo,
                "Valor actual (legacy)": legacy, "Valor nuevo (OCR)": ocr_val,
            })

if not filas_preview:
    st.caption("Los valores del OCR coinciden con lo que ya tenia SIGE — nada para corregir.")
else:
    st.dataframe(pd.DataFrame(filas_preview), use_container_width=True, hide_index=True, height=320)

st.caption(f"{candidatas['codigo'].nunique()} propiedades, {len(filas_preview)} campos a corregir en total.")

if ui.button_primary(f"\u2705 Aplicar automatizacion a {len(candidatas)} propiedades", key="aplicar_auto"):
    hoy = date.today().strftime("%d/%m/%Y")
    corregidas, campos_corregidos = 0, 0
    for _, row in candidatas.iterrows():
        updates = {}
        for campo in campos:
            ocr_val = row[f"{campo}_ocr"]
            if pd.isna(ocr_val):
                continue
            if str(row[f"{campo}_legacy"]) != str(ocr_val):
                updates[campo] = ocr_val
                campos_corregidos += 1
        if updates:
            updates["fuente"] = "automatizacion OCR"
            updates["ultima_actualizacion"] = hoy
            db.update_property(row["codigo"], updates)
            corregidas += 1

    ui.info_banner(
        f"Automatizacion aplicada: {corregidas} propiedades corregidas, {campos_corregidos} campos actualizados en SIGE.",
        tone="success",
    )
    st.caption("Anda al panel de SIGE (target_system) para ver el antes/despues reflejado.")
    st.rerun()
