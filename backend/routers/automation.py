"""Automation endpoints: preview, apply, and the Step 6C.1 Playwright flow.

Thin orchestration over ``backend/services/automation`` (the business logic
layer). ``apply`` recomputes the corrections server-side from the current
files every time; nothing is trusted from the browser. ``playwright`` drives
the Mock External System through its UI (Step 6C.1): the value to write is
recomputed server-side from the stored files and the external system is only
updated through real browser interaction — never by a direct Excel write.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    AutomationApplyResult,
    AutomationPreview,
    PlaywrightAutomationRequest,
    PlaywrightAutomationResult,
)
from backend.services import automation as automation_svc
from backend.services import playwright_automation as playwright_svc

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/preview", response_model=AutomationPreview)
def preview() -> AutomationPreview:
    """Proposed corrections (OCR vs current values); never modifies data."""
    return AutomationPreview(**automation_svc.preview())


@router.post("/apply", response_model=AutomationApplyResult)
def apply() -> AutomationApplyResult:
    """Apply the currently detected corrections to properties_db.xlsx."""
    return AutomationApplyResult(**automation_svc.apply_preview_changes())


@router.post("/playwright", response_model=PlaywrightAutomationResult)
def playwright(payload: PlaywrightAutomationRequest) -> PlaywrightAutomationResult:
    """Automatizar UNA correccion mediante el sistema externo (browser UI).

    Recomputa el cambio esperado desde los archivos autoridad
    (properties_db.xlsx + ocr_output.xlsx) y lo aplica via Playwright sobre
    la interfaz del sistema externo. No confia en valores enviados por el
    browser y nunca escribe Excel como fallback.
    """
    try:
        result = playwright_svc.apply_correction(payload.codigo, payload.field)
    except ValueError as exc:
        # Invalid field (422) or missing property (404) — same conventions as
        # the properties endpoints.
        if "Campo no automatizable" in str(exc):
            raise HTTPException(status_code=422, detail=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    return PlaywrightAutomationResult(**result)