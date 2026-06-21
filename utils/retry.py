"""
Shared retry-with-backoff helper for throttling-prone operations.

momo rate-limits automated traffic, so navigation/search/filter actions can
intermittently time out. `with_retry` re-runs an action with exponential backoff
and makes the cost visible: every call emits a `[PERF]` line carrying `retries=N`
(N>0 means the op only succeeded after retrying, i.e. degraded performance), and
each retry also emits a `[RETRY]` warning. Grep `retries=` to spot degraded runs.
"""
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.logger import logger
from utils.perf import log_perf


def with_retry(
    op, action, *, retries=2, base_delay=1.0, throttle_delay=5.0,
    retry_on=(Exception,), throttle_on=(PlaywrightTimeoutError,), **context,
):
    """
    Runs `action` (a zero-arg callable), retrying on `retry_on` exceptions with
    exponential backoff. Returns the action's result. Re-raises the final exception
    after exhausting retries. Exceptions outside `retry_on` propagate immediately.

    Backoff is exception-aware: throttle-class errors (`throttle_on`, default Playwright
    TimeoutError) back off from the longer `throttle_delay` because momo's rate-limit
    window lasts seconds — a 1s nudge just gets throttled again. Other retryable errors
    (e.g. a dropped-input AssertionError) back off from the shorter `base_delay` since
    they clear on an immediate re-try. Both grow exponentially (delay, 2x, 4x, ...).
    """
    start = time.perf_counter()
    attempt = 0
    while True:
        try:
            result = action()
            log_perf(op, (time.perf_counter() - start) * 1000, retries=attempt, **context)
            return result
        except retry_on as exc:
            if attempt >= retries:
                log_perf(
                    op, (time.perf_counter() - start) * 1000,
                    retries=attempt, status="failed", **context,
                )
                raise
            is_throttle = isinstance(exc, throttle_on)
            current_base = throttle_delay if is_throttle else base_delay
            delay = current_base * (2 ** attempt)
            logger.warning(
                f"[RETRY] op={op} attempt={attempt + 1}/{retries} "
                f"delay_s={delay:.1f} reason={type(exc).__name__}"
                f"{' kind=throttle' if is_throttle else ''}"
            )
            time.sleep(delay)
            attempt += 1
