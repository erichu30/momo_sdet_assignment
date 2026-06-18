import os
import re
import time
import shutil
import pytest
import logging
from playwright.sync_api import Page, BrowserContext
from utils.logger import logger
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage

# Helper to parse test case selections (e.g. SEARCH-001, SEARCH-{001..003})
def parse_test_cases(raw_input: str) -> set[str]:
    """
    Parses test case selection patterns like SEARCH-001, SEARCH-{001..003}
    and returns a normalized set of string IDs (e.g. {'SEARCH-001', 'SEARCH-002', 'SEARCH-003'}).
    """
    ids = set()
    parts = re.split(r',(?![^{]*})', raw_input)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        range_match = re.match(r'^([A-Z0-9_]+)-\{(\d+)\.\.(\d+)\}$', part, re.IGNORECASE)
        if range_match:
            prefix = range_match.group(1).upper()
            start = int(range_match.group(2))
            end = int(range_match.group(3))
            raw_start_str = range_match.group(2)
            pad_len = len(raw_start_str) if len(raw_start_str) > 1 else 3
            
            for i in range(min(start, end), max(start, end) + 1):
                ids.add(f"{prefix}-{i:0{pad_len}d}")
        else:
            single_match = re.match(r'^([A-Z0-9_]+)-(\d+)$', part, re.IGNORECASE)
            if single_match:
                prefix = single_match.group(1).upper()
                num_str = single_match.group(2)
                pad_len = max(3, len(num_str))
                normalized_num = f"{int(num_str):0{pad_len}d}"
                ids.add(f"{prefix}-{normalized_num}")
            else:
                ids.add(part.upper())
            
    return ids

# Register custom command-line options
def pytest_addoption(parser):
    pass

# Filter collected tests dynamically by test case ID
def pytest_collection_modifyitems(config, items):
    test_cases_env = os.environ.get("TEST_CASE_FILTER")
    if test_cases_env:
        allowed_ids = parse_test_cases(test_cases_env)
        logger.info(f"Filtering test collection to match Test Case ID(s): {allowed_ids}")
        
        selected = []
        deselected = []
        
        for item in items:
            test_id_marker = item.get_closest_marker("test_id")
            if test_id_marker:
                test_id = test_id_marker.args[0].upper()
                if test_id in allowed_ids:
                    selected.append(item)
                    continue
            deselected.append(item)
            
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected

# Configure logging level dynamically based on MOMO_LOG_LEVEL env variable
def pytest_configure(config):
    log_level_env = os.environ.get("MOMO_LOG_LEVEL", "INFO").upper()
    
    # Configure custom logger level
    momo_logger = logging.getLogger("momo_automation")
    numeric_level = getattr(logging, log_level_env, logging.INFO)
    momo_logger.setLevel(numeric_level)
    for handler in momo_logger.handlers:
        handler.setLevel(numeric_level)
    
    # Configure pytest's built-in log capturing levels dynamically
    config.option.log_cli_level = log_level_env
    config.option.log_level = log_level_env
    logger.info(f"Test Framework Configured: Log level and Pytest capture set to {log_level_env}.")

# Dynamically adjust playwright launch arguments based on environment configurations
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    headless_env = os.environ.get("MOMO_HEADLESS", "true").lower() == "true"
    log_level_env = os.environ.get("MOMO_LOG_LEVEL", "INFO").upper()
    
    launch_args = {**browser_type_launch_args, "headless": headless_env}
    
    if log_level_env == "DEBUG":
        logger.info("Verbose DEBUG level active: Applying 800ms action slow_mo.")
        launch_args["slow_mo"] = 800
        
    return launch_args

# Set up browser context arguments to capture video in DEBUG mode
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    log_level_env = os.environ.get("MOMO_LOG_LEVEL", "INFO").upper()
    if log_level_env == "DEBUG":
        import tempfile
        # Use system temp directory for temporary video storage to keep workspace clean
        temp_dir = tempfile.gettempdir()
        temp_video_dir = os.path.join(temp_dir, "momo_temp_videos")
        os.makedirs(temp_video_dir, exist_ok=True)
        return {
            **browser_context_args,
            "record_video_dir": temp_video_dir,
            "record_video_size": {"width": 1280, "height": 720}
        }
    return browser_context_args

