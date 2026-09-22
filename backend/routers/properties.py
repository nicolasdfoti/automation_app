"""Endpoints for the SIGE property catalog."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import Property, PropertyList, PropertyUpdate
from backend.services import properties as properties_svc

router = APIRouter(prefix="/properties", tags=["properties"])

_VALID_FUENTE = {
    "carga manual (legacy)": "carga manual (legacy)",
    "automatizacion ocr": "automatizacion OCR",
}

# Canonical values map to the 'esquematico_generado' flag, matching the
# 'Con esquematico' / 'Pendiente' options of the SIGE page.
_ESTADO_MAP = {
    "generado": True,
    "con esquematico": True,
    "pendiente": False,
}


def _parse_fuente(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    if normalized not in _VALID_FUENTE:
        raise HTTPException(
            status_code=422,
            detail=f"fuente invalida: {value!r}. Valores admitidos: 'carga manual (legacy)', 'automatizacion OCR'.",
        )
    return _VALID_FUENTE[normalized]


def _parse_estado(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split()).casefold()
    if normalized not in _ESTADO_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"estado invalido: {value!r}. Valores admitidos: 'generado', 'con esquematico', 'pendiente'.",
        )
    return _ESTADO_MAP[normalized]


@router.get("", response_model=PropertyList)
def read_properties(
    search: str | None = Query(None, max_length=120, description="Substring de codigo o direccion (no sensible a mayusculas)."),
    fuente: str | None = Query(None, description="'carga manual (legacy)' o 'automatizacion OCR'."),
    estado: str | None = Query(None, description="'generado' | 'con esquematico' | 'pendiente'."),
    superficie_min: float | None = Query(None, ge=0, description="Filtra superficie_m2 >= valor."),
    superficie_max: float | None = Query(None, ge=0, description="Filtra superficie_m2 <= valor."),
) -> PropertyList:
    if superficie_min is not None and superficie_max is not None and superficie_min > superficie_max:
        raise HTTPException(status_code=422, detail="superficie_min no puede ser mayor que superficie_max.")

    items = properties_svc.list_properties(
        search=search.strip() if search else None,
        fuente=_parse_fuente(fuente),
        esquematico=_parse_estado(estado),
        superficie_min=superficie_min,
        superficie_max=superficie_max,
    )
    return PropertyList(count=len(items), items=items)


@router.get("/{codigo}", response_model=Property)
def read_property(codigo: str) -> Property:
    record = properties_svc.get_property(codigo)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No existe la propiedad {codigo} en target_system")
    return Property(**record)


@router.put("/{codigo}", response_model=Property)
def update_property(codigo: str, payload: PropertyUpdate) -> Property:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    record = properties_svc.update_property(codigo, updates)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No existe la propiedad {codigo} en target_system")
    return Property(**record)