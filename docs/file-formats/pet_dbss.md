# `pet.dbss` Format

## Purpose

Defines one record per pet type/tier combination, covering icon path, species, tier, equip-skill slots, and several numeric parameters. Each record represents a specific pet at a specific tier (e.g. "Dog variant #40 at Tier 4"). Companion `petoffset.dbss` enables O(1) lookup by pet ID.

Example:

```text
pet_id: 0xFC05  →  species: 105 (GoldStar)  tier: 4
equip_skill_slots: 4   unknown_12: 4
icon: New_UI_Common_forLua\Window\Stable\Pet\GoldStar_Pet_0004.dds
```

---

## Companion Files

| File             | Required | Role                                                     |
| ---------------- | -------- | -------------------------------------------------------- |
| `petoffset.dbss` | Required | `pet_id → (data_offset, data_size)` for variable records |
| `petgrade.dbss`  | Optional | `(species, variant) → grade` per pet type                |

All multi-byte values are little-endian.

---

## File Layout

### Header (6 bytes)

| Offset  | Type | Field            | Notes                                                                        |
| ------- | ---- | ---------------- | ---------------------------------------------------------------------------- |
| `+0x00` | u32  | count            | Number of pet records (observed: 1,782 before 2026-09-27, 2,009 after)       |
| `+0x04` | u16  | first_record_key | `pet_id` of the first record, part of record 0, not a separate header field |

> `+0x04` is the key prefix of the first record, not a standalone header field. Records begin immediately at `+0x04`.

### Record (variable size, typically 181–194 bytes)

Each record is stored as `[u16 key_prefix][data_bytes]`. The `key_prefix` (2 bytes) equals `pet_id` and is also the first 2 bytes of `data_bytes`.

#### Fixed Header (32 bytes)

| Offset  | Type | Field             | Notes                                                                                   |
| ------- | ---- | ----------------- | --------------------------------------------------------------------------------------- |
| `+0x00` | u16  | pet_id            | Unique record key; equal to the preceding 2-byte file prefix                            |
| `+0x02` | u8   | variant           | Sub-variant within the species (1–57 observed)                                          |
| `+0x03` | u8   | species           | Pet family/model code                                                                   |
| `+0x04` | u8   | —                 | Always 0; reserved                                                                      |
| `+0x05` | u8   | tier              | Tier (0 = lowest, 4 = highest for regular pets)                                         |
| `+0x06` | u8   | —                 | Always 1; reserved                                                                      |
| `+0x07` | u8   | max_level         | Usually 10; Airiss variants have 20, 30, or 50                                          |
| `+0x08` | u32  | —                 | Always `0x90000000`; purpose unknown                                                    |
| `+0x0C` | u8   | —                 | Always 1; reserved                                                                      |
| `+0x0D` | u16  | —                 | Always 0; reserved                                                                      |
| `+0x0F` | u8   | equip_skill_slots | Number of equip skill slots; = `tier + 1` for regular pets (max 4); Airiss have up to 9 |
| `+0x10` | u16  | unknown_10        | `0` or `256` (355 records, mostly species 1); not padding                               |
| `+0x12` | u8   | unknown_12        | 97 distinct values; not reliably equal to the icon filename number                      |
| `+0x13` | u8   | —                 | Always 0; reserved                                                                      |
| `+0x14` | u32  | unknown_14        | 0 for many species, non-zero for others; about 140 distinct values                      |
| `+0x18` | u32  | icon_path_len     | Byte length of the icon path string (no null terminator)                                |
| `+0x1C` | u32  | —                 | Always 0; reserved                                                                      |

Earlier versions of this doc called `unknown_14` `type_param`, and first labeled `unknown_12` `dds_variant`. In the footer below, `unknown_2a` was `upgrade_table` and `unknown_53` was `tier_score` (`grade_score` in the parser). The parser called `unknown_10` `reserved_10`.

#### Icon Path (variable, `icon_path_len` bytes)

Stored immediately after the fixed header. **Not null-terminated.** Length is given by `icon_path_len`.

