import time
from playwright.sync_api import Page, Locator, expect
from utils.logger import logger

class BasePage:
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
        popup_close_selectors = [
            "#momoPopupClose", 
            "#moPromoClose", 
            "a.close", 
            "button.close", 
            "div.closeBtn",
            "#closeBtn",
            ".pop-close",
            "#close_pop"
        ]
        
        # Give a split second for popups to render
        self.page.wait_for_timeout(1000)
        
        for selector in popup_close_selectors:
            try:
                locator = self.page.locator(selector).first
                if locator.is_visible(timeout=500):
                    logger.info(f"Detected overlay popup: Clicking {selector} to dismiss.")
                    locator.click()
                    self.page.wait_for_timeout(500)
            except Exception as e:
                # We want popup dismissal to be non-blocking
                logger.debug(f"Popup check failed for selector {selector}: {str(e)}")

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

    def take_screenshot(self, name: str):
        path = f"test-results/{name}_{int(time.time())}.png"
        self.page.screenshot(path=path)
        logger.info(f"Saved screenshot to {path}")
        return path
