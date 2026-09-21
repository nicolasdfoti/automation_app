"""
Pipeline de OCR mock - v1 (dentro de pipeline_app)

Misma arquitectura que un pipeline real: descubrimiento de proyectos
por codigo, procesamiento independiente por proyecto, paralelizado,
progreso impreso como "procesados X/Y". La diferencia adrede respecto
a un OCR real es que, como el PDF mock tiene texto seleccionable, se
lee directo con pdfplumber en vez de con reconocimiento de trazos/digitos.

Lee los PDFs de shared_store.SCHEMATICS_DIR y escribe el resultado en
shared_store.OCR_OUTPUT_XLSX.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared_store import db


def extract_codigo(stem: str):
    m = re.match(r"^(\d{5,8})", stem.strip())
    return m.group(1) if m else None


def discover_projects(base_dir: Path, omitir_codigos=None):
    omitir_codigos = set(omitir_codigos or [])
    sin_clasificar = []
    proyectos = []
    for pdf in sorted(base_dir.glob("*.pdf")):
        codigo = extract_codigo(pdf.stem)
        if not codigo:
            sin_clasificar.append(pdf)
            continue
        if codigo in omitir_codigos:
            continue
        proyectos.append({"codigo": codigo, "pdf": pdf})

    if sin_clasificar:
        print(f"[aviso] {len(sin_clasificar)} PDF sin codigo reconocible:")
        for p in sin_clasificar[:20]:
            print("   -", p)

    return proyectos


_PATTERNS = {
    "direccion": r"Direccion:\s*(.+)",
    "fecha_relevamiento": r"Fecha de relevamiento:\s*(\d{2}/\d{2}/\d{4})",
    "superficie_m2": r"Superficie:.*?(\d+(?:\.\d+)?)\s*m2",
    "capacidad_personas": r"Capacidad:.*?(\d+)\s*pers",
    "plazas_estacionamiento": r"estacionamiento:.*?(\d+)\s*u\.",
    "anio_construccion": r"construccion:.*?(\d{4})",
    "salas": r"ambientes:.*?(\d+)\s*u\.",
}
_TIPOS = {
    "superficie_m2": float, "capacidad_personas": int,
    "plazas_estacionamiento": int, "anio_construccion": int, "salas": int,
}


def procesar_proyecto(proyecto: dict) -> dict:
    codigo, pdf_path = proyecto["codigo"], proyecto["pdf"]
    fila = {"codigo": codigo, "archivo": pdf_path.name}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = pdf.pages[0].extract_text() or ""
    except Exception as e:
        fila["error"] = str(e)
        for campo in _PATTERNS:
            fila[campo] = None
        return fila

    for campo, patron in _PATTERNS.items():
        m = re.search(patron, texto)
        if not m:
            fila[campo] = None
            continue
        valor = m.group(1).strip()
        caster = _TIPOS.get(campo)
        try:
            fila[campo] = caster(valor) if caster else valor
        except ValueError:
            fila[campo] = None

    return fila


def run_pipeline(base_dir: Path, omitir_codigos=None, workers: int = 1, limite=None) -> pd.DataFrame:
    proyectos = discover_projects(base_dir, omitir_codigos)
    if limite:
        proyectos = proyectos[:limite]

    print(f"Proyectos a procesar (tras filtrar pendientes): {len(proyectos)}")
    if not proyectos:
        return pd.DataFrame()

    filas = []
    if workers <= 1:
        for i, proyecto in enumerate(proyectos, 1):
            filas.append(procesar_proyecto(proyecto))
            if i % 5 == 0 or i == len(proyectos):
                print(f"  procesados {i}/{len(proyectos)}")
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(procesar_proyecto, p): p for p in proyectos}
            for i, fut in enumerate(as_completed(futs), 1):
                p = futs[fut]
                try:
                    filas.append(fut.result())
                except Exception as e:
                    print(f"[error] proyecto {p['codigo']}: {e}")
                    filas.append({"codigo": p["codigo"], "error": str(e)})
                if i % 5 == 0 or i == len(proyectos):
                    print(f"  procesados {i}/{len(proyectos)}")

    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser(description="Pipeline de OCR mock sobre esquematicos sinteticos")
    ap.add_argument("--omitir-codigos", type=str, default="")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()

    omitir = [c.strip() for c in args.omitir_codigos.split(",") if c.strip()]
    df = run_pipeline(db.SCHEMATICS_DIR, omitir_codigos=omitir, workers=args.workers, limite=args.limite)
    if df.empty:
        print("No hay proyectos nuevos para procesar.")
        return

    if db.OCR_OUTPUT_XLSX.exists():
        previo = pd.read_excel(db.OCR_OUTPUT_XLSX)
        combinado = pd.concat([previo, df], ignore_index=True).drop_duplicates("codigo", keep="last")
    else:
        combinado = df
    combinado.to_excel(db.OCR_OUTPUT_XLSX, index=False)
    print(f"Guardado: {db.OCR_OUTPUT_XLSX} ({len(combinado)} propiedades totales, "
          f"{len(df)} nuevas/actualizadas en esta corrida)")


if __name__ == "__main__":
    sys.exit(main())
