"""Endpoints for schematic generation and download.

Thin wrapper over the existing ``pdf_creator.generator`` business logic; no
generator logic is duplicated here.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.schemas import (
    GenerateAllResult,
    PendingSchematicList,
    SchematicGenerateRequest,
    SchematicResult,
)
from backend.services import properties as properties_svc
from backend.services import schematics as schematics_svc

router = APIRouter(prefix="/schematics", tags=["schematics"])


@router.get("/pending", response_model=PendingSchematicList)
def read_pending() -> PendingSchematicList:
    items = schematics_svc.list_pending()
    return PendingSchematicList(count=len(items), items=items)


@router.post("/generate", response_model=SchematicResult)
def generate(payload: SchematicGenerateRequest) -> SchematicResult:
    record = properties_svc.get_property(payload.codigo)
    if record is None:
        raise HTTPException(
            status_code=404, detail=f"No existe la propiedad {payload.codigo} en target_system"
        )
    if record["esquematico_generado"]:
        raise HTTPException(
            status_code=409, detail=f"La propiedad {payload.codigo} ya tiene esquematico generado"
        )

    overrides = schematics_svc.build_numeric_overrides(
        superficie_m2=payload.superficie_m2 or 0.0,
        capacidad_personas=payload.capacidad_personas or 0,
        plazas_estacionamiento=payload.plazas_estacionamiento or 0,
        anio_construccion=payload.anio_construccion or 0,
        salas=payload.salas or 0,
    )
    return SchematicResult(**schematics_svc.generate_schematic(payload.codigo, overrides))


@router.post("/generate-all", response_model=GenerateAllResult)
def generate_all() -> GenerateAllResult:
    summary = schematics_svc.generate_all_pending()
    return GenerateAllResult(**summary)


@router.get("/{codigo}/download")
def download(codigo: str) -> FileResponse:
    status, path = schematics_svc.get_schematic_path(codigo)
    if status == "property_not_found":
        raise HTTPException(status_code=404, detail=f"No existe la propiedad {codigo} en target_system")
    if status == "no_schematic":
        raise HTTPException(status_code=404, detail=f"La propiedad {codigo} no tiene esquematico generado")
    if status == "file_missing":
        raise HTTPException(status_code=404, detail=f"No se encontro el archivo del esquematico de {codigo}")
    return FileResponse(path, media_type="application/pdf", filename=path.name)