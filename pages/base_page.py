import os
import time
from playwright.sync_api import Page, Locator, expect
from utils.logger import logger
from utils.runtime_config import get_runtime_config

class BasePage:
    # momo shows dynamic promotional overlays; these are the known close controls.
    POPUP_CLOSE_SELECTORS = [
        "#momoPopupClose",
        "#moPromoClose",
        "a.close",
        "button.close",
        "div.closeBtn",
        "#closeBtn",
        ".pop-close",
        "#close_pop",
    ]
    # How long to wait for any overlay to appear before assuming none will.
    POPUP_APPEAR_TIMEOUT = 2000

    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, url: str):
        logger.info(f"Navigating to {url}")
        self.page.goto(url)
        self.page.wait_for_load_state("load")
        self.dismiss_popups()

    def dismiss_popups(self):
        """
        Attempts to find and close typical momo promotional overlay popups.
        Since momo displays dynamic popups, this method tries multiple selectors.
        If no popups are found, it skips gracefully without throwing.
        """
        # Wait once (web-first) for any candidate overlay to appear; bail fast if none do.
        combined = self.page.locator(", ".join(self.POPUP_CLOSE_SELECTORS)).first
        try:
            combined.wait_for(state="visible", timeout=self.POPUP_APPEAR_TIMEOUT)
        except Exception:
            logger.debug("No overlay popup detected; continuing.")
            return

        # Dismiss every currently-visible overlay, waiting for each to detach
        # instead of sleeping a fixed amount of time.
        for selector in self.POPUP_CLOSE_SELECTORS:
            locator = self.page.locator(selector).first
            try:
                if not locator.is_visible():
                    continue
                logger.info(f"Detected overlay popup: dismissing {selector}.")
                locator.click()
                locator.wait_for(state="hidden", timeout=3000)
            except Exception as e:
                # We want popup dismissal to be non-blocking
                logger.debug(f"Popup dismissal skipped for selector {selector}: {e}")

    def click_element(self, selector: str, name: str = "element"):
        logger.info(f"Clicking on {name} ({selector})")
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=10000)
        locator.click()

    def fill_input(self, selector: str, text: str, name: str = "input"):
        logger.info(f"Filling {name} ({selector}) with '{text}'")
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=10000)
        locator.fill(text)

    def get_text(self, selector: str) -> str:
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=10000)
        return locator.inner_text().strip()

    def take_screenshot(self, name: str) -> str:
        # Keep manual screenshots under the same report directory as all other
        # run assets (resolved from MOMO_REPORT_DIR), and ensure it exists.
        screenshot_dir = os.path.join(get_runtime_config().report_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"{name}_{int(time.time())}.png")
        self.page.screenshot(path=path)
        logger.info(f"Saved screenshot to {path}")
        return path
