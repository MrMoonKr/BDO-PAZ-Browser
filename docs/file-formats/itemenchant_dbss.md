# `itemenchant.dbss` Format

## Purpose

The per-item enchant table, and in practice the closest thing the client data has
to a master item table. It holds one variable-length block per
(item, enchant level) pair, keyed through a required offset companion. Each block
carries the item's **icon path as an inline string**, which makes this file the
authoritative item ID to icon mapping, the one thing that cannot be derived from
an item ID alone. Items that place or summon something (furniture, fences,
crops, pets) also name that character, which links them to
`characterobject.dbss` and `characterstatic.dbss`.

At roughly 194 MB it is the largest file in the game data.

Example:

```text
item 24626 (King Clam Wall Ornament)
  -> New_Icon/03_ETC/06_Housing/InHouse_Cultivate_Sea_Clam_01_Wall.dds
item 58011 ([Event] Fence)
  -> New_Icon/03_ETC/06_Housing/00058003.dds
  -> places character 2053 ([Event] Fence)
```

---

## Companion Files

| File                      | Required | Role                                          |
| ------------------------- | -------- | --------------------------------------------- |
| `itemenchantoffset.dbss`  | Required | Maps the packed key to a block offset and size |
| `languagedata_en.loc`     | Optional | Item name and description for the item ID (`str_type=0`, `str_id4` 0 and 1) |
| `skill.dbss`              | Optional | The buffs of `skill_key_1` and `skill_key_2`, through the `SKILL_BUFFS` lookup index |

All multi-byte values are little-endian.

---

## File Layout

| Offset  | Type | Field   | Notes                                                |
| ------- | ---- | ------- | ---------------------------------------------------- |
| `+0x00` | u32  | count   | Record count, matching the companion; observed 169,965 before 2026-09-27, 170,322 after |
| `+0x04` | ...  | blocks  | Variable-length blocks, contiguous, in key order      |

Blocks are addressed only through the companion. The first block starts at byte
`4`, and the last block ends exactly at end of file (203,540,909 bytes observed),
so the block stream is gap-free. The 2026-09-27 client file is 203,937,007 bytes.

---

## `itemenchantoffset.dbss`

| Offset  | Type  | Field  | Notes                            |
| ------- | ----- | ------ | -------------------------------- |
| `+0x00` | u8[4] | magic  | `PABR` (ASCII)                   |
| `+0x04` | u32   | count  | Number of rows; observed 169,965 before 2026-09-27, 170,322 after |
| `+0x08` | ...   | rows   | `count` × 12-byte rows           |
| end-12  | ...   | trailer | 12-byte file trailer            |

### Row (12 bytes)

| Offset  | Type | Field       | Notes                                        |
| ------- | ---- | ----------- | -------------------------------------------- |
| `+0x00` | u32  | key         | Packed item ID and enchant level, see below |
| `+0x04` | u32  | data_offset | Byte offset of the block in `itemenchant.dbss` |
| `+0x08` | u32  | data_size   | Block length in bytes                        |

Rows are contiguous: `data_offset + data_size` of one row equals the next row's
`data_offset`.

### Trailer (12 bytes)

The same trailer shape used by
[fairyupgraderate.bss](fairyupgraderate_bss.md) and
[zodiacsignindex.bss](zodiacsignindex_bss.md).

| Offset  | Type | Field          | Observed  | Notes                              |
| ------- | ---- | -------------- | --------- | ---------------------------------- |
| `+0x00` | u32  | reserved_a     | 0         | Always zero                        |
| `+0x04` | u32  | end_of_rows    | 2,039,588 | Equals `8 + count × 12` (2,043,872 after 2026-09-27) |
| `+0x08` | u32  | reserved_b     | 0         | Always zero                        |

---

## Key Packing

```text
key = (enchant_level << 24) | item_id
```

| Field         | Bits   | Observed range |
| ------------- | ------ | -------------- |
| enchant_level | 31..24 | 0-25           |
| item_id       | 23..0  | 1-1,000,827 (1-1,000,841 after 2026-09-27) |

The low 24 bits are confirmed item IDs: 69,292 of them match a name in
`languagedata_en.loc`. The high byte is the enhancement level. Every item has
one record per level from `0` up to its maximum, with no gaps, and the maximum
matches the item's enhancement range in game. Level `0` is the base item, which
is all the icon index needs. Earlier versions of this doc called the field
`key_variant`, because 25 looked wider than BDO's enhancement range.

Per-item maximum on the 2026-09-27 client, checked in game (2026-09-28):

