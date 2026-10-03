# `newquest.bss` Format

## Purpose

Defines "new quest" / quest-notice UI sequence data. The decoded first section groups quest IDs into blocks of quest reference rows (224 blocks and 1,255 rows in the pre-2026-09-27 fixture, 232 and 1,281 in the 2026-09-27 client). A later payload contains UTF-16-LE Korean text, PA markup, and date strings used by the same UI surface.

Example:

```text
group 0 -> quest 11059 / 9 -> [Event] Love for Pets
group 4 -> quest 6809 / 1 -> LOC type 18 title when available
```

---

## File Layout

All multi-byte values are little-endian unless noted otherwise.

### Header (8 bytes)

| Offset  | Type    | Field       | Notes                                      |
| ------- | ------- | ----------- | ------------------------------------------ |
| `+0x00` | char[4] | magic       | `PABR` (ASCII)                             |
| `+0x04` | u32     | group_count | Number of decoded quest groups; `224` in the pre-2026-09-27 fixture, `232` in the 2026-09-27 client |

### Quest Group Stream

Starts at `+0x08` and runs through file offset `0x00006771` in the pre-2026-09-27 fixture (224 groups, 1,255 quest reference rows) and `0x000069E3` in the 2026-09-27 client (232 groups, 1,281 rows). The file stores no total row count; each group header holds its own.

The first group uses a shorter 10-byte header. Every later group uses a 23-byte header immediately before their quest reference rows. Header fields are only partially decoded.

#### First Group Header (10 bytes)

| Offset  | Type | Field           | Observed | Notes                    |
| ------- | ---- | --------------- | -------- | ------------------------ |
| `+0x00` | u32  | unknown_00      | `1`      | Meaning not confirmed    |
| `+0x04` | u8[3] | padding        | `00 00 00` | Observed zero          |
| `+0x07` | u8   | quest_ref_count | `2`      | Number of following rows |
| `+0x08` | u16  | padding         | `0`      | Observed zero            |

#### Later Group Header (23 bytes)

| Offset  | Type | Field           | Observed / Notes                            |
| ------- | ---- | --------------- | ------------------------------------------- |
| `+0x00` | u8   | unknown_00      | Observed `0` in sampled headers             |
| `+0x01` | u32  | unknown_01      | Group/sequence value; meaning unknown       |
| `+0x05` | u32  | unknown_05      | Group/sequence value; meaning unknown       |
| `+0x09` | u32  | unknown_09      | Observed `0` in sampled headers             |
| `+0x0D` | u16  | unknown_0d      | Group key / sequence value; meaning unknown |
| `+0x0F` | u32  | unknown_0f      | Group key / sequence value; meaning unknown |
| `+0x13` | u8   | unknown_13      | Small byte; meaning unknown                 |
| `+0x14` | u16  | quest_ref_count | Number of following rows                    |
| `+0x16` | u8   | padding         | Observed zero in sampled headers            |

### Quest Reference Row (17 bytes, repeated `quest_ref_count` times)

| Offset  | Type | Field          | Notes                                                                   |
| ------- | ---- | -------------- | ----------------------------------------------------------------------- |
| `+0x00` | u8   | unknown_00     | Observed `0` in all decoded rows                                        |
| `+0x01` | u16  | quest_chain_id | LOC type 18 `str_id1`; combines with `quest_id` to form quest key       |
| `+0x03` | u16  | quest_id       | LOC type 18 `str_id2`; combines with `quest_chain_id` to form quest key |
| `+0x05` | u32  | unknown_05     | Observed range `1..1795` (`1..1837` in the 2026-09-27 client); meaning not confirmed |
| `+0x09` | u32  | unknown_09     | Commonly `2`; other small values appear                                 |
| `+0x0D` | u32  | unknown_0d     | Observed range `2..1788`; meaning not confirmed                         |

