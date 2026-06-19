from pages.base_page import BasePage

class SearchResultsPage(BasePage):
    # Selectors
    HEADER_TITLE = "h1"
    PRODUCT_TITLES = "h3.prdName"
    PRODUCT_PRICES = "span.price"
    SORT_PRICE_TAB = "li.priceHeight"
    PRICE_MIN_INPUT = "input#priceS"
    PRICE_MAX_INPUT = "input#priceE"
    PRICE_FILTER_SUBMIT = "a.priceBtn"
    NO_DATA_CONTAINER = ".nodata, div:has-text('找不到'), div:has-text('查無')"

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
        """
        # TODO: Implement product price parsing
        return []

    def sort_by_price(self):
        """
        Clicks the price sort option tab to sort products.
        """
        # TODO: Implement price sorting action
        pass

    def apply_price_range(self, min_price: int, max_price: int):
        """
        Fills the min and max price inputs and submits the filter.
        """
        # TODO: Implement price bounds input and filter submission
        pass

    def is_no_results_visible(self) -> bool:
        """
        Determines whether the page is displaying the 'No results found' UI.
        """
        # TODO: Implement negative path assertion
        return False
