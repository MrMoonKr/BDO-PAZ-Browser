# `plantzone.dbss` Format

## Purpose

Defines worker production zones. Each record belongs to one worldmap production sub-node (`record_id` is an `exploration.bss` node key, named through LOC type 29), carries several invariant control fields and one variant byte, links to a production key in `plantexchangegroup.bss`, and lists which worker species may work the zone. `plantzoneoffset.dbss` is required to address the variable-length records.

```text
Observed records: 394. Record payloads are 32, 34, or 37 bytes depending on the worker-species list length.
record_id=1539 -> Teff, production key 1539 -> item subgroup 40189 -> Teff
```

The production-key and worker-species readings follow [asheimo/bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor) (`FORMATS.md`, "Worker-production item tables"), checked against the current client files below.

## Graph

### Tags

- file format
- dbss
- plant
- zone
- worker
- production

### Connections

- `plantzoneoffset.dbss` - required offset table for `plantzone.dbss`
- [exploration.bss](exploration_bss.md) - `record_id` is a production sub-node key (394/394)
- [languagedata.loc](languagedata_loc.md) - `record_id` names resolve via LOC `str_type=29`
- [plantworker.bss](plantworker_bss.md) - `worker_species` values match the species byte at worker record `+0x38F`
- `plantexchangegroup.bss` - low 16 bits of `production_key` join its `+0x00` key (394/394)
- `itemsubgroup.dbss` - `plantexchangegroup.bss` `+0x06` joins its subgroup key, which lists the produced item IDs

---

## Companion Files

| File                   | Required | Role                                                   |
| ---------------------- | -------- | ------------------------------------------------------ |
| `plantzoneoffset.dbss` | Required | Maps `record_id` to byte offset and payload byte count |

All multi-byte values are little-endian unless noted otherwise.

---

## File Layout

| Offset  | Type | Field         | Notes                                      |
| ------- | ---- | ------------- | ------------------------------------------ |
| `+0x00` | u32  | record_count  | Number of records; observed `394`          |
| `+0x04` | ...  | record_stream | Variable-length records, packed back-to-back |

`(file_size - 4) / record_count` is not integral, so records must be sliced with `plantzoneoffset.dbss`.

---

## Record Structure

### Plant Zone Record (32, 34, or 37 bytes)

| Offset  | Type | Field                | Notes                                                                    |
| ------- | ---- | -------------------- | ------------------------------------------------------------------------ |
| `+0x00` | u32  | record_id            | `exploration.bss` node key; matches `record_id` in `plantzoneoffset.dbss` |
| `+0x04` | u32  | unknown_04           | Always observed as `2`                                                   |
| `+0x08` | u32  | unknown_08           | Always observed as `0`                                                   |
| `+0x0C` | u16  | unknown_0c           | Always observed as `2`                                                   |
| `+0x0E` | u8   | variant              | Observed range `0`-`4`; correlates with node kind, see below             |
| `+0x0F` | u16  | unknown_0f           | Always observed as `101`; note unaligned offset                          |
| `+0x11` | u16  | unknown_11           | Always observed as `201`; note unaligned offset                          |
| `+0x13` | u32  | unknown_13           | Always observed as `1`; note unaligned offset                            |
| `+0x17` | u32  | production_key       | Low 16 bits: `plantexchangegroup.bss` key; high 16 bits usually `0`      |
| `+0x1B` | u32  | worker_species_count | Number of trailing `worker_species`; observed `1`, `3`, or `6`           |
| `+0x1F` | u8[] | worker_species       | Allowed worker species, `worker_species_count` bytes                     |

The current parser exposes `production_key` as `linked_id` and `worker_species` as `values`.

Observed record-size distribution:

| Size | Count | `worker_species_count` | `worker_species`    | Zones                                     |
| ---- | ----- | ---------------------- | ------------------- | ----------------------------------------- |
| 32   | 2     | 1                      | `06`                | Dokkebi Forest excavation (1807, 1808)    |
| 34   | 42    | 3                      | `06 07 08`          | Land of the Morning Light production nodes |
| 37   | 350   | 6                      | `00 01 02 03 04 05` | All other zones                           |

### `worker_species` Values

The same byte is the last byte (`+0x38F`) of every `plantworker.bss` record. Names below come from the LOC type 6 names of the workers carrying each value; the client enum for this byte was not found in `global_define_cpp_enum.luac`.

| Value | Workers                                                  |
| ----- | -------------------------------------------------------- |
| 0     | Goblin workers (plus named special workers such as Torres, Darifu) |
| 1     | Human workers (plus Demibeast workers)                   |
| 2     | Giant workers                                            |
| 3     | Papu workers                                             |
| 4     | Fadus workers                                            |
| 5     | Dwarf workers                                            |
| 6     | Dokkebi workers                                          |
| 7     | Dolswe workers                                           |
| 8     | Shellfolk workers                                        |

### `variant` by Node Kind

`exploration.bss` `node_kind` of the zone's node, counted per `variant`:

