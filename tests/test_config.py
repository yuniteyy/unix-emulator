"""Tests for command-line parameters and debug output."""
import unittest

from vfs_shell.config import debug_lines, parse_args
from vfs_shell.shell import DEFAULT_PROMPT


class ParseArgsTests(unittest.TestCase):
    """Conversion of ``argv`` into a configuration."""

    def test_defaults(self):
        """Without arguments all parameters have default values."""
        config = parse_args([])
        self.assertIsNone(config.vfs)
        self.assertIsNone(config.script)
        self.assertEqual(config.prompt, DEFAULT_PROMPT)
        self.assertFalse(config.headless)

    def test_all_parameters(self):
        """Every supported parameter is recognised."""
        config = parse_args(
            ["--vfs", "a.xml", "--prompt", "> ", "--script", "s.txt",
             "--headless"])
        self.assertEqual(config.vfs, "a.xml")
        self.assertEqual(config.prompt, "> ")
        self.assertEqual(config.script, "s.txt")
        self.assertTrue(config.headless)

    def test_unknown_parameter(self):
        """An unknown parameter makes the parser exit."""
        with self.assertRaises(SystemExit):
            parse_args(["--bogus"])


class DebugTests(unittest.TestCase):
    """The debug output lists every parameter."""

    def test_debug_lists_values(self):
        """Each parameter and its value appear in the debug text."""
        config = parse_args(["--vfs", "x.xml", "--prompt", "$ "])
        text = "\n".join(debug_lines(config))
        for name in ("vfs", "prompt", "script", "headless"):
            self.assertIn(name, text)
        self.assertIn("'x.xml'", text)
