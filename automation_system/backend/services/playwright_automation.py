"""Automate a single correction through the Target System UI (Playwright).

The backend *recomputes* the expected correction from the authoritative files
(properties_db.xlsx + ocr_output.xlsx) every time — nothing from the request
body is trusted — and then drives the Target System frontend (:5173) through
its real UI:

    validate -> recompute expected -> open property detail in target UI ->
    read current field -> update field -> save -> verify -> result

Failures are reported with a stage name and never fall back to a direct
Excel write. ``sync_playwright`` runs on a dedicated thread so it plays well
with FastAPI's threadpool (sync Playwright refuses to run inside a thread
that is already inside an asyncio event loop).
"""
from __future__ import annotations

import os
import threading

from automation_system.backend.services.automation import (
    FIELD_LABELS,
    build_changes,
    _clean_numeric,
    _display,
)
from shared_store import db

# Where the Target System UI is served (the browser automation targets).
DEFAULT_TARGET_URL = os.environ.get("TARGET_UI_URL", "http://127.0.0.1:5173")

# Browser visibility. Default: visible browser (portfolio demo). Set
# PLAYWRIGHT_HEADLESS=1 to run without a window (e.g. CI).
DEFAULT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "0") == "1"

# DOM id per editable field in the Target System property detail UI.
FIELD_ID = {
    "superficie_m2": "property-field-superficie",
    "capacidad_personas": "property-field-capacidad",
    "plazas_estacionamiento": "property-field-estacionamiento",
    "anio_construccion": "property-field-anio",
    "salas": "property-field-salas",
}

ALLOWED_FIELDS = set(FIELD_LABELS)


def _recompute_expected(codigo: str, field: str) -> dict | None:
    """The correction the backend wants to apply, recomputed from the files.

    Returns {"field", "before", "expected"} or None when there is nothing
    to correct for this property/field.
    """
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    if propiedades.empty or ocr.empty or "codigo" not in ocr.columns:
        return None
    for item in build_changes(propiedades, ocr):
        if item["codigo"] == str(codigo):
            for change in item["changes"]:
                if change["field"] == field:
                    return {
                        "field": field,
                        "before": change["current_value"],
                        "expected": change["new_value"],
                    }
    return None


def _run_browser(codigo: str, field: str, expected, *, url: str, headless: bool) -> dict:
    """Drive the Target System UI with Playwright. Returns a structured result."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    steps: list[str] = []
    stage = "browser_start"

    def make_failure(message: str) -> dict:
        return {
            "success": False,
            "codigo": codigo,
            "field": field,
            "before": None,
            "expected": _display(expected),
            "after": None,
            "verified": False,
            "stage": stage,
            "error": message,
            "steps": list(steps),
        }

    field_id = FIELD_ID[field]
    field_selector = f"#{field_id}"
    detail_url = f"{url.rstrip('/')}/propiedades/{codigo}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.set_default_timeout(15_000)
            steps.append("[Playwright] browser_start: chromium launched (headless=%s)" % headless)

            stage = "navigation"
            page.goto(detail_url, wait_until="domcontentloaded")
            steps.append(f"[Playwright] navigation: target detail page loaded at {detail_url}")

            stage = "field_update"
            field_input = page.locator(field_selector).first
            field_input.wait_for(state="visible")
            current_raw = field_input.input_value()
            current = _clean_numeric(current_raw)
            steps.append(f"[Playwright] field_update: current value read = {current}")

            field_input.fill(str(_display(expected)))
            steps.append(f"[Playwright] field_update: typed {_display(expected)} into '{field_id}'")

            stage = "save"
            page.get_by_role("button", name="Guardar cambios").click()
            page.locator('[role="status"]').filter(
                has_text="Cambios guardados correctamente"
            ).wait_for(state="visible")
            steps.append("[Playwright] save: confirmation 'Cambios guardados correctamente' shown")

            stage = "verification"
            after_raw = field_input.input_value()
            after = _clean_numeric(after_raw)
            verified = after is not None and abs(float(after) - float(expected)) < 1e-9
            steps.append(f"[Playwright] verification: value after save = {after} (expected {_display(expected)})")

            return {
                "success": verified,
                "codigo": codigo,
                "field": field,
                "before": current,
                "expected": _display(expected),
                "after": after,
                "verified": verified,
                "stage": None if verified else "verification",
                "error": None if verified else "El valor leido tras guardar no coincide con el esperado",
                "steps": steps,
            }
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            return make_failure(str(exc))
        finally:
            browser.close()


def apply_correction(codigo: str, field: str, url: str = DEFAULT_TARGET_URL, headless: bool = DEFAULT_HEADLESS) -> dict:
    """Recompute the expected correction and apply it through the Target UI.

    Raises ValueError for invalid field / missing property so the router can
    return proper HTTP statuses. Returns a non-raising dict result otherwise,
    including the no-change case (success=False, stage='no_change').
    """
    if field not in ALLOWED_FIELDS:
        raise ValueError(
            f"Campo no automatizable: {field!r}. Permitidos: {sorted(ALLOWED_FIELDS)}"
        )

    propiedades = db.read_properties()
    if propiedades.empty or not (propiedades["codigo"].astype(str) == str(codigo)).any():
        raise ValueError(f"No existe la propiedad {codigo} en target_system")

    target = _recompute_expected(codigo, field)
    if target is None:
        return {
            "success": False,
            "codigo": codigo,
            "field": field,
            "before": None,
            "expected": None,
            "after": None,
            "verified": False,
            "stage": "no_change",
            "error": f"No hay correccion pendiente para {codigo} en {field}",
            "steps": [],
        }

    # Playwright sync API must run on a thread outside the event loop.
    result_box: dict = {}
    thread = threading.Thread(
        target=lambda: result_box.update(
            _run_browser(codigo, field, target["expected"], url=url, headless=headless)
        )
    )
    thread.start()
    thread.join()

    return result_box