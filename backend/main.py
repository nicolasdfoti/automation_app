"""Automation Suite API entrypoint.

Serves the future React frontend through /api/*. Business logic lives in the
existing modules (shared_store, pdf_creator, pipeline_app); this app only
wraps them.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import properties as properties_router
from backend.routers import schematics as schematics_router
from backend.routers import compare as compare_router
from backend.routers import stats as stats_router
from backend.routers import ocr as ocr_router

app = FastAPI(title="Automation Suite API", version="0.1.0")

# Development CORS for the future React app (Vite dev server).
# Production (Step 12) will serve the built SPA from this same process,
# making CORS unnecessary there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(properties_router.router, prefix="/api")
app.include_router(schematics_router.router, prefix="/api")
app.include_router(ocr_router.router, prefix="/api")
app.include_router(compare_router.router, prefix="/api")
app.include_router(stats_router.router, prefix="/api")
