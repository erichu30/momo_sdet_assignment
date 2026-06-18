#!/usr/bin/env python3
import argparse
import configparser
import os
import re
import sys
import pytest

CONFIG_FILE = "config.ini"
PYTEST_INI = "pytest.ini"

def load_config() -> dict:
    """
    Loads default configuration settings from config.ini.
    Returns fallback defaults if config.ini is missing or corrupted.
    """
    defaults = {
        "headless": True,
        "log_level": "INFO",
        "report_path": "./results",
        "pwdebug": False,
        "trace": True
    }
    if os.path.exists(CONFIG_FILE):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE, encoding="utf-8")
            if "momo_automation" in config:
                sec = config["momo_automation"]
                if "headless" in sec:
                    defaults["headless"] = sec.getboolean("headless")
                if "log_level" in sec:
                    defaults["log_level"] = sec.get("log_level").upper()
                if "report_path" in sec:
                    defaults["report_path"] = sec.get("report_path")
                if "pwdebug" in sec:
                    defaults["pwdebug"] = sec.getboolean("pwdebug")
                if "trace" in sec:
                    defaults["trace"] = sec.getboolean("trace")
        except Exception as e:
            print(f"Warning: Failed to read {CONFIG_FILE}, using fallback defaults. Error: {e}")
    return defaults

def get_report_filename_from_pytest_ini() -> str:
    """
    Parses pytest.ini's addopts to extract the configured HTML report filename.
    Returns a fallback filename if parsing fails or option is missing.
    """
    fallback_filename = "pytest_html_report.html"
    if os.path.exists(PYTEST_INI):
        try:
            config = configparser.ConfigParser()
            config.read(PYTEST_INI, encoding="utf-8")
            if "pytest" in config and "addopts" in config["pytest"]:
                addopts = config["pytest"]["addopts"]
                match = re.search(r'--html=([^\s]+)', addopts)
                if match:
                    filename = match.group(1).strip()
                    return filename
        except Exception as e:
            print(f"Warning: Failed to parse {PYTEST_INI} for report filename: {e}")
    return fallback_filename

def main():
    defaults = load_config()

    parser = argparse.ArgumentParser(
        description="momo Web Automation Testing CLI Framework"
    )
    
    # CLI Overrides
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="Run tests in headless mode (overrides config.ini default)"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        default=None,
        help="Run tests in headed mode (overrides config.ini default)"
    )
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default=None,
        help="Set execution log level (overrides config.ini default)"
    )
    parser.add_argument(
        "--report", "-r",
        type=str,
        default=None,
        help="Output directory path for the HTML test report (overrides config.ini default)"
    )
    parser.add_argument(
        "--pwdebug",
        action="store_true",
        default=None,
        help="Enable Playwright Inspector interactive debugging GUI"
    )
    parser.add_argument(
        "--no-pwdebug",
        action="store_true",
        default=None,
        help="Disable Playwright Inspector interactive debugging GUI"
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        default=None,
        help="Enable Playwright execution trace capturing (.zip) (overrides config.ini default)"
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        default=None,
        help="Disable Playwright execution trace capturing (.zip) (overrides config.ini default)"
    )
    parser.add_argument(
        "--tier", "-t",
        type=str,
        help="Filter execution by testing level markers (comma-separated, e.g. RAT,FAST)"
    )
    parser.add_argument(
        "--test-case", "-c",
        nargs="+",
        action="append",
        help="Filter execution by specific Test Case IDs (e.g. SEARCH-001, SEARCH-{001..003})"
    )
    parser.add_argument(
        "test_targets",
        nargs="*",
        default=["suites/"],
        help="Optional test paths or specific test cases to execute (default: suites/)"
    )

    args = parser.parse_args()

    # Determine final configurations (CLI overrides config.ini defaults)
    final_headless = defaults["headless"]
    if args.headless is not None:
        final_headless = True
    elif args.headed is not None:
        final_headless = False

    final_log_level = args.log_level if args.log_level is not None else defaults["log_level"]
    
    # Resolve directory path
    report_dir = args.report if args.report is not None else defaults["report_path"]
    abs_report_dir = os.path.abspath(report_dir)
    
    # Automatically create output directory if missing
    os.makedirs(abs_report_dir, exist_ok=True)
    
    # Extract filename from pytest.ini and combine
    report_filename = get_report_filename_from_pytest_ini()
    final_report_path = os.path.join(abs_report_dir, report_filename)

    # Determine PWDEBUG activation
    final_pwdebug = defaults["pwdebug"]
    if args.pwdebug is not None:
        final_pwdebug = True
    elif args.no_pwdebug is not None:
        final_pwdebug = False

    # Determine Playwright trace activation
    final_trace = defaults["trace"]
    if args.trace is not None:
        final_trace = True
    elif args.no_trace is not None:
        final_trace = False

    # Export configuration to environment variables for conftest.py
    os.environ["MOMO_HEADLESS"] = "true" if final_headless else "false"
    os.environ["MOMO_LOG_LEVEL"] = final_log_level
    os.environ["MOMO_REPORT_DIR"] = abs_report_dir
    os.environ["MOMO_ENABLE_TRACE"] = "true" if final_trace else "false"
    
    if final_pwdebug:
        os.environ["PWDEBUG"] = "1"
        # Playwright Inspector requires headed browser mode to display
        os.environ["MOMO_HEADLESS"] = "false"
        final_headless = False

    # Base pytest arguments (overriding pytest.ini's local html path dynamically)
    pytest_args = [
        "-v",
        "-s",
        f"--html={final_report_path}",
        "--self-contained-html"
    ]

    # Handle testing level filtering (--tier)
    if args.tier:
        tiers = [t.strip().lower() for t in args.tier.split(",") if t.strip()]
        if tiers:
            marker_expr = " or ".join(tiers)
            pytest_args.extend(["-m", marker_expr])

    # Handle specific Test Case ID filtering (--test-case)
    if args.test_case:
        flattened_tcs = []
        for item in args.test_case:
            if isinstance(item, list):
                flattened_tcs.extend(item)
            else:
                flattened_tcs.append(item)
        os.environ["TEST_CASE_FILTER"] = ",".join(flattened_tcs)

    # Add targeted tests / directories
    pytest_args.extend(args.test_targets)

    # Output run configuration overview
    print(f"Launching Momo Web Automation Framework...")
    print(f"  Headless: {final_headless} (CLI override)" if (args.headless or args.headed) else f"  Headless: {final_headless} (default from config.ini)")
    print(f"  Log Level: {final_log_level} (CLI override)" if args.log_level else f"  Log Level: {final_log_level} (default from config.ini)")
    print(f"  Report Path: {final_report_path} (resolved from report_dir='{report_dir}' & pytest.ini filename='{report_filename}')")
    print(f"  Playwright Inspector (PWDEBUG): {final_pwdebug} (CLI override)" if (args.pwdebug or args.no_pwdebug) else f"  Playwright Inspector (PWDEBUG): {final_pwdebug} (default from config.ini)")
    print(f"  Playwright Trace: {final_trace} (CLI override)" if (args.trace or args.no_trace) else f"  Playwright Trace: {final_trace} (default from config.ini)")
    print(f"  Command parameters: {pytest_args}\n")

    # Run pytest programmatically
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
