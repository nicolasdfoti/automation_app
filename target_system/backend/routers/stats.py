"""Read-only dashboard statistics (Target System)."""
from __future__ import annotations

from fastapi import APIRouter

from target_system.backend.schemas import Stats
from target_system.backend.services.dashboard import compute_dashboard_stats
from shared_store import db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=Stats)
def read_stats() -> Stats:
    stats = compute_dashboard_stats(db.read_properties())
    return Stats(**stats)