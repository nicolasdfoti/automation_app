"""Target System API parity test battery.

Run with the project venv:

    venv/Scripts/python.exe -m target_system.backend.tests.test_target_api

Follows the project's inline test-battery convention (no pytest dependency).
Compares the new Target System API against the Phase 1 baseline snapshot
(docs/phase0_endpoint_baseline.json). The PUT test snapshots the workbook and
restores it unconditionally in ``finally``.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

from fastapi.testclient import TestClient  # noqa: E402

from target_system.backend.main import app  # noqa: E402
from shared_store import db  # noqa: E402

BASELINE_FILE = REPO_ROOT / "docs" / "phase0_endpoint_baseline.json"
SNAPSHOT_DIR = Path(os.environ["TEMP"]) / f"target_api_test_{os.getpid()}"

client = TestClient(app)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    shutil.copy2(db.PROPERTIES_XLSX, SNAPSHOT_DIR / db.PROPERTIES_XLSX.name)


def restore() -> None:
    shutil.copy2(SNAPSHOT_DIR / db.PROPERTIES_XLSX.name, db.PROPERTIES_XLSX)


def load_baseline() -> dict:
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


def run_checks() -> None:
    baseline = load_baseline()

    # --- health ---
    r = client.get("/api/health")
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok"}
    assert r.json() == baseline["/api/health"]["body"]
    print("[ok] /api/health identico al baseline")

    # --- properties list: structure, count, item shape, string codigo ---
    r = client.get("/api/properties")
    assert r.status_code == 200, r.text
    body = r.json()
    base_body = baseline["/api/properties"]["body"]
    assert body["count"] == base_body["count"] == 20, (body["count"], base_body["count"])
    assert len(body["items"]) == len(base_body["items"]) == 20
    assert list(body["items"][0].keys()) == list(base_body["items"][0].keys())
    assert body == base_body, "GET /api/properties difiere del baseline"
    assert all(isinstance(i["codigo"], str) for i in body["items"])
    print(f"[ok] /api/properties identico al baseline ({body['count']} items, codigo str)")

    # --- filtering / search behavior ---
    r = client.get("/api/properties", params={"search": "insisti"})
    assert r.status_code == 200
    subset = r.json()
    assert subset["count"] < body["count"]
    for item in subset["items"]:
        haystack = f"{item['codigo']} {item['direccion']}".casefold()
        assert "insisti" in haystack
    r = client.get("/api/properties", params={"estado": "pendiente"})
    assert r.status_code == 200
    assert all(i["esquematico_generado"] is False for i in r.json()["items"])
    r = client.get("/api/properties", params={"fuente": "automatizacion OCR"})
    assert r.status_code == 200
    assert r.json()["count"] == body["count"]  # corpus completo es totalmente automatizado
    r = client.get("/api/properties", params={"superficie_min": "isimo_bad"})
    assert r.status_code == 422
    r = client.get("/api/properties", params={"superficie_min": 800, "superficie_max": 200})
    assert r.status_code == 422
    print("[ok] filtros/search: busqueda, estado, fuente, 422 en rangos invalidos")

    # --- detail 550482 matches baseline ---
    r = client.get("/api/properties/550482")
    assert r.status_code == 200, r.text
    assert r.json() == baseline["/api/properties/550482"]["body"]
    print("[ok] /api/properties/550482 identico al baseline")

    # --- missing property 404 behavior ---
    r = client.get("/api/properties/999999")
    assert r.status_code == 404
    assert r.json() == baseline["/api/properties/999999"]["body"]
    r = client.put("/api/properties/999999", json={"direccion": "x"})
    assert r.status_code == 404
    print("[ok] propiedad inexistente -> 404 (GET y PUT)")

    # --- stats matches baseline ---
    r = client.get("/api/stats")
    assert r.status_code == 200, r.text
    assert r.json() == baseline["/api/stats"]["body"]
    print("[ok] /api/stats identico al baseline")

    # --- update: snapshot/restore, isolated ---
    target_codigo = "239789"
    before = client.get(f"/api/properties/{target_codigo}").json()
    payload = {"superficie_m2": float(before["superficie_m2"]) + 1.0}
    r = client.put(f"/api/properties/{target_codigo}", json=payload)
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["superficie_m2"] == payload["superficie_m2"]
    assert updated["codigo"] == target_codigo
    assert updated["direccion"] == before["direccion"]
    # persisted
    r2 = client.get(f"/api/properties/{target_codigo}")
    assert r2.json()["superficie_m2"] == payload["superficie_m2"]
    # validation still enforced
    rbad = client.put(f"/api/properties/{target_codigo}", json={"superficie_m2": -5})
    assert rbad.status_code == 422
    print("[ok] PUT actualiza y persiste; validacion 422 preservada")

    # --- no automation routes exist ---
    for path in ("/api/ocr/status", "/api/compare", "/api/schematics/pending", "/api/automation/preview"):
        r = client.get(path)
        assert r.status_code == 404, (path, r.status_code)
    print("[ok] Target no registra rutas de Automation (404 en /api/ocr, /compare, /schematics, /automation)")


def main() -> None:
    snapshot()
    print(f"[setup] snapshot en {SNAPSHOT_DIR}")
    try:
        run_checks()
    finally:
        restore()
    print("TARGET API TESTS: PASS")


if __name__ == "__main__":
    main()