```text
New_UI_Common_forLua\Window\Stable\Pet\GoldStar_Pet_0004.dds
```

The icon path is ASCII-encoded with no null terminator; its byte length is given by `icon_path_len`.

#### Fixed Footer (94 bytes, immediately after the icon path)

| Offset  | Type     | Field           | Notes                                                         |
| ------- | -------- | --------------- | ------------------------------------------------------------- |
| `+0x00` | u32      | const_30000_a   | Always 30000 in every record                                  |
| `+0x04` | u32      | —               | Always 0                                                      |
| `+0x08` | u32      | const_15000     | Always 15000 (= const_30000_a / 2)                            |
| `+0x0C` | u32      | —               | Always 0                                                      |
| `+0x10` | u32      | const_30000_b   | Always 30000                                                  |
| `+0x14` | u32      | —               | Always 0                                                      |
| `+0x18` | u32      | const_500000    | Always 500000                                                 |
| `+0x1C` | u32      | const_1000000   | Always 1000000                                                |
| `+0x20` | u32      | const_2         | Always 2                                                      |
| `+0x24` | u16      | acquire_type_id | Key into `petequipskillaquire.dbss`; 0 = none; varies by tier |
| `+0x26` | u16      | equip_skill_id  | Pet equip-skill identifier; varies by pet type and tier       |
| `+0x28` | u16      | —               | Always 0; padding                                             |
| `+0x2A` | u32 × 10 | unknown_2a      | Usually ten times 1,000,000; see Open Questions               |
| `+0x52` | u8       | —               | Always 0                                                      |
| `+0x53` | u8       | unknown_53      | Mostly 11, 16 or 17, loosely by tier; see Open Questions      |
| `+0x54` | u8       | —               | Always 0                                                      |
| `+0x55` | u8       | —               | Always 26; purpose unknown                                    |
| `+0x56` | u8       | —               | Always 0                                                      |
| `+0x57` | u8       | —               | Always 1; purpose unknown                                     |
| `+0x58` | u8       | —               | Always 1; purpose unknown                                     |
| `+0x59` | u8 × 5   | —               | Always 0; padding                                             |

> Footer offsets are relative to the byte immediately following the icon path.

---

## petoffset.dbss

Provides O(1) lookup of any pet record by `pet_id`. Records are **not** stored in file order, use the offset to locate any record.

### Header (4 bytes)

| Offset  | Type | Field | Notes                       |
| ------- | ---- | ----- | --------------------------- |
| `+0x00` | u32  | count | Must equal `pet.dbss` count |

### Offset Record (10 bytes, repeated `count` times)

| Offset  | Type | Field       | Notes                                                                           |
| ------- | ---- | ----------- | ------------------------------------------------------------------------------- |
| `+0x00` | u16  | pet_id      | Matches `pet_id` in the main record                                             |
| `+0x02` | u32  | data_offset | Absolute byte offset in `pet.dbss` to the **data** (past the 2-byte key prefix) |
| `+0x06` | u16  | data_size   | Size of data in bytes (excluding the 2-byte key prefix)                         |
| `+0x08` | u16  | —           | Always 0; padding                                                               |

`record_start = data_offset - 2` gives the position of the 2-byte key prefix in the file.  
`total_record_size = data_size + 2`.

---

## Suggested UI Layout

| Column         | Type | Notes                                                                                                  |
| -------------- | ---- | ------------------------------------------------------------------------------------------------------ |
| Pet ID         | num  | `pet_id` as decimal only                                                                               |
| Icon           | Icon | Rendered from `icon_path`; shown immediately after Pet ID                                              |
| Name           | text | LOC type 6 lookup with `str_id1 = pet_id`; fallback to raw species ID                                  |
| Species ID     | num  | Raw `species` code                                                                                     |
| Tier           | num  | `tier` (0–4)                                                                                           |
| Skill Slots    | num  | `equip_skill_slots`                                                                                    |
| Max Level      | num  | `max_level` (10 for normal, 20/30/50 for Airiss)                                                       |
| Acquire Type   | num  | `acquire_type_id` → `petequipskillaquire.dbss`                                                         |
| Equip Skill ID | num  | `equip_skill_id`                                                                                       |
| Grade          | text | Optional `petgrade.dbss` join on `(species, variant)`: 1 Classic, 2 Rare, 3 Premium, 4 Rare, 5 Special |

