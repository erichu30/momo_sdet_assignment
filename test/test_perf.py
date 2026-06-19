import unittest

from utils.perf import measure


class TestMeasure(unittest.TestCase):

    def test_emits_perf_line_with_op_duration_and_context(self):
        with self.assertLogs("momo_automation", level="INFO") as cm:
            with measure("demo_op", keyword="iPhone"):
                pass
        output = "\n".join(cm.output)
        self.assertIn("[PERF] op=demo_op", output)
        self.assertIn("duration_ms=", output)
        self.assertIn("keyword=iPhone", output)

    def test_logs_even_when_block_raises(self):
        with self.assertLogs("momo_automation", level="INFO") as cm:
            with self.assertRaises(ValueError):
                with measure("boom"):
                    raise ValueError("intentional")
        self.assertIn("[PERF] op=boom", "\n".join(cm.output))
