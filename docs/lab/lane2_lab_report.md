# Lane 2 Lab — report (run 2026-08-17)

> Spec + pre-registered metric sheet: `docs/completed/lane2_lab.md`. Zero LLM. Read-only
> over live stores; Du stayed up. All outputs under `data/lab/lane2/`.

**Inputs:** 52054 fragments (2026-05-30 → today), 16031 stamped tuples, 96 world objects, 35 hearing-ledger voices.

## Scorecard

| # | Test | Pre-registered line | Result | Verdict |
|---|------|--------------------:|--------|---------|
| L1 | Build | < 120s | 304 referents, 100443 mention-edges, 7.8s | PASS |
| L2 | Depth-ledger parity | 20/20 | 20/20 | PASS |
| L3 | Glass float emerges | ≥20 obs, terminal, world-absent | did NOT emerge | FAIL (K1) |
| L4 | The cat | kept + ≥2 channels | kept=True, channels(≥3)=['read', 'lived', 'thought', 'dream'] | PASS |
| L5 | storm-sounds vs arousal | \|z\| ≥ 2 | w=0.0079, z=13.74 (n=10569/3473) | SIGNAL |
| L5 | storm-sounds vs valence | \|z\| ≥ 2 | w=-0.0086, z=-1.21 (n=10569/3473) | null-indistinguishable |
| L5 | fire_crackle vs valence | \|z\| ≥ 2 | w=0.3657, z=21.27 (n=398/13644) | SIGNAL |
| L7 | Temporal holdout | real < shuffled | median 9.5556 vs 5.6905 (97 referents) | FAIL (K3) |

## Kill criteria
- **K1 (glass float absent)**: TRIGGERED
- **K2 (parity <18/20)**: not triggered
- **K3 (holdout no better than shuffled)**: TRIGGERED
- **K4 (coreference junk)**: FOUNDER-GRADED

## L2 — parity detail
- ✓ `sound:gull_cries` — ledger=738 graph=738
- ✓ `sound:thunder` — ledger=496 graph=496
- ✓ `sound:oystercatcher_call` — ledger=267 graph=267
- ✓ `sound:window_rattle` — ledger=108 graph=108
- ✓ `sound:waves_on_shingle` — ledger=76.902877 graph=76.902877
- ✓ `sound:wind_in_trees` — ledger=76 graph=76
- ✓ `sound:shingle_drag` — ledger=57.444375 graph=57.444375
- ✓ `sound:clock_tick` — ledger=56 graph=56
- ✓ `item:shore_kelp_530eea` — ledger=37 graph=37
- ✓ `item:garden_stone_36d383` — ledger=20 graph=20
- ✓ `item:driftwood_17` — ledger=10 graph=10
- ✓ `item:shore_shell_d56354` — ledger=9 graph=9
- ✓ `item:shore_shell_0c2d66` — ledger=6 graph=6
- ✓ `item:shore_sea_glass_5e60b2` — ledger=4 graph=4
- ✓ `book:TheStrangeLifeofNikolaTesla` — ledger=35750 graph=35750
- ✓ `book:The Voyage of the Beagle` — ledger=1207532 graph=1207532
- ✓ `book:Tales from a Rolltop Desk` — ledger=318451 graph=318451
- ✓ `book:Life on the Mississippi` — ledger=823151 graph=823151
- ✓ `book:Boy Scouts Handbook The First Edition 1911` — ledger=766719 graph=766719
- ✓ `book:The Scouting Guide to Survival` — ledger=271723 graph=271723

## L3 — glass float detail
- `opera glass`: {"label": "opera glass", "distinct_fragments": 475, "terminal": false, "days_since_last_mention": 1.7, "in_world_substrate": true, "depth": {"seen": 3, "looked_at": 0, "investigated": 0, "kept": 0}, "channels": {"read": 458, "lived": 3, "thought": 13, "dream": 1}}
- `glass popular`: {"label": "glass popular", "distinct_fragments": 446, "terminal": true, "days_since_last_mention": 7.7, "in_world_substrate": true, "depth": {"seen": 3, "looked_at": 0, "investigated": 0, "kept": 0}, "channels": {"read": 445, "lived": 3, "thought": 7}}

