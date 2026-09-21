"""Read-only dashboard statistics, reusing the SIGE dashboard service."""
from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import Stats
from backend.services.dashboard import compute_dashboard_stats
from shared_store import db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=Stats)
def read_stats() -> Stats:
    stats = compute_dashboard_stats(db.read_properties())
    return Stats(**stats)