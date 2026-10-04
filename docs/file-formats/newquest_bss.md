# `newquest.bss` Format

## Purpose

Defines the new-quest (event) list: quest IDs grouped under events such as `[Event] Mastering Life Skills`, each group with an event period, and per quest a condition line and two condition scripts. 232 groups and 1,281 quest references on client 3458. All text sits in a string pool at the end of the file (Korean group names, Korean condition lines, scripts, dates); LOC type 58 holds the English names and condition lines.

[`mainquest.bss`](mainquest_bss.md), [`recommendationquest.bss`](recommendationquest_bss.md) and [`repetitionquest.bss`](repetitionquest_bss.md) share this layout, each with its own LOC type; one handler reads all four. This doc is the layout reference for all four.

Example:

```text
group 0 (key 1, "[Event] Mastering Life Skills", 2018-10-3 10:00 to 2018-11-7 09:59)
  -> quest 11059 / 9 -> [Event] Love for Pets
quest 11101 / 11 -> offered while checkperiodbyGmt(0, 2019/9/4-00:00, 2019/9/25-09:00);
                    ruled out by clearQuest(11101,9);<or>clearQuest(11101,10);<or>...
```

---

## File Layout

All multi-byte values are little-endian unless noted otherwise.

```text
header (8)
group[group_count]:
    group header (10)
    quest reference row (17) x quest_ref_count
    group trailer (13)
string pool: u32 string_count, string entry x string_count
file trailer (8)
```

### Header (8 bytes)

| Offset  | Type    | Field       | Notes                                      |
| ------- | ------- | ----------- | ------------------------------------------ |
| `+0x00` | char[4] | magic       | `PABR` (ASCII)                             |
| `+0x04` | u32     | group_count | Number of quest groups; `232` on client 3458 |

### Group Header (10 bytes)

| Offset  | Type | Field           | Notes                                                                   |
| ------- | ---- | --------------- | ----------------------------------------------------------------------- |
| `+0x00` | u16  | group_key       | The group's key, see Localization; unique per group                     |
| `+0x02` | u32  | name index      | String pool index of the Korean group name; `0` for the first group     |
| `+0x06` | u8   | unknown_06      | `0` on most groups; see Open Questions                                  |
| `+0x07` | u16  | quest_ref_count | Number of following rows                                                |
| `+0x09` | u8   | padding         | Observed zero                                                           |

### Quest Reference Row (17 bytes, repeated `quest_ref_count` times)

| Offset  | Type | Field          | Notes                                                                   |
| ------- | ---- | -------------- | ----------------------------------------------------------------------- |
| `+0x00` | u8   | unknown_00     | `0` on every row here; `1` on 7 `mainquest.bss` rows                    |
| `+0x01` | u16  | quest_chain_id | LOC type 18 `str_id1`; combines with `quest_id` to form quest key       |
| `+0x03` | u16  | quest_id       | LOC type 18 `str_id2`; combines with `quest_chain_id` to form quest key |
| `+0x05` | u32  | unknown_05     | String pool index of the Korean condition line, the source of the LOC condition line |
| `+0x09` | u32  | unknown_09     | String pool index of a condition script, often the empty string; see String Pool |
| `+0x0D` | u32  | unknown_0d     | String pool index of a second condition script, often the empty string; see String Pool |

### Group Trailer (13 bytes)

| Offset  | Type | Field        | Notes                                                                  |
| ------- | ---- | ------------ | ---------------------------------------------------------------------- |
| `+0x00` | u8   | unknown_00   | Observed zero                                                          |
| `+0x01` | u32  | start index  | String pool index of the event start, e.g. `2019-10-16 04:00`; the empty string in the other three lists |
| `+0x05` | u32  | end index    | String pool index of the event end, e.g. `2019-11-13 05:59`; always after the start |
| `+0x09` | u32  | unknown_09   | Observed `0` in every group of the four files                          |

The start of group 1 `[Event] Black Desert 2019 Halloween` is `2019-10-16 04:00`, and its English condition lines read `Oct 16 (after maintenance) - ...`.

### String Pool

Follows the last group trailer: a u32 `string_count`, then `string_count` entries, indexed from `0`.

| Offset  | Type      | Field  | Notes                                     |
| ------- | --------- | ------ | ----------------------------------------- |
| `+0x00` | u8        | marker | `1` on every entry                        |
| `+0x01` | u32       | length | Text length in bytes                      |
| `+0x05` | u16[]     | text   | UTF-16-LE, `length` bytes, no terminator  |

The pool holds each distinct string once, in first-use order: the group name, then each row's condition line and two scripts, then the trailer's dates. On client 3458 every entry is used (1,840 here). Index `0` is the first group's name, and the empty string sits at a low index (`2` here), which is why the script fields read `2` on so many rows.

The condition lines are the Korean source of the LOC lines and carry the same `<PAColor>` tags. The scripts are client condition calls separated by `;`, with `<or>` between alternatives and `!` for negation: `checkperiodbyGmt(0, 2019/9/4-00:00, 2019/9/25-09:00);`, `clearquest(40022,1);`, `progressquest(...)`, `getLevel()>59;`, `isContentsGroupOpen(0,2177);`, `checkClass(...)`, `getLifeLevel(6)>80;`. Across the four files:

- `unknown_0d` reads as the condition for the quest to be offered: event periods, content groups, level and class checks, prerequisite quests (`mainquest.bss` quest 40022 / 2 needs `clearquest(40022,1);`).
- `unknown_09` mostly lists the quests that rule this one out: the other branches of a crossroad (7500 / 81 lists 7500 / 82), `do not accept Techthon and Quality Iron` (2001 / 138 lists 2001 / 137), and the other quests of a "once a week per Family" set. No level check ever appears in it.

