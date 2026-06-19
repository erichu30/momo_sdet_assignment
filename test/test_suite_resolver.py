import os
import shutil
import tempfile
import unittest

from run_tests import resolve_suite_targets


class TestResolveSuiteTargets(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.suites = os.path.join(self.tmp, "suites")
        for d in ("SEARCH", "CART", "common", "__pycache__"):
            os.makedirs(os.path.join(self.suites, d))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_resolves_single_suite_to_its_directory(self):
        self.assertEqual(
            resolve_suite_targets("SEARCH", self.suites),
            [os.path.join(self.suites, "SEARCH")],
        )

    def test_is_case_insensitive(self):
        self.assertEqual(
            resolve_suite_targets("search", self.suites),
            [os.path.join(self.suites, "SEARCH")],
        )

    def test_resolves_multiple_comma_separated(self):
        self.assertEqual(
            resolve_suite_targets("SEARCH, CART", self.suites),
            [os.path.join(self.suites, "SEARCH"), os.path.join(self.suites, "CART")],
        )

    def test_unknown_suite_raises_with_available_list(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_suite_targets("BOGUS", self.suites)
        msg = str(ctx.exception)
        self.assertIn("BOGUS", msg)
        self.assertIn("SEARCH", msg)
        self.assertIn("CART", msg)

    def test_common_and_pycache_are_not_treated_as_suites(self):
        with self.assertRaises(ValueError):
            resolve_suite_targets("common", self.suites)
