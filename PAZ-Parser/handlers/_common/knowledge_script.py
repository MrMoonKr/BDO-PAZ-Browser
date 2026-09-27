"""Knowledge links in inline NPC action scripts.

`characterstatic.dbss` and `npcsimply.bss` store the same action script,
usually `getknowledge(<id>);`. A few rows spell it `getKnowledge`.
"""

from __future__ import annotations

import re

_GET_KNOWLEDGE = re.compile(r"getknowledge\((\d+)\)", re.IGNORECASE)


def knowledge_id_of(script: str) -> int | None:
    """The argument of the first `getknowledge(<id>)` call, or None."""
    match = _GET_KNOWLEDGE.search(script)
    return int(match.group(1)) if match else None
