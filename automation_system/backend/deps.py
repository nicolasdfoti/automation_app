"""Write serialization for the shared_store Excel files.

A cross-process write lock reserves the write routes (seed, schematic
generation, automation apply, demo reset) so that concurrent writes to the
same workbooks are serialized even across processes. The lock lives in the
API layer on purpose: db.py (the business data layer) is left untouched.
"""
from __future__ import annotations

from common.store_lock import LockTimeoutError, write_lock

__all__ = ["write_lock", "LockTimeoutError"]