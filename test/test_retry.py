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
