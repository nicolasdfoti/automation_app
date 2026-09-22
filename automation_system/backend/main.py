"""Automation System API entrypoint.

Serves the Automation React frontend (Vite :5174) through /api/*. Business
logic lives in ``automation_system/backend/services/*`` (which reads the
shared_store files), ``pdf_creator`` and ``pipeline_app``. Target-owned
property access happens over HTTP to the Target System API (:8000) — this
app never imports ``target_system.backend.*``.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from automation_system.backend.routers import schematics as schematics_router
from automation_system.backend.routers import ocr as ocr_router
from automation_system.backend.routers import compare as compare_router
from automation_system.backend.routers import automation as automation_router

app = FastAPI(title="Automation System API", version="0.1.0")

# Development CORS for the Automation React app (Vite dev server :5174).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(schematics_router.router, prefix="/api")
app.include_router(ocr_router.router, prefix="/api")
app.include_router(compare_router.router, prefix="/api")
app.include_router(automation_router.router, prefix="/api")