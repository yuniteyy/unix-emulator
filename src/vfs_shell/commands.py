"""Built-in commands.

Every command is a function ``(shell, args) -> str`` returning its output.
Failures are reported by raising :class:`CommandError`.
"""


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


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
