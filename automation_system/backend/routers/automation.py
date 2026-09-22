"""Automation endpoints: preview, apply, and the Playwright flow.

Thin orchestration over ``automation_system/backend/services/automation`` (the
business logic layer). ``apply`` recomputes the corrections server-side from
the current files every time; nothing is trusted from the browser. ``playwright``
drives the Target System UI (http://127.0.0.1:5173) for ONE correction: the
value to write is recomputed server-side from the stored files and the target
is only updated through real browser interaction — never by a direct Excel
write.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from automation_system.backend.schemas import (
    AutomationApplyResult,
    AutomationPreview,
    PlaywrightAutomationRequest,
    PlaywrightAutomationResult,
)
from automation_system.backend.services import automation as automation_svc
from automation_system.backend.services import playwright_automation as playwright_svc

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/preview", response_model=AutomationPreview)
def preview() -> AutomationPreview:
    """Correcciones propuestas contra los datos actuales (solo lectura)."""
    return AutomationPreview(**automation_svc.preview())


@router.post("/apply", response_model=AutomationApplyResult)
def apply() -> AutomationApplyResult:
    """Aplica las correcciones detectadas a properties_db.xlsx."""
    return AutomationApplyResult(**automation_svc.apply_preview_changes())


@router.post("/playwright", response_model=PlaywrightAutomationResult)
def playwright(payload: PlaywrightAutomationRequest) -> PlaywrightAutomationResult:
    """Automatizar correcciones mediante la UI de target (browser headed).

    Recomputa los cambios esperados desde los archivos autoridad
    (properties_db.xlsx + ocr_output.xlsx) y los aplica via Playwright sobre la
    UI de target (:5173) en una ventana visible. Cuando ``payload.field`` es
    None se corrigen todos los campos pendientes de la propiedad. No confia en
    valores enviados por el browser y nunca escribe Excel como fallback.
    """
    try:
        result = playwright_svc.apply_correction(payload.codigo, payload.field)
    except ValueError as exc:
        # Invalid field (422) or missing property (404) — same conventions as
        # the target properties endpoints.
        if "Campo no automatizable" in str(exc):
            raise HTTPException(status_code=422, detail=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    return PlaywrightAutomationResult(**result)