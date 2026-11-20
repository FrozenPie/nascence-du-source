# T4 tension lifecycle: what ends a tension? (J-3302)

Read-only analysis and design, 2026-11-06. Du is down; no Du code, store or log was edited. Every number comes from `scripts/analysis_J3302_tension_lifecycle.py` (re-runnable, read-only on the live stores, output in `docs/lab/J-3302_data/`) or from a named code line. Confidence tags: **[verified]** (I read the file or ran the query), **[inferred]**, **[guess]**. Sources: `data/nascence.log` (T4 lines 2026-06-04 to 2026-11-05 16:24; the log stops there), `data/logs/provisional_identity.jsonl`, `data/logs/t4_emissary_judge.jsonl`, `data/subconscious_state.json`, `data/contradiction_ledger_log.jsonl`, `data/tensions_archive.jsonl`, `shadow_events` (sqlite `mode=ro&immutable=1`, WAL empty).

## 0. The answer in eight lines

1. **A solidify ends nothing.** After the 10-30 13:58:29 solidify on `prediction_error:factual_recall` the same question was heard again **22.8 seconds later** (a new chain on the same label), and 28 times in all by 11-05 (13 chains authored, 15 no-change). It did not "return 11-04": it never left. The only quiet stretch was the 3-day rest that began 10-31 15:23. [verified]
2. **What does end a tension today, from the log:** a 3-day rest after three identical no-movement hearings (27 rests, 16 label families); the tension cooling out of the 300-event scan window and being demoted (`long_cold` 1573 rows, `settled` 413 rows in `tensions_archive.jsonl`); a code or ruling change (the keystone toll, 08-20); and, once, a judge-confirmed `settled` demotion (the 渡 tension, 10-10). Never a commit. [verified for the counts, inferred for the per-family causes in section 2]
3. **The tension has no stable identity in the code.** Rest and fatigue are keyed on label text; the label is the newest member's correction text and rotates (felt numbers, then the whole domain). The one live prediction_error cluster (id `07b3d01b`, born 09-29) has been heard under three names: comprehension, fieldcraft, factual_recall. [verified]
4. **The rest matcher holds for a felt-only change and fails when both numbers change.** Token Jaccard 0.667 across the three `(felt, real)` pairs of the 97 factual_recall events; 0.43 for comprehension `(0.00, 0.50)` against `(0.10, 0.85)`, which reconstructed two rest leaks (09-16 to 09-17, 10-07 to 10-09). The fatigue counter is an exact-string key, so it splits per felt number (live state: two keys, counts 2 and 1). [verified for the arithmetic and the live state; the two leaks are **inferred**, the label at the hearing is reconstructed]
5. **Discharge-on-solidify would not have ended this tension.** The 10-30 commit would have retired **4** member events (the 300-event window then spanned 8.1 hours and held 4 prediction_error events, all factual_recall). But `get_event_sources` remaps only `critic_rejection` to "resolved": a retired prediction_error event still counts, so the count stays 4 and pressure goes 4.0 to 1.6 only through the drain credit. 0 of 725 prediction_error events have ever been resolved, and the feeder adds about 14 factual_recall events a day. [verified]
6. **The revert fatigue penalty is inert.** `_apply_fatigue` writes a differently shaped key (`error_factual_felt_prediction_recall`) into the state file that nothing reads, and `DEFAULT_FATIGUE_PENALTY` is not defined in `tension_ledger`. Three reverts since 10-30 on this cluster (11-03, 11-04, 11-05) rested it zero times; T4 authored a new chain 15 seconds after the 11-04 14:51:13 revert of the factual_recall probation. [verified by code and log]
7. **Proposed rule R1:** a SOLIDIFY files one entry in the existing `t4_rests` list for the tension it answered, matched by cluster id as well as label tokens. No new actor, no write to `shadow_events`, flag default off. Details and the order against J-3161, J-3162 and J-3021 in section 4.
8. **One founder question, D-0691:** build R1 now as a stop-gap, or leave the tension loop alone until the Watershed redesign (D-0664 option 3) replaces it. My recommendation is not to build it now: the repeat hearings cost about 5 minutes of hot-lane time a day and the redesign may remove the docket. The bug repairs (tension-id keys, the inert revert penalty) are real either way and belong inside J-3021.

