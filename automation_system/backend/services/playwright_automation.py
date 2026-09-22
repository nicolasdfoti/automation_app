"""Automate corrections through the Target System UI (Playwright).

The backend *recomputes* the expected corrections from the authoritative files
(properties_db.xlsx + ocr_output.xlsx) every time — nothing from the request
body is trusted — and then drives the Target System frontend (:5173) through
its real UI:

    validate -> recompute expected -> open property detail in target UI ->
    read current fields -> update fields -> save (single form submit) ->
    reload -> read back and verify -> result

Browser lifecycle
-----------------
One automation run = ONE Chromium instance. ``apply_corrections`` (batch) and
``apply_correction`` (single) always go through ``_run_browser_run`` which:

- launches Chromium ONCE,
- creates ONE browser context,
- reuses ONE page for every correction of the run (navigating to each
  property's detail page),
- only recreates the page after a failed correction so the next one can
  continue with the same browser/context,
- closes Chromium ONCE when the run finishes.

The browser stays visible while the run is active. ``PLAYWRIGHT_HEADLESS=1``
switches to a headless (fast) mode using the exact same lifecycle; the
demo/directed inter-step pauses (``PLAYWRIGHT_STEP_DELAY_MS``) are only applied
when the browser is headed (human-observable continuity) and skipped in
headless mode. All real synchronization uses Playwright's waiting mechanisms
(locator.wait_for / wait_for_load_state / expect semantics); no large fixed
``time.sleep`` calls.

Failures are reported per correction with a stage name and never fall back to
a direct Excel write. ``sync_playwright`` runs on a dedicated thread so it
plays well with FastAPI's threadpool (sync Playwright refuses to run inside a
thread that is already inside an asyncio event loop).
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
# Only takes effect in headed mode; 0 disables it. Headless runs skip pauses.
DEFAULT_STEP_DELAY_MS = int(os.environ.get("PLAYWRIGHT_STEP_DELAY_MS", "750"))

# Playwright synchronization bounds (proper waits, not fixed sleeps).
DEFAULT_TIMEOUT_MS = 15_000
NAVIGATION_TIMEOUT_MS = 30_000

# DOM id per editable field in the Target System property detail UI.
FIELD_ID = {
    "superficie_m2": "property-field-superficie",
    "capacidad_personas": "property-field-capacidad",
    "plazas_estacionamiento": "property-field-estacionamiento",
    "anio_construccion": "property-field-anio",
    "salas": "property-field-salas",
}

ALLOWED_FIELDS = set(FIELD_LABELS)

SAVE_STATUS_TEXT = "Cambios guardados correctamente"


def _compute_pending(
    codigo: str,
    field: str | None,
    propiedades,
    ocr,
) -> list[dict]:
    """Pending corrections for ``codigo`` (and ``field`` when given).

    Recomputes the expected values from the files via ``build_changes``. Returns
    a list of ``{"field", "label", "current_value", "new_value"}`` items, or an
    empty list when there is nothing to correct for this property/field.
    """
    if propiedades.empty or ocr.empty or "codigo" not in ocr.columns:
        return []
    for item in build_changes(propiedades, ocr):
        if item["codigo"] == str(codigo):
            return [
                c for c in item["changes"] if field is None or c["field"] == field
            ]
    return []


def _recompute_pending(codigo: str, field: str | None) -> list[dict]:
    return _compute_pending(codigo, field, db.read_properties(), db.read_ocr_output())


def _build_jobs(codigos: list[str], field: str | None) -> list[tuple[str, list[dict]]]:
    """Reads the store ONCE and maps every code to its pending corrections.

    Codes with nothing to correct are left out (they become ``no_change``
    results without ever opening a browser).
    """
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    jobs: list[tuple[str, list[dict]]] = []
    for codigo in codigos:
        pending = _compute_pending(codigo, field, propiedades, ocr)
        if pending:
            jobs.append((codigo, pending))
    return jobs


def _pause(steps: list[str], *, headless: bool, step_delay_ms: int, note: str) -> None:
    """Small visible pause between steps (skipped when headless or 0ms)."""
    if headless or step_delay_ms <= 0:
        return
    steps.append(f"[Playwright] pausa {step_delay_ms}ms: {note}")
    time.sleep(step_delay_ms / 1000.0)


def _field_targets(pending: list[dict]) -> list[dict]:
    return [
        {
            "field": c["field"],
            "label": c["label"],
            "expected": c["new_value"],
        }
        for c in pending
    ]


def _make_no_change(codigo: str, field: str | None) -> dict:
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


def _make_failure(
    codigo: str,
    pending: list[dict],
    *,
    stage: str,
    error: str,
    steps: list[str],
) -> dict:
    targets = _field_targets(pending)
    single = len(targets) == 1
    changes = [
        {
            "field": t["field"],
            "label": t["label"],
            "before": None,
            "expected": _display(t["expected"]),
            "after": None,
            "verified": False,
        }
        for t in targets
    ]
    return {
        "success": False,
        "codigo": codigo,
        "field": targets[0]["field"] if single else None,
        "before": None,
        "expected": _display(targets[0]["expected"]) if single else None,
        "after": None,
        "verified": False,
        "changes": changes,
        "stage": stage,
        "error": error,
        "steps": list(steps),
    }


def _apply_property(
    page,
    codigo: str,
    pending: list[dict],
    *,
    url: str,
    headless: bool,
    step_delay_ms: int,
) -> dict:
    """Correct ONE property on a shared page (navigate -> edit -> save -> verify).

    The page is reused across the whole run; navigation to the next property
    happens here. Raises nothing: Playwright errors are converted into a
    structured failure result with the failing ``stage``.
    """
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    steps: list[str] = []
    stage = "navigation"

    targets = _field_targets(pending)
    single = len(targets) == 1
    detail_url = f"{url.rstrip('/')}/propiedades/{codigo}"

    try:
        stage = "navigation"
        page.goto(detail_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
        steps.append(
            f"[Playwright] navigation: detalle de {codigo} cargado en {detail_url}"
        )
        _pause(steps, headless=headless, step_delay_ms=step_delay_ms, note="pagina del detalle cargada")

        stage = "field_update"
        before_values: dict[str, float | int | None] = {}
        for t in targets:
            field_input = page.locator(f"#{FIELD_ID[t['field']]}").first
            field_input.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
            before = _clean_numeric(field_input.input_value())
            before_values[t["field"]] = before
            steps.append(
                f"[Playwright] field_update: {t['field']} valor actual leido = {_display(before)}"
            )
        for t in targets:
            page.locator(f"#{FIELD_ID[t['field']]}").first.fill(
                str(_display(t["expected"]))
            )
            steps.append(
                f"[Playwright] field_update: escrito {_display(t['expected'])} en "
                f"'#{FIELD_ID[t['field']]}'"
            )
        _pause(steps, headless=headless, step_delay_ms=step_delay_ms, note="campos editados")

        stage = "save"
        page.get_by_role("button", name="Guardar cambios").click()
        page.locator("[role='status']").filter(
            has_text=SAVE_STATUS_TEXT
        ).wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
        steps.append(
            f"[Playwright] save: confirmacion '{SAVE_STATUS_TEXT}' visible"
        )
        _pause(steps, headless=headless, step_delay_ms=step_delay_ms, note="guardado, recargando para verificar")

        stage = "verification"
        # Reload so the values read back come from the persisted Target data,
        # not from what Playwright just typed.
        page.reload(wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
        changes: list[dict] = []
        all_verified = True
        for t in targets:
            field_input = page.locator(f"#{FIELD_ID[t['field']]}").first
            field_input.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
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
            "field": targets[0]["field"] if single else None,
            "before": before_values.get(targets[0]["field"]) if single else None,
            "expected": _display(targets[0]["expected"]) if single else None,
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
        return _make_failure(
            codigo, pending, stage=stage, error=str(exc), steps=steps
        )
    except Exception as exc:  # last-resort isolation for the current property
        return _make_failure(
            codigo, pending, stage=stage or "error", error=str(exc), steps=steps
        )


def _run_browser_run(
    jobs: list[tuple[str, list[dict]]],
    *,
    url: str,
    headless: bool,
    step_delay_ms: int,
) -> tuple[list[dict], list[str]]:
    """Launch ONE browser, process every job, close the browser once.

    Returns ``(results, run_steps)``. The browser, context and page are kept
    alive for the entire run; a page is only recreated after a failed
    correction so the run can continue without relaunching Chromium.
    """
    from playwright.sync_api import sync_playwright

    results: list[dict] = []
    run_steps: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        run_steps.append(
            "[Playwright] browser_start: chromium abierto "
            f"(headless={headless}, {'ventana visible' if not headless else 'sin ventana'})"
        )
        _pause(
            run_steps,
            headless=headless,
            step_delay_ms=step_delay_ms,
            note="navegador abierto",
        )
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        try:
            for codigo, pending in jobs:
                try:
                    result = _apply_property(
                        page,
                        codigo,
                        pending,
                        url=url,
                        headless=headless,
                        step_delay_ms=step_delay_ms,
                    )
                finally:
                    # Only recreate the page (same browser/context) when the
                    # previous correction left it unusable.
                    try:
                        if page.is_closed():
                            page = context.new_page()
                            page.set_default_timeout(DEFAULT_TIMEOUT_MS)
                    except Exception:
                        try:
                            page = context.new_page()
                            page.set_default_timeout(DEFAULT_TIMEOUT_MS)
                        except Exception:
                            pass
                results.append(result)
                if not result["success"]:
                    run_steps.append(
                        f"[Playwright] correccion de {codigo} fallida (_stage={result['stage']})"
                    )
                _pause(
                    run_steps,
                    headless=headless,
                    step_delay_ms=step_delay_ms,
                    note=f"siguiente correccion ({codigo})",
                )
        finally:
            try:
                browser.close()
            except Exception:
                pass
            run_steps.append("[Playwright] browser_close: chromium cerrado")

    return results, run_steps


def _run_in_thread(fn):
    """Run a sync Playwright routine on a dedicated thread (outside the loop)."""
    result_box: dict = {}
    thread = threading.Thread(target=lambda: result_box.update(fn()))
    thread.start()
    thread.join()
    return result_box


def apply_correction(
    codigo: str,
    field: str | None = None,
    url: str = DEFAULT_TARGET_URL,
    headless: bool | None = None,
    step_delay_ms: int = DEFAULT_STEP_DELAY_MS,
) -> dict:
    """Recompute the pending corrections and apply them through the Target UI.

    When ``field`` is None every pending field of the property is corrected in
    one browser session. ``headless`` lets the caller override the module
    default (``PLAYWRIGHT_HEADLESS``) for a single run. Raises ValueError for
    invalid field / missing property so the router can return proper HTTP
    statuses. Returns a non-raising dict result otherwise, including the
    no-change case (success=False, stage='no_change').
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
        return _make_no_change(codigo, field)

    effective_headless = DEFAULT_HEADLESS if headless is None else bool(headless)

    box = _run_in_thread(
        lambda: {
            "_": _run_browser_run(
                [(codigo, pending)],
                url=url,
                headless=effective_headless,
                step_delay_ms=step_delay_ms,
            )
        }
    )
    results, run_steps = box["_"]
    result = results[0]
    # Single-property results keep the browser lifecycle in their own steps so
    # the (previously public) step stream stays informative and unchanged.
    result["steps"] = run_steps + result["steps"]
    return result


