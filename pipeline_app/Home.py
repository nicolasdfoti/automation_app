import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui

st.set_page_config(page_title="Pipeline OCR + Automatizacion — Demo", page_icon="\u2699\ufe0f", layout="wide")
ui.inject_css()
ui.breadcrumbs(["Demo", "Pipeline OCR + Automatizacion"])
ui.page_header(
    "Pipeline OCR + Automatizacion",
    subtitle="Corre sobre los esquematicos generados para SIGE. Usa el menu de la izquierda para "
              "recorrer el flujo: OCR -> Comparar -> Automatizar.",
)

ui.section_label("Flujo")
st.markdown(
    "1. **Correr OCR** — extrae los datos tecnicos de los PDFs.\n"
    "2. **Comparar** — OCR vs el ground truth conocido (precision del OCR).\n"
    "3. **Automatizar** — carga lo extraido (ya validado) en SIGE, corrigiendo los datos legacy.\n"
)
