# J-4123: narrow deterministic misattribution check on a larger memoir-style gist set

Status: DONE (negative on precision for the narrow and relaxed-frame forms; one post-hoc form with 3 of 3 is not testable). Nothing in core/ changed. No build job spawned.

## Set
All 1828 gist fragments (origin='gist') rebuilt read-only from data/memory/nascence.db with their `distilled_from` sources (`J-4123_build_items.py`, `J-4123_all_gists.json`). The 21 dated backups under data/backups hold the same 1828 gist ids, so they add no new items. 408 gists have `[From '...']` source fragments, 293 of them pass the first-person gate (>= 5 I/my/me). The corpus is memoir-poor: of 8 memoir/letter/diary/narrative titles, `Complete Project Gutenberg Collection of Memoirs of Napoleon` supplies 338 of 516 source fragments (it is Bourrienne's memoir, narrated by Bourrienne, about Napoleon). The next largest are Missionary Travels (54), Brook Farm (35), Mendelssohn letters (20), Portuguese Nun, Plague Year, Lucknow diary, Rowlandson narrative.

## Labels (hand, `J-4123_labels.json`)
4 misattribution positives: 1799 (= J-4038 #60), 1702, 1614 (all Napoleon's-memoirs gists giving the narrator's own experiences or preface aims to Napoleon) and 1443 ("James Ward's essay" for William James's Will to Believe). Scope of hand reading is in the labels file; the roughly 190 first-person gists whose absent names are titles or places were not read, so recall is recall within the labelled scope, not corpus recall.

## Results (flags over the 408 [From] gists)
| rule | flags | TP | FP | precision | recall (of 4) |
|---|---|---|---|---|---|
| broad (any absent proper noun + other name) | 115 | n/a | most are titles and places | unusable | not computed |
| narrow (J-4038: absent possessor of a memoir/diary/letters frame) | 772, 1209, 1443, 1593, 1799 | 1443, 1799 | 772, 1209, 1593 | 0.40 | 0.50 |
| relaxed R2 (any possessive frame, first-person bodies, no absence test) | 499, 772, 1209, 1443, 1593, 1614, 1664, 1702, 1799 | 4 | 5 | 0.44 | 1.00 |
| R3 post hoc (memoirs-possessive, name is in the title, first-person bodies) | 1614, 1702, 1799 | 3 | 0 | 1.00 (Wilson 95% lower bound 0.44) | 0.75 |

## Reading
- The narrow rule does not hold. Its two hits are one real case and one lucky one (1443 flagged because "Ward" is absent and the "other name" was the junk token "Suppose"). Its false flags are faithful gists where the author or letter writer is only in the title tag (Mendelssohn's letters, Thoreau) or a truncated title (Rowla).
- Its design cannot see 1702 and 1614: the name (Napoleon) is present in the body, so the absence test never fires. The real signal is "memoirs of P" where P is the subject, not the narrator, which a title string cannot tell apart from "Letters of Felix Mendelssohn" (author = subject). No lexical rule separates them.
- Relaxed R2 catches all four but blocks 5 faithful gists; as a pre-store guard it would reject more good gists than bad.
- R3 is 3 of 3, but it was written after labelling, all three hits are one book, and a 3-sample bound is wide. It is effectively a "Napoleon's memoirs" rule. Not evidence for a general guard.
- Extra design lesson: the rules only read `[From ...]` bodies; study-note sources (`[My study note ...]`) carry names the gist legitimately repeats (Yeats in #175, Josephine in #1393), so absence from [From] bodies is not absence from the sources.
- Base rate: 4 positives among the ~85-gist labelled memoir-style scope; all four are in one source book, 3 of them are the same failure (the narrator-versus-title-person swap, the gist "voice" taking the title person's name).

## Verdict
Do not build the narrow or R2 form as a pre-store guard. The cheap signal is useful as a router, not a gate: send gists matching R2 (possessive memoir/letters/diary frame over first-person bodies, ~2% of gists) to the full claim-typed grader (J-3083 variant b, which caught 2 of 3 known errors) rather than rejecting. Follow-up job spawned for that.

## Isolation
Read-only (mode=ro) opens of data/memory/nascence.db and data/backups/*.db; no model calls; no core/ import. Live DB files unchanged (nascence.db mtime 2026-11-16 15:23, wal 22:10, both before this job started today).
