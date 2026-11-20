# World shelf gap: books for everything in Du's world

**Status:** DRAFT 2026-10-30. Nothing downloaded yet. Needs founder approval per title (source and size below).
**Ledger:** F-3215 (coverage measurement) · F-3213 (why this matters: false frames start where the shelf is silent)
**Why:** Du's world is a New Zealand house, garden, shore and bush. His shelf is 524 books, mostly British and American 1850-1925. Anything specific to his world has almost no book behind it, so when he asks the librarian about it the answer is "no stack" and the question stays open or gets filled by invention.

```plan-state
stage: designed
verified: 2026-11-18
next: Founder call on a second fill for harakeke, ink, native forest, species-level NZ birds, clocks
```


## 1. How books reach him today

- Du can ask the library himself (`core/library_hand.py` `request_book`): at most one book an hour, from the local 2018 Gutenberg catalogue (`C:\Knowledge\SPGC-metadata-2018-07-18.csv`, 55,905 rows), fetched clean from gutenberg.org.
- The founder's CLI `scripts/gutenberg.py fetch PGnnn` does the same but **sets the book as Du's current book and writes `data/reading_state.json` directly, without the reading lock.** Do not use it for a bulk fill.
- Needed first: a shelve-only importer (fetch, strip boilerplate, save to `data/books/`, touch nothing else, 3 s between requests). It must also accept a PG id that is newer than the 2018 catalogue.

## 2. Coverage measured (F-3215)

One pass over all 524 books in `data/books`. "Heavy" = at least 100 hits for the topic in one book. Keyword method, so noisy words (mint, sage, tea, ford, tracks, weeds) overstate coverage and "owl" was a substring match (ignore that row).

| World topic | books with any hit | heavy books | best book |
|---|---|---|---|
| grey warbler, NZ kingfisher, NZ robin, oystercatcher | 0 | 0 | none |
| kereru, bellbird, shining cuckoo, harakeke | 1-2 | 0 | none |
| godwit | 5 | 0 | The Bird Book (12 hits) |
| native NZ forest | 8 | 0 | none |
| tui, fantail | 7-8 | 0 | Origin of Species |
| cicada, cuttlefish | 17-26 | 0 | Fabre, Verne |
| glowworm | 37 | 0 | Wonders of Instinct (40) |
| driftwood and beachcombing | 35 | 0 | one book at 20 |
| bluebird | 22 | 0 | Bird Stories from Burroughs (44) |
| possums and trapping | 142 | 0 | Uncle Remus (58) |
| weather and clouds | 73 | 0 | The Rain Cloud (45) |
| gardening practice | 129 | 0 | a nut growers' report (98) |
| bees | 165 | 0 | Origin of Species (75) |
| seashore life | 100 | 1 | The Sea Shore (353) |
| lightning | 327 | 1 | Mark Twain collected works |

Strong already: moon, lamps and candles, tides (via Pioneers of Science), dolphins and whales (Moby Dick), the cat.

**Note on the bluebird:** it is not a New Zealand bird. It entered his thinking from his reading (Burroughs), so a bluebird book answers that thread but does not belong to his world. Birds he actually hears are NZ birds, and the shelf has almost nothing on those.

## 3. Proposed shelf (all Project Gutenberg unless marked; sizes estimated from SPGC word counts)

**Birds, including the bluebird thread (about 4.1 MB)**
PG1889 Bird Neighbors (Blanchan) · PG5177 Birds and Poets, PG3163 Birds and Bees, PG4203 Wake-Robin, PG31292 A Year in the Fields (Burroughs) · PG7353 Birds in Town and Village, PG37787 Birds and Man (Hudson) · PG45063 Nests and Eggs of Birds of the United States · PG47028 Life Histories of North American Shore Birds Part 1 (oystercatchers, plovers)