Rows are sorted by `pet_id` ascending for stable browsing.

---

## Notes

- Total file size = 4 + Σ(2 + `data_size`) over all records: 332,420 bytes for the 1,782 records before the 2026-09-27 client update, 376,078 bytes for 2,009 records after it.
- Record size varies because `icon_path_len` differs per pet (observed: 55–68 bytes). The 32-byte header and 94-byte footer are fixed; only the path varies.
- `pet_id` appears three times per record: as the 2-byte key prefix in the file, as field `+0x00` in the data header, and as the `pet_id` field in the `petoffset.dbss` index.
- English pet display names resolve from `languagedata_en.loc` with `str_type = 6` and `str_id1 = pet_id`.
- `equip_skill_slots` = `tier + 1` for all regular pets (values 1–4). Airiss pets break this rule, reaching values of 7, 8, or 9.
- `max_level` is 10 for all regular pets. Airiss variants: tier 1 = 20, tier 2 = 30, tier 3 = 50.
- `unknown_12` does NOT reliably match the icon filename's 4-digit number (e.g. Cat_0991 → 0, Cat_0000 → 45).
- The three constant groups in the footer (30000, 15000, 30000, 500000, 1000000, 2) are identical in every record.
- `acquire_type_id` values 301–304 appear for regular pets and correspond to tiers 0–4 (tier 0 → 301, tier 4 → 304); lower values (1, 2, 3, 4) and mid-range values (101–104, 201–204, 401–404, 501–504) appear for specific sub-groups. 501–504 (21 pets, in both the pre-2026-09-27 and the 2026-09-27 files) have no row in `petequipskillaquire.dbss`.
- 21 records have no `petgrade.dbss` row for their `(species, variant)` and show no grade.

---

## Open Questions

### `unknown_10` Meaning

The u16 at `+0x10` is `0` in most records and `256` (byte `+0x11` = 1) in 355, 248 of them species 1. What it switches is unknown.

### `unknown_12` Meaning

It does not match the 4-digit icon filename number: Cats 0991–0993 all store 0, Cat_0000 stores 45, and Dogs show values like 79, 68, 51 that match neither path numbers nor tier. Its meaning is unknown.

### Footer constant fields

The six constant u32 values in the footer (30000, 15000, 30000, 500000, 1000000, 2) are identical in every record. They may be global pet system parameters duplicated per record, or references to shared game tables. Their in-game meaning (satiety, exchange cost, breeding cost?) is unconfirmed.

### `unknown_2a` Meaning

Ten u32 values. 1,642 of the 1,782 records before the 2026-09-27 update store ten times 1,000,000 and 96 store ten zeros; the rest mix 0 and 1,000,000 or carry smaller values such as 220,000, 100,000 and 40,000. BDO rates often use 1,000,000 as 100%, so this may be ten per-slot rates, but what the slots are is unknown.

### `acquire_type_id` pools 501–504

`acquire_type_id` keys into the `petequipskillaquire.dbss` skill roll table. Values 501–504 occur on 21 pets but have no row there, so where those pets roll their equip skills from is unknown.

### `unknown_14` Meaning

Varies by pet type (0 for many; non-zero values like 0x00BF7A00 for others) and is consistent within a species group. Purpose unknown; it could be a bitfield of capabilities, a hash, or a sub-type attribute.

### `unknown_53` Meaning

Most records store 11 at tier 0-1, 16 at tier 2 and 17 at tier 3-4, but other values occur (1, 12-14, 47-50, 53-57), and pets added in the 2026-09-27 client store 16 or 17 at tier 1 and 17 at tier 2. It follows tier loosely without being a function of it. Possibly a UI display tier, a difficulty tier or a capacity index.
