"""Built-in commands.

Every command is a function ``(shell, args) -> str`` returning its output.
Failures are reported by raising :class:`CommandError`; a command that
fails halfway may attach the output produced so far.
"""
import re

from .vfs import SEPARATOR, TEXT_ENCODING, VfsError

CURRENT_DIR = "."
HIDDEN_PREFIX = "."
LS_FLAGS = "la"
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"
DIR_SIZE = 4096
BLOCK_SEPARATOR = "\n\n"
COLUMN_SEPARATOR = "  "
OPTION_PREFIX = "-"
END_OF_OPTIONS = "--"
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
REPLACEMENT = "\ufffd"


class CommandError(Exception):
    """User-visible command failure that may carry partial output."""

    def __init__(self, message, output=""):
        """Store the error ``message`` and the output produced so far."""
        super().__init__(message)
        self.output = output


def _is_option(arg):
    """Tell whether ``arg`` looks like an option such as ``-l``."""
    return arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX


def _add_flags(arg, allowed, flags):
    """Add the letters of the option ``arg`` to ``flags``."""
    if arg.startswith(END_OF_OPTIONS):
        raise CommandError(f"unrecognized option '{arg}'")
    for letter in arg[len(OPTION_PREFIX):]:
        if letter not in allowed:
            raise CommandError(f"invalid option -- '{letter}'")
        flags.add(letter)


def parse_options(args, allowed):
    """Split ``args`` into a set of flag letters and a list of operands.

    ``--`` ends option processing. Unknown options raise
    :class:`CommandError`.
    """
    flags, operands = set(), []
    for index, arg in enumerate(args):
        if arg == END_OF_OPTIONS:
            operands.extend(args[index + 1:])
            break
        if _is_option(arg):
            _add_flags(arg, allowed, flags)
        else:
            operands.append(arg)
    return flags, operands


def _mode(node):
    """Return the fixed permission string for ``node``."""
    return DIR_MODE if node.is_dir else FILE_MODE


def _size(node):
    """Return the size shown by ``ls -l`` for ``node``."""
    return DIR_SIZE if node.is_dir else node.size


def _long_lines(entries):
    """Format ``(name, node)`` pairs as ``ls -l`` lines."""
    if not entries:
        return []
    rows = [(_mode(node), node.owner, node.group, str(_size(node)), name)
            for name, node in entries]
    owner_w = max(len(row[1]) for row in rows)
    group_w = max(len(row[2]) for row in rows)
    size_w = max(len(row[3]) for row in rows)
    return [f"{mode} {owner:<{owner_w}} {group:<{group_w}} "
            f"{size:>{size_w}} {name}"
            for mode, owner, group, size, name in rows]


def _dir_entries(node, flags):
    """Return the sorted visible ``(name, child)`` pairs of a directory."""
    items = node.children.items()
    if "a" not in flags:
        items = [item for item in items
                 if not item[0].startswith(HIDDEN_PREFIX)]
    return sorted(items, key=lambda item: item[0].lower())


def _ls_block(path, node, flags, header):
    """Return the text listing one ``ls`` operand."""
    entries = _dir_entries(node, flags) if node.is_dir else [(path, node)]
    if "l" in flags:
        lines = _long_lines(entries)
    else:
        names = COLUMN_SEPARATOR.join(name for name, _ in entries)
        lines = [names] if names else []
    if header and node.is_dir:
        lines.insert(0, f"{path}:")
    return "\n".join(lines)


def cmd_ls(shell, args):
    """List files: ``ls [-l] [-a] [PATH...]``."""
    flags, operands = parse_options(args, LS_FLAGS)
    targets = operands or [CURRENT_DIR]
    blocks, errors = [], []
    for path in targets:
        try:
            node, _ = shell.vfs.lookup(path, shell.cwd)
        except VfsError as exc:
            errors.append(f"cannot access '{path}': {exc}")
            continue
        block = _ls_block(path, node, flags, bool(targets[1:]))
        if block:
            blocks.append(block)
    output = BLOCK_SEPARATOR.join(blocks)
    if errors:
        raise CommandError("\n".join(errors), output)
    return output


def cmd_cd(shell, args):
    """Change the current directory: ``cd [DIR]`` (no ``DIR`` means ``/``)."""
    if args[1:]:
        raise CommandError("too many arguments")
    target = args[0] if args else SEPARATOR
    try:
        node, names = shell.vfs.lookup(target, shell.cwd)
    except VfsError as exc:
        raise CommandError(f"{target}: {exc}") from None
    if not node.is_dir:
        raise CommandError(f"{target}: Not a directory")
    shell.cwd = names
    return ""


def cmd_echo(shell, args):
    """Print the arguments separated by single spaces."""
    return " ".join(args)


def _read_text(shell, path):
    """Return the content of file ``path`` as printable text.

    Undecodable bytes and control characters (except tab and newline)
    are replaced so that binary data cannot break the display.
    """
    node, _ = shell.vfs.lookup(path, shell.cwd)
    if node.is_dir:
        raise VfsError("Is a directory")
    text = node.data.decode(TEXT_ENCODING, errors="replace")
    return CONTROL_CHARS.sub(REPLACEMENT, text.replace("\r\n", "\n"))


def cmd_cat(shell, args):
    """Print the content of files: ``cat FILE...``."""
    if not args:
        raise CommandError("missing file operand")
    parts, errors = [], []
    for path in args:
        try:
            parts.append(_read_text(shell, path))
        except VfsError as exc:
            errors.append(f"{path}: {exc}")
    output = "".join(parts)
    if errors:
        raise CommandError("\n".join(errors), output)
    return output


def cmd_exit(shell, args):
    """Stop the interpreter. Accepts no arguments."""
    if args:
        raise CommandError("too many arguments")
    shell.running = False
    return ""


def cmd_vfs_save(shell, args):
    """Save the current VFS state to a disk file in the XML format."""
    if not args:
        raise CommandError("missing file operand")
    if args[1:]:
        raise CommandError("too many arguments")
    try:
        shell.vfs.save(args[0])
    except VfsError as exc:
        raise CommandError(str(exc)) from None
    return f"VFS saved to {args[0]}"


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "echo": cmd_echo,
    "cat": cmd_cat,
    "exit": cmd_exit,
    "vfs-save": cmd_vfs_save,
}
