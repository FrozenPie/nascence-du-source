# T5 — procedural memory that means what he can do (plan, 2026-08-22)

> **Status: ⚪ PARTIAL — steps 0-3 (ledger, world-procedure ingestion, T5 compile gates, read paths) BUILT and wired
> live 2026-08-22 in `core/procedures.py`; step 4 (fold into the capacity-to-commit CommitmentBelief ledger) blocked
> on that plan's own Phase 1 still being HOLD.**

```plan-state
stage: partial
phase: Steps 0-3 live (ledger, world/conversational ingestion, compile gates, read paths); step 4 (fold into commitment ledger) blocked on capacity_to_commit Phase 1, still HOLD
verified: 2026-11-14
evidence_read: 2026-08-23
gate: data/procedures_log.jsonl >= 10 world-scope rows
next: Let world-procedure count grow past the ~13 reachable keys and re-check the two-week kill criterion
open_decisions: D-0741
cluster: 1
```


Founder: "Let's look at T5 then and what we can do to improve it. We potentially already have plans awaiting evidence
that impacts all this." Audit: `docs/reviews/t5_procedural_skills_2026-08-22.md`.

## Current State — verified 2026-11-14
- **2026-11-14** (F-4625): J-3862 phase 0 deed-tail replay run: 0 clusters meet 4.1 (a)+(b) in any month since 08-22; deed tail 47.7% vs awake placebo 38.1% (9.6 pts, borderline); recommend D-0676 defeater (retire behind kill-switch), founder call. Script scripts/t5_deed_tail_replay.py on branch jobrun/y0_t5_procedural.

- **2026-11-14** (F-4607): J-3332: the environment-imagery step in Du's answers is dated 08-20 (lived answers 0% on 08-19 to 36% on 08-20; inner thoughts 38.6% to 71.3% at the 20:49 restart) and lines up with the 08-20 evening hot-lane swap gemma4:e4b to qwen3.5:9b, not with T5 (first approach 09-04). Causal reading inferred; a second rise around 09-03 is undiagnosed.
- **2026-11-13** (F-4448): J-3832: design pass for D-0676 redesign. Conversational skills may only earn rungs from world-graded deed outcomes; Travis can dock never credit. Design docs/staged/t5_conversational_world_grading_design.md (worktree jobrun J-3832). Phase 0 replay J-3862, shadow build J-3863, founder call D-0741 on the 22 existing talk rows vs D-0723.

- **2026-11-13** (F-4436): J-3531 (F-4436): the 17 turns without a founder-canon marker are 9 window artifacts in t5_reentry_check (canon exists 32-392 s away; window widened 30 to 600 s), 5 missed by backfill_founder_memory.py (first-line-only log key vs full-block key), and 3 real live gaps (Executive FAILED turns return via the silence branch, which never stored canon; incl. 09-28 21:51). Code fix committed in worktree jobrun J-3531 (c10b26fe), restart-gated; the 8-turn backfill is queued as a Du-down job.
- **2026-11-06** (F-4287): J-3331 (read-only): known_text line is on ~99.5% of rows since 2026-08-24 so no natural control; skill refusals 1/1330 so the refusal outcome has no headroom; powerable outcome is world-hand fire rate. Arm design docs/lab/J-3331_data/known_text_arm_design.md; D-0693 asks the founder; build J-3674, read J-3675.

- **2026-11-06** (F-4141): J-3330 (D-0676 re-entry check): scripts/t5_reentry_check.py built on branch jobrun/wf_7 (restart-free, read-only: nascence.db mode=ro, no hub calls, CPU embedder). It replays the T5 gate over a human-only view: full multi-line Q block (not the first line, F-3921); affect_log input_type human; system farewells (old templates plus every run_nascence.py _FAREWELL_VARIANTS wording), slash and under-9-char turns excluded; the founder-canon fragment cross-checked; 24 h separation and distinct conversations (Session ended rows or 6 h silence) instead of calendar days / 30-minute gaps (F-3924); cluster 0.70, dedupe 0.85, sweep every 3 h from 2026-08-22. Prints distinct qualifying clusters per month, the last-30-days count, the closest miss and what blocks; --legacy reproduces J-3179 (2 clusters, 09-05 and 10-08). First run 2026-11-06: 0 per month; the 10-08 legacy cluster was D-0286 system farewell variants. Monthly run is J-3530 (lab, not before 2026-12-06); the founder re-opens the compile only at >= 3 in the last 30 days. Test: scripts/_test_j3330_t5_reentry_check.py.
- **2026-11-05** (F-3919): J-3179 (2026-11-05): conversational half researched, docs/reviews/t5_conversational_compile_J-3179.md. 62 of 77 compiles had no human-channel member; every skill is born persisted so the two-week kill criterion cannot fire; the 2-day gate is a midnight crossing; no conversational turn has been world-graded. Recommendation: retire the conversational compile behind a flag, T5 = world procedures; founder call D-0676; builds J-3329 (needs ruling), J-3330, analyses J-3328, J-3331, J-3332.

