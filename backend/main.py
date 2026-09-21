"""Automation Suite API entrypoint.

Serves the future React frontend through /api/*. Business logic lives in the
existing modules (shared_store, pdf_creator, pipeline_app); this app only
wraps them.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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