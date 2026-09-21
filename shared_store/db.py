"""
shared_store — el punto de integracion entre los tres sistemas.

En un escenario real, pdf_creator / target_system / pipeline_app
integrarian via una API o una base de datos comun. Para la demo, ese
"comun" es esta carpeta: cada sistema la lee/escribe con las funciones
de aca, nunca importando el codigo interno de otro sistema.

- properties_db.xlsx  -> due\u00f1o: target_system (la propiedad existe o no
                          existe ahi; ese es el universo real de codigos)
- ground_truth.xlsx    -> due\u00f1o: pdf_creator (que valor "correcto" escribio
                          en cada esquematico que genero)
- schematics/           -> due\u00f1o: pdf_creator (los PDFs)
- ocr_output.xlsx       -> due\u00f1o: pipeline_app (lo que el OCR extrajo)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

STORE_DIR = Path(__file__).resolve().parent
PROPERTIES_XLSX = STORE_DIR / "properties_db.xlsx"
GROUND_TRUTH_XLSX = STORE_DIR / "ground_truth.xlsx"
SCHEMATICS_DIR = STORE_DIR / "schematics"
OCR_OUTPUT_XLSX = STORE_DIR / "ocr_output.xlsx"

SCHEMATICS_DIR.mkdir(parents=True, exist_ok=True)

PROPERTY_COLUMNS = [
    "codigo", "direccion",
    "superficie_m2", "capacidad_personas", "plazas_estacionamiento",
    "anio_construccion", "salas",
    "esquematico_generado", "archivo_esquematico",
    "fuente", "ultima_actualizacion",
]

NUMERIC_FIELDS = [
    "superficie_m2", "capacidad_personas", "plazas_estacionamiento",
    "anio_construccion", "salas",
]


# --- target_system: universo de propiedades ---------------------------

def read_properties() -> pd.DataFrame:
    if not PROPERTIES_XLSX.exists():
        return pd.DataFrame(columns=PROPERTY_COLUMNS)
    return pd.read_excel(PROPERTIES_XLSX)


def write_properties(df: pd.DataFrame) -> None:
    df.to_excel(PROPERTIES_XLSX, index=False)


def append_properties(records: list[dict]) -> None:
    df = read_properties()
    nuevo = pd.DataFrame(records)
    combinado = pd.concat([df, nuevo], ignore_index=True)
    write_properties(combinado)


def update_property(codigo: str, updates: dict) -> None:
    df = read_properties()
    mask = df["codigo"].astype(str) == str(codigo)
    if not mask.any():
        raise ValueError(f"No existe la propiedad {codigo} en target_system")
    for k, v in updates.items():
        if k in df.columns and df[k].dtype != object:
            df[k] = df[k].astype(object)  # evita LossySetitemError al mezclar tipos tras el roundtrip por excel
        df.loc[mask, k] = v
    write_properties(df)


def propiedades_pendientes_de_esquematico() -> pd.DataFrame:
    df = read_properties()
    if df.empty:
        return df
    return df[df["esquematico_generado"] == False]  # noqa: E712


# --- pdf_creator: ground truth de lo que escribio en cada PDF ---------

def append_ground_truth(record: dict) -> None:
    row = pd.DataFrame([record])
    if GROUND_TRUTH_XLSX.exists():
        existente = pd.read_excel(GROUND_TRUTH_XLSX)
        combinado = pd.concat([existente, row], ignore_index=True)
    else:
        combinado = row
    combinado.to_excel(GROUND_TRUTH_XLSX, index=False)


def read_ground_truth() -> pd.DataFrame:
    if not GROUND_TRUTH_XLSX.exists():
        return pd.DataFrame()
    return pd.read_excel(GROUND_TRUTH_XLSX)


# --- pipeline_app: salida del OCR --------------------------------------

def read_ocr_output() -> pd.DataFrame:
    if not OCR_OUTPUT_XLSX.exists():
        return pd.DataFrame()
    return pd.read_excel(OCR_OUTPUT_XLSX)