def apply_corrections(
    codigos: list[str],
    field: str | None = None,
    url: str = DEFAULT_TARGET_URL,
    headless: bool | None = None,
    step_delay_ms: int = DEFAULT_STEP_DELAY_MS,
) -> dict:
    """Correct several properties in ONE browser run (persistent lifecycle).

    The browser opens once, stays visible for the whole run, reuses a single
    context/page across every correction and closes once at the end. Codes with
    nothing to correct produce ``no_change`` results without a browser.
    ``headless`` overrides the module default (``PLAYWRIGHT_HEADLESS``) for
    this run. Raises ValueError for an invalid field (422) or a missing
    property (404).
    """
    if field is not None and field not in ALLOWED_FIELDS:
        raise ValueError(
            f"Campo no automatizable: {field!r}. Permitidos: {sorted(ALLOWED_FIELDS)}"
        )

    codigos = [str(c) for c in codigos]
    if not codigos:
        raise ValueError("Debe indicar al menos un codigo")

    propiedades = db.read_properties()
    if not propiedades.empty:
        known = set(propiedades["codigo"].astype(str))
        missing = [c for c in codigos if c not in known]
        if missing:
            raise ValueError(
                f"No existe la propiedad {missing[0]} en target_system"
            )

    jobs = _build_jobs(codigos, field)

    if not jobs:
        return {
            "success": False,
            "total": 0,
            "corrected": 0,
            "failed": 0,
            "without_changes": len(codigos),
            "results": [_make_no_change(c, field) for c in codigos],
            "steps": [],
        }

    effective_headless = DEFAULT_HEADLESS if headless is None else bool(headless)

    box = _run_in_thread(
        lambda: {
            "run": _run_browser_run(
                jobs,
                url=url,
                headless=effective_headless,
                step_delay_ms=step_delay_ms,
            )
        }
    )
    results, run_steps = box["run"]
    result_by_code = {r["codigo"]: r for r in results}

    ordered_results: list[dict] = []
    for codigo in codigos:
        if codigo in result_by_code:
            ordered_results.append(result_by_code[codigo])
        else:
            ordered_results.append(_make_no_change(codigo, field))

    processed = [r for r in ordered_results if r["stage"] != "no_change"]
    corrected = sum(1 for r in processed if r["success"])
    failed = sum(1 for r in processed if not r["success"])
    without_changes = len(ordered_results) - len(processed)

    return {
        "success": bool(processed) and failed == 0,
        "total": len(processed),
        "corrected": corrected,
        "failed": failed,
        "without_changes": without_changes,
        "results": ordered_results,
        "steps": run_steps,
    }