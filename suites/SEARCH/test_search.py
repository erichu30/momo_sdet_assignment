import time

import pytest
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage

# Smoke-level budget for homepage accessibility (spec: "under 3-5 seconds").
MAX_HOMEPAGE_LOAD_SECONDS = 5.0

# Of the first 5 results, how many must mention the keyword to count as "relevant".
# Tolerant of the odd sponsored/cross-sell slot while still proving search relevance.
MIN_RELEVANT_OF_FIRST_FIVE = 4


class TestMomoSearch:

    @pytest.mark.rat
    @pytest.mark.test_id("SEARCH-000")
    def test_homepage_accessibility(self, home_page: HomePage):
        """
        Scenario 0: Release Acceptance Testing (RAT)

        [Specifications]
        - ID: SEARCH-000
        - Input: None (Navigate to homepage)
        - Output: Homepage loaded successfully
        - Testing Level: Release Acceptance Testing (Smoke Test)
        - Expected Result: Homepage is accessible, page loads successfully in under 3-5 seconds,
                           and the browser title contains "momo".
        """
        start = time.time()
        home_page.navigate()
        load_seconds = time.time() - start

        title = home_page.page.title()
        assert "momo" in title.lower(), \
            f"Homepage title should contain 'momo', got: {title!r}"
        assert load_seconds < MAX_HOMEPAGE_LOAD_SECONDS, \
            f"Homepage should load within {MAX_HOMEPAGE_LOAD_SECONDS}s, took {load_seconds:.2f}s"

    @pytest.mark.fast
    @pytest.mark.test_id("SEARCH-001")
    def test_happy_path_search(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 1: Happy Path Search
        
        [Specifications]
        - ID: SEARCH-001
        - Input: Product search keyword (e.g., "iPhone")
        - Output: List of search results matching the keyword
        - Testing Level: Core UX Happy Path Testing (FAST)
        - Expected Result: Search header reflects keyword, product count > 0, first 5 product titles are relevant.
        """
        keyword = "iPhone"
        home_page.navigate()
        home_page.search_for(keyword)

        header = search_results_page.get_search_header_text()
        assert keyword.lower() in header.lower(), \
            f"Search header should reflect '{keyword}', got: {header!r}"

        titles = search_results_page.get_product_titles()
        assert len(titles) > 0, "Search should return at least one product"

        first_five = titles[:5]
        relevant = [t for t in first_five if keyword.lower() in t.lower()]
        assert len(relevant) >= MIN_RELEVANT_OF_FIRST_FIVE, \
            f"Expected >= {MIN_RELEVANT_OF_FIRST_FIVE} of first 5 titles to mention '{keyword}', got: {first_five}"

    @pytest.mark.toft
    @pytest.mark.test_id("SEARCH-002")
    def test_advanced_price_range_filtering(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 2: Advanced Price Range Filtering
        
        [Specifications]
        - ID: SEARCH-002
        - Input: Product keyword ("咖啡機") and Price range [2000, 5000]
        - Output: Price-filtered search results
        - Testing Level: Testing Of Functionality and Toleration (TOFT)
        - Expected Result: Every product displayed on the results page has a price within [2000, 5000].
        """
        keyword = "咖啡機"
        min_price, max_price = 2000, 5000
        home_page.navigate()
        home_page.search_for(keyword)
        search_results_page.apply_price_range(min_price, max_price)

        prices = search_results_page.get_product_prices()
        assert len(prices) > 0, "Filtered search should return at least one product"
        out_of_range = [p for p in prices if not (min_price <= p <= max_price)]
        assert not out_of_range, \
            f"All prices must be within [{min_price}, {max_price}], out-of-range: {out_of_range}"

    @pytest.mark.fast
    @pytest.mark.test_id("SEARCH-003")
    def test_search_autocomplete_suggestions(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 3: Autocomplete Suggestions
        
        [Specifications]
        - ID: SEARCH-003
        - Input: Partial keyword text input (e.g., "iPhone")
        - Output: Dropdown recommendation keyword suggestions list
        - Testing Level: Core UX Happy Path Testing (FAST)
        - Expected Result: Suggestions dropdown becomes visible, suggestion list is not empty, 
                           clicking a suggestion redirects to results page containing the selected keyword.
        """
        keyword = "iPhone"
        home_page.navigate()
        
        # 1. Type partial keyword to trigger suggestions
        home_page.type_keyword_for_suggestions(keyword)
        
        # 2. Verify suggestions dropdown container is visible
        suggestion_locator = home_page.page.locator(home_page.SUGGESTION_CONTAINER)
        suggestion_locator.wait_for(state="visible", timeout=5000)
        assert suggestion_locator.is_visible(), "Suggestions dropdown container should be visible after typing keyword"
        
        # 3. Retrieve suggestion texts and assert list is populated (count > 0)
        suggestions = home_page.get_suggestions()
        assert len(suggestions) > 0, f"Expected suggestions dropdown to have options, got 0"
        
        # 4. Click the first suggestion item
        selected_suggestion = suggestions[0]
        home_page.click_suggestion_by_index(0)
        
        # 5. Verify redirection and successful results load for the selected suggestion
        search_results_page.page.wait_for_load_state("load")
        header_text = search_results_page.get_search_header_text()
        assert selected_suggestion.lower() in header_text.lower(), \
            f"Expected search header to match suggestion '{selected_suggestion}', got: '{header_text}'"

    @pytest.mark.fet
    @pytest.mark.test_id("SEARCH-004")
    def test_negative_no_results(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 4: Negative Path - No Search Results
        
        [Specifications]
        - ID: SEARCH-004
        - Input: Gibberish keyword that doesn't exist (e.g., "xyz999abc_not_exist")
        - Output: No-results layout/placeholder view
        - Testing Level: Functional Edge Testing (FET)
        - Expected Result: System displays 'No results found' message, product list has 0 items.
        """
        # TODO: Implement Scenario 4
        pass
