"""Validation tests for the automation_system Playwright flow (no browser).

Run with the project venv:

    venv/Scripts/python.exe -m automation_system.backend.tests.test_playwright_validation

Follows the inline launcher convention (no pytest dependency). shared_store
workbooks are snapshotted first and restored unconditionally in ``finally``.

Covers every path that does NOT require a real browser or the running Target
System stack: endpoint existence, invalid field (422), missing property (404)
and the no-change case (stage='no_change', no browser). The live E2E (driving
http://127.0.0.1:5173) requires Target UI + Target backend + Automation
backend up and is exercised manually / documented in the README.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from automation_system.backend.main import app  # noqa: E402
from automation_system.backend.services import automation as automation_svc  # noqa: E402
from automation_system.backend.services import playwright_automation as pw_svc  # noqa: E402
from shared_store import db  # noqa: E402

TARGET_CODIGO = "550482"
FIELD = "superficie_m2"
SNAPSHOT_DIR = Path(os.environ["TEMP"]) / f"playwright_validation_{os.getpid()}"

client = TestClient(app)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(f, SNAPSHOT_DIR / f.name)


def restore() -> None:
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(SNAPSHOT_DIR / f.name, f)
    print("[restore] shared_store restaurado al snapshot")


def run_checks() -> None:
    # --- 1. endpoint exists -------------------------------------------------
    r = client.post("/api/automation/playwright", json={})
    assert r.status_code == 422, r.text  # route exists: pydantic validation fires
    print("[ok] endpoint POST /api/automation/playwright existe (validacion 422)")

    # --- 2. invalid field rejected (422) ------------------------------------
    r = client.post("/api/automation/playwright", json={"codigo": TARGET_CODIGO, "field": "direccion"})
    assert r.status_code == 422, r.text
    print("[ok] campo invalido rechazado  (status=%s)" % r.status_code)

    # --- 3. missing property rejected (404) ---------------------------------
    r = client.post("/api/automation/playwright", json={"codigo": "999999", "field": FIELD})
    assert r.status_code == 404, r.text
    print("[ok] propiedad inexistente rechazada (status=%s)" % r.status_code)

    # --- 4. no-change case: rejected safely, no browser ---------------------
    ocr = db.read_ocr_output()
    assert "codigo" in ocr.columns and not ocr.empty
    ocr_norm = ocr.drop_duplicates("codigo", keep="last")
    ocr_val = ocr_norm.loc[ocr_norm["codigo"].astype(str) == TARGET_CODIGO, FIELD].iloc[0]
    db.update_property(TARGET_CODIGO, {FIELD: ocr_val})  # fuerza estado sin cambio
    result = pw_svc.apply_correction(TARGET_CODIGO, FIELD)
    assert result["success"] is False and result["stage"] == "no_change", result
    assert result["steps"] == []
    print("[ok] sin cambios -> escenario no_change (sin abrir browser)")


def main() -> None:
    snapshot()
    print(f"[setup] snapshot en {SNAPSHOT_DIR}")
    try:
        run_checks()
    finally:
        restore()
    print("PLAYWRIGHT VALIDATION TESTS: PASS")


if __name__ == "__main__":
    main()