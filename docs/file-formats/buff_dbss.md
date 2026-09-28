# `buff.dbss` Format

## Purpose

The master buff table: every buff and debuff the game can apply, from potions,
food and scrolls to title effects, furniture, boss mechanics and monster-only
debuffs. Each record carries an internal Korean name, a level, an effect type,
ten numeric parameters, a duration, an optional icon and an optional Korean
description whose English form lives in LOC type 5.

Example:

```text
buff_id 48830
  name         수렵 숙련도 +70 3시간   (internal label, "Hunting Mastery +70 3 hours")
  icon         New_Icon/04_PC_Skill/03_Buff/HuntingBuff.dds
  description  Hunting Mastery +70      (LOC str_type=5, str_id1=48830)
```

---

## Companion Files

| File                  | Required | Role                                              |
| --------------------- | -------- | ------------------------------------------------- |
| `buffoffset.dbss`     | Required | `buff_id → (offset, size)` index into this file   |
| `languagedata_en.loc` | Optional | English descriptions, `str_type=5`                |

`buffsimply.bss` holds the same 44,609 buff IDs in fixed 30-byte rows followed
by an icon path string table. It is not needed to read this file and is not yet
documented.

All multi-byte values are little-endian.

---

## File Layout

| Offset  | Type | Field   | Notes                                              |
| ------- | ---- | ------- | -------------------------------------------------- |
| `+0x00` | u32  | count   | Number of records; see below                       |
| `+0x04` | ...  | records | Variable-length records, located via the offset file |

The records tile the file exactly: sorted by offset, each ends where the next
begins, and the last ends at EOF.

Observed records: 44,609 in the pre-2026-09-27 test fixture, 44,645 in the
2026-09-27 client. The row counts elsewhere in this doc are from the fixture.

---

## Record Structure

A record is a chain of fixed blocks and length-prefixed strings. The strings use
the shared 8-byte prefix (u32 length, u32 zero, no terminator); UTF-16 lengths
count characters, ASCII lengths count bytes.

| Order | Type               | Field       | Notes                                                    |
| ----- | ------------------ | ----------- | -------------------------------------------------------- |
| 1     | u16                | buff_id     | Always equals the offset row's `buff_id`                 |
| 2     | prefixed UTF-16    | name        | Internal Korean label; no LOC counterpart                |
| 3     | 133 bytes          | stats block | See Stats Block below                                    |
| 4     | prefixed UTF-16    | unknown_str | Short digit text, `"0"` in 39,455 rows; 186 distinct     |
| 5     | prefixed ASCII     | icon_path   | Relative to `ui_texture/icon/`; see Notes                |
| 6     | u8                 | is_shown    | See Notes; `1` in 12,746 rows                            |
| 7     | u32                | apply_rate  | `1000000` (100%) in 44,427 rows; per-million scale       |
| 8     | prefixed UTF-16    | description | Korean, with `<PAColor>` tags; empty in 30,290 rows      |
| 9     | 27 bytes           | tail block  | See Tail Block below                                     |

Record sizes range from 203 to 2,198 bytes, median 237.

### Stats Block (133 bytes)

Offsets are relative to the end of the name string.

