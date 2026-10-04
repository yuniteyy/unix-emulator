"""Smoke tests for the Tk window (skipped when no display is present)."""
import tkinter as tk
import unittest

from vfs_shell.gui import ShellWindow
from vfs_shell.shell import Shell


class WindowTests(unittest.TestCase):
    """Title, echo and output of the GUI."""

    def setUp(self):
        """Open a window or skip the test if Tk cannot start."""
        try:
            self.window = ShellWindow(Shell(vfs_name="demo"))
        except tk.TclError:
            self.skipTest("no display available")

    def tearDown(self):
        """Close the window if it is still open."""
        if self.window.shell.running:
            self.window.root.destroy()

    def text(self):
        """Return everything shown in the output area."""
        return self.window.output.get("1.0", "end")

    def test_title_has_vfs_name(self):
        """The window title contains the VFS name."""
        self.assertIn("demo", self.window.root.title())

    def test_submit_shows_dialog(self):
        """Both the typed line and the result are displayed."""
        self.window.submit("ls -l")
        self.assertIn("$ ls -l", self.text())
        self.assertIn("name: ls, args: ['-l']", self.text())

    def test_error_is_displayed(self):
        """Errors are displayed in the same area."""
        self.window.submit("nope")
        self.assertIn("nope: command not found", self.text())
