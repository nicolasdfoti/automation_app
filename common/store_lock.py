"""Cross-process write lock for the shared Excel data files.

Why this exists
---------------
Today ``backend/deps.py`` serializes writes with a ``threading.Lock``, which is
only valid within a single process. Once the suite is split into two FastAPI
processes (Target System + Automation System) that both write the same Excel
workbooks, that guarantee disappears. This module provides a bidirectional
(cross-process) lock that neither app owns: the Target app and the Automation
app both use it, so concurrent writes to the same workbook are serialized.

Mechanism (documented decision)
-------------------------------
- Lock target: one small sidecar file next to the store, so every process
  that manipulates the same Excel data agrees on the same lock path
  (configurable via ``STORE_LOCK_FILE`` for tests/CI).
- Windows (this repo: ``os.name == 'nt'``, Windows Python via WSL interop):
  ``msvcrt.locking`` on a 1-byte range of the sidecar file. Cross-process by
  design and auto-released when the handle closes or the process exits.
- POSIX fallback: ``fcntl.flock`` (same guarantees).
- A process-local ``threading.Lock`` additionally serializes threads inside
  the same process (file locks alone behave per-process on some platforms).

Safety guarantees
-----------------
- Lock acquisition is non-blocking with a bounded retry loop and timeout; it
  raises ``LockTimeoutError`` instead of spinning forever.
- Release happens in ``finally``: an exception inside the critical section
  still releases the lock.
- No stale locks survive normal exceptions: the OS releases the byte-range
  lock implicitly when the file descriptor is closed (or process dies).
  The sidecar file itself is intentionally kept (never deleted while locked);
  deleting it would be racy.
"""
from __future__ import annotations

import os
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

if os.name == "nt":  # pragma: no cover - platform branch exercised by CI
    import msvcrt
else:  # pragma: no cover - POSIX fallback
    import fcntl

# Sidecar lock file lives next to the Excel store so both apps resolve the
# same path regardless of their own module layout.
DEFAULT_LOCK_FILE = Path(__file__).resolve().parent.parent / "shared_store" / ".write_lock"

# Number of non-blocking attempts per second and the overall timeout.
ACQUIRE_INTERVAL = 0.05
ACQUIRE_TIMEOUT = 30.0

# Process-local guard: serializes threads within this process on top of the
# cross-process file lock.
_PROCESS_LOCK = threading.Lock()


class LockTimeoutError(TimeoutError):
    """Raised when the cross-process lock could not be acquired in time."""


def _lock_path() -> Path:
    override = os.environ.get("STORE_LOCK_FILE")
    return Path(override) if override else DEFAULT_LOCK_FILE


def _acquire_file_lock(handle: int) -> None:
    if os.name == "nt":  # pragma: no cover - exercised in Windows env
        os.lseek(handle, 0, os.SEEK_SET)
        msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
    else:  # pragma: no cover - POSIX fallback
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _release_file_lock(handle: int) -> None:
    if os.name == "nt":  # pragma: no cover - exercised in Windows env
        os.lseek(handle, 0, os.SEEK_SET)
        msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
    else:  # pragma: no cover - POSIX fallback
        fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def write_lock(
    lock_file: str | Path | None = None,
    timeout: float = ACQUIRE_TIMEOUT,
) -> Iterator[None]:
    """Serialize writes to the shared Excel workbooks across processes.

    The default ``lock_file`` is the sidecar next to the store; tests may pass
    an explicit path to keep genuine data untouched. The lock is released in
    ``finally`` (also on exceptions) and implicitly on process exit.
    """
    path = Path(lock_file) if lock_file is not None else _lock_path()
    with _PROCESS_LOCK:
        # Open (create if needed) a binary handle and ensure it has at least
        # one byte so msvcrt.locking has a range to lock.
        handle = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o666)
        try:
            os.lseek(handle, 0, os.SEEK_END)
            if os.fstat(handle).st_size == 0:
                os.write(handle, b"\x00")
            os.lseek(handle, 0, os.SEEK_SET)
        except OSError:
            os.close(handle)
            raise

        deadline = time.monotonic() + timeout
        try:
            while True:
                try:
                    _acquire_file_lock(handle)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise LockTimeoutError(
                            f"No se pudo adquirir el lock de escritura ({path}) en {timeout:.1f}s"
                        ) from None
                    time.sleep(ACQUIRE_INTERVAL)
            try:
                yield
            finally:
                try:
                    _release_file_lock(handle)
                finally:
                    os.close(handle)
        except LockTimeoutError:
            os.close(handle)
            raise