# `mentalcard.dbss` Format

## Purpose

Defines every knowledge entry (card). Each record holds the card ID, its owning knowledge category (theme), the amity conversation parameters, the Korean source name, description and acquisition text, the icon path, and a world position. Used to build knowledge trees and place entries within the knowledge UI.

Field names `cardKey`, `themeKey`, `minFavor`, `maxFavor` and `interest` follow the notes of [bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor); the layout below was re-checked against our files.

Example:

```text
card_id: 15879  →  theme_id: 10087 "Ecology of Voidekaia"  →  "Despair-Consumed Blader"
favor 4 to 8, interest 42, icon UI_Artwork/IC_015879.dds
```

## Graph

### Tags

- file format
- dbss
- knowledge

### Connections

- [mentaltheme.dbss](mentaltheme_dbss.md), the category tree that `theme_id` points into; its entry lists hold the same card IDs
- [knowledgelearning.dbss](knowledgelearning_dbss.md), maps characters and items to the `card_id` they teach
- [languagedata_en.loc](languagedata_loc.md), card name, description and acquisition text (str_type=34) and category names (str_type=9)

---

## Companion Files

| File                    | Required | Role                                                 |
| ----------------------- | -------- | ---------------------------------------------------- |
| `mentalcardoffset.dbss` | Required | Provides card ID, byte offset and size for each card |

All multi-byte values are little-endian.

---

## File Layout

### mentalcardoffset.dbss

`PABR` index with 12-byte rows, the same shape as other `PABR` offset companions but with a u32 key.

#### Header (8 bytes)

| Offset  | Type  | Name  | Description                                     |
| ------- | ----- | ----- | ----------------------------------------------- |
| `+0x00` | u8[4] | magic | ASCII `PABR`                                    |
| `+0x04` | u32   | count | Number of rows; `12502` in the current client   |

#### Index Row (12 bytes, repeated `count` times)

| Offset  | Type | Name        | Description                                              |
| ------- | ---- | ----------- | -------------------------------------------------------- |
| `+0x00` | u32  | card_id     | Equals the `card_id` at the start of the record          |
| `+0x04` | u32  | data_offset | Absolute offset of the record in `mentalcard.dbss`       |
| `+0x08` | u32  | size        | Record size in bytes                                     |

Rows tile `mentalcard.dbss` exactly: the first record starts at `4`, each next record starts where the previous one ends, and the last ends at the file size.

#### Trailer (12 bytes)

| Offset  | Type | Value  | Notes                                         |
| ------- | ---- | ------ | --------------------------------------------- |
| `+0x00` | u32  | `0`    |                                               |
| `+0x04` | u32  | varies | End offset of the index rows (`150032`)       |
| `+0x08` | u32  | `0`    |                                               |

### mentalcard.dbss

| Offset  | Type | Name    | Description                                     |
| ------- | ---- | ------- | ----------------------------------------------- |
| `+0x00` | u32  | count   | Number of records; matches `mentalcardoffset`   |
| `+0x04` | ...  | records | Variable-size card records, back to back        |

Strings are `i64` UTF-16 code-unit counts followed by that many UTF-16LE units, except the icon path, which is an `i64` byte count followed by ASCII.

---

## Record Structure

### Card Header (33 bytes)

| Offset  | Type | Name       | Description                                                                    |
| ------- | ---- | ---------- | ------------------------------------------------------------------------------ |
| `+0x00` | u32  | card_id    | Knowledge entry ID; equals the index key; LOC `str_type=34`, `str_id1`         |
| `+0x04` | u16  | theme_id   | Owning category in `mentaltheme.dbss`; LOC `str_type=9`                        |
| `+0x06` | u8   | theme_flag_a | Observed `0` or `1`; `1` on 172 cards, mostly story and adventure-log entries |
| `+0x07` | u8   | theme_flag_b | Observed `0` or `1`; `1` on 373 cards, almost all under theme `10399` (None)  |
| `+0x08` | f32  | min_favor  | Amity conversation favor, lower bound; whole numbers `0` to `72`              |
| `+0x0C` | f32  | max_favor  | Amity conversation favor, upper bound; whole numbers `0` to `100`             |
| `+0x10` | f32  | interest   | Amity conversation interest; whole numbers `0` to `100`                       |
| `+0x14` | u32  | flags      | Bit field; `4` on 9,874 cards, otherwise combinations of bits 0, 28, 29, 30, 31 |
| `+0x18` | u32  | packed_a   | `0` exactly when `flags == 4`; otherwise values near `320`, `576`, `832`, `1088` |
| `+0x1C` | u32  | packed_b   | `0` exactly when `flags == 4`; otherwise `256`, `512`, `768` or `1024`        |
| `+0x20` | u8   | reserved   | Always `0`                                                                     |

