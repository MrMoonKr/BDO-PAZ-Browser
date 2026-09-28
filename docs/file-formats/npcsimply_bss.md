# `npcsimply.bss` Format

## Purpose

Stores a compact identity table for service and story NPCs. Each row maps a character ID to its primary NPC service role, inline Korean display strings and, for most rows, a `getknowledge(<id>);` action script that links the NPC to a knowledge ID. English names come from LOC type `6`, keyed by the same character ID.

Example:

```text
character_id: 47727 -> "Jackson"  -> kind: 3 (ShopMerchant) -> name: 잭슨  -> role: <과일상인>
character_id: 47647 -> "Neoksam"  -> kind: 25 (ItemMarket)  -> role: <거래소장> -> script: getknowledge(2387);
```

---

## File Layout

Top-level PABR block with a fixed-width record table followed by an inline string pool.

| Offset  | Type     | Field       | Notes                                      |
| ------- | -------- | ----------- | ------------------------------------------ |
| `+0x00` | char[4]  | magic       | ASCII `PABR`                               |
| `+0x04` | u32      | count       | Number of NPC records (observed: 2237; older extraction: 2169) |
| `+0x08` | record[] | records     | 33-byte records repeated `count` times     |
| varies  | pool     | string_pool | Counted string table referenced by records |
| EOF - 8 | trailer  | trailer     | Offset of the string pool, see below       |

All multi-byte values are little-endian unless noted otherwise.

---

## Record Structure

### NPC Record (33 bytes, repeated `count` times)

| Offset  | Type | Field             | Notes                                                                 |
| ------- | ---- | ----------------- | --------------------------------------------------------------------- |
| `+0x00` | u16  | character_id      | Character-template key; all 2237 exist in `characterstatic.dbss`; 2198 have a LOC type `6` name, see Notes |
| `+0x02` | u8   | unknown_02        | `1` on 2074 rows; runs of sequential values on related NPCs, see Open Questions |
| `+0x03` | u8   | zero              | Always 0                                                              |
| `+0x04` | u32  | kind              | Primary `SpawnType` role; 23 observed values in the range 1-40         |
| `+0x08` | u32  | script_ref        | String-pool index of the action script; `getknowledge(...)` on 2161 rows (one spelled `getKnowledge`), the empty string on 76 |
| `+0x0C` | u32  | unknown_id        | Usually 0; non-zero on 58 rows                                         |
| `+0x10` | u16  | unknown_value     | Usually 0; non-zero on the same 58 rows as `unknown_id`                |
| `+0x12` | u16  | sentinel          | Usually `0xFFFF`; 0 on the same 58 rows as `unknown_id`                |
| `+0x14` | u8   | unknown_flag      | Usually 0; 1 on 32 rows                                                |
| `+0x15` | u32  | name_ref          | String-pool index for the Korean display name                          |
| `+0x19` | u32  | role_ref          | String-pool index for Korean role/title text; points at the empty string when absent |
| `+0x1D` | u32  | padding           | Always 0                                                              |

An earlier version of this doc read `+0x00` as a u32 `npc_id`. The high half is `unknown_02`: as a u32 only 20 of 2237 values resolve through LOC, as a u16 all of them do.

`script_ref`, `name_ref`, and `role_ref` are unaligned u32 values inside the 33-byte row. bdo-data-extractor ([asheimo/bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor)) reads the same references as aligned u32s at `+0x14` and `+0x18` shifted right by 8 (`packedNameRef`, `packedTitleRef`); both readings give the same index on every row, because the byte after each unaligned reference is always 0. `name_ref` is usually `script_ref + 1` (2045 rows).

The `script_ref` string equals the `characterstatic.dbss` action script of the same character on all 2237 rows.

### `kind` Values

`kind` is a `CppEnums.SpawnType` value, the same enum as the 46 role flags in `characterspawntype.dbss`. For all 2237 rows, the `characterspawntype.dbss` flag at index `kind` is set for the same character, so `kind` picks one primary role from that character's flags. Most common values:

| Value | Rows | SpawnType | Typical role text |
| ----- | ---- | --------- | ----------------- |
| 4     | 1197 | `ImportantNpc` | `<탐험 거점 관리>`, `<물물교환원>`, empty |
| 3     | 226  | `ShopMerchant` | `<창고지기>`, `<약초상인>` |
| 5     | 121  | `TradeMerchant` | `<무역 관리>` |
| 2     | 105  | `ItemRepairer` | `<대장장이>`, `<무기상인>` |
| 16    | 97   | `Potion` | `<잡화상인>` |
| 7     | 87   | `Stable` | `<마구간지기>` |
| 20    | 55   | `Collect` | `<재료상인>` |
| 1     | 46   | `SkillTrainer` | `<기술교관>` |
| 8     | 38   | `Wharf` | `<나루터지기>` |
| 25    | 22   | `ItemMarket` | `<거래소장>` |

