"""Target System API entrypoint.

Independent FastAPI application owning the property-management API
(Dashboard, Properties, Property Detail). It shares the Excel store via
``shared_store`` and the cross-process lock via ``common.store_lock``, but
contains no Automation routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from target_system.backend.routers import properties as properties_router
from target_system.backend.routers import stats as stats_router

app = FastAPI(title="Target System API", version="0.1.0")

# Development CORS: only the Target frontend (Vite dev server) is allowed.
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
app.include_router(stats_router.router, prefix="/api")