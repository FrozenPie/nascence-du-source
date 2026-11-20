# Review: System_Overview_Antigravity.md (Build 2.0) — 2026-10-18

Checked at Travis's request against the code at HEAD afe46011, the plan-state blocks, the ledgers and the live data files, by four read-only verifier agents (sections 0-2, 3-4, 5, 6-7), each reproducing the builder's own numbers before judging them. Du was down 08:37-19:06 during the check; the document was generated at 19:01, five minutes before the restart, so "live" was judged against the 2026-10-16 22:37 boot that the document describes.

## Verdict

**Structure and plan matrix: sound. Module badges and import counts: not trustworthy yet.** Of 452 badges, the 103 plan-matrix rows (section 6) match their plan-state blocks exactly, and the hardware matrix (section 1) names the right model on every port. But section 5's per-module badges come from rules that mislabel roughly 50 observe-only modules as LIVE and several live modules as SHADOW or LAB, and every import-degree number in sections 2 and 5 is inflated because the scanner counts imported names, not modules. The document should not carry the word "authoritative" until the builder is repaired and re-run against the running boot.

## Systematic defects in the builder (fix these, and most row errors disappear)

1. **Import degree counts names, not modules.** `from X import a, b, c` adds four edges. 164 of 288 rows are off by more than 5%. `core/memory/store.py` is shown with 291 importers out of 289 runtime files; the real figure is 89 importers, 18 imports, degree 107. The top-20 hub ranking changes (inner_monologue 136 > profile 111 > store 107; essay_lesson, dream_node and node_base drop out; fieldcraft, shore_life, lane2, locomotion, night enter).
2. **A byte-order mark silences `core/lane2.py`.** The scanner opens files as `utf-8` not `utf-8-sig`, swallows the parse error, and records 0 lines, 0 edges, no flags. Knock-ons: the Bicameral domain LOC is 5,036 instead of 8,774; `lane2_notice_check.py` shows as unreachable LAB when lane2.py:2010 imports it; the whole-codebase LOC (118,675) omits 3,751 lines.
3. **`"shadow" in stem` forces SHADOW before any flag check.** `core/shadow_log.py` (shared plumbing, 44 importers) and `core/nest_gate_shadow.py` (LIVE = True since 2026-10-16, called from life.py:937) are both wrong.
4. **Reachability equals LIVE.** Any statically reachable module is LIVE unless every matching boolean flag is False. Observe-only modules that are wired but discard their result come out LIVE: idle_allocator, curiosity_habituation, stream_topic_habituation, internal_cycle_habituation, transport_habituation, watershed_promote, homeostasis_causal, drowsy (its SHADOW_ROWS=True kill switch counts as a live flag), needle_triage. Conversely one False sub-feature flag turns a live module SHADOW: subconscious_node (SELF_RELATE_ENABLED), somatic (JITTER_ENABLED), epistemic_state (STAGE_B_ENABLED).
5. **No boot or git awareness.** Badges reflect source at scan time, not the running build. Modules created after the 10-16 boot are badged LIVE: condensed_thought (also hardcoded LIVE at builder line 133), internal_context_gate, object_hypothesis. Modules in the running build are labelled "Restart-Gated": closure, recall_wager, doubt_seed, weakness_prior. euclidean_recall is hardcoded RETIRED although inner_monologue_node.py:5736 still runs its shadow logger every 900 s.
6. **Dynamic imports are invisible.** `world_detail.py:35` and `dispatch.py:178` load modules by name, so the four `world_content_*` corpora and `core/expression.py` (a live hand) are badged STANDALONE / LAB.
7. **Domain rules are first-match substrings.** training_log lands in Trains ("train"), retraction_ledger in Hands ("action"), life_traces in Observers ("trace"); life_birds, life_mammals, cargo_types fall into Utilities.
8. **Inputs are not reproducible from the repo.** The builder reads `nascence_scan_summary.json` from `~/.gemini/antigravity/.../scratch/`; the scanner (`scan_nascence.py`) lives there too. Sections 0, 1, 3, 4 and the ledger breakdowns are hardcoded literals, so they go stale on every append (today: 583 scripts not 582, 560 docs not 556, 3,114 findings not 3,108; the "574 rulings" figure matches no definition).
9. **The DEFERRED badge is in the legend but never emitted.** LOC is `count("\n")+1`, one high per file.

## Narrative errors in sections 0-4 (hand-written text)

