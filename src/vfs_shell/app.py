"""Application bootstrap."""
from .gui import run_gui
from .shell import Shell

EXIT_OK = 0


def main():
    """Start the GUI emulator and return the process exit code."""
    run_gui(Shell())
    return EXIT_OK
