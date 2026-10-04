"""Navigation through previously entered lines (Up/Down keys)."""

STEP = 1


class InputHistory:
    """Remember entered lines and walk through them."""

    def __init__(self):
        """Create an empty history."""
        self.items = []
        self.pos = 0

    def add(self, line):
        """Append ``line`` and move the cursor past the last item."""
        self.items.append(line)
        self.pos = len(self.items)

    def current(self):
        """Return the line under the cursor or an empty string."""
        if self.pos < len(self.items):
            return self.items[self.pos]
        return ""

    def previous(self):
        """Move one line back and return it."""
        if self.pos:
            self.pos -= STEP
        return self.current()

    def following(self):
        """Move one line forward and return it."""
        if self.pos < len(self.items):
            self.pos += STEP
        return self.current()
