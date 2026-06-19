"""
Pytest reporting plugin: per-test-case asset management and HTML report embedding.

These fixtures/hooks are imported into suites/conftest.py so pytest discovers them
in the conftest namespace, keeping conftest itself thin. All runtime decisions are
driven by the typed RuntimeConfig snapshot rather than raw env lookups.
"""
import os
import time
import shutil
import logging

import pytest
from pytest_html import extras
from playwright.sync_api import Page

from utils.logger import logger
from utils.runtime_config import get_runtime_config


@pytest.fixture(autouse=True)
def test_case_asset_manager(page: Page, request):
    """
    Autouse fixture that creates test suite-specific directories at runtime
    and moves traces/videos to structured output paths for pytest HTML report linking.
    Also dynamically sets up case-specific log files under the output directory.
    """
    test_id_marker = request.node.get_closest_marker("test_id")
    if not test_id_marker:
        yield
        return

    cfg = get_runtime_config()
    test_case_id = test_id_marker.args[0].upper()
    test_suite = test_case_id.split("-")[0]

    # Resolve the runtime test case directory: results/<SUITE>/<ID>
    test_case_dir = os.path.join(cfg.report_dir, test_suite, test_case_id)
    os.makedirs(test_case_dir, exist_ok=True)

    # Expose path details to pytest item properties for access in hooks
    request.node.user_properties.append(("test_case_dir", test_case_dir))
    request.node.user_properties.append(("test_case_id", test_case_id))

    # Set up case-specific log file handler
    case_log_path = os.path.join(test_case_dir, "test.log")
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    case_file_handler = logging.FileHandler(case_log_path, encoding="utf-8")
    case_file_handler.setFormatter(formatter)

    momo_logger = logging.getLogger("momo_automation")
    case_file_handler.setLevel(momo_logger.level)
    momo_logger.addHandler(case_file_handler)

    momo_logger.info(f"=== Starting Test Case: {test_case_id} ===")

    # Start tracing if trace is enabled
    if cfg.enable_trace:
        momo_logger.debug(f"[{test_case_id}] Starting Playwright execution trace.")
        page.context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield

    # Post-test execution asset sorting
    if cfg.enable_trace:
        # 1. Stop and save tracing zip
        trace_path = os.path.join(test_case_dir, "trace.zip")
        try:
            page.context.tracing.stop(path=trace_path)
            momo_logger.info(f"[{test_case_id}] Saved trace file to: {trace_path}")
        except Exception as e:
            momo_logger.debug(f"Failed to save Playwright trace: {e}")

        # 2. Flush and move video file
        try:
            # Closing the page flushes the video file to disk
            video = page.video
            page.close()
            if video:
                video_src = video.path()
                video_dest = os.path.join(test_case_dir, "video.webm")
                # Wait up to 2 seconds for video file compilation to complete
                for _ in range(20):
                    if os.path.exists(video_src):
                        shutil.copy(video_src, video_dest)
                        momo_logger.info(f"[{test_case_id}] Moved video recording to: {video_dest}")
                        break
                    time.sleep(0.1)
        except Exception as e:
            momo_logger.debug(f"Failed to move video recording: {e}")

    momo_logger.info(f"=== Finished Test Case: {test_case_id} ===")
    try:
        momo_logger.removeHandler(case_file_handler)
        case_file_handler.close()
    except Exception as e:
        momo_logger.debug(f"Failed to cleanup case file handler: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Embeds screenshots, traces, videos and logs into the pytest HTML report."""
    outcome = yield
    rep = outcome.get_result()

    # We embed report info during the call phase
    if rep.when != "call":
        return

    # Read target properties set by test_case_asset_manager
    test_case_dir = None
    test_case_id = None
    for prop in item.user_properties:
        if prop[0] == "test_case_dir":
            test_case_dir = prop[1]
        elif prop[0] == "test_case_id":
            test_case_id = prop[1]

    if not (test_case_dir and test_case_id):
        return

    cfg = get_runtime_config()
    test_suite = test_case_id.split("-")[0]
    extra = getattr(rep, "extra", [])

    # 1. Capture and embed screenshot on failure
    if rep.failed and "page" in item.funcargs:
        page = item.funcargs["page"]
        screenshot_name = "failure.png"
        screenshot_path = os.path.join(test_case_dir, screenshot_name)
        try:
            page.screenshot(path=screenshot_path)
            # Path relative to the report HTML at results/pytest_html_report.html
            relative_path = f"{test_suite}/{test_case_id}/{screenshot_name}"
            extra.append(extras.image(relative_path, name="Failure Screenshot"))
            logger.error(f"[{test_case_id}] Test FAILED! Screenshot linked in report: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot on test failure: {e}")

    # 2. Embed URLs for traces and videos
    if cfg.enable_trace:
        relative_trace = f"{test_suite}/{test_case_id}/trace.zip"
        extra.append(extras.url(relative_trace, name="Execution Trace (.zip)"))
        logger.info(f"[{test_case_id}] Linked trace ({relative_trace}) in HTML report.")

    if cfg.is_debug:
        relative_video = f"{test_suite}/{test_case_id}/video.webm"
        extra.append(extras.url(relative_video, name="Execution Video (.webm)"))
        logger.info(f"[{test_case_id}] Linked video ({relative_video}) in HTML report.")

    # 3. Always embed URL for the individual test log file
    relative_log = f"{test_suite}/{test_case_id}/test.log"
    extra.append(extras.url(relative_log, name="Execution Log (.log)"))

    rep.extra = extra
