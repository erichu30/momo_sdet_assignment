"""
Lightweight performance instrumentation.

Wrap a timed operation with `measure(...)` to emit one greppable, machine-parseable
`[PERF]` log line carrying the operation name, its duration in milliseconds, and any
extra context. Grep `[PERF]` across the per-case logs under results/ (or the global
results/test_run.log) to build a performance matrix for observation and extended tests.

Example line:
    [PERF] op=navigate duration_ms=712 url=https://www.momoshop.com.tw/
"""
import time
from contextlib import contextmanager

from utils.logger import logger


@contextmanager
def measure(op: str, **context):
    """Times the wrapped block and logs a [PERF] line (even if the block raises)."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        extra = "".join(f" {key}={value}" for key, value in context.items())
        logger.info(f"[PERF] op={op} duration_ms={duration_ms:.0f}{extra}")
