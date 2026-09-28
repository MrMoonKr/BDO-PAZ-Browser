# `stringtable.bss` Format

## Purpose

The Korean source of the client's keyed UI strings. Each row pairs a string key
(`LUA_WIDGET_TOWNNPCNAVI_NPCTYPETEXT_6`) with its Korean text and a 32-bit key
hash. The hash is the LOC type `37` `str_id1`, so this file is how a key the
client scripts use turns into the translated text in `languagedata_*.loc`.

```text
GAME  0x4D282741  LUA_WIDGET_TOWNNPCNAVI_NPCTYPETEXT_6  "창고"
      -> LOC type 37, str_id1=0x4D282741, str_id2=1  "Storage"
```

---

## Companion Files

| File                  | Required | Role                                                       |
| --------------------- | -------- | ---------------------------------------------------------- |
| `languagedata_en.loc` | Optional | Translated text, type `37` keyed by the row hash and sheet |

All multi-byte values are little-endian unless noted otherwise.

---

## File Layout

A PABR file of eight sheets, followed by the same counted string table and
8-byte trailer as [`npcsimply.bss`](npcsimply_bss.md#string-pool). Every
string in the table is UTF-16LE (`is_wide=1`).

| Offset  | Type    | Field              | Notes                                                        |
| ------- | ------- | ------------------ | ------------------------------------------------------------ |
| `+0x00` | char[4] | magic              | ASCII `PABR`                                                 |
| `+0x04` | u32     | sheet_count        | `8` on client 3458                                           |
| `+0x08` | sheet[] | sheets             | Sheets back to back, see below                               |
| varies  | table   | string_table       | Counted string table; `95,195` strings on client 3458        |
| EOF - 8 | u32     | string_table_start | Where the last sheet ends (`0xC6DD8` on client 3458)         |
| EOF - 4 | u32     | zero               | Always `0`                                                   |

---

## Record Structure

### Sheet Header (12 bytes)

| Offset  | Type | Field      | Notes                                                        |
| ------- | ---- | ---------- | ------------------------------------------------------------ |
| `+0x00` | u32  | sheet_hash | Hash of the sheet name; same hash family as `key_hash`       |
| `+0x04` | u32  | name_ref   | String table index of the sheet name (`GAME`, `RESOURCE`, ...) |
| `+0x08` | u32  | row_count  | Number of 16-byte rows that follow                           |

### String Row (16 bytes, repeated `row_count` times)

| Offset  | Type | Field     | Notes                                                              |
| ------- | ---- | --------- | ------------------------------------------------------------------ |
| `+0x00` | u32  | key_hash  | Hash of the key string; the LOC type `37` `str_id1`                 |
| `+0x04` | u32  | key_ref   | String table index of the key, e.g. `NPCSHOP_BUY`                  |
| `+0x08` | u32  | value_ref | String table index of the Korean text; never the empty string       |
| `+0x0C` | u32  | zero      | Always `0`                                                         |

Rows are not sorted by hash or key. The string table is interned: each string
is stored once, in the order the sheets first use it (sheet name, then key
and value of each row), and later uses point back. No key repeats within a
sheet; 6,553 values reuse an earlier text such as `"확인"`.

---

## Sheets

The sheet order is fixed on client 3458. `loc str_id2` is the LOC type `37`
`str_id2` that every LOC row of that sheet's keys carries.

| # | Name          | Hash         | Rows   | `loc str_id2` | Holds                                                      |
| - | ------------- | ------------ | ------ | ------------- | ---------------------------------------------------------- |
| 0 | `GAME`        | `0xBDC20727` | 22,936 | `1`           | Lua UI strings (`LUA_*`, `WEBHELPER_*`), labels and tooltips |
| 1 | `SymbolNo`    | `0xA9B8EA3C` | 4,529  | `6`           | Server error and result messages (`eErrNo*`)               |
| 2 | `IMAGESLIDE`  | `0x8AD0A01B` | 204    | `7`           | Image slide subtitles (`SEQUENCE_SUBTITLE_IMAGE_SLIDE_*`)  |
| 3 | `ACTIONCHART` | `0x138A8C63` | 2,000  | `3`           | Speech bubbles and action lines (`Bubble_*`, `Trade_*`)     |
| 4 | `RESOURCE`    | `0x9C44332D` | 9,525  | `2`           | UI panel resources (`PANEL_*`)                             |
| 5 | `CUTSCENE`    | `0x08342431` | 8,564  | `0`           | Cutscene subtitles (`CS_*`)                                |
| 6 | `TOOL`        | `0xE09F9402` | 785    | `4`           | Enum labels (`eSymNo*`), e.g. chat types, log reasons      |
| 7 | `WEB`         | `0xA5AA1B9E` | 2,360  | `5`           | In-game web page strings (`WEB_*`)                         |

This settles which LOC type `37` `str_id2` is which sheet (the old
"Type 37 sheet names" question in
[`languagedata_loc.md`](languagedata_loc.md)).

---

## LOC Join

Look up a key's translated text as LOC type `37`, `str_id1 = key_hash`,
`str_id2 = ` the sheet's `loc str_id2`, `str_id3 = 0`, `str_id4 = 0`.

- 50,779 of the 50,903 rows have a LOC row on client 3458. The other 124
  (62 `GAME`, 33 `CUTSCENE`, 17 `RESOURCE`, 12 `SymbolNo`) have Korean text
  only; they read like newer content not yet translated, so fall back to
  the Korean `value_ref` text.
- 44 keys sit in two sheets (`NPCSHOP_BUY` in `GAME` and `RESOURCE`). Both
  rows carry the same hash and share the key string, and LOC keeps them
  apart by `str_id2`, which can hold different text (`ALCHEMY_MANUFACTURE_BTN_MANUFACTURE`:
  `GAME` "Start", `RESOURCE` "Start Crafting"). So the hash depends on the
  key alone, not on the sheet.
- 3,027 LOC type `37` `str_id1` values have no row here; keys dropped from
  the client whose translations LOC still carries.
- 352 LOC rows use `str_id3 = 1` as a second variant of a key, mostly
  regional URLs (`WEBHELPER_*_EN`) and date lines (`*_GMT`, `*_UTC`). 164 keys
  have only the `str_id3 = 1` row, so a lookup should try `str_id3 = 0` first
  and then `1`. `str_id4` is always `0`.

### Town NPC Navigation Types

The `GAME` sheet holds the town NPC navigation labels as
`LUA_WIDGET_TOWNNPCNAVI_NPCTYPETEXT_1` to `_39`, one per number with no gaps.
The client picks them by `SpawnType`, and the suffix is not always the
`SpawnType` value; the full mapping is the Navi label column of
[`characterspawntype.dbss` SpawnType](characterspawntype_dbss.md#spawntype).
A few, as the English LOC text:

| Key suffix | Korean        | English (LOC)              | SpawnType          |
| ---------- | ------------- | -------------------------- | ------------------ |
| `_1`       | 기술 교관     | Skill Instructor           | `SkillTrainer` (1) |
| `_6`       | 창고          | Storage                    | `WareHouse` (6)    |
| `_25`      | 아이템 거래소 | Central Market             | `ItemMarket` (25)  |
| `_35`      | 악기 상인     | Instruments                | `Instrument` (40)  |
| `_39`      | 황실제작 납품 | Imperial Crafting Delivery | `SupplyShop` (33)  |

The client reads these through `PAGetString(Defines.StringSheet_GAME, key)`,
so a script's `StringSheet_<name>` picks the sheet and with it the LOC
`str_id2`.

---

## Suggested UI Layout

One table over all sheets, one row per string row.

| Column | Type | Notes                                                                          |
| ------ | ---- | ------------------------------------------------------------------------------ |
| Sheet  | text | Sheet name from `name_ref`                                                     |
| Hash   | num  | `key_hash` as hex (`0x4D282741`), the LOC type `37` `str_id1`                   |
| Key    | text | `key_ref`                                                                      |
| Text   | text | LOC type `37` with the sheet's `str_id2` (`str_id3` 0, then 1), else the Korean `value_ref` |

---

## Notes

- Some values forward to another key rather than holding text, e.g.
  `ALCHEMY_COOK_TEXT_DESCRPITION` = `{TextBind:TEXTBIND_ALCHEMY_COOK_TEXT_DESCRPITION}`,
  and the LOC text keeps the same placeholder. Values also carry `<PAColor...>`
  tags and `{name}` placeholders.
- bdo-data-extractor names the sheets `GAME`, `RESOURCE`, `ACTIONCHART` and
  others; the names are stored in this file, so that part is now confirmed.
- Hash functions tried against `key_hash` and `sheet_hash` without a match, on
  ASCII, UTF-16LE and UTF-32LE, as is, lower and upper case, with and without
  a terminator: CRC-32 (zlib, MPEG-2, Castagnoli, no final xor), FNV-1 and
  FNV-1a, Jenkins `hashlittle` (seed 0 and `0x7C`), Murmur3 (seed 0), djb2,
  sdbm, ELF and the Java string hash. Nothing needs the function, since every
  key is stored with its hash.

---

## Open Questions

### Hash Function

`key_hash` and `sheet_hash` come from one function of the string alone (the 44
keys in two sheets share a hash), but none of the common 32-bit hashes listed
in Notes reproduce it. Knowing it would let a key that appears only in client
scripts, never in this file, be looked up in LOC directly.

### `str_id3 = 1` Variants

352 LOC type `37` rows use `str_id3 = 1`. Most look like a second,
region-specific text of the key (a newer URL, a UTC instead of GMT date line),
but some keys have only the `str_id3 = 1` row. Which condition makes the client
pick variant `1` is not known.
