"""Human-readable durations for millisecond fields (buff durations, cooldowns)."""

from __future__ import annotations

_MS_PER_SECOND = 1000
_SECONDS_PER_HOUR = 3600
_SECONDS_PER_MINUTE = 60


def format_duration(duration_ms: int) -> str:
    """Render milliseconds as "1h 30m", "45s" or "1.5s"; empty for zero."""
    if duration_ms <= 0:
        return ""

    seconds, millis = divmod(duration_ms, _MS_PER_SECOND)
    hours, remainder = divmod(seconds, _SECONDS_PER_HOUR)
    minutes, secs = divmod(remainder, _SECONDS_PER_MINUTE)

    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or millis:
        text = f"{secs}.{millis:03d}".rstrip("0").rstrip(".")
        parts.append(f"{text}s")
    return " ".join(parts)