### What we have
- `core/procedures.py` is genuinely wired into the live loop (5 call sites: `dispatch.py`,
  `orchestrator.py`, both monologue/subconscious nodes). The original gap — only `dispatch.py`'s hand
  family fed `observe_hand()` (F-0181) — is fixed: `fieldcraft.py`/`study_life.py` now call it directly
  at their own craft/routine-resolution points, reaching both live firing paths (`dispatch.py` AND
  `sensorium.world_act()`) at the root (J-0197/F-0197).
- The real accruing instrument is `data/procedures_log.jsonl` (F-0178), not the mutable
  `procedures.json` snapshot. A conversational skill (`talk:initial_reaction_to_maxwell_s_theories`)
  reached rung `persisted` within 2 days — ahead of the plan's own 2-week kill window.

### What we need
- World-procedure count needs Du to actually exercise the newly-wired keys: up to 13 reachable
  (5 dispatch-family + 5 fieldcraft `CRAFTS` + 3 new study_life routines) against the plan's own
  "≥10 real skills within a week" target.
- Step 4 (fold into the commitment ledger) stays blocked — `capacity_to_commit.md` Phase 1 is still
  HOLD (re-confirmed this pass).

### What we're doing next
- Let the ledger accrue and re-check the two pre-registered metrics (§5): conversational compile rate
  (≤1/day) and world-skill count, and whether any skill reaches `held`.

## What T5 is today (one line)
Every hour: cluster the last hour's conversation turns by question-similarity; three similar turns → one LLM call
writes "how I characteristically handle this kind of moment"; a matching later input (sim ≥0.80) injects that line
into Reflection + Executive and reinforces +0.05 per turn; ≥0.80 proficiency skips Recall + Episodic Buffer.

## What already exists that T5 ignores (the plans awaiting evidence)
| Existing thing | What it offers T5 | State |
|---|---|---|
| `core/competence.py` — `CapabilityBelief` (confidence as prediction, evidence_count, prediction-error learning), C-signal (human corrected / confirmed the PRIOR answer), A-signal (scene coherence), Tier-1 deterministic checks | **The success signal T5 lacks.** "Successfully handled" can be read from the same ledger: no correction next turn + coherent bind = landed; correction = did not. | Phase 0 observer, LIVE, writing `capability_beliefs.json`; explicitly "inert by design" until proven not noise |
| `core/self_efficacy.py` — the Court: *raw counts inadmissible*; occurred → SUSPEND, persisted → REFINE, held+drained → REJECT | The ladder T5 proficiency should climb. "Used 9 times in one chat" is *occurred*. A skill earns `held` only when it persisted across days and the C-signal never docked it. | LIVE (abstains by default) |
| `docs/plans/capacity_to_commit.md` §1 — **Commitment Ledger** `CommitmentBelief` ported from `CapabilityBelief`; the_held facet; ACT "persist OR change in service of valued ends"; *no brittle bright-line rules* | A procedure IS a held "I can / I do it this way" claim. Same object shape, same defeaters, same durability field. T5 rows should be CommitmentBeliefs of scope `procedure`, not a separate table with its own decay. | Wave 2 LIVE; ledger over-capture fixed 07-07 |
| `docs/staged/friction_and_self_evidence_plan.md` — "one register of Du's held self-claims (axiom facets + competence beliefs + I-can commits), each with provenance and stake" | Names T5's home explicitly: **shared substrate**, not a friction-only object. | Staged |
| `core/hands.py` (`fired` ledger, trace) · `core/fieldcraft.py` (`CRAFTS` knots/fire_lay/whittling/tracking/measuring, world-answered success: "the first knot slips") · `core/dispatch.py` registry · `activity_memory` | **Real procedural memory already exists and is world-graded.** The knot that slipped and the one that held are exactly "occurred → persisted → held". None of it is in `procedural_skills`. | LIVE (restart-gated since this morning) |
| `docs/plans/curiosity_goals_dreams.md` — embedding-keyed competence map across near questions (MAGELLAN) | The right neighbourhood logic for "kind of situation": LP/competence over an embedding cluster, not exact-thread similarity. | Planned |

