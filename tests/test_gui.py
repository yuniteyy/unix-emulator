"""Smoke tests for the Tk window (skipped when no display is present)."""
import time
import tkinter as tk
import unittest

from vfs_shell.gui import ShellWindow
from vfs_shell.script import play
from vfs_shell.shell import Shell
from vfs_shell.vfs import Vfs

ATTEMPTS = 20
PAUSE = 0.01


class WindowTests(unittest.TestCase):
    """Title, echo and output of the GUI."""

    def setUp(self):
        """Open a window or skip the test if Tk cannot start."""
        try:
            self.window = ShellWindow(Shell(Vfs.empty("demo")))
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
        self.window.submit("echo hi there")
        self.assertIn("demo:/$ echo hi there", self.text())
        self.assertIn("\nhi there\n", self.text())

    def test_error_is_displayed(self):
        """Errors are displayed in the same area."""
        self.window.submit("nope")
        self.assertIn("nope: command not found", self.text())


class PlaybackTests(unittest.TestCase):
    """Script playback inside the window."""

    def test_script_is_replayed(self):
        """Steps appear in the output and the input is enabled again."""
        try:
            window = ShellWindow(Shell(Vfs.empty("demo"), prompt="> "))
        except tk.TclError:
            self.skipTest("no display available")
        window.play(play(window.shell, ["echo a", "bad"]), delay=1)
        for _ in range(ATTEMPTS):
            window.root.update()
            time.sleep(PAUSE)
        text = window.output.get("1.0", "end")
        window.root.destroy()
        self.assertIn("> echo a", text)
        self.assertIn("bad: command not found", text)
