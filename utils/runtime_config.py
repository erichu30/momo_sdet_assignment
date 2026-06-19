"""
Typed runtime configuration accessor.

Collapses the repeated, stringly-typed `os.environ.get(...).upper()` parsing that
was previously scattered across conftest into a single source of truth. Each
fixture/hook calls `get_runtime_config()` fresh, so the returned snapshot always
reflects the current environment exported by run_tests.py.
"""
import os
from dataclasses import dataclass
from typing import Optional

from utils.env_keys import EnvKeys


@dataclass(frozen=True)
class RuntimeConfig:
    headless: bool
    log_level: str
    report_dir: str
    enable_trace: bool
    test_case_filter: Optional[str]

    @property
    def is_debug(self) -> bool:
        return self.log_level == "DEBUG"


def get_runtime_config() -> RuntimeConfig:
    """Reads a fresh snapshot of runtime config from the environment."""
    return RuntimeConfig(
        headless=os.environ.get(EnvKeys.HEADLESS, "true").lower() == "true",
        log_level=os.environ.get(EnvKeys.LOG_LEVEL, "INFO").upper(),
        report_dir=os.environ.get(EnvKeys.REPORT_DIR, os.path.abspath("./results")),
        enable_trace=os.environ.get(EnvKeys.ENABLE_TRACE, "true").lower() == "true",
        test_case_filter=os.environ.get(EnvKeys.TEST_CASE_FILTER),
    )