### Card Body (variable, follows the header)

| Order | Type          | Name            | Description                                                                 |
| ----- | ------------- | --------------- | --------------------------------------------------------------------------- |
| 1     | i64 + utf16le | name_ko         | Korean card name; English form is LOC `str_type=34`, `str_id4=0`            |
| 2     | i64 + utf16le | description_ko  | Korean description; English form is LOC `str_type=34`, `str_id4=1`          |
| 3     | u8            | body_flag       | `0` or `1`; `1` on 474 cards, mostly adventure-log themes                   |
| 4     | u8            | body_reserved   | Always `0`                                                                  |
| 5     | u32           | body_value      | `5` on 10,455 cards, `0` on 1,893, `1` to `4` on the rest                   |
| 6     | i64 + ascii   | icon_path       | Always under `UI_Artwork/`, e.g. `UI_Artwork/IC_015879.dds`                 |
| 7     | i64 + utf16le | acquisition_ko  | Korean "how to obtain" text; English form is LOC `str_type=34`, `str_id4=2` |
| 8     | f32 × 3       | position        | World `x`, `y` (height), `z`; all zero on 9,356 cards                       |
| 9     | u8            | tail_kind       | `17` on 10,388 cards, otherwise `0` to `16`                                 |
| 10    | u32           | tail_value      | `0`, `1` or `3`                                                             |
| 11    | u32           | hash_count      | `1` to `7`                                                                  |
| 12    | u32 × hash_count | hashes       | Hash-like values; 271 distinct, lists share prefixes between cards          |
| 13    | u8[5]         | padding         | Always zero                                                                 |

Every one of the 12,502 records parses with this layout and ends exactly at its index `size`. The same layout holds for the older test fixture (12,087 records).

---

## Confirmed Examples

| card_id | LOC Name                | theme_id | min/max favor | interest | flags        | position                     |
| ------- | ----------------------- | -------- | ------------- | -------- | ------------ | ---------------------------- |
| `15879` | Despair-Consumed Blader | `10087`  | `4` / `8`     | `42`     | `0x80000000` | `0, 0, 0`                    |
| `3001`  | Velia                   | `5101`   | `45` / `50`   | `17`     | `4`          | `152611, -7849, 290383`      |
| `15949` | Ynix Remnant            | `355`    | `35` / `36`   | `22`     | `4`          | `1115590, 6865, 651513`      |

---

## Suggested UI Layout

| Column          | Type | Notes                                                    |
| --------------- | ---- | -------------------------------------------------------- |
| Knowledge ID    | num  | `card_id`                                                |
| Icon            | text | `icon_path`, lowercased under `ui_texture/`; 12,034 of 12,087 files exist |
| Knowledge Name  | text | LOC `str_type=34`, `str_id4=0`; fallback to `name_ko`    |
| Category ID     | num  | `theme_id` (u16, not the full u32)                       |
| Category Name   | text | LOC `str_type=9` for `theme_id`                          |
| Favor           | text | `{min_favor} to {max_favor}`                             |
| Interest        | num  | `interest`                                               |
| Obtain          | text | LOC `str_type=34`, `str_id4=2`; fallback to `acquisition_ko` |
| Position        | text | `x, y, z` rounded; dash when all zero                    |

---

## Notes

