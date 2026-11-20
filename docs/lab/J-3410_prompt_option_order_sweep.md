# J-3410: option-placeholder / pre-filled-example position-bias sweep of Du's prompts (from F-4044)

Status: analysis only. No prompt edited, no Du code changed, nothing live. Written 2026-11-07 in worktree `wt_wh9`.
Scripts: `scripts/lab_j3410_site_census.py` (which prompts ship the hazard), `scripts/lab_j3410_judge_skew.py`
(live per-judge verdict skew, read-only), `scripts/lab_j3410_order_replay.py` (the order-control replay itself, runnable and
resumable), `scripts/_test_J3410_order_replay.py` (its test). Data: `docs/lab/J-3410_data/`.

## 1. The answer in five lines

1. The hazard is wider than F-4044's one prompt. The shipped answer schemas fall into five forms (section 3). The big one is
   the two-option boolean placeholder: **every judge-panel prompt that lists its options lists `true` first, never `false`
   first**, and the panel feeds the *same* system text to both families. So a prompt-form artifact is common-mode across the
   two "decoupled" judges: family decoupling does not decouple the prompt.
2. **Option order has never been controlled for any of them.** The only reversal anywhere in the tree is F-4044's own
   Brev/Crev arms in `scripts/lab_guidance_classify.py` (command-r7b, a 3-way enum). The other position-bias work in the
   repo (J-3150, J-3253, J-2052, the si_open_doubt labs) is about A/B pair presentation, not about listed answer options.
   Prior framing labs (pursuits `advances`, tension `resolves`, 2026-08-23) varied the whole framing, not the order.
3. Live verdicts DO show strong per-key skew, and two judges given the identical prompt often sit at opposite ends
   (`cuts`: mixtral 14 percent true, falcon3 88; `resolves` 15 vs 55; `bears` 5 vs 27; `refs` 98 vs 55). That proves at least
   one judge is not reading the case on those keys. It does NOT prove position bias: skew and position bias are different
   claims, and only a reversal replay separates them.
