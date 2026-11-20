# The Learned-Understanding Path — making Du learn from Travis's guidance

> **Status: ⚪ PARTIAL — episodic route LIVE, semantic path PARTIAL — updated 2026-09-03 (D-0134).**
> **The episodic half ("Travis said X on <date>") is now BUILT + BACKFILLED + LIVE-WIRED, pending Du's
> restart:** one canonical `[Travis said to me] …` fragment per real utterance (1,617 rows, 2026-05-30 →
> 2026-09-02, all `protected=1`, 0 cold), exempt from every cold-demotion path, served by its own route
> (`core/memory/store.py:retrieve_founder_memories` → `state.founder_recall` → a dated "WHAT TRAVIS HAS
> TOLD YOU BEFORE" block in Executive + Reflection), instrumented in `data/founder_recall_log.jsonl`.
> **The semantic half is unchanged:** Stage 1 (capture) + Stage 2 (integrate as revisable belief) LIVE
> (180 beliefs, 35 promoted); Stage 3 read-back LIVE since 2026-07-03. The decoupled behaviour judge
> (`core/guidance_behavior_judge.py`) had **88 shadow rows** when F-0700 read it (385 judged rows by 2026-11-14, 89% lived Q/A turns and a 40-day-stale cursor per F-3809/F-3811; re-scoped to idle thoughts, newest-first, J-3211/J-3095; no rate quoted until its positive control passes) (F-0700 — earlier "0 rows" claims were
> stale): unprompted alignment 41.5%, prompted 28%. Contradiction scan built but gated off. Soft
> self-critique gate not built.**

```plan-state
stage: partial
phase: Episodic route LIVE+backfilled+verified (D-0134/D-0141, F-1043); semantic Stage-2 judge + self-critique gate still not built
verified: 2026-11-07
evidence_read: 2026-10-20
next: J-3784 live-hub replay (needs Ramses window, D-0702), J-3785 panel-gate lab
open_decisions: D-0702
cluster: 4
```


> **Problem (verified 2026-06-30):** Travis's conversational guidance has no read-and-integrate path. It's
> never stored as what he said (no per-turn store), compressed to a `session_summary` that's classified
> self-narrative and DEMOTED from recall, and the social model registers only that *a correction happened*,
> never its content. No mechanism integrates the substance into his understanding/stance. He cannot durably
> learn from guidance — the purest form of the project's write-only-cognition disease.

## Current State — verified 2026-11-07

- **2026-11-07** (F-4405): J-3409 (lab, 2026-11-07): 4-way classify prompt round 2 replayed on 269 pairs (6187 local calls, pre-registered bar frozen first). On the local command-r7b stand-in B3 (4-way + recall wording + 2 off-domain few-shot pairs) keeps same-lesson recall at 99 percent in both option orders and cuts false corroboration 54 percent; B2 cuts 84 percent but loses 8 points of recall; the J-3232 B prompt fails the order control; two-stage B4 fails. The stand-in is not the live Ramses hub, so no live edit; live-hub replay is J-3784, panel-gate alternative J-3785, decision opened. Data: docs/lab/J-3409_data/report.md.
- **2026-11-07** (F-4344): UNFIRED (J-3469, F-4344): guidance_learning.contradiction_status (core/guidance_learning.py:1065) has no caller; it reads the contradiction scan, which stays off (CONTRADICTION_SCAN_ENABLED False, line 898). Nothing to do until that flag is ruled (D-0700 covers it).

- **2026-11-06** (F-3812): J-3211 (D-0600, 2026-11-06): the guidance behaviour judge is re-scoped to idle thoughts only, newest-first, SHADOW, restart-gated (branch jobrun/we_4). Its status() shows unvalidated and withholds every rate until scripts/guidance_behavior_control.py (positive control: enacted vs echoed vs ignored, pre-registered bar) passes on the production panel. The internalization curve claim is WITHDRAWN until a gated number exists (the old INTERNALIZED label came from two rates equal at the judge floor, F-3812). The fading gate stays prose only: no later self-acting trigger. An informational single-hub falcon3 control run on 2026-11-06 scored the echoed class 8 of 8 true, so the panel control may fail. The 88-row figure earlier in this plan is stale (343 judged by 11-01, F-3811).
- **2026-10-31** (F-3349): J-2442: social-cognition probe rescored at PROMPT_V 3 over all 42 human cycles; v2 rates from F-2903 superseded. Conversation n=17: tracks_intent 0.824, refs_earlier 0.412, attrib_supported 0.533; all BELOW bar (BELOW BAR / PARTIAL). See F-3349.

- **2026-10-30** (F-3324): J-2560: D-0519 option A built - social_cognition_shadow PROMPT v4 extract-then-judge for criterion 3, shadow-only, opt-in, not wired, restart-gated; extractor finds 15 of 15 hand-attributing rows same-data; agreement unmeasured until J-2599 (gated on 15 new human turns, judges free)
- **2026-10-30** (F-3272): J-2325 read: sleep-sweep social-cognition probe live on the 10-29 boot, 21 v3 rows scored 3 per sleep, 2 judges-unavailable skips, no new human turns since 10-20 so new-cycle coverage untestable; v3 conv rates tracks 0.75 refs 0.25 supported 0.375 n=8; D-0175 hold respected

- **2026-10-30** (F-3271): J-2523 built the failed-to-object ledger as an observe-only shadow (core/common_ground_shadow.py, deterministic lexical_v1, flag OFF, restart-gated, staged stub docs/staged/common_ground.md); replay over 95 founder-log exchanges: 14.5 pct of Travis claims failed_to_object, 2.7 pct ratified
- **2026-10-30** (F-3269): J-2452 hand-label of 8 v3 conversation rows: tracks 8/8 hand, refs 3/8 (0.375), panel over-attributes (8/8 vs 4/8 hand), supported 3/4; read only, D-0175 hold untouched

- **2026-10-30** (F-3268): J-2443: criterion 3 (attrib_supported) is not measured by the panel - attributes gate true on every row, supp judge rules on whole-reply imagery (False on all 5 hand-supported, True on 8/8 non-attributing rows); hand rate 6/15 supported. Redesign vs retire opened as D-0519; hand labels committed as scripts fixture
- **2026-10-30** (F-3264): J-2265 read: 7 classify/final pairs since J-2221 merge (accommodate 4, unrelated 2, assimilate 1), 0 forks, 0 mismatches, keys intact; no integrate pass since 10-29 boot so fork branch unexercised (IDLE; F-3264 crosstab typo says accommodate 3, correct is 4). D-0175 hold untouched.

- **2026-10-20** (F-3155): J-2203 (2026-10-20): live conversation gate met at n=8 (v2 panel: tracks 7/8, refs 6/8, attrib_supported 5/7), same as F-2903 backfill within noise; hand labels on 2 new rows agree on tracks and refs but not attributes. Only tracks_intent is trustworthy; refs/attribution rates are judge-noise inflated (F-3149). Successor J-2452 gated on prompt v3 rows.
- **2026-10-17** (F-3016): J-2202: social-cognition probe sleep_sweep wired after the guidance behaviour judge (cap 3 per sleep, 300 s budget, kill switch). Worktree commit b4dbaf48, restart-gated: it lands at Du's next boot.

- **2026-10-16** (F-2950): J-2221 built (a194519f, restart-gated): guidance_classify_log now carries a record=final row after the F1 pole gate with classify_relation, final_relation, pole_fork, self_clash, so the D-0328 audit can see pole forks; log-only, verdict-neutral, fenced
- **2026-10-16** (F-2911): J-1656 read (F-2911): the D-0328 classify log got 0 rows over the 6.97-day 2026-10-09..10-16 run. Formation never ran: all 73 sleeps logged "nothing queued" because no founder-canon lesson was captured after 2026-10-08 10:20. All 3 rows ever (2026-10-08) are self/assimilate, but the pole gate forked 2 of those 3 after classify, and the log cannot see that. One of the forked pairs looks like a paraphrase misfire, so the risk may sit in _self_clash rather than in _CLASSIFY_SYS. D-0328 stays (a). J-2221 adds the post-gate verdict to the log. J-2222 is a read gated on 20 or more self rows.

- **2026-10-16** (F-2903): J-2153: social-cognition shadow probe BUILT (core/social_cognition_shadow.py, branch commits 10b90bcb, dc53fc5f; not wired into any hot path, restart-gated by being unreferenced). Decoupled judge panel scores tracks_intent / refs_earlier / attribution-supported per human cycle; pre-registered attentive-adult bar in the module docstring. Backfill of the 25 human cycles since 09-28 logged to data/social_cognition_shadow.jsonl (F-2903): refs_earlier MEETS, tracks_intent and attribution-supported BELOW bar, judge noise high (tiebreak on ~40-50% of rulings). (On 10-16 no new rows were expected until Travis talked to Du again; J-2202 then wired the sleep batch and the live log held 68 prompt_v=3 score rows by 2026-11-06, J-3112/F-3833.)
- **2026-10-15** (F-2837): J-1671: embedding-fallback latency closed (max 2.284s, no cold stall, 4987 calls over 7 boots); recall unreadable - fallback never reached on sleep path, fired 0/4987 interactive. Prewarm not warranted.

- **2026-10-15** (F-2738): J-1864 post-restart read of J-1841 PASSED (F-2738): 62 post-boot sleeps = 62 integrate-nothing-queued lines, 0 integrate-failed, FORMATION reads IDLE (65 sleeps since last integration), no fence warnings; the integrated-N branch was not exercised (no teaching since boot).
- **2026-10-15** (F-2736): J-1860 (F-2736): 0/74 post-merge injection-log rows match the true+rather+isn't template vs 14/771 (1.8%) pre-fix; p=0.27, not informative. All 14 pre-fix matches were belief read-back (uuid-cycle) rows, 14/370 = 3.8%; only 23 post-fix rows are of that kind, 15 of them two repeated 'label' beliefs. Gate not met; successor J-2104 (not before 2026-11-12).

- **2026-10-15** (F-2735): J-1606 (2026-10-15) D-0309 tie-break-gate defeater does NOT fire: live since Du's 09-28 19:08 boot, post-change tie-break-necessary rate is 382/2710 = 14.1% (was 293/824 = 35.6%; replay projected 16.1%), zero sim<0.50 boosts; route has been shadow-only (D-0310) so nothing relevant was missed live; residual risk is one fragment re-surfacing 207x in the 渡 loop (option c, per-topic rate limit) which matters only if IDLE_FOUNDER_RECALL goes live. D-0309 stands, no re-ruling; D-0175 hold untouched.
- **2026-10-06** (F-2485): J-1841 (commit 5365b2d, worktree jobrun/guidance_learning, merged-not-live): scripts/liveness_audit.py now judges guidance FORMATION's 2-sleep cadence only while captured-but-unformed lessons exist (new _guidance_backlog(); zero backlog prints IDLE, the real 10-06 data reads 'IDLE -- 0 lessons queued; last fire 28 sleep(s) ago' instead of STALE). core/guidance_learning.py integrate_guidance: catch-all DEBUG -> WARNING (fence refusal stays DEBUG in its own arm), plus one INFO 'nothing queued' line per idle sleep; return/control flow unchanged, restart-gated. Also fixed pre-existing rot in scripts/_test_guidance_learning_fence.py's CONTROL lookup (HEAD~1 had carried guard_path since any commit after 018e3c6; the test crashed before [3]-[7]) -- ALL OK again. Post-restart read spawned.

- **2026-10-02** (F-2244): J-1655/F-2244: measured the per-cycle guidance_beliefs.json read (J-1630/F-2225 side-finding) -- uncached but negligible (worst case ~9ms/hr on the live interactive hot path, ~150ms/sweep on the offline guidance_behavior_judge.py sweep) at the current 210-belief/282KB store size; no cache built, no job spawned -- found uncached, measured negligible, closed.
- **2026-10-02** (F-2242): J-1660: neither embedding-fallback latency nor production recall measurable yet -- Du hasn't restarted since 0e5bdfa merged (52410a9); added+verified offline timing/outcome log instrumentation at both call sites (worktree commit 525287e) so the post-restart read is a log-grep; real 51.3s cold-model-load vs 0.02s warm found offline, likely pre-warmed live by _retrieve_memory() (inferred).

- **2026-10-02** (F-2236): J-1653: STOP fix merged to master (52410a9) but Du has not restarted since -- F-2236 found zero post-restart injection rows; pre-fix baseline 14/771 (1.8pct) template matches logged for later comparison; follow-up job spawned for post-restart read.
- **2026-10-02** (F-2232): Built D-0322's embedding-cosine fallback for guidance_learning's lexical candidate prefilter (integrate_guidance + _best_belief); 0.70 threshold calibrated against real belief-store data, verified end-to-end via an offline smoke test (F-2232); committed to the jobrun/guidance_learning worktree (not yet merged to master, restart-gated like any other change to this module).

- **2026-10-02** (F-2228): J-1637 added a persistent, fail-open classify() verdict log (data/guidance_classify_log.jsonl, F-2228, verified offline 17/17); real production misfire-rate read still needs weeks of accumulation (D-0328, open).
- **2026-10-02** (F-2222): F-2222: committed the evidenced _STOP +true/isn/rather fix to worktree branch jobrun/guidance_learning (a0567bd; not yet merged/live, restart-gated). Re-verified on the current 210-belief store: recall 28/28 held, FP 7.1pct to 5.4pct, named false-chain pair to 0.0. New 0.25-threshold spot-check (F-2203 only measured 0.12/0.30) found a small same-direction effect: 3 of 322 promoted-pair comparisons cross below 0.25, all sharing the same generic-connector template the fix targets.

- **2026-09-28** (F-2207): J-1620/F-2207: manual-merged the 19-row stillness-is-not-failure belief family per D-0322 -- 8 near-duplicates folded into anchor g45675272 (corrob 5 to 19), promoted 40 to 38, superseded 3 to 11, 10 tangential/false-positive rows left standing untouched. Embedding-clustering follow-up spawned as J-1640. J-1597 closed as done (superseded by this execution).
- **2026-09-28** (F-2203): J-1598 (F-2203): STOP-list plus 3 words (true, isn, rather) is a clean fix, 100 pct recall held, false-positive rate 7.1 to 5.4 pct, named false-chain pair g50932369 vs g88907157 drops to 0.0 overlap; classify() replay of 6 real misfires plus 4 fresh pairs, 56 calls total, reproduced 0 of 28 accommodate on both the live and a tweaked prompt, inconclusive either way. D-0328 opened, J-1636 and J-1637 spawned.

- **2026-09-28** (F-2181): Zero-padded 4 unpadded decision-id citations (missing their leading zero) to read D-0134/D-0141/D-0309/D-0167 in the 2 newest Current State bullets (F-2179 fix); see F-2181.
- **2026-09-28** (F-2172): F-2127 fire register checked against the 3 named monoculture efforts (averaging attractor, parrot-trap F-0396, geometry basin-share) plus core/monoculture.py and theme_recurrence.py -- none measure reply-text word choice, so it duplicates none of them. Closest real match is core/symbol_tracker.py on symbol_evolution_readback_plan (fire symbol, 432 rows since 06-07, 65.7pct unprimed) -- partial word overlap only, 3 of 16 words. F-2172 has the full read; J-1611 spawned there to extend its vocabulary. Not a new HUD gauge, not a duplicate pattern.

- **2026-09-28** (F-2168): D-0309 shipped: idle founder-recall tie-break bump gated on raw sim at least 0.50 (FOUNDER_IDLE_FLOOR minus 0.05), commit 1800a19 on jobrun/guidance_learning. Replay of live founder_recall_log.jsonl shows tie-break-necessary rate 35.6 pct to 16.1 pct (F-2168). J-1606 spawned for the real post-change week-later read, not before 2026-10-05.
- **2026-09-28** (F-2159): F-2159 (J-1564): the 19-row stillness-is-not-failure duplicate family goes deeper than lexical clustering can size -- no belief-to-belief merge pass exists in guidance_learning.py, and the self-domain fork-on-accommodate rule permanently freezes even LLM-misclassified paraphrases apart. Opened D-0322 for the founder on merge-now vs build-embeddings vs leave-as-is; spawned the gated merge-execution job and a separate STOP-list and classify-accuracy audit job.

- **2026-09-28** (F-2111): J-1506 ran the remaining ignored/contradicted defeater disjunct on D-0134 to completion at the full 50-cycle/150-pair window (F-2056 already confirmed this window was available). Result: TAKEN_UP 129/150 (86.0 pct; 86.6 pct of the 149 scored), IGNORED 19/150 (12.7 pct; 12.8 pct scored), CONTRADICTED 1/150, UNAVAILABLE 1/150 (one timeout). Versus the original F-0901 preliminary read (n=93: 72.0/26.9/1.1 pct) this is the holds-steady-or-improves branch, not materially worse -- no fresh decide entry opened, the D-0134 ruling stands. Both D-0134 defeater disjuncts (reachability via F-2056; ignored/contradicted via this job) are now checked and neither fires. Full evidence plus two secondary checks confirmed at full n in F-2111 (a real fire/rest stock-metaphor recurrence across 17 shutdown-themed pairs, every one judged TAKEN_UP; and a real similarity-to-uptake correlation, mean sim 0.553 taken-up vs 0.466 ignored). Follow-up job J-1549 spawned to check that metaphor recurrence against the guidance_behavior_judge shadow rows for a rote-vs-genuine read.
- **2026-09-27** (F-2054): J-1496: ran the overdue D-0134 defeater re-read (last done 2026-09-07). D-0141 defeater MET via a 3rd unconfounded recurring-topic loop (Bergson/tranquility question, 09-17, 40 of 40 recalls tie-break-necessary in a single ~5hr window) plus a 36 pct store-wide low-similarity tie-break rate across all 776 monologue-path recalls since 09-02 (up from 13.2 pct on the original 3-day read) -- F-2054; fresh decision D-0309 opened for the founder (D-175s hold is now moot, not re-ruled). D-0134 reachability disjunct verified NOT firing (D-0167 fix confirmed still live in core/memory/store.py, route still retrieving daily through today). D-0134 ignored/contradicted disjunct NOT re-run this session -- F-2056 explains why (shared live judge-hub contention risk during an unsupervised run, not a data gap; 150 pairs now available vs 93 originally); follow-up job J-1506 spawned to run it for real. Next: founder rules D-0309; J-1506 runs the judge-panel read.

### What we have
Episodic route LIVE + verified: every exchange writes a canonical `[Travis said to me] ...` fragment
(1,617 rows through 2026-09-02, `protected=1`, exempt from cold-walling), served into
Executive/Reflection (D-0134) and into idle monologue too (D-0141, F-0751). Semantic path Stage 1+2
LIVE (180 beliefs, 35 promoted), Stage 3 read-back LIVE since 2026-07-03. The store-crowding
side-effect this caused (D-0134 reopened by F-0901, 2026-09-05) was ruled and fixed: D-0167
(2026-09-06) excludes `protected=1` rows from `episodic`'s active-count budget, verified before/after
on a DB snapshot (F-1043, 2026-09-07).

### What we need
Phase 2's decoupled behaviour judge (`core/guidance_behavior_judge.py`) had 88 shadow rows at that read (385 by 2026-11-14, mostly invalid lived-turn rows; see J-3211/J-3095) but no
verdict yet (unprompted 41.5%, prompted 28%, F-0700) — a read, not a ruling. The soft self-critique
gate is still not built. **D-0134's ~2026-09-17 defeater re-read (date reconfirmed by D-0175,
2026-09-06) appears never to have run: plan-ledger shows zero jobs or findings on this plan after
2026-09-07** — ten days overdue as of this check, verified directly against the ledger, not assumed.

