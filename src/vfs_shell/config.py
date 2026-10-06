"""Command-line parameters of the emulator."""
import argparse
from dataclasses import dataclass

from .shell import DEFAULT_PROMPT


@dataclass
class Config:
    """Parameters given at start-up."""

    vfs: str = None
    prompt: str = DEFAULT_PROMPT
    script: str = None
    headless: bool = False


def build_parser():
    """Create the argument parser of the emulator."""
    parser = argparse.ArgumentParser(
        prog="vfs_shell",
        description="Emulator of a UNIX-like shell with a virtual FS.")
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="path to the physical location of the VFS (XML file)")
    parser.add_argument(
        "--prompt", metavar="TEXT", default=DEFAULT_PROMPT,
        help="input prompt; {vfs} and {cwd} are substituted")
    parser.add_argument(
        "--script", metavar="PATH",
        help="path to the startup script with emulator commands")
    parser.add_argument(
        "--headless", action="store_true",
        help="run without GUI: print the dialog to the console")
    return parser


def parse_args(argv=None):
    """Parse ``argv`` (default: ``sys.argv``) into a :class:`Config`."""
    values = build_parser().parse_args(argv)
    return Config(vfs=values.vfs, prompt=values.prompt,
                  script=values.script, headless=values.headless)


def debug_lines(config):
    """Return debug lines listing every parameter of ``config``."""
    return [
        "[debug] параметры запуска:",
        f"[debug]   vfs      = {config.vfs!r}",
        f"[debug]   prompt   = {config.prompt!r}",
        f"[debug]   script   = {config.script!r}",
        f"[debug]   headless = {config.headless!r}",
    ]
