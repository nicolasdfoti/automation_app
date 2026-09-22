"""OCR workflow endpoints — orchestration only, no OCR logic here."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.schemas import OcrResultList, OcrRunResult, OcrStatus
from backend.services import ocr as ocr_svc

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/run", response_model=OcrRunResult)
def run(
    reprocesar_todo: bool = Query(False, description="Ignorar lo ya procesado"),
) -> OcrRunResult:
    result = ocr_svc.run_ocr(reprocesar_todo=reprocesar_todo, workers=1)
    return OcrRunResult(**result)


@router.get("/status", response_model=OcrStatus)
def status() -> OcrStatus:
    return OcrStatus(**ocr_svc.read_status())


@router.get("/results", response_model=OcrResultList)
def results() -> OcrResultList:
    items = ocr_svc.read_results()
    return OcrResultList(count=len(items), items=items)