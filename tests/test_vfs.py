"""Tests for the in-memory VFS: loading, saving and path lookup."""
import os
import tempfile
import unittest
from pathlib import Path

from vfs_shell.vfs import Node, Vfs, VfsError

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples" / "vfs"


def load_text(xml):
    """Load a VFS from an XML string through a temporary file."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "t.xml")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(xml)
        return Vfs.load(path)


class LoadTests(unittest.TestCase):
    """Reading the example VFS files."""

    def test_minimal(self):
        """The minimal VFS has a name and a single file."""
        vfs = Vfs.load(EXAMPLES / "minimal.xml")
        self.assertEqual(vfs.name, "minimal")
        self.assertEqual(list(vfs.root.children), ["readme.txt"])

    def test_several_files(self):
        """Text, empty and base64 files are decoded correctly."""
        vfs = Vfs.load(EXAMPLES / "files.xml")
        kids = vfs.root.children
        self.assertEqual(kids["hello.txt"].data, b"Hello, VFS!\n")
        self.assertEqual(kids["empty.txt"].size, 0)
        self.assertTrue(kids["logo.bin"].binary)
        self.assertEqual(kids["logo.bin"].data, b"\x89PNG\r\n\x1a\n")
        self.assertEqual(kids["notes.txt"].owner, "alice")

    def test_three_levels(self):
        """Nested directories are available at depth three and more."""
        vfs = Vfs.load(EXAMPLES / "deep.xml")
        node, names = vfs.lookup("/home/alice/docs/archive/2026", [])
        self.assertTrue(node.is_dir)
        self.assertEqual(names, ["home", "alice", "docs", "archive", "2026"])
        self.assertIn("summary.txt", node.children)

    def test_name_defaults_to_file_stem(self):
        """Without a ``name`` attribute the file name is used."""
        vfs = load_text("<vfs />")
        self.assertEqual(vfs.name, "t")


class LoadErrorTests(unittest.TestCase):
    """Every kind of broken input is reported with a VfsError."""

    def assert_error(self, path, text):
        """Loading ``path`` fails with a message containing ``text``."""
        with self.assertRaises(VfsError) as caught:
            Vfs.load(path)
        self.assertIn(text, str(caught.exception))

    def test_missing_file(self):
        """A missing file is reported."""
        self.assert_error("/no/such/file.xml", "not found")

    def test_not_well_formed(self):
        """Broken XML is reported."""
        self.assert_error(EXAMPLES / "invalid" / "broken.xml", "invalid VFS")

    def test_wrong_root(self):
        """The root element must be ``<vfs>``."""
        self.assert_error(EXAMPLES / "invalid" / "wrong_root.xml", "<vfs>")

    def test_bad_base64(self):
        """Invalid base64 data is reported."""
        self.assert_error(EXAMPLES / "invalid" / "bad_base64.xml", "base64")

    def test_duplicate_names(self):
        """Two entries with one name in a directory are rejected."""
        self.assert_error(EXAMPLES / "invalid" / "duplicate.xml", "duplicate")

    def test_invalid_names_and_tags(self):
        """Names with a slash and unknown tags are rejected."""
        for xml in ('<vfs><file name="a/b" /></vfs>',
                    '<vfs><file /></vfs>',
                    '<vfs><link name="x" /></vfs>',
                    '<vfs><file name="f" encoding="rot13" /></vfs>',
                    '<vfs><file name="f"><x /></file></vfs>'):
            with self.assertRaises(VfsError, msg=xml):
                load_text(xml)


class SaveTests(unittest.TestCase):
    """Saving returns the VFS to the original format."""

    def round_trip(self, name):
        """Load, save and load again; return both VFS objects."""
        first = Vfs.load(EXAMPLES / name)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "copy.xml")
            first.save(path)
            return first, Vfs.load(path)

    def test_round_trip_keeps_tree(self):
        """The saved file describes exactly the same tree."""
        for name in ("minimal.xml", "files.xml", "deep.xml"):
            first, second = self.round_trip(name)
            self.assertEqual(first.name, second.name)
            self.assertEqual(first.root, second.root)

    def test_unsafe_text_is_stored_as_base64(self):
        """Control characters survive thanks to base64."""
        vfs = Vfs.empty("x")
        node = vfs.lookup("/", [])[0]
        node.children["c.txt"] = Node("c.txt", False, data=b"a\x00b\r\n")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "c.xml")
            vfs.save(path)
            again = Vfs.load(path)
        self.assertEqual(again.root.children["c.txt"].data, b"a\x00b\r\n")

    def test_save_error(self):
        """An unwritable path is reported."""
        with self.assertRaises(VfsError):
            Vfs.empty().save("/no/such/dir/x.xml")


class LookupTests(unittest.TestCase):
    """Absolute and relative path resolution."""

    def setUp(self):
        """Load the deep example."""
        self.vfs = Vfs.load(EXAMPLES / "deep.xml")

    def test_relative_and_parent(self):
        """Relative paths and ``..`` are resolved from ``cwd``."""
        node, names = self.vfs.lookup("../bob", ["home", "alice"])
        self.assertEqual(names, ["home", "bob"])
        self.assertIn("todo.txt", node.children)

    def test_parent_of_root_is_root(self):
        """``..`` at the root stays at the root."""
        _, names = self.vfs.lookup("../..", [])
        self.assertEqual(names, [])

    def test_missing_and_not_a_directory(self):
        """Both failure kinds give distinct messages."""
        with self.assertRaisesRegex(VfsError, "No such file"):
            self.vfs.lookup("/nope", [])
        with self.assertRaisesRegex(VfsError, "Not a directory"):
            self.vfs.lookup("/etc/motd/x", [])
