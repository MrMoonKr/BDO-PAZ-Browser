"""English role labels from the town NPC navigation widget.

`panel_widget_townnpcnavi.luac` labels 35 SpawnType values with a `GAME`
sheet key, `LUA_WIDGET_TOWNNPCNAVI_NPCTYPETEXT_<n>`. Three keys of the same
family are not in its table but name three more roles (`_36` to `_38`); the
other values have no label. The key's text is LOC type 37 under its
`stringtable.bss` hash. The hash function is unknown but depends on the key
string alone, so the hashes are stored here, and a test checks them against
`stringtable.bss`.
"""

from __future__ import annotations

from typing import NamedTuple

from _bss.stringtable.parser import GAME_SHEET
from _bss.stringtable.text import ui_key_text

NAVI_KEY_PREFIX = "LUA_WIDGET_TOWNNPCNAVI_NPCTYPETEXT_"


class NaviLabel(NamedTuple):
    key_number: int
    key_hash: int

    @property
    def key(self) -> str:
        return f"{NAVI_KEY_PREFIX}{self.key_number}"


# SpawnType value -> its navi label key. Values 1 to 32 use their own number.
NAVI_LABELS: dict[int, NaviLabel] = {
    1: NaviLabel(1, 2157914725),
    2: NaviLabel(2, 2352264433),
    3: NaviLabel(3, 3325987074),
    4: NaviLabel(4, 3219162772),
    5: NaviLabel(5, 1115583420),
    6: NaviLabel(6, 1294477121),
    7: NaviLabel(7, 49211463),
    8: NaviLabel(8, 1205438008),
    9: NaviLabel(9, 4080069977),
    10: NaviLabel(10, 3121334316),
    11: NaviLabel(11, 1521154370),
    12: NaviLabel(12, 1359641139),
    13: NaviLabel(13, 2228645894),
    14: NaviLabel(14, 1194484225),
    15: NaviLabel(15, 315835027),
    16: NaviLabel(16, 991043969),
    17: NaviLabel(17, 2693412439),
    18: NaviLabel(18, 2685791670),
    19: NaviLabel(19, 2956420698),
    20: NaviLabel(20, 1329177972),
    21: NaviLabel(21, 3844698584),
    22: NaviLabel(22, 582308069),
    23: NaviLabel(23, 2448865197),
    24: NaviLabel(24, 3011467695),
    25: NaviLabel(25, 3172783243),
    26: NaviLabel(26, 3297497959),
    27: NaviLabel(27, 2703345213),
    28: NaviLabel(28, 1155601631),
    29: NaviLabel(29, 4250856223),
    30: NaviLabel(30, 4079886923),
    31: NaviLabel(31, 3924337536),
    32: NaviLabel(32, 496319309),
    33: NaviLabel(39, 3667015331),  # SupplyShop
    34: NaviLabel(34, 4246715780),  # RandomShopDay
    40: NaviLabel(35, 2501342341),  # Instrument
    # Not in the widget's table; Hiznak (47022) is titled Black Spirit's Training.
    42: NaviLabel(36, 642645702),  # TraningVehicleShop
    43: NaviLabel(37, 2947837342),  # AbyssOneEnterPosGuide, Abyssal Well
    45: NaviLabel(38, 202659900),  # ChurchBuff, Silver (Church) Buffs
}

_KEY_HASHES = {GAME_SHEET: {label.key: label.key_hash for label in NAVI_LABELS.values()}}


def navi_label(spawn_type: int) -> str:
    """The LOC text of a SpawnType's navi label, or '' without a label or LOC."""
    label = NAVI_LABELS.get(spawn_type)
    return ui_key_text(_KEY_HASHES, GAME_SHEET, label.key) if label else ""
