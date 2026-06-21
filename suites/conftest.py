import os
import logging

import pytest
from playwright.sync_api import Page

from utils.logger import logger
from utils.runtime_config import get_runtime_config
from utils.test_case_parser import parse_test_cases
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage

# Reporting fixtures/hooks live in utils.reporting; importing them here lets pytest
# discover them in the conftest namespace while keeping this file thin.
from utils.reporting import test_case_asset_manager, pytest_runtest_makereport  # noqa: F401


# Filter collected tests dynamically by test case ID
def pytest_collection_modifyitems(config, items):
    cfg = get_runtime_config()
    if not cfg.test_case_filter:
        return

    allowed_ids = parse_test_cases(cfg.test_case_filter)
    logger.info(f"Filtering test collection to match Test Case ID(s): {allowed_ids}")

    selected = []
    deselected = []
    for item in items:
        test_id_marker = item.get_closest_marker("test_id")
        if test_id_marker and test_id_marker.args[0].upper() in allowed_ids:
            selected.append(item)
        else:
            deselected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


# Configure logging level dynamically based on the resolved runtime config
def pytest_configure(config):
    cfg = get_runtime_config()
    numeric_level = getattr(logging, cfg.log_level, logging.INFO)

    momo_logger = logging.getLogger("momo_automation")
    momo_logger.setLevel(numeric_level)
    for handler in momo_logger.handlers:
        handler.setLevel(numeric_level)

    # Configure pytest's built-in log capturing levels dynamically
    config.option.log_cli_level = cfg.log_level
    config.option.log_level = cfg.log_level
    logger.info(f"Test Framework Configured: Log level and Pytest capture set to {cfg.log_level}.")


# Dynamically adjust playwright launch arguments based on runtime config
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    cfg = get_runtime_config()
    launch_args = {**browser_type_launch_args, "headless": cfg.headless}

    if cfg.is_debug:
        logger.info("Verbose DEBUG level active: Applying 800ms action slow_mo.")
        launch_args["slow_mo"] = 800

    return launch_args


# Set up browser context arguments to capture video in DEBUG mode
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    cfg = get_runtime_config()
    if not cfg.is_debug:
        return browser_context_args

    import tempfile
    # Use system temp directory for temporary video storage to keep workspace clean
    temp_video_dir = os.path.join(tempfile.gettempdir(), "momo_temp_videos")
    os.makedirs(temp_video_dir, exist_ok=True)
    return {
        **browser_context_args,
        "record_video_dir": temp_video_dir,
        "record_video_size": {"width": 1280, "height": 720},
    }


# Setup Page Object Models
@pytest.fixture
def home_page(page: Page) -> HomePage:
    return HomePage(page)


@pytest.fixture
def search_results_page(page: Page) -> SearchResultsPage:
    return SearchResultsPage(page)
