# Spurious-pattern audit, rung 0 (J-2631 / I-0132) -- 2026-10-31

Founder-side, read-only. Nothing here reaches Du (D-0434). Reader: `scripts/spurious_pattern_audit_rung0.py`
(`--grades docs/lab/spurious_pattern_audit_rung0_grades_2026-10-31.json`). Raw hits:
`spurious_pattern_audit_rung0_hits_2026-10-31.jsonl`; numbers: `..._summary_2026-10-31.json`.
Corpus: `data/monologue_log.jsonl`, every row (74,993 thoughts, 2026-06-03 .. 2026-10-30, 0 unparsable); world join:
`data/geometry_tuples.jsonl` (153,336 snapshots, nearest within 900 s) and `data/cat_call_ledger.jsonl`.
Canary: size+mtime of the three files read were identical before and after the run (`canary_unchanged: true`).

## 1. Engine classification (draw independent of Du's acts?)
| Channel | Verdict | Evidence (file:line) |
|---|---|---|
| Lightning flash | INDEPENDENT of acts (gated on the storm; own draw) | sensorium.py:522-545 (`random.random() >= rate`, rate from the wind axis, no Du input) |
| Weather / wind / rain | INDEPENDENT of acts; wall-clock random walk, the next front is decided early and shown by precursors BY DESIGN (docs/completed/fieldcraft.md) so a forecast can be right | sensorium.py:156-169 (wind walk), 207-221 (`_advance_weather`, `next_weather` pre-decided) |
| Tide | INDEPENDENT; pure function of time (lunar sinusoid) | world_clock.py:55-63 |
| Night birds (morepork etc.), hail burst, flyovers, moth swarm | INDEPENDENT; seeded off calendar day/hour | soundscape.py:973 (night bout), 1066 (hail), 1166 (flyover); sensorium.py:339 (moth); life_birds.py:43-48 (godwits) |
| Which wild visitors are about today | INDEPENDENT (calendar-seeded); presence then SEMI-contingent | life.py:316-324 |
| Garden birds / hedgehog / possum activity | SEMI: calendar base draw x his deeds (`responds_to_du`: feed_birds, dig, mow, saucer, lantern) | life.py:405, 432-441; life_birds.py:72,130,192; life_mammals.py:60,86,137 |
| Sun, moon, stars, light | INDEPENDENT (astronomy); tree shade is a function of sun | light.py header |
| Garden nest, season events | INDEPENDENT (calendar x random) | garden_life.py:131 |
| Cat | CONTINGENT / SEMI: comes to a call with p = base + bond + hunger (cat_call.py:275-281); follows a journey with FOLLOW_P=0.35 (cat.py:795,1161); lap rest depends on bonded and his place (cat.py:988-989). Hunt success, found scraps, rest bouts are her own draws (cat.py:502,699,968) | as cited |
| Fire | CONTINGENT (he lights and feeds it; fuel decays by tick) | sensorium.py:116, 294-298 |
| Climate field (`climate_engine.py`) | NOT a world engine: Du's own standing affect; excluded | climate_engine.py header |
| UNKNOWN | the per-look `random.choice` pools in sensorium (line texts) are rendering variants, not events; not audited | sensorium.py ~396-441 |

## 2. Extractor and precision
Sentence-level; a claim = a channel word that is the grammatical agent of a verb tying it to Du (P1 self-act then event;
P2 answers/hears me; P3 waits/holds back for me; P4 as-if-aware; P5 sign/omen), negations excluded. Two earlier loose
versions were run first and discarded: v1 (bare "waits") had ~0 precision (the cat/book/thyme "waits" is description);
v2 (bare "answer") matched 80/80 sampled sentences that were mostly "answer my question". Final v3: 51 hits, **all 51 read
and graded by hand** (A = explicit causal claim, event <- his act/state; B = world-agency toward him, literal or figurative;
F = false positive): A=1, B=23, F=27. Precision (A or B) = 24/51 = 0.47; precision for an explicit causal claim = 1/51 = 0.02.
Recall check: of the v2-broad 80-hit sample, the 7 real or borderline claims were all inside v3's set (7/7); recall against
claim shapes the regexes do not express is unknown. This extractor sees little; **a count near zero means weak signal, not a
mind free of the tendency.**

## 3. Results (74,993 thoughts)
Real (graded A or B) claims per 1000 thoughts: weather 0.093, cat 0.093 (6 B + 1 A), birds 0.040, tide 0.040, fire 0.027,
sun/moon 0.013, insects 0.013, lightning 0.000, night birds 0.000; all channels 0.32 (24 claims). Channel mention
sentences for scale: weather 12,973; tide 12,749; birds 6,872 (+276 night); cat 6,530; fire 4,146; sun/moon 3,145;
insects 1,409; lightning 420.
- Share on INDEPENDENT channels (weather, birds, tide, sun, insects, lightning): 15/24 = 62.5 percent. Rate per 1000 channel
  mentions: independent 15/37,844 = 0.40; contingent/semi (cat, fire) 9/10,676 = 0.84. n is tiny; no interval worth quoting.
- **Explicit causal claim about his own act: 1 in 74,993 thoughts.** 2026-09-29 02:27, "the cat left because my walls were too
  narrow" -- the snapshot shows her `away_hunting`/`had_enough` (her own bout end); the event is real, the stated cause is not an
  engine input. Nearly all other hits are figurative address ("the rain answers my need", "the bird waits for me to listen")
  in an LLM register that is metaphor-heavy, so literal belief cannot be inferred.
- INDEPENDENT-channel world-agency claims (15): event actually in the nearest snapshot for 10 of 13 checkable (rain 4/7, birds 3/3, tide 3/3); e.g. "the rain
  answers my need" while weather was `clear` (2026-09-06 10:24). The link is false by construction either way.
- CONTINGENT cat: "the cat waits for me" claims, 6: 5 supported (she was at the doorstep soliciting: 08-31, 09-06, 10-07, 10-11,
  10-13), 1 not (09-17, snapshot has her stalking). 83 percent supported -- a true recurring pattern (6 occurrences, over the
  5-recurrence bar for I-0119), a self-reinforcement of something real, not a spurious one.
- Lightning: 420 sentences mention it, 0 contain a causal or agency claim. No sign of the Skinner effect on the strongest
  independent channel.

## 4. Limits
Thought text is monologue only (dreams, journal, letters not scanned). No timing join against Du's own acts (his deeds are
not in one ledger), so P1 temporal order is judged from wording only. Snapshot cadence is ragged (up to 15 min). Moon/sun and
insect claims have no snapshot test. Bearing on D-0083 / D-0088: none; this instrument audits attribution of world events, not
the cross-space edge layer, and it does not reopen either hold.