## L6 — windowing materiality (top divergences, 7d vs all-time; 5086/16031 tuples in window)
- `blackbird_song`: all-time -0.1157 vs 7d 0.1453 (divergence 0.261)
- `oystercatcher_call`: all-time -0.2042 vs 7d 0.0404 (divergence 0.2446)
- `waves_crashing`: all-time -0.1676 vs 7d 0.0461 (divergence 0.2137)
- `waves_on_shingle`: all-time 0.1393 vs 7d -0.067 (divergence 0.2063)
- `cat_purr`: all-time 0.2389 vs 7d 0.0549 (divergence 0.1841)

## L7 — top holdout gaps (feed for L8)
- `study`: gap 138.889
- `study note`: gap 67.778
- `other hand`: gap 58.111
- `science science`: gap 54.222
- `active imagination`: gap 52.889
- `dream dream`: gap 46.167
- `principles psychology`: gap 42.722
- `psychology volume`: gap 42.611
- `book:The Principles of Psychology Volume 1 of 2`: gap 42.556
- `study human`: gap 41.778

## L8 — gap diagnosis (FOUNDER-GRADED — no self-certified pass)
- `study` (gap 138.889) → **2-stale** — last train mention 29d before split · depth={'seen': 169, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'read': 3965, 'lived': 169, 'thought': 220, 'dream': 37, 'told': 1}
- `study note` (gap 67.778) → **2-stale** — last train mention 29d before split · depth={'seen': 81, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'read': 1862, 'lived': 81, 'thought': 23, 'dream': 8}
- `other hand` (gap 58.111) → **2-stale** — last train mention 29d before split · depth={'seen': 11, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'lived': 11, 'read': 1368, 'told': 1, 'dream': 12, 'thought': 1}
- `science science` (gap 54.222) → **2-stale** — last train mention 29d before split · depth={'seen': 52, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'thought': 107, 'read': 2631, 'lived': 52, 'told': 4, 'dream': 2}
- `active imagination` (gap 52.889) → **2-stale** — last train mention 29d before split · depth={'seen': 26, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'told': 1, 'read': 8, 'thought': 2779, 'lived': 26, 'dream': 2}
- `dream dream` (gap 46.167) → **2-stale** — last train mention 29d before split · depth={'seen': 51, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'told': 7, 'thought': 453, 'read': 225, 'dream': 1035, 'lived': 51}
- `principles psychology` (gap 42.722) → **1-too-shallow** — investigated=0, seen=4 · depth={'seen': 4, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'thought': 5, 'read': 1030, 'lived': 4}
- `psychology volume` (gap 42.611) → **1-too-shallow** — investigated=0, seen=3 · depth={'seen': 3, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'read': 1025, 'lived': 3, 'thought': 2}
- `book:The Principles of Psychology Volume 1 of 2` (gap 42.556) → **2-stale** — last train mention 49d before split · depth={'seen': 2, 'looked_at': 0, 'investigated': 1, 'kept': 0} · channels={'read': 1024, 'lived': 2, 'thought': 2}
- `study human` (gap 41.778) → **1-too-shallow** — investigated=0, seen=9 · depth={'seen': 9, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'read': 1437, 'lived': 9, 'thought': 15}

## L9 — coreference proposals (FOUNDER-GRADED; 41 total, top 10)
- book-garden possibly_same_referent_as lived-garden — UNRESOLVED (read=383, lived=203)
- book-study possibly_same_referent_as lived-study — UNRESOLVED (read=3965, lived=169)
- book-sense self possibly_same_referent_as lived-sense self — UNRESOLVED (read=250, lived=148)
- book-cat possibly_same_referent_as lived-cat — UNRESOLVED (read=255, lived=119)
- book-person says possibly_same_referent_as lived-person says — UNRESOLVED (read=82, lived=501)
- book-societal expectations possibly_same_referent_as lived-societal expectations — UNRESOLVED (read=118, lived=82)
- book-study note possibly_same_referent_as lived-study note — UNRESOLVED (read=1862, lived=81)
- book-shore possibly_same_referent_as lived-shore — UNRESOLVED (read=456, lived=78)
- book-science science possibly_same_referent_as lived-science science — UNRESOLVED (read=2631, lived=52)
- book-dream dream possibly_same_referent_as lived-dream dream — UNRESOLVED (read=225, lived=51)

