import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui

st.set_page_config(page_title="Comparar — Demo", page_icon="\U0001F50E", layout="wide")
ui.inject_css()
ui.breadcrumbs(["Demo", "Pipeline OCR + Automatizacion", "Comparar"])
ui.page_header(
    "Comparar OCR vs Ground Truth",
    subtitle="Mide que tan bien leyo el OCR cada esquematico, comparando contra el valor que se sabe "
              "correcto porque lo generamos nosotros mismos.",
)

gt = db.read_ground_truth()
ocr = db.read_ocr_output()

if gt.empty or ocr.empty:
    ui.empty_state(
        "\U0001F50E", "Todavia no hay nada para comparar",
        "Necesitas esquematicos generados (con su ground truth) y haber corrido el OCR sobre ellos.",
    )
    st.stop()

campos = db.NUMERIC_FIELDS
merged = gt.merge(ocr, on="codigo", suffixes=("_gt", "_ocr"), how="inner")

if merged.empty:
    ui.empty_state("\U0001F50E", "No hay codigos en comun", "El ground truth y el OCR output no comparten ningun codigo todavia.")
    st.stop()

# --- comparacion campo a campo ---
resultado = pd.DataFrame({"codigo": merged["codigo"]})
total_comparaciones = 0
total_correctas = 0
for campo in campos:
    col_gt, col_ocr = f"{campo}_gt", f"{campo}_ocr"
    if col_gt not in merged or col_ocr not in merged:
        continue
    match = merged[col_gt].astype(str) == merged[col_ocr].astype(str)
    resultado[campo] = match
    total_comparaciones += len(match)
    total_correctas += int(match.sum())

resultado["todas_correctas"] = resultado[campos].all(axis=1)
exactitud_global = round(100 * total_correctas / total_comparaciones, 1) if total_comparaciones else 0.0
propiedades_con_error = int((~resultado["todas_correctas"]).sum())

ui.metric_row([
    {"label": "Propiedades comparadas", "value": len(resultado), "hint": "con ground truth y OCR"},
    {"label": "Exactitud global", "value": f"{exactitud_global}%", "hint": "campos correctos / total"},
    {"label": "Con al menos un error", "value": propiedades_con_error, "hint": "de las comparadas"},
])

st.divider()
ui.section_label("Exactitud por campo")
por_campo = pd.DataFrame({
    "Campo": campos,
    "Exactitud (%)": [round(100 * resultado[c].mean(), 1) for c in campos],
})
st.bar_chart(por_campo.set_index("Campo"))

st.divider()
ui.section_label("Detalle por propiedad")


def _resaltar(val):
    if isinstance(val, bool) or val in (True, False):
        return "background-color: #e7f2ec; color: #2f6f4f;" if val else "background-color: #fbeedd; color: #a15c00;"
    return ""


tabla_detalle = resultado[["codigo"] + campos + ["todas_correctas"]].copy()
tabla_detalle = tabla_detalle.rename(columns={"todas_correctas": "OK"})
st.dataframe(
    tabla_detalle.style.applymap(_resaltar, subset=campos + ["OK"]),
    use_container_width=True, hide_index=True, height=380,
)

with st.expander("Ver valores lado a lado (ground truth vs OCR) para propiedades con error"):
    con_error = merged[~resultado["todas_correctas"]]
    if con_error.empty:
        st.caption("No hay propiedades con error.")
    else:
        cols = ["codigo"] + [f"{c}_gt" for c in campos] + [f"{c}_ocr" for c in campos]
        st.dataframe(con_error[cols], use_container_width=True, hide_index=True)

st.page_link("pages/3_Automatizar.py", label="\u2192 Ir a Automatizar (corregir SIGE con lo extraido)")
