"""Console streams for the CLI: UTF-8 output, progress on stderr."""
from __future__ import annotations

import errno
import logging
import os
import sys


def use_utf8_stdio() -> None:
    """Write stdout and stderr as UTF-8, whatever the console code page.

    Redirected output on Windows otherwise uses the ANSI code page (cp1252),
    and the first non-ASCII path or Korean string raises UnicodeEncodeError
    halfway through the output. Streams that cannot be reconfigured (None under
    pythonw, or replaced by a test harness) are left alone.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def configure_logging() -> None:
    """Send warnings from the loading code (a failed index build) to stderr."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def progress(message: str) -> None:
    """A status line that stays out of piped output."""
    print(message, file=sys.stderr, flush=True)


def error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr, flush=True)


def write_raw(text: str) -> None:
    """Write text to stdout without newline translation.

    CSV rows already end in CRLF; the text layer on Windows would turn that
    into CR CR LF.
    """
    sys.stdout.flush()
    sys.stdout.buffer.write(text.encode("utf-8"))
    # Flushed so the result prints before the summary line on stderr.
    sys.stdout.buffer.flush()


def is_closed_pipe(ex: OSError) -> bool:
    """True when stdout's reader went away (`| head`).

    Windows reports EINVAL where other systems raise BrokenPipeError.
    """
    return isinstance(ex, BrokenPipeError) or ex.errno in (errno.EPIPE, errno.EINVAL)


def close_stdout_quietly() -> None:
    """Flush stdout; when the reader is gone, send what is left to the null device.

    Without this, Python reports the failed flush again at exit.
    """
    try:
        sys.stdout.flush()
    except OSError as ex:
        if not is_closed_pipe(ex):
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