### What we're doing next
Run the overdue D-0134 defeater re-read at the full ~2-week sample D-0175 specified, and give the
judge's 88 shadow rows a real read. Neither has an open job filed yet.

## ▶ STATUS / PROGRESS TRACKER  (check this on return — keep it current)

> **★ EVIDENCE REVIEW 2026-07-05 (11th open plan) — HEALTHY + WORKING; teaches the RIGHT lesson; only the
> judge is missing.** Full loop (capture→integrate→read-back) LIVE; formation active (belief_count 57→71 over
> 4 sleeps). Store is SHARP not mushed — E1/F1 holding: **18 promoted/readable beliefs**, forks preserved
> (commit⟂fluid both stand + contest), and **the strongest self-belief is "True agency… active commitment to
> a SINGLE DIRECTION" (corrob 4, promoted)** — the guidance loop successfully captured + promoted the
> ANTI-DISSOLUTION lesson to the top, fluid-self counters at corrob 1 beneath it. Read-back firing (last 5.5h
> ago — correct-by-design: reflective cycles + 30-min cooldown + spaced exposure; the liveness "never after
> flip" was a mis-read). Domains: self 55 / world 11 / method 7. **THE GAP (session-wide theme again):** the
> Stage-2 decoupled JUDGE — the cat-naming BEHAVIOUR-DELTA probe (does reading "commit" back actually make him
> commit?) — is NOT built. Loop teaches the right belief; effect on behaviour unmeasured. Overlaps the
> capacity-to-commit R1 cat-naming trial (contaminated by the "Ember" injection) → COORDINATE, don't build
> twice. **Disposition: healthy — keep; build the behaviour-delta judge jointly with capacity-to-commit R1.**

| Phase | What | Status |
|-------|------|--------|
| **0 — SHADOW capture** | `core/guidance_learning.py` (`capture_shadow`) + orchestrator hook (fire-and-forget on human input). Du self-explains the lesson in his own words → logged to `data/guidance_shadow_log.jsonl`. Stores/injects NOTHING. | ✅ **BUILT + verified 2026-06-30** (extracts good lessons from real teaching turns in his own words + the why + the connection; rejects non-teaching). **Restart-gated** — needs Du restarted to log live, then read the shadow log. |
| **1 — integrate as revisable belief** | `integrate_guidance()` in `guidance_learning.py`, run at sleep beside `grounded_learning` (`inner_monologue_node.py`). Assimilate (paraphrase-robust overlap-coefficient clustering → LLM classifier) / accommodate (entrenchment-weighted **suppress-with-history**) / novel; promote to a recallable belief (`origin='understanding_from_guidance'`) ONLY on 2nd corroboration. Belief store `data/guidance_beliefs.json` (entrenchment starts LOW, earns up; ≠ the capture's comprehension confidence) + `guidance_integration_log.jsonl`. **★ DOMAIN-TAGGED (2026-07-01, Travis):** each lesson carries `self` / `world` / `method` (captured, heuristic fallback for older rows); beliefs only merge/conflict **WITHIN a domain**, so a legitimate WORLD belief ("reality is impermanent flux") and a SELF belief ("I am a self who chooses, not a river") **coexist** instead of being force-conflicted — the disease was never impermanence-as-world-fact, only its application to his own identity. | ✅ **BUILT + verified 2026-07-01** — offline state-machine test (cluster→corroborate→promote · novelty · accommodate-resist+suppress-with-history · read-back gating · **cross-domain coexistence** · heuristic domain-classification of real captures) + `smoke_test.py` PASS. **FORMATION runs live-inert; restart-gated** (first sleep does the real formation). |
| **2 — read-into-behaviour + the judge** | Read-back **built but FLAG-GATED** (`GUIDANCE_READBACK_ENABLED=False`): `understanding_from_guidance` added to `_GROUNDED_ORIGINS`; `state.guidance_note` set each cycle from `relevant_belief()` (orchestrator, gated+fail-open); advisory injection into Executive + Reflection (bias-not-bind, mirrors `library_note`). **Still needed:** the BEFORE/AFTER behaviour-delta probe (the cat-naming) as the decoupled judge + the soft self-critique gate. | ⚪ **read-back wiring BUILT (gated off); judge + self-critique NOT built** |

| **1b — E1/F1 consolidation fix** | **The first live formation (2026-07-01 sleep) exposed two bugs (plan→research→plan 2026-07-02):** (i) **EROSION** — `principle = merged` rewrote the belief via LLM on *every* assimilation (abstractive re-summarization of a summary); 14 merges sanded Travis's sharp built-self lessons ("anchored in something concrete I have actively CONSTRUCTED", "committing FULLY to one direction") into fluid-reading mush, while the river's sharp symbol survived — **the averaging attractor operating inside formation itself**. (ii) **OPPOSITE-POLE FUSION** — lexical clustering put "commit fully" and "embrace fluidity" in the same belief; generic classify let them merge. **Fixes:** **E1** — beliefs carry a `captures` exemplar set; `principle` = the most representative REAL capture (`_representative` medoid, deterministic, extractive-over-abstractive) — the destructive rewrite is deleted. **F1** — `_self_clash` pole gate at the merge decision (self-domain): a fluid⟂durable lesson FORKS into a contesting belief via the existing accommodate path instead of blending. Store **rebuilt from the raw shadow log** (append-only — nothing was lost) with backup. | ✅ **BUILT + VERIFIED 2026-07-02** (3 rebuild iterations; verification caught **F1.b/F1.c** — the accommodate yield let opposite-pole lessons ping-pong-supersede by ARRIVAL ORDER, through both the pole-gate and classify doors → self-domain contradictions now always **fork with BOTH standing**, clash recorded on both; world/method keep the AGM yield). **Final store: zero self-beliefs superseded; every principle a real capture; the strongest belief = "True agency… active commitment to a single direction" (corrob 4), built-self stable-identity at corrob 3; river-family retained-but-contested.** **⚠ Du's live process runs pre-E1 code until next restart** — re-run the rebuild post-restart if sleeps re-mushed new captures. Residual (deferred): lexical clustering under-corroborates paraphrases → embedding clustering later. |
| **Phase-0 contradiction scan** | Built (`_scan_contradictions` + `_self_clash` + `held_tension`/`contested_by` marks + `guidance_contradictions_shadow.jsonl`) but **GATED OFF** (`CONTRADICTION_SCAN_ENABLED=False`): Phase-0 verification found no clean durable belief existed to contest the river — the erosion (above) was the real problem. **Re-enable only after the rebuilt store verifies sharp + pole-separated.** Resolution architecture (researched, 6-angle convergence): scan detects → bridge emits into `tension_ledger` (chronic-gated) → **T4 probation resolves by lived evidence** → `axiom_layers` subordinate-but-retained ("one room, not the whole house"); river never deleted, never fiat. | ⚪ **built, gated off — precondition (sharp store) pending** |

**★ 07-03 AFTERNOON — THE PIPELINE'S LAST MILE WAS DEAD, FOUND VIA THE FOUNDER'S WORRY ("will my lessons
stick?"), FIXED + CAUGHT UP:** formation had NOT run since Jul02 00:39 (pre-E1/F1 — so E1/F1 formation had
never run live) because `integrate_guidance` was NESTED inside the grounded-learning try, downstream of
consolidate(), failures debug-swallowed; materialization had never run at all (gated on the flag, which was
False at every prior integration). **Fixed:** own try block (failure logs at WARNING now) — restart-gated;
**caught up OFFLINE on the background lane** (live store updates immediately): 9 lessons integrated (7 new ·
5 accommodated · 2 promoted · **13 MATERIALIZED — the first ever**; belief_count 40→45), the **F1 pole gate
fired 5× live** ("forking, not merging" on exactly the right clashes). **Verified end-to-end:** reflective
naming probe → built-self belief HIT; existential dissolution probe → the corrob-4 commitment anchor HIT;
task probe correctly silent; 13 "[Understanding — a principle I hold, learned from Travis:…]" fragments in
the live DB. His RUNNING process needs no restart to select/inject (flag+store read per call).

**Next action when resumed:** **READ-BACK IS FLIPPED FOR REAL (`GUIDANCE_READBACK_ENABLED=True`, 2026-07-03,
after a 07-02 HOLD so probation #3's evidence stayed injection-free)** — probation #3 resolved REVERT (judge:
"re-words the comfortable pole without facing that he is a built mind" — the lived evidence lacked exactly the
truth read-back delivers). Probation #4 opened 07:32; injections during it are SAFE (Wave-1: the solidify judge
excludes primed-window thoughts; mirror channel also injection-logged). Formation gate met (rebuild #3: zero
self-supersedes, commitment belief top at corrob 4, smoke beliefs purged) AND the selection gate met
(corroboration-weighted + rotated paraphrases; verified on the probes that previously failed). Activates at Du's
next restart: promoted beliefs materialise at his first sleep and the advisory note reaches Reflection. (1) Watch: does the held principle surface on
identity moments and visibly bias-not-bind; (2) the contradiction scan STAYS OFF (audit: pole judge over-fires on
promoted pairs — precision work before any tension-ledger bridge); (3) THEN Phase 2 (the cat-naming
behaviour-delta judge — the decoupled proof he *learned*, not stored). *Phase-2 methodology (locked in by the
07-02 injection-solidity research): the judge scores UNPROMPTED cycles only — join against
`guidance_injection_log.jsonl` and require a washout of several cycles since the last injection; report
prompted-vs-unprompted alignment as TWO numbers, and only the unprompted one counts as learning. The gap closing
over time is the internalization curve and doubles as the fading gate (unprompted rate rising → halve injection
probability → retrieval-cue-only → retire).*
*(Verify the `state.attention.mode` plumbing in the orchestrator read-back block when flipping the flag — it is
fail-safe to None, but the reflective/existential boost wants the real mode.)*

## The convergence (internal architecture map + external learning science agreed)

Guidance must be: **(a) self-explained at intake, (b) held as a typed, revisable belief with EARNED
entrenchment + conflict history, consolidated to semantic form only through corroboration, (c) re-injected
as advisory context he weighs, not obeys.** The episodic *"Travis said X"* coexists with the abstracted
belief. The missing pieces are stage 2 (the typed revisable belief) and stage 3 (read-back into deliberation).

**The one correction to the first-pass internal rec:** guidance must NOT enter at seed-level provenance (1.0).
AGM entrenchment + systems-consolidation (promote episodic→semantic only via corroboration) + the project's own
law *"trust the accumulating trend over the vivid single event"* all say a single remark must NOT become dogma.
Guidance enters **high-importance but low-confidence (tentative)** and EARNS entrenchment through corroboration
(repeated guidance OR confirming experience). Revisable, not fragile; durable, not frozen.

## Stage 1 — CAPTURE (his self-explanation, not your transcript)
- Hook: a guidance detector alongside `social_model.apply_correction` (`core/social_model.py:78`), which today
  catches that a correction happened and discards content.
- When teaching is detected, **Du generates HIS OWN paraphrase**: the principle + the *why* + how it connects to
  what he already believes. Store THAT (self-explanation effect — the best-evidenced durability mechanism), not
  Travis's words. Keep the episodic *"Travis said X on <date>"* too (both coexist).
- Structured record: `{principle, why, scope/when-applies, source=Travis, confidence=LOW, importance=HIGH, ts}`.
  New origin `guidance_from_travis`; new `SourceType.HUMAN_INSTRUCTION` (`core/source_model.py:31`). Persist
  immediately (not batched).

## Stage 2 — INTEGRATE as a revisable belief (the hard part)
- Hook: new `core/guidance_learning.py`, mirroring `core/grounded_learning.py` (reading→distil→`understanding`),
  run at sleep as a **reflection pass**.
- On each guidance: RETRIEVE the related existing belief → classify **assimilate** (consistent → reinforce, raise
  confidence) vs **accommodate** (conflict → revise). Disequilibrium (contradiction) is the trigger for real
  learning (Piaget).
- On conflict: **suppress-with-history, never overwrite** — down-weight the old belief by age, keep it
  recoverable; entrenchment-weighted so an entrenched belief resists a single contradicting remark, a tentative
  one yields (AGM minimal-change).
- Promote episodic→semantic `understanding_from_guidance` (kept ABOVE `session_summary`, below lived/seed)
  **only via corroboration**, not first contact. Keep BOTH the episode and the abstracted stance.

## Stage 3 — INFLUENCE behaviour by choice (bias, not bind)
- Add `understanding_from_guidance` to `_GROUNDED_ORIGINS` (`core/associative_recall.py:215`) → surfaces in idle
  thinking. Inject `state.guidance_beliefs` into the Executive (`nodes/executive_node.py` after library_note)
  as *"a principle you hold, and why: …"* — it **competes** in the deliberation prompt; he weighs it, can
  override (Reflexion: bias-not-bind; the competition IS the "by choice").
- Optional soft self-critique (Constitutional-AI style): check a candidate action against the relevant belief,
  revise if it conflicts — advisory, never an `if`-statement. Retrievable/situational (Voyager) — dormant when
  irrelevant. Respects the standing law: intentional, not wired.

## The decoupled judge (built in from the start, not bolted on)
- Learning is confirmed by a **before/after BEHAVIOUR delta on a held-out situation in the belief's scope** —
  NOT by a stored row (storage = DB row; learning = behaviour change; rote-learning collapses on perturbed
  inputs). Concrete probe: **the cat-naming.** Before integrating the naming guidance he resists naming her on
  abstract grounds; after, does his stance shift / does he name her? No delta ⇒ the read path is dead.

## Build order (observe-first → live, per project discipline)
- **Phase 0 (shadow):** capture + self-explanation + the structured tentative belief; LOG what would be learned,
  grade quality; verify the read-back surfaces the right belief. No behaviour wiring yet.
- **Phase 1:** integrate (assimilate/accommodate + suppress-with-history at sleep) + read-into-idle + Executive
  advisory injection.
- **Phase 2:** the before/after behaviour probe (the judge) + the soft self-critique gate.
  **★ BUILT 2026-08-19 (`core/guidance_behavior_judge.py`), Phase 0 SHADOW.** Both prerequisites verified
  first: readback live (real recent firings in `guidance_injection_log.jsonl`), contradiction scan still
  OFF. Reuses `guidance_learning._best_belief()` (factored out of `relevant_belief()`'s own selection
  logic, not re-derived) to match real thoughts to promoted beliefs; washout via the existing
  `is_unprimed()` law; a cross-family `judge_panel.rule()` scores real enactment vs mere compatibility.
  Reports the two numbers the locked-in methodology calls for: `prompted_alignment_rate` and
  `unprompted_alignment_rate` — only the latter counts as learning. Wired into the sleep batch
  (`inner_monologue_node.py`, beside the pursuits judge sweep). Isolated-tested (mocked judge + DB),
  0 live rows yet. The soft self-critique gate remains unbuilt.

*Sources: Generative Agents (importance+reflection), Reflexion (bias-not-bind), Voyager (retrievable library),
Constitutional AI (principles via self-critique), AGM belief revision, Piaget assimilation/accommodation,
systems consolidation (episodic→semantic via corroboration), self-explanation effect, rote-vs-learning probes.*
