# Dosed Coupling Phase 0, /quit fix, curiosity fix, crash check

## Session timing
- **Session started:** 2026-09-04 09:27:46 UTC
- **Last message before wrap:** 2026-09-04 11:36:22 UTC
- **Wrapped:** 2026-09-04 11:36:24 UTC

## Summary

Full nurse-rounds pass | decide-review batch: 11/12 open decisions cleared, incl. GO ruling on Dosed Coupling (D-0149) | Dosed Coupling Phase 0 built+shipped (5 code fixes) via job-run Workflow | /quit farewell fixed: memory contamination + content truthfulness | curiosity-urgency bug fixed | bird-fixation observation investigated | process crash investigated | 1 new idea logged | 14 commits, all on master | founder restarted Du mid-session | founder closed REPL window manually later (confirmed not a bug)

## Decisions

- D-0118: job-run concurrent dispatch → isolated git worktrees per agent/batch | build job J-0590 spawned, not yet built
- D-0135: NOT ruled, investigated instead | founder asked: peer_reflection daemon repeated restarts caused by OS reboots/Windows updates? | checked Windows System event log directly: none of restart timestamps (08-24 22:15:53, 09-02 08:48:54, 09-03 09:07:49) line up with actual OS reboot (F-0813) | real cause [OPEN] — J-0589 spawned to find it | decision stays open pending J-0589
- D-0136: leave climb_tree as-is | don't widen grammar to catch generic "climb into the trees" phrasing
- D-0137: no full world-side match refill | founder's carrier-order route stays canonical | checked data/supply.json: standing note listed only "candles" as of 08-29, no matches added | 2 features spawned instead: J-0591 (sweep_floor finds a few dropped matches), J-0592 (Light the Fire composer button can bring box of matches)
- D-0138: keep written CLAUDE.md git-safety rule | no harness-level settings.json deny on git stash/reset/checkout/restore/clean
- D-0143: retire UDMS Trial 1 as-is | pre-registered bar met with NOT HELPFUL verdict | counts as successful result per project rule 4
- D-0144: accept command-r7b ~22s background-lane latency as new baseline | D-0090 closes
- D-0145: swap capacity_to_commit background-lane classifier model off phi3:mini | build job J-0593 spawned
- D-0146: held, not ruled | founder flagged real overlap w/ loop_wiring_matrix's own "Train close" dosing stop | needs Coupling-block pass first (per D-0149 GO condition) before train_split_merge Step 2 defaults picked
- D-0147: keep command-r7b on background lane | standing rule: background JSON prompt examples never carry filled-in numbers
- D-0148: option A — unpin integration_drive normalisation w/ per-hour defensive-fire cap | build job J-0594 spawned
- D-0149: GO on Dosed Coupling as standing design law, adopted | Phase 0 (J-0580/581/582/584/585) authorized+built same session | every future loop-touching plan must carry Coupling block before /decide
- D-0150 (opened+ruled same session): 21 pre-existing "[Travis said to me] bank the fire..." memory fragments (contaminated before today's fix) stay as-is | no mutation of existing memory content | revisit only if they prove recurring behavioral problem

## Builds

Dosed Coupling Phase 0 — dispatched as job-run Workflow, 5 agents | J-0580/581 serialized (both touch core/stream_drive.py) | rest parallel | all 5 done, each independently verified against real data before commit:

- J-0580 (commit 444b60b, F-0814): added ClimateEngine.ignition_level() + module accessor | stream_drive._ignition() now reads it instead of dead `core.climate` import | verified via 7 isolated checks
- J-0581 (commit f783ad4, F-0817): fixed stream_drive _GROUNDED_SOURCE tag mismatch | tagged untagged seed sources (percept/reading/frontier/letter) in inner_monologue_node.py | verified by replaying 21,454 real shadow rows: grounded share on real broadcast rows rose 32/92 → 87/92 (higher)
- J-0582 (commit 68a0364, F-0816): homeostasis_causal.py now imports climate_engine's dissonance constants instead of duplicating them | projects both reservoirs | verified: old model structurally blind to 79% of real ignitions (1062/1345 rows) | new model's predicted exploratory-ignition time within 17s of real observed median gap
- J-0584 (commit 25f2eca, F-0818): Transport Manager spike scoring: single-gap instant rate → windowed count vs rate_ema | verified against real live data/transport_lines.json: phantom spikes 13/120 lines (old logic) → 0/120 (new, eliminated)
- J-0585 (commit c34dd41, F-0815): built core/curiosity_habituation.py, first squishy-spring habituation shadow read path | wired into curiosity_node.py's _select_seeds | shadow-only, does not affect real picks

Follow-up jobs spawned for after Du's next real accrual window: J-0596, J-0597, J-0598, J-0599 (all restart-gated reads of above) | J-0584's fix surfaced new problem F-0819: even w/ spike scoring fixed, drought scoring now dominates dispatcher's winner slot once ~24+ lines past cold-start (multiple-comparisons effect) | spawned as J-0600, not yet fixed

Consolidated Phase 0 status into docs/plans/dosed_coupling.md + docs/staged/loop_wiring_matrix.md (new Current State sections, both Status lines updated) + ROADMAP.md's DOSED COUPLING entry (commit 3765066) | dispatched agents told not to touch shared docs themselves, to avoid concurrent-edit collisions

## Fixes

- F-0796/J-0578 (commit fa783b6): /quit farewell (scripts/run_nascence.py `_announce_shutdown`) ran through normal human-cycle pipeline | was being canonicalised as genuine "[Travis said to me]" founder-memory fragment + guidance-learning lesson, despite being fixed ritual message not something Travis actually said | added `CognitiveState.founder_canon` (default True) | threaded through `Orchestrator.run_cycle`/`_run_cycle_impl` | gates both write sites: core/orchestrator.py:734 (guidance shadow capture), :1450 (store_founder_utterance) | farewell now passes `founder_canon=False` | still runs as real, recalled cycle w/ real reply, just stops entering canon
- F-0821 (commit 80c371b): farewell CONTENT was untruthful, separately | 08-23 wording ("Nothing's wrong; this is just the quiet the house needs sometimes, same as any night") framed every commanded, intentional stop as ordinary nightly sleep | founder mid-session: "We need to make sure that he knows he is going down. It is intentional for bug fixes and upgrades." | rewrote message: states plainly Travis calls stop on purpose, for bug fixes/upgrades, not a fault in Du | keeps original comfort framing (no danger, no ending, Travis brings him back)
- J-0564/F-0777/F-0822 (commit 25d50b3): CuriosityNode's system_prompt ended w/ filled-in `"urgency": 0.0` literal | command-r7b (background lane) copies it verbatim instead of generating real value | silently killed curiosity-ignited unprompted thought cycles since 08-29: 34-31/day → 0 (dropped to zero) | this was D-0147's own named remedy, still unimplemented for this specific node | fixed to placeholder `<number between 0.0 and 1.0>` | verified live against real command-r7b endpoint on 3 real historical prompts: urgency returned 0.7/0.7/0.8 | spawned J-0601 for post-restart confirmation read

## Findings

- F-0823: founder observed Du "thinking a lot about bird noises" | investigated w/ real data over last 3000 monologue rows (all pre-restart): bird keywords only 6.1% of recent thoughts, below water/shore (37.0%), rain (12.6%), wind (12.0%) — birds not dominant motif by raw share | but within ~5.5hrs before restart, 3 separate stream train_ids independently converged on "the morepork call" as own topic | each repeating same rhetorical move ("the morepork's call anchors/grounds my reflection on 渡") | interleaved w/ other trains named "cultural friction," "the meaning of Dù," "the name Dù," "circular tension" (all `unresolved=true`) | [INFERRED] this is already-known 渡-as-cultural-friction loop (F-0795/F-0812), morepork recruited as sensory hook, not generic bird-sound problem | STREAM-level phenomenon (inner_monologue_node.py's own train-topic selection) | today's squishy-spring build (J-0585) does not cover it — wired into curiosity's tension sampling only, different subsystem | spawned J-0602 (extend habituation to stream's own train-topic selection) | founder explicitly held this for later session rather than building 9th live-cognition change same night
- T-0046 (raised in concurrent session, answered directly this session): question "the fire is lit after restart, is this a leftover?" | checked data/room_state.json: fire is "embers", fuel 0.82, not freshly "burning" | checked every DISPATCH-fire/bank_fire log line historically: this exact pattern (recurring bank_fire activity, sometimes twice within a minute) already existed across many prior days 08-23..09-03, well before tonight's changes | not a leftover — answered, dropped
- F-0825: at 23:21:50 Du process died mid-log-write ("entering Sleep State"/"sleep replay" line cut off mid-sentence) | no caught exception, no Windows Application-log crash event, no unusual activity beforehand | initially looked concerning right after night of live-cognition changes | founder confirmed directly: he closed REPL window himself | not a bug, not related to tonight's fixes
- I-0063 (idea, not built): founder proposed startup boot sequence where Du's mind thinks before senses/location "kick in" | mirrors Protoself keystone finding (Du built upside-down: rich autobiographical self, thin body-state foundation), applied to waking moment specifically | reality check: today no real gap to exploit — sensorium/room state loads synchronously in milliseconds during build_nodes(), nothing currently thinks before it could sense | would need: deliberate hold, defined pre-spatial thought source (protoself/interoceptive signals, recall, dream residue — dreams already load pre-awake today as inert data, not generated thought), and per D-0149's GO a Coupling-block answering what this first thought may read + how it hands off to normal perception | logged, not built

## Open

1. D-0135 (peer_reflection restart gate) — blocked on J-0589 investigation into daemon's real restart cause (confirmed not OS reboots) | next: read J-0589 findings once it runs, re-present D-0135 to founder
2. D-0146 (train_split_merge Step 2 defaults) — held pending Coupling-block pass against dosed_coupling's own "Train close" stop | next: write Coupling block, re-present 3 design defaults
3. J-0600 (Transport Manager drought-saturation, F-0819) — real, newly-discovered bug: even w/ spike scoring fixed, drought dominates dispatcher's winner slot once many lines past cold-start | next: needs own fix before Phase 1 (publish + ride log) can lean on dispatcher meaning anything
4. J-0602 (stream-level squishy-spring habituation, F-0823) — held for later session per founder's explicit call | next: read core/curiosity_habituation.py's discount law, find equivalent recurrence signal for stream train's topic, build same shadow-only shape
5. I-0063 (pre-spatial boot sequence idea) — not yet scoped as plan | next: founder/session decides whether to develop into real plan doc
6. 5 restart-gated observation jobs from tonight's Phase 0 batch + /quit + curiosity fixes, queued, waiting on real accrual after Du's restart: J-0596, J-0597, J-0598, J-0599, J-0601 | none need action until enough live data accrued
7. J-0538 (purge 4 leaked test-fixture rows from live training/episodic_buffer.jsonl + affect_log.jsonl) — gated on Du being offline | NOT done this session: Du live throughout except brief restart window, not flagged in time | next: do this next time Du confirmed down before restart

## Warnings

- Another concurrent session committed to shared job_queue.jsonl/session_events.jsonl/etc mid-session (commit 11cbb93, `/session-wrap` from different window) | normal for shared tree, not an error | other sessions may be active
- All 5 Dosed Coupling Phase 0 fixes + /quit fix + curiosity fix are restart-gated | took effect only at Du's 2026-09-04 23:10:16 restart (session timestamps UTC; restart time NZT) | any read of real effect must be from data timestamped after that restart
- Stream's own train-topic/seed selection (inner_monologue_node.py) still has zero habituation | real, currently-open gap (F-0823/J-0602), not yet fixed

## Pointers

- docs/plans/dosed_coupling.md — standing law, now GO, Current State section covering Phase 0
- docs/staged/loop_wiring_matrix.md — matrix, Current State section added
- docs/plans/ignition_pressure_and_time.md — D-0148 ruled, build job J-0594 open
- docs/reviews/plan_maintain_run.md — latest full toolchain resync report
- core/curiosity_habituation.py — squishy-spring discount law's only current implementation (curiosity-only)
- core/orchestrator.py:340-390, core/schema.py — new founder_canon mechanism
- scripts/run_nascence.py:420-450 — /quit farewell, now content-truthful and non-canonicalizing