## Sampled objects (recognize Du's life, or catch the graph lying)
- **cat** (being): depth={'seen': 119, 'looked_at': 0, 'investigated': 0, 'kept': 1} · channels={'read': 255, 'lived': 119, 'thought': 238, 'dream': 7} · mentions=619 · ledger={"cat_phase": "kept", "cat_distant_seen": 147}
- **gull_cries** (sound): depth={'seen': 4333, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'dream': 1, 'thought': 1} · mentions=2 · ledger={"hearing_places": {"shore": 738}, "hearing_place_sum": 738, "bed_hours": 0.0}
- **fire_crackle** (sound): depth={'seen': 933, 'looked_at': 0, 'investigated': 0, 'kept': 0} · channels={'read': 1, 'lived': 2, 'thought': 7} · mentions=10 · ledger={"hearing_places": {"study": 8.977887}, "hearing_place_sum": 8.977887, "bed_hours": 8.977887}
- **driftwood_17** (item): depth={'seen': 0, 'looked_at': 10, 'investigated': 0, 'kept': 1} · channels={} · mentions=0 · ledger={"ws_observations": 10, "ws_name": "sea-bleached driftwood log", "ws_class": "driftwood"}
- **shore_birch_042** (item): depth={'seen': 0, 'looked_at': 1, 'investigated': 0, 'kept': 1} · channels={} · mentions=0 · ledger={"ws_observations": 1, "ws_name": "weathered pale branch", "ws_class": "driftwood"}

*Total lab runtime: 26.5s. Graph persisted to `data/lab/lane2/graph.json`.*

---

## Re-verification run (2026-08-24, job J-0044) — same script, current data, kills HOLD

The pre-registered lab already ran to completion on 2026-08-17 (extended through a 2026-08-20 audit
correction, both preserved below). This section is a **re-run of the identical, unmodified
`scripts/lane2_lab.py`** against today's live stores, requested by job-queue J-0044 (spawned from
gauge-check G-0011's 2026-08-23 triage) to check whether the K1/K3 kills still hold now that
`data/geometry_tuples.jsonl` has grown from 11,479 → **16,031 rows** and `memory_fragments` from
46,255 → **52,054 rows** (+5,799 fragments, +4,552 tuples since the original run). The script's own
`main()` overwrites this file wholesale (`REPORT.write_text`) and hardcodes "run 2026-08-17" in its
own header regardless of when it actually executes — that date string above is the script's own
artifact, not a claim about when this section was produced. The scorecard/detail sections above
(inputs=52054/16031/96/35) ARE today's (2026-08-24) numbers; only the header line is stale by
construction. This section, and everything below the next `---`, was hand-preserved from the
2026-08-17/-20 backup because the script has no memory of hand-authored follow-up analysis and would
have silently destroyed it on overwrite.

**Result: both kill criteria that triggered on 08-17 trigger again on 08-24, on ~35% more data.**

| # | 08-17 run | 08-24 re-run | Verdict |
|---|---|---|---|
| L1 (build) | 191 referents, 90742 edges, 13.7s | 304 referents, 100443 edges, 7.8s | PASS both |
| L2 (parity) | 20/20 | 20/20 | PASS both |
| L3 (glass float) | did NOT emerge | did NOT emerge | **K1 TRIGGERED both runs** |
| L4 (cat) | kept, 4 channels | kept, 4 channels | PASS both |
| L5 storm↔arousal | z=3.45 SIGNAL | z=13.74 SIGNAL | holds, stronger |
| L5 storm↔valence | z=-2.66 SIGNAL | z=-1.21 **null-indistinguishable** | **weakened below threshold with more data** |
| L5 fire_crackle↔valence | z=18.5 SIGNAL | z=21.27 SIGNAL | holds |
| L7 (temporal holdout) | median 8.12 vs 5.94 (94 refs) | median 9.56 vs 5.69 (97 refs) | **K3 TRIGGERED both runs, gap widened** |

