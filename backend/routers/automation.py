"""Automation endpoints: preview and apply the detected corrections.

Thin orchestration over ``backend/services/automation`` (the business logic
layer). ``apply`` recomputes the corrections server-side from the current
files every time; nothing is trusted from the browser. Playwright/browser
automation is explicitly out of scope for this workflow.
"""
from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import AutomationApplyResult, AutomationPreview
from backend.services import automation as automation_svc

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/preview", response_model=AutomationPreview)
def preview() -> AutomationPreview:
    """Proposed corrections (OCR vs current values); never modifies data."""
    return AutomationPreview(**automation_svc.preview())


@router.post("/apply", response_model=AutomationApplyResult)
def apply() -> AutomationApplyResult:
    """Apply the currently detected corrections to properties_db.xlsx."""
    return AutomationApplyResult(**automation_svc.apply_preview_changes())