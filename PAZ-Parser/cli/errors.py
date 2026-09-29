from __future__ import annotations


class CliError(Exception):
    """A user-facing command failure; the message is printed without a traceback."""