Neither script holds every condition its LOC line names: of 496 `repetitionquest.bss` lines that start `from Lv. N`, 75 have the level check in a script. The rest is likely checked by the quest itself.

### File Trailer (8 bytes)

| Offset  | Type | Field         | Notes                                                    |
| ------- | ---- | ------------- | -------------------------------------------------------- |
| `+0x00` | u32  | pool offset   | File offset of the string pool's `string_count` (`0x69F1` here) |
| `+0x04` | u32  | unknown_04    | Observed `0`                                             |

### Reading With the Old Framing

The handler still reads the older framing of this doc, which gives the same rows: a 10-byte "first group header" (the group header above, whose u16 key and zero name index read together as a u32 key) and a 23-byte "later group header", which is the previous group's 13-byte trailer followed by the next group's 10-byte header. In that framing the later header's `unknown_00`, `unknown_01`, `unknown_05`, `unknown_09` are the trailer fields, `+0x0D` is `group_key`, `unknown_0f` is the name index, `unknown_13` is `unknown_06` and `+0x14` the row count. The "text payload" after the stream was the last group's trailer, the string pool and the file trailer.

Earlier versions of this doc called the row's `unknown_00` `flags` and `unknown_05` / `unknown_09` / `unknown_0d` `sequence_a` / `sequence_b` / `sequence_c`, and named the header fields `header_flag`, `unknown_a`, `unknown_b`, `unknown_c`, `group_key_a`, `group_key_b` and `unknown_d`.

Derived packed quest ID:

```text
packed_quest_id = (quest_id << 16) | quest_chain_id
```

## Localization

LOC type `58` holds the English text of this list, keyed by the group's
`group_key`:

| Key                                              | Text                                         |
| ------------------------------------------------ | -------------------------------------------- |
| `str_id1 = group_key`, `str_id4 = 0`             | Group name, e.g. key 1 `[Event] Mastering Life Skills` |
| `str_id1 = packed_quest_id`, `str_id2 = group_key`, `str_id4 = 1` | The quest's condition line, e.g. `From <PAColor0xfff3d900>Lara <PAOldColor>during the event, once per Family` |

On client 3458 all 232 groups have a name (type 58 has 265, so some
belong to groups no longer in the file) and all 1,281 rows have a
condition line. A quest in two groups has a line under each key: quest
11060 / 1 sits in the groups with keys 2 (`[Event] Black Desert 2019
Halloween`) and 62 (`[Event] Black Desert 2020 Halloween`). Condition lines carry `<PAColor>`
tags; group names do not. The Korean names and condition lines in the
string pool are the source of both, so they can stand in where LOC has no row.

---

## Reference Rows

Client 3458:

| Group | Row | Group Key | Quest Chain ID | Quest ID | unknown_05 | unknown_09 | unknown_0d | Example LOC Title |
| ----: | --: | --------: | -------------: | -------: | ---------: | ---------: | ---------: | ----------------- |
| 0     | 0   | `1`       | `11059`        | `9`      | `1`        | `2`        | `2`        | `[Event] Love for Pets` |
| 0     | 1   | `1`       | `11059`        | `10`     | `1`        | `2`        | `2`        | `[Event] Savory Good Feed` |

---

## Suggested UI Layout

| Column       | Type | Notes                                                            |
| ------------ | ---- | ---------------------------------------------------------------- |
| Main ID      | num  | `quest_chain_id`; LOC type 18 `str_id1`                          |
| Sub ID       | num  | `quest_id`; LOC type 18 `str_id2`                                |
| Group Key    | num  | `group_key` of the row's group                                   |
| Group Name   | text | LOC type 58 `str_id1 = group_key`, `str_id4 = 0`                 |
| Icon         | text | Quest icon resolved from `packed_quest_id` through the quest icon index |
| Title        | text | Prefer LOC type 18 row with matching main/sub ID and `str_id4=0`, in its game colours |
| Condition    | text | LOC type 58 `(packed_quest_id, group_key)`, `str_id4 = 1`, in its game colours |

`group` (the index in file order), `unknown_05`, `unknown_09` and `unknown_0d` stay on the record for search and export but are not shown. The handler does not read the string pool yet, so the event period and the two scripts are not shown either.

---

## Notes

- Decompressed size is `820,905` bytes on client 3458 (`816,761` with 224 groups and 1,255 rows before 2026-09-27).
- 27 quests sit in two groups (29 before 2026-09-27); each copy has its own condition line in LOC.
- The string pool indexes shift whenever a string is added earlier in the file, so `unknown_05` / `unknown_09` / `unknown_0d` are not stable across patches: quest `77129` had `unknown_05 = 899` before 2026-09-27 and `896` after.

---

## Open Questions

### Group Header Byte `unknown_06`

`0` on 227 of 232 groups here, and `1`, `2`, `6` or `8` on the rest (`[Hunting] Sniping, ...` 2, `Krogdalo's Three Seeds` 1, `[Season] Stronger Tuvala Gear` 8). In `recommendationquest.bss` it runs `0` to `8` and groups by theme ([Life] [Leap] gurus at 4 to 7, mounts and outfits at 2), so it may be a category or tab; which UI uses it is not confirmed.

### Script Roles

Which of `unknown_09` and `unknown_0d` hides a quest and which offers it is read from the patterns above, not confirmed. Some `mainquest.bss` rows put a requirement in `unknown_09` with a negation (4015 / 5 `Another Chaser` has `!clearquest(4001,1);`), which fits "hidden while this holds".

### Duplicate Quest References

A quest in two groups has a condition line under both group keys, so a quest can be listed by two events (11060 / 1 in the 2019 and 2020 Halloween groups). Whether the game shows both copies at once is not confirmed.
