"""Tests for ls, cd, echo and cat working on example VFS files."""
import unittest
from pathlib import Path

from vfs_shell.shell import Shell
from vfs_shell.vfs import Vfs

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "vfs"


def make_shell(name):
    """Create a shell with the example VFS ``name`` mounted."""
    return Shell(Vfs.load(EXAMPLES / f"{name}.xml"))


class LsTests(unittest.TestCase):
    """Behaviour of ``ls``."""

    def setUp(self):
        """Mount the deep example."""
        self.shell = make_shell("deep")

    def test_root_listing_is_sorted(self):
        """Without arguments the current directory is listed."""
        self.assertEqual(self.shell.execute("ls").output,
                         "etc  home  usr  var")

    def test_path_argument(self):
        """A directory path argument is listed."""
        result = self.shell.execute("ls /home/alice/docs")
        self.assertEqual(result.output, "archive  report.txt")

    def test_empty_directory(self):
        """An empty directory gives no output and no error."""
        result = self.shell.execute("ls /var/log/empty_dir")
        self.assertEqual(result.lines(), [])
        self.assertFalse(result.is_error)

    def test_file_operand(self):
        """A file operand is printed as is."""
        self.assertEqual(self.shell.execute("ls /etc/motd").output,
                         "/etc/motd")

    def test_long_format(self):
        """``-l`` shows mode, owner, group, size and name."""
        result = self.shell.execute("ls -l /home/alice/docs")
        self.assertEqual(result.lines(), [
            "drwxr-xr-x alice users 4096 archive",
            "-rw-r--r-- alice users   10 report.txt",
        ])

    def test_multiple_operands_have_headers(self):
        """Several operands are separated and titled like in UNIX."""
        result = self.shell.execute("ls /etc /usr")
        self.assertEqual(result.output, "/etc:\nmotd\n\n/usr:\nbin")

    def test_missing_path_keeps_other_output(self):
        """An error does not hide the listing of valid operands."""
        result = self.shell.execute("ls /etc nope")
        self.assertTrue(result.is_error)
        self.assertEqual(result.lines(), [
            "/etc:", "motd",
            "ls: cannot access 'nope': No such file or directory"])

    def test_through_a_file(self):
        """A file in the middle of the path gives 'Not a directory'."""
        result = self.shell.execute("ls /etc/motd/x")
        self.assertIn("Not a directory", result.output)

    def test_invalid_option(self):
        """Unknown options are rejected."""
        self.assertEqual(self.shell.execute("ls -z").output,
                         "ls: invalid option -- 'z'")
        self.assertIn("unrecognized", self.shell.execute("ls --all").output)

    def test_hidden_files(self):
        """Dot files are hidden unless ``-a`` is given."""
        shell = make_shell("files")
        self.assertNotIn(".secret", shell.execute("ls").output)
        self.assertIn(".secret", shell.execute("ls -a").output)
        self.assertIn(".secret", shell.execute("ls -la").output)

    def test_double_dash(self):
        """After ``--`` everything is an operand."""
        result = self.shell.execute("ls -- -l")
        self.assertIn("cannot access '-l'", result.output)


