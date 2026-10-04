"""Town names, shared by the tables that link a town.

LOC type 17 names the towns that hire workers and keep storage: the
`plantworkerselect.bss` selection IDs, and the worker contracts and storage
expansions of `buff.dbss`. `5` is Velia, `77` Calpheon City.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_TOWN_NAME = 17


def town_name(town_key: int) -> str:
    """English name of a town, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_TOWN_NAME, town_key)