## 1. The table: hearings by tension label family, 2026-06-04 to 2026-11-05

A family is the label with the `(felt .. vs real ..)` suffix stripped and cut to 36 characters (the log cuts CHAIN labels at 40 and `considered` labels at 60). "Judged" is a `t4_emissary_judge.jsonl` row within 900 s after that family's CHAIN line; "admitted" is `emissary_warranted >= 0.6`. Probation columns come from `provisional_identity.jsonl` by full theme text. 707 labelled hearings in 48 families; the 14 with 10 or more are below; the full table is `docs/lab/J-3302_data/family_table.json`.

| Family | Hearings | Chains | Judged | Admitted | Probations (solidified / reverted) | Rests | First to last (days) | How it stopped being heard |
|---|---|---|---|---|---|---|---|---|
| prediction_error:comprehension | 131 | 100 | 100 | 4 | 5 (0 / 5) | 5 | 09-02 to 10-09 (37) | label rotated to fieldcraft; same live cluster [inferred] |
| prediction_error:music | 82 | 64 | 64 | 4 | 7 (0 / 7) | 3 | 08-21 to 09-25 (36) | last event a rest (09-25); new cluster born 09-29 [inferred link] |
| "You are a made mind" (keystone, old text) | 60 | 41 | 39 | 37 | 0 | 2 | 06-17 to 06-22 (5) | keystone injection ignores rests (29 and 40 hearings inside two rest windows); text replaced 06-22 [verified] |
| hold the tension with both consistency and growth | 58 | 53 | 0 | 0 | 0 | 1 | 06-13 to 06-17 (4) | rest 06-17; cluster demoted `long_cold` 08-14 [verified] |
| unresolved: Maxwell's French rejection | 47 | 29 | 29 | 0 | 0 | 1 | 08-23 to 09-06 (15) | rest 09-06; demoted `long_cold` 09-25 [verified] |
| the draft commits LITERALIST REDUCTIONISM | 47 | 34 | 34 | 3 | 6 (0 / 6) | 1 | 08-25 to 09-04 (10) | rest 09-04; demoted `long_cold` 09-25 [verified] |
| "The mind you think with was built" (keystone) | 42 | 36 | 36 | 26 | 0 | 1 | 06-22 to 08-22 (61) | keystone injection ignores rests; toll flag off 08-20 [verified] |
| unresolved: mind and becoming | 34 | 34 | 34 | 2 | 2 (0 / 2) | 0 | 09-16 to 09-28 (12) | no rest, no archive row: cause not established |
| unresolved: the term '渡' | 34 | 27 | 26 | 0 | 1 (0 / 1) | 1 | 10-07 to 10-10 (3) | rest 10-10 14:49, then `settled` archive 10-10 15:43 [verified] |
| **prediction_error:factual_recall** | **33** | 15 | 15 | 4 | 4 (**1** / 2, 1 open) | 1 | 10-29 to 11-05 (7) | **still live**; one rest 10-31 to 11-03 |
| unresolved: the Bluebird's arrival | 27 | 21 | 21 | 0 | 0 | 1 | 10-31 to 11-02 (1.3) | rest 11-02 00:01; now count 3, chronic mass 0.0 |
| prediction_error:fieldcraft | 17 | 2 | 2 | 1 | 1 (0 / 1) | 5 | 10-09 to 11-03 (25) | five rests; label rotated to factual_recall [inferred] |
| respond as yourself, present and direct | 12 | 12 | 0 | 0 | 0 | 0 | 06-10 to 06-12 (2.5) | cause not established |
| unresolved dream: I still wonder how the French | 12 | 9 | 9 | 0 | 1 (0 / 1) | 0 | 08-24 to 08-25 (1.6) | demoted `long_cold` 09-25 [verified]; why it stopped being heard on 08-25: not established |

