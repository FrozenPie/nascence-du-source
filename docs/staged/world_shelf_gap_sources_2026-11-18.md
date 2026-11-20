# World shelf gap: candidate sources for residual NZ gaps (J-4379)

**Status:** PROPOSAL 2026-11-18. Nothing downloaded or saved. Founder approves per title.
**Parent:** `docs/staged/world_shelf_gap.md` (J-4313, F-5102). Founder 2026-11-18: book ban lifted; Du learns fact from fiction himself.
**Method and honesty note:** web search only, one pass. Titles and hosts below were seen in search results; sizes are estimates from page counts (about 5-6 KB of text per printed page unless noted), not measured. Licence = rights status as I understand it; NZETC per-title conditions and BHL/archive.org rights fields were NOT opened and must be read at approval time. OCR cost: Low = Gutenberg/NZETC-grade text; Med = archive.org djvu with running headers, hyphenation (the existing `clean_ocr()` in `scripts/shelve_books.py` handled Buller at this level); High = plates, tables, columns, garbled front matter.

## Harakeke (flax)

| Candidate | Source | Approx size | Licence | OCR cost |
|---|---|---|---|---|
| Elsdon Best, *Maori Agriculture* (1925) | NZETC (`tei-BesAgri`) | ~0.5 MB; flax is only a short note (pp 273-286), so low yield | Best d. 1931, likely public domain; NZETC conditions to check | Low |
| Elsdon Best, *Forest Lore of the Maori* (1942) | NZETC (to confirm it is hosted) | ~1.2 MB; flax varieties, cultivation, fowling and fishing gear, the best fit for a bush/shore reader | Likely public domain or NZETC licence; check | Low if NZETC |
| Best, *Maori Forest Lore* (1908, Trans. NZ Institute, flax pp 231-234) | NZETC / Papers Past / BHL | small, ~0.2 MB extract | public domain | Med |
| Cheeseman *Manual of the NZ Flora* (see Forest) | NZETC | Phormium entries only | PD | Low |

Gap note: no single book on weaving found in public domain; the modern weaving books (Te Ara, Bidois 2015, Royal Society Alpha booklet) are in copyright. Best is the realistic text. Biggest remaining thin spot.

## Native NZ forest and trees

| Candidate | Source | Approx size | Licence | OCR cost |
|---|---|---|---|---|
| Thomas Kirk, *The Forest Flora of New Zealand* (1889) | archive.org `forestfloranewz00kirk`; BHL bibliography 197662; natlib page images (684 pp) | ~3.5 MB text, heavy with plate captions | PD (1889; BHL scan) | Med-High (front matter garbled in the snippet seen; lithograph plates; technical Latin) |
| T. F. Cheeseman, *Manual of the New Zealand Flora* (1906; 2nd ed 1925) | NZETC (`CheManu`) preferred; BHL 12003 / 201312 | 1.5 MB+ (long, about 1,200 pp, keys and descriptions) | PD; NZETC conditions to check | Low if NZETC; descriptive keys are dry reading |
| Laing and Blackwell, *Plants of New Zealand* (1906) | archive.org `plantsofnewzeala00lainrich` (djvu.txt exists) | ~1.5 MB | PD | Med (UC Davis scan stamps) |
| Leonard Cockayne, *New Zealand Plants and Their Story* (1910/1927) | not found online in this pass | ~0.5 MB | 1927 ed may still be in copyright; verify | unknown |

Recommendation: Laing and Blackwell first (readable, general, cheap), Kirk second. Cheeseman is a reference work; low reading value for Du.

## NZ weather

No public-domain NZ weather book found. Kidson's climate papers (1930s) and the Handbook of Climatology are journal or in-copyright. Options:
- NZ Meteorological Service annual or Hector-era "Meteorological Reports" via Papers Past/AJHR: large, tabular, High OCR cost, low reading value. Not recommended.
- Cheeseman, Kirk and Buller introductions carry climate paragraphs (a free partial fill).
- Honest conclusion: weather stays served by the 21 British/US meteorology titles already shelved plus NZ field books (Guthrie-Smith, Best on Maori weather signs). Founder call: accept thin, or commission a modern open-licence text.