| Offset  | Type    | Field           | Notes                                                                 |
| ------- | ------- | --------------- | --------------------------------------------------------------------- |
| `+0x00` | i16     | buff_level      | 1 to 999; `1` in 32,071 rows. Ranks buffs within a `group`; staged buffs count up, e.g. boss stages 1 to 10 |
| `+0x02` | u8[2]   | reserved        | Always `0`                                                            |
| `+0x04` | u16     | group           | `0` in 28,199 rows. Shared by some effect families, see Notes         |
| `+0x06` | i16     | condition_type  | `0` in 44,390 rows; selects a trigger such as on-hit recovery         |
| `+0x08` | u8      | effect_type     | 173 distinct values; see Enum Values                                  |
| `+0x09` | u8      | flag_09         | `1` in 44,489 rows                                                    |
| `+0x0A` | u8      | flag_0a         | `1` in 31,950 rows                                                    |
| `+0x0B` | u8      | flag_0b         | `1` in 14,707 rows                                                    |
| `+0x0C` | u8[7]   | flag_0c..flag_12 | Each byte is `0` or `1`                                              |
| `+0x13` | i64[10] | param_1..param_10 | Effect parameters; meaning depends on `effect_type`. Percentages use a per-million scale (`100000` = 10%) |
| `+0x63` | u8      | flag_63         | `0` or `1`                                                            |
| `+0x64` | u8      | flag_64         | `0` or `1`                                                            |
| `+0x65` | u16     | reserved        | Always `0`                                                            |
| `+0x67` | u8      | flag_67         | `0` or `1`                                                            |
| `+0x68` | u32     | duration_ms     | `0` in 30,016 rows; max `86400000` (24 h). `3600000` = 60 min        |
| `+0x6C` | u32     | unknown_6c      | Millisecond-like (1000, 2000, 3000); only on periodic effects        |
| `+0x70` | u8[14]  | reserved        | `0` in every row but one                                              |
| `+0x7E` | u8      | flag_7e         | `1` in 44,514 rows                                                    |
| `+0x7F` | u8      | unknown_7f      | Always `2`                                                            |
| `+0x80` | u8      | reserved        | Always `0`                                                            |
| `+0x81` | u8      | unknown_81      | `46` in every row but one                                             |
| `+0x82` | u8      | unknown_82      | `2` in every row but one                                              |
| `+0x83` | u8      | flag_83         | `0` or `1`                                                            |
| `+0x84` | u8      | flag_84         | `0` or `1`                                                            |

### Tail Block (27 bytes)

Offsets are relative to the end of the description string. Mostly zero.

| Offset  | Type | Field       | Notes                                        |
| ------- | ---- | ----------- | -------------------------------------------- |
| `+0x00` | u8   | flag_00     | `1` in 34 rows                               |
| `+0x01` | u8   | flag_01     | `1` in 6 rows                                |
| `+0x02` | u32  | unknown_02  | `0`, `1` or `2`                              |
| `+0x06` | u8   | unknown_06  | `3` in 44,575 rows                           |
| `+0x07` | i32  | unknown_07  | `0`, `1000000` or `-1000000`                 |
| `+0x0B` | u8[12] | reserved  | Always `0`                                   |
| `+0x17` | u8   | flag_17     | `1` in 221 rows                              |
| `+0x18` | u8   | stacking_category | 61 distinct values; broad effect family, see Enum Values |
| `+0x19` | u8   | flag_19     | `1` in 2,066 rows                            |
| `+0x1A` | u8   | unknown_1a  | `6` in 18,895 rows, else `0` or `1`          |

---

## `buffoffset.dbss`

`PABR` index into `buff.dbss`, the same layout as `characterstaticoffset.dbss`
except that `data_offset` points *at* the inline `buff_id` and `size` includes
it.

### Header (8 bytes)

| Offset  | Type  | Field | Notes                                      |
| ------- | ----- | ----- | ------------------------------------------ |
| `+0x00` | u8[4] | magic | ASCII `PABR`                               |
| `+0x04` | u32   | count | Always equals the `buff.dbss` count        |

### Index Row (10 bytes, repeated `count` times)

| Offset  | Type | Field       | Notes                                           |
| ------- | ---- | ----------- | ----------------------------------------------- |
| `+0x00` | u16  | buff_id     | Unique; 43 to 65,528                            |
| `+0x02` | u32  | data_offset | Absolute offset of the record in `buff.dbss`    |
| `+0x06` | u32  | size        | Record size in bytes, including the `buff_id`   |

### Trailer (12 bytes)

| Offset  | Type | Value  | Notes                                         |
| ------- | ---- | ------ | --------------------------------------------- |
| `+0x00` | u32  | `0`    |                                               |
| `+0x04` | u32  | varies | End offset of the index rows (`446098`)       |
| `+0x08` | u32  | `0`    |                                               |

---

## Enum Values

`effect_type` (stats block `+0x08`). Labels are inferred from the internal names
of the buffs that use each value.

