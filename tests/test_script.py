"""Tests for startup scripts and the headless mode."""
import contextlib
import io
import os
import tempfile
import unittest

from vfs_shell.app import main, run_headless
from vfs_shell.script import ScriptError, load_script, play
from vfs_shell.shell import Shell
from vfs_shell.vfs import Vfs


def run_lines(lines, **kwargs):
    """Run ``lines`` headless and return the printed output lines."""
    printed = []
    run_headless(Shell(Vfs.empty(), **kwargs), lines, emit=printed.append)
    return printed


class PlayTests(unittest.TestCase):
    """Script playback imitates a user dialog."""

    def test_input_and_output_are_shown(self):
        """Both the typed line and its output are displayed."""
        out = run_lines(["echo hi"], prompt="> ")
        self.assertEqual(out, ["> echo hi", "hi"])

    def test_errors_are_skipped(self):
        """An erroneous line is reported and the script goes on."""
        out = run_lines(["bad", "echo ok"])
        self.assertIn("bad: command not found", out)
        self.assertTrue(any("строка 1" in text for text in out))
        self.assertIn("ok", out)

    def test_blank_lines_and_comments(self):
        """Blank lines vanish, comments are only echoed."""
        out = run_lines(["", "# note", "echo x"], prompt="> ")
        self.assertEqual(out[0], "> # note")
        self.assertEqual(len(out), 3)

    def test_exit_stops_script(self):
        """Nothing after ``exit`` is executed."""
        shell = Shell()
        steps = list(play(shell, ["exit", "ls"]))
        self.assertEqual(len(steps), 1)
        self.assertFalse(shell.running)


class LoadTests(unittest.TestCase):
    """Reading script files."""

    def test_missing_file(self):
        """A missing script is reported."""
        with self.assertRaises(ScriptError):
            load_script("/no/such/script.txt")

    def test_read_lines(self):
        """The file is split into lines."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "s.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("ls\ncd x\n")
            self.assertEqual(load_script(path), ["ls", "cd x"])


class MainTests(unittest.TestCase):
    """End-to-end runs of :func:`vfs_shell.app.main`."""

    def run_main(self, argv):
        """Run ``main`` and return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_script_is_an_error(self):
        """A missing script gives a message and a non-zero code."""
        code, _, err = self.run_main(["--headless", "--script", "nope"])
        self.assertNotEqual(code, 0)
        self.assertIn("script not found", err)

    def test_debug_output_and_prompt(self):
        """Parameters are printed and the custom prompt is used."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "s.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("ls\n")
            code, out, _ = self.run_main(
                ["--headless", "--prompt", "me> ", "--script", path])
        self.assertEqual(code, 0)
        self.assertIn("[debug]", out)
        self.assertIn("me> ls", out)
