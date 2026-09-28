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
| `languagedata_en.loc`     | Optional | Item name for the item ID (`str_type=0`)      |

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
key = (key_variant << 24) | item_id
```

| Field       | Bits   | Observed range |
| ----------- | ------ | -------------- |
| key_variant | 31..24 | 0-25           |
| item_id     | 23..0  | 1-1,000,827 (1-1,000,841 after 2026-09-27) |

The low 24 bits are confirmed item IDs: 69,292 of them match a name in
`languagedata_en.loc`. **What the high byte means is not confirmed.** Variant `0`
is the base item, with exactly one record per item ID, which is all the icon
index needs.

| Key group     | Rows    | Meaning                     |
| ------------- | ------- | --------------------------- |
| variant 0     | 69,954  | One per base item           |
| variants 1-25 | 100,011 | Unconfirmed, see the open question |

Row counts are from the pre-2026-09-27 fixture. The 2026-09-27 client has 70,284 variant-0 rows and 100,038 rows with variants 1-25; the variant range is still 0-25.

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
| `+0x06` | u8   | grade        | `0` to `5`                                                   |
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
| `+0xCC` | u32  | skill_key_1  | Skill a consumable casts; see bdo-data-extractor below       |
| `+0xD0` | u32  | skill_key_2  | Second skill, used by composite meals                        |
| `+0xD4` | ...  | unknown      | Numeric fields up to the first string                        |

Checked on Balacs Lunchbox (`9359`): `item_type` 2, `grade` 3, `weight`
1,000 (0.1 LT), `buy_price` 38,775, `sell_price` 1,551, and a non-zero
`skill_key_1`.

The fixed part of this layout, and the names of `item_type`, `category`,
`grade`, `dye_parts` and the skill keys, come from
[bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor/blob/HEAD/FORMATS.md),
which decodes the whole header from `+0x00` to `+0xD4` (class mask, stack
size, market category, durability and more). The offsets above were checked
against this file; the names `category` and `dye_parts` were not. Its
`dyeable` flag at `+0xA8` does not line up cleanly with `dye_parts`: 2,017
items have dye parts with `dyeable` at `0`, and 16 store `3` there.

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

`character_id` sits in the fixed numeric part: in every base-item (variant 0) block the first string starts at `+0xB4` (180) or later, and every block is at least 693 bytes long.

| Measure (variant-0 blocks)                       | Value |
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
`(length, 0, ascii × length)` shape rather than seek a constant.

A block holds at most two strings:

| Position | Content                                                        |
| -------- | -------------------------------------------------------------- |
| first    | Icon path, relative to `ui_texture/icon/`                       |
| second   | Optional effect tag such as `ITEM_BIC_HIT_1`; absent in most blocks |

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

| Column        | Type | Notes                                             |
| ------------- | ---- | ------------------------------------------------- |
| Item ID       | num  | `item_id` from the key                            |
| Icon          | text | First block string, prefixed `ui_texture/icon/`   |
| Item          | text | LOC `str_type=0`, `str_id1=item_id`               |
| Object ID     | num  | `character_id` of the placed object or summoned pet; dash when `0` |
| Object        | text | LOC `str_type=6`, `str_id1=character_id`          |
| Effect Tag    | text | Second block string when present                  |

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

The optional second string looks like an effect or sound tag
(`ITEM_BIC_HIT_1` through `ITEM_BIC_HIT_4` were observed) and appeared in 46 of
350 sampled blocks, all of them weapons or armour. What consumes it, and whether
other tag families exist, is unconfirmed.

### Key Variant Meaning

The high byte of the key runs 0-25. It was first read as an enchant level, since
the file is named `itemenchant`, but that does not hold up: BDO's visible
enchant range is narrower than 25, and the values do not line up with enchant
levels in the app. Whether the byte is an enchant step, a different upgrade
track, a variant index, or something else is unresolved, so the field is named
`key_variant` and is not displayed. Variant `0` is reliably the base item, which
is the only property the icon index depends on.