### String Pool

The string pool begins immediately after the fixed record table:

```text
string_pool_offset = 0x08 + count * 33
```

Observed `string_pool_offset` is `0x12065` (older extraction: `0x117A1`).

| Offset  | Type        | Field        | Notes                                      |
| ------- | ----------- | ------------ | ------------------------------------------ |
| `+0x00` | u32         | string_count | Observed: 4746                             |
| `+0x04` | string[]    | strings      | Counted entries, indexed from 0            |

### String Entry

Every entry has a one-byte encoding flag and a u32 byte length. There is no
terminator: the next entry starts right after the payload, and the last one ends
exactly at the trailer.

| Offset  | Type  | Field       | Notes                                   |
| ------- | ----- | ----------- | --------------------------------------- |
| `+0x00` | u8    | is_wide     | `1` for UTF-16LE, `0` for UTF-8         |
| `+0x01` | u32   | byte_length | Payload length in bytes                 |
| `+0x05` | bytes | payload     | UTF-16LE when `is_wide=1`, else UTF-8   |

An earlier version of this doc read the flag as an optional marker and the
next entry's `0` flag as a terminator; both readings split the pool the same
way. `exploration.bss` uses the same entry layout, and the parser shares one
reader for both (`handlers/_common/pabr_strings.py`).

Observed pool contents: 2636 UTF-8 strings and 2110 UTF-16LE strings. The pool is not purely 8-bit: every script entry is UTF-16LE. One entry is the empty string (index 34 in the current file, index 0 in the older extraction); absent scripts and roles point at it.

### Trailer (8 bytes)

| Offset  | Type | Field              | Notes                                      |
| ------- | ---- | ------------------ | ------------------------------------------ |
| `+0x00` | u32  | string_pool_offset | Equals `0x08 + count * 33` (`0x12065`)     |
| `+0x04` | u32  | zero               | Always 0                                   |

This is the same `[string table][u32 rows_end][u32 0]` tail that `playercharacterstatic.bss` and `characterstaticoffset.dbss` carry after their rows.

---

## Suggested UI Layout

| Column       | Type | Notes                                                     |
| ------------ | ---- | --------------------------------------------------------- |
| Character ID | num  | `character_id`                                            |
| Name (EN)    | text | LOC `str_type=6`, `str_id1=character_id`                  |
| Kind         | text | `kind` shown as its `SpawnType` name                      |
| Name (KR)    | text | `name_ref`                                                |
| Role         | text | `role_ref`; Korean title/role, blank when empty           |
| Knowledge ID | num  | Parsed from `getknowledge(<id>);` in `script_ref`         |
| Script       | text | Raw script string for debugging/export                    |

---

## Notes

- The record table size is exactly `2237 * 33` bytes; fixed records end at `0x12065`, and the string pool parses exactly up to the 8-byte trailer.
- `script_ref` points to a `getknowledge(<id>);` UTF-16LE string for 2161 of 2237 records.
- `name_ref` and `role_ref` point to Korean UTF-8 strings in the same pool. Role strings are often bracketed labels such as `<과일상인>` or `<거점관리인>`.
- `unknown_id`, `unknown_value`, `sentinel=0`, and `unknown_flag=1` cluster on vendor/manager rows such as warehouse keepers, material vendors, and stable keepers.
- Every row's character has `npc_kind` low byte `2` (NPC) in `characterstatic.dbss`.
- 39 characters have no LOC type `6` name in the current English file: `47623`, `47753`, `47772` to `47807` and `61267`. The handler shows `-` for them; their Korean name stays in its own column.

---

## Open Questions

### What does `unknown_02` encode?

It is `1` on 2074 rows, `0` on 20 and `2` on 18. Most of the remaining 125 rows form runs that follow the character IDs of related NPCs: node managers `47675`-`47704` hold `34`-`63`, the five Thrones `47705`-`47709` hold `64`-`68`, and the Olvia Academy staff `62480`-`62502` hold `10`-`27` (the bulletin board `62521` holds `99`). It may be an order or group index, but nothing else confirms it.

### What are `unknown_id`, `unknown_value`, and `unknown_flag`?

These fields are mostly default but become non-zero together on 58 rows, with `unknown_flag=1` on 32 of those rows. `unknown_id` repeats across NPCs (`3001`, `16142`, `16143`, `23004`, `58008`-`58010`, `58012`, `693901` and others) with `unknown_value` between 1 and 60, which looks like an item key and count, but no item table has been joined to confirm it.

### How does the client choose `kind` among several role flags?

`kind` is always one of the character's `characterspawntype.dbss` flags, but characters often have several (for example `Stable` and `Mating`). Whether `kind` drives the map icon, the NPC list filter or something else is not confirmed.
