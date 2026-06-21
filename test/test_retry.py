import unittest
from unittest.mock import patch

from utils.retry import with_retry


class TestWithRetry(unittest.TestCase):

    def test_returns_result_and_logs_zero_retries_on_success(self):
        calls = []

        def action():
            calls.append(1)
            return "ok"

        with self.assertLogs("momo_automation", level="INFO") as cm:
            result = with_retry("demo", action)

        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 1)
        output = "\n".join(cm.output)
        self.assertIn("[PERF] op=demo", output)
        self.assertIn("retries=0", output)

    @patch("utils.retry.time.sleep", return_value=None)
    def test_retries_then_succeeds_and_flags_retry_count(self, _sleep):
        calls = []

        def action():
            calls.append(1)
            if len(calls) < 3:
                raise TimeoutError("throttled")
            return "ok"

        with self.assertLogs("momo_automation", level="INFO") as cm:
            result = with_retry("demo", action, retries=2, retry_on=(TimeoutError,))

        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 3)
        output = "\n".join(cm.output)
        self.assertIn("[RETRY] op=demo", output)   # degradation is observable
        self.assertIn("retries=2", output)         # final PERF line carries the count

    @patch("utils.retry.time.sleep", return_value=None)
    def test_raises_after_exhausting_retries(self, _sleep):
        def action():
            raise TimeoutError("always")

        with self.assertRaises(TimeoutError):
            with_retry("demo", action, retries=1, retry_on=(TimeoutError,))

    @patch("utils.retry.time.sleep", return_value=None)
    def test_does_not_retry_unlisted_exception(self, _sleep):
        calls = []

        def action():
            calls.append(1)
            raise ValueError("not retryable")

        with self.assertRaises(ValueError):
            with_retry("demo", action, retries=2, retry_on=(TimeoutError,))
        self.assertEqual(len(calls), 1)

    @patch("utils.retry.time.sleep", return_value=None)
    def test_throttle_class_errors_use_longer_backoff(self, sleep):
        # Treat ValueError as the throttle class so we can prove the longer-backoff
        # path without depending on Playwright's TimeoutError in a unit test.
        def action():
            raise ValueError("throttled")

        with self.assertRaises(ValueError):
            with_retry(
                "demo", action, retries=2,
                base_delay=1.0, throttle_delay=5.0,
                retry_on=(ValueError,), throttle_on=(ValueError,),
            )
        # Two retries before giving up: throttle backoff = 5, 10 (not 1, 2).
        delays = [call.args[0] for call in sleep.call_args_list]
        self.assertEqual(delays, [5.0, 10.0])

    @patch("utils.retry.time.sleep", return_value=None)
    def test_non_throttle_errors_use_base_backoff(self, sleep):
        # A retryable-but-not-throttle error keeps the short backoff (e.g. dropped input).
        def action():
            raise ValueError("structural")

        with self.assertRaises(ValueError):
            with_retry(
                "demo", action, retries=2,
                base_delay=1.0, throttle_delay=5.0,
                retry_on=(ValueError,), throttle_on=(KeyError,),
            )
        delays = [call.args[0] for call in sleep.call_args_list]
        self.assertEqual(delays, [1.0, 2.0])
