"""Write serialization for the shared_store Excel files (Target System).

Guards the write routes (property updates) with the shared cross-process lock
so concurrent writes to the same workbooks are serialized across processes.
"""
from __future__ import annotations

from common.store_lock import LockTimeoutError, write_lock

__all__ = ["write_lock", "LockTimeoutError"]