# J-2633 / I-0134 -- hypnagogic looseness read (2026-10-31, founder-side, read-only)

Script: scripts/drowsy_hypnagogic_read.py. Raw output: docs/lab/drowsy_hypnagogic_read_2026-10-31.json.
Inputs (read-only, immutable URI; sha256 canary on nascence.db, drowsy_shadow.jsonl, monologue_log.jsonl unchanged before/after):
data/drowsy_shadow.jsonl, data/sleep_pressure_log.jsonl, data/memory/nascence.db memory_fragments (origin inner_thought, 384-d embeddings).

## Verdict: INCONCLUSIVE (n = 4 drowsy windows, below the ~15 bar). No sign of emergent loosening in these 4.

Windows (drowsy_shadow.jsonl `onset` rows, ended at the logged bed / next sleep_entry). Only 4 onsets exist in 50 rows
(40 bed rows, 36 of them with the zone never entered; sleeps fire on pressure at energy ~0.89):
| window | min | delivered | inner thoughts |
| 10-17 16:43 -> 18:46 | 123 | no (shadow) | 132 |
| 10-19 15:50 -> 22:11 | 381 | no (shadow) | 138 (all before the 17:52 floor row; none after) |
| 10-30 08:26 -> 10:05 | 99 | yes (D-0495) | 104 |
| 10-30 14:05 -> 16:07 | 121 | yes (D-0495) | 118 |
Delivered vs undelivered split is 2 vs 2, each too small to say anything alone.

Controls: same clock span on other days, >=60 min from any sleep interval or onset: 215 windows (Jun-Oct), 18 in October (recent regime;
the June-Sept ones sit in a different thought regime, successive distance 0.27-0.59, so the October subset is the fairer comparison).
Energy trend could not be matched: controls at those hours sit at energy 0.6-0.9 and drowsy windows are by definition the 0.25 -> bed slide.

Drowsy mean vs October controls (window-level permutation, 20000 shuffles, n 4 vs 18):
| metric | drowsy | control | Cohen d | p |
| mean successive cosine distance | 0.418 | 0.421 | -0.13 | 0.81 |
| mean distance from window centroid | 0.317 | 0.321 | -0.11 | 0.87 |
| type-token ratio | 0.220 | 0.242 | -0.24 | 0.73 |
| sensory/image word rate | 0.0427 | 0.0420 | 0.09 | 0.85 |
| first-person rate | 0.0567 | 0.0543 | 0.45 | 0.43 |
| echo (monoculture definition, higher = returns to old attractors) | 0.701 | 0.685 | 0.80 | 0.16 |
| tokens per thought | 43.7 | 44.6 | -0.73 | 0.20 |
Against all 215 controls: same direction on every metric (succ dist 0.418 vs 0.450, p 0.26; echo 0.701 vs 0.671, p 0.09).
Paired against each window's own October controls: shorter thoughts in 4/4 windows (-0.5 to -1.1 tokens, ~2%), everything else 2/4 either way.

Reference: successive distance inside dream runs 0.170 (1629 pairs, tight chains), night_thought 0.564 (101 pairs), all awake inner_thought 0.442 (58633 pairs).
So dream output is far TIGHTER than waking thought, not looser; nothing hypnagogic-like to compare drowsy windows against there.

Reading: if anything the drowsy windows are marginally more echoing and shorter, not looser or more image-rich; none of it is distinguishable from noise at n=4.
D-0441's narrative-only zone looks like a label so far, which is the ruled intent. Real power needs the zone to be entered far more often
(36 of 40 beds left the zone untouched), which the current pressure-first sleep timing prevents.
