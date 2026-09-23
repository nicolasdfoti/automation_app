import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db
import ui
from pipeline_app.ocr import pipeline_mock

st.set_page_config(page_title="Correr OCR — Demo", page_icon="\U0001F50D", layout="wide")
ui.inject_css()
ui.breadcrumbs(["Demo", "Pipeline OCR + Automatizacion", "Correr OCR"])
ui.page_header(
    "Correr OCR sobre los esquematicos",
    subtitle="Descubre por codigo, procesa en paralelo por proyecto, y deja el resultado en "
              "ocr_output.xlsx para compararlo despues contra el ground truth.",
)


def _codigos_procesados() -> set:
    if not db.OCR_OUTPUT_XLSX.exists():
        return set()
    try:
        df = pd.read_excel(db.OCR_OUTPUT_XLSX, usecols=["codigo"])
        return set(df["codigo"].dropna().astype(int).astype(str))
    except Exception:
        return set()


pdfs = sorted(db.SCHEMATICS_DIR.glob("*.pdf")) if db.SCHEMATICS_DIR.exists() else []
codigos_procesados = _codigos_procesados()

if not pdfs:
    ui.empty_state(
        "\U0001F4C4", "Todavia no hay esquematicos para procesar",
        "Generalos primero desde el Generador de Esquematicos (pdf_creator).",
    )
else:
    filas = []
    for pdf in pdfs:
        codigo = pdf.stem.split("_")[0]
        procesado = codigo in codigos_procesados
        filas.append({
            "Codigo": codigo, "Archivo": pdf.name,
            "Modificado": datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%d/%m %H:%M"),
            "Estado": "\u2705 Procesado" if procesado else "\u23F3 Pendiente",
        })
    pendientes = sum(1 for f in filas if f["Estado"].startswith("\u23F3"))

    ui.metric_row([
        {"label": "PDFs encontrados", "value": len(filas), "hint": "generados por pdf_creator"},
        {"label": "Procesados", "value": len(filas) - pendientes, "hint": "con fila en ocr_output.xlsx"},
        {"label": "Pendientes", "value": pendientes, "hint": "esperando OCR"},
    ])

    rows_html = '<div class="app-file-row app-file-head"><div>Codigo</div><div>Archivo</div><div>Modificado</div><div>Estado</div></div>'
    for f in filas:
        ok = f["Estado"].startswith("\u2705")
        pill = ui.status_pill("Procesado" if ok else "Pendiente", "success" if ok else "warning")
        rows_html += (
            f'<div class="app-file-row"><div>{f["Codigo"]}</div><div>{f["Archivo"]}</div>'
            f'<div>{f["Modificado"]}</div><div>{pill}</div></div>'
        )
    st.markdown(rows_html, unsafe_allow_html=True)

ui.section_label("Ejecutar OCR")

with st.container(border=True):
    forzar_todo = st.checkbox("Reprocesar todo (ignorar lo ya procesado)", key="forzar_todo")
    workers = st.number_input(
        "Proyectos en paralelo", min_value=1, max_value=max(1, os.cpu_count() or 1),
        value=max(1, (os.cpu_count() or 2) - 1), key="ocr_workers",
    )
    run_ocr = ui.button_primary("\u25B6\ufe0f  Ejecutar OCR sobre los esquematicos pendientes", key="run_ocr", disabled=not pdfs)

    if run_ocr:
        omitir_codigos = [] if forzar_todo else list(codigos_procesados)

        with st.status("Corriendo OCR mock sobre los esquematicos\u2026", expanded=True) as status:
            barra = st.progress(0.0)
            progreso_texto = st.empty()
            progreso_texto.caption("Arrancando\u2026")

            # Run pipeline in a thread to avoid blocking the UI
            result_box = {"df": None, "error": None}
            
            def run_pipeline_thread():
                try:
                    df = pipeline_mock.run_pipeline(
                        db.SCHEMATICS_DIR,
                        omitir_codigos=omitir_codigos,
                        workers=int(workers),
                    )
                    result_box["df"] = df
                except Exception as e:
                    result_box["error"] = e
            
            thread = threading.Thread(target=run_pipeline_thread)
            thread.start()
            
            # Simple progress animation while thread runs
            import time
            dots = 0
            while thread.is_alive():
                dots = (dots + 1) % 4
                progreso_texto.caption(f"Procesando{'.' * dots}")
                time.sleep(0.5)
            
            thread.join()
            
            barra.progress(1.0)
            
            if result_box["error"]:
                raise result_box["error"]
            
            df = result_box["df"]
            
            # Persist results (same logic as pipeline_mock.main)
            if df is not None and not df.empty:
                if db.OCR_OUTPUT_XLSX.exists():
                    previo = pd.read_excel(db.OCR_OUTPUT_XLSX)
                    combinado = pd.concat([previo, df], ignore_index=True).drop_duplicates("codigo", keep="last")
                else:
                    combinado = df
                combinado.to_excel(db.OCR_OUTPUT_XLSX, index=False)
                procesados = len(df)
                total = len(combinado)
            else:
                procesados = 0
                total = len(pd.read_excel(db.OCR_OUTPUT_XLSX)) if db.OCR_OUTPUT_XLSX.exists() else 0

        if result_box["error"] is None:
            status.update(label="OCR terminado correctamente", state="complete")
            ui.info_banner(f"OCR completado: {procesados} nuevos/actualizados, {total} totales en ocr_output.xlsx.", tone="success")
            st.page_link("pages/2_Comparar.py", label="\u2192 Ir a Comparar contra el ground truth")
            if st.button("\U0001F504 Actualizar lista y estados", key="refresh_after_ocr"):
                st.rerun()
        else:
            status.update(label="El OCR termino con errores", state="error")
            ui.info_banner("Hubo un error corriendo el pipeline.", tone="danger")
            st.code(str(result_box["error"]))
