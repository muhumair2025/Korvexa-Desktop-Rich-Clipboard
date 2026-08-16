"""
Unit tests for URL utilities.
"""

import unittest

from utils.urls import extract_domain


class TestUrls(unittest.TestCase):
    """Tests for URL extraction and domain parsing."""

    def test_extract_domain(self):
        self.assertEqual(extract_domain("https://github.com/torvalds/linux"), "github.com")
        self.assertEqual(extract_domain("http://sub.domain.co.uk/page?query=1"), "sub.domain.co.uk")
        self.assertEqual(extract_domain("example.com/test"), "example.com")


if __name__ == "__main__":
    unittest.main()
