"""Application bootstrap: configuration, script loading, start-up."""
import sys

from .config import debug_lines, parse_args
from .gui import run_gui
from .script import ScriptError, load_script, play
from .shell import Shell
from .vfs import Vfs, VfsError

EXIT_OK = 0
EXIT_ERROR = 1


def run_headless(shell, lines, emit=print):
    """Play ``lines`` without GUI, passing every output line to ``emit``."""
    for step in play(shell, lines):
        for text in step.display_lines():
            emit(text)
    return EXIT_OK


def load_vfs(config):
    """Load the VFS named by ``--vfs`` or create an empty one."""
    if config.vfs:
        return Vfs.load(config.vfs)
    return Vfs.empty()


def read_lines(config):
    """Return script lines: from the script file or, headless, stdin."""
    if config.script:
        return load_script(config.script)
    if config.headless:
        return sys.stdin.read().splitlines()
    return []


def main(argv=None):
    """Run the emulator and return the process exit code."""
    config = parse_args(argv)
    debug = debug_lines(config)
    print("\n".join(debug))
    try:
        vfs = load_vfs(config)
        lines = read_lines(config)
    except (VfsError, ScriptError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    shell = Shell(vfs, prompt=config.prompt)
    if config.headless:
        return run_headless(shell, lines)
    steps = play(shell, lines) if config.script else None
    run_gui(shell, intro=debug, steps=steps)
    return EXIT_OK
