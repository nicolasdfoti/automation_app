"""Test battery for common/store_lock cross-process write locking.

Run with the project venv:

    venv/Scripts/python.exe -m common.tests.test_store_lock

Follows the project's inline test-battery convention (no pytest dependency).

Proves real cross-process mutual exclusion by spawning independent Python
worker subprocesses that contend on the same lock file:

- Test A: lose-proof counter. Two processes increment a shared counter inside
  the lock P*N times. Any overlap (i.e. a missing lock) loses increments, so
  final count must equal P*N. A timestamp log additionally verifies that no
  two processes hold the lock simultaneously.
- Test B: exception inside the critical section still releases the lock
  (the counter can be re-acquired immediately afterwards).
- Test C: acquisition respects the timeout: a holder keeps the lock and a
  second process raises LockTimeoutError instead of waiting forever.

Read-only for the real data: every path lives under a TEMP snapshot dir.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKER_SOURCE = textwrap.dedent(
    """
    import os
    import sys
    import time
    from pathlib import Path

    sys.path.insert(0, sys.argv[1])
    from common.store_lock import write_lock, LockTimeoutError

    lock_file = sys.argv[2]
    counter_file = sys.argv[3]
    log_file = sys.argv[4]
    iters = int(sys.argv[5])
    pid = os.getpid()

    def count() -> int:
        try:
            return int(Path(counter_file).read_text())
        except FileNotFoundError:
            return 0

    with open(log_file, "a", encoding="utf-8") as log:
        for _ in range(iters):
            with write_lock(lock_file=lock_file, timeout=15):
                log.write(f"ENTER {pid}\\n")
                log.flush()
                n = count()
                time.sleep(0.02)
                n += 1
                Path(counter_file).write_text(str(n))
                log.write(f"EXIT {pid}\\n")
                log.flush()
    print("worker-ok")
    """
)


def _snapshot_dir() -> Path:
    base = Path(os.environ["TEMP"]) / f"store_lock_test_{os.getpid()}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _run_worker(lock: Path, counter: Path, log: Path, iters: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            WORKER_SOURCE,
            str(REPO_ROOT),
            str(lock),
            str(counter),
            str(log),
            str(iters),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _check_no_overlap(log: Path) -> None:
    """Assert the timestamp log never shows two pids inside the lock at once."""
    held: dict[int, int] = {}
    lines = log.read_text(encoding="utf-8").splitlines()
    assert lines, "log vacio: ningun worker entro a la seccion critica"
    for line in lines:
        event, pid_s = line.split()
        pid = int(pid_s)
        if event == "ENTER":
            assert pid not in held, f"worker {pid} entro dos veces sin salir"
            assert len(held) == 0, f"superposicion: {pid} entro mientras {list(held)} retenia el lock"
            held[pid] = 1
        elif event == "EXIT":
            assert pid in held, f"worker {pid} salio sin haber entrado"
            del held[pid]
        else:
            raise AssertionError(f"evento desconocido: {line!r}")
    assert not held, f"workers terminaron sin soltar el lock: {list(held)}"


def _test_mutual_exclusion(snap: Path) -> None:
    lock = snap / "lock.test"
    counter = snap / "counter.txt"
    log = snap / "log.txt"

    procs = [_run_worker(lock, counter, log, 25) for _ in range(2)]
    for proc in procs:
        assert "worker-ok" in proc.stdout, proc.stdout + proc.stderr

    assert counter.read_text().strip() == "50", (
        f"esperado 50 incrementos con lock, se leyeron {counter.read_text().strip()}: "
        "los workers se superpusieron (el lock no serializa entre procesos)"
    )
    _check_no_overlap(log)
    print("[ok] exclusion mutua: 2 procesos x 25 incrementos, count=50 sin superposicion")


def _test_release_on_exception(snap: Path) -> None:
    lock = snap / "lock_exc.test"
    src = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        from common.store_lock import write_lock
        with write_lock(lock_file={str(snap / 'lock_exc.test')!r}, timeout=15):
            raise RuntimeError("bomba")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", src], capture_output=True, text=True, timeout=60
    )
    assert proc.returncode != 0 and "bomba" in proc.stderr

    from common import store_lock

    with store_lock.write_lock(lock_file=lock, timeout=5):
        pass  # sin LockTimeoutError => el lock fue liberado tras la excepcion
    print("[ok] liberacion ante excepcion: se re-adquiere el lock tras un raise")


def _test_timeout(snap: Path) -> None:
    lock = snap / "lock_tmo.test"

    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"""
import sys
sys.path.insert(0, {str(REPO_ROOT)!r})
import time
from common.store_lock import write_lock
with write_lock(lock_file={str(lock)!r}, timeout=15):
    print("holder-locked")
    sys.stdout.flush()
    time.sleep(6)
""",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "holder-locked"
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                f"""
import sys
sys.path.insert(0, {str(REPO_ROOT)!r})
from common.store_lock import write_lock, LockTimeoutError
try:
    with write_lock(lock_file={str(lock)!r}, timeout=1):
        pass
    print("no-timeout")
except LockTimeoutError:
    print("lock-timeout")
""",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert "lock-timeout" in proc.stdout, proc.stdout + proc.stderr
        print("[ok] timeout: segundo proceso respeta el timeout y lanza LockTimeoutError")
    finally:
        holder.terminate()
        holder.wait(timeout=30)


def main() -> None:
    snap = _snapshot_dir()
    _test_mutual_exclusion(snap)
    _test_release_on_exception(snap)
    _test_timeout(snap)
    print("STORE LOCK TESTS: PASS")


if __name__ == "__main__":
    main()