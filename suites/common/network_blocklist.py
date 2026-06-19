"""
Shared third-party network blocklist for E2E suites.

Loads a list of registrable hosts (see blocked_hosts.txt) and exposes helpers to
decide whether a request URL belongs to a blocked third party. Any test suite can
reuse this; pages.BasePage.block_requests() consumes the predicate built here.
"""
import os
from typing import Callable, List
from urllib.parse import urlparse

DEFAULT_BLOCKLIST_PATH = os.path.join(os.path.dirname(__file__), "blocked_hosts.txt")


def load_blocked_hosts(path: str = DEFAULT_BLOCKLIST_PATH) -> List[str]:
    """Parses the blocklist file, skipping comments/blanks and normalizing case."""
    hosts: List[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            # Strip inline comments and surrounding whitespace.
            entry = line.split("#", 1)[0].strip().lower()
            if entry:
                hosts.append(entry)
    return hosts


def is_blocked(host: str, blocked_hosts) -> bool:
    """True if host equals a blocked domain or is a subdomain of one."""
    host = (host or "").lower()
    return any(host == b or host.endswith("." + b) for b in blocked_hosts)


def is_blocked_url(url: str, blocked_hosts) -> bool:
    """True if the URL's host is blocked."""
    return is_blocked(urlparse(url).hostname or "", blocked_hosts)


def make_block_predicate(blocked_hosts) -> Callable[[str], bool]:
    """Returns a predicate `url -> bool` suitable for BasePage.block_requests()."""
    return lambda url: is_blocked_url(url, blocked_hosts)