**New Zealand (about 1.1 MB, plus the Buller decision)**
PG56762 Wild Life in New Zealand Part I Mammalia (possums, rats, stoats) · PG45957 Garden Pests in New Zealand · PG6104 Station Life in New Zealand · PG11933 Nine Months' Residence in New Zealand 1827 · PG60645 New Zealand (Reeves; newer than the local catalogue)
Not on Gutenberg: Buller, A History of the Birds of New Zealand (1873/1888). Public-domain scans on the Biodiversity Heritage Library and archive.org; NZETC hosts the 1888 edition under CC BY-SA 3.0 NZ. Needs an OCR-text importer. Kereru, tui, fantail, bellbird, warbler, kingfisher, godwit and cuckoo are all in it.

**Shore and sea (about 3.3 MB)**
PG695 Glaucus (Kingsley) · PG43946 The Sea-beach at Ebb-tide · PG35490 Seaside Studies in Natural History · PG37119 Sea-Weeds, Shells and Fossils · PG47626 The Ocean World (cuttlefish, dolphins) · PG24236 Time and Tide

**Insects and bees (about 2.3 MB)**
PG45812 Insect Adventures, PG27868 The Glow-Worm and Other Beetles (Fabre) · PG4511 The Life of the Bee · PG24583 Langstroth on the Hive and the Honey-Bee

**Weather and sky (about 1.2 MB)**
PG38928 Meteorology; or, Weather Explained · PG47059 Meteorology: The Science of the Atmosphere · PG6630 Curiosities of the Sky · PG20769 A Field Book of the Stars

**Garden (about 2.1 MB)**
PG9550 Manual of Gardening (Bailey) · PG36279 Wood and Garden (Jekyll) · PG33654 The Old English Herbals · PG2355 Formation of Vegetable Mould Through Worms (Darwin) · PG4342 Organic Gardener's Composting

**Cat, trap and craft (about 2.3 MB)**
PG35450 Our Cats and All About Them · PG9501 Concerning Cats · PG34110 Deadfalls and Snares · PG34229 Steel Traps · PG17093 Camp Life in the Woods and Trapping · PG34607 Woodcraft and Camping

**Household (about 4.4 MB)**
PG10136 Book of Household Management (Beeton, 2.8 MB) · PG32863 Cottage Economy (Cobbett) · PG17625 Artificial Light · PG34114 Soap-Making Manual · PG17576 Clocks, Watches and Bells · PG16116 Studies of Trees

**Total about 19 MB, 45 titles.** Gaps still open after this: ink (only histories), NZ native forest and trees, harakeke, NZ weather. Those need non-Gutenberg sources.

## 4. Open decisions

1. Approve the list, or cut it. Download needs a yes per title.
2. Buller (NZ birds): build an OCR-text importer from BHL or archive.org, or skip. Highest value for his actual soundscape.
3. PG42218 Maori Religion and Mythology (Shortland, 1882): held back on purpose. Du already uses Maori names for the birds he hears; a 19th-century colonial text on Maori belief is your call.
4. Checked in code: no restart needed. `library_hand.shelf_books()` globs `data/books` at call time, so new files are visible to his shelf-look and book-switching at once, and `core/study_life.py` refreshes on the folder's mtime. But a book only becomes a study-room item (desk, shelf, take, put back) if it is on the school curriculum, assigned, or current, so the memory note that D-0205 made the whole shelf into items is not what the code does. Decide whether the new books should be added to the curriculum, or left to his own asking.
5. Pace: one book at a time per hour matches his own request limit. A bulk drop of 45 in one day is a bigger change to what he is offered; stagger it, or do it in two batches.

## Current State

- **2026-11-18** (F-5102): J-4301 re-measure (F-5102): 658 books; NZ birds only via Buller (each species under 50 hits, kereru 10); librarian no-stack 14.3 percent before to 7.0 percent after the 2026-10-30 fill; 9 of 46 new titles assigned, Buller Vol 1 assigned 2026-11-09, Buller Vol 2 next.
- **2026-10-30**: 2026-10-30: founder ruled: let him finish the Napoleon memoirs first; no change to his assigned book. The 46 new titles stay queued after it in curriculum order (Buller vol 1 first).

