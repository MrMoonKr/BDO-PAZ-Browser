# `characterspawntype.dbss` Format

## Purpose

NPC role flags. Each record gives one character (NPC, monster, object) 46 independent 0/1 bytes, one per value of the client's `CppEnums.SpawnType`: skill trainer, warehouse, stable, node manager (`Explorer`), shop merchant and so on. The client uses them for NPC services and town navigation.

Example:

```text
character 47659 Alper
  -> ItemRepairer, ImportantNpc, Stable, Intimacy, Mating, Grocery
```

## Graph

### Tags

- file format
- dbss
- npc
- spawn type

### Connections

- [languagedata_en.loc](languagedata_loc.md) - NPC names (`str_type=6`, `str_id1=character_id`)
- [characterstatic.dbss](characterstatic_dbss.md) - same `character_id` key space
- [characterobject.dbss](characterobject_dbss.md) - same `character_id` key space; shares the character icon index

---

## Companion Files

| File                            | Required | Role                                           |
| ------------------------------- | -------- | ---------------------------------------------- |
| `characterspawntypeoffset.dbss` | Optional | Maps `character_id` to the record offset; the main file can be walked without it |

All multi-byte values are little-endian.

---

## File Layout

### Header (4 bytes)

| Offset  | Type | Field | Notes                                  |
| ------- | ---- | ----- | -------------------------------------- |
| `+0x00` | u32  | count | Number of records; observed `24,017`   |

### Record (48 bytes, repeated `count` times)

| Offset  | Type   | Field        | Notes                                                        |
| ------- | ------ | ------------ | ------------------------------------------------------------ |
| `+0x00` | u16    | character_id | Unique; equals the offset-table key                          |
| `+0x02` | u8[46] | roles        | One byte per `SpawnType` value, each `0` or `1`; see below   |

---

## Enum Values

### SpawnType

Names come from `CppEnums.SpawnType` in `luacscript/x64/include/global_define_cpp_enum.luac`, in the client's spelling without the `eSpawnType_` prefix. The enum has no name for value `41`, although one record sets it. Counts and examples are from the observed file.

| Value | Offset  | SpawnType | Records | Example |
| ----: | ------- | --------- | ------: | ------- |
| 0 | `+0x02` | `NormalNpc` | 21,561 | Weakkebi (`47183`) |
| 1 | `+0x03` | `SkillTrainer` | 52 | Valks (`47653`) |
| 2 | `+0x04` | `ItemRepairer` | 255 | Alper (`47659`) |
| 3 | `+0x05` | `ShopMerchant` | 299 | Jackson (`47727`) |
| 4 | `+0x06` | `ImportantNpc` | 2,272 | Edania Merchant (`47759`) |
| 5 | `+0x07` | `TradeMerchant` | 124 | Roig Mills (`47651`) |
| 6 | `+0x08` | `WareHouse` | 33 | Erdin (`47665`) |
| 7 | `+0x09` | `Stable` | 91 | Alper (`47659`) |
| 8 | `+0x0A` | `Wharf` | 38 | Akin (`47670`) |
| 9 | `+0x0B` | `Transfer` | 31 | Erdin (`47665`) |
| 10 | `+0x0C` | `Intimacy` | 2,145 | Jackson (`47727`) |
| 11 | `+0x0D` | `Guild` | 16 | Selim (`47666`) |
| 12 | `+0x0E` | `Explorer` | 494 | Zaid (`47741`) |
| 13 | `+0x0F` | `Inn` | 0 |  |
| 14 | `+0x10` | `Auction` | 38 | Taner (`47657`) |
| 15 | `+0x11` | `Mating` | 45 | Alper (`47659`) |
| 16 | `+0x12` | `Potion` | 141 | Eileen (`47649`) |
| 17 | `+0x13` | `Weapon` | 99 | Ferit (`47658`) |
| 18 | `+0x14` | `Jewel` | 15 | Emet (`47662`) |
| 19 | `+0x15` | `Furniture` | 38 | Ergin (`47656`) |
| 20 | `+0x16` | `Collect` | 58 | Daon (`47301`) |
| 21 | `+0x17` | `Fish` | 37 | Akin (`47670`) |
| 22 | `+0x18` | `Worker` | 30 | Serdar (`47671`) |
| 23 | `+0x19` | `Alchemy` | 0 |  |
| 24 | `+0x1A` | `GuildShop` | 59 | Zafer (`47661`) |
| 25 | `+0x1B` | `ItemMarket` | 21 | Taner (`47657`) |
| 26 | `+0x1C` | `TerritorySupply` | 7 | Heira (`46010`) |
| 27 | `+0x1D` | `TerritoryTrade` | 0 |  |
| 28 | `+0x1E` | `Smuggle` | 0 |  |
| 29 | `+0x1F` | `Cook` | 34 | Vargas (`47740`) |
| 30 | `+0x20` | `PC` | 0 |  |
| 31 | `+0x21` | `Grocery` | 79 | Alper (`47659`) |
| 32 | `+0x22` | `RandomShop` | 22 | Patrigio (`47673`) |
| 33 | `+0x23` | `SupplyShop` | 12 | Faruk (`47663`) |
| 34 | `+0x24` | `RandomShopDay` | 10 | Morco (`47466`) |
| 35 | `+0x25` | `FishSupplyShop` | 12 | Burak (`47668`) |
| 36 | `+0x26` | `GuildSupplyShop` | 0 |  |
| 37 | `+0x27` | `GuildStable` | 17 | Zafer (`47661`) |
| 38 | `+0x28` | `GuildWharf` | 19 | Vedat (`47669`) |
| 39 | `+0x29` | `PcRoomStable` | 0 |  |
| 40 | `+0x2A` | `Instrument` | 4 | Artina (`59267`) |
| 41 | `+0x2B` | `Unknown41` | 1 | Miles (`59279`), the Grand Prix quest giver |
| 42 | `+0x2C` | `TraningVehicleShop` | 9 | Hiznak (`47022`) |
| 43 | `+0x2D` | `AbyssOneEnterPosGuide` | 15 | The Magnus Entrance - Well (`61263`) |
| 44 | `+0x2E` | `ChangeMarniStone` | 1 | Wacky Toshi (`44638`) |
| 45 | `+0x2F` | `ChurchBuff` | 21 | Edania Merchant (`47766`) |