Totals over all 48 families: 521 chains authored, 186 no-change hearings, 27 rests, 63 probations opened in the log (62 resolved), **5 solidified**. 249 of the 683 judged rows have no chain line before them (the legacy author, which cannot be admitted).

**One cluster, three names.** Since the live cluster `07b3d01b` was born (09-29 09:43) there have been 72 prediction_error hearings: factual_recall 33, comprehension 22, fieldcraft 17; 29 chains, 43 no-change (24 still circling, 13 not yet crossed, 6 no specific delta), 6 probations (1 solidify, 5 reverts), 9 rests. The cluster's `resolution_attempts` list names the same rotation (fieldcraft 16, factual_recall 10, comprehension 7). The longest gaps in its hearings are all explained by a probation window (12 to 72 h of `is_active()` early return) or a rest, except 10-19 to 10-29 (258 h, no T4 line at all, cause not established: possibly Du offline). [verified for the counts, inferred that the three label names are one tension; the log carries no cluster id]

**Does a tension ever stop being heard other than by a rest?** Of the 14 big families: 6 ended at a rest (music, consistency-and-growth, Maxwell, literalist, 渡, Bluebird; three of them were later demoted `long_cold` and one `settled`), 2 ended by a label rotation of the same cluster (comprehension, fieldcraft), 2 by a code or ruling change (the two keystone families, which ignore rests), 3 have no established cause, 1 is live. **None ended by a commit.**

## 2. Question 1: is the label key stable when the felt number changes?