| Value | Rows  | Observed buffs                                     | Parameters, where confirmed                          |
| ----- | ----- | -------------------------------------------------- | ---------------------------------------------------- |
| 1     | 1,662 | On-hit effects (HP recovery on hit, back attack)   |                                                      |
| 2     | 443   | Max HP                                             | `param_1` = amount                                   |
| 18    | 3,386 | Summons                                            |                                                      |
| 25    | 1,597 | Combat, skill and life EXP gain                    | `param_1` = bonus per million; `param_2` 0 combat, 1 skill, 2 life |
| 38    | 5,683 | Story and record unlocks                           |                                                      |
| 39    | 1,732 | All AP, positive or negative                       | `param_1` = `3`, `param_2` = amount                  |
| 40    | 870   | All Accuracy                                       | `param_1` = `3`, `param_2` = amount                  |
| 43    | 1,730 | All Damage Reduction                               | `param_1` = `3`, `param_2` = amount                  |
| 45    | 8,286 | Damage multipliers (monster attack %, pure damage) |                                                      |
| 46    | 1,831 | Species extra AP                                   |                                                      |
| 49    | 1,378 | Crowd-control resistance                           |                                                      |
| 58    | 1,132 | Elixirs, herbal teas, sequence check buffs         |                                                      |

These are also confirmed against the English LOC type 5 text of their buffs. Percentages use the same per-million scale.

| Value | Rows | Effect                        | Parameters                                                        |
| ----- | ---: | ----------------------------- | ----------------------------------------------------------------- |
| 3     | 291  | HP Recovery                   | `param_1` = amount                                                |
| 5     | 85   | Max MP/WP/SP                  | `param_1` = amount                                                |
| 6     | 268  | MP Recovery                   | `param_1` = amount                                                |
| 8     | 205  | Max Stamina                   | `param_1` = amount                                                |
| 9     | 383  | Movement Speed                | `param_1` per million (`25000` = 2.5%)                            |
| 10    | 320  | Attack Speed                  | `param_1` per million                                             |
| 11    | 312  | Casting Speed                 | `param_1` per million                                             |
| 30    | 509  | Critical Hit Rate             | `param_1` per million                                             |
| 41    | 804  | All Evasion                   | `param_1` = `3`, `param_2` = amount                               |
| 80    | 180  | Life-skill EXP                | `param_1` = life skill (`4` Alchemy), `param_2` = amount          |
| 93    | 238  | Special-attack extra damage   | `param_1` = attack kind (`2` down, `3` air, `4` critical), `param_2` per million |
| 105   | 123  | Ignore resistance             | `param_1` = resistance kind (`8` all), `param_2` per million      |
| 128   | 78   | Weather resistance            | `param_1` = `0` heatstroke, `1` hypothermia; `param_2` per million |

[bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor/blob/HEAD/FORMATS.md) also names these, unconfirmed here because their buffs have no English text: 29 Weight Limit, 50 Mount EXP, 57 Drop Rate, 63 worker stamina recovery, 67 potential ranks, 79 Energy recovery, 89 Breath/Strength/Health EXP, 90 Death Penalty Resistance, 95 underwater breathing. It gives 149 as life-skill mastery with `param_1` the life skill, but `Hunting Mastery +100` stores `param_1 = 15`, which that source reads as "all life skills".

### `stacking_category` (tail block `+0x18`)

A broad family byte. Confirmed values:

| Value | Rows | Family                     | Evidence                                              |
| ----- | ---: | -------------------------- | ----------------------------------------------------- |
| 0     | 41,859 | None                     |                                                       |
| 1     | 428  | Food                       | `최상위 음식` (top-tier food) buffs                    |
| 6     | 118  | Perfume                    | `녹음의 향수` and its component buffs                  |
| 21    | 4    | Whale tendon elixirs       | The three Whale Tendon Elixirs, plus `[Event] Sweet Pumpkin Pie`, which gives the same buff in game |

