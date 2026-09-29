"""Command-line commands of `browser.py`, one module per command.

Every command loads the PAZ folder through the same `Api` the GUI uses
(`session.open_session`), so what a command prints is what the app shows.
Progress and errors go to stderr, results to stdout, so output can be piped.
"""
