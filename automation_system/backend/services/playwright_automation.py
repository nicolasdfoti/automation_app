"""Automate corrections through the Target System UI (Playwright).

The backend *recomputes* the expected corrections from the authoritative files
(properties_db.xlsx + ocr_output.xlsx) every time — nothing from the request
body is trusted — and then drives the Target System frontend (:5173) through
its real UI:

    validate -> recompute expected -> open property detail in target UI ->
    read current fields -> update fields -> save (single form submit) ->
    reload -> read back and verify -> result

The browser is HEADED by default so the interactive/demo workflow is visible
on the desktop (for property e.g. ``http://127.0.0.1:5173/propiedades/877597``).
Set ``PLAYWRIGHT_HEADLESS=1`` for CI/test runs that must not open a window.
A small ``PLAYWRIGHT_STEP_DELAY_MS`` pause is inserted between meaningful
visible steps (browser open, navigation, field edit, save, verification) so a
human can follow the automation; the delay is skipped in headless mode.

Failures are reported with a stage name and never fall back to a direct
Excel write. ``sync_playwright`` runs on a dedicated thread so it plays well
with FastAPI's threadpool (sync Playwright refuses to run inside a thread
that is already inside an asyncio event loop).
"""
from __future__ import annotations

import os
import threading
import time

from automation_system.backend.services.automation import (
    FIELD_LABELS,
    build_changes,
    _clean_numeric,
    _display,
)
from shared_store import db

# Where the Target System UI is served (the browser automation targets).
DEFAULT_TARGET_URL = os.environ.get("TARGET_UI_URL", "http://127.0.0.1:5173")

# Browser visibility. Headed by default (interactive/demo workflow). Set
# PLAYWRIGHT_HEADLESS=1 to run without a window (e.g. CI/test runs).
DEFAULT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "0") == "1"

# Pause between important visible steps so a human can observe the automation.
# Only takes effect in headed mode; 0 disables it.
DEFAULT_STEP_DELAY_MS = int(os.environ.get("PLAYWRIGHT_STEP_DELAY_MS", "750"))

# DOM id per editable field in the Target System property detail UI.
FIELD_ID = {
    "superficie_m2": "property-field-superficie",
    "capacidad_personas": "property-field-capacidad",
    "plazas_estacionamiento": "property-field-estacionamiento",
    "anio_construccion": "property-field-anio",
    "salas": "property-field-salas",
}

ALLOWED_FIELDS = set(FIELD_LABELS)


def _recompute_pending(codigo: str, field: str | None) -> list[dict]:
    """Pending corrections for ``codigo`` (and ``field`` when given).

    Recomputes the expected values from the files via ``build_changes``. Returns
    a list of ``{"field", "label", "current_value", "new_value"}`` items, or an
    empty list when there is nothing to correct for this property/field.
    """
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    if propiedades.empty or ocr.empty or "codigo" not in ocr.columns:
        return []
    for item in build_changes(propiedades, ocr):
        if item["codigo"] == str(codigo):
            changes = [
                c for c in item["changes"] if field is None or c["field"] == field
            ]
            return changes
    return []


def _pause(steps: list[str], *, headless: bool, step_delay_ms: int, note: str) -> None:
    """Small visible pause between steps (skipped when headless or 0ms)."""
    if headless or step_delay_ms <= 0:
        return
    steps.append(f"[Playwright] pausa {step_delay_ms}ms: {note}")
    time.sleep(step_delay_ms / 1000.0)


