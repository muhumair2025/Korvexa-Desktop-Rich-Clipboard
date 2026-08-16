"""
Unit tests for PrivacyService heuristic detection and application ignore list.
"""

import unittest

from models.settings_model import AppSettings
from services.privacy_service import PrivacyService


class TestPrivacy(unittest.TestCase):
    """Tests for sensitive data detection and process filtering."""

    def setUp(self):
        self.settings = AppSettings(
            detect_sensitive=True,
            save_sensitive=False,
            ignored_apps=["keepass.exe", "1password.exe", "bitwarden.exe"],
        )
        self.service = PrivacyService(self.settings)

    def test_ignored_application(self):
        self.assertTrue(self.service.is_application_ignored("keepass.exe"))
        self.assertTrue(self.service.is_application_ignored("C:\\Program Files\\1Password\\1password.exe"))
        self.assertFalse(self.service.is_application_ignored("notepad.exe"))
        self.assertFalse(self.service.is_application_ignored("chrome.exe"))

    def test_sensitive_heuristics(self):
        # AWS Key
        self.assertTrue(self.service.is_sensitive_content("AKIAIOSFODNN7EXAMPLE"))
        # Private Key
        self.assertTrue(self.service.is_sensitive_content("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA..."))
        # Bearer token
        self.assertTrue(self.service.is_sensitive_content("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"))
        # Password pattern
        self.assertTrue(self.service.is_sensitive_content("password = MySecretPass123!"))
        # Normal text
        self.assertFalse(self.service.is_sensitive_content("Meeting notes for Monday sprint review."))

    def test_should_save_item(self):
        # Should NOT save if from ignored app
        self.assertFalse(self.service.should_save_item("keepass.exe", "normal text"))
        # Should NOT save if sensitive and save_sensitive is False
        self.assertFalse(self.service.should_save_item("notepad.exe", "password = SuperSecretPass123"))
        # Should save normal text from normal app
        self.assertTrue(self.service.should_save_item("notepad.exe", "normal document text"))


if __name__ == "__main__":
    unittest.main()
