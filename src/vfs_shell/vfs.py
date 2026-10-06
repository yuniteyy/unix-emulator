"""In-memory virtual file system loaded from and saved to XML.

Format::

    <vfs name="demo" owner="root" group="root">
      <dir name="home" owner="alice" group="users">
        <file name="a.txt">text</file>
        <file name="b.bin" encoding="base64">AAEC</file>
      </dir>
    </vfs>

All data lives in memory: nothing is unpacked or written to disk except
by an explicit :meth:`Vfs.save`.
"""
import base64
import binascii
import re
from xml.etree import ElementTree
from dataclasses import dataclass, field
from pathlib import Path

ROOT_TAG = "vfs"
DIR_TAG = "dir"
FILE_TAG = "file"
ENC_TEXT = "text"
ENC_BASE64 = "base64"
DEFAULT_NAME = "default"
DEFAULT_OWNER = "root"
DEFAULT_GROUP = "root"
TEXT_ENCODING = "utf-8"
RESERVED_NAMES = ("", ".", "..")
UNSAFE_TEXT = re.compile(r"[\x00-\x08\x0b-\x1f\ufffe\uffff]")
SEPARATOR = "/"
PARENT = ".."
CURRENT = "."


class VfsError(Exception):
    """The VFS cannot be loaded, saved or navigated."""


@dataclass
class Node:
    """A directory or a file of the virtual file system."""

    name: str
    is_dir: bool
    owner: str = DEFAULT_OWNER
    group: str = DEFAULT_GROUP
    data: bytes = b""
    binary: bool = False
    children: dict = field(default_factory=dict)

    @property
    def size(self):
        """Return the size of the file content in bytes."""
        return len(self.data)


def _decode_data(element, name):
    """Return ``(bytes, is_binary)`` for the ``<file>`` ``element``."""
    if len(element):
        raise VfsError(f"file '{name}' must not contain elements")
    encoding = element.get("encoding", ENC_TEXT)
    text = element.text or ""
    if encoding == ENC_TEXT:
        return text.encode(TEXT_ENCODING), False
    if encoding != ENC_BASE64:
        raise VfsError(f"unknown encoding {encoding!r} of file '{name}'")
    try:
        return base64.b64decode("".join(text.split()), validate=True), True
    except binascii.Error as exc:
        raise VfsError(f"invalid base64 in file '{name}': {exc}") from None


def _parse_children(element):
    """Parse the child elements of ``element`` into a name->node dict."""
    children = {}
    for child in element:
        node = _parse_node(child)
        if node.name in children:
            raise VfsError(f"duplicate name '{node.name}'")
        children[node.name] = node
    return children


def _parse_node(element):
    """Convert a ``<dir>`` or ``<file>`` element into a :class:`Node`."""
    name = element.get("name")
    if name is None or name in RESERVED_NAMES or SEPARATOR in name:
        raise VfsError(f"invalid name {name!r} in <{element.tag}>")
    owner = element.get("owner") or DEFAULT_OWNER
    group = element.get("group") or DEFAULT_GROUP
    if element.tag == DIR_TAG:
        children = _parse_children(element)
        return Node(name, True, owner, group, children=children)
    if element.tag == FILE_TAG:
        data, binary = _decode_data(element, name)
        return Node(name, False, owner, group, data, binary)
    raise VfsError(f"unknown element <{element.tag}>")


def _is_text_safe(data):
    """Tell whether ``data`` can be stored as XML text."""
    try:
        text = data.decode(TEXT_ENCODING)
    except UnicodeDecodeError:
        return False
    return not UNSAFE_TEXT.search(text)


def _to_element(node):
    """Convert a :class:`Node` back into an XML element."""
    tag = DIR_TAG if node.is_dir else FILE_TAG
    element = ElementTree.Element(
        tag, name=node.name, owner=node.owner, group=node.group)
    if node.is_dir:
        element.extend(_to_element(kid) for kid in node.children.values())
    elif node.binary or not _is_text_safe(node.data):
        element.set("encoding", ENC_BASE64)
        element.text = base64.b64encode(node.data).decode("ascii")
    elif node.data:
        element.text = node.data.decode(TEXT_ENCODING)
    return element


class Vfs:
    """A named tree of :class:`Node` objects kept entirely in memory."""

    def __init__(self, name, root):
        """Create a VFS called ``name`` with the root directory ``root``."""
        self.name = name
        self.root = root

    @classmethod
    def empty(cls, name=DEFAULT_NAME):
        """Return a VFS that has only an empty root directory."""
        return cls(name, Node("", True))

    @classmethod
    def load(cls, path):
        """Read the VFS from the XML file ``path``."""
        try:
            top = ElementTree.parse(path).getroot()
        except FileNotFoundError:
            raise VfsError(f"VFS file not found: {path}") from None
        except ElementTree.ParseError as exc:
            raise VfsError(f"invalid VFS format: {exc}") from None
        except OSError as exc:
            raise VfsError(f"cannot read {path}: {exc.strerror}") from None
        if top.tag != ROOT_TAG:
            raise VfsError(
                f"invalid VFS format: root element must be <{ROOT_TAG}>")
        root = Node("", True, top.get("owner") or DEFAULT_OWNER,
                    top.get("group") or DEFAULT_GROUP,
                    children=_parse_children(top))
        return cls(top.get("name") or Path(path).stem, root)

    def save(self, path):
        """Write the VFS to ``path`` in the same XML format."""
        top = _to_element(self.root)
        top.tag = ROOT_TAG
        top.attrib["name"] = self.name
        ElementTree.indent(top)
        try:
            ElementTree.ElementTree(top).write(
                path, encoding=TEXT_ENCODING, xml_declaration=True)
        except OSError as exc:
            raise VfsError(f"cannot write {path}: {exc.strerror}") from None

    def lookup(self, path, cwd):
        """Resolve ``path`` relative to ``cwd`` (a list of names).

        Returns ``(node, names)`` where ``names`` is the normalised
        absolute location. Raises :class:`VfsError` when it is missing.
        """
        names = [] if path.startswith(SEPARATOR) else list(cwd)
        stack = [self.root]
        for name in names:
            stack.append(stack[-1].children[name])
        for part in path.split(SEPARATOR):
            self._step(stack, names, part)
        return stack[-1], names

    @staticmethod
    def _step(stack, names, part):
        """Move the walk ``stack`` by one path component ``part``."""
        if part in ("", CURRENT):
            return
        if part == PARENT:
            if names:
                names.pop()
                stack.pop()
            return
        if not stack[-1].is_dir:
            raise VfsError("Not a directory")
        child = stack[-1].children.get(part)
        if child is None:
            raise VfsError("No such file or directory")
        stack.append(child)
        names.append(part)
