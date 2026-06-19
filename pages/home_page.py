from pages.base_page import BasePage

class HomePage(BasePage):
    # Selectors
    SEARCH_INPUT = 'input[name="search-input"]'
    SEARCH_BUTTON = 'button:has-text("搜尋")'
    SUGGESTION_CONTAINER = 'div[class*="mu-z-dropdown"]'
    SUGGESTION_ITEMS = 'div[class*="mu-z-dropdown"] button'

    def __init__(self, page):
        super().__init__(page)
        self.url = "https://www.momoshop.com.tw/"

    def navigate(self):
        """
        Navigates to the momo homepage.
        """
        self.navigate_to(self.url)

    def search_for(self, keyword: str):
        """
        Fills keyword into search bar and clicks search, landing on the results page.
        """
        self.fill_input(self.SEARCH_INPUT, keyword, name="search box")
        self.click_element(self.SEARCH_BUTTON, name="search button")
        self.page.wait_for_load_state("load")

    def type_keyword_for_suggestions(self, keyword: str):
        """
        Inputs partial keyword to trigger the autocomplete suggestion box.
        """
        locator = self.page.locator(self.SEARCH_INPUT)
        locator.wait_for(state="visible", timeout=10000)
        locator.click()
        locator.clear()
        locator.press_sequentially(keyword, delay=100)

    def get_suggestions(self) -> list[str]:
        """
        Retrieves the visible autocomplete suggestions from the dropdown list.
        """
        locator = self.page.locator(self.SUGGESTION_ITEMS)
        # Wait for at least the first item to become visible before querying
        locator.first.wait_for(state="visible", timeout=5000)
        return [text.strip() for text in locator.all_inner_texts() if text.strip()]

    def click_suggestion_by_index(self, index: int):
        """
        Clicks suggestion item at the specified index.
        """
        locator = self.page.locator(self.SUGGESTION_ITEMS).nth(index)
        locator.wait_for(state="visible", timeout=5000)
        locator.click()
