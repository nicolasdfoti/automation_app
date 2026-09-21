"""Dashboard statistics formerly computed inside target_system/Home.py."""
from __future__ import annotations

import pandas as pd


def compute_dashboard_stats(df: pd.DataFrame) -> dict:
    """KPI values shown on the SIGE home page."""
    return {
        "total": len(df),
        "pendientes": int((df["esquematico_generado"] == False).sum()),  # noqa: E712
        "corregidas": int((df["fuente"] == "automatizacion OCR").sum()),
        "superficie_total": df["superficie_m2"].sum(),
        "capacidad_total": int(df["capacidad_personas"].sum()),
    }


def recent_activity(df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    """Most recently updated properties, newest first (same as SIGE home)."""
    reciente = df.copy()
    reciente["_fecha_ord"] = pd.to_datetime(
        reciente["ultima_actualizacion"], format="%d/%m/%Y", errors="coerce"
    )
    reciente = reciente.sort_values("_fecha_ord", ascending=False).head(limit)
    return reciente