Value `2` (647 rows) holds 600-minute elixir-style buffs and value `38` the Adventure's Boon blessings. bdo-data-extractor reads `2` as elixir/draught and `26` as a single draught-reset control record, but 82 buffs here carry `26`, many of them species extra AP (`카마실비아 종족 추가 공격력 +17`).

---

## Suggested UI Layout

| Column      | Type | Notes                                                               |
| ----------- | ---- | ------------------------------------------------------------------- |
| Buff ID     | num  | `buff_id`; right-aligned                                            |
| Icon        | text | `icon_path`, resolved under `ui_texture/icon/`; dash when empty     |
| Title       | text | Coloured first line of the description when more lines follow; dash otherwise |
| Internal Name | text | Korean `name`; labelled internal because no English form exists   |
| Description | text | LOC `str_type=5`, `str_id1=buff_id`; falls back to the inline Korean description, `<null>` counts as empty |
| Level       | num  | `buff_level`                                                        |
| Effect Type | num  | `effect_type`                                                       |
| Duration    | text | `duration_ms` formatted as h/min/s; dash when `0`, stored as `None` so it sorts last                   |
| Param 1     | num  | `param_1`                                                           |
| Param 2     | num  | `param_2`                                                           |
| Param 3     | num  | `param_3`                                                           |

---

## Notes

- `icon_path` is set in 15,272 records over 1,017 distinct paths. 221 of those
  hold the literal placeholder `UNKNOWN`, and a few use backslash separators.
  Resolve by lowercasing, normalizing `\` to `/` and prefixing
  `ui_texture/icon/`, e.g. `ui_texture/icon/new_icon/04_pc_skill/03_buff/huntingbuff.dds`.
- `is_shown` looks like a "visible in the buff bar" flag: 11,882 of its 12,746
  set rows have both an icon and a description, against 312 of the 31,863
  clear rows.
- The buff name has no English form anywhere in LOC. Of 13,658 names with at
  least two numbers, the best match under any type and sub-field keyed by
  `buff_id` is 48 of 3,522 in type 10, which is chance. Names are internal
  labels such as `테스트용 토레스 일꾼` (test Torres worker); the game shows
  players only the description.
- The inline Korean description matches LOC type 5 by content; numbers agree
  in every checked row apart from thousands separators.
- LOC type 10 was once assumed to be buff text keyed by `buff_id`. It is not:
  only half of the IDs overlap and the text disagrees (see the LOC doc).
- `group` is not a LOC key: 8827 resolves to an unrelated item in type 0 and
  a skill in type 10. Some families share one value: the 18 food Max HP buffs
  (+100 to +300) all use `5616`. Others do not: each buff of Adventure's Boon
  has its own (9056 to 9061 below), and the same effect in the 60 and 300
  minute variants uses 9050 and 9062. `+0x00` to `+0x07` used to be read as
  two u32 fields; bytes `+0x02` and `+0x03` are zero in every record.
- `group` is a u16. Its keys run from `1` to `22100` and from `40001` to
  `60016`; the upper range holds 411 keys on 1,181 rows. Earlier versions of
  the parser read it as an i16, which turned those into negative numbers.
- No two buffs share a `group` and a `buff_level`: the 16,410 grouped buffs
  form 16,410 distinct pairs in the fixture, and 16,414 of 16,414 in the
  2026-09-27 client. Within a group the level orders the variants by
  strength, then duration: the 18 food Max HP buffs of group `5616` run from
  level 1 (+30, 30 min) to 12 (+100, 120 min), 13 to 16 (+150) and 17 to 18
  (+300 event foods). 1,082 buffs with no group also have a level above 1.
- One buff record holds one effect, so a consumable with several effects
  applies a run of consecutive buffs. Only the first carries the description,
  the icon and `is_shown`, and its description opens with the display title.
  Example: item 761880, `[Blessing] Adventure's Boon (120 min)` (LOC type 0),
  applies buffs 48723 to 48728:

  | buff_id | Effect                   | effect_type | param_1  | param_2 |
  | ------- | ------------------------ | ----------- | -------- | ------- |
  | 48723   | All AP +8                | 39          | 3        | 8       |
  | 48724   | All Accuracy +8          | 40          | 3        | 8       |
  | 48725   | All Damage Reduction +8  | 43          | 3        | 8       |
  | 48726   | Max HP +150              | 2           | 150      | 0       |
  | 48727   | Combat EXP +15%          | 25          | 150000   | 0       |
  | 48728   | Skill EXP +15%           | 25          | 150000   | 1       |

  The 60 and 300 minute variants sit either side, at 48717 and 48729.
