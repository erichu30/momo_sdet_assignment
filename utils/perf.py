"""
Lightweight performance instrumentation.

Wrap a timed operation with `measure(...)` to emit one greppable, machine-parseable
`[PERF]` log line carrying the operation name, its duration in milliseconds, and any
extra context. Grep `[PERF]` across the per-case logs under results/ (or the global
results/test_run.log) to build a performance matrix for observation and extended tests.

`log_perf(...)` is the shared formatter, also reused by utils.retry so retried
operations report their `retries=` count in the same format.

Example line:
    [PERF] op=navigate duration_ms=712 retries=0 url=https://www.momoshop.com.tw/
"""
import time
from contextlib import contextmanager

from utils.logger import logger


def log_perf(op: str, duration_ms: float, **fields):
    """Emits a single [PERF] line: op, duration_ms, then any extra key=value fields."""
    extra = "".join(f" {key}={value}" for key, value in fields.items())
    logger.info(f"[PERF] op={op} duration_ms={duration_ms:.0f}{extra}")


@contextmanager
def measure(op: str, **context):
    """Times the wrapped block and logs a [PERF] line (even if the block raises)."""
    start = time.perf_counter()
    try:
        yield
    finally:
        log_perf(op, (time.perf_counter() - start) * 1000, **context)
