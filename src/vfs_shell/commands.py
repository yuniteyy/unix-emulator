"""Built-in commands.

Every command is a function ``(shell, args) -> str`` returning its output.
Failures are reported by raising :class:`CommandError`.
"""
from .vfs import VfsError


class CommandError(Exception):
    """User-visible command failure that may carry partial output."""

    def __init__(self, message, output=""):
        """Store the error ``message`` and the output produced so far."""
        super().__init__(message)
        self.output = output


def _stub(name, args):
    """Describe a stub call: its name and the arguments received."""
    return f"name: {name}, args: {args}"


def cmd_ls(shell, args):
    """Stub of ``ls``: print the command name and its arguments."""
    return _stub("ls", args)


def cmd_cd(shell, args):
    """Stub of ``cd``: print the command name and its arguments."""
    return _stub("cd", args)


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
    "exit": cmd_exit,
    "vfs-save": cmd_vfs_save,
}