Checked in game: Wacky Toshi (`ChangeMarniStone`) exchanges Marni stones, and Miles (value `41`) hands out the Grand Prix quests, `[Daily] Grand Prix, Become the Best` (4549/11) and `[Weekly] Old Moon Grand Prix, Rider of Honor` (4549/10).

The roles fit the NPCs they are set on: stable keepers carry `Stable` and `Mating`, arms dealers `ItemRepairer` and `Weapon`, node managers `Explorer`, and the Magnus entrance wells `AbyssOneEnterPosGuide`.

---

## characterspawntypeoffset.dbss

A parallel lookup index with one entry per main-file record.

### Header (8 bytes)

| Offset  | Type  | Field | Notes                                            |
| ------- | ----- | ----- | ------------------------------------------------ |
| `+0x00` | u8[4] | magic | `PABR` (ASCII)                                   |
| `+0x04` | u32   | count | Number of index records; matches main file count |

### Index Record (10 bytes, repeated `count` times)

| Offset  | Type | Field        | Notes                                      |
| ------- | ---- | ------------ | ------------------------------------------ |
| `+0x00` | u16  | character_id | Equals the record's own `character_id`     |
| `+0x02` | u32  | offset       | Byte offset into `characterspawntype.dbss` |
| `+0x06` | u32  | size         | Record byte count; always 48               |

### Trailer (12 bytes)

| Offset  | Type | Value  | Notes                                      |
| ------- | ---- | ------ | ------------------------------------------ |
| `+0x00` | u32  | 0      |                                            |
| `+0x04` | u32  | varies | Byte offset of end-of-records in this file |
| `+0x08` | u32  | 0      |                                            |

---

## Suggested UI Layout

| Column       | Type | Notes                                                        |
| ------------ | ---- | ------------------------------------------------------------ |
| Character ID | num  | `character_id`, right-aligned                                |
| Name (EN)    | text | LOC `str_type=6`, `str_id1=character_id`                     |
| One per role | num  | `1` or empty; header is the `SpawnType` name; only roles set on some row are shown |

---

## Notes

- Every record sets at least one role. 21,561 records set only `NormalNpc`, and no record sets `NormalNpc` together with another role; the other 2,456 are service NPCs.
- 103 distinct role patterns occur.
- `Inn`, `Alchemy`, `TerritoryTrade`, `Smuggle`, `PC`, `GuildSupplyShop` and `PcRoomStable` are set on no record.
- An earlier version of this doc read `+0x00` as a u32 entity ID and the flags from `+0x04`. That turned the `NormalNpc` and `SkillTrainer` bytes into a fake "entity namespace" in the high 16 bits (entity `82176` is character `16640` with `NormalNpc` set) and shifted every flag index by two.
- Records are stored in offset-table order, not sorted by `character_id`.

## Open Questions

### Value 41

The client enum skips `41`, but Miles (`59279`) sets it, together with `ItemRepairer`, `ImportantNpc` and `Grocery`. In game Miles gives the Grand Prix quests, so `41` is probably a Grand Prix (horse racing) role. As far as I know he is the only Grand Prix NPC (2026-09-27), which fits a single record, but there is no second case to confirm the name.

### ChurchBuff

`ChurchBuff` is set on 21 NPCs such as Zario (`47766`) and Resh (`47764`), but neither appears to give a church-style buff. What the client does with this role is open.
