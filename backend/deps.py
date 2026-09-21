"""Write serialization for the shared_store Excel files.

A single process-level lock is reserved for the write routes added in later
steps (seed, schematic generation, automation apply, demo reset). It lives in
the API layer on purpose: db.py (the business data layer) is left untouched.
"""
from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

_WRITE_LOCK = threading.Lock()


@contextmanager
def write_lock() -> Iterator[None]:
    """Serialize writes to the shared_store workbooks within this process."""
    with _WRITE_LOCK:
        yield