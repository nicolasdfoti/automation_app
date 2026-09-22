"""Comparison endpoints — translate compute_comparison, never duplicate it."""
from __future__ import annotations

from fastapi import APIRouter

from automation_system.backend.schemas import CompareResponse
from automation_system.backend.services.compare_api import compare_summary

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("", response_model=CompareResponse)
def compare() -> CompareResponse:
    return CompareResponse(**compare_summary())