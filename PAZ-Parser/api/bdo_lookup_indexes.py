"""The lookup indexes from the app core's side: the fingerprint of their disk cache.

Which indexes exist and how each is built lives with the handlers, in
`_common/lookup_builders.py`, so a new index changes no core module.
"""

from __future__ import annotations

from _common.lookup_builders import build_indexes
from paz.bdo_index_cache import builder_fingerprint


def index_fingerprint() -> str:
    """Hash of the code that decides what the indexes contain.

    Starts from `build_indexes`, whose module imports every builder, and
    follows their project imports.
    """
    return builder_fingerprint([build_indexes])
