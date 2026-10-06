"""Startup scripts: loading and step-by-step playback."""
from dataclasses import dataclass

from .shell import Result

COMMENT_PREFIX = "#"
SKIP_NOTE = "[script] строка {number}: ошибка, строка пропущена"


class ScriptError(Exception):
    """The startup script cannot be read."""


@dataclass
class Step:
    """One executed line of a script together with its outcome."""

    number: int
    prompt: str
    line: str
    result: Result

    def display_lines(self):
        """Return the lines imitating the user dialog for this step."""
        lines = [self.prompt + self.line]
        lines.extend(self.result.lines())
        if self.result.is_error:
            lines.append(SKIP_NOTE.format(number=self.number))
        return lines


def load_script(path):
    """Read the script ``path`` and return its lines."""
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return handle.read().splitlines()
    except FileNotFoundError:
        raise ScriptError(f"script not found: {path}") from None
    except UnicodeDecodeError:
        raise ScriptError(f"script is not UTF-8 text: {path}") from None
    except OSError as exc:
        raise ScriptError(f"cannot read {path}: {exc.strerror}") from None


def play(shell, lines):
    """Execute ``lines`` one by one, yielding a :class:`Step` for each.

    Blank lines are skipped, comments are only echoed, erroneous lines
    are reported and skipped. ``exit`` ends the playback.
    """
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        prompt = shell.prompt_text()
        if line.lstrip().startswith(COMMENT_PREFIX):
            yield Step(number, prompt, line, Result())
            continue
        yield Step(number, prompt, line, shell.execute(line))
        if not shell.running:
            return