def _run_browser(
    codigo: str,
    pending: list[dict],
    *,
    url: str,
    headless: bool,
    step_delay_ms: int,
) -> dict:
    """Drive the Target System UI with Playwright. Returns a structured result."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    steps: list[str] = []
    stage = "browser_start"

    field_targets = [
        {
            "field": c["field"],
            "label": c["label"],
            "expected": c["new_value"],
        }
        for c in pending
    ]
    single = len(field_targets) == 1
    detail_url = f"{url.rstrip('/')}/propiedades/{codigo}"

    def make_failure(message: str) -> dict:
        changes = [
            {
                "field": t["field"],
                "label": t["label"],
                "before": None,
                "expected": _display(t["expected"]),
                "after": None,
                "verified": False,
            }
            for t in field_targets
        ]
        return {
            "success": False,
            "codigo": codigo,
            "field": field_targets[0]["field"] if single else None,
            "before": None,
            "expected": _display(field_targets[0]["expected"]) if single else None,
            "after": None,
            "verified": False,
            "changes": changes,
            "stage": stage,
            "error": message,
            "steps": list(steps),
        }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.set_default_timeout(15_000)
            steps.append(
                f"[Playwright] browser_start: chromium abierto (headless={headless}, ventana visible)"
            )
            _pause(
                steps,
                headless=headless,
                step_delay_ms=step_delay_ms,
                note="navegador abierto",
            )

            stage = "navigation"
            page.goto(detail_url, wait_until="domcontentloaded")
            steps.append(
                f"[Playwright] navigation: detalle de {codigo} cargado en {detail_url}"
            )
            _pause(
                steps,
                headless=headless,
                step_delay_ms=step_delay_ms,
                note="pagina del detalle cargada",
            )

            stage = "field_update"
            before_values: dict[str, float | int | None] = {}
            for t in field_targets:
                field_id = FIELD_ID[t["field"]]
                field_input = page.locator(f"#{field_id}").first
                field_input.wait_for(state="visible")
                before = _clean_numeric(field_input.input_value())
                before_values[t["field"]] = before
                steps.append(
                    f"[Playwright] field_update: {t['field']} valor actual leido = {_display(before)}"
                )
            for t in field_targets:
                field_id = FIELD_ID[t["field"]]
                page.locator(f"#{field_id}").first.fill(str(_display(t["expected"])))
                steps.append(
                    f"[Playwright] field_update: escrito {_display(t['expected'])} en '#{field_id}'"
                )
            _pause(
                steps,
                headless=headless,
                step_delay_ms=step_delay_ms,
                note="campos editados",
            )

            stage = "save"
            page.get_by_role("button", name="Guardar cambios").click()
            page.locator('[role="status"]').filter(
                has_text="Cambios guardados correctamente"
            ).wait_for(state="visible")
            steps.append("[Playwright] save: confirmacion 'Cambios guardados correctamente' visible")
            _pause(
                steps,
                headless=headless,
                step_delay_ms=step_delay_ms,
                note="guardado, recargando para verificar",
            )

            stage = "verification"
            # Reload so the values read back come from the persisted Target data,
            # not from what Playwright just typed.
            page.reload(wait_until="domcontentloaded")
            changes: list[dict] = []
            all_verified = True
            for t in field_targets:
                field_id = FIELD_ID[t["field"]]
                field_input = page.locator(f"#{field_id}").first
                field_input.wait_for(state="visible")
                after = _clean_numeric(field_input.input_value())
                expected_num = _clean_numeric(t["expected"])
                verified = (
                    after is not None
                    and expected_num is not None
                    and abs(float(after) - float(expected_num)) < 1e-9
                )
                all_verified = all_verified and verified
                changes.append({
                    "field": t["field"],
                    "label": t["label"],
                    "before": before_values.get(t["field"]),
                    "expected": _display(t["expected"]),
                    "after": after,
                    "verified": verified,
                })
                steps.append(
                    f"[Playwright] verification: tras recargar, {t['field']} = {_display(after)}"
                    f" (esperado {_display(t['expected'])}, {'OK' if verified else 'DIFERENTE'})"
                )

            return {
                "success": all_verified,
                "codigo": codigo,
                "field": field_targets[0]["field"] if single else None,
                "before": before_values.get(field_targets[0]["field"]) if single else None,
                "expected": _display(field_targets[0]["expected"]) if single else None,
                "after": changes[0]["after"] if single else None,
                "verified": changes[0]["verified"] if single else False,
                "changes": changes,
                "stage": None if all_verified else "verification",
                "error": (
                    None
                    if all_verified
                    else "Un valor leido tras guardar y recargar no coincide con el esperado"
                ),
                "steps": steps,
            }
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            return make_failure(str(exc))
        finally:
            browser.close()


def apply_correction(
    codigo: str,
    field: str | None = None,
    url: str = DEFAULT_TARGET_URL,
    headless: bool = DEFAULT_HEADLESS,
    step_delay_ms: int = DEFAULT_STEP_DELAY_MS,
) -> dict:
    """Recompute the pending corrections and apply them through the Target UI.

    When ``field`` is None every pending field of the property is corrected in
    one browser session. Raises ValueError for invalid field / missing property
    so the router can return proper HTTP statuses. Returns a non-raising dict
    result otherwise, including the no-change case (success=False,
    stage='no_change').
    """
    if field is not None and field not in ALLOWED_FIELDS:
        raise ValueError(
            f"Campo no automatizable: {field!r}. Permitidos: {sorted(ALLOWED_FIELDS)}"
        )

    propiedades = db.read_properties()
    if propiedades.empty or not (propiedades["codigo"].astype(str) == str(codigo)).any():
        raise ValueError(f"No existe la propiedad {codigo} en target_system")

    pending = _recompute_pending(codigo, field)
    if not pending:
        target = "ningun campo" if field is None else field
        return {
            "success": False,
            "codigo": codigo,
            "field": field,
            "before": None,
            "expected": None,
            "after": None,
            "verified": False,
            "changes": [],
            "stage": "no_change",
            "error": f"No hay correccion pendiente para {codigo} en {target}",
            "steps": [],
        }

    # Playwright sync API must run on a thread outside the event loop.
    result_box: dict = {}
    thread = threading.Thread(
        target=lambda: result_box.update(
            _run_browser(
                codigo,
                pending,
                url=url,
                headless=headless,
                step_delay_ms=step_delay_ms,
            )
        )
    )
    thread.start()
    thread.join()

    return result_box