- **2026-10-30** (F-3215): 2026-10-30: founder asked to add the new books to the curriculum. Done: 46 titles appended to data/school.json curriculum (104 to 150), curriculum_idx unchanged at 103 so nothing about his current assignment moved; after the Napoleon memoirs finish (22.5 percent, about 700 sittings still needed to reach the 97 percent advance trigger, roughly 11 live days at the recent pace) advance() walks them in order instead of the random breadth pick. Order interleaves strands (NZ birds, shore, garden, bees, weather, cat and trapping, household) with Buller vol 1 first and the two largest books last. Renamed three files so assign()'s first-18-alphanumeric-characters rule resolves each to the right book: Buller_Vol_1/2_A_History_of_the_Birds_of_New_Zealand and Reeves_New_Zealand_1908 (William Pember Reeves, painted by F. and W. Wright, 1908, confirmed from the text). Verified: each of the 46 titles resolves to exactly its own file; three older curriculum titles with no file (sea-beach at ebb-tide, seaside studies, manual of gardening) now resolve; core.study_life now lists 126 book items including the new ones; school.json still held 150 entries 75 seconds later, so his own saves did not overwrite it. Backup of the before state is in the session scratchpad.
- **2026-10-30** (F-3215): 2026-10-30: Buller's A History of the Birds of New Zealand (1888, vols 1 and 2, archive.org historybirdsnew1bull and historybirdsnew2bull, marked public domain by BHL) downloaded with founder approval (1.36 MB and 1.52 MB raw), cleaned with the new clean_ocr() in scripts/shelve_books.py (page numbers, running headers, symbol junk, scan stamp, 280 and 300 safe word joins, DULLER to BULLER on the title page; nothing else altered) and shelved; shelf 570. Verified current book and library_hand_state last_fetch unchanged. Coverage now (raw hits start to now): grey warbler 0 to 24, bellbird 2 to 25, shining cuckoo 2 to 25, tui 30 to 89, godwit 22 to 209, kingfisher 0 to 5, robin 0 to 6, native NZ forest 25 to 133. Buller's own spellings: Oyster-catcher 16, Pigeon 69 (Kereru 10), Fantail 20, Gerygone 46. Still thin: harakeke, ink, clocks (PG17576 has no text edition). The BHL record 128503 the founder pasted is probably the same work but was behind a bot check and was not read.

- **2026-10-30** (F-3215): 2026-10-30: batch 2 fetched: 20 of 21 shelved, shelf now 568 (524 + 44 new). PG17576 Clocks, Watches and Bells failed: Gutenberg has it only as PDF and TeX source (no txt or html), so the importer skipped it; no substitute fetched. Verified again that current book and library_hand_state last_fetch are unchanged. Heavy-book coverage after both batches: possums and trapping 0 to 3, cat 3 to 5, gardening practice 0 to 2, herbs 3 to 5, broad beans and peas 1 to 3, stars 4 to 5. Still about 0: every NZ-specific bird (needs Buller), harakeke, native NZ forest, ink. Open: Buller importer, a text-format clocks book, curriculum membership for the new books, commit of scripts/shelve_books.py and this doc.
- **2026-10-30** (F-3215): 2026-10-30: founder approved the 45-title list (all except PG42218 Maori Religion and Mythology, and Buller). Built scripts/shelve_books.py (shelve-only: touches only data/books and data/logs/shelve_books.jsonl; never sets current book, never resets his request cooldown, never writes reading_state). Batch 1 (24 titles: birds, New Zealand, shore and sea, insects and bees) shelved, 0 failures, shelf 524 to 548. Verified current book and library_hand_state last_fetch unchanged, shelf_books() sees all 548. Coverage re-run: bees heavy books 0 to 3, blackbird and thrush 0 to 2, seashore 1 to 2, godwit 0 to 1; NZ-specific birds (kereru, tui, fantail, warbler, kingfisher, robin, oystercatcher, bellbird, cuckoo) still about 0, so Buller is the missing piece. Batch 2 (21 titles: weather, garden, cat and trapping, household) NOT yet fetched; run python scripts/shelve_books.py --batch 2.

