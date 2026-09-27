# `npcpersonality.dbss` Format

## Purpose

Defines NPC personality entries used to parameterise AI behaviour. Each record maps a personality ID to three knowledge group references and four floating-point amity threshold parameters. Used to drive the in-game amity mini-game.

Example:

```text
personality_id: 0x2875  →  personality_type: 101 (Hammer)
interest_groups: Vendors of Serendia (4), Serendia Log II (4), Plants (4)
interest: 11–37, favor: 10–35
```

## Graph

### Tags

- file format
- dbss
- npc
- amity

### Connections

- [zodiacsign.dbss](zodiacsign_dbss.md), personality_type maps to zodiac_id via `major = personality_type // 100`
- [languagedata_en.loc](languagedata_loc.md), knowledge group names (str_type=9)

---

## Companion Files

| File                        | Required | Role                                    |
| --------------------------- | -------- | --------------------------------------- |
| `npcpersonalityoffset.dbss` | Required | ID-keyed index (same count, same order) |

All multi-byte values are little-endian.

---

## File Layout

### Header (4 bytes)

| Offset  | Type | Field | Notes                                          |
| ------- | ---- | ----- | ---------------------------------------------- |
| `+0x00` | u32  | count | Number of personality records (observed: 1182) |

### Record (34 bytes, repeated `count` times)

| Offset  | Type | Field              | Notes                                                         |
| ------- | ---- | ------------------ | ------------------------------------------------------------- |
| `+0x00` | u16  | personality_id     | Unique personality identifier                                 |
| `+0x02` | u32  | interest_group_a   | `(item_count << 16) \| group_id`, first amity interest group |
| `+0x06` | u32  | interest_group_b   | Second amity interest group                                   |
| `+0x0A` | u32  | interest_group_c   | Third amity interest group                                    |
| `+0x0E` | u16  | personality_id_dup | Always equal to `personality_id` at `+0x00`; purpose unknown  |
| `+0x10` | f32  | interest_min       | Inclusive lower bound for amity interest (range: 11–37)       |
| `+0x14` | f32  | interest_max       | Upper bound for amity interest (range: 23–70); inclusive or exclusive is open |
| `+0x18` | f32  | favor_min          | Inclusive lower bound for amity favor (range: 10–35)          |
| `+0x1C` | f32  | favor_max          | Upper bound for amity favor (range: 14–68); inclusive or exclusive is open |
| `+0x20` | u16  | personality_type   | Personality category code (see enum below)                    |

#### interest_group Encoding

Each `interest_group` field is a packed u32:

```text
bits 31–16 : item_count  (per-group count; meaning unconfirmed, see below)
bits 15–0  : group_id    (knowledge group ID, matches node_id in mentalcard.dbss)
```

The same numbers appear on the BDO wiki next to each NPC's interest groups, but the game does not show them: the conversation window lists only the topics you can use, with no per-group count or maximum (I checked in game, 2026-09-27). It is not the number of topics offered either: with Oliviero (count `6` for Serendia Adventure Log II) the topic list showed 7 cards of that group. What the count controls is open. Observed values: 0, 1, 2, 4, 5, 6, 7, 8, 10. All three fields in a record typically share the same `item_count` (1121 of 1182 records).

---

## Enum Values

### personality_type Codes

24 distinct values in the range 101–1202, following the pattern `(major × 100) + variant` where variant is 1 or 2:

| Major | Variant 1 | Variant 2 | Horoscope     |
| ----- | --------- | --------- | ------------- |
| 1     | 101       | -         | Hammer        |
| 2     | 201       | 202       | Boat          |
| 3     | 301       | 302       | Shield        |
| 4     | 401       | 402       | Giant         |
| 5     | 501       | 502       | Camel         |
| 6     | 601       | 602       | Black Dragon  |
| 7     | 701       | 702       | Treant Owl    |
| 8     | 801       | 802       | Elephant      |
| 9     | 901       | -         | Key           |
| 10    | 1001      | 1002      | Wagon         |
| 11    | 1101      | 1102      | Sealing Stone |
| 12    | 1201      | 1202      | Goblin        |

Confirmed by cross-referencing `amity-npcs.json` horoscope fields against `personality_id` values. Majors 1 and 9 have only variant 1.

---

## npcpersonalityoffset.dbss

An index file with one entry per personality record, stored in the same order as the main file.

### Header (4 bytes)

| Offset  | Type | Field | Notes                                  |
| ------- | ---- | ----- | -------------------------------------- |
| `+0x00` | u32  | count | Must equal `npcpersonality.dbss` count |

### Offset Record (10 bytes, repeated `count` times)