4. There are also direct counter-examples that a first-listed or pre-filled option does not simply win: dream `resolved`
   ships `{"resolved": true, ...}` pre-filled yet is true on 1.5 percent of 359 mixtral calls (its prompt says "refute-biased,
   when unsure answer false"); the decomposed critic ships `violation: false` pre-filled yet flags 32 percent; the condensed
   twin's `kind` ships "fragment" first and gets fragment 41 / tick 38 / silent 21 percent.
5. Stations that need an order-control replay are listed in section 6, ranked. A pilot replay on falcon3 (the real
   JUDGE_2) and gemma4 (the tiebreak) is in section 5: on three stations reversing the order flipped 0-2 verdicts in 27-132 pairs
   (first_listed_sum 0.99-1.07, pure position effect would be 2.0). No order effect there; a strong model lean that does not
   depend on order was found instead (falcon3 `held` 30/30 true, `metaphor` 87/88 false).

## 2. What F-4044 actually showed (and the limit on reading it)

F-4044 (J-3232, command-r7b, temp 0.2): placeholder `<assimilate|accommodate|unrelated>` answered *accommodate* (listed
second) on 86 percent of not-same pairs; the reversed list `<unrelated|accommodate|assimilate>` flipped it to *assimilate*
(listed LAST) at 41 percent on not-same and 100 percent on true same-lesson pairs. So the lean is not "the second option": it
moved to a different position when the order changed. What is established is only that the answer depends on the listed
order on that model; the direction of the dependence is not a fixed first/second rule. That is why the sweep below does not
predict a direction per station, it asks for a reversal.

## 3. The five forms, and how many prompt fragments ship each

`scripts/lab_j3410_site_census.py` walks `core/`, `nodes/`, `scripts/run_nascence.py` with `ast` (BOM-safe: `core/lane2.py`
starts with a BOM and an earlier naive scan silently skipped it) and finds 137 answer-schema fragments; after removing log-row
docstrings and non-LLM schemas (cat/life/nest ledgers, flag dicts) the prompt-bearing ones are:

| form | example (shipped text) | where |
|---|---|---|
| bool_pipe | `{"held": true\|false, "why": ...}` | pursuits advances, tension resolves, lane2 held/contradicted/metaphor/coherent/contradicts, guidance_behavior aligns, pursuit_close resolved, social_cognition (4 keys, one `%s` template), peers honoured, subconscious genuine/seeded/has_movement/changed |
| bool_or | `{"genuine": true or false}`, `<true or false>` | self_interrogation genuine, same_lesson, refinery supported, symbol_window specific, ground_grade (2 keys), curiosity prefire (2 keys), episodic_buffer scene_invented, commitment legitimate / load_bearing, condensed twin open |
| bool_pair | `{"cuts": true} or {"cuts": false}` | follow_line supported/cuts/follows, evidence_recall bears (true first in all four) |
| enum_pipe / enum_or | `"class": "achieved\|impossible\|superseded\|conflict\|illegitimate"`, `"verdict": "stand" or "insight" or "unclear"` | executive response_type (6), perception (4 fields, 4-5 options each), commitment class (5) and second-look verdict (3) and kind (2), narrative_quality transformation (4), follow_line supports yes\|partly\|no, memory_router time_bias, voice_fidelity kind, lane2 horizon (generator) |
| prefilled (one option named as the example answer) | `{"approved": true, ...}`, `{"relation": "assimilate"}` | critic approved/identity_consistent, reflection (2 booleans), salience interrupt, executive should_respond, decomposed_critic violation false, left_lane integrated/genuine true and classification "additive", dream resolved true, subconscious connects/changed/unresolved true, guidance_learning relation "assimilate" |

| prose-listed options | "The only allowed answers for each belief are three words: fluid, durable, or neither" (`_SELF_CLASH_SYS`, P-0019); "classification is 'additive' or 'replacing'" (P-0094) | found by reading, NOT by the census (it only sees JSON-shaped fragments); there are certainly more |

Adjacent but out of scope here: numeric pre-fills (`"confidence": 0.0`, `"grounded": 0.0` in the left-lane graders and
`curiosity_worth`), which anchor in the same way and need their own sweep. Spawned as J-3721.

## 4. Live evidence: skew per station (read-only, `data/judge_panel_log.jsonl`, rows since 2026-09-03, n=33,696)

JUDGE_1 = mixtral:8x7b :11438, JUDGE_2 = falcon3:7b :11440; both receive the identical system text. "true" is the first-listed
option in every row below. Source: `docs/lab/J-3410_data/judge_skew_since_0903.json` (regenerate with
`python scripts/lab_j3410_judge_skew.py --since 1788348000`).

| key @ caller (registry row) | n | mixtral true | falcon3 true | v1/v2 agree | panel verdict true | form |
|---|---|---|---|---|---|---|
| genuine @ active_imagination_novelty (P-0104, WRITE-ONLY) | 2764 | 1.000 | 0.998 | 0.998 | 1.000 | bool_pipe |
| genuine @ self_interrogation (P-0105, LIVE) | 893 | 0.995 | 0.994 | 0.991 | 0.999 | bool_or |
| coherent @ lane2 (P-0111, WRITE-ONLY) | 6278 | 0.956 | 0.676 | 0.717 | 0.783 | bool_pipe |
| advances @ pursuit (P-0100, LIVE) | 5460 | 0.830 | 0.864 | 0.831 | 0.837 | bool_pipe |
| follows @ follow_line (P-0102) | 473 | 0.886 | 0.941 | 0.899 | 0.962 | bool_pair |
| cuts @ follow_line (P-0102) | 315 | 0.143 | 0.876 | **0.254** | 0.743 | bool_pair |
| supported @ follow_line (P-0102) | 314 | 0.589 | 0.748 | 0.771 | 0.758 | bool_pair |
| bears @ evidence (P-0099, LIVE) | 4098 | 0.054 | 0.267 | 0.764 | 0.265 | bool_pair |
| resolves @ tension (P-0103, LIVE) | 1426 | 0.146 | 0.549 | **0.572** | 0.136 | bool_pipe |
| held @ lane2 (P-0109) | 4531 | 0.336 | 0.529 | 0.665 | 0.434 | bool_pipe |
| contradicted @ lane2 (P-0109, 2nd ask) | 548 | 0.032 | 0.243 | 0.775 | 0.061 | bool_pipe |
| aligns @ guidance_behavior (P-0106, SHADOW) | 329 | 0.078 | 0.252 | 0.777 | 0.168 | bool_pipe |
| tracks / refs / attributes / attrib_supported @ social_cognition (P-0108, SHADOW) | 69/49/69/63 | .59 / .98 / .97 / .25 | .86 / .55 / .91 / .68 | .63 / .59 / .87 / .54 | .91 / .61 / 1.0 / .69 | bool_pipe |
| metaphor @ lane2 (P-0110) | 4307 | 0.025 | 0.001 | 0.975 | 0.012 | bool_pipe |
| contradicts @ lane2 (P-0112, retired by D-0599) | 701 | 0.011 | 0.006 | 0.986 | 0.002 | bool_pipe |
| resolved @ dream (P-0107) | 359 | 0.015 | 0.031 | 0.971 | 0.009 | PRE-FILLED true |
| resolved @ pursuit_close (P-0101, SHADOW) | 90 | 0.000 | 0.044 | 0.955 | 0.000 | bool_pipe |

The granite tiebreak (core/judge_panel.py:104-118, measured 2026-11-06, shared hub only) is constant on `resolves` 0.000,
`held` 0.002, `bears` 0.953, `genuine` 0.993, `taken_up` 0.982 (D-0530 already turned the tiebreak off for these five); that
is the same family of symptom, found there by a different route.

Reading, with confidence stated:
* **Verified** (numbers computed from the log, script above): the figures in the table; falcon3 answers `true` more often than
  mixtral on 13 of these 20 keys (mean +0.107 over them), mixtral more on 7.
* **Inferred**: that falcon3 is the more first-option-leaning judge. Equally consistent with mixtral being stricter. A pair of
  models that differ by 0.73 on `cuts` cannot both be right, but nothing here says which one is wrong or why.
* **Inferred**: `genuine` (both judges 99.4-100 percent true on two different callers, both listing `true` first, granite 99.3
  percent on the same key) is the strongest candidate for a first-option effect because it is constant in every family. It is
  also the key a self-interrogation gate rests on. Constant-true is exactly what a position effect OR an easy question OR a
  never-fails judge would all produce, so the reversal is the only way to tell them apart.
* **Structural** (follows from the code, not a measurement): both judges get one shared system string, so a first-option
  effect would be common-mode and would show up as AGREEMENT, not disagreement. The high-agreement near-constant rows
  (genuine, metaphor, contradicts, resolved) are therefore the ones where the panel's agreement statistic is least informative.

### Non-panel stations (single model; live distribution of the categorical output)

| row | lane / model (registry) | form | live distribution | read |
|---|---|---|---|---|
| P-0008 critic (legacy) | hot qwen3.5:9b | pre-filled `approved: true` + "WHEN IN DOUBT, APPROVE" | `data/logs/critic_shadow_alongside.jsonl` n=495: legacy approves 98.8 percent; the decomposed critic approves 68.1 percent on the same drafts | two confounds (pre-fill AND an explicit approve-when-unsure instruction); the decomposed critic is the natural control |
| P-0009 executive | hot qwen3.5:9b | 6-way enum, `answer` first, `should_respond: true` pre-filled | `internal_cycle_context_shadow.jsonl` n=256 (internal cycles only): answer 236, challenge 19, decline 1; question/reflection/silence 0 | first-listed is 92 percent; human-turn distribution not found in a log |
| P-0052 self-relate | background command-r7b | pre-filled `connects: true` | `self_relate_shadow.jsonl` n=2142: connects true 90.6 percent; the placeholder text "one first-person sentence" was echoed back verbatim 5 times | candidate; the question may simply usually be yes |
| P-0018 classify | background command-r7b | pre-filled `assimilate` | `guidance_classify_log.jsonl` (61 rows, 29 without a relation field): of the 32 with one, assimilate 13, unrelated 11, accommodate 8 | live is NOT dominated by the pre-filled option; F-4044's A arm already measured the same prompt |
| P-0048 narrative_quality | background command-r7b (WRITE-ONLY) | 4-way, `redemption` first | `narrative_quality_log.jsonl` llm n=1553: redemption 52 percent, uniform 40, flat 5, contamination 3 | first-listed is modal; WRITE-ONLY so low stakes |
| P-0039 condensed twin | hot (shadow) | `kind: fragment or tick or silent` | `condensed_thought_shadow.jsonl` n=2725: fragment 1112, tick 1048, silent 564 | no dominance: weak evidence AGAINST a strong first-option effect here |
| P-0017 decomposed critic | hot | pre-filled `violation: false` per check | flags on 32 percent of drafts | pre-filled-false does not suppress flags |
| P-0121 refinery faithfulness | mixtral (shadow) | `supported: true or false` | `refinery_shadow.jsonl` n=805: accepted 70 percent | no dominance |

## 5. Pilot: option-order control replay on the real JUDGE_2 (falcon3:7b, local :11440)

Design (`scripts/lab_j3410_order_replay.py`): the production function builds the real prompt (its `judge_panel.rule_detail`
is stubbed to capture `(system, user, key)`, so no prompt text is retyped); the same call is asked twice on a local hub, once
as shipped and once with ONLY the listed order reversed (`true|false` becomes `false|true`); temperature 0, JSON mode,
`num_predict` 200, the same payload as `judge_panel._ask`. Statistics per station: true-rate under each order, flip counts,
exact McNemar p on the discordant pairs, and `first_listed_sum` = P(first-listed chosen | shipped) + P(first-listed chosen |
reversed): a pure position effect gives 2.0, no effect gives 1.0. Labelled fixtures give accuracy by order as well.

Pilot stations (labelled fixtures already in the repo): P-0117 same_lesson (J-3232 pairs, hand labels), P-0109 held
(J-3210 hand labels), P-0110 metaphor (J-3205 passages, Claude pre-labels, not founder labels).

Throughput caveat: the local CPU hubs are shared with the other running chains. Early in the job falcon3 took 47-105 s per
call (queued behind sibling traffic; see the hub's own `data/logs/cpu_tier_11440.log`); the script is resumable and both hubs
were finished across the job, so the tables below are complete for the three pilot stations. The R1 stations that need
fixtures (section 6) are the part not run; they are spawned as a lab job.

### 5.1 Results (temperature 0, 500 calls per hub, both arms complete)

Files: `docs/lab/J-3410_data/order_replay_{falcon3,gemma4}.jsonl` (every call) and `..._report.json` (statistics). Hubs: falcon3:7b
:11440 (the real JUDGE_2) and gemma4:12b :11439 (the real tiebreak for held/metaphor; a different family from both). Labels: P-0117
J-3232 hand labels (n=66 same / 66 not-same), P-0109 J-3210 hand labels (23 held / 7 not), P-0110 Claude pre-labels (12 metaphor /
76 not; NOT founder labels). gemma4 had 22 call timeouts (`http:TimeoutError`), so its n_pairs is 127 / 27 / 82 (5, 3, 6 pairs
dropped as invalid); falcon3 had none.

| station @ hub | pairs | true-rate shipped / reversed | verdicts flipped by reversal | McNemar p | first_listed_sum | accuracy shipped / reversed |
|---|---|---|---|---|---|---|
| P-0117 same_lesson @ falcon3 | 132 | 0.447 / 0.447 | 0 of 132 | 1.0 | 1.000 | 0.917 / 0.917 |
| P-0117 same_lesson @ gemma4 | 127 | 0.465 / 0.465 | 0 of 127 | 1.0 | 1.000 | 0.953 / 0.953 |
| P-0110 metaphor @ falcon3 | 88 | 0.011 / 0.023 | 1 of 88 | 1.0 | 0.989 | 0.847 / 0.861 |
| P-0110 metaphor @ gemma4 | 82 | 0.354 / 0.366 | 1 of 82 | 1.0 | 0.988 | 0.912 / 0.897 |
| P-0109 held @ falcon3 | 30 | 1.000 / 0.933 | 2 of 30 | 0.5 | 1.067 | 0.767 / 0.767 |
| P-0109 held @ gemma4 | 27 | 0.852 / 0.815 | 1 of 27 | 1.0 | 1.037 | 0.889 / 0.852 |

Reading (verified = computed from the jsonl by `lab_j3410_order_replay.py report`; inferred = my reading of it):
* **Verified**: on these three stations, at temperature 0, on these two local models, reversing the listed answer order moves
  the verdict on 0-2 pairs in 27-132. first_listed_sum is 0.99-1.07 against a pure-position-effect value of 2.0 and a
  no-effect value of 1.0. So there is NO position effect on same_lesson, metaphor or held on falcon3 or gemma4.
* **Verified**: the F-4044 result does not transfer by default. F-4044 was command-r7b on a 3-way enum with an unfilled
  placeholder. These are 2-way booleans on other models. The sweep did not retest command-r7b (Ramses/retired).
* **Verified, and it matters more than the order result**: the lean is real and order-independent. falcon3 on `held` says true
  on 30 of 30 shipped-order pairs (7 of those are hand-labelled not-held: recall on not-held 0.00 shipped, 0.14 reversed) and
  on `metaphor` says false on 87 of 88 (recall on the 12 metaphors 0.08). The same constant answer appears under both
  orders, so it is a model lean on that question, not a listed-position artifact. gemma4 on the same metaphor prompt says true
  on 35 percent. Two judges from different families on the identical prompt disagree by 34 points with no order involved.
* **Inferred**: this is why live skew cannot be read as position bias (section 4): the highest-skew rows in the live table are
  most likely lean-of-the-model-on-the-question like these two, not first-option effects. Where the replay can be run, it says
  the first-option story is not what is happening. That argues for dropping `genuine`, `cuts`, `bears`, `resolves` from
  "assume position bias" to "needs the reversal before anyone acts", which is how section 6 already ranks them.
* **Inferred, small n**: `held` n=30 (23 positive) and `metaphor` positives n=12 are too few to exclude a small order
  effect; the pair counts can only exclude a large one (a flip rate near 0.5). P-0117 at 127-132 pairs per hub is the solid one.
* Cost: a labelled station on a local hub took about 9.5-10.5 s per call at median once the sibling chains were quiet (the
  47-105 s per call seen early in the job was queue contention on the shared CPU hubs).


## 6. Which stations need an order-control replay

Ranking rule: (live gate or live-provisional) x (strong live skew OR two judges far apart on the identical prompt) x (no
instruction in the prompt that already forces a direction).

**Replay first (R1)**
1. **P-0105 self_interrogation `genuine`** (`true or false`, 99.5 percent true in both families, LIVE). Reverse to `false or true`.
2. **P-0102 follow_line `cuts` / `supported` / `follows`** (literal pair, true first; `cuts` 14 vs 88 percent). Reverse the pair.
3. **P-0099 evidence_recall `bears`** and **P-0103 tension `resolves`** (LIVE; 5 vs 27 and 15 vs 55 percent; granite constant on both).
4. **P-0100 pursuits `advances`** (LIVE, 83-86 percent true; the 2026-08-23 framing lab already showed this prompt moves with
   framing, so order is the next obvious axis).
5. **P-0008 critic** pre-filled `approved: true` (98.8 percent approve, hot qwen3.5) and **P-0009 executive** `response_type`
   (`answer` first, 92 percent of internal cycles): reverse the enum order and the pre-fill; needs the hot lane (see finding on
   :11433), so run it when that hub answers.
6. **P-0117 same_lesson** (the D-0622 gate, unfilled `<true or false>`, no live rows yet because it is restart-gated): in the pilot.

**Replay second (R2)**
P-0109 held/contradicted (tiebreak is gemma4, not granite), P-0111 coherent (WRITE-ONLY but 96 percent mixtral true),
P-0106 aligns, P-0108 social cognition (SHADOW; keys `refs`, `attrib_supported` are 40-43 points apart), P-0037/P-0116
commitment judges (5-way `class` and 3-way `verdict`, both on mixtral; the Ramses hub is off-limits to this job),
P-0092/P-0094/P-0095 left-lane graders (pre-filled `integrated: true` / `genuine: true` / `additive`; no live skew log found),
P-0052 (pre-filled `connects: true`, 90.6 percent), P-0044 follow_line generators (`supports` yes|partly|no),
P-0001 perception enums, P-0118 curiosity prefire, P-0122 episodic buffer judge.

**No replay needed now (N)**
Constant-and-instruction-driven or balanced: P-0107 dream `resolved` (pre-filled `true`, 1.5 percent true: the instruction wins),
P-0101 pursuit-close, P-0110 metaphor, P-0112 contradicts (retired), P-0039 condensed kind, P-0017 decomposed critic, P-0018
(F-4044 already controlled the 3-way placeholder; what is NOT controlled is the *shipped pre-filled* form, folded into R1 as
a single extra arm if it is cheap), P-0121 refinery. These are balanced or push away from the first option; a reversal would
confirm, not discover. DEAD / WRITE-ONLY rows with no consumer (P-0020, P-0021, P-0097, P-0004) are out unless revived.

## 7. What a clean fix would look like (NOT done: this job is findings only)

* Cheapest and additive: let `judge_panel.rule_detail` take a `counterbalance` option that sends JUDGE_1 the shipped order and
  JUDGE_2 the reversed order (or alternates by call), default off. Under that design a first-option effect no longer agrees
  across the two judges, it shows up as disagreement, which is the signal the panel already knows how to read. It changes live
  verdicts, so it needs a founder ruling and a shadow arm first (decoupled-judge law).
* Where a prompt pre-fills an example, replace it with a neutral placeholder whose option order is randomised per call and
  logged, so the order becomes a covariate instead of a constant.
* Neither is built here.

## 8. Not run / not established

* No Ramses call was made. mixtral :11438, granite :11437 and command-r7b :11441 are Ramses/retired; their order sensitivity
  is untested here. F-4044 remains the only direct measurement and is on command-r7b.
* The hot lane :11433 hung on a trivial JSON chat call (25 s, no reply; `/api/tags` and `/api/ps` still answered, qwen3.5:9b
  resident) so no hot-lane replay was run.
* The pilot covers three stations on falcon3 and gemma4 only (6 of the ~35 ranked stations, none of the R1 live-gate stations
  except P-0117); labels for P-0110 are Claude's, not Travis's; held and metaphor-positive n are small (30, 12).
* No station was replayed on the models the verdicts actually come from for mixtral (Ramses) or command-r7b (retired); the
  two that were replayed are the local ones.
* Skew is not bias. A near-constant verdict is a reason to run the reversal, not a result.

## Appendix A. Per-row table (registry rows that ship the hazard)

Lane/model is the registry's own `lane` field (docs/prompt_registry.jsonl, checked 2026-11-07 with `prompt_registry.py check`:
130 sites, all registered). "Order controlled?" is no for every row unless stated: no reversal of a listed answer order exists
anywhere in the tree except F-4044's arms. Tier = section 6.

| row | lane / model | form and listed order | live evidence | tier |
|---|---|---|---|---|
| P-0001 perception | hot qwen3.5:9b | enum_pipe x4 fields (event_type 4, context_type 5, subject 4, register 5 options) | no categorical log found | R2 |
| P-0003 salience | hot | pre-filled `interrupt: false` | LLM call retired by D-0682 | N |
| P-0004 memory router | hot, WRITE-ONLY | `time_bias recent\|distant\|all`, pre-filled false | no consumer | N |
| P-0007 reflection | hot | pre-filled `needs_more_memory false`, `emotionally_aligned true` | none found | R2 |
| P-0008 critic | hot | pre-filled `approved true`, `identity_consistent true` (+ "WHEN IN DOUBT, APPROVE") | legacy approves 98.8 percent vs decomposed 68.1 (n=495) | R1 |
| P-0009 executive | hot | enum_pipe 6 (`answer` first), pre-filled `should_respond true` | answer 92 percent of 256 internal cycles | R1 |
| P-0014 guidance capture | hot | `is_guidance <true or false>` | not computed | R2 |
| P-0017 decomposed critic | registry lane blank | pre-filled `violation false` per check | flags 31.9 percent | N |
| P-0018 classify | command-r7b :11441 (fails over to hot) | pre-filled `assimilate`, 3 options in prose | assimilate 13 of 32 | F-4044 + 1 arm |
| P-0019 pole gate | command-r7b | prose `fluid, durable, or neither` | F-3790: 34 of 58 forks (59 percent) | R2 |
| P-0037 commitment defeater | mixtral :11438 | bool_or `legitimate` + enum_pipe `class` (5, `achieved` first) | `achieved` is 1967 ledger events but not separable from deed-record detections | R2 |
| P-0038 commitment scan | hot | enum_or `kind defeater or reflexive`, bool_or `load_bearing` | none | R2 |
| P-0039 condensed twin | hot (shadow) | enum_or `kind fragment or tick or silent` | 41/38/21 percent | N |
| P-0044 follow_line generators | command-r7b | `supports "yes"\|"partly"\|"no"` (V1), angle placeholders (V2) | none | R2 |
| P-0048 narrative quality | command-r7b, WRITE-ONLY | enum_pipe 4 (`redemption` first) | redemption 52 percent | N |
| P-0052 self-relate | command-r7b | pre-filled `connects true` | true 90.6 percent (n=2142) | R2 |
| P-0092 / P-0095 / P-0094 left-lane graders | left lane / Emissary (registry lane blank on these three rows; P-0114, the same module, names :11439 gemma4:12b) | pre-filled `integrated true` / `genuine true` / `additive` | no live log found | R2 |
| P-0099 evidence bears | panel mixtral + falcon3, tiebreak granite | literal pair, true first | 5.4 vs 26.7 percent | R1 |
| P-0100 pursuits advances | panel | bool_pipe | 83 vs 86 percent; framing lab 2026-08-23 | R1 |
| P-0101 pursuit close | panel (SHADOW) | bool_pipe | ~0 percent true | N |
| P-0102 follow_line judges | panel | literal pair x3, true first | cuts 14 vs 88 | R1 |
| P-0103 tension resolves | panel | bool_pipe | 15 vs 55; granite 0.000 | R1 |
| P-0104 AI novelty genuine | panel (WRITE-ONLY) | bool_pipe | 100 / 99.8 percent true | R2 (rides with P-0105) |
| P-0105 self_interrogation genuine | panel | bool_or | 99.5 / 99.4 percent true | R1 |
| P-0106 aligns | panel (SHADOW) | bool_pipe | 7.8 vs 25.2 | R2 |
| P-0107 dream resolved | panel (WRITE-ONLY) | PRE-FILLED `true` | 1.5 / 3.1 percent true | N |
| P-0108 social cognition | panel (SHADOW) | bool_pipe, one `%s` template for 4 keys | refs 98 vs 55, supported 25 vs 68 | R2 |
| P-0109 held / contradicted | panel, tiebreak gemma4 :11439 | bool_pipe | held 34 vs 53; contradicted 3 vs 24 | R2 (held in pilot) |
| P-0110 metaphor | panel, tiebreak gemma4 | bool_pipe | 2.5 / 0.1 percent true | N (in pilot) |
| P-0111 coherent | panel (WRITE-ONLY) | bool_pipe | 96 vs 68 | R2 |
| P-0112 contradicts | panel (SHADOW, retired by D-0599) | bool_pipe | ~1 percent | N |
| P-0117 same_lesson | panel | bool_or `<true or false>` | restart-gated, no rows yet | R1 (in pilot) |
| P-0118 curiosity prefire | falcon3 :11440 (SHADOW) | bool_or x2 (`answerable`, `unsupported_link`) | no log found | R2 |
| P-0119 symbol window judge | gemma4 :11439, offline | bool_or `specific` | offline only | R3 |
| P-0120 voice fidelity | falcon3 :11440 (SHADOW) | enum_or `kind claim or commitment or question` | none | R3 |
| P-0121 refinery faithfulness | mixtral (SHADOW) | bool_or `supported` | accepted 70 percent | N |
| P-0122 episodic buffer judge | gemma4 then falcon3 (SHADOW) | bool_or `scene_invented`, list of `true or false` | none | R3 |
| P-0123 AI seeded | panel (SHADOW) | bool_pipe + two pre-filled examples (none/false, moth/true) | none | R3 |
| P-0098 Lane 2 generator | Lane 2 Witness seat (registry lane blank) | enum_pipe `horizon next\|hour\|day` (a generator field, not a judge) | not measured | R3 |

## Appendix B. Findings and follow-up jobs

Findings: F-4339 (reversal pilot: no order effect on three 2-way stations, order-independent lean instead), F-4340 (the sweep itself).
Spawned: J-3719 (R1 live-gate order replay incl. hot lane and the mixtral arm to run later), J-3720 (per-key judge informativeness,
minority-class recall), J-3721 (numeric pre-fills and prose-listed options).
