"""Tkinter front-end: an output area and a one-line input field."""
import tkinter as tk
from tkinter import scrolledtext

from .history import InputHistory

TITLE_TEMPLATE = "Эмулятор - [{vfs}]"
FONT = ("Courier New", 11)
COLOR_BG = "#1e1e1e"
COLOR_FG = "#d4d4d4"
END = "end"


class ShellWindow:
    """Terminal-like window bound to a :class:`vfs_shell.shell.Shell`."""

    def __init__(self, shell, root=None):
        """Build the window for ``shell`` inside ``root`` (or a new Tk)."""
        self.shell = shell
        self.root = root or tk.Tk()
        self.history = InputHistory()
        self._build_widgets()

    def _build_widgets(self):
        """Create the output area, prompt label and input field."""
        self.root.title(TITLE_TEMPLATE.format(vfs=self.shell.vfs_name))
        self.output = scrolledtext.ScrolledText(
            self.root, state="disabled", font=FONT,
            bg=COLOR_BG, fg=COLOR_FG, wrap="word")
        self.output.pack(fill="both", expand=True)
        bar = tk.Frame(self.root, bg=COLOR_BG)
        bar.pack(fill="x")
        self.prompt_label = tk.Label(
            bar, font=FONT, bg=COLOR_BG, fg=COLOR_FG,
            text=self.shell.prompt_text())
        self.prompt_label.pack(side="left")
        self.entry = tk.Entry(
            bar, font=FONT, bg=COLOR_BG, fg=COLOR_FG,
            insertbackground=COLOR_FG, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True)
        self._bind_keys()
        self.entry.focus_set()

    def _bind_keys(self):
        """Attach the Enter, Up and Down handlers to the input field."""
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>", self._on_up)
        self.entry.bind("<Down>", self._on_down)

    def write(self, text):
        """Append ``text`` and a newline to the output area."""
        self.output.configure(state="normal")
        self.output.insert(END, text + "\n")
        self.output.configure(state="disabled")
        self.output.see(END)

    def submit(self, line):
        """Echo ``line`` like a terminal, run it and show the result."""
        self.write(self.shell.prompt_text() + line)
        result = self.shell.execute(line)
        for text in result.lines():
            self.write(text)
        self.prompt_label.configure(text=self.shell.prompt_text())
        if not self.shell.running:
            self.root.destroy()

    def _on_enter(self, _event):
        """Run the typed line and clear the input field."""
        line = self.entry.get()
        self.entry.delete(0, END)
        if line.strip():
            self.history.add(line)
        self.submit(line)

    def _set_entry(self, text):
        """Replace the content of the input field with ``text``."""
        self.entry.delete(0, END)
        self.entry.insert(0, text)

    def _on_up(self, _event):
        """Show the previous history line."""
        self._set_entry(self.history.previous())

    def _on_down(self, _event):
        """Show the next history line."""
        self._set_entry(self.history.following())


def run_gui(shell):
    """Open the window for ``shell`` and enter the Tk main loop."""
    window = ShellWindow(shell)
    window.root.mainloop()
