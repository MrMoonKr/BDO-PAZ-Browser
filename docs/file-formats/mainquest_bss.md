# `mainquest.bss` Format

## Purpose

Defines the main-quest list: quest IDs grouped into main-quest chains, each group named by LOC type 43, with per quest a condition line (where and when it can be accepted) and two condition scripts. 120 groups and 3,268 quest references on client 3458. All text sits in a string pool at the end of the file (Korean group names, Korean condition lines, scripts).

Example:

```text
group 0 (key 104, "[Special Growth] Taking My Own Path") -> quest 40022 / 1 -> [Special Growth] Birth of a Prestigious Family
quest 40022 / 2 -> offered after clearquest(40022,1);
```

---

## File Layout

Same layout as [`newquest.bss`](newquest_bss.md), the layout reference: an 8-byte `PABR` header with a group count; per group a 10-byte header, 17-byte quest reference rows and a 13-byte trailer; a string pool; an 8-byte file trailer. One handler reads all four quest lists. Values seen on client 3458:

| Field                                  | Observed                                              |
| -------------------------------------- | ----------------------------------------------------- |
| `group_count`                          | `120`                                                 |
| First group                            | key `104`, `14` rows                                  |
| Group header `unknown_06`              | `0`, except `1` on key 101 `[Invitation from I] Someone Beckons` |
| Group trailer start / end index        | Index `2`, the empty string: no event period          |
| Row `unknown_00`                       | `0`, except `1` on 7 rows, see Open Questions         |
| Row `unknown_09` (first script)        | Empty string on 2,667 rows, a script on 601           |
| Row `unknown_0d` (second script)       | Empty string on 1,348 rows, a script on 1,920         |
| String pool                            | `3,490` strings; `string_count` at `0x0000E3D4`       |

The scripts check prerequisite quests (`clearquest`, `progressquest`), class (`checkClass`), level and content groups (`isContentsGroupOpen`); see String Pool in the `newquest.bss` doc for the two script roles.

```text
packed_quest_id = (quest_id << 16) | quest_chain_id
```

## Localization

LOC type `43` holds the English text of this list, keyed by the group's `group_key`:

| Key                                                               | Text                                                 |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| `str_id1 = group_key`, `str_id4 = 0`                              | Group name, e.g. key 104 `[Special Growth] Taking My Own Path` |
| `str_id1 = packed_quest_id`, `str_id2 = group_key`, `str_id4 = 1` | The quest's condition line, e.g. `From <PAColor0xfff3d900>Alustin<PAOldColor> in Velia, complete ...` |

On client 3458 all 120 groups have a name (type 43 has 170, keys 1 to 171, so some belong to groups no longer in the file) and all 3,268 rows have a condition line. Condition lines carry `<PAColor>` tags (all but 6); group names do not. The string pool holds the Korean source of both.

---

## Suggested UI Layout

| Column       | Type | Notes                                                            |
| ------------ | ---- | ---------------------------------------------------------------- |
| Main ID      | num  | `quest_chain_id`; LOC type 18 `str_id1`                          |
| Sub ID       | num  | `quest_id`; LOC type 18 `str_id2`                                |
| Group Key    | num  | `group_key` of the row's group                                   |
| Group Name   | text | LOC type 43 `str_id1 = group_key`, `str_id4 = 0`                 |
| Icon         | text | Quest icon resolved from `packed_quest_id` through the quest icon index |
| Title        | text | Prefer LOC type 18 row with matching main/sub ID and `str_id4=0`, in its game colours |
| Condition    | text | LOC type 43 `(packed_quest_id, group_key)`, `str_id4 = 1`, in its game colours |

`group` (the index in file order), `unknown_00`, `unknown_05`, `unknown_09` and `unknown_0d` stay on the record for search and export but are not shown. The handler does not read the string pool yet.

---

## Notes

- Decompressed size is `447,790` bytes on client 3458.
- No quest appears twice; every group key is unique.
- Earlier versions of this doc read the later group header as 22 bytes starting one byte later, so each row took its leading `unknown_00` from the byte before it; the row values were the same. They named the first header's `group_key` `unknown_00` and the later header's `group_key` `unknown_0c`.

---

## Open Questions

### Row Byte `unknown_00`

`1` on only 7 rows, all in group key 51: quests 6603 / 3 to 8 and 6002 / 13. What it changes is not confirmed.

### Shared Fields

`unknown_06` and the roles of the two scripts are open for all four lists; see the Open Questions of [`newquest.bss`](newquest_bss.md).
