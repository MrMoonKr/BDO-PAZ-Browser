# `journalquest.dbss` Format

## Purpose

Adventure Log (bookshelf) data. Defines the journal groups shown in the in-game Adventure Log UI (e.g., "Igor Bartali's Adventures", "Shakatu Merchants' Archive"), the books (volumes) inside each group, and per-book metadata: Korean journal name, journal description, book name and unlock requirement, two bookshelf asset names, and the ordered list of quests that make up the book's pages.

Field names `journal_key`, `book_key` and the "book" terminology follow the notes of [bdo-data-extractor](https://github.com/asheimo/bdo-data-extractor); every field below was re-verified against our extracted files.

Example:

```text
Journal 1 / Book 1, Igor Bartali's Adventures Vol. I
  unlock (LOC 63, id4=2) = "Reach Lv. 51, complete [Calpheon] main ..."
  pages: 3 packed quest IDs 66284, 131820, 197356 (chain 748, quests 1..3)
    "Hey There Big Fellow!" | "Irresistible Lure" | "The Divine Entity inside the Cave"

Journal 8 / Book 1, Olvia Academy Journal / Emma Bartali's Journal
  pages: 13 packed quest IDs (chain 2326, quests 1..13)
```

---

## Companion Files

| File                         | Required | Role                                                                        |
| ---------------------------- | -------- | --------------------------------------------------------------------------- |
| `journalquestoffset.dbss`    | Required | Provides `(journal_key, book_key) → (byte_offset, byte_size)` record lookup |
| `quest.dbss`                 | Optional | Quest record for each page (conditions, objective, rewards)                 |
| `languagedata_en.loc`        | Optional | English journal/book text via LOC type=63; page quest text via LOC type=18  |

All multi-byte values are little-endian.

---

## File Layout

### Main File Header (4 bytes)

| Offset  | Type | Field         | Notes                                          |
| ------- | ---- | ------------- | ---------------------------------------------- |
| `+0x00` | u32  | group_count   | Number of journal groups; `13` since the 2026-09-27 client update, `12` before |

### Group Block (variable length, repeated `group_count` times)

| Field        | Type                | Notes                                                              |
| ------------ | ------------------- | ------------------------------------------------------------------ |
| `book_count` | u32                 | Number of book records in this group; equals the offset-file count |
| books        | book_count × Book   | Variable-length book records (see Record Structure)                |

The value previously documented as header `unknown_1` (`15` at `+0x04`) is the `book_count` of the first group (journal 1 has 15 books). The 4-byte header, the `book_count` words and the indexed records tile the file exactly, with no gaps or overlaps (verified on the `49,206`-byte file after the 2026-09-27 update with 13 groups and 119 records, the `46,620`-byte file before it with 12 and 112, and the `46,476`-byte fixture). Groups are stored physically in offset-file order; inside group 6 the offset-file order of books differs from their physical order (see [journalquestoffset.dbss](journalquestoffset_dbss.md)).

---

## Record Structure

### Book Record (variable length)

Strings are length-prefixed: a u64 character count followed by that many UTF-16LE (or single-byte ASCII) code units, with no terminator.

| Offset  | Type                  | Field                  | Notes                                                                                      |
| ------- | --------------------- | ---------------------- | ------------------------------------------------------------------------------------------ |
| `+0x00` | u32                   | journal_key            | Journal group key; equals the containing group in 112 of 112 records                       |
| `+0x04` | u32                   | book_key               | Book key within the group; equals the offset-file key in 112 of 112 records                |
| `+0x08` | u8                    | unknown_08             | `0` or `1`; `1` in 43 records (all books of journals 7, 10, 12 and 13, plus journal 6 book 8)      |
| `+0x09` | u64 + utf16le[n]      | journal_name_kr        | Korean journal name; identical for every book in a group except journal 6                  |
| varies  | u64 + utf16le[n]      | journal_description_kr | Korean journal description                                                                 |
| varies  | u64 + utf16le[n]      | book_name_kr           | Korean book (volume) name; may contain a `\n` and a second line                            |
| varies  | u64 + utf16le[n]      | unlock_requirement_kr  | Korean unlock text with `<PAColor0x........>` markup; empty (`n=0`) in 51 of 112 books      |
| varies  | u64 + ascii[n]        | bookshelf_scene        | E.g. `Combine_Etc_Adventure_Bookshelf01`; 31 distinct values                               |
| varies  | u64 + ascii[n]        | book_model             | `Adventure_Bookshelf_Static_book_00` to `_06`                                              |
| varies  | u32                   | page_count             | Number of page quest IDs                                                                   |
| varies  | u32[page_count]       | page_quest_ids         | Packed quest IDs `(quest_id << 16) \| quest_chain_id`                                      |
| varies  | u32                   | reserved_end           | `0` in 112 of 112 records; the record ends exactly here                                   |

Earlier versions of this doc called `unknown_08` `flag_08`. An even older reading of `unknown_08` as a u32 (`0x00000d00` etc.) was this byte plus the low bytes of the first string length. The "trailing `"` in `combine_model`" was the low byte of the next string's u64 length (`0x22` = 34 characters); it is not part of the stored value.

### Page Quest IDs

Every page is a single packed quest ID `(quest_id << 16) | quest_chain_id`, the same scheme as [quest.dbss](quest_dbss.md) and [allquestlist.bss](allquestlist_bss.md). There is only one encoding: the old "Type A / Type B" split does not occur in either file version (all 827 current pages decode with `lo16 = quest_chain_id`). All pages of one book belong to a single quest chain (112 of 112 books), and 110 books start at `quest_id = 1`.

Current file totals (after the 2026-09-27 update): 119 books, 901 pages, 901 distinct page quest IDs, all present in `allquestlist.bss`; one quest chain per book, 117 books start at `quest_id = 1`, and 51 books have no unlock text. Before the update: 112 books, 827 pages, all with a LOC type 18 `id4=0` title.

---

## Journal Group Table

Current client data (`files/journalquest.dbss`), offset-file order:

| Journal Key | Books | Pages | English Journal Name (LOC 63, `id4=0`) | `unknown_08` set | Books with unlock text |
| ----------: | ----: | ----: | -------------------------------------- | ------------: | ---------------------: |
|           1 |    15 |    71 | Igor Bartali's Adventures              |             0 |                     15 |
|           2 |    11 |    51 | Shakatu Merchants' Archive             |             0 |                     11 |
|           3 |    10 |   105 | Storybook - Morning Bosses             |             0 |                      0 |
|           4 |     1 |    17 | Justin Bartali's Adventures            |             0 |                      1 |
|           5 |    13 |    66 | Crow Merchants' Records                |             0 |                     13 |
|           6 |     7 |    44 | Event Logs                             |             1 |                      4 |
|           7 |    15 |   180 | Storybook - Donghae                    |            15 |                      0 |
|           8 |     1 |    13 | Olvia Academy Journal                  |             0 |                      0 |
|           9 |    10 |    53 | Old Moon Logs                          |             0 |                     10 |
|          11 |     9 |    45 | The Eyes of Adventure                  |             0 |                      0 |
|          12 |    13 |   138 | Storybook - Hwanghae                   |            13 |                      0 |
|          10 |     7 |    44 | Outer Edania                           |             7 |                      7 |
|          13 |     7 |    74 | Inner Edania (added 2026-09-27)        |             7 |                      7 |

The older fixture (`PAZ-Parser/tests/fixtures/journalquest.dbss`, 815 pages) has the same books, except journal 8 was a one-page placeholder (chain 896) instead of the 13-page Olvia Academy Journal.

---

## Localization

Journal and book text is in LOC `str_type=63`. The LOC key's second u32 packs `str_id2`/`str_id3` (low 24 bits) and `str_id4` (high byte), so this is the same as "low 24 bits select the book, high byte selects the field":

| LOC Field  | Value                                                                    | Notes                                         |
| ---------- | ------------------------------------------------------------------------ | --------------------------------------------- |
| `str_type` | `63`                                                                     |                                               |
| `str_id1`  | `journal_key`                                                            |                                               |
| `str_id2`  | `book_key`                                                               | `str_id3` is always `0`                       |
| `str_id4`  | `0` = journal name, `1` = journal description, `2` = unlock requirement, `3` = book name |                               |

Checked against all 112 books: `id4=0`, `1` and `3` exist for every book; `id4=2` exists for exactly the 61 books whose Korean `unlock_requirement_kr` is non-empty. The English journal name for every book is LOC 63 `id4=0`.

LOC type 63 also holds rows the file does not reference: `str_id2=0` rows for journal keys 1 to 13 (older journal names such as "Rulupee's Travels" under key 2). Journal key 13 ("Inner Edania", books 1 to 7) had LOC rows before it had records; the 2026-09-27 update added its 7 books.

Page text is LOC `str_type=18` keyed by the page's packed quest ID, like any quest:

| LOC Field  | Value                              | Notes                                         |
| ---------- | ---------------------------------- | --------------------------------------------- |
| `str_type` | `18`                               |                                               |
| `str_id1`  | `page_quest_id & 0xFFFF`           | Quest chain ID                                |
| `str_id2`  | `page_quest_id >> 16`              | Quest ID within the chain; no off-by-one      |
| `str_id4`  | `0` = title, `1` = story text      | See [quest.dbss](quest_dbss.md) for `2`/`3`   |

---

## Suggested UI Layout

| Column              | Type | Notes                                                                 |
| ------------------- | ---- | --------------------------------------------------------------------- |
| Journal             | num  | `journal_key`                                                         |
| Book                | num  | `book_key`                                                            |
| Journal Name        | text | LOC type=63 `id4=0`, falling back to `journal_name_kr`                |
| Description         | text | LOC type=63 `id4=1`, falling back to `journal_description_kr`         |
| Book Name           | text | LOC type=63 `id4=3`, falling back to `book_name_kr`                   |
| Unlock Requirement  | text | LOC type=63 `id4=2`, falling back to `unlock_requirement_kr` with PAColor markup stripped |
| Pages               | num  | `page_count`                                                          |
| Page Titles         | text | LOC type=18 `id4=0` for each page quest ID                            |
| Bookshelf Scene     | text | `bookshelf_scene`                                                     |
| Book Model          | text | `book_model`                                                          |

---

## Notes

- All records are located through `journalquestoffset.dbss`; the book records are self-describing (length-prefixed strings, counted page list), so the file can also be walked sequentially using the per-group `book_count` words.
- Strings are length-prefixed, so the odd byte offset of the first string (`+0x09`, after two u32 and one u8) has no alignment meaning.
- Unlock text uses BDO rich-text markup: `<PAColor0xAARRGGBB>` to set color (e.g. `<PAColor0xFFf3d900>`), `<PAOldColor>` to reset, and backtick-delimited quest names.
- Journal 6 ("Event Logs") is the only group whose Korean journal name differs between books (two variants: event logs and 10th anniversary event logs).
- Each page quest has a `quest.dbss` record whose `quest_category` is `11`; that value occurs on no other quest. Page records hold the journal's permanent Family-stat rewards (see [quest.dbss](quest_dbss.md)).

---

## Open Questions

### `unknown_08` Meaning

The byte at `+0x08` is `1` for every book of journals 7 ("Storybook - Donghae"), 10 ("Outer Edania"), 12 ("Storybook - Hwanghae") and 13 ("Inner Edania", added 2026-09-27) and for journal 6 book 8, and `0` elsewhere, including the other storybook journal 3. bdo-data-extractor also leaves it unnamed. Its effect (UI style, story mode, reward handling) needs an in-game comparison.

### Offset-Index Order vs Display Order

In journal 6 the offset file lists books as 1, 2, 10, 7, 8, 11, 12 while the data file stores them as 1, 10, 2, 7, 8, 11, 12. bdo-data-extractor states that the index order is the UI order; this has not been checked in game.

### Unreferenced LOC Type 63 Rows

LOC 63 has `str_id2=0` rows for journal keys 1 to 13 with names that do not match the current journals (key 2 is "Rulupee's Travels" in LOC but "Shakatu Merchants' Archive" in the file). Whether these are leftovers or something else is unknown. Journal 13 ("Inner Edania") was LOC-only until the 2026-09-27 update shipped its books, so LOC can run ahead of the data files.