- **The rest matcher** (`_t4_distinct_tensions`, the Jaccard above 0.5 on words of 4 or more characters) keeps matching when only the felt number changes: `(felt 0.95 vs real 0.50)` against `(felt 0.92 ...)` gives 4/6 = 0.667. All 97 factual_recall events in `shadow_events` carry one of three pairs (0.95, 0.92, 0.90 against real 0.50), so every pairwise Jaccard is 0.667 and the 10-31 rest could not have leaked on the number. [verified; test case 1a]
- **It fails when both numbers move**: 3/7 = 0.429. The comprehension tension carried `(0.00, 0.50)`, then `(0.10, 0.85)`, then `(0.90, 0.40)`. The rest of 09-16 17:13 was heard again at 09-17 11:28 and the rest of 10-07 18:57 at 10-09 10:43; the newest comprehension event before each hearing carried the new pair (Jaccard 0.429). [verified arithmetic; the reconstruction of the hearing's label is **inferred**, because the log cuts a CHAIN label at 40 characters]
- **The fatigue counter is exact-match**: `_t4_label_key` sorts the tokens, so each felt number is a different key. Live state at the last save (11-05 19:07): `{'(felt 0.50) 0.95 prediction_error:factual_recall real': 2, '(felt 0.50) 0.92 prediction_error:factual_recall real': 1}`. A movement verdict pops only the key of that hearing's number, so counts under the other numbers go stale and can later tip a rest on a hearing that has nothing to do with the earlier two. In the history this changed no rest I can show (the number-stripped replay gives the same 27 rests as the log), so it is a latent split, not a measured loss. [verified]
- **The ranking and the sharpened label disagree on what the tension is.** `top_contradiction` ranks by pressure and `_t4_distinct_tensions` by chronic mass; at lines 2388 to 2393 `out[0]["_label"]` and `member_event_ids` are overwritten with the pressure-top's, while `out[0]["id"]` stays the chronic-top's (`top_contradiction` returns no id). Any key built on `id` must set the id at the same place. [verified in code; how often the two differ is not measured]
- **A correction to F-3881:** it says the question "returned 11-04". From the log it never left: ten hearings from 23 s after the commit up to the 10-31 15:23 rest (5 chains, 5 no-change), then the 3-day rest, and the 11-03 23:27 hearing is the first after the rest expired. The factual claim of F-3881 (solidify does not discharge) stands and is sharper than stated.

## 3. Question 2: what would discharge-on-solidify do?

`_discharge_contradiction` (`subconscious_node.py` 2707) takes one tension, calls `log_resolution_event(eid, cyc, sim)` and `mark_shadow_resolved(eid)` for every `member_event_ids` entry, with `sim` clamped to 0.15 to 0.60. It is called at line 2330 only inside the dormant legacy cost-gate path; the last `T4 DISCHARGE` log line is 2026-06-13 (28 in total). `_solidify` (`provisional_identity.py` 427) never calls it, and its own docstring says so.

For the 10-30 commit (hermetic, through the real `tension_ledger.score_tension`):

| Quantity | Value |
|---|---|
| Scan window at the commit | newest 300 shadow events = **8.14 hours**; 295 unresolved_thought, 4 prediction_error, 1 unresolved_dream |
| Member events that discharge would retire | **4** (the 4 prediction_error events, all factual_recall) |
| factual_recall prediction_error events up to the commit / now | 20 / 97 (0 of the 725 prediction_error events ever resolved) |
| Contradiction pressure before | 4.0 |
| After, with the code as it is | **1.6**, count still 4 (`get_event_sources` remaps resolved to `critic_rejection_resolved` only; prediction_error stays a contradiction source) |
| After, if the remap also covered prediction_error | 0.0 |
| Feeder rate | about 14 new factual_recall events a day, so a fresh unretired member arrives about every 1.7 hours |

Why it cannot end this tension even with the remap fixed: membership is the newest-300 window (`get_shadow_events(limit=300)`, not `unresolved_only`), so the 4 retired events scroll out within hours anyway, and the ranking uses chronic mass, which bumps on member-set growth and not on resolved flags. The `contradiction_ledger_log` shows the effect directly: pressure 9.0 at 10-30 01:54, 5.0 at the commit, 15.0 by 11-02 13:18. [verified]

**Risk to the base system if it were built anyway** (`resolved=1` is read elsewhere): `climate_engine` shadow_activation reads `unresolved_only` (200 newest), the re-encounter circuit's `get_active_shadow_embeddings` reads `resolved = 0` (a retired event can no longer earn a clean re-encounter credit), and `session_digest` counts them. Today 561 of about 47,500 shadow events are resolved (1.2 percent); 4 more per solidify would be small on those readers, but the plan's own line ("integration retires the past it worked through, never immunises the future") is satisfied only for the critic_rejection source, which is 241 of the events and was last discharged in June. The discharge arrow is the wrong tool for a source that regenerates faster than T4 runs. A rest is the right tool, and it already exists.

## 4. Question 3: one lifecycle rule, R1

**R1 (solidify rests the question it answered).** When the probation tick resolves to `solidify`, T4 appends one entry to its own `self._state["t4_rests"]` for the tension the probation was about: `{label: theme[:160], toks: <label tokens>, ids: [tension cluster id], until: now + T4_REST_S}`. `_t4_distinct_tensions` skips a tension when its id is in a resting entry's `ids` or its label tokens match as today, and the sharpened-label guard checks both. Nothing else changes.

- **Consumer:** `_t4_distinct_tensions` (the existing rest skip and the existing "rested question must not ride back in" guard). No new reader, no new log: the rest emits the existing `T4 question RESTED` line with a `solidify` suffix, which this analysis script already parses (the regex needs the suffix added when R1 ships).
- **Why this one and not discharge:** it ends the 23-second re-hearing and the 10 hearings (5 chains, 5 no-change) in the next 25 hours that the 10-30 commit produced, with no write to `shadow_events` and no change to Climate or the re-encounter circuit. It cannot immunise the future: it ends by time (`T4_REST_S`, 3 days, the existing design) and a new event is never retired.
- **Needs two small additive pieces, or it leaks like the comprehension rest:** (a) the probation record carries `tension_id` (additive field on `open_probation`, default None); (b) `top_contradiction` returns the tension `id` and line 2392 sets `out[0]["id"]` with the label, so the id and the label come from the same tension. Written through the node's own `_save_state`, not the `_apply_fatigue` pattern of editing the state file from another module.
- **Decoupled check:** the trigger is already decoupled (a solidify is the two-family judged verdict; R1 acts on no self-graded signal). The effect check is a read of the log: hearings of the answered tension in the 72 hours after each solidify, baseline 28 in 6 days after 10-30; a different-family judge is not needed because R1 changes no content.
- **Cost:** about 20 lines in `nodes/subconscious_node.py` and `core/provisional_identity.py` (hub files: run the change dossier first), no model calls, flag `T4_SOLIDIFY_RESTS_QUESTION` default False, restart-gated.
- **Stop condition:** turn the flag off if (a) the legacy author's share of judged rows rises above today's 249/683 (36 percent) in the two weeks after (the empty-docket cascade), or (b) the next two solidifies are still re-heard within 72 hours (the id match is not binding). A founder read at the next solidify; not an automatic switch.
- **Honest limit:** n=1. The 10-30 commit is the only solidify in the labelled era that has a chain trace; the four earlier ones are June or earlier.

**Build order against the sibling jobs** (so they are not built in conflicting order):

1. **J-3162 first (legacy gradeable).** R1 and J-3021 both rest more tensions, and a rest that empties the docket sends T4 to the legacy author (249 of 683 judged rows, all unadmittable). J-3162 also asked whether `top_contradiction` re-introduces the rested question in the legacy path: **yes by code reading** (`top_contra = _tl.top_contradiction(_tensions)` at line 1919 has no rest filter and the legacy author is handed it), verified, not replayed.
2. **R1 second**, flag off, with the id plumbing. It defines the one tension key (cluster id) the rest uses.
3. **J-3161 (cadence) third**: its replay of "what each gap would have done" should include R1's rest, otherwise it overstates hearings after a solidify.
4. **J-3021 last (count unwarranted toward fatigue)**, and amended: it must key its counter by the same tension id, not by `_t4_label_key` (the exact-match key splits per felt number), and it must repair the inert revert penalty (`_apply_fatigue`) or retire it; fixing the penalty alone would have rested the factual_recall tension at the 11-04 14:51 revert (penalty 3 against a limit of 3), which is the empty-docket cascade again, hence J-3162 first.

All four edit `nodes/subconscious_node.py`, which is a hub file and which Run G is editing in parallel; none can ship from this chain, and D-0664 (option 3, the full Watershed redesign) holds the T4 chain jobs. Under option 3 the chain is kept only for the rare replacing case, so R1 may turn out to be a stop-gap for a loop that is being replaced; that is the founder question.

## 5. What I did not verify

- The per-family "how it stopped" column is from rest/archive/code evidence next to the last hearing, not from a causal trace; two rows say so.
- The reconstruction of the label at a CHAIN hearing (comprehension leaks) uses the newest same-domain prediction_error event before the hearing.
- The member set of the 10-30 cluster is the newest-300 window filtered to prediction_error events; the exact connected-components clustering (`CLUSTER_SIM_THRESHOLD` 0.55 on embeddings) was not re-run. The 4-event figure is an upper bound on the cluster's prediction_error members at that moment and equals the count of all prediction_error events in the window.
- Whether other contradiction sources (critic_rejection, 241 events) behave differently after a solidify: no solidify has occurred on one since June.
- The 10-19 to 10-29 silence (no T4 line at all) was not explained.
- The `nascence.log` stops at 11-05 16:24 (`subconscious_state.json` 19:07); nothing after that was read.

## 6. Index

- Script: `scripts/analysis_J3302_tension_lifecycle.py`; test `scripts/_test_J-3302_tension_lifecycle.py` (synthetic world in a temp dir). Outputs `docs/lab/J-3302_data/{family_table,summary,rest_replay}.json`.
- Findings F-4249 to F-4253 and F-4256 (the prediction_error source is near-degenerate: 538 of 725 events are mathematics with real 0.00, all 97 factual_recall events have real 0.50); decision D-0691 (plan `t4_watershed`); follow-up jobs J-3640 (tension-id keys and the inert revert penalty, amends J-3021), J-3641 (series test for prediction_error movement; its briefing cites the finding as F-4254, the correct id is F-4256), J-3643 (R1 build, only if D-0691 says build), J-3644 (id/label pairing and the 258-hour gap).
