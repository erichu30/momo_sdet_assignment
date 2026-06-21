import re

from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.retry import with_retry

class SearchResultsPage(BasePage):
    # Selectors
    HEADER_TITLE = "h1"
    PRODUCT_CARD = "li.listAreaLi"
    PRODUCT_TITLES = "h3.prdName"
    PRODUCT_PRICES = "span.price"
    # momo seeds the results grid with sponsored (RTB) ad slots — typically the
    # first several cards — that do NOT participate in sorting/filtering. They are
    # marked by this tag and are excluded when we need the organic result order.
    AD_TAG = "ins.tenMaxAdTag, .tenMaxAdTag, .adTag"
    # The sort bar reuses class `priceHeight` for BOTH the 價格(price) and 評價(rating)
    # tabs, so this selector must always be disambiguated by text "價格".
    SORT_PRICE_TAB = "li.priceHeight"
    # Clicking the price tab toggles direction; momo encodes it in the URL:
    #   searchType=2 -> price low→high (asc), tab gains class token "up"
    #   searchType=3 -> price high→low (desc), tab gains class token "down"
    SEARCH_TYPE_ASC = "2"
    SEARCH_TYPE_DESC = "3"
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

    def get_product_prices(self, exclude_ads: bool = False) -> list[int]:
        """
        Extracts product prices as integers, in DOM order.
        Prices render with thousands separators (e.g. "2,699"), so only digits are kept.

        `exclude_ads=True` drops sponsored ad slots (see AD_TAG): these sit at fixed
        positions and ignore sort/filter, so any ordering assertion must skip them.
        Extraction is per-card so the ad flag stays aligned with its own price.
        """
        self.page.locator(self.PRODUCT_PRICES).first.wait_for(state="visible", timeout=10000)
        cards = self.page.eval_on_selector_all(
            self.PRODUCT_CARD,
            """(els, adSel) => els.map(li => {
                const isAd = !!li.querySelector(adSel);
                const priceEl = li.querySelector('span.price');
                return [isAd, priceEl ? priceEl.innerText : null];
            })""",
            self.AD_TAG,
        )
        result = []
        for is_ad, text in cards:
            if (exclude_ads and is_ad) or not text:
                continue
            digits = re.sub(r"[^\d]", "", text)
            if digits:
                result.append(int(digits))
        return result

    def sort_by_price(self, ascending: bool = True):
        """
        Sorts the results by price in the requested direction by clicking the 價格 tab.

        momo toggles direction on each click (default → desc → asc → desc …) and
        reflects the active sort in the URL (searchType=2 asc / =3 desc). We click up
        to a few times until the tab shows the target direction, waiting for the grid
        to reload between clicks so the next read sees the re-sorted list.
        """
        target_token = "up" if ascending else "down"

        def _sort():
            tab = self.page.locator(self.SORT_PRICE_TAB, has_text="價格")
            for _ in range(3):
                if target_token in (tab.get_attribute("class") or ""):
                    return
                tab.click()
                # Each click navigates (searchType=2|3); wait for the reload so the
                # tab's class and the product grid reflect the new sort before re-check.
                self.page.wait_for_url(
                    re.compile(r"searchType=[23]"),
                    wait_until="load", timeout=self.NAVIGATION_TIMEOUT,
                )
            raise AssertionError(
                f"Price sort never reached '{target_token}' direction (ascending={ascending})"
            )

        with_retry(
            "sort_by_price", _sort,
            retry_on=(PlaywrightTimeoutError, AssertionError),
            ascending=ascending,
        )

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