- `card_id` → LOC `str_type=34`, `str_id1=card_id`; `str_id4` selects name (0), description (1) and acquisition text (2). 12,485 of 12,502 cards have an English name.
- `theme_id` → LOC `str_type=9`, `str_id1=theme_id` → knowledge category name. Read it as a u16: 524 cards have a non-zero byte at `+0x06` or `+0x07`, and reading `+0x04` as a u32 gives values such as `86040` (`0x15018`) that match no theme. With the u16 read, every card's theme lists that card in its `mentaltheme.dbss` entries.
- The three floats are whole numbers. `min_favor <= max_favor` on 12,382 cards. Median favor range is 34 to 39 with interest 22 on `flags == 4` cards, and 20 to 26 with interest 30 on the rest.
- `acquisition_ko` is empty on 651 cards. Whenever LOC has `str_id4=2` for a card, the card also has a non-empty `acquisition_ko` (11,766 cards).
- Non-zero positions are on 3,146 cards, mostly NPC, barterer and node-manager entries.
- The index key is not a separate row identifier: it equals `card_id` on every row.
- How the conversation uses the values, per the [Black Desert Foundry, Story Exchange guide](https://www.blackdesertfoundry.com/story-exchange-guide/): a topic (card) has a fixed Interest Level and a Favor range. The NPC rolls its own Interest Level and Favor each conversation (from its `npcpersonality.dbss` ranges). The window then shows values relative to that NPC: Sparking Interest = topic interest / NPC interest (the chance of a positive reaction, always positive when the topic's is higher), and Interest gained = topic favor minus NPC favor. So the same card shows different numbers with different NPCs (the user sees it that way, 2026-09-27), and a reading converts back to base values: `interest ≈ sparking × NPC interest`, `favor = interest gained + NPC favor`.
- The guide's example is close to, but not equal to, the stored values: topic Shiel shows Interest Level `11` and Favor `31`-`39`; card `11` stores `10` and `33`-`38`. Its NPC, Lorenzo Murray (`40015`), shows Interest `32` and Favor `15`, both inside his stored ranges (`31`-`34`, `15`-`19`).
- The topic tooltip has two parts: **Attributes**, the card's own Interest Level and Favor range, and **Interaction Effect**, the values relative to the current NPC. For Lost Lamb with Oliviero it shows Attributes `23` / `33` ~ `37` and Interaction Effect Sparking Interest `23 (77%)`, Favor `2-6`, which fits the formulas above exactly with Oliviero at Interest Level `30` (23 / 30 = 77%) and Favor `31` (33 - 31 = 2, 37 - 31 = 6).
- In-game readings through Oliviero (`41091`), current client, 2026-09-27 (the Attributes part), next to the stored values and the tracker dataset:

  | card_id | Name | interest stored / seen | favor stored / seen | Tracker |
  | ---: | --- | --- | --- | --- |
  | 6059 | Al Rhundi's Journal | 100 / 100 | 1-1 / 1-1 | 100 / 1-1 |
  | 4024 | Lost Lamb | 21 / 23 | 34-36 / 33-37 | 23 / 35-38 |
  | 6062 | Lazy Soldiers | 10 / 12 | 35-38 / 30-38 | 12 / 34-38 |
  | 6063 | Cruhorn's Errand | 41 / 43 | 5-7 / 2-7 | 43 / 5-6 |
  | 6075 | Kite Flying | 29 / 28 | 22-28 / 23-26 | 25 / 25-29 |
  | 6079 | Cannonball Master | 20 / 18 | 45-46 / 45-49 | 19 / 45-50 |
  | 6095 | Broken Cannon | 1 / 3 | 44-48 / 40-57 | 5 / 43-60 |
  | 102 | Ornella (via Amerigo and via Cleia) | 12 / 12 | 33-36 / 35-38 | 13 / 35-38 |

  Seen interest is within 2 of the stored value on every card. Seen favor ranges contain the stored range on 6 of 7 (Kite Flying is narrower). Only the fixed `100` / `1`-`1` card matches exactly. The two sets of readings also differ from each other (interest agrees on 3 of 6 cards, favor on none), so the shown values are not a fixed function of the stored ones. Oliviero's own Interest Level stayed at 30 to 31 over several conversations (stored `30`-`34`), and his Favor stayed at `31` (stored `31`-`35`).
- The tooltip is built by `PaGlobal_MentalGame_All:updateTooltipContext` in `luacscript/x64/widget/dialogue/panel_mentalgame_all_1.luac` (Lua 5.1 bytecode, decompiled with unluac). Attributes come from the live conversation card, not from this record: Interest Level is `card:getHit()`, Favor is `card:getMinDD()` ~ `card:getMaxDD()`. The Interaction Effect is `getHit() / npc:getCurrentDV() * 100` (clamped to 0-100) and `getMinDD() - npc:getCurrentPV()` / `getMaxDD() - npc:getCurrentPV()` (clamped at 0), so the NPC's interest is `CurrentDV` and its favor `CurrentPV`. The static record (`card:getStaticStatus()`, this file) is only used for the card key and the combo text: `getBuffType()`, `getApplyTurn()` (shown plus one, "after N turns"), `getValidTurn()` and `getVariedValue()`. How the engine turns the stored favor and interest into `getHit` / `getMinDD` / `getMaxDD` is not visible in the Lua.
- Stored favor and interest are close to, but mostly not equal to, the readings in an amity tracker dataset. Against 62 cards, 2 match exactly, 55 are within 5 on every value, and seven differ by 6 to 44, for example `6161` Slum in the City (interest `59` stored, `15` seen) and `4333` Calpheon Giant Bee (`28` / `24`-`30` stored, `2` / `40`-`47` seen). The dataset does not say which NPC each reading came from. No NPC in the current `npcpersonality.dbss` has card `4333`'s theme (`10321`, Creatures of Northern Calpheon) as an interest group.

---


## Open Questions

### Flags And Packed Fields

`flags`, `packed_a` and `packed_b` separate the 9,874 `flags == 4` cards from the rest. They probably hold the combo effect the Lua reads through `getStaticStatus()`. Ornella (`102`) shows "After 2 turns, Favor will increase by 4 for 3 turns" and stores bytes `+0x14` = `1`, `+0x19` = `4`, `+0x1D` = `3`: apply turn (shown plus one), value, duration. Lost Lamb (`4024`) shows no combo and has `flags == 4` with both packed fields zero. On the 2,628 other cards `+0x14` is `0` or `1` and `+0x19` and `+0x1D` are `1` to `4`. Bytes `+0x15` to `+0x18` read as an f32 of `1.0` to about `5.0` whose meaning is unknown, and the buff type (favor or interest, up or down) is not located. Predicted from the bytes, to check in game: Lazy Soldiers (`6062`) value 4 for 4 turns, Kite Flying (`6075`) 2 for 1 turn, Cruhorn's Errand (`6063`) 2 for 3 turns, Al Rhundi's Journal (`6059`) 2 for 4 turns, all applying on the next turn; Cannonball Master (`6079`) and Broken Cannon (`6095`) no combo.

### Body Value And Tail Fields

`body_flag`, `body_value`, `tail_kind`, `tail_value` and the hash list are not decoded. `body_value` 1 to 4 appears on single NPC cards such as the Sausan Scout, Sniper and Assassin, which suggests a small enum.

### Position Meaning

The position may be the card's map marker or the point where it is learned. The Iliya Island card (`3030`) sits at `159209, -7831, 292072`, next to the Velia card, which points to the acquisition point rather than the island itself. Checking card `3030` in game (where its Find/Locate marker points) would settle it.

### Favor And Interest Names

The field names come from bdo-data-extractor. In game, card `15879` (Despair-Consumed Blader) should show Interest 42 and Favor 4 to 8 in the amity conversation window if the names are right.

### How does the game derive a card's shown values?

The NPC-relative numbers follow from the base values (see Notes), but the base values seen in game, in the tracker and in a 2024 guide are still off from the stored ones by a few points (Shiel `11` / `31`-`39` seen, `10` / `33`-`38` stored). Either those readings are from an older patch, or the displayed topic values pass through another rule. Current readings through Oliviero (see Notes) are within 2 of the stored interest and around the stored favor, and differ from the tracker's readings of the same cards, so a card's Attributes are not simply the stored values. They are fixed per card: Ornella (`102`) shows `12` / `35`-`38` both through Amerigo and through Cleia, in separate conversations, and another player sees about the same ranges (user, 2026-09-27). The shifts go both ways (interest `+2` on four cards, `-1` and `-2` on two), so it is not a fixed offset. The displayed numbers do not occur as f32 anywhere else in the card records, and `mentalcard.dbss` is the only card table in `gamecommondata/binary`. The tooltip code does not read them from this file either (see the next note), so the values come from the engine or the server.