| Max | Items  | Example                                   | In game                     |
| --- | ------ | ----------------------------------------- | --------------------------- |
| 0   | 60,873 | Non-enhanceable items                     | -                           |
| 1   | 4,147  | Basteer Longsword (10011); 4,093 of them are Pearl Shop outfit tops (`09_Cash/01_Equip/03_Upperbody` icons) | Basteer: enhanceable, "※ Enhancement is available by using only Black Stone (Basteer)."; the level count is not shown |
| 2   | 2      | Sealed Spirit's Earring (11826)           | +1 to +2                    |
| 3   | 4      | Tears of the Wind Necklace (11654)        | +1 to +3                    |
| 5   | 251    | Deboreka Earring (11882), Sicil's Necklace (11625) | +1 to +5 (PRI to PEN) |
| 7   | 50     | Ultimate Basteer Longsword (10070)        | +1 to +7                    |
| 10  | 518    | Kharazad Necklace (11697), Sovereign Scythe (747402) | +1 to +10        |
| 15  | 105    | Adventurer's Longsword (10073)            | +1 to +15                   |
| 20  | 4,167  | Kzarka Gauntlet (11210), Blackstar Greatsword (731101) | +1 to +15, then PRI to PEN |
| 25  | 167    | Tuvala Helmet (695105), Tuvala Noble Sword (695135) | +1 to +15, PRI to PEN, then VI to X |

---

## Block Structure

Only the item ID, the placed character and the strings are confirmed. A block
opens with the item ID and ends with a large run of enchant-related numeric
fields that are not yet decoded.

| Offset  | Type | Field    | Notes                                    |
| ------- | ---- | -------- | ---------------------------------------- |
| `+0x00` | u32  | item_id      | Repeats the item ID from the key                             |
| `+0x04` | u8   | item_type    | Tooltip class (`EItemType`), see below                       |
| `+0x05` | u8   | category     | Item classification                                          |
| `+0x06` | u8   | grade        | `0` to `5`, the item name colour, see below                  |
| `+0x07` | ...  | unknown      | Numeric fields                                               |
| `+0x3F` | i32  | weight       | Divide by 10,000 for LT                                      |
| `+0x43` | ...  | unknown      | Numeric fields                                               |
| `+0x6E` | i64  | buy_price    |                                                              |
| `+0x76` | i64  | sell_price   |                                                              |
| `+0x7E` | ...  | unknown      | Numeric fields                                               |
| `+0xAA` | u16  | character_id | Character the item places or summons; `0` when none. See below |
| `+0xAC` | u8   | dye_parts    | `0` on all 3,960 object links; across base items `0` (61,650), `1` (4,786), `2` (2,165), `5` (1,052), `10` (218) |
| `+0xAD` | u8   | unknown_ad   | `0` in 69,875 base items                                     |
| `+0xAE` | ...  | unknown      | Numeric fields                                               |
| `+0xCC` | u32  | skill_key_1  | Skill a consumable casts, a [`skill.dbss`](skill_dbss.md) key; its `buff_ids` are the item's buffs; `0` when none |
| `+0xD0` | u32  | skill_key_2  | Second skill, used by composite meals; `0` when none          |
| `+0xD4` | ...  | unknown      | Numeric fields up to the first string                        |

Checked on Balacs Lunchbox (`9359`): `item_type` 2, `grade` 3, `weight`
1,000 (0.1 LT), `buy_price` 38,775, `sell_price` 1,551, and a non-zero
`skill_key_1`.

The skill keys are fixed fields, read at `+0xCC` and `+0xD0` whatever the
strings hold. Every enchant level of an item stores the same keys as its base
block (client 3458). Simple Cron Meal (`9692`) uses both: the buffs of its
two skills give the effects its tooltip lists on bdocodex (Combat EXP +20%,
Skill EXP +10%, Max HP +150, Back Attack and Critical Hit Extra Damage +5%,
Heatstroke/Hypothermia Resistance +10% and more). A few items store `1`
(skill 0 level 1), which has no `skill.dbss` record and links nothing.

