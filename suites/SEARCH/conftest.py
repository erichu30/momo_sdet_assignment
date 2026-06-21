import os

import pytest

from pages.base_page import BasePage
from suites.common.network_blocklist import (
    DEFAULT_BLOCKLIST_PATH,
    load_blocked_hosts,
    make_block_predicate,
)
from utils.logger import logger


@pytest.fixture(autouse=True)
def block_third_party_requests(page):
    """
    Drop non-momo analytics/ads/tracking traffic for every SEARCH test so the
    suite focuses on momo's own search flow. The route is registered before the
    test body navigates, so it applies to all subsequent requests on the page.
    """
    blocked_hosts = load_blocked_hosts()
    BasePage(page).block_requests(make_block_predicate(blocked_hosts))
    logger.info(
        f"Applied 3rd-party networking filter: blocking {len(blocked_hosts)} hosts "
        f"(refer to {os.path.relpath(DEFAULT_BLOCKLIST_PATH)})"
    )
    yield
