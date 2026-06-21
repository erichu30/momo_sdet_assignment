"""
Centralized environment-variable key names.

These keys form the contract between the producer (run_tests.py, which resolves
CLI/config.ini overrides and exports them) and the consumers (conftest fixtures
and reporting hooks, which read them at runtime). Keeping the names in one place
prevents silent breakage when a key is renamed on only one side.
"""


class EnvKeys:
    HEADLESS = "MOMO_HEADLESS"
    LOG_LEVEL = "MOMO_LOG_LEVEL"
    REPORT_DIR = "MOMO_REPORT_DIR"
    ENABLE_TRACE = "MOMO_ENABLE_TRACE"
    TEST_CASE_FILTER = "TEST_CASE_FILTER"
    # Playwright Inspector flag (consumed by Playwright itself, not our code)
    PWDEBUG = "PWDEBUG"
