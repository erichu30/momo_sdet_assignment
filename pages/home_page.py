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
        # TODO: Implement navigation
        pass

    def search_for(self, keyword: str):
        """
        Fills keyword into search bar and clicks search.
        """
        # TODO: Implement search execution
        pass

    def type_keyword_for_suggestions(self, keyword: str):
        """
        Inputs partial keyword to trigger the autocomplete suggestion box.
        """
        # TODO: Implement autocomplete trigger
        pass

    def get_suggestions(self) -> list[str]:
        """
        Retrieves the visible autocomplete suggestions from the dropdown list.
        """
        # TODO: Implement suggestions text retrieval
        return []

    def click_suggestion_by_index(self, index: int):
        """
        Clicks suggestion item at the specified index.
        """
        # TODO: Implement suggestion click action
        pass