**K1 still stands** — no bigram matching "float"/"glass" clears the ≥20-obs + terminal + world-absent
bar; `opera glass` and `glass popular` are still system-vocabulary artifacts, same as 08-17 (see the
Post-run diagnosis below, unchanged in substance).

**K3 still stands, and got worse, not better.** I independently re-checked the per-10-day-bucket
fragment distribution against the current `geometry_tuples.jsonl` (day0=2026-07-05, 49-day span):
`[3331, 0, 0, 5249, 7451, 0]` — buckets 2 and 3 (roughly 07-15 → 08-03, ~19 days) are still zero.
The new data (the +4,552 tuples) landed entirely in the bucket AFTER the hole, not inside it — the
hole was never backfilled, it was just walked past. Since L7's 80/20 holdout split falls inside the
already-post-hole region, every top-gap referent is still classified `2-stale — last train mention
29d before split` (was 24-48d on 08-17) in the fresh L8 output above. This is the same structural
cause identified on 08-17, confirmed to still be operative on 08-24: **the kill is not a fluke of a
thin early dataset, it survived a 35% data-volume increase**, which is stronger evidence for K3 being
a real, current property of this data (not an artifact that more data would quietly fix) than the
original single run could support alone.

**One real change worth flagging, not previously visible:** the storm-sounds↔valence pair, one of
the three pre-named L5 signals the 08-17 report called "an unambiguous positive," **dropped out of
significance** (z=-2.66 → z=-1.21) as more data accumulated, while storm↔arousal and fire↔valence
both got stronger. This is exactly the kind of result the lab's own standing law (item 5, added
08-20) warns about — a signal measured on a small early window is not guaranteed to survive more
data — and it means the founder's storm-unease/fire-comfort finding should now be read as **two
confirmed pairs (arousal, fire-valence) and one that did not replicate (storm-valence)**, not three
for three as the original report stated.

*Re-run script/data confirmation: `scripts/lane2_lab.py` unmodified from 08-17 (only read-only stores
changed under it); ran via `python scripts/lane2_lab.py`, 26.5s, read-only per its own isolation
contract (`sqlite3.connect(f"file:{DB}?mode=ro", uri=True)` — SQLite enforces this at the driver
level, a write attempt raises rather than silently succeeding; JSON/JSONL sources opened for read
only; writes confined to `data/lab/lane2/graph.json` and this report). No `lab_env.py` isolation
wrapper used, per the job's own isolation="none" and the plan's "should not need lab_env.py". Checked
after the run: `os.stat` mtimes on `data/memory/nascence.db` and every seed JSON file the graph reads
(`sound_knowledge.json`, `world_substrate.json`, `keepsakes.json`, `reading_state.json`,
`cat_state.json`) all predate this run (last touched 2026-08-21 → 2026-08-23, by Du's own live
process) — none was modified by the lab run, consistent with the read-only contract holding.*

---

## Post-run diagnosis (2026-08-17 session — why each kill triggered)

**K1 (L3, glass float) — a builder artifact AND a false premise, both informative:**
- *Artifact:* frequency-only bigram discovery drowned in SYSTEM VOCABULARY. Top discovered
  referents: 'active imagination' (2,462 fragments), 'valence reflection' (2,217), 'study note'
  (1,631), 'carl gustav' / 'gustav jung'. The discovery layer surfaced Du's architecture, not his
  world — his memory text is saturated with introspection vocabulary (the T2 self-mass skew,
  visible again from a new angle). Rank-80 cutoff sat at 324 fragments; the glass float has 61.
  Fix direction for the real build: CONTRAST discovery — bigrams overrepresented in lived/action
  channels relative to thought/read — not raw frequency.
