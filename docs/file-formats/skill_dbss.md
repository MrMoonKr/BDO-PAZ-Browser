# `skill.dbss` Format

## Purpose

The rule record of every skill rank: class skills, passives, item and event
skills, mount and guild skills. Each record carries the rank's cooldown, the
buffs it applies, an effect script, and the skills it leads to. This is the
middle link of the item effect chain: a consumable names a skill key, and
the skill names its buffs.

```text
item 761880  skill_key_1 = 0xBA430001  (itemenchant.dbss +0xCC)
  -> skill 47683 level 1
       buff_ids 48723, 48724, 48725, 48726, 48727, 48728  (buff.dbss)
```

---

## Companion Files

| File                  | Required | Role                                                            |
| --------------------- | -------- | --------------------------------------------------------------- |
| `skilloffset.dbss`    | Required | `skill_key → (offset, size)` index into this file               |
| `buff.dbss`           | Optional | The buffs named by `buff_ids`                                   |
| `skilltype.dbss`      | Optional | Korean name, kind and icon of the same skill, see [`skilltype.dbss`](skilltype_dbss.md); the app reads name and icon through the `SKILL_NAME_KR` and `SKILL_ICON` lookup indexes |
| `languagedata_en.loc` | Optional | Skill names and descriptions, LOC type `10`, `str_id1 = skill_no` |

All multi-byte values are little-endian.

---

## Skill Keys

Every table in the skill cluster keys a skill rank by a u32:

```text
skill_key = skill_no << 16 | level
```

30,424 keys on client 3458, over 30,342 skill numbers. Almost every key is
level `1` (30,342); 54 are level `2`, 18 level `3`, and a handful go up to
`13`. Rank chains such as "Grave Digging I" to "IV" use separate skill numbers,
not levels, and [`skillgroup.bss`](skillgroup_bss.md) lists them.

The first key in the index, `0xDEAD0001`, is skill `57005` level 1,
"[Event] Energy of Happiness". It looks like a sentinel but is an ordinary
skill; `0xDEAC0001` next to it is skill `57004`, "Grim Reaper's Fury".

---

## File Layout

### skilloffset.dbss

| Offset  | Type     | Field   | Notes                                                           |
| ------- | -------- | ------- | --------------------------------------------------------------- |
| `+0x00` | u8[4]    | magic   | `PABR`                                                          |
| `+0x04` | u32      | count   | Number of index rows; `30424` on client 3458                    |
| `+0x08` | ...      | rows    | `count` index rows                                              |
| end     | 12 bytes | trailer | Empty string table: `u32 0`, `u32` end of the rows (`8 + 12 * count`), `u32 0` |

#### Index Row (12 bytes)

| Offset  | Type | Field     | Notes                                        |
| ------- | ---- | --------- | -------------------------------------------- |
| `+0x00` | u32  | skill_key | `skill_no << 16 \| level`                    |
| `+0x04` | u32  | offset    | Byte offset of the record in `skill.dbss`     |
| `+0x08` | u32  | size      | Record size in bytes                          |

Read it with `parse_pabr_u32_offset_rows()`.

### skill.dbss

| Offset  | Type | Field   | Notes                                                    |
| ------- | ---- | ------- | -------------------------------------------------------- |
| `+0x00` | u32  | count   | Number of records; matches the offset file               |
| `+0x04` | ...  | records | Each record is preceded by a repeated copy of its key   |

The records tile the file: each starts 4 bytes after the previous one ends
(the repeated key), the first at `8`, and the last ends at end of file.

Strings are a `u64` count followed by that many units: UTF-16LE for text and
scripts, single-byte ASCII for `name`. There is no terminator.

---

## Record Structure

### Skill Record (variable, `size` bytes from `offset`)

Fields in order. Offsets marked `N+` count from the end of `name`; with an
empty name `N` is `17`.

| Offset  | Type       | Field               | Notes                                                           |
| ------- | ---------- | ------------------- | --------------------------------------------------------------- |
| `+0x00` | u32        | skill_key           | Equals the index key                                            |
| `+0x04` | u32        | level_1_key         | `skill_no << 16 \| 1`; equals `skill_key` except on the 82 keys above level 1 |
| `+0x08` | u8         | unknown_08          | Non-zero on 8,842 records                                       |
| `+0x09` | string     | name                | ASCII internal name such as `SUMMON_BOSS`, `SETUP_QUESTITEM`; empty on 24,794 records |
| `N+0`   | u32        | name_hash           | `0` when `name` is empty; one value per name (4,461 names)      |
| `N+4`   | u8[74]     | unknown_n04         | Not decoded                                                     |
| `N+78`  | u32        | cooldown_ms         | Cooldown in milliseconds; `0` on 22,798 records, see Notes      |
| `N+82`  | u16[10]    | buff_ids            | `buff.dbss` IDs, zero-padded; see below                          |
| `N+102` | string     | description         | Korean effect text, UTF-16; empty on 21,114 records, `UNKNOWN` on 1,284. Line breaks are stored as the two characters `\n` (873 on client 3458) and decoded by the parser |
| next    | string     | script              | UTF-16 effect script such as `DAM_ATT_2(...)`, `AWAKEN();`, `BATH();`; empty on 21,594 records |
| next    | u8[36]     | unknown_tail        | Not decoded                                                     |
| next    | u32        | next_skill_count    | `0` on 25,209 records, `1` on 4,560; up to `75`, see below       |
| next    | u32[]      | next_skill_keys     | Skill keys this rank leads to, see below                        |
| next    | u32        | unknown_zero        | Always `0`                                                      |
| next    | u32        | base_skill_count    | `1` on 155 records, else `0`                                    |
| next    | u32[]      | base_skill_keys     | The skill a Core skill enhances, see below                      |
| next    | f32        | unknown_f32         | `-1.0` on 29,722 records, else `0.0`                            |
| next    | u8[3]      | unknown_end         | Usually zero                                                    |