# Runtime Test Case Asset and Folder Manager
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
        
    test_case_id = test_id_marker.args[0].upper()
    test_suite = test_case_id.split("-")[0]
    
    # Resolve the runtime test case directory: results/<SUITE>/<ID>
    base_report_dir = os.environ.get("MOMO_REPORT_DIR", os.path.abspath("./results"))
    test_case_dir = os.path.join(base_report_dir, test_suite, test_case_id)
    os.makedirs(test_case_dir, exist_ok=True)
    
    # Expose path details to pytest item properties for access in hooks
    request.node.user_properties.append(("test_case_dir", test_case_dir))
    request.node.user_properties.append(("test_case_id", test_case_id))
    
    log_level_env = os.environ.get("MOMO_LOG_LEVEL", "INFO").upper()
    
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
    enable_trace_env = os.environ.get("MOMO_ENABLE_TRACE", "true").lower() == "true"
    if enable_trace_env:
        momo_logger.debug(f"[{test_case_id}] Starting Playwright execution trace.")
        page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
    yield
    
    # Post-test execution asset sorting
    if enable_trace_env:
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

# Setup Page Object Models
@pytest.fixture
def home_page(page: Page) -> HomePage:
    return HomePage(page)

@pytest.fixture
def search_results_page(page: Page) -> SearchResultsPage:
    return SearchResultsPage(page)

# Hook into Pytest Report generation to embed screenshots, videos, logs and traces
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    # We embed report info during the call phase
    if rep.when == "call":
        extra = getattr(rep, "extra", [])
        
        # Read target properties set by test_case_asset_manager
        test_case_dir = None
        test_case_id = None
        for prop in item.user_properties:
            if prop[0] == "test_case_dir":
                test_case_dir = prop[1]
            elif prop[0] == "test_case_id":
                test_case_id = prop[1]
                
        if test_case_dir and test_case_id:
            test_suite = test_case_id.split("-")[0]
            
            # 1. Capture and embed screenshot on failure
            if rep.failed:
                if "page" in item.funcargs:
                    page = item.funcargs["page"]
                    screenshot_name = "failure.png"
                    screenshot_path = os.path.join(test_case_dir, screenshot_name)
                    try:
                        # Capture screenshot to target folder
                        page.screenshot(path=screenshot_path)
                        
                        # Generate path relative to report HTML at results/pytest_html_report.html
                        relative_path = f"{test_suite}/{test_case_id}/{screenshot_name}"
                        
                        from pytest_html import extras
                        extra.append(extras.image(relative_path, name="Failure Screenshot"))
                        logger.error(f"[{test_case_id}] Test FAILED! Screenshot linked in report: {relative_path}")
                    except Exception as e:
                        logger.error(f"Failed to take screenshot on test failure: {e}")
            
            # 2. Embed URLs for videos and traces
            enable_trace_env = os.environ.get("MOMO_ENABLE_TRACE", "true").lower() == "true"
            log_level_env = os.environ.get("MOMO_LOG_LEVEL", "INFO").upper()
            from pytest_html import extras
            
            if enable_trace_env:
                relative_trace = f"{test_suite}/{test_case_id}/trace.zip"
                extra.append(extras.url(relative_trace, name="Execution Trace (.zip)"))
                logger.info(f"[{test_case_id}] Linked trace ({relative_trace}) in HTML report.")
                
            if log_level_env == "DEBUG":
                relative_video = f"{test_suite}/{test_case_id}/video.webm"
                extra.append(extras.url(relative_video, name="Execution Video (.webm)"))
                logger.info(f"[{test_case_id}] Linked video ({relative_video}) in HTML report.")
                
            # 3. Always embed URL for the individual test log file
            from pytest_html import extras
            relative_log = f"{test_suite}/{test_case_id}/test.log"
            extra.append(extras.url(relative_log, name="Execution Log (.log)"))
            
        rep.extra = extra