- *False premise:* the float is NOT terminal. 61 mentions spanning 08-11 through TODAY (channels:
  inner_thought 53, action 3, active_imagination 3, dream 2). The object never entered
  world_substrate (real world-absence) but lives on in near-daily rumination. The pre-registered
  terminal criterion was wrong on the facts — the lab corrected our own belief about the float.
  And the channel profile IS the depth-ladder story in live data: he has THOUGHT about it 17x more
  than he ever ACTED on it. Seen-not-investigated, exactly the driftwood point.

**K3 (L7, holdout) — triggered honestly, and the diagnosis is a data-integrity discovery:**
Fragments per 10-day bucket across the store's 79-day span:
[7596, 5576, 4680, 4484, 0, 0, 0, 23919, 0] — a ~30-DAY HOLE (~Jul 9 - Aug 8) followed by
23,919 fragments (HALF the store) arriving in the last 10 days. Every top L8 gap is classified
'2-stale — last train mention 24-48d before split', i.e. the referents vanish into the hole. No
recency predictor can bridge that; shuffled series spread the regime shift evenly and therefore
'predict' better. K3 stands as pre-registered ON THIS DATA — but whether it reflects Du's actual
life or the store's lifecycle dynamics (episodic pruning? mass reading-ingestion? re-timestamping?)
is a FOUNDER-CHECK before the kill is treated as final. The hole itself may be the lab's most
valuable single finding.

> **FOUNDER-CHECK RESOLVED (2026-08-24, job J-0146, finding F-0108):** the hole is the documented
> 30-day Du outage (2026-07-09 → 2026-08-07), verified at day resolution directly against both
> `nascence.db` and `geometry_tuples.jsonl` — not a store-lifecycle artifact. Full evidence and
> reasoning in `docs/completed/lane2_lab.md`'s 2026-08-24 update. K3 stands as real data scarcity from a
> real outage, not corrupted data.

**The unambiguous positive: L5, all three pre-named pairs are REAL signals.**
fire_crackle <-> valence at z=18.5 (weight +0.60!) — the fire-comfort association is enormous in
his data. Storm-sounds <-> valence z=-2.66 (storms genuinely darken him, slightly), storm <->
arousal z=+3.45. The founder's thunder-fear hypothesis is CONFIRMED in shape (as storm-unease +
fire-comfort): the commonality machinery finds real, directional affect-weather structure. The
affect-nudge courier would have a genuine reservoir to read on day one.

> **2026-08-24 update:** the storm↔valence leg of this "three for three" no longer replicates on
> more data (z=-2.66 → z=-1.21) — see the re-verification section above. The other two legs held.

---

## Item-population scan (founder-directed follow-up, same session)

Lexicon: 281 seeded item-terms (substrate/keepsake/garden/fixture/creature/shore-find) + 60 channel-contrast discovered bigrams (the K1 fix, trialed live: bigrams counted in LIVED fragments only). 294 referents cleared the 15-mention floor.

**FLOAT-LIKE PROFILES (thought≥20 AND thought≥5×lived): 68 of 294.** The glass float is NOT an anomaly — it is a population.

