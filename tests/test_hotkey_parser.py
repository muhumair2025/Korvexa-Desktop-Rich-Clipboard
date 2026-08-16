"""
Unit tests for hotkey string parser.
"""

import unittest

from hotkeys.global_hotkey import MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, VK_MAP, parse_hotkey_string


class TestHotkeyParser(unittest.TestCase):
    """Tests for hotkey string combination parsing."""

    def test_parse_ctrl_shift_v(self):
        parsed = parse_hotkey_string("Ctrl+Shift+V")
        self.assertIsNotNone(parsed)
        modifiers, vk = parsed
        self.assertEqual(modifiers, MOD_CONTROL | MOD_SHIFT)
        self.assertEqual(vk, VK_MAP["V"])

    def test_parse_ctrl_alt_delete(self):
        parsed = parse_hotkey_string("Ctrl+Alt+DELETE")
        self.assertIsNotNone(parsed)
        modifiers, vk = parsed
        self.assertEqual(modifiers, MOD_CONTROL | MOD_ALT)
        self.assertEqual(vk, VK_MAP["DELETE"])

    def test_invalid_hotkey(self):
        self.assertIsNone(parse_hotkey_string(""))
        self.assertIsNone(parse_hotkey_string("Ctrl+Shift"))  # Missing key


if __name__ == "__main__":
    unittest.main()
