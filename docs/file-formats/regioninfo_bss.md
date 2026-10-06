# `regioninfo.bss` Format

## Purpose

Stores every world region: towns, hunting grounds, castles, arenas, caves and sea areas. The primary key is a region key that resolves through LOC `str_type=17` (the region name). Each record also carries the region type, the node war day, the territory and its capital, the region group, the worldmap node the region belongs to and, for 20 port regions, the Guild Wharf Manager NPC.

Example:

```text
region_key=5   -> Velia (MainTown, Balenos, capital Velia, node 1 Velia, Guild Wharf Manager 40145 Robert)
region_key=724 -> Kamasylvia Castle (CastleInSiege, Kamasylvia, capital Grána, Guild Wharf Manager 50989 Syluna)
region_key=290 -> Longleaf Tree Sentry Post (Hunting, Calpheon, node war on Tuesday)
```

The layout follows [iDevelopThings/bdo-data-extractor](https://github.com/iDevelopThings/bdo-data-extractor) (`FORMATS.md`, section 11). I walked it against the client 3458 file: every record tiles exactly up to the string table and every span it calls reserved is zero in all 1594 records. Field meanings marked confirmed below were checked against LOC, the client's Lua enums and the linked tables; the extractor's other names stay `unknown_*` here.

---

## Companion Files

| File                  | Required | Role                                                                                       |
| --------------------- | -------- | ------------------------------------------------------------------------------------------ |
| `languagedata_en.loc` | Optional | Region names (type 17), territory names (type 12), node names (type 29), NPC names (type 6) |

All multi-byte values are little-endian unless noted otherwise.

---

## File Layout

| Offset  | Type    | Field              | Notes                                                          |
| ------- | ------- | ------------------ | -------------------------------------------------------------- |
| `+0x00` | char[4] | magic              | `PABR` (ASCII)                                                 |
| `+0x04` | u32     | record_count       | Observed `1594` (client 3458; the extractor documents `1572`)  |
| `+0x08` | record  | records            | Variable records packed back-to-back with no alignment         |
| varies  | pool    | string_table       | `u32 count` plus Korean strings (shared `pabr_strings` layout); observed `1108` entries |
| EOF-8   | u32     | string_table_start | Absolute file offset of `string_table.count`; observed `623714` |
| EOF-4   | u32     | zero_trailer       | Observed `0`                                                   |

A record is a 210-byte head, two counted lists and a 171-byte tail, so its size is `389 + 2 * key_count + 12 * vector_count`. The walk ends exactly at `string_table_start`; the parser raises an error when it does not.

---

## Record Structure

### Region Head (210 bytes)

Offsets are hex; the extractor's decimal offset is in the notes where it named the field.

| Offset  | Type      | Field              | Notes |
| ------- | --------- | ------------------ | ----- |
| `+0x00` | u16       | region_key         | LOC `str_type=17`, `str_id1=region_key`; unique; all 1594 resolve |
| `+0x02` | u8[3]     | unknown_02         | Extractor: RGB world-map colour (`mapColor`). Not checked; kept as a hex string |
| `+0x05` | u8        | reserved           | Always `0` |
| `+0x06` | u8        | region_type        | `CppEnums.RegionType`; see Enum Values |
| `+0x07` | u8        | node_war_day       | `CppEnums.VillageSiegeType`, Sunday `0` to Saturday `6`; `7` (the enum's `_Count`) for no node war |
| `+0x08` | u8[3]     | reserved           | Always `0` |
| `+0x0B` | u8        | unknown_0b         | Values `0`, `1`, `3`, `4`; `3` on Velia, Heidel, Altinova and Valencia City, `4` on the Margoria islands |
| `+0x0C` | bool      | unknown_0c         | Set on 318 regions, among them Velia, Glish, Ossuary, Heidel Castle and Lake Flondor; possibly a safe zone |
| `+0x0D` | bool      | unknown_0d         | Set on the 9 arena regions |
| `+0x0E` | bool      | unknown_0e         | Extractor: `ocean`. Set on 199 regions, mostly islands and sea |
| `+0x0F` | bool      | is_desert          | Set on 43 regions, all in Valencia (territory 4): the Great Desert, the sand dunes, Pilgrim's Sanctums, Cantusa, Aakman |
| `+0x10` | bool      | unknown_10         | Extractor: `prison`. Set on 8 desert regions: Aakman Temple, Scarlet Sand Chamber, Ibellab Oasis, Hystria Ruins, Roud Sulfur Mine, Pila Ku Jail, Muiquun, Jail |
| `+0x11` | bool      | unknown_11         | Extractor: `sea`. Set on 62 regions: Sea, Margoria, Oquilla's Eye, Crow Merchants' Vessel |
| `+0x12` | bool[9]   | unknown_12 .. unknown_1a | Several mirror `region_type` (`0x13` = Siege or CastleInSiege, `0x14` = Fortress, `0x18` = MainTown, `0x19` = MinorTown, `0x1A` = either town); `0x12` is set on Jail only |
| `+0x1B` | bool      | unknown_1b         | Extractor: `locator`. Set on 1514 regions |
| `+0x1C` | bool      | unknown_1c         | Set on 118 regions |
| `+0x1D` | u16       | unknown_1d         | |
| `+0x1F` | bool      | unknown_1f         | Set on 54 regions (Rameda Island, Altar of Agris, Western Guard Camp) |
| `+0x20` | u32       | unknown_20         | `22950` in every record (the extractor saw `19950`), so it changes between patches |
| `+0x24` | u8        | reserved           | Always `0` |
| `+0x25` | bool      | unknown_25         | |
| `+0x26` | u32       | unknown_26         | Extractor: outlaw respawn waypoint key. Set on 204 records, all exploration node keys (Muiquun for several desert regions) |
| `+0x2A` | f32[3]    | unknown_2a         | Extractor: the position paired with `unknown_26` |
| `+0x36` | bool[5]   | unknown_36 .. unknown_3a | |
| `+0x3B` | u8        | reserved           | Always `0` |
| `+0x3C` | u32       | unknown_3c         | |
| `+0x40` | u8[2]     | reserved           | Always `0` |
| `+0x42` | bool      | unknown_42         | |
| `+0x43` | u8        | reserved           | Always `0` |
| `+0x44` | u32       | unknown_44         | |
| `+0x48` | u8[10]    | reserved           | Always `0` |
| `+0x52` | bool      | unknown_52         | |
| `+0x53` | u8        | reserved           | Always `0` |
| `+0x54` | u32       | unknown_54         | |
| `+0x58` | u8[2]     | reserved           | Always `0` |
| `+0x5A` | u8        | territory_key      | Territory 0 to 13; LOC `str_type=12`, `str_id4=1` names it (Balenos, Serendia ... Inner Edania). The key of `territoryinfo.bss` |
| `+0x5B` | u8        | reserved           | Always `0` |
| `+0x5C` | u32       | name_index         | Index into `string_table`; the region's Korean name (`벨리아 마을` for Velia) |
| `+0x60` | u32       | unknown_60         | Index into `string_table`; a Korean place name, see Notes. The extractor calls it the capital's name, which it is not |
| `+0x64` | u16       | capital_region_key | Region key of the territory capital: the same in every region of a territory and always that territory's `MainTown` (Velia, Heidel, Calpheon City ... Angavu Outpost) |
| `+0x66` | u16       | unknown_66         | A region key. Extractor: affiliated town. Often the region itself or a nearby town, but also non-town regions (Evergart Falls points to 417) |
| `+0x68` | u16       | region_group_key   | Key of `regiongroupinfo.bss`: the file has 250 records and this field 250 distinct values (`0` on 32 regions) |
| `+0x6A` | u8        | reserved           | Always `0` |
| `+0x6B` | u16       | unknown_6b         | Non-zero on 628 records; equals `node_key` on 873 (zero included) |
| `+0x6D` | u8[2]     | reserved           | Always `0` |
| `+0x6F` | u16       | node_key           | `exploration.bss` node key; non-zero on 1331 records and every one is a node. The node that covers the region (Lumbering 1 -> Trent) |
| `+0x71` | u8[2]     | reserved           | Always `0` |
| `+0x73` | bool      | unknown_73         | |
| `+0x74` | u8[3]     | reserved           | Always `0` |
| `+0x77` | f32[3]    | unknown_77         | Extractor: waypoint position. Zero on 1580 records |
| `+0x83` | f32[3]    | unknown_83         | A world position shared by many regions; pairs with `unknown_60`, see Notes. The extractor calls it the region position, which it is not |
| `+0x8F` | u8[4]     | reserved           | Always `0` |
| `+0x93` | bool      | unknown_93         | |
| `+0x94` | u8        | reserved           | Always `0` |
| `+0x95` | u32       | unknown_95         | |
| `+0x99` | f32[5]    | unknown_99         | Velia: `45, 38, 0, 55, 0.6` |
| `+0xAD` | u32       | unknown_ad         | |
| `+0xB1` | u32       | unknown_b1         | |
| `+0xB5` | u32       | unknown_b5         | `0xFFFFFFFF` in every record |
| `+0xB9` | u32[6]    | unknown_b9         | Set mainly on towns; Velia `105580, 105554, 105551, 105607, 105547, 105580` |
| `+0xD1` | bool      | unknown_d1         | |

### Counted Lists (after the head)

| Offset             | Type        | Field              | Notes |
| ------------------ | ----------- | ------------------ | ----- |
| `+0xD2`            | u32         | key_count          | |
| `+0xD6`            | u16[n]      | unknown_d2_keys    | Region keys; set on 58 town regions and always includes the region itself. Extractor: warehouse group. Velia's list holds the mainland towns from Velia to Muzgar; Hakinza Sanctuary's holds Altinova, Asparkan, Shakatu, Sand Grain Bazaar, Muzgar, Velandir, Aal's Revelation and Angavu Outpost |
| `+0xD6 + 2n`       | u32         | vector_count       | |
| `+0xDA + 2n`       | f32[3][m]   | unknown_d2_vectors | World positions; only The Great Desert of Valencia (region 230) has any (3) |

### Region Tail (171 bytes, after the lists)

Offsets are relative to the start of the tail. The parser keeps only the confirmed field; the extractor lists 45 more scalar fields (`unknownTail1` to `unknownTail162`), and its reserved spans at tail `+0x00`, `+0x50`, `+0x8A` (7 bytes), `+0x92` (8 bytes) and `+0xA6` (3 bytes) are zero in every record.

| Offset  | Type | Field                   | Notes |
| ------- | ---- | ----------------------- | ----- |
| `+0xA9` | u16  | guild_wharf_manager_key | NPC character key; set on 20 regions and every NPC is titled `<Guild Wharf Manager>` in LOC (Robert in Velia, Sebastian in Port Epheria, Elro in Oquilla's Eye) |

---

## Enum Values

### `region_type` (`CppEnums.RegionType`)

Names from `global_define_cpp_enum.luac`, without the `eRegionType_` prefix. The enum ends with `_Count` = 7, but the file also uses 7 and 8.

| ID  | Name          | Records | Examples |
| --- | ------------- | ------- | -------- |
| 0   | MinorTown     | 45      | Glish, Olvia, Keplan, Port Epheria, Western Guard Camp |
| 1   | MainTown      | 14      | The territory capitals: Velia, Heidel, Calpheon City ... Angavu Outpost |
| 2   | Hunting       | 1489    | Every field region |
| 3   | Siege         | 14      | Calpheon Castle Site, Lake Kaia, Mediah Shore, Treant Forest |
| 4   | Fortress      | 8       | Balenos Forest, Southern Neutral Zone, Naga Marsh |
| 5   | CastleInSiege | 13      | Calpheon Castle, Mediah Castle, Kamasylvia Castle, Duvencrune |
| 6   | Arena         | 8       | Velia Duel Arena, Battle Arena, Valencia Arena |
| 7   | (not in enum) | 2       | Pit of the Undying (950, 1070) |
| 8   | (not in enum) | 1       | Battle Arena (1072) |

### `node_war_day` (`CppEnums.VillageSiegeType`)

`0` Sunday, `1` Monday, `2` Tuesday, `3` Wednesday, `4` Thursday, `5` Friday, `6` Saturday, `7` none. Client 3458 has 6 regions on each day from Sunday to Thursday, 33 on Friday (most of them Margoria islands) and none on Saturday, the conquest war day.

---

## Suggested UI Layout

| Column              | Type | Notes |
| ------------------- | ---- | ----- |
| Region Key          | num  | `region_key` |
| Region              | text | LOC type 17 name, falling back to the Korean `name_index` string |
| Type                | text | `region_type` enum name |
| Territory           | text | LOC type 12 (`str_id4=1`) name of `territory_key`; sorts by key |
| Capital             | text | LOC type 17 name of `capital_region_key` |
| Node                | text | `node_key` with its LOC type 29 name; `-` when 0 |
| Region Group        | num  | `region_group_key` |
| Node War Day        | text | Day name; `-` for none; sorts in week order, none last |
| Desert              | flag | `is_desert` |
| Guild Wharf Manager | text | `guild_wharf_manager_key` with its NPC name; `-` when 0 |

---

## Notes

- **LOC type 17 is the region name.** All 1594 region keys resolve in LOC type 17, which has 1658 IDs; the other 64 (750, 807 to 809, 821, 1177, 1178, 1417 ...) have no region in this client and look like retired regions. The `plantworkerselect.bss` selection IDs are region keys too: all 31 are towns of type `MainTown` or `MinorTown`. So both readings hold: type 17 names regions, and the worker-selection towns are regions; the `buff.dbss` town keys name towns through the same type. [`languagedata_loc.md`](languagedata_loc.md) says so.
- **`region_info.xml`** (`gamecommondata/`) keys its boxes by the same region key: `<box region_index=...>` matches `region_key`, and every one of its 183 region keys exists here. It is not a box per region: it holds 721 boxes (AABB plus an oriented box, `fieldNo="1"` on all) for 183 regions, nearly all caves, interiors and other small enclosed regions (Ossuary, Coastal Cave, Imp Cave, Secret Cave, Basement Cellar). Each box has a `property_index` into a 187-entry `propertyArray` of `WeatherTable`/`WeatherTime` values, and a `binArray` of 10626 grid cells indexes the boxes spatially. The `unknown_83` position falls inside the region's own boxes for only 18 of the 183, which is one reason it is not the region position.
- **`unknown_60` and `unknown_83` form a pair.** Grouping the records by the `unknown_83` position gives 230 groups, and 214 of them share a single `unknown_60` name: 90 regions point to `벨리아 마을` (Velia) at `(-1226, -7012, 81647)`, 107 to `하킨자 성전` (Hakinza Sanctuary), 81 to `알티노바` (Altinova). The name is often the territory capital or the `unknown_66` region, but matches neither consistently (463 and 470 of 1594). It looks like the place a player returns or revives to, but nothing in the client confirms that yet.
- The node war regions are field regions plus a few castles and towns: each day from Sunday to Thursday lists one region from each of six territories, for example Sunday holds Forest of Plunder, Orc Camp, Quint Hill, Valencia Castle, Neruda Plain and Neftak Outpost.
- Several flag bytes repeat `region_type` (see `unknown_12` .. `unknown_1a`), so they may be the client's per-type properties expanded into the record.
- Related files out of scope here: `regionclientdata.xml` and its per-service variants (`regionclientdata_<code>_.xml`) place NPCs and monsters per region and key them by `<RegionInfo Key=...>`, the same region key; `regioninfo_linkandcheckvalid2.bss` (19 KB) has not been looked at.

---

## Open Questions

### What `unknown_60` and `unknown_83` are used for

The Korean place name and world position are shared by many regions and pair up as one place (see Notes), which suggests the respawn or return point for the region. Checking a few regions in game, by dying or using a return option in, say, Ossuary and Coastal Cave (both point to Velia at `(-1226, -7012, 81647)`), would settle it.

### Region types 7 and 8

`CppEnums.RegionType` ends at Arena (6) with `_Count` = 7, but Pit of the Undying (950, 1070) has type 7 and one Battle Arena (1072) type 8. The enum in the client Lua may be older than the data, or these types are server-only.

### Meaning of `unknown_d2_keys`

The list holds town region keys and includes the owning region; the extractor calls it a warehouse group. Velia's list covers the mainland towns but not Valencia City or Shakatu, so it is not simply "all towns you can transport to". Comparing a town's in-game transport destinations with its list would confirm it.

### The unconfirmed flags

`unknown_0c` (possibly a safe zone), `unknown_0e` and `unknown_11` (the extractor's `ocean` and `sea`), `unknown_10` (the extractor's `prison`, but set on Ibellab Oasis and Hystria Ruins too) and `unknown_1b` (the extractor's `locator`) have plausible readings that nothing in the client confirms yet.
