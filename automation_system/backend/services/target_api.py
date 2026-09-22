"""HTTP client for the Target System API (default :8000).

Automation never imports ``target_system.backend.*``; target-owned property
reads go through this client over HTTP. A 404 maps to ``None``; transport
failures and unexpected status codes raise ``TargetApiError`` so callers can
fail loudly instead of guessing.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import httpx

# Base URL of the Target System API, overridable for other environments.
TARGET_API_BASE = os.environ.get("TARGET_API_BASE_URL", "http://127.0.0.1:8000")


class TargetApiError(RuntimeError):
    """Unexpected target response (non-404 error, no connection, etc.)."""


def get_property(codigo: str) -> dict | None:
    """Fetch one property from the Target System API.

    Returns the property dict, or ``None`` when it does not exist (404).
    """
    encoded = quote(str(codigo), safe="")
    url = f"{TARGET_API_BASE}/api/properties/{encoded}"
    try:
        resp = httpx.get(url, timeout=15.0)
    except httpx.HTTPError as exc:
        raise TargetApiError(
            f"Target API inalcanzable en {TARGET_API_BASE}: {exc}"
        ) from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise TargetApiError(
            f"Target API respondio {resp.status_code} para /api/properties/{codigo}: "
            f"{resp.text[:200]}"
        )
    return resp.json()