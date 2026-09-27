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
| Knowledge Name  | text | LOC `str_type=34`, `str_id4=0`; fallback to `name_ko`    |
| Category ID     | num  | `theme_id` (u16, not the full u32)                       |
| Category Name   | text | LOC `str_type=9` for `theme_id`                          |
| Favor           | text | `{min_favor} to {max_favor}`                             |
| Interest        | num  | `interest`                                               |
| Obtain          | text | LOC `str_type=34`, `str_id4=2`; fallback to `acquisition_ko` |

---

## Notes

- `card_id` → LOC `str_type=34`, `str_id1=card_id`; `str_id4` selects name (0), description (1) and acquisition text (2). 12,485 of 12,502 cards have an English name.
- `theme_id` → LOC `str_type=9`, `str_id1=theme_id` → knowledge category name. Read it as a u16: 524 cards have a non-zero byte at `+0x06` or `+0x07`, and reading `+0x04` as a u32 gives values such as `86040` (`0x15018`) that match no theme. With the u16 read, every card's theme lists that card in its `mentaltheme.dbss` entries.
- The three floats are whole numbers. `min_favor <= max_favor` on 12,382 cards. Median favor range is 34 to 39 with interest 22 on `flags == 4` cards, and 20 to 26 with interest 30 on the rest.
- `acquisition_ko` is empty on 651 cards. Whenever LOC has `str_id4=2` for a card, the card also has a non-empty `acquisition_ko` (11,766 cards).
- Non-zero positions are on 3,146 cards, mostly NPC, barterer and node-manager entries.
- The index key is not a separate row identifier: it equals `card_id` on every row.

---

- Stored favor and interest are close to, but mostly not equal to, values read from the in-game amity window. Those readings may be from an older patch, so this is not settled. Against 62 cards, 2 match exactly, 55 are within 5 on every value, and the differences show no pattern per NPC (the same NPC's cards differ by different amounts). Seven cards differ by 6 to 44, for example `6161` Slum in the City (interest `59` stored, `15` seen) and `4333` Calpheon Giant Bee (`28` / `24`-`30` stored, `2` / `40`-`47` seen).

## Open Questions

### Flags And Packed Fields

`flags`, `packed_a` and `packed_b` separate the 9,874 `flags == 4` cards from the rest, but what the bits mean (card type, amity reaction, hidden state) is not known.

### Body Value And Tail Fields

`body_flag`, `body_value`, `tail_kind`, `tail_value` and the hash list are not decoded. `body_value` 1 to 4 appears on single NPC cards such as the Sausan Scout, Sniper and Assassin, which suggests a small enum.

### Position Meaning

The position may be the card's map marker or the point where it is learned. The Iliya Island card (`3030`) sits at `159209, -7831, 292072`, next to the Velia card, which points to the acquisition point rather than the island itself. Checking card `3030` in game (where its Find/Locate marker points) would settle it.

### Favor And Interest Names

The field names come from bdo-data-extractor. In game, card `15879` (Despair-Consumed Blader) should show Interest 42 and Favor 4 to 8 in the amity conversation window if the names are right.

### How does the game derive a card's shown values?

Earlier in-game readings are within a few points of `interest`, `min_favor` and `max_favor`, but rarely equal to them, and not offset by a fixed amount per NPC. The readings may be outdated; fresh ones are needed before deciding whether the game rolls values per player, adds a modifier, or simply shows the stored values.
