import os
import unittest
from run_tests import build_parser, resolve_configurations

class TestCLIAndOverrides(unittest.TestCase):
    
    def setUp(self):
        # Cache environment variables to prevent test pollution
        self.original_env = dict(os.environ)
        self.default_configs = {
            "headless": True,
            "log_level": "INFO",
            "report_path": "./results",
            "pwdebug": False,
            "trace": True
        }

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_cli_parser_defaults(self):
        """Test that the parser defaults are None or expected fallbacks for override detection."""
        parser = build_parser()
        args = parser.parse_args([])
        
        self.assertIsNone(args.headless)
        self.assertIsNone(args.headed)
        self.assertIsNone(args.log_level)
        self.assertIsNone(args.report)
        self.assertIsNone(args.pwdebug)
        self.assertIsNone(args.no_pwdebug)
        self.assertIsNone(args.trace)
        self.assertIsNone(args.no_trace)
        self.assertIsNone(args.tier)
        self.assertIsNone(args.test_case)
        self.assertEqual(args.test_targets, ["suites/"])

    def test_cli_headless_overrides(self):
        """Test CLI --headed and --headless flags override config.ini settings."""
        parser = build_parser()
        
        # Test --headed overrides headless=True default
        args = parser.parse_args(["--headed"])
        resolved = resolve_configurations(args, self.default_configs)
        self.assertFalse(resolved["headless"])
        self.assertEqual(os.environ["MOMO_HEADLESS"], "false")

        # Test --headless overrides headless=False default
        custom_defaults = dict(self.default_configs, headless=False)
        args = parser.parse_args(["--headless"])
        resolved = resolve_configurations(args, custom_defaults)
        self.assertTrue(resolved["headless"])
        self.assertEqual(os.environ["MOMO_HEADLESS"], "true")

    def test_cli_log_level_overrides(self):
        """Test CLI --log-level / -l overrides config.ini settings."""
        parser = build_parser()
        args = parser.parse_args(["-l", "DEBUG"])
        resolved = resolve_configurations(args, self.default_configs)
        self.assertEqual(resolved["log_level"], "DEBUG")
        self.assertEqual(os.environ["MOMO_LOG_LEVEL"], "DEBUG")

    def test_cli_report_overrides(self):
        """Test CLI --report / -r overrides config.ini settings."""
        parser = build_parser()
        args = parser.parse_args(["-r", "./my_output"])
        resolved = resolve_configurations(args, self.default_configs)
        self.assertEqual(resolved["report_dir"], "./my_output")
        self.assertEqual(os.environ["MOMO_REPORT_DIR"], os.path.abspath("./my_output"))
        self.assertTrue(resolved["report_path"].endswith("pytest_html_report.html"))

    def test_cli_pwdebug_override_side_effects(self):
        """Test CLI --pwdebug overrides defaults, sets PWDEBUG=1, and forces headed mode (headless=False)."""
        parser = build_parser()
        args = parser.parse_args(["--pwdebug"])
        resolved = resolve_configurations(args, self.default_configs)
        
        self.assertTrue(resolved["pwdebug"])
        self.assertFalse(resolved["headless"])  # Forced headed
        self.assertEqual(os.environ["PWDEBUG"], "1")
        self.assertEqual(os.environ["MOMO_HEADLESS"], "false")

    def test_cli_trace_overrides(self):
        """Test CLI --trace and --no-trace flags override config.ini settings."""
        parser = build_parser()
        
        # Test --no-trace overrides trace=True default
        args = parser.parse_args(["--no-trace"])
        resolved = resolve_configurations(args, self.default_configs)
        self.assertFalse(resolved["trace"])
        self.assertEqual(os.environ["MOMO_ENABLE_TRACE"], "false")

        # Test --trace overrides trace=False default
        custom_defaults = dict(self.default_configs, trace=False)
        args = parser.parse_args(["--trace"])
        resolved = resolve_configurations(args, custom_defaults)
        self.assertTrue(resolved["trace"])
        self.assertEqual(os.environ["MOMO_ENABLE_TRACE"], "true")

    def test_cli_tier_filtering_pytest_args(self):
        """Test CLI --tier / -t appends correct -m expression to pytest arguments."""
        parser = build_parser()
        
        args = parser.parse_args(["-t", "RAT,FAST"])
        resolved = resolve_configurations(args, self.default_configs)
        pytest_args = resolved["pytest_args"]
        
        self.assertIn("-m", pytest_args)
        self.assertIn("rat or fast", pytest_args)

    def test_cli_test_case_filtering_env(self):
        """Test CLI --test-case / -c sets correct TEST_CASE_FILTER environment variable."""
        parser = build_parser()
        
        # Test case filtering: single or multiple (args.test_case is accumulated as nested list)
        args = parser.parse_args(["-c", "SEARCH-001", "-c", "SEARCH-{002..003}"])
        resolved = resolve_configurations(args, self.default_configs)
        
        self.assertIn("TEST_CASE_FILTER", os.environ)
        self.assertEqual(os.environ["TEST_CASE_FILTER"], "SEARCH-001,SEARCH-{002..003}")