class CdTests(unittest.TestCase):
    """Behaviour of ``cd`` and the prompt."""

    def setUp(self):
        """Mount the deep example."""
        self.shell = make_shell("deep")

    def test_absolute_and_relative(self):
        """Both kinds of path change the directory."""
        self.shell.execute("cd /home/alice")
        self.assertEqual(self.shell.cwd_text(), "/home/alice")
        self.shell.execute("cd docs/archive")
        self.assertEqual(self.shell.cwd_text(), "/home/alice/docs/archive")

    def test_parent_and_dot(self):
        """``..`` and ``.`` are supported."""
        self.shell.execute("cd /home/alice/docs")
        self.shell.execute("cd ../../bob/.")
        self.assertEqual(self.shell.cwd_text(), "/home/bob")

    def test_no_argument_goes_to_root(self):
        """``cd`` alone returns to the root."""
        self.shell.execute("cd /etc")
        self.shell.execute("cd")
        self.assertEqual(self.shell.cwd_text(), "/")

    def test_prompt_follows_directory(self):
        """The ``{cwd}`` placeholder reflects the current directory."""
        self.shell.execute("cd /usr/bin")
        self.assertEqual(self.shell.prompt_text(), "deep:/usr/bin$ ")

    def test_ls_is_relative_to_cwd(self):
        """``ls`` without arguments lists the current directory."""
        self.shell.execute("cd /home")
        self.assertEqual(self.shell.execute("ls").output, "alice  bob")

    def test_errors_keep_directory(self):
        """A failed ``cd`` leaves the directory unchanged."""
        self.shell.execute("cd /etc")
        for line, text in (("cd /nope", "No such file or directory"),
                           ("cd motd", "Not a directory"),
                           ("cd a b", "too many arguments")):
            result = self.shell.execute(line)
            self.assertTrue(result.is_error)
            self.assertIn(text, result.output)
            self.assertEqual(self.shell.cwd_text(), "/etc")


class EchoTests(unittest.TestCase):
    """Behaviour of ``echo``."""

    def setUp(self):
        """Create a shell with an empty VFS."""
        self.shell = Shell()

    def test_joins_arguments(self):
        """Arguments are joined by single spaces."""
        self.assertEqual(self.shell.execute("echo a   b  c").output, "a b c")

    def test_quotes_keep_spaces(self):
        """Quoted arguments keep their inner spaces."""
        result = self.shell.execute('echo "a   b"  c')
        self.assertEqual(result.output, "a   b c")

    def test_no_arguments(self):
        """``echo`` alone prints an empty line."""
        self.assertEqual(self.shell.execute("echo").lines(), [])


class CatTests(unittest.TestCase):
    """Behaviour of ``cat``."""

    def setUp(self):
        """Mount the files example."""
        self.shell = make_shell("files")

    def test_single_file(self):
        """The content of a file is printed."""
        result = self.shell.execute("cat hello.txt")
        self.assertEqual(result.lines(), ["Hello, VFS!"])

    def test_unicode(self):
        """Non-ASCII text is shown correctly."""
        result = self.shell.execute("cat notes.txt")
        self.assertIn("Привет, мир!", result.lines())

    def test_several_files(self):
        """Files are concatenated in the given order."""
        result = self.shell.execute("cat hello.txt data.csv")
        self.assertEqual(result.lines()[0], "Hello, VFS!")
        self.assertIn('1,"Smith, John"', result.lines())
        self.assertIn("2,<none> & co", result.lines())

    def test_empty_file(self):
        """An empty file prints nothing."""
        self.assertEqual(self.shell.execute("cat empty.txt").lines(), [])

    def test_binary_file_does_not_crash(self):
        """Binary data is decoded with replacement characters."""
        result = self.shell.execute("cat logo.bin")
        self.assertFalse(result.is_error)
        self.assertIn("PNG", result.output)
        self.assertNotIn("\x1a", result.output)
        self.assertNotIn("\r", result.output)

    def test_errors(self):
        """Missing operand, missing file and directories are reported."""
        deep = make_shell("deep")
        self.assertEqual(self.shell.execute("cat").output,
                         "cat: missing file operand")
        self.assertIn("No such file", self.shell.execute("cat x").output)
        self.assertEqual(deep.execute("cat /etc").output,
                         "cat: /etc: Is a directory")

    def test_partial_output_before_error(self):
        """Valid files are printed even if another operand fails."""
        result = self.shell.execute("cat hello.txt nope")
        self.assertTrue(result.is_error)
        self.assertEqual(result.lines(), [
            "Hello, VFS!", "cat: nope: No such file or directory"])

    def test_relative_to_cwd(self):
        """Relative file names are resolved from the current directory."""
        deep = make_shell("deep")
        deep.execute("cd /home/alice/docs")
        self.assertEqual(deep.execute("cat report.txt").output, "Q3 report\n")