| Offset  | Type | Field          | Notes                                                                          |
| ------- | ---- | -------------- | ------------------------------------------------------------------------------ |
| `+0x00` | u16  | personality_id | Matches `personality_id` in the main record                                    |
| `+0x02` | u32  | data_offset    | Byte offset into main file; 2 bytes past record start (skips `personality_id`) |
| `+0x06` | u16  | data_size      | Always 32 (= record size minus the 2-byte personality_id header)               |
| `+0x08` | u16  | -              | Not parsed; assumed padding                                                    |

`record_start = data_offset - 2`

The offset file's `data_offset` values increment by exactly 34 (the main record stride) for each successive entry, it is a 1-to-1 sequential index providing no reordering.

---

## Suggested UI Layout

| Column            | Type | Notes                                            |
| ----------------- | ---- | ------------------------------------------------ |
| Row               | num  | Record index within the file                     |
| ID                | num  | `personality_id`                                 |
| Group A (ID ×cnt) | num  | `group_a_id` with its repeat count               |
| Group B (ID ×cnt) | num  | `group_b_id` with its repeat count               |
| Group C (ID ×cnt) | num  | `group_c_id` with its repeat count               |
| Int Min           | num  | Interest range lower bound                       |
| Int Max           | num  | Interest range upper bound                       |
| Fav Min           | num  | Favor range lower bound                          |
| Fav Max           | num  | Favor range upper bound                          |
| Horoscope         | text | Zodiac sign resolved from the personality type   |

---

## Notes

- All 1182 `personality_id` values are unique, it is a true record key.
- `personality_id_dup` at `+0x0E` is always identical to `personality_id` at `+0x00`; appears to be alignment padding or a redundant lookup key.
- The `variant` in `personality_type` (1 or 2) is not exposed in `amity-npcs.json`; its in-game meaning is unknown. Distribution is roughly even (584 variant-1, 598 variant-2).
- The groups and counts match the BDO wiki for Amerigo (41013): Vendors of Serendia, Serendia Adventure Log II and Plants (Serendia), `4` each.
- The NPC rolls its Interest Level and Favor within these ranges at the start of each conversation, and keeps them when the conversation is continued ([Black Desert Foundry, Story Exchange guide](https://www.blackdesertfoundry.com/story-exchange-guide/)). The guide's Lorenzo Murray (40015) shows Interest 32 and Favor 15, inside the stored 31-34 and 15-19. Worked back from topic tooltips in the current client (2026-09-27), all inside their stored ranges: Oliviero (41091) Interest 30 / Favor 31, Amerigo (41013) 22 / 28, Cleia (41056) 21 / 26. A tracker range built from a few conversations can therefore be narrower than the stored one.
- They match the wiki for Oliviero (41091) too: Serendia Adventure Log II, Officers of Serendia and Plants (Serendia), `6` each. Each group holds more cards than `item_count` (18, 13 and 11 here). Sharing a group does not mean sharing topics: Amerigo, who also has Serendia Adventure Log II, did not offer the Log II cards Oliviero did. Which cards an NPC offers is open.
- The stored ranges do not equal the ranges in an amity tracker dataset (taken from a wiki, possibly outdated) or one in-game check (Ornella), under either reading of the upper bound. Interest / favor:

  | NPC | Tracker or game | Stored | Stored, max minus 1 |
  | --- | --- | --- | --- |
  | Amerigo (41013) | 20-24 / 27-29 | 21-24 / 26-29 | 21-23 / 26-28 |
  | Cleia (41056) | 20-23 / 25-29 | 21-23 / 25-30 | 21-22 / 25-29 |
  | George Fusto (41118) | 22-25 / 26-30 | 22-24 / 25-29 | 22-23 / 25-28 |
  | Ornella (41002), in game | 22-23 / 27-28 | 21-25 / 25-28 | 21-24 / 25-27 |

  The seen ranges are shifted or narrower in both directions, so they settle neither reading.

## Open Questions

### What does `item_count` control?

The per-group count matches the numbers the BDO wiki lists next to each interest group, but the game shows no per-group count, and Oliviero's topic list held 7 cards of a group whose count is `6`. It may cap how many of the group's topics the NPC accepts, weight which topics are offered, or be unused. `0` occurs as well. Per the naming rule it should become an `unknown_*` field once the handler pass reaches this format.

### Are the upper bounds inclusive?

An earlier version of this doc called `interest_max` and `favor_max` exclusive (usable maximum one less than stored) without recorded evidence. Ornella's in-game favor reached `28`, her stored maximum, which argues against that, but the in-game and tracker ranges differ from the stored ones by more than one elsewhere (see Notes). How the displayed range is derived from the stored one is open.