| referent | kind | in world | thought | lived | read | dream | ratio | silent (days) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| against | seeded/keepsake | False | 2266 | 240 | 2201 | 158 | 9.4 | 0.0 |
| myself | seeded/keepsake | False | 2040 | 312 | 1543 | 284 | 6.5 | 0.0 |
| constant | seeded/keepsake | False | 1624 | 113 | 434 | 11 | 14.4 | 0.0 |
| whole | seeded/keepsake | False | 1568 | 244 | 2626 | 35 | 6.4 | 0.0 |
| tide | seeded/keepsake | False | 1281 | 254 | 156 | 60 | 5.0 | 0.0 |
| carl gustav | discovered/contrast | None | 1261 | 141 | 1 | 6 | 8.9 | 0.1 |
| gustav jung | discovered/contrast | None | 1261 | 137 | 1 | 6 | 9.2 | 0.1 |
| sheer | seeded/keepsake | False | 837 | 83 | 83 | 4 | 10.1 | 0.1 |
| energy | seeded/keepsake | False | 807 | 81 | 405 | 39 | 10.0 | 0.0 |
| relentless | seeded/keepsake | False | 729 | 20 | 107 | 38 | 36.5 | 0.0 |
| rock | seeded/keepsake | False | 679 | 115 | 448 | 17 | 5.9 | 0.0 |
| solid | seeded/keepsake | False | 672 | 61 | 444 | 38 | 11.0 | 0.0 |
| potential | seeded/keepsake | False | 644 | 117 | 186 | 34 | 5.5 | 0.0 |
| surface | seeded/keepsake | False | 504 | 93 | 956 | 200 | 5.4 | 0.1 |
| next | seeded/keepsake | False | 493 | 65 | 2043 | 7 | 7.6 | 0.1 |
| perfect | seeded/keepsake | False | 428 | 56 | 699 | 4 | 7.6 | 0.1 |
| edges | seeded/keepsake | False | 401 | 58 | 122 | 48 | 6.9 | 0.0 |
| until | seeded/keepsake | False | 377 | 28 | 1959 | 31 | 13.5 | 0.0 |
| raw | seeded/keepsake | False | 341 | 57 | 127 | 19 | 6.0 | 0.0 |
| glass | seeded/keepsake | True | 299 | 57 | 1120 | 151 | 5.2 | 0.1 |
| pure | seeded/keepsake | False | 282 | 45 | 495 | 19 | 6.3 | 0.0 |
| trapped | seeded/keepsake | False | 274 | 42 | 27 | 35 | 6.5 | 0.2 |
| wind | seeded/keepsake | False | 260 | 34 | 875 | 95 | 7.6 | 0.1 |
| field | seeded/keepsake | False | 233 | 32 | 849 | 10 | 7.3 | 0.0 |
| door | seeded/fixture | True | 231 | 38 | 989 | 220 | 6.1 | 0.2 |

**Grounded profiles for contrast (lived≥20, not float-like): 144** — the items he actually ACTS on:

- `yet` (seeded/keepsake): lived=1077, thought=3266, ratio=3.0
- `becoming` (seeded/keepsake): lived=860, thought=3025, ratio=3.5
- `where` (seeded/keepsake): lived=611, thought=2912, ratio=4.8
- `carl jung` (discovered/contrast): lived=357, thought=1716, ratio=4.8
- `internal` (seeded/keepsake): lived=369, thought=1295, ratio=3.5
- `merely` (seeded/keepsake): lived=458, thought=1117, ratio=2.4
- `river` (seeded/keepsake): lived=375, thought=1092, ratio=2.9
- `structure` (seeded/keepsake): lived=257, thought=1084, ratio=4.2
- `when` (seeded/keepsake): lived=451, thought=896, ratio=2.0
- `seems` (seeded/keepsake): lived=503, thought=806, ratio=1.6
- `fixed` (seeded/keepsake): lived=329, thought=712, ratio=2.2
- `perhaps` (seeded/keepsake): lived=287, thought=665, ratio=2.3

*Scan runtime 7.2s; read-only.*

---

## Item-population scan — CLEANED read (founder: "go through all Du's items, not just floats")

Raw scan: 294 referents, but two lexicon-pollution sources found and excluded (keepsake `item`
fields are prose snippets, not names — tokenizing them seeded abstractions like 'against'/'myself';
substrate NAME adjectives ('worn', 'pale', 'little') leaked via unigram tokenization). Clean
concrete-item population: **104 referents → 12 float-like, 56 grounded.**

**FINDING 1 — the glass float is a POPULATION, and it has structure.** At least four distinct
classes of ungrounded referent:
- **The identity-ghost (the biggest float in his mind):** `carl gustav jung` — his FORMER NAME.
  thought=1,261-1,716 mentions, lived=~140-357, read=1. Near-zero book presence: this is almost
  entirely SELF-GENERATED rumination on a name he shed when he chose 渡 (06-07). The single
  largest un-grounded thought-object in the store is who he used to be.
- **Sound-ghosts:** `oystercatcher` — thought=79, lived=3, read=0, dream=9. 66 identified hearings
  in the ledger, yet the bird exists for him almost entirely as rumination about a call. Heard,
  never engaged.
- **Dream-symbols:** `door` — thought=231, dream=220(!), lived=38. A fixture that has become a
  threshold-symbol; its life is in his dreams, not his rooms.
