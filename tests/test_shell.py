"""Tests for parsing, dispatch and error reporting of the shell core."""
import unittest

from vfs_shell.history import InputHistory
from vfs_shell.shell import Shell, parse_line


class ParseTests(unittest.TestCase):
    """Splitting of an input line into a command and arguments."""

    def test_split_by_spaces(self):
        """Words are separated by any amount of spaces."""
        self.assertEqual(parse_line("ls   -l  /tmp"), ["ls", "-l", "/tmp"])

    def test_quotes_group_words(self):
        """Quoted text stays a single argument."""
        self.assertEqual(parse_line('echo "a b"'), ["echo", "a b"])

    def test_unbalanced_quote(self):
        """An unbalanced quote is a parse error."""
        with self.assertRaises(ValueError):
            parse_line('echo "oops')


class ExecuteTests(unittest.TestCase):
    """Behaviour of :meth:`Shell.execute`."""

    def setUp(self):
        """Create a fresh shell for every test."""
        self.shell = Shell()

    def test_empty_line(self):
        """An empty line produces no output and no error."""
        result = self.shell.execute("   ")
        self.assertEqual(result.lines(), [])
        self.assertFalse(result.is_error)

    def test_unknown_command(self):
        """An unknown command is reported as an error."""
        result = self.shell.execute("foo bar")
        self.assertTrue(result.is_error)
        self.assertEqual(result.output, "foo: command not found")

    def test_parse_error(self):
        """Broken quoting is reported as an error."""
        result = self.shell.execute('ls "x')
        self.assertTrue(result.is_error)
        self.assertIn("parse error", result.output)

    def test_stub_prints_name_and_args(self):
        """Stubs print their own name and the received arguments."""
        result = self.shell.execute("ls -l a b")
        self.assertEqual(result.output, "name: ls, args: ['-l', 'a', 'b']")
        result = self.shell.execute("cd /usr")
        self.assertEqual(result.output, "name: cd, args: ['/usr']")

    def test_exit(self):
        """``exit`` stops the shell."""
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)

    def test_exit_with_arguments(self):
        """``exit`` rejects arguments and keeps running."""
        result = self.shell.execute("exit now")
        self.assertTrue(result.is_error)
        self.assertTrue(self.shell.running)


class HistoryTests(unittest.TestCase):
    """Walking through entered lines."""

    def test_walk_back_and_forth(self):
        """Up and Down move through the stored lines."""
        history = InputHistory()
        history.add("one")
        history.add("two")
        self.assertEqual(history.previous(), "two")
        self.assertEqual(history.previous(), "one")
        self.assertEqual(history.previous(), "one")
        self.assertEqual(history.following(), "two")
        self.assertEqual(history.following(), "")