The fixed part of this layout, and the names of `item_type`, `category`,
`grade`, `dye_parts` and the skill keys, come from
[bdo-data-extractor](https://github.com/iDevelopThings/bdo-data-extractor/blob/HEAD/FORMATS.md),
which decodes the whole header from `+0x00` to `+0xD4` (class mask, stack
size, market category, durability and more). The offsets above were checked
against this file; the names `category` and `dye_parts` were not. Its
`dyeable` flag at `+0xA8` does not line up cleanly with `dye_parts`: 2,017
items have dye parts with `dyeable` at `0`, and 16 store `3` there.

#### `grade`

The colour the game draws the item name in. The colours are the ones
`PAGlobalFunc_SetItemTextColorByItemGrade` in the client Lua
(`include/global_util`) sets, in this order; the same file wraps a name in
the grade's `<PAColor>` tag for text. Grade 5 purple is confirmed in game.
Other tables read the grade from the `ITEM_GRADE` lookup index. Counts are
base items on client 3458.

| Value | Colour       | Example                         | Base items |
| ----: | ------------ | ------------------------------- | ---------: |
| 0     | `0xFFC4C4C4` | Memory Fragment                 | 7,334      |
| 1     | `0xFF83A543` | Faint Dream Box                 | 4,182      |
| 2     | `0xFF438DCC` | Caphras Stone                   | 6,904      |
| 3     | `0xFFF5BA3A` | Kzarka Longsword, Cron Stone    | 17,155     |
| 4     | `0xFFD05D48` | Blackstar Longsword, Black Stone | 34,433    |
| 5     | `0xFFA070EF` | Sovereign Longsword, Kharazad Earring | 276  |

#### `item_type`

`EItemType`, which selects the tooltip label. Names from bdo-data-extractor;
the counts are base items here.

| Value | Name         | Tooltip label       | Base items |
| ----: | ------------ | ------------------- | ---------: |
| 0     | Normal       | General             | 6,243      |
| 1     | Equip        | Equipment           | 29,763     |
| 2     | Skill        | Consumable          | 13,245     |
| 3     | Tent         | Holding Tool        | 279        |
| 4     | Installation | Installable Object  | 3,597      |
| 5     | Jewel        | Socket Item         | 565        |
| 6     | CannonBall   | Cannonball          | 22         |
| 7     | Mapae        | License             | 246        |
| 8     | Material     | Crafting Material   | 1,630      |
| 10    | ContentsEvent | Special Items      | 13,272     |

Values 11 to 20 also occur (1,092 items) and are unnamed. Every one of the
3,597 `Installation` items and the 279 `Tent` items names a placed character.
| varies  | ...  | strings      | One or two length-prefixed ASCII strings                     |
| varies  | ...  | unknown  | Remaining enchant data                   |

### Placed or summoned character

`character_id` sits in the fixed numeric part: in every block, at every level, the first string's prefix starts at `+0xF2` (242) or later (client 3458), and every block is at least 693 bytes long.

| Measure (level-0 blocks)                         | Value |
| ------------------------------------------------ | ----: |
| Characters named by at least one item            | 5,095 |
| ... that have a `characterobject.dbss` record    | 3,960 |
| ... named by exactly one item (kept as a link)   | 5,090 |
| Characters named by more than one item           |     5 |

Measured before the 2026-09-27 update. After it, 5,103 characters are named by at least one item, still 5 by more than one, so 5,098 are kept as links.

All 5,095 are `characterstatic.dbss` IDs; the ones without an object record are mostly pets.

Examples: `58001` Strong Fence Garden (item) → `2001` Strong Fence Garden; `820908` Truffle Mushroom Hypha → `1436` Truffle Mushroom Crop; `860014` [Pet] Striped Cat (Tier 3) → `9425` Cat. Of the 3,960 object links, 2,961 have identical item and character names; the rest pair a seed with its crop or a `[Guild]` item with its structure.

Character `1` is named by 120 unrelated items, so there the value is not a link. The browser keeps only characters named by exactly one item.

### Length-prefixed string

| Offset  | Type   | Field  | Notes                          |
| ------- | ------ | ------ | ------------------------------ |
| `+0x00` | u32    | length | Byte length of `text`          |
| `+0x04` | u32    | zero   | Always 0 in observed data      |
| `+0x08` | char[] | text   | ASCII, not null-terminated     |

The string does **not** sit at a fixed block offset, 47 distinct offsets were
observed across a 400-block sample, so a parser must scan for the
`(length, 0, ascii × length)` shape rather than seek a constant. The browser
starts the scan at `+0xD4`, where the fixed fields end.

A block holds at most two strings:

| Position | Content                                                        |
| -------- | -------------------------------------------------------------- |
| first    | Icon path, relative to `ui_texture/icon/`                       |
| second   | Optional `second_string` such as `ITEM_BIC_HIT_1`; absent in most blocks, meaning unconfirmed |

**The first string is always the icon path.** In a 400-block sample the length
prefix matched the string length 400 out of 400 times.

### Resolving the icon path

Stored paths always begin with `New_Icon/`, so the PAZ path is the stored value
prefixed with `ui_texture/icon/`, matched case-insensitively:

```text
New_Icon/03_ETC/06_Housing/InHouse_Cultivate_Sea_Clam_01_Wall.dds
  -> ui_texture/icon/new_icon/03_etc/06_housing/inhouse_cultivate_sea_clam_01_wall.dds
```

---

## Icon Coverage

Measured against the 73,947 item IDs in `languagedata_en.loc` (`str_type=0`):

| Measure                                        | Value          |
| ---------------------------------------------- | -------------- |
| Items with a level-0 record                     | 69,292 (93.7%) |
| Sampled icon paths resolving to a real PAZ file | 99.3%          |
| Level-0 records carrying an icon path           | 100%           |

For comparison, deriving `product_icon_png/{item_id:08d}.png` from the ID alone
reaches only 14.9% of items, and indexing every ID-named icon under
`ui_texture/icon` by basename reaches 28.8%. The icon path stored here is the
only approach that covers items whose icon is named after a 3D asset
(furniture) or keyed by a cash-product ID rather than the item ID.

---

## Suggested UI Layout

One row per item, read from its level-0 block. Higher levels only feed Max Level: most repeat the base icon, and nothing else in them is decoded yet. The 551 items of [specialenchantitem.bss](specialenchantitem_bss.md) are the exception: their level blocks store the icon of that level, which differs from the base icon in 1,356 of their 3,081 keys on client 3458, and that file holds the same paths in fixed rows. The offset table keeps one row per key, with an Enchant Level column.

| Column        | Type | Notes                                             |
| ------------- | ---- | ------------------------------------------------- |
| Item ID       | num  | `item_id` from the key                            |
| Icon          | text | First block string, prefixed `ui_texture/icon/`   |
| Item          | text | LOC `str_type=0`, `str_id1=item_id`, in its `grade` colour |
| Description   | text | LOC `str_type=0`, `str_id4=1`, in its game colours, on one line and cut; the file stores no description. 61,837 of 70,284 items have one on client 3458 |
| Max Level     | num  | Highest `enchant_level` among the item's keys; `0` when it cannot be enhanced |
| Object ID     | num  | `character_id` of the placed object or summoned pet; dash when `0` |
| Object        | text | LOC `str_type=6`, `str_id1=character_id`          |
| Buffs         | list | Buffs of `skill_key_1`, then `skill_key_2` (`SKILL_BUFFS` lookup index), each once, with buff icon and the first line of its LOC type `5` text in its game colours; sorts by count |

---

## Notes

- `itemenchantbackendtest.dbss` (73 MB) contains the identical set of 169,962
  icon path references and 21,768 unique paths, it looks like a test copy and
  adds nothing. `itemenchantbackend.dbss` (121 MB) contains no icon paths at all.
- 17 `gamecommondata` tables store inline icon paths this way. After this file
  the largest are `cashproduct.dbss` (14,750 unique paths, keyed by cash product
  ID rather than item ID), `quest.dbss` (6,366) and `skilltype.dbss` (3,530).
- The icon path is why ~14,400 ID-named icons match no LOC item name: cash-shop
  items reference a product-ID icon such as
  `Icon/New_Icon/09_Cash/03_Product/00105099.dds` while the item itself is a
  different ID. Those icons are reachable only through a stored path.
- Reading the whole file to build an index costs a 194 MB decompress, which is
  too slow to repeat per launch; an index built from this file should be cached
  on disk and invalidated on the PAZ meta version, the way `paz/bdo_cache.py`
  already caches the entry list.
- Blocks are contiguous and the companion is sorted by key, so a targeted lookup
  can read a single block by offset without parsing the whole file.

---

## Open Questions

### Enchant Data Fields

Only the header fields listed in Block Structure are checked here. The rest
of the header, and everything after the icon string, are not decoded in this
doc. bdo-data-extractor maps most of the header and part of the post-icon
block (market flags, enhancement group and type); those would need checking
against this file before they are documented here.

### Items Without a Record

4,655 of the 73,947 LOC item IDs have no level-0 record. Whether these are
unreleased, region-specific, or simply not enchantable is unknown, and it is
also unconfirmed whether they have an icon reachable some other way.

### Second Block String

The optional second string (`second_string` in the parser; it has no fixed
offset, so it cannot be named `unknown_<offset>`) looks like an effect or sound tag
(`ITEM_BIC_HIT_1` through `ITEM_BIC_HIT_4` were observed) and appeared in 46 of
350 sampled blocks, all of them weapons or armour. What consumes it, and whether
other tag families exist, is unconfirmed. Earlier versions called it
`effect_tag` and showed it as an Effect Tag column; it stays on the record for
search and CSV but is no longer shown.