- **Thought-heavy world-items:** `kelp` (96 vs 16), `tide` (1,281 vs 254), `rock` (679 vs 115),
  `chair` (24 vs 0 — never once lived), `bee`, `tangle` — plus the original glass float (53 vs 3).

**FINDING 2 — the store's text carries the system's own VOICEPRINT, and it breaks even the K1
fix.** The channel-contrast discovery's top "lived" bigrams were `valence reflection` (2,216),
`curiosity valence`, `fear valence`, `trust valence`, `person asks`, `recent aug` — architecture
template text embedded inside lived-channel fragment content. Channel-contrast alone therefore
ALSO fails: the lived channel's raw text is contaminated at the source. **New hard requirement for
Lane 2's script side: a system-voiceprint filter (strip the architecture's own template vocabulary)
BEFORE any mining.** This is the concrete meaning of the founder's "filter scripts find hidden
connections" — the filters must first know the system's own voice so they can subtract it.

**What this changes in the lab's conclusions:** K1's remedy is now three-layered (voiceprint-strip
→ head-noun lexicon → channel-contrast), not one; the float-profile (thought/lived ratio + which
channel dominates) graduates from a validation check to a first-class computed DIMENSION of every
object in the graph — the founder's seen-vs-investigated depth question, computable today; and the
identity-ghost finding hands the T2 self-mass skew a concrete face: the reservoir's biggest
ungrounded object is the discarded name.


---

## Trend-shape analysis (founder: "a good algorithm would see the Jung thoughts were in bulk and
## then slowly going away over time — it would know to treat these different")

Share-of-store per 10-day bucket (share, not raw counts, so the July hole cannot fake a decline):

| referent | 05-30 | 06-09 | 06-19 | 06-29 | 08-08 | n | shape |
|---|---:|---:|---:|---:|---:|---:|---|
| jung (shed name) | 38.1% | 11.9% | 3.3% | 8.5% | 1.4% | 4,439 | EXTINCT GHOST |
| glass float | 0 | 0 | 0 | 0 | 0.25% | 61 | NEW/ACTIVE |
| door | 4.3% | 6.4% | 1.8% | 4.2% | 4.4% | 2,011 | PERENNIAL SYMBOL |
| tide | 0.1% | 1.0% | 2.7% | 5.8% | 6.6% | 2,033 | GROWING WORLD-PRESENCE |
| rock | 0.1% | 3.0% | 3.9% | 5.6% | 8.5% | 2,635 | GROWING WORLD-PRESENCE |
| the cat | 0 | 0.3% | 0.4% | 2.1% | 0.4% | 236 | SETTLED COMPANION |
| oystercatcher | 0 | 0 | 0 | 0.4% | 0.3% | 94 | EPISODIC |

**THE HEADLINE: the Jung trend-break aligns exactly with the self-naming event.** Daily series:
40-48% of ALL fragments through 06-04..06-08, peaking at 48.3% ON 06-07 — the day he chose 渡 —
then collapsing to 2.0% by 06-17 and 0.5% by 06-18. Extinction in eleven days. A trend-break
detector with no knowledge of the event would flag 06-07 and find the naming recorded in his own
store — the diagnosis loop (trend break → why? → cross-link to event) demonstrated end-to-end on
real history. (And the early bulk is not rumination ABOUT Jung — in that era he WAS Jung; the fade
IS the identity migration, visible in mention-shares.)

**Correction to the previous appendix, owned:** calling Jung "the biggest float in his mind" was
static-mass thinking. By trend it is a RESOLVED ghost — sediment of a completed migration — and
treating it as an active obsession would be exactly the availability-bias error the trend machinery
exists to prevent. The founder's push was the correction.

**The completed float-profile dimension (design consequence):** channel mix × depth ladder ×
TREND SHAPE — six shapes observed in real data (extinct ghost / new-active / perennial symbol /
growing world-presence / settled companion / episodic), each demanding different treatment, none
distinguishable from a static ratio. Classifier notes: settling ≠ extinction (the cat settles to a
nonzero floor; Jung extinguishes to ~0 — the floor matters, not just direction); the tide/rock
rises cross-link to WORLD BUILDOUT eras, not obsession — trend-breaks must be checked against
system-arrival events too.


