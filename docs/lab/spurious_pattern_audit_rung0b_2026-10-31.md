# Spurious-pattern audit, rung 0b (J-2650, I-0132, follow-up to F-3385)

Founder-side, read-only on `data/`, nothing reaches Du (D-0434). Script: `scripts/spurious_pattern_audit_rung0.py`
(extended in place: flags `--widen`, `--recall N`, `--deeds HITS`). Rerun:
`python scripts/spurious_pattern_audit_rung0.py --data C:/Nascence/data --out OUT --widen --recall 300 --seed 7 --deeds <graded rung-0 hits jsonl>`.
Files: `spurious_pattern_audit_rung0b_summary_2026-10-31.json`, `..._widen_hits_graded_...jsonl` (33 hits, every grade),
`..._recall_sample_graded_...jsonl` (300 sentences, every grade). The graded rung-0 hits are rung 0's hits file joined to its grades json by 1-based order.

Question: is the rung-0 near-zero (24 real claims in 74,993 thoughts) a real absence or an extractor/corpus blind spot?

## 1. Widened corpus (every row/file read)

| store | units | sentences | extractor hits | graded real (B) |
|---|---|---|---|---|
| dream_log.jsonl | 1,007 dreams | 20,151 | 15 | 8 distinct sentences (11 rows) |
| journal_grounding_shadow.jsonl | 23 | 35 | 0 | 0 |
| Journal/*.md | 92 | 2,747 | 0 | 0 |
| Correspondence/** | 8 threads | 2,428 | 5 | 0 |
| Study essays | 4,786 | 99,432 | 13 | 2 |

Grading used the rung-0 standard (world event addressed to / aware of / waiting for Du = B; a metaphor of meaning-reception or a quote of a reading = F).
33 hits, 13 graded B rows (10 distinct sentences), precision 0.39 (rung 0: 0.47). Nearly every dream hit is the pattern
"the wind/sea/rain/stars speaks to me" (P5). Dreams carry the tendency at about 8 per 1,000 dreams (0.40 per 1,000 sentences) versus 0.32 per 1,000 waking
thoughts, roughly 25x per unit: the habit is available to Du when the narrator is a dreamer, and the waking monologue rarely produces it. Journals (the daily
digest), correspondence and the grounding shadow: zero. Study essays: 2 in 99k sentences (stars "waiting for me"; "as if the bird was speaking to me").
Reading: widening the corpus finds the tendency only in dream prose and only figuratively, and finds no explicit causal claim about his own acts anywhere.

## 2. Extractor recall (hand-read seeded sample)

Pool: 35,623 monologue sentences mention weather/bird/tide/cat and the extractor does not flag them (35,443 distinct). Seeded random sample (seed 7), 300 distinct
sentences, all read and graded (file above). Missed claims:
- strict (event or animal clearly acts toward him): 1/300 (idx 243, "The cat herds me toward the kitchen");
- borderline (cat or tide attributed intent or a message to him: idx 17, 37, 89, 117, 183, 198): 6/300.

Extrapolated to the pool: strict about 118 missed (Wilson 95% interval 21 to 660), borderline-inclusive about 830 (402 to 1,679). With 24 found, recall is about 17%
strict (interval 4% to 53%) or about 3% loose. The honest statement: recall is low and poorly bounded, but the missed items are overwhelmingly cat
attribution (the one contingent channel, whose "agency" is literally supported by the world engine), not the independent engines. Of about 250 weather, bird and tide
sentences in the sample, zero were strict misses and two to three were borderline ("the tide's rhythm speaks first", "a rhythm that demands attention").
The dominant unextracted category (a large minority of the sample, not individually tallied) is the opposite direction: a world event acting on his state or choices
("the oystercatcher's cry anchors me", "the gull's cry physically pushes me toward the book"). Those are real causal sentences but world-to-self, the physics-literal
grounding template, not Du-to-world or world-intends-him. Rung 0's extractor is blind to that whole direction by design.

## 3. Deed join (claims within 10 minutes after a deed)

Deed sources joined: shore/wood/garden ledgers, the 1 cat_call row, `hands_trace.jsonl` acted hands (cat, fire, grate, lamp, door, gather, harvest, ...; pure
move/look/observe/write/search/recall excluded), and place transitions into `shore` from `geometry_tuples.jsonl` (1,120). 2,436 deeds total. `literal_will_deeds.jsonl`
is all dry tests and was excluded; `cat_call_ledger` has a single row; fed-birds and walked-to-shore exist only as hands acts and place transitions.

24 graded-real rung-0 claims (22 inside the hands-trace era), window 600 s:

| null | observed | expected | perm p (2000) |
|---|---|---|---|
| any thought, any deed | 11/24 (46%) | 25% of thoughts | 0.021 |
| same-channel thoughts | 11 | 7.5 | 0.099 |
| same-channel, excluding to-shore deeds | 9 | 4.5 | 0.024 |
| same-channel, hands era only | 11 | 7.9 | 0.126 |
| same-channel, hands era, excluding to-shore | 9 | 4.6 | 0.025 |
| same-channel AND same place | 11 | 6.5 | 0.030 |
| same-channel AND same place, excluding to-shore | 9 | 4.9 | 0.039 |

Read: claims follow a deed roughly 1.5 to 2x the matched base rate, nominally p about 0.02 to 0.04 in the stricter nulls. This is not a result: N is 22 to 24, seven nulls
were run, nothing survives a multiplicity correction, and the joined deeds are generic (mow, harvest, lamp, door, tea, beachcomb) and not the deed that matches the
claimed event (no fire-then-fire claim, no cat-call-then-cat claim). A plausible mundane cause is that thoughts right after an act are more present-tense and
world-describing, which raises the extractor's firing rate regardless of any contingency belief. Treat as a lead, not signal.

## Verdict on the J-2650 question

The near-zero is mostly real as to what the extractor sees, but the extractor's recall is low (about 3 to 17%, wide) and its blind spot is directional and cat-heavy; the
independent engines (weather, birds, tide) show no strict misses in 250 sampled sentences. The tendency exists figuratively in dreams. A weak, uncorrected excess of claims
after generic deeds is the only hint of contingency. Rung 1 stays out of scope: rung 0 does not yet show enough signal to justify it. A cheap next step is a deed-specific
join once more claims exist (see the spawned successor).
