import os
import tempfile
import unittest

from suites.common.network_blocklist import (
    load_blocked_hosts,
    is_blocked,
    is_blocked_url,
    make_block_predicate,
)


class TestNetworkBlocklist(unittest.TestCase):

    def test_load_skips_comments_blanks_and_normalizes(self):
        content = "# header comment\n\n  Doubleclick.net  \ncriteo.com   # inline comment\n\n"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            hosts = load_blocked_hosts(path)
        finally:
            os.unlink(path)
        self.assertEqual(hosts, ["doubleclick.net", "criteo.com"])

    def test_is_blocked_matches_exact_and_subdomains(self):
        blocked = ["doubleclick.net", "criteo.com"]
        self.assertTrue(is_blocked("doubleclick.net", blocked))
        self.assertTrue(is_blocked("googleads.g.doubleclick.net", blocked))
        self.assertTrue(is_blocked("gum.criteo.com", blocked))

    def test_is_blocked_rejects_momo_and_lookalikes(self):
        blocked = ["criteo.com"]
        self.assertFalse(is_blocked("www.momoshop.com.tw", blocked))
        self.assertFalse(is_blocked("evilcriteo.com", blocked))      # not a real subdomain
        self.assertFalse(is_blocked("criteo.com.evil.com", blocked))  # suffix spoof

    def test_is_blocked_url_extracts_host(self):
        blocked = ["doubleclick.net"]
        self.assertTrue(is_blocked_url("https://googleads.g.doubleclick.net/pagead?a=1", blocked))
        self.assertFalse(is_blocked_url("https://www.momoshop.com.tw/main/Main.jsp", blocked))

    def test_make_block_predicate_returns_callable(self):
        predicate = make_block_predicate(["taboola.com"])
        self.assertTrue(predicate("https://trc.taboola.com/sync"))
        self.assertFalse(predicate("https://i1.momoshop.com.tw/x.jpg"))

    def test_real_blocklist_has_known_trackers_and_excludes_momo(self):
        hosts = load_blocked_hosts()
        self.assertIn("doubleclick.net", hosts)
        self.assertIn("criteo.com", hosts)
        self.assertIn("taboola.com", hosts)
        self.assertNotIn("momoshop.com.tw", hosts)
        # momo's own hosts must never be considered third-party
        self.assertFalse(is_blocked("apihotsearch.momoshop.com.tw", hosts))
