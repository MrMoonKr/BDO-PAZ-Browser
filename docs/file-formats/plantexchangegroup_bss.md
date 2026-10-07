# `plantexchangegroup.bss` Format

## Purpose

Worker production groups. Each row is one production key: `plantzone.dbss` points at it from `production_key`, and the row links to the `itemsubgroup.dbss` subgroup that lists the items the node produces. Each row also carries a Korean label of the form "node - work type".

```text
zone 2050 (Lumbering) -> production_key=1928 "플라테르 산맥 - 벌목" -> item subgroup 42356
  -> Elder Tree Timber (4611), Bloody Tree Knot (5005), Elder Tree Sap (5014)
zone 1539 (Teff) -> production_key=1539 "포할람 농장 - 테프" -> item subgroup 40189 -> Teff (7022)
```

The row size and the join fields match [iDevelopThings/bdo-data-extractor](https://github.com/iDevelopThings/bdo-data-extractor) (`FORMATS.md`, "Worker-production item tables"), which leaves the `+0x5A` tail unmapped; it is the label's string table index.

## Companion Files

| File                   | Required | Role                                                              |
| ---------------------- | -------- | ----------------------------------------------------------------- |
| `plantzone.dbss`       | Optional | The zones that use each production key, for the English name      |
| `plantzoneoffset.dbss` | Optional | Index into `plantzone.dbss`                                       |
| `languagedata_en.loc`  | Optional | Node names (LOC type 29) and item names (LOC type 0)              |

Each zone's parent node comes from the `NODE_PARENT` lookup index (see `docs/handler.md`), built from `exploration.bss` and the worldmap links, so the preview opens no worldmap companion. The subgroup key is resolved through [`itemsubgroup.dbss`](itemsubgroup_dbss.md); the preview reads those items from the `PRODUCTION_ITEMS` lookup index (see `docs/handler.md`) instead of opening the 13 MB table as a companion.

All multi-byte values are little-endian unless noted otherwise.

## File Layout

PABR block with fixed 94-byte rows followed by the same counted string table and 8-byte trailer as [`npcsimply.bss`](npcsimply_bss.md).

| Offset             | Type    | Field        | Notes                                                 |
| ------------------ | ------- | ------------ | ----------------------------------------------------- |
| `+0x00`            | char[4] | magic        | ASCII `PABR`                                          |
| `+0x04`            | u32     | count        | Number of rows; `403` on the 2026-09-27 client        |
| `+0x08`            | row[]   | rows         | 94-byte rows repeated `count` times                   |
| `8 + count * 94`   | table   | string_table | Counted string table, see [`npcsimply.bss` String Pool](npcsimply_bss.md#string-pool) |
| EOF - 8            | u32     | string_table_start | Equals `8 + count * 94` (`37,890`)              |
| EOF - 4            | u32     | zero         | Always `0`                                            |

Rows are not sorted by key; the file opens with key 1775 and ends with keys 1, 31, 23, 22, 21.

## Record Structure

### Production Group Row (94 bytes, repeated `count` times)

| Offset  | Type    | Field              | Notes                                                                   |
| ------- | ------- | ------------------ | ----------------------------------------------------------------------- |
| `+0x00` | u16     | production_key     | Join from `plantzone.dbss` `production_key`; unique, observed `1`-`2044` |
| `+0x02` | u16     | unknown_02         | Equals `production_key` on all 403 rows                                  |
| `+0x04` | u16     | unknown_04         | Always `0`                                                              |
| `+0x06` | u32     | item_subgroup_key  | `itemsubgroup.dbss` key; observed `40001`-`45019`, see below            |
| `+0x0A` | u8[80]  | unknown_0a         | Always all zero                                                         |
| `+0x5A` | u32     | name_ref           | String table index of the Korean group label; unaligned                 |

`name_ref` covers every one of the 275 strings. Rows that share a label share the index (keys 1773 and 1774 are both "마지막 순례길 - 채집"). Most labels are "node - work type"; some use one phrase with no dash, such as "고대인의 석실 발굴" or "생선 건조장".

### `item_subgroup_key` Values

401 of the 403 subgroup keys are distinct; 42170 is shared by keys 1541 and 1542, 43165 by 1505 and 1930. The thousands band loosely follows the work type of the label, but every band holds exceptions, so it is not a rule:

| Band    | Mostly                                      |
| ------- | ------------------------------------------- |
| `40xxx` | Farming (재배, 농장) and crop specialties    |
| `41xxx` | Mining (채광, 광산, 광맥)                    |
| `42xxx` | Lumbering (벌목)                            |
| `43xxx` | Gathering (채집)                            |
| `44xxx` | Excavation, drying yards, finance, specialties |
| `45xxx` | Keys 1929 (통발) and 1931 (발굴), both missing from the index |

37 subgroup keys are absent from `itemsubgroupoffset.dbss`. 36 of them are the unresolved `plantzone.dbss` zones (see its Open Questions); the 37th is subgroup 45019 of key 1931, which no zone uses.

### English Names

No LOC type holds the labels, and the EU client ships no Korean LOC to match them against. The worker manager (`new_worldmap_workmanager_plant.luac`) reads a per-group description through `ToClient_getPlantWorkableItemExchangeDescriptionByIndex` into `_workName` but never shows it; the panel shows the product's item name. The two halves of the label can be rebuilt in English from the worldmap nodes:

```text
production_key -> plantzone.dbss zone record_id (a sub-node) -> LOC type 29 "Lumbering"
zone -> NODE_PARENT (its one link in mapdata_realexplore2.bwp) -> LOC type 29 "Platerra Mountains"
1928 -> "Platerra Mountains - Lumbering"  (Korean: 플라테르 산맥 - 벌목)
```

Every one of the 439 zones is an `exploration.bss` sub-node with exactly one worldmap link (see [`*.bwp`](waypoint_bwp.md)), so `NODE_PARENT` holds all of them and the preview names a zone with `node_with_parent_name()` from `_common/node.py`. A key gets a name only when every zone using it gives the same one; on client 3458 that is 365 of the 403 keys. The rest keep the Korean label: keys no zone uses (1931 and seven more), and keys shared by zones under different nodes, where the Korean label names a region instead (1231 칼페온 채집, Calpheon gathering, over Karanda Ridge and Longleaf Tree Sentry Post). The `exploration.bss` manager family was used before the links and named 324: it has no main node for some families (Godu Village, 1880) and the wrong one for Specialties 1563 (Areha Palm Forest instead of Arehaza, key 992 아레하자 마을 - 특산품). Investment banks read "Altinova - Gulabi Investment Bank" where the Korean label is only the bank name (928 굴라비 자산 관리소). The English halves follow the worldmap names, not the Korean wording: 1545 "가비냐 대분화구 - 티타늄" (titanium) becomes "Gavinya Great Crater - Mining", and 1203 "칼페온 파프리카 재배" (Calpheon paprika farming) becomes "Northern Wheat Plantation - Paprika Farming".

## Suggested UI Layout

| Column             | Type | Notes                                                                 |
| ------------------ | ---- | --------------------------------------------------------------------- |
| Production Key     | num  | `production_key`                                                      |
| Name               | text | English "parent node - sub-node" name (see English Names), else the Korean `name_ref` string |
| Item Subgroup      | num  | `item_subgroup_key`                                                   |
| Items              | text | Icon and LOC type 0 name of each of the subgroup's items in its grade colour (`ITEM_GRADE`); a dash when the subgroup is missing |

## Notes

- All 439 `plantzone.dbss` zones on the 2026-09-27 client resolve to a row. 8 keys are not used by any zone: 1503, 1675, 1676, 1931, 2015, 2021, 2036, 2037.
- `production_key` equals the zone's `record_id` for 157 of the 439 zones; the two are separate key spaces, and several zones share one key (1521 and 1934 are used by four zones each).
- LOC type 29 at `str_id1=production_key` gives a node name only by coincidence, when the key equals a node key; use the zone's `record_id` for the node name. That name is the sub-node, the work-type half of the label ("Lumbering", "Teff"); see English Names for the node half.
- bdo-data-extractor calls `+0x06` the "normal-output subgroup". No second subgroup key (for example luck drops) was found in `unknown_0a`, which is zero on every row.
