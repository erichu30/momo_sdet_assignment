import os
import unittest
from unittest.mock import patch, mock_open
from run_tests import load_config, get_report_filename_from_pytest_ini

class TestConfigLoader(unittest.TestCase):
    
    @patch("os.path.exists")
    def test_load_config_missing_file(self, mock_exists):
        """Test load_config when config.ini is missing - should return default fallback values."""
        mock_exists.return_value = False
        configs = load_config()
        
        self.assertTrue(configs["headless"])
        self.assertEqual(configs["log_level"], "INFO")
        self.assertEqual(configs["report_dir"], "./results")
        self.assertTrue(configs["trace"])
        self.assertFalse(configs["pwdebug"])

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
[momo_automation]
headless = false
log_level = DEBUG
report_dir = ./custom_results
pwdebug = true
trace = false
""")
    def test_load_config_with_valid_file(self, mock_file, mock_exists):
        """Test load_config when config.ini exists - should correctly parse configuration settings."""
        mock_exists.return_value = True
        configs = load_config()

        self.assertFalse(configs["headless"])
        self.assertEqual(configs["log_level"], "DEBUG")
        self.assertEqual(configs["report_dir"], "./custom_results")
        self.assertFalse(configs["trace"])
        self.assertTrue(configs["pwdebug"])

    @patch("os.path.exists")
    def test_get_report_filename_missing_pytest_ini(self, mock_exists):
        """Test get_report_filename_from_pytest_ini when pytest.ini is missing - should return fallback name."""
        mock_exists.return_value = False
        filename = get_report_filename_from_pytest_ini()
        self.assertEqual(filename, "pytest_html_report.html")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
[pytest]
addopts = --html=my_custom_report.html --self-contained-html -v -s
""")
    def test_get_report_filename_valid_pytest_ini(self, mock_file, mock_exists):
        """Test get_report_filename_from_pytest_ini when pytest.ini exists - should parse addopts and extract --html path."""
        mock_exists.return_value = True
        filename = get_report_filename_from_pytest_ini()
        self.assertEqual(filename, "my_custom_report.html")
