import pytest
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage


class TestMomoSearch:

    @pytest.mark.rat
    @pytest.mark.test_id("SEARCH-001")
    def test_happy_path_search(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 1: Happy Path Search

        [Specifications]
        - ID: SEARCH-001
        - Input: Product search keyword (e.g., "iPhone")
        - Output: Search results page for the keyword
        - Testing Level: Release Acceptance Testing (RAT smoke - core search works)
        - Expected Result: Search header reflects the keyword and at least one product is returned.

        Note: this smoke deliberately asserts only the stable search *contract* (the query ran
        and produced results). Result *relevance/ordering* is momo's ranking output — it shifts
        daily with promotions and sponsored slots, so asserting it here would be flaky. Ordering
        is covered separately by the deterministic price-sort test (SEARCH-005).
        """
        keyword = "iPhone"
        home_page.navigate()
        home_page.search_for(keyword)

        header = search_results_page.get_search_header_text()
        assert keyword.lower() in header.lower(), \
            f"Search header should reflect '{keyword}', got: {header!r}"

        titles = search_results_page.get_product_titles()
        assert len(titles) > 0, "Search should return at least one product"

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

        # 2. Verify suggestions dropdown is visible
        assert home_page.wait_for_suggestions(), \
            "Suggestions dropdown should be visible after typing keyword"

        # 3. Retrieve suggestion texts and assert list is populated (count > 0)
        suggestions = home_page.get_suggestions()
        assert len(suggestions) > 0, "Expected suggestions dropdown to have options, got 0"

        # 4. Click the first suggestion (navigation is awaited inside the POM)
        selected_suggestion = suggestions[0]
        home_page.click_suggestion_by_index(0)

        # 5. Verify redirection landed on results matching the selected suggestion
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
        gibberish = "xyz999abc_not_exist"
        home_page.navigate()
        home_page.search_for(gibberish)
        
        # Verify empty state elements or message is visible
        assert search_results_page.is_no_results_visible(), \
            "Expected 'No results found' placeholder or indicator to be visible"
        
        # Verify product count is 0
        product_count = search_results_page.get_product_count()
        assert product_count == 0, f"Expected 0 product items, but found {product_count}"

    @pytest.mark.toft
    @pytest.mark.test_id("SEARCH-005")
    def test_sort_by_price_ascending_and_descending(self, home_page: HomePage, search_results_page: SearchResultsPage):
        """
        Scenario 5: Sort by Price (ascending and descending)

        [Specifications]
        - ID: SEARCH-005
        - Input: Product keyword ("行動電源"), price sort toggled low→high then high→low
        - Output: Re-ordered product grid for each direction
        - Testing Level: Testing Of Functionality and Toleration (TOFT)
        - Expected Result: Organic (non-sponsored) product prices are non-decreasing when
                           sorted ascending, and non-increasing when sorted descending.

        Sponsored ad slots sit at fixed positions and ignore the sort, so we compare only
        organic prices (exclude_ads=True). Verifying BOTH directions proves the control
        actually re-sorts rather than coincidentally matching one order.
        """
        keyword = "行動電源"
        home_page.navigate()
        home_page.search_for(keyword)

        # Ascending: price low -> high
        search_results_page.sort_by_price(ascending=True)
        asc_prices = search_results_page.get_product_prices(exclude_ads=True)
        assert len(asc_prices) > 1, "Need at least two organic products to verify ordering"
        assert asc_prices == sorted(asc_prices), \
            f"Ascending sort: prices should be non-decreasing, got: {asc_prices}"

        # Descending: price high -> low
        search_results_page.sort_by_price(ascending=False)
        desc_prices = search_results_page.get_product_prices(exclude_ads=True)
        assert len(desc_prices) > 1, "Need at least two organic products to verify ordering"
        assert desc_prices == sorted(desc_prices, reverse=True), \
            f"Descending sort: prices should be non-increasing, got: {desc_prices}"