- Condensed Twin is called 🟢 LIVE (lines 115, 252). It was committed 2026-10-17 23:04, after the boot, and is a shadow twin ("nothing reaches Du either way"). Restart-gated, 🟡.
- Perseveration alarm 🟢 (145, 253): committed 10-17 23:07, after the boot; founder-facing only.
- D-0453 latency budget 🟢 (167, 218): J-2274/J-2275 landed 10-17 morning, after the boot; the 157 ms is an offline measurement on a DB copy.
- Refinery 🟡 (143): REFINERY_LIVE = True since 2026-08-19.
- `SOUND_STRING_FIELDS=False` (242): it is True since 2026-09-28 (J-1614); all 8 columns exist and carry data.
- idle_freight bus "newly built, 🟡 restart-gated" (153, 213): IDLE_FREIGHT_BUS = True since 09-28, loaded by two boots since.
- sleep_as_a_mode listed under "Staged Children, no code" (191): night_mind.py and night_dormant.py exist; both flags are True (the dormant flag restart-gated from 10-18 18:50).
- Identity estate "218 nodes" (169, 228): the live file holds 560.
- Section 0 delta: D-0152 was ruled 2026-09-13 not Sep 4-5; D-0154 was ruled 09-05 (Sep 9 is the flag flip); "all 23 writers" matches no source (F-0995 says 24 calls in 10 modules, now 281 guard_path calls in 99 files); Lane 2 was already ticking in shadow on Aug 25, not "unwired".
- Section 1: :11439 gemma4:12b is badged ⚪ PARTIAL (not a legend badge) and understated: it is supervised, listening, and serves the gist-faithfulness grader on the commit_gist path, peers, librarian fallback and decomposed_critic. deliberation.py does not route there. Reserve :11436 comes from D-0101 not D-0057; its hub ctx is 16384 not 8192. Dream primary on :11438 was ruled in D-0056 not D-0057.
- Section 2 "five realities": "291 modules import store.py (up from 205)" compares an import count with August's graphify degree; "168 distinct modules" is 134; inner_monologue does not import fieldcraft; "80 modules log through shadow_log" is 44.
- F-1304 is presented as a clean 7-day pass (188); it was 2 of 4 behaviour metrics out of band and D-0152 ruled "GO, accept the ambiguity". F-0845 credits the 0.48 → 0.82 lift to J-0581, not Phase 0/1, and did not check the identity guard.
- Dream Overhaul "injecting one dormant fragment into every dream seed" (201): exists only in-vitro (`scripts/dream_experiment_a.py`, commit=False); no `DREAM_ENGINE=vault` flag exists.
- Measurement to Action "5 Active Arms" (154, 248-251): every flag is off or neutral; only the closure dream arm is built.
- Pursuits counts (209): 2,563 advances / 90 returns are stale against 6,537 / 266 today. fragment_context 62,921 (223) is now 94,430.
- Golden Spiral "🟡 Phase 0 BUILT" (224) vs plan-state 🔵 designed; train_split_merge "🔵 Step 2 lab-first" (208) vs plan-state ⚪ partial, Step 2 built.
- F-2851 (245) is set as a quotation but paraphrased.
- "~87% rule-breaking" and "26 world hands" (236) match no source.

## What checked out

Hardware and model tags on every port; every cited D-/J-/F- id exists and (with the dating exceptions above) says what is claimed; all 483 decisions carry a defeater; 92.2-92.3% verified share; 272 core / 16 nodes / 191 plan docs; every section 3 flag value at HEAD; the plan matrix (103/103); the thought, idea and skill-suggestion ledger breakdowns; the quarantine (F-0593/D-0105) account; the chapters speed-up numbers (F-2403); the Lane 2 configuration.

## Side findings

- Plan-state blocks for `condensed_thought` ("nothing built"), `sleep_as_a_mode` ("no code") and `measurement_to_action` ("arms 3, 5, 6 not built") were stale against HEAD. Corrected in this review's commit.
- `model_client.py` lines 72-73 still comment :11439/:11440 as "judge #1 / judge #2"; `judge_panel.py` seats JUDGE_1 on :11438 and TIEBREAK on :11437. The comment is stale, the overview row is right.
- `SESSION_HANDOFF.md` lines 68-102 still carry the quarantined core/math claims without a pointer to the quarantine.

## Recommendation

