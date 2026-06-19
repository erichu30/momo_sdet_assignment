import re

from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.retry import with_retry

class SearchResultsPage(BasePage):
    # Selectors
    HEADER_TITLE = "h1"
    PRODUCT_TITLES = "h3.prdName"
    PRODUCT_PRICES = "span.price"
    SORT_PRICE_TAB = "li.priceHeight"
    PRICE_MIN_INPUT = "input#priceS"
    PRICE_MAX_INPUT = "input#priceE"
    PRICE_FILTER_SUBMIT = "a.priceBtn"
    # momo's empty-state message, e.g. 很抱歉，查無 "..." 的相關商品。Matched by text
    # (not a wrapper-div :has-text) to avoid false positives elsewhere on the page.
    NO_RESULTS_PATTERN = re.compile(r"查無.*相關商品")

    def get_search_header_text(self) -> str:
        """
        Returns the main header/title text of the search results page.
        """
        return self.get_text(self.HEADER_TITLE)

    def get_product_titles(self) -> list[str]:
        """
        Extracts titles of all visible product cards in the results page.
        """
        titles = self.page.locator(self.PRODUCT_TITLES)
        titles.first.wait_for(state="visible", timeout=10000)
        return [t.strip() for t in titles.all_inner_texts()]

    def get_product_prices(self) -> list[int]:
        """
        Extracts prices of all visible products and returns them as a list of integers.
        Prices render with thousands separators (e.g. "2,699"), so only digits are kept.
        """
        prices = self.page.locator(self.PRODUCT_PRICES)
        prices.first.wait_for(state="visible", timeout=10000)
        result = []
        for text in prices.all_inner_texts():
            digits = re.sub(r"[^\d]", "", text)
            if digits:
                result.append(int(digits))
        return result

    def sort_by_price(self):
        """
        Clicks the price sort option tab to sort products.
        """
        # TODO: Implement price sorting action
        pass

    def apply_price_range(self, min_price: int, max_price: int):
        """
        Fills the min and max price inputs and submits the filter, reloading results.
        """
        def _apply():
            self.fill_input(self.PRICE_MIN_INPUT, str(min_price), name="min price")
            self.fill_input(self.PRICE_MAX_INPUT, str(max_price), name="max price")
            # momo re-renders the filter sidebar; confirm the values actually stuck
            # before submitting, else an empty filter is sent (no _advPriceS applied).
            # A dropped value raises AssertionError, which triggers a retry (re-fill).
            expect(self.page.locator(self.PRICE_MIN_INPUT)).to_have_value(str(min_price))
            expect(self.page.locator(self.PRICE_MAX_INPUT)).to_have_value(str(max_price))
            self.click_element(self.PRICE_FILTER_SUBMIT, name="price filter submit")
            # Wait until the URL actually reflects the applied price filter, so callers
            # read the filtered list rather than the stale (already-loaded) unfiltered page.
            self.page.wait_for_url(
                re.compile(r"_advPriceS="), wait_until="load", timeout=self.NAVIGATION_TIMEOUT
            )

        with_retry(
            "apply_price_range", _apply,
            retry_on=(PlaywrightTimeoutError, AssertionError),
            min=min_price, max=max_price,
        )

    def is_no_results_visible(self) -> bool:
        """
        Determines whether the page is displaying the 'No results found' UI by
        matching momo's specific empty-state message (查無 ... 相關商品).
        """
        locator = self.page.get_by_text(self.NO_RESULTS_PATTERN)
        try:
            locator.first.wait_for(state="visible", timeout=5000)
            return True
        except Exception:
            return False

    def get_product_count(self) -> int:
        """Returns the number of product cards currently rendered on the page."""
        return self.page.locator(self.PRODUCT_TITLES).count()
