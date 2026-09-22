"""Test battery for the Step 6C.1 Playwright automation flow.

Run with the project venv:

    venv/Scripts/python.exe -m backend.tests.test_playwright

Follows the inline launcher convention (no pytest dependency). shared_store
workbooks are snapshotted first and restored unconditionally in ``finally``,
so property 550482 is left exactly as it was. The mock external system is
started as a subprocess on port 5174 and its own JSON store is seeded from
the shared_store.

Coverage (per the 6C.1 spec):
1. Endpoint exists.
2. Invalid field rejected (422).
3. Missing property rejected (404).
4. No-change case rejected with success=False / stage='no_change' (no browser).
5. Playwright flow succeeds for 550482 / superficie_m2 via the real browser.
6. Verification confirms the new value after saving.
7. A failure (external system unreachable) does NOT modify properties_db.xlsx.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from backend.services import automation as automation_svc  # noqa: E402
from backend.services import playwright_automation as pw_svc  # noqa: E402
from mock_external_system import store as ext_store  # noqa: E402
from shared_store import db  # noqa: E402

TARGET_CODIGO = "550482"
FIELD = "superficie_m2"
SNAPSHOT_DIR = Path(os.environ["TEMP"]) / f"playwright_test_{os.getpid()}"
EXTERNAL_PORT = 5174
EXTERNAL_URL = f"http://127.0.0.1:{EXTERNAL_PORT}"

client = TestClient(app)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(f, SNAPSHOT_DIR / f.name)
    pdfs = SNAPSHOT_DIR / "schematics"
    pdfs.mkdir(exist_ok=True)
    for pdf in db.SCHEMATICS_DIR.glob("*.pdf"):
        shutil.copy2(pdf, pdfs / pdf.name)


def restore() -> None:
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(SNAPSHOT_DIR / f.name, f)
    for pdf in db.SCHEMATICS_DIR.glob("*.pdf"):
        pdf.unlink()
    for pdf in (SNAPSHOT_DIR / "schematics").glob("*.pdf"):
        shutil.copy2(pdf, db.SCHEMATICS_DIR / pdf.name)
    print("[restore] shared_store restaurado al snapshot")


def seed_stale() -> object:
    """Pone superficie de 550482 en estado stale (difiera del OCR)."""
    ocr = db.read_ocr_output().drop_duplicates("codigo", keep="last")
    cur = float(ocr.loc[ocr["codigo"].astype(str) == TARGET_CODIGO, FIELD].iloc[0])
    stale = round(cur * 0.9, 1)  # p.ej. 563.0 -> 506.7 (dentro de limite)
    assert not automation_svc._equivalentes(stale, cur), "el valor stale debe diferir del OCR"
    assert automation_svc._en_rango(FIELD, stale)
    db.update_property(TARGET_CODIGO, {FIELD: stale})
    return stale


def run_mock_external() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_external_system.main:app",
         "--host", "127.0.0.1", "--port", str(EXTERNAL_PORT), "--log-level", "warning"],
        cwd=str(Path(__file__).resolve().parent.parent.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(80):
        if proc.poll() is not None:
            raise RuntimeError("mock external system exited during startup")
        try:
            urllib.request.urlopen(f"{EXTERNAL_URL}/api/health", timeout=0.5)
            return proc
        except Exception:
            time.sleep(0.25)
    proc.terminate()
    raise RuntimeError("mock external system did not become ready")


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
    ocr = db.read_ocr_output().drop_duplicates("codigo", keep="last")
    ocr_val = ocr.loc[ocr["codigo"].astype(str) == TARGET_CODIGO, FIELD].iloc[0]
    db.update_property(TARGET_CODIGO, {FIELD: ocr_val})  # fuerza estado sin cambio
    r = client.post("/api/automation/playwright", json={"codigo": TARGET_CODIGO, "field": FIELD})
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["success"] is False and body["stage"] == "no_change"
    print("[ok] sin cambios -> escenario no_change (sin abrir browser)")

    # --- 5/7. E2E: estado stale -> Playwright -> UI externa -> verificar -----
    e2e(ocr_val)


def e2e(ocr_val) -> None:
    stale = seed_stale()
    print(f"[setup] 550482 superficie puesta stale = {stale} (OCR={ocr_val})")

    proc = run_mock_external()
    try:
        urllib.request.urlopen(urllib.request.Request(f"{EXTERNAL_URL}/api/reseed", method="POST"), timeout=3).read()
        ext = ext_store.get(TARGET_CODIGO)
        assert ext is not None and automation_svc._clean_numeric(ext[FIELD]) is not None

        result = pw_svc.apply_correction(TARGET_CODIGO, FIELD, url=EXTERNAL_URL, headless=False)
        assert result["success"] is True, result
        assert result["codigo"] == TARGET_CODIGO and result["field"] == FIELD
        print("[ok] playwright flow exitoso (browser real)")

        # --- 6. verification confirma el nuevo valor ---
        assert result["verified"] is True, result
        assert result["after"] == result["expected"], result
        assert automation_svc._equivalentes(result["after"], ocr_val), result
        assert any("verification" in s for s in result["steps"])
        print(f"[ok] verificacion: before={result['before']} after={result['after']} (== OCR {ocr_val})")

        ext_after = ext_store.get(TARGET_CODIGO)
        assert automation_svc._equivalentes(ext_after[FIELD], result["after"])
        print("[ok] el sistema externo persistio el cambio via la UI (JSON propio)")

        # properties_db.xlsx NO debe tener el valor corregido (ese archivo es
        # de target_system; el browser solo toco el sistema externo)
        props_db = db.read_properties()
        prop = props_db[props_db["codigo"].astype(str) == TARGET_CODIGO].iloc[0]
        assert automation_svc._clean_numeric(prop[FIELD]) == stale, "properties_db no debe cambiar su value"

        # --- 7. fallo controlado (distribucion del sistema externo caida) ---
        before = db.read_properties()[db.read_properties()["codigo"].astype(str) == TARGET_CODIGO][FIELD].iloc[0]
        proc.terminate()
        proc.wait()
        failed = pw_svc.apply_correction(TARGET_CODIGO, FIELD, url=EXTERNAL_URL, headless=False)
        assert failed["success"] is False, failed
        assert failed["stage"] in {"browser_start", "navigation", "property_search",
                                   "property_open", "field_update", "save", "verification"}, failed
        after = db.read_properties()[db.read_properties()["codigo"].astype(str) == TARGET_CODIGO][FIELD].iloc[0]
        assert automation_svc._clean_numeric(after) == automation_svc._clean_numeric(before), (
            "properties_db.xlsx sigue sin modificarse ante un fallo"
        )
        print(f"[ok] fallo controlado durante '{failed['stage']}' sin tocar properties_db.xlsx")
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()


def main() -> None:
    snapshot()
    print(f"[setup] snapshot en {SNAPSHOT_DIR}")
    try:
        run_checks()
    finally:
        restore()
        ext_store.STORE_FILE.unlink(missing_ok=True)
    print("PLAYWRIGHT AUTOMATION TESTS: PASS")


if __name__ == "__main__":
    main()