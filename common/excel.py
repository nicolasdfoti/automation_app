"""Neutral Excel/data helpers shared by both future applications.

Centralizes the NaN/null handling, numeric cleaning/serialization and row
serialization semantics that today are duplicated in ``backend/services``
(properties, compare_api, ocr, schematics, automation). The implementations
below reproduce those behaviors exactly; nothing here knows about any
application or router.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd


def is_na(value: Any) -> bool:
    """True for None, pd.NA, or a float NaN."""
    if value is None or value is pd.NA:
        return True
    return isinstance(value, float) and math.isnan(value)


def clean(value: Any) -> Any:
    """None for NaN/NA, original value otherwise (JSON-safe serialization)."""
    return None if is_na(value) else value


def clean_numeric(value: Any):
    """None for missing/non-numeric/non-finite values, else the float.

    Mirrors automation's ``_clean_numeric``: None, float NaN, whitespace-only
    strings, unknown types and infinite values all become None.
    """
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(num) or math.isinf(num):
        return None
    return num


def equivalentes(a: Any, b: Any) -> bool:
    """Numeric equivalence ignoring representation (563, 563.0, '563')."""
    na, nb = clean_numeric(a), clean_numeric(b)
    if na is None and nb is None:
        return True
    if na is None or nb is None:
        return False
    return na == nb


def display(value: Any):
    """Clean numeric for display: int when it has no decimals, else float."""
    num = clean_numeric(value)
    if num is None:
        return None
    if isinstance(num, float) and num.is_integer():
        return int(num)
    return num


def properties_to_records(df: pd.DataFrame) -> list[dict]:
    """Serialize property rows to JSON-friendly dicts.

    Preserves the exact semantics of ``backend/services/properties.py``:
    NaN -> None, ``codigo`` as str, ``esquematico_generado`` as native bool.
    """
    records: list[dict] = []
    for row in df.to_dict("records"):
        record = {key: clean(value) for key, value in row.items()}
        record["codigo"] = str(record["codigo"])
        record["esquematico_generado"] = bool(record["esquematico_generado"])
        records.append(record)
    return records