| `variant` | Dominant kinds                                                 |
| --------- | -------------------------------------------------------------- |
| 0         | Quarry 66, MonopolyFarm 3, Logging 1, Excavation 1             |
| 1         | Collect 48, Farm 15, Excavation 6, MonopolyFarm 4, Craft 1     |
| 2         | Farm 35, Collect 13, MonopolyFarm 11                           |
| 3         | Logging 62, Excavation 3, Quarry 1                             |
| 4         | FishTrap 41, MonopolyFarm 25, Finance 24, Excavation 24, Craft 6, MinorFinance 2, Quarry 1, Logging 1 |

### `production_key` High Bits

Most keys fit in the low 16 bits. Nineteen records (15 Specialties, 2 Mining, 1 Gathering, 1 Excavation) use non-zero high 16 bits:

| High 16 bits | Count | Low 16-bit range |
| ------------ | ----- | ---------------- |
| `0`          | 375   | `1`-`2044`       |
| `1`          | 3     | `960`-`1235`     |
| `2`          | 6     | `23`-`1213`      |
| `3`          | 2     | `962`-`970`      |
| `4`          | 2     | `963`-`971`      |
| `5`          | 2     | `972`-`975`      |
| `6`          | 2     | `973`-`976`      |
| `7`          | 2     | `974`-`977`      |

The high word counts up across consecutive Specialties node keys: 104-110 (Balenos farms such as Bartali, Finto and Wale Farm) carry `1`-`7`, and 613-619 (Calpheon farms such as Falres Dirt and Dias Farm) carry `1`-`7` again. Only the low 16 bits are needed for the join: all 394 low values are `plantexchangegroup.bss` keys, while the full u32 matches only 375.

### Production Item Chain

```text
production_key & 0xFFFF -> plantexchangegroup.bss +0x00 (productionKey)
plantexchangegroup.bss +0x06 (u32 itemSubgroupKey) -> itemsubgroup.dbss subgroup key
itemsubgroup.dbss record -> item IDs (LOC type 0)
```

Example: zone 2050 (Lumbering) -> production key 1928 -> subgroup 42356 -> Elder Tree Timber, Bloody Tree Knot, Elder Tree Sap. 358 of the 394 zones resolve to items; the other 36 reference subgroup keys that are absent from `itemsubgroupoffset.dbss`.

---

## `plantzoneoffset.dbss`

Provides the byte ranges for records in `plantzone.dbss`.

| Offset  | Type | Field        | Notes                             |
| ------- | ---- | ------------ | --------------------------------- |
| `+0x00` | u32  | record_count | Must equal `plantzone.dbss` count |
| `+0x04` | ...  | rows         | 12-byte rows repeated `count` times |

### Offset Row (12 bytes)

| Offset  | Type | Field       | Notes                                             |
| ------- | ---- | ----------- | ------------------------------------------------- |
| `+0x00` | u16  | record_id   | Matches `plantzone.dbss` record `+0x00`           |
| `+0x02` | u16  | zero        | Always observed as `0`                            |
| `+0x04` | u32  | data_offset | Absolute byte offset into `plantzone.dbss`        |
| `+0x08` | u32  | data_size   | Record payload byte count: `32`, `34`, or `37`    |

Offset rows are not sorted by `data_offset`, but sorted rows cover every byte from `plantzone.dbss +0x04` through EOF with no gaps or overlaps.

---

## Suggested UI Layout

| Column         | Type | Notes                                               |
| -------------- | ---- | --------------------------------------------------- |
| Zone ID        | num  | `record_id`                                         |
| Node Name      | text | LOC type 29, `str_id1=record_id`, `str_id4=0`       |
| Variant        | num  | `variant`                                           |
| Production Key | num  | Low 16 bits of `production_key`; show high word separately when non-zero |
| Worker Species | text | Render `worker_species` as species names            |
| Data Size      | num  | Useful for debugging `worker_species_count` classes |

---

## Notes

- `plantzone.dbss` and `plantzoneoffset.dbss` both report `394` records.
- The offset table's `record_id` equals the record payload's first u32 for all records.
- `worker_species_count` always equals the number of trailing bytes.
- Every `record_id` is an `exploration.bss` sub-node (`is_sub_node=1`) of a production kind; only three production sub-nodes have no plant zone (1564 Specialties and the disabled `UnKnown` records 1831 and 1839).
- The reference project reports 425 plant zones with 389 resolving to items; the current client file has 394 zones with 358 resolving, and the same 36 unresolved.
- Worker output quantities and luck bonus drops are not identified in these tables.

---

## Open Questions

### Variant Meaning

`variant` tracks the production type (Quarry is mostly `0`, Logging `3`, Fish Drying/Finance `4`) but Farm, Collect, MonopolyFarm and Excavation nodes are split across several values, so it is not simply the node kind. It may be a worker-stat or work-type class; the client enum was not identified.

### Production Key High Word

The high 16 bits of `production_key` count up across consecutive Specialties node keys, and the full u32 is not a valid `plantexchangegroup.bss` key for those 19 records. Whether the client uses the high word (for example as a display order or unlock step) is not confirmed.

### Unresolved Subgroups

36 zones point at production keys whose subgroup key is missing from `itemsubgroupoffset.dbss`. They are not empty: in game zone 2051 `Fish Drying Yard` (production key 1929, subgroup 45018) produces 4 items plus 2 lucky drops. Where the client reads their items from is open.
