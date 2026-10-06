"""Shell core: line parsing, command dispatch and error reporting."""
import shlex
from dataclasses import dataclass

from .commands import COMMANDS, CommandError
from .vfs import Vfs

DEFAULT_PROMPT = "{vfs}:{cwd}$ "
ROOT_PATH = "/"


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
    """Interpreter state: VFS name, prompt, directory and run flag."""

    def __init__(self, vfs=None, prompt=DEFAULT_PROMPT):
        """Create a shell working on ``vfs`` (empty by default)."""
        self.vfs = vfs if vfs is not None else Vfs.empty()
        self.prompt = prompt
        self.cwd = []
        self.running = True

    @property
    def vfs_name(self):
        """Return the name of the mounted VFS."""
        return self.vfs.name

    def cwd_text(self):
        """Return the current directory as an absolute path."""
        return ROOT_PATH + "/".join(self.cwd)

    def prompt_text(self):
        """Return the prompt; ``{vfs}`` and ``{cwd}`` are substituted."""
        text = self.prompt.replace("{vfs}", self.vfs_name)
        return text.replace("{cwd}", self.cwd_text())

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
