# `worldmapmonster.dbss` Format

## Purpose

The monster markers of the world map: hunting zones, field and world bosses,
Black Shrine bosses, Abyssal Wells and the Pilgrim's Sanctum spots. One
variable-length record per marker with two Korean label lines and a name, the
world position, the marker illustration and an optional condition script.
LOC type 40 holds the translations.

Example:

```text
marker 36, WorldmapMonster_36.dds
  line 1  추천 공격력 180 (3인 파티 권장) -> "Recommended AP: 180 (Party of 3 Recommended)"
  line 2  최종 공격력 300 (3인 파티 권장) -> "AP (Total Stat): 300 (Party of 3)"
  name    바실리스크 소굴                -> "Basilisk Den"
```

---

## Companion Files

| File                         | Required | Role                                                                 |
| ---------------------------- | -------- | -------------------------------------------------------------------- |
| `worldmapmonsteroffset.dbss` | Required | Bare u16-keyed index: marker key -> record offset and size           |
| `languagedata_en.loc`        | Optional | LOC type 40, `str_id1` = key, `str_id4` 0 / 1 / 2 = name / line 1 / line 2 |

All multi-byte values are little-endian.

---

## File Layout

### `worldmapmonsteroffset.dbss`

No magic and no trailer (`parse_bare_offset_rows()`).

| Offset  | Type  | Field | Notes                                         |
| ------- | ----- | ----- | --------------------------------------------- |
| `+0x00` | u32   | count | Number of rows; 229 on client 3458            |
| `+0x04` | row[] | rows  | 10-byte rows: u16 key, u32 offset, u32 size   |

The rows are not in file order: they interleave the regular keys (1 to 249)
with the 20 keys from 10001 to 10020, both counting down.

### `worldmapmonster.dbss`

| Offset  | Type  | Field   | Notes                                                     |
| ------- | ----- | ------- | --------------------------------------------------------- |
| `+0x00` | u32   | count   | Same count as the offset table                            |
| `+0x04` | ...   | records | Each record is preceded by a copy of its u16 key          |

The offset of a row points past that preceding copy, at the record's own key.

---

## Record Structure

### Marker Record (variable size)

Strings are a u64 unit count followed by the text, with no terminator: UTF-16LE
for the wide ones, ASCII for the icon path (`RecordReader`).

| Order | Type        | Field        | Notes                                                                 |
| ----- | ----------- | ------------ | --------------------------------------------------------------------- |
| 1     | u16         | key          | Same as the offset row                                                |
| 2     | wide string | line1_kr     | First label line: a level range (`Lv 12~15`), a recommended AP, or a category (`월드 우두머리`, world boss) |
| 3     | wide string | line2_kr     | Second label line: the final AP, or the same text as line 1 (142 records) |
| 4     | wide string | name_kr      | Zone or boss name                                                     |
| 5     | f32 x 3     | position     | World position; the second value is the height                        |
| 6     | string      | icon         | Marker illustration relative to `ui_texture/`; empty on the 16 Abyssal Wells |
| 7     | wide string | condition    | Condition script, empty on 165 records (`getknowledge(10497);`, `!checkFieldType(hadumField);`, `getlevel()>59;`) |
| 8     | wide string | unknown_str  | Always empty                                                          |
| 9     | i32         | unknown_ref  | `-1` on 120 records, else a small number; see Open Questions          |
| 10    | u8          | unknown_kind | 0 to 4, groups the markers; see Open Questions                        |
| 11    | u8          | unknown_flag | Always `1`                                                            |
| 12    | u8          | reserved     | Always `0`                                                            |

---

## Suggested UI Layout

| Column    | Type | Notes                                                                              |
| --------- | ---- | ---------------------------------------------------------------------------------- |
| Key       | num  | `key`; right-aligned                                                               |
| Icon      | text | `icon`, lowercased under `ui_texture/`; dash when empty                            |
| Name      | text | LOC type 40 `str_id4` 0, falling back to `name_kr`                                  |
| Label     | text | LOC type 40 `str_id4` 1, falling back to `line1_kr`                                 |
| Detail    | text | LOC type 40 `str_id4` 2, falling back to `line2_kr`; dash when it repeats the label |
| Condition | text | `condition`; dash when empty                                                       |

The position, `unknown_str`, `unknown_ref`, `unknown_kind` and `unknown_flag`
stay on the record but out of the table.

---

## Notes

- All 229 records walk to exactly their offset-table size with the layout
  above on client 3458.
- The markers are the world map monster icons the drop item window links to
  (`window/dropitem/panel_window_renewdropitem_all_1` registers
  `FromClient_Worldmap_LinkedDropUI_MouseOn` / `MouseOut` / `MouseClick` for
  them).
- LOC type 40 names all 229 markers and has both label lines for each.
- All 191 distinct icons exist once resolved under `ui_texture/` and
  lowercased: `combine/etc/worldmapboss/` for the zone and boss art,
  `combine/icon/` for the portal, sanctum, Griffon platform and Sea Palace
  markers, and
  `combine/etc/combine_etc_ocean_change02.dds` for the Margoria sea markers.
- The `unknown_kind` groups on client 3458: `0` hunting zones (161, the level
  and AP labels), `1` Abyssal Wells (16, no icon), `2` Black Shrine bosses
  (17), `3` the keys from 10001 (20, Pilgrim's Sanctum and the Offering Site
  markers, whose icons are named `Combine_WorldMap_HardcoreServer_*`; the drop
  item window checks `ToClient_HardCoreChannelWithContensOption`), `4` world, field and hunting field bosses (15).
- No lookup index is built from this file: no other table names these keys.

---

## Open Questions

### What does `unknown_ref` point at?

It is `-1` on 120 records. The 92 hunting zones that set it use distinct
values from 1 to 119, and the 17 Black Shrine bosses use 0 to 9. It may be the
hunting ground index of the drop item window, which links to these markers, but
nothing in the client files seen so far names it.

### What names the `unknown_kind` values?

The five values line up with the marker groups in Notes, but no Lua enum or
string names them; the world map code that reads the file is engine side.
