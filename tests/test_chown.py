"""Tests for ``chown``: ownership changes happen only in memory."""
import os
import tempfile
import unittest
from pathlib import Path

from vfs_shell.commands import CommandError, parse_owner_spec
from vfs_shell.shell import Shell
from vfs_shell.vfs import Vfs

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "vfs"


def owner_group(shell, path):
    """Return ``(owner, group)`` of ``path`` in the shell's VFS."""
    node, _ = shell.vfs.lookup(path, shell.cwd)
    return node.owner, node.group


class SpecTests(unittest.TestCase):
    """Parsing of ``OWNER[:GROUP]``."""

    def test_valid_forms(self):
        """All supported forms give the expected pair."""
        self.assertEqual(parse_owner_spec("al"), ("al", None))
        self.assertEqual(parse_owner_spec("al:us"), ("al", "us"))
        self.assertEqual(parse_owner_spec(":us"), (None, "us"))
        self.assertEqual(parse_owner_spec("al:"), ("al", "al"))
        self.assertEqual(parse_owner_spec("1000:100"), ("1000", "100"))

    def test_invalid_forms(self):
        """Empty and malformed specifications are rejected."""
        for spec in ("", ":", "bad name", "a:b:c", "-x", "a:b c"):
            with self.assertRaises(CommandError, msg=spec):
                parse_owner_spec(spec)


class ChownTests(unittest.TestCase):
    """Behaviour of the command itself."""

    def setUp(self):
        """Mount the deep example."""
        self.shell = Shell(Vfs.load(EXAMPLES / "deep.xml"))

    def test_owner_only(self):
        """Only the owner changes."""
        self.shell.execute("chown carol /home/bob/todo.txt")
        self.assertEqual(owner_group(self.shell, "/home/bob/todo.txt"),
                         ("carol", "users"))

    def test_owner_and_group(self):
        """Both values change."""
        self.shell.execute("chown dave:staff /home/bob/todo.txt")
        self.assertEqual(owner_group(self.shell, "/home/bob/todo.txt"),
                         ("dave", "staff"))

    def test_group_only(self):
        """``:GROUP`` changes only the group."""
        self.shell.execute("chown :wheel /home/bob/todo.txt")
        self.assertEqual(owner_group(self.shell, "/home/bob/todo.txt"),
                         ("bob", "wheel"))

    def test_trailing_colon(self):
        """``OWNER:`` sets the group to the owner name."""
        self.shell.execute("chown erin: /etc/motd")
        self.assertEqual(owner_group(self.shell, "/etc/motd"),
                         ("erin", "erin"))

    def test_several_files(self):
        """Every operand is processed."""
        self.shell.execute("chown x /etc/motd /var/log/syslog.txt")
        self.assertEqual(owner_group(self.shell, "/etc/motd")[0], "x")
        self.assertEqual(owner_group(self.shell, "/var/log/syslog.txt")[0],
                         "x")

    def test_directory_without_recursion(self):
        """Without ``-R`` only the directory itself changes."""
        self.shell.execute("chown frank /home/alice")
        self.assertEqual(owner_group(self.shell, "/home/alice")[0], "frank")
        self.assertEqual(owner_group(self.shell, "/home/alice/docs")[0],
                         "alice")

    def test_recursive(self):
        """``-R`` changes the whole subtree."""
        self.shell.execute("chown -R frank:team /home/alice")
        for path in ("/home/alice", "/home/alice/docs",
                     "/home/alice/docs/report.txt",
                     "/home/alice/docs/archive/2026/summary.txt"):
            self.assertEqual(owner_group(self.shell, path),
                             ("frank", "team"), path)
        self.assertEqual(owner_group(self.shell, "/home/bob")[0], "bob")

    def test_relative_path(self):
        """Paths are resolved from the current directory."""
        self.shell.execute("cd /home/bob")
        self.shell.execute("chown gina todo.txt")
        self.assertEqual(owner_group(self.shell, "/home/bob/todo.txt")[0],
                         "gina")

    def test_ls_shows_new_owner(self):
        """The change is visible through ``ls -l``."""
        self.shell.execute("chown gina:ops /home/bob/todo.txt")
        out = self.shell.execute("ls -l /home/bob").output
        self.assertIn("gina ops", out)

    def test_errors(self):
        """Every kind of misuse gives a clear message."""
        cases = (
            ("chown", "chown: missing operand"),
            ("chown alice", "chown: missing operand after 'alice'"),
            ("chown alice /nope", "cannot access '/nope'"),
            ('chown "bad name" /etc/motd', "invalid user"),
            ("chown a:b:c /etc/motd", "invalid group"),
            ("chown -z alice /etc/motd", "invalid option -- 'z'"),
        )
        for line, text in cases:
            result = self.shell.execute(line)
            self.assertTrue(result.is_error, line)
            self.assertIn(text, result.output, line)

    def test_failed_command_changes_nothing(self):
        """A rejected specification leaves the VFS untouched."""
        self.shell.execute("chown a:b:c /etc/motd")
        self.assertEqual(owner_group(self.shell, "/etc/motd"),
                         ("root", "root"))

    def test_valid_operands_still_processed(self):
        """A missing operand does not stop the other ones."""
        result = self.shell.execute("chown zed /etc/motd /nope")
        self.assertTrue(result.is_error)
        self.assertEqual(owner_group(self.shell, "/etc/motd")[0], "zed")


class InMemoryTests(unittest.TestCase):
    """The source file changes only after an explicit ``vfs-save``."""

    def test_source_untouched_until_saved(self):
        """The XML on disk is the same until ``vfs-save`` is used."""
        source = EXAMPLES / "deep.xml"
        before = source.read_bytes()
        shell = Shell(Vfs.load(source))
        shell.execute("chown -R zoe /home")
        self.assertEqual(source.read_bytes(), before)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.xml")
            shell.execute(f"vfs-save {path}")
            again = Shell(Vfs.load(path))
        self.assertEqual(owner_group(again, "/home/alice/docs")[0], "zoe")
        self.assertEqual(owner_group(again, "/etc")[0], "root")
