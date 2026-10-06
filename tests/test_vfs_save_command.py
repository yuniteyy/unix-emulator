"""Tests for the ``vfs-save`` command and VFS start-up errors."""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from vfs_shell.app import main
from vfs_shell.shell import Shell
from vfs_shell.vfs import Vfs

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "vfs"


class VfsSaveTests(unittest.TestCase):
    """Behaviour of ``vfs-save PATH``."""

    def setUp(self):
        """Mount the files example."""
        self.shell = Shell(Vfs.load(EXAMPLES / "files.xml"))

    def test_save_writes_loadable_file(self):
        """The saved file can be loaded again."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "s.xml")
            result = self.shell.execute(f"vfs-save {path}")
            self.assertFalse(result.is_error)
            self.assertEqual(Vfs.load(path).root, self.shell.vfs.root)

    def test_missing_operand(self):
        """The path argument is mandatory."""
        result = self.shell.execute("vfs-save")
        self.assertEqual(result.output, "vfs-save: missing file operand")

    def test_too_many_arguments(self):
        """Only one path is accepted."""
        self.assertTrue(self.shell.execute("vfs-save a b").is_error)

    def test_unwritable_path(self):
        """A write failure is shown as an error."""
        result = self.shell.execute("vfs-save /no/such/dir/x.xml")
        self.assertTrue(result.is_error)
        self.assertIn("cannot write", result.output)


class StartupTests(unittest.TestCase):
    """Loading problems stop the start-up with a message."""

    def run_main(self, argv):
        """Run ``main``; return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_vfs(self):
        """A missing VFS file gives an error and code 1."""
        code, _, err = self.run_main(["--headless", "--vfs", "no.xml"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_broken_vfs(self):
        """A malformed VFS file gives an error and code 1."""
        path = str(EXAMPLES / "invalid" / "broken.xml")
        code, _, err = self.run_main(["--headless", "--vfs", path])
        self.assertEqual(code, 1)
        self.assertIn("invalid VFS", err)

    def test_vfs_name_in_prompt(self):
        """The VFS name from the XML is used in the prompt."""
        path = str(EXAMPLES / "deep.xml")
        with tempfile.TemporaryDirectory() as folder:
            script = os.path.join(folder, "s.txt")
            with open(script, "w", encoding="utf-8") as handle:
                handle.write("ls\n")
            _, out, _ = self.run_main(
                ["--headless", "--vfs", path, "--script", script])
        self.assertIn("deep:/$ ls", out)