- Only headline buffs have a display name, and it is not a field: their
  description opens with it on a coloured line of its own
  (`<PAColor0xffe9bd23>[Blessing] Adventure's Boon<PAOldColor>`), then the
  effects. Against LOC type 5 the buffs split as follows:

  | Type 5 text                          | Buffs  | First line                                  |
  | ------------------------------------ | ------ | ------------------------------------------- |
  | None or `<null>`                     | 30,488 | Nothing; hidden and group-member buffs      |
  | One line                             | 11,846 | The effect itself, e.g. `Mount EXP +3%`     |
  | Coloured first line, then effects    | 2,038  | The title; 2,020 of these have `is_shown`   |
  | Several lines, no colour             | 237    | Sometimes a title, sometimes an effect list |

  421 titles equal an item name once its `(120 min)`-style suffix is dropped.
  A few are flavour lines rather than names
  (`Time in Sycraia surges forward.`). The inline Korean description uses the
  same convention, so the title survives when LOC is not loaded.
- The parameters are the only reliable effect value; the name and the
  description can each be stale. Of 11,766 buffs whose name and description
  both hold numbers, about 500 disagree beyond a change of scale, and either
  side can be the outdated one:

  | buff_id | Name              | Description | Applied parameter | Matches     |
  | ------- | ----------------- | ----------- | ----------------- | ----------- |
  | 48866   | Life EXP +15%     | +3%         | `150000` (15%)    | name        |
  | 48321   | All Evasion -6    | -8          | `-6`              | name        |
  | 48661   | HP Regen +75      | +50         | `50`              | description |
  | 48766   | Olvia pass (2594.61) | Trade EXP +53630 | `129731`  | neither     |

  The inline Korean description and LOC type 5 always agree with each other,
  so this is drift in the game data, not a parsing or translation error.
- Item IDs do not appear in this file: 761880 is not stored anywhere in it as
  a u32 or i64, so the item-to-buff link lives in another table.

---

## Open Questions

### What does `unknown_str` hold?

A short UTF-16 string of digits (`"0"`, `"90"`, `"158"`), and occasionally `*`.
It could be a group or stacking key stored as text, but no table has been
matched against it.

### What does `unknown_6c` measure?

It is only set on periodic effects such as bleeds and heal-over-time, and holds
millisecond-like values. It is not the stated tick interval: a buff named
"every 3 seconds" stores `2000`.

### What do the ten parameters mean per effect type?

`param_1` through `param_10` change meaning with `effect_type`. The types in
Enum Values are confirmed; the rest have not been worked out. For 39, 40, 41
and 43 `param_1` is `3`; bdo-data-extractor reads it as the target (`0` melee,
`1` ranged, `2` magic, `3` all).

### When is `group` shared?

Food Max HP buffs share group `5616`, but duration variants of Adventure's Boon
each get their own value, so `group` is not simply "one effect across variants".
What decides whether buffs share one is open. The unique (`group`,
`buff_level`) pairs suggest a group is a set of buffs that replace each other,
the higher level winning; that needs an in-game check, for example eating a
+100 food with a +150 food active.

### Is `buff_level` a level or a category?

bdo-data-extractor splits `+0x00` into `i16 Category`, `u8 CategoryLevel` and
`u8 Level`. The two bytes are zero in every record here, the i16 counts up
on staged buffs such as boss stages, and it ranks the buffs of one `group`
(see Notes), so it is kept as `buff_level` until the client names it.

### Which table links items to their buffs?

Consumable items such as 761880 apply buff groups, but the item ID is not in
`buff.dbss`. The link is likely in an item table or runs through a skill the
item triggers.
