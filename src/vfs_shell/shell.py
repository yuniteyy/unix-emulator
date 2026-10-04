"""Shell core: line parsing, command dispatch and error reporting."""
import shlex
from dataclasses import dataclass

from .commands import COMMANDS, CommandError

DEFAULT_VFS_NAME = "default"
DEFAULT_PROMPT = "$ "


@dataclass
class Result:
    """Outcome of executing one input line."""

    output: str = ""
    is_error: bool = False

    def lines(self):
        """Return the output as a list of display lines."""
        if not self.output:
            return []
        text = self.output
        if text.endswith("\n"):
            text = text[:-1]
        return text.split("\n")


def parse_line(line):
    """Split an input line into words; quotes group words together.

    Raises ``ValueError`` when quotes are not balanced.
    """
    return shlex.split(line)


def format_error(name, error):
    """Build the text shown for a failed command ``name``."""
    lines = [f"{name}: {text}" for text in str(error).split("\n")]
    if error.output:
        lines.insert(0, error.output.rstrip("\n"))
    return "\n".join(lines)


class Shell:
    """Interpreter state: VFS name, prompt and the running flag."""

    def __init__(self, vfs_name=DEFAULT_VFS_NAME, prompt=DEFAULT_PROMPT):
        """Create a shell with the given VFS name and prompt."""
        self.vfs_name = vfs_name
        self.prompt = prompt
        self.running = True

    def prompt_text(self):
        """Return the prompt to display before the next input."""
        return self.prompt

    def execute(self, line):
        """Run one input line and return its :class:`Result`."""
        try:
            words = parse_line(line)
        except ValueError as exc:
            return Result(f"parse error: {exc}", True)
        if not words:
            return Result()
        return self._dispatch(words[0], words[1:])

    def _dispatch(self, name, args):
        """Find the command ``name`` and run it with ``args``."""
        handler = COMMANDS.get(name)
        if handler is None:
            return Result(f"{name}: command not found", True)
        try:
            return Result(handler(self, args))
        except CommandError as exc:
            return Result(format_error(name, exc), True)