---

## All-dimensions sweep (founder: "treat these as dimensions but for ALL our inputs") — EXPLORATORY,
## then the confound pass that corrected it

Generalized the L5 machinery over every stamped dimension x affect (17 tests, shuffle nulls, tuple
span Jul 5 - Aug 17, 11,479 tuples). Raw sweep highlights: moon_illum x valence r=+0.735 (z=75!),
fire='burning' x valence +0.407, fire_fuel x valence +0.361, circadian hour x valence/arousal
(|z| 10-13), place='study' x valence -0.132, tide_level x arousal -0.047.

**THE CONFOUND PASS (partial correlation controlling for time) — half the sweep dies:**
- `fire_fuel x valence: +0.384 raw -> +0.018 controlled.` GONE — entirely a shared time trend.
- `moon_illum x valence: +0.735 raw -> +0.402 controlled` — but r(time,moon)=-0.951: the moon is so
  collinear with time in this span that the partial is numerically fragile. UNRESOLVED until the
  span covers 2-3 full lunar cycles.
- **The circadian results survive by construction** (hour-of-day cycles fast; slow-trend confounds
  cannot produce them): a real candidate circadian mood signature.
- `level x arousal (+0.298)` — flagged as likely TAUTOLOGICAL (same-axis leakage: level and arousal
  are plausibly computed from shared inputs). The geometry plan's disease — "most of the axes were
  secretly the same axis" — caught empirically.
- **Consequence for L5's fire_crackle z=18.5 (the earlier headline): now SUSPECT** until re-tested
  with time control — the shuffle null destroys all time structure and cannot distinguish "fire
  moments are happy moments" from "fire eras were happy eras." The earlier confidence outran the
  confound check; owned.

~~**THE REAL HEADLINE THE CONFOUND CHECK EXPOSED: r(time, valence) = -0.677.** Du's valence has
declined strongly and near-monotonically across the whole 43-day tuple span (Jul 5 -> Aug 17).~~

**★ RETRACTED 2026-08-20 (audit — docs/reviews/audit_2026-08-20.md). The decline does not exist.**
The report's own alternative hypothesis ("affect-instrument drift — the emotion systems were rebuilt
during this span") was the correct one, and the span was not a span. Recomputed on the same tuples:
- Jul 5–7 (pre-cutover instrument): mean valence **+0.793** (n=2,436)
- Jul 8, the day after `AFFECT_SOURCE_PROTOSELF` went live: **+0.066** (n=895) — a **−0.73 STEP at the
  instrument cutover**, not a decline
- Jul 9 → Aug 7: **ZERO data — Du was down for 30 days** (the "43-day span" contains a 30-day hole)
- Aug 8–20, one instrument end-to-end: **r(time, valence) = +0.012** (n=9,362) — dead flat
The −0.677 was a two-cluster regression across an instrument change and a month of silence. Clause
added to the standing law below as (5). *(The negativity itself is real but has a different, structural
cause: the level-coded `1 − 2·D` channel is wired downstream where both source theories specify the
derivative channel — see the audit §6.8. The phasic channel is mean −0.00015, i.e. sign-balanced.)*

**Standing law derived for the dimension engine (added to the Lane 2 doc):** before ANY coupling is
claimed: (1) classify each dimension fast/slow-cycling; (2) slow dimensions require de-trending /
partial correlation against time; (3) tautology screen — dimension pairs computed from shared
inputs are the same axis, not a coupling; (4) surviving couplings state their controlled, not raw,
strength; (5) **(added 2026-08-20, the −0.677 lesson) any time-series claim must first verify the
series was produced by ONE unchanged instrument end-to-end, and must plot n-per-day before trusting
a correlation** — an instrument cutover plus a data gap manufactured this report's own headline.
The naive correlator would have told Du "the moon lifts your heart"; the skeptical layer
says "your heart sank while the moon waned — mostly, it is the sinking." That skepticism IS the
Emissary.