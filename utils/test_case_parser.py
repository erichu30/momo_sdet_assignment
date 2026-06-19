"""Parsing of Test Case ID selection patterns used by the --test-case CLI filter."""
import re


def parse_test_cases(raw_input: str) -> set[str]:
    """
    Parses test case selection patterns like SEARCH-001, SEARCH-{001..003}
    and returns a normalized set of string IDs (e.g. {'SEARCH-001', 'SEARCH-002', 'SEARCH-003'}).
    """
    ids = set()
    parts = re.split(r',(?![^{]*})', raw_input)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        range_match = re.match(r'^([A-Z0-9_]+)-\{(\d+)\.\.(\d+)\}$', part, re.IGNORECASE)
        if range_match:
            prefix = range_match.group(1).upper()
            start = int(range_match.group(2))
            end = int(range_match.group(3))
            raw_start_str = range_match.group(2)
            pad_len = len(raw_start_str) if len(raw_start_str) > 1 else 3

            for i in range(min(start, end), max(start, end) + 1):
                ids.add(f"{prefix}-{i:0{pad_len}d}")
        else:
            single_match = re.match(r'^([A-Z0-9_]+)-(\d+)$', part, re.IGNORECASE)
            if single_match:
                prefix = single_match.group(1).upper()
                num_str = single_match.group(2)
                pad_len = max(3, len(num_str))
                normalized_num = f"{int(num_str):0{pad_len}d}"
                ids.add(f"{prefix}-{normalized_num}")
            else:
                ids.add(part.upper())

    return ids