Earlier versions of this doc called the row's `unknown_00` `flags` and `unknown_05` / `unknown_09` / `unknown_0d` `sequence_a` / `sequence_b` / `sequence_c`. In the group headers, the first header's `unknown_00` was `group_key`, and the later header's `unknown_00`, `unknown_01`, `unknown_05`, `unknown_09`, `unknown_0d`, `unknown_0f` and `unknown_13` were `header_flag`, `unknown_a`, `unknown_b`, `unknown_c`, `group_key_a`, `group_key_b` and `unknown_d`.

Derived packed quest ID:

```text
packed_quest_id = (quest_id << 16) | quest_chain_id
```

### Text / Markup Payload

Starts immediately after the decoded quest reference stream (file offset `0x00006772` in the pre-2026-09-27 fixture). The payload contains UTF-16-LE Korean text, PA markup, and date/time strings such as `2018-10-3 10:00` and `2026-05-28 07:00`.

The first payload bytes resemble another small header followed by UTF-16 text, but record lengths and relationships to quest groups are not fully confirmed.

---

## Reference Rows

Pre-2026-09-27 fixture:

| Group | Row | unknown_00 | Quest Chain ID | Quest ID | unknown_05 | unknown_09 | unknown_0d | Example LOC Title |
| ----: | --: | ---------: | -------------: | -------: | ---------: | ---------: | ---------: | ----------------- |
| 0     | 0   | `0`   | `11059`        | `9`      | `1`        | `2`        | `2`        | `[Event] Love for Pets` |
| 0     | 1   | `0`   | `11059`        | `10`     | `1`        | `2`        | `2`        | `[Event] Savory Good Feed` |
| 1     | 0   | `0`   | `2035`         | `6`      | `6`        | `2`        | `7`        | LOC type 18 title when available |
| 4     | 0   | `0`   | `6809`         | `1`      | `30`       | `2`        | `2`        | LOC type 18 title when available |
| 223   | 0   | `0`   | `11593`        | `1`      | `899`      | `2`        | `2`        | `[Event] Crio's Symbol of Joy and Fortune` |

---

## Suggested UI Layout

| Column       | Type | Notes                                                            |
| ------------ | ---- | ---------------------------------------------------------------- |
| Main ID      | num  | `quest_chain_id`; LOC type 18 `str_id1`                          |
| Sub ID       | num  | `quest_id`; LOC type 18 `str_id2`                                |
| Group        | num  | Decoded group index, `0` to `group_count - 1`                    |
| Icon         | text | Quest icon resolved from `packed_quest_id` through the quest icon index |
| Title        | text | Prefer LOC type 18 row with matching main/sub ID and `str_id4=0` |

`unknown_05`, `unknown_09` and `unknown_0d` stay on the record for search and export but are not shown.

---

## Notes

- Observed decompressed size is `816,761` bytes in the pre-2026-09-27 fixture and `820,905` in the 2026-09-27 client.
- The decoded quest reference stream contains 224 groups and 1,255 rows in the pre-2026-09-27 fixture, 232 groups and 1,281 rows in the 2026-09-27 client.
- The 1,255 fixture rows contain 1,226 unique quest IDs; 29 quest IDs appear twice.
- Decoded quest reference rows use the same 17-byte shape as `mainquest.bss`.
- The decoded quest reference stream ends at offset `0x00006772` in the fixture (`0x000069E4` in the 2026-09-27 client); the rest of the file is mostly UTF-16-LE text/markup payload.

---

## Open Questions

### Group Header Fields

The meaning of the `unknown_*` group header fields is not confirmed.

### `unknown_05` / `unknown_09` / `unknown_0d` Meaning

The three row u32s look like order, parent, or link indexes, but their exact UI behavior is not confirmed. They are not stable across a patch: quest `77129` has `unknown_05 = 899` in the fixture and `896` in the 2026-09-27 client.

### Duplicate Quest References

29 packed quest IDs appear twice in the decoded quest reference stream. Their UI reason is not confirmed.

### Text Payload Boundaries

The UTF-16 text/markup section after `0x00006772` is confirmed as text payload, but its record lengths and mapping back to quest groups still need decoding.
