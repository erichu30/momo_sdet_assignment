import os
import unittest

from utils.env_keys import EnvKeys
from utils.runtime_config import get_runtime_config


class TestRuntimeConfig(unittest.TestCase):

    def setUp(self):
        # Cache and clear the contract env vars to avoid cross-test pollution
        self.original_env = dict(os.environ)
        for key in (
            EnvKeys.HEADLESS,
            EnvKeys.LOG_LEVEL,
            EnvKeys.REPORT_DIR,
            EnvKeys.ENABLE_TRACE,
            EnvKeys.TEST_CASE_FILTER,
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_defaults_when_env_missing(self):
        """get_runtime_config returns sane defaults when nothing is exported."""
        cfg = get_runtime_config()
        self.assertTrue(cfg.headless)
        self.assertEqual(cfg.log_level, "INFO")
        self.assertEqual(cfg.report_dir, os.path.abspath("./results"))
        self.assertTrue(cfg.enable_trace)
        self.assertIsNone(cfg.test_case_filter)
        self.assertFalse(cfg.is_debug)

    def test_parses_exported_env_values(self):
        """Env values are parsed into the correct typed fields."""
        os.environ[EnvKeys.HEADLESS] = "false"
        os.environ[EnvKeys.LOG_LEVEL] = "debug"  # lower-case should be normalized
        os.environ[EnvKeys.REPORT_DIR] = "/tmp/momo_out"
        os.environ[EnvKeys.ENABLE_TRACE] = "false"
        os.environ[EnvKeys.TEST_CASE_FILTER] = "SEARCH-001"

        cfg = get_runtime_config()
        self.assertFalse(cfg.headless)
        self.assertEqual(cfg.log_level, "DEBUG")
        self.assertTrue(cfg.is_debug)
        self.assertEqual(cfg.report_dir, "/tmp/momo_out")
        self.assertFalse(cfg.enable_trace)
        self.assertEqual(cfg.test_case_filter, "SEARCH-001")

    def test_producer_consumer_roundtrip(self):
        """
        The producer (run_tests.resolve_configurations) and the consumer
        (get_runtime_config) agree because they share EnvKeys constants.
        """
        from run_tests import build_parser, resolve_configurations

        defaults = {
            "headless": True,
            "log_level": "INFO",
            "report_dir": "./results",
            "pwdebug": False,
            "trace": True,
        }
        args = build_parser().parse_args(["--headed", "-l", "DEBUG", "--no-trace"])
        resolve_configurations(args, defaults)

        cfg = get_runtime_config()
        self.assertFalse(cfg.headless)
        self.assertEqual(cfg.log_level, "DEBUG")
        self.assertTrue(cfg.is_debug)
        self.assertFalse(cfg.enable_trace)
