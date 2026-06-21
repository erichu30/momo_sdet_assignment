import pytest
from utils.test_case_parser import parse_test_cases

def test_parse_single_test_case():
    """Test parsing of single case ID, including automatic zero-padding."""
    assert parse_test_cases("SEARCH-001") == {"SEARCH-001"}
    assert parse_test_cases("SEARCH-1") == {"SEARCH-001"}
    assert parse_test_cases("search-002") == {"SEARCH-002"}

def test_parse_range_test_cases():
    """Test parsing of range expression like SEARCH-{001..003}."""
    assert parse_test_cases("SEARCH-{001..003}") == {"SEARCH-001", "SEARCH-002", "SEARCH-003"}
    assert parse_test_cases("SEARCH-{1..3}") == {"SEARCH-001", "SEARCH-002", "SEARCH-003"}

def test_parse_multiple_mixed():
    """Test parsing of mixed comma-separated values."""
    raw_input = "SEARCH-001, SEARCH-{002..003}, SEARCH-005"
    expected = {"SEARCH-001", "SEARCH-002", "SEARCH-003", "SEARCH-005"}
    assert parse_test_cases(raw_input) == expected