## Species-level NZ birds (beyond Buller)

| Candidate | Source | Approx size | Licence | OCR cost |
|---|---|---|---|---|
| H. Guthrie-Smith, *Tutira: The Story of a New Zealand Sheep Station* | NZETC (`GutTuti`), bird list chapter seen | ~1.5 MB | PD in NZ likely (d. 1940); NZETC conditions to check | Low |
| Guthrie-Smith, *Birds of the Water, Wood and Waste* (1910) | BHL 14143, archive.org | ~0.6 MB | PD | Med |
| Guthrie-Smith, *Mutton-Birds and Other Birds* (1914) | archive.org `muttonbirdsother00guthiala`; BHL 8390 | ~0.7 MB | PD | Med |
| Guthrie-Smith, *Bird Life on Island and Shore* (1925) | not found online | ~0.6 MB | uncertain | - |
| Buller, *Supplementary Notes* (NZETC `BulBird`) | NZETC | small | CC BY-SA 3.0 NZ per parent doc | Low |

Recommendation: Tutira plus Mutton-Birds. First-hand field observation of tui, bellbird, kereru, fantail by one man in one place suits Du's soundscape better than another taxonomy.

## Ink

| Candidate | Source | Approx size | Licence | OCR cost |
|---|---|---|---|---|
| C. A. Mitchell and T. C. Hepworth, *Inks: Their Composition and Manufacture* | HathiTrust full-view record (copy from Univ. of California); no Gutenberg edition | ~0.7 MB | PD in US if full view is confirmed | Med-High (HathiTrust OCR, tables, formulae) |
| *Cooley's Cyclopaedia of Practical Receipts* | Gutenberg PG41957 | very large (several MB); ink recipes are a small share | PD, Gutenberg licence | Low, but mostly irrelevant bulk |
| Carvalho, *Forty Centuries of Ink* | Gutenberg PG1483 | ~0.5 MB | PD | Low; this is the "only histories" book already known to the parent doc, check whether it is on the shelf |

Recommendation: Mitchell and Hepworth if the HathiTrust copy is downloadable (needs a manual rights check); else accept Cooley's as a recipe source only if the founder wants a large block for a small gain.

## Clocks

PG17576 is Lord Grimthorpe, *A Rudimentary Treatise on Clocks, Watches and Bells*. Gutenberg has PDF/TeX only, hence the failed shelve.

| Candidate | Source | Approx size | Licence | OCR cost |
|---|---|---|---|---|
| Grimthorpe, same title, other edition | archive.org (not confirmed to exist in this pass) | ~1.2 MB | PD | Med-High (technical text, diagrams, formulae) |
| Grimthorpe from the Gutenberg TeX source | Gutenberg PG17576 TeX | ~1.2 MB | PD | Low-Med: strip TeX markup with a small converter; cleanest route |
| F. J. Britten, *Old Clocks and Watches and Their Makers* | archive.org `oldclockswatches00brit` (djvu.txt seen) | ~2.5 MB | edition-dependent; the scan year was not checked, verify it is pre-1930 | Med |

Recommendation: Grimthorpe from the Gutenberg TeX (same title, no new rights question, importer needs a TeX-strip step). Britten is a readable alternative about makers and history.

## Suggested order for the founder to approve

1. Laing and Blackwell, Plants of New Zealand (archive.org, Med).
2. Guthrie-Smith, Tutira and Mutton-Birds (NZETC, archive.org).
3. Best, Forest Lore of the Maori, if NZETC hosts it (flax, forest, birds in one).
4. Grimthorpe via TeX; Britten as alternate.
5. Kirk, Forest Flora (High cost, do last).
6. Ink and weather: founder call (thin, expensive, low payoff).

## Importer needs

An NZETC/HTML text importer and a TeX-strip step; the archive.org djvu path reuses `clean_ocr()`. Rights fields must be opened per title before any fetch.