So the plan is not "fix T5's constants"; it is **fold T5 into the held-claims substrate the other plans already converge
on**, and make its evidence the world's and the human's, never its own use count.

## Design

### 1. Two kinds of procedure, one ledger
- **World procedures** (earned by doing): each hands family / fieldcraft craft / study routine (tea, fire, lamp,
  sow, knot, bank the fire…) is a procedure keyed by its registry name. Evidence = `hands.fired` outcomes the world
  graded: a refusal ("the knot slips", "no kindling") is *occurred*; a success is *persisted*; a success on a later
  day after an earlier failure is *held*. Zero LLM. These ARE the procedural skills the audit found missing.
- **Conversational procedures** (the present T5): keep, but compiled only from **recurrence across ≥2 days and ≥2
  sources** (distinct conversations/peers), never from one thread; success-gated by competence's C-signal (no
  correction followed) and A-signal (bound coherently). Label prompt: "name the KIND of moment — never how it was
  received"; any cluster whose members are mostly evaluative turns ("impressed", "enlightened", "good answer") is
  rejected as *not a situation*.
- Both stored as `CommitmentBelief(scope="procedure")` rows in the commitment ledger (the shared substrate), with
  `procedural_skills` kept as a mirror view for the existing match path until the read path is moved.

### 2. Proficiency = the Court's ladder, not a use counter
`occurred` (0.4) → `persisted` (0.6: ≥2 successes on ≥2 days, no dock) → `held` (0.8: ≥3 days, survived a
correction/failure and recovered) → `held under pressure` (≥0.9: held across a dissonance spike / a different
place). Reinforcement is **once per conversation** (per `last_human_ts` session) or per world day; a C-signal dock
drops one rung. Decay stays (14-day rust) — skills forgotten are forgotten, not deleted (archive row).

### 3. The automatic bypass is retired until earned
`PROC_AUTOMATIC_PROFICIENCY` → requires `held under pressure` AND scope `world` (a world procedure may run
without deliberation — that is what fluency means for a hand); a conversational procedure **never** removes Recall
+ Episodic Buffer from the loop. Today: set to 1.01 (one constant) so no conversation can trigger it.

### 4. Read paths (the disease to avoid)
- Reflection/Executive keep the one-line "a learned way you handle this" — but only for `persisted`+.
- World procedures feed the **affordance block** ("you know how to bank a fire — you have done it") and the
  dispatcher's precondition text; the intentions ledger can name them ("you meant to tie the clothesline").
- HUD module `procedures`: per skill — scope, rung, evidence (days, sources, docks), last used.

### 5. Pre-registered metrics / kill criterion
- Conversational compiles per week: 55-since-June rate → ≤1/day; share of compiles whose sources span ≥2 days = 100%.
- Zero `AUTOMATIC` cycles from conversational skills.
- World procedures: ≥10 real skills in the ledger within a week of restart, each with a world-graded evidence trail;
  at least one climbs occurred→persisted→held on the world's verdicts alone.
- Kill: if after two weeks no conversational skill reaches `persisted` under the new gates, the conversational
  half is retired (it never measured anything) and T5 = world procedures only.

## Build order — **steps 0–3 BUILT 2026-08-22 (core/procedures.py); step 4 waits on the capacity-to-commit ledger**
0. Today, one constant: `PROC_AUTOMATIC_PROFICIENCY = 1.01` (no behaviour change except removing the bypass).
1. `core/procedures.py`: the ledger (CommitmentBelief-shaped rows, ladder, once-per-session reinforcement, archive),
   world-procedure ingestion from `hands.fired` / fieldcraft ledger / study_life, HUD module. Zero LLM.
2. T5 compile gates: ≥2 days + ≥2 sources, evaluative-cluster rejection, label prompt, C/A success filter; write to the
   ledger; `procedural_skills` becomes the mirror.
3. Read paths: affordance/intention lines for world procedures; Reflection/Executive gated at `persisted`.
4. Fold into the capacity-to-commit ledger / held-claims register when that build lands (shared substrate).