Every one of the 30,424 records on client 3458 walks to exactly its `size`
with this layout.

### `buff_ids`

Ten u16 slots. The IDs fill the front and the rest are `0`; no record has a
non-zero ID after a zero. 20,362 records name one buff, 507 fill all ten, and
107 name none. Every ID is a `buff.dbss` key.

This is the item to buff link: `itemenchant.dbss` `skill_key_1` and
`skill_key_2` are keys of this table, and the buffs of both skills are the
item's effects. Item 761880 casts skill 47683, which applies the six buffs
48723 to 48728.

### `next_skill_keys` and `base_skill_keys`

Every key in both lists is a `skill.dbss` key (7,877 and 155 entries).

`next_skill_keys` points forward along a skill line: "Ample Storage Lv. 26"
lists Lv. 27, "Soul Shower III" lists its next rank and "Core: Soul Shower".
Awakening, Succession and a few other hub skills list every skill they
unlock: most "Succession:" skills list 34 Prime skills, and "Succession:
Elemental Revelation" (4933) lists 75.
Of the 3,858 consecutive rank pairs in `skillgroup.bss`, 3,422 appear here as
rank `i` listing rank `i + 1`.

`base_skill_keys` is set only on the 155 "Core:" skills and names the skill
the Core enhances ("Core: Soul Shower" -> "Soul Shower III"). In 154 of the
155 cases that base skill lists the Core in its `next_skill_keys`.

---

## Suggested UI Layout

Opens sorted by `skill_key` (Skill No, then Level); the index order is arbitrary
and starts with event skills.

| Column      | Type | Notes                                                                 |
| ----------- | ---- | --------------------------------------------------------------------- |
| Skill No    | num  | `skill_key >> 16`                                                     |
| Level       | num  | `skill_key & 0xFFFF`                                                  |
| Icon        | icon | `IconKind.SKILL` icon of `skill_no` (the `skilltype.dbss` icon path)  |
| Name        | text | LOC type `10`, `str_id1 = skill_no`, `str_id4 = 0`; else the `skilltype.dbss` Korean name, else `name` |
| Cooldown    | num  | `cooldown_ms` as a duration (`8s`, `13.5s`, `30m`); empty when `0`; sorts by `cooldown_ms` |
| Buffs       | list | `buff_ids` as buff ID and the first line of its LOC type `5` text; sorts by count |
| Next Skills | list | `next_skill_keys` as skill names                                      |
| Base Skill  | text | `base_skill_keys` as skill name                                       |
| Script      | text | `script`                                                              |

---

## Notes

- `cooldown_ms` is checked in game (2026-09-28) on three Sorceress skill
  lines: Grave Digging I to IV show 8 s (8,000 stored), Imminent Doom (1209)
  18 s (18,000) and Succession: Imminent Doom (4859) 14 s (14,000). 7,547 of the 7,626 non-zero values are whole
  seconds; the other 79 are mostly Black Spirit variants at 90% of a round
  value (13,500, 8,100). The field name and its position `@95` come from
  bdo-data-extractor, which reads it at a fixed offset. That only holds when
  `name` is empty: skill 17569 has the 22-character name
  `SHADOW_SKILL_SLOT4_2LV`, and its cooldown (9,000) sits 22 bytes later.
- `description` is not the Korean source of LOC type `10` `str_id4 = 1`:
  Healing Touch (65209) stores a guild war effect text here while its LOC
  description is a usage hint. The skill applies buff 65209, and that buff's
  LOC type `5` text is the English of the stored line ("- Effect: Recover
  200 HP every 3 sec"), so `description` may be the effect text of the
  skill's buffs. Checked on this one skill only.
- `name_hash` is not the `stringtable.bss` key hash (both are unknown
  functions); it is kept as a hash because it is fixed per name and zero
  when the name is empty.
- `skillsimply.dbss` has exactly the same 30,424 keys, see
  [`skillsimply.dbss`](skillsimply_dbss.md).

---

## Open Questions

### What does the fixed block `unknown_n04` hold?

The 74 bytes between `name_hash` and `cooldown_ms` are sparse: byte `N+69`
(`+86` with an empty name) is set on all but 13 records, `N+5` and `N+7` on
about two thirds and `N+4` on about a third. Nothing here has been matched to a
tooltip value yet, so the block stays unnamed.

### What do `unknown_tail` and `unknown_f32` control?

The 36 bytes before `next_skill_count` are zero on most records. On class
skills they hold a hash-like u32 at `+8`, an f32 at `+20` (`900.0` on Soul
Shower III) and sometimes a skill key and a u16 after it, and `unknown_f32` is `-1.0` on nearly every record. Their meaning
needs a skill whose tooltip shows a value that only these bytes could hold.