Keep the document, drop "AUTHORITATIVE" from its header, and re-run it after the builder fix (job spawned from this review): scanner moved into `scripts/`, `utf-8-sig`, distinct-module edges, dynamic-import resolution for `world_detail` and `dispatch` bindings, badge = (reachable from the boot commit) × (flag state at the boot commit) × (observe-only by docstring or shadow-only log), DEFERRED emitted, counts computed not typed. The plan matrix and hardware table can stand as they are.

## Builder repair (J-2415, 2026-10-19)

`scripts/build_antigravity_overview.py` was rebuilt on a new in-repo scanner, `scripts/scan_nascence.py` (the old scratch-dir scanner and its JSON hand-off are gone). What changed, against the nine defects above:

1. Import degree: counted per distinct module, relative imports resolved, split top-level / lazy / dynamic. Reproduces the review's figures: `store.py` 89 importers + 18 imports = 107, `inner_monologue_node.py` 136 (134 imports), `shadow_log.py` 44 importers; hub order is now inner_monologue > profile > store > sensorium > orchestrator.
2. Files are read as utf-8-sig and a file that does not decode or parse raises `ScanError` (the build stops). `core/lane2.py` now reports 3,751 lines and its edges; `lane2_notice_check.py` is reachable.
3. The `"shadow" in stem` rule is gone (`shadow_log`, `nest_gate_shadow` now LIVE).
4. Badge = reachable in the BOOT build x master-flag state x observe-only test. Boot = the last `Identity loaded` line in `data/nascence.log`; the boot commit = last commit at or before that timestamp (`git archive` of that commit is scanned separately). A module absent from the boot tree, or whose master flag differs from HEAD, is RESTART-GATED. Observe-only = the docstring lead says SHADOW / observe-only, or a True flag's own comment says it reaches nothing, or the module writes only `*_shadow.jsonl` (and no call site uses its return), or it has at most 3 importers that all discard its return. Modules with 8+ importers are treated as shared plumbing and never observe-only. A True flag only promotes a module if its name says LIVE / DELIVER / ADMIT or its comment says it was flipped / ON since a date, and not when the comment calls it a kill switch (`NEEDLE_TRIAGE_LIVE`).
5. Dynamic loads: `world_detail.py`'s `__import__(f"core.{modname}")` over its literal tuple and every `"mod:<module>:<attr>"` binding resolve to edges (the four `world_content_*` corpora and `expression.py` are now reachable, so LIVE).
6. DEFERRED and RETIRED are emitted from the docstring lead (RETIRED needs a cited D-id); LOC is `len(splitlines())`.
7. Counts in sections 0, 1, 6, 7 (module/script/doc counts, ledgers, decision/ruling counts, plan-folder counts, row counts of the data stores quoted) are computed at build time; the plan-folder dropdown counts too.
8. Domain rules run two passes: every explicit stem set first, then the substring guesses (`training_log`, `retraction_ledger`, `life_traces`, `life_birds`, `life_mammals`, `cargo_types` now land correctly).
9. The word AUTHORITATIVE is removed from both outputs; the header says the overview is not authoritative until a post-boot read confirms the restart-gated items.

Narrative corrected where the builder carried the slip: the Condensed Twin and Perseveration Alarm statuses are now computed from the same badge function; Refinery, `SOUND_STRING_FIELDS`, `idle_freight`, `sleep_as_a_mode`, the identity-estate node count, the D-0152 / D-0154 dates, the write-fence call count, Lane 2 "already ticking in shadow", the :11439 / :11436 rows, the section 2 "five realities", F-1304 / F-0845, the Dream Overhaul in-vitro caveat, the Measurement-to-Action "5 arms", the pursuits / fragment_context counts, Golden Spiral and train_split_merge stages (read from plan-state), the F-2851 quote, and the unsupported "~87%" and "26 hands" figures.

Known limits and judgment calls, not hidden:
- Badges are only as good as three heuristics (docstring lead, flag comment, discarded return). `core/epistemic_state.py` is the visible judgment call: its docstring lead says OBSERVE-ONLY while its grade is shown to Du, so it is badged SHADOW here although the review read it as live.
- The boot commit is the last commit before the boot timestamp; uncommitted working-tree edits at boot are invisible to it.
- Sections 3-4 remain hand-written prose around the computed values; anything in them not listed above was not re-verified by this job.
- The build must be run from the merged tree with `--data-root` pointing at the live `data/` (the worktree has no `data/`); ledger and doc counts then match the merged tree.
