"""Read-only access to the properties workbook for the API layer.

Thin wrapper around ``shared_store.db`` (which stays untouched). Mirrors the
filter semantics of ``target_system/pages/1_Propiedades.py`` and serializes
rows into a JSON-friendly shape.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from shared_store import db


def _clean(value: Any) -> Any:
    """Convert pandas NaN/NA to None so the values are JSON-serializable."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def filter_properties(
    df: pd.DataFrame,
    *,
    search: str | None = None,
    fuente: str | None = None,
    esquematico: bool | None = None,
    superficie_min: float | None = None,
    superficie_max: float | None = None,
) -> pd.DataFrame:
    """Same filtering as the SIGE 'Propiedades' page, applied in the same order."""
    vista = df.copy()
    if search:
        vista = vista[
            vista["codigo"].astype(str).str.contains(search, case=False)
            | vista["direccion"].str.contains(search, case=False, na=False)
        ]
    if fuente:
        vista = vista[vista["fuente"] == fuente]
    if esquematico is not None:
        vista = vista[vista["esquematico_generado"] == esquematico]
    if superficie_min is not None:
        vista = vista[vista["superficie_m2"] >= superficie_min]
    if superficie_max is not None:
        vista = vista[vista["superficie_m2"] <= superficie_max]
    return vista


def properties_to_records(df: pd.DataFrame) -> list[dict]:
    """Rows as JSON-friendly dicts: codigo as str, NaN -> None, bools native."""
    records: list[dict] = []
    for row in df.to_dict("records"):
        record = {key: _clean(value) for key, value in row.items()}
        record["codigo"] = str(record["codigo"])
        record["esquematico_generado"] = bool(record["esquematico_generado"])
        records.append(record)
    return records


def list_properties(
    *,
    search: str | None = None,
    fuente: str | None = None,
    esquematico: bool | None = None,
    superficie_min: float | None = None,
    superficie_max: float | None = None,
) -> list[dict]:
    df = db.read_properties()
    vista = filter_properties(
        df,
        search=search,
        fuente=fuente,
        esquematico=esquematico,
        superficie_min=superficie_min,
        superficie_max=superficie_max,
    )
    return properties_to_records(vista)


def get_property(codigo: str) -> dict | None:
    df = db.read_properties()
    if df.empty:
        return None
    vista = df[df["codigo"].astype(str) == codigo]
    if vista.empty:
        return None
    return properties_to_records(vista.head(1))[0]