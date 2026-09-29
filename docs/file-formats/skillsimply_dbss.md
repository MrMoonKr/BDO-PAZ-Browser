# `skillsimply.dbss` Format

## Purpose

A compact per-rank skill record with the same keys as
[`skill.dbss`](skill_dbss.md). Its bytes repeat parts of the
[`skilltype.dbss`](skilltype_dbss.md) action configuration (the same
`ff ff ff ff ff 7f` run and repeated key), so it reads like a slimmed copy the
client loads when it does not need the full record. Only the framing and the
first fields are decoded; nothing here is needed for names, icons or buffs.

---

## Companion Files

| File                     | Required | Role                                                  |
| ------------------------ | -------- | ----------------------------------------------------- |
| `skillsimplyoffset.dbss` | Required | `skill_key → (offset, size)` index into this file     |

All multi-byte values are little-endian.

---

## File Layout

### skillsimplyoffset.dbss

Unlike `skilloffset.dbss` this index has no magic and no trailer: a u32 count
(`30424` on client 3458) and then 12-byte rows of u32 `skill_key`, u32
`offset`, u32 `size`, ending exactly at end of file. Read it with
`parse_bare_u32_offset_rows()`.

### skillsimply.dbss

| Offset  | Type     | Field   | Notes                                                           |
| ------- | -------- | ------- | --------------------------------------------------------------- |
| `+0x00` | u8[4]    | magic   | `PABR`                                                          |
| `+0x04` | u32      | count   | Number of records; `30424`, the `skill.dbss` key set exactly    |
| `+0x08` | ...      | records | Back to back, no repeated key between them                      |
| end     | 12 bytes | trailer | Empty string table: `u32 0`, `u32` end of the records, `u32 0`  |

---

## Record Structure

### Skill Simply Record (variable, `size` bytes from `offset`)

| Offset  | Type    | Field       | Notes                                                              |
| ------- | ------- | ----------- | ------------------------------------------------------------------ |
| `+0x00` | u32     | skill_key   | Equals the index key                                               |
| `+0x04` | u32     | level_1_key | `skill_no << 16 \| 1`, as in `skill.dbss`                           |
| `+0x08` | u8[6]   | unknown_08  | Not decoded                                                        |
| `+0x0E` | u32     | hash_count  | `1` on 29,916 records, up to `4`                                   |
| `+0x12` | u32[]   | hashes      | Hash-like values; `0x6016CFF7` is the first on 18,784 records, 444 distinct |
| next    | bytes   | unknown     | Not decoded; see below                                             |

Sizes are even, from 114 bytes (25,006 records) to 134 (4 records), nine in all. The hash list
explains part of that, but 4,914 records are longer than `110 + 4 *
hash_count` bytes, so another variable part follows. The last byte is `0xCA`
on 30,397 records and `0xB3` on 27.

---

## Suggested UI Layout

| Column   | Type | Notes                                                       |
| -------- | ---- | ----------------------------------------------------------- |
| Skill No | num  | `skill_key >> 16`                                           |
| Level    | num  | `skill_key & 0xFFFF`                                        |
| Name     | text | LOC type `10`, `str_id1 = skill_no`, `str_id4 = 0`          |
| Size     | num  | Record size, for comparing records while the body is open   |

---

## Notes

- `0x6016CFF7` also sits in the `skilltype.dbss` configuration of 18,744
  records, close to the 18,784 here, which is the main reason to read this
  table as a projection of it.

---

## Open Questions

### What does the record body hold?

Past the hash list the record has a second variable part and ends in a
marker byte (`0xCA` or `0xB3`). Matching it field by field against the
`skilltype.dbss` configuration of the same key would likely decode both,
once that configuration is decoded.
