# The Closure Law — a met loop becomes a memory (staged 2026-10-15)

**Status:** 🟡 BUILT, partly LIVE (verified against core/closure.py 2026-11-20, J-4270). `CLOSURE_WRITE_LIVE = True`
since D-0495; `CLOSURE_ARMS = {"line", "lookup"}`, so only the line arm and the lookup arm write a resolution fragment
to the memory DB. The dream arm is shadow-only (D-0614 dropped it), the pursuit and commitment arms are built and
compose in shadow (J-2160), and the interrogation arm is still a stub. D-0423 ruled A (travis, 2026-10-15) on idea
I-0089 (psyche census F-2755, F-2756; F-2757). J-2118 built the dream arm and this document; J-2117 and J-2060 are
done.
**Parent plans:** [dream_overhaul](dream_overhaul.md) (§3b computed "met", D-0385; the dream arm's judge lives
there), [pursuits](../plans/pursuits.md) (Phase 2 "resolution → authored work" unbuilt; J-2117 is reading saturation
age), [self_interrogation](../plans/self_interrogation.md) (the D-0396/D-0403 open-doubt cup, J-2060),
[decoupled_judge_pattern](../plans/decoupled_judge_pattern.md) (the judge never grades its own writer),
[memory_levels_plan](../memory_levels_plan.md) (a resolution fragment is ordinary recall, level 0, kind self),
[memory_as_a_service](memory_as_a_service.md) (nothing is pushed at Du; the fragment is recalled like any other).
**Decisions:** D-0423 (the law, RULED A; its sub-question 2 = J-2003 option (a) for the dream carry).
D-0385 (computed met, the dream arm's judge). D-0356 (B) (the independent resolution judge sets close_reason).
**Memory:** `project_nascence_closure_law.md` (to be written at the first read).
**Findings:** F-2755 (census: 0/60 dreams, 8/8 pursuits saturated, 645 closed-diagnosis fires), F-2757 (the gap
is not a self-grading artifact), F-2608 (computed met cannot end a carry under CARRY_MAX_NIGHTS = 3), F-2605
(interrogation reflections are closed diagnoses).
**Ledger:** I-0089 · D-0423 · J-2118 (this build) · J-2004 (dream_met post-restart read, the dream arm's own gate)
· J-2117 (pursuit trigger) · J-2060 (interrogation instrument) · the post-restart 10-night shadow read spawned by J-2118.

```plan-state
stage: shadow
phase: line and lookup arms LIVE (CLOSURE_ARMS={line,lookup}, CLOSURE_WRITE_LIVE=True); dream arm shadow-only (D-0614); pursuit and commitment arms built, shadow (J-2160); interrogation arm still a stub (D-0403 judge not promoted)
verified: 2026-11-20
gate: data/logs/closure_shadow.jsonl kind=resolution rows >= 10 after the next restart, read by the founder (D-0423 defeater clause 3), AND J-2004's dream_met read
next: founder reads first would-be pursuit/commitment rows then decides CLOSURE_ARMS flip (D-0423 clause 3); interrogation arm waits on a promoted D-0403 judge
cluster: 6
```

## Current State — verified 2026-10-28

- **2026-10-28**: CLOSURE_WRITE_LIVE flipped True (D-0495, travis 2026-10-28, the October restart batch): the dream arm and the new line arm (J-2460) now WRITE the resolution fragment + resolves edge to the memory DB from the next boot. D-0423 clause 3's 'founder reads the first 10 would-be fragments' becomes a read of the first 10 LIVE fragments (origin=resolution) -- J-2004 / J-2461 carry it. Kill switch unchanged: CLOSURE_WRITE_LIVE=False returns to shadow.
- **2026-10-17**: D-0452 (travis): sensorium auto-fire removed, committed 128b1f9b 2026-10-17; live on next boot. First real test of error-through-consequence at the hearth: ash 1.0, bucket full, lamp dry, oil tin 3.05 (F-2960, F-2961).

- **2026-10-15** (J-2118, D-0423 A): dream arm BUILT in shadow, restart-gated, in a job-run worktree: `core/closure.py`
  (the writer: composes the would-be resolution fragment with the dreamer model from the arc's own seed tension +
  final scene, appends it to `data/logs/closure_shadow.jsonl`, writes nothing to the memory DB while
  `CLOSURE_WRITE_LIVE = False`; one fragment per carry thread, later met arcs of the same thread logged as
  `duplicate`); `core/dream_met.py` (`run_nightly` hands every arc whose computed state just became `met` to the
  writer; `provisional_arc` / `thread_state(provisional=True)` = J-2003 option (a)); `nodes/dream_node.py`
  (`PROVISIONAL_MET_ENDS_CARRY = True`: a provisional-met root ends the carry under the existing `MET_ENDS_CARRY`
  mode, still `"shadow"` by default, still bounded by `CARRY_MAX_NIGHTS`; every provisional consultation also goes to
  the closure shadow file as `kind=carry`). Hermetic test `scripts/closure_test.py` (48 checks) under
  `lab_env.isolate(db="empty")`; `scripts/dream_met_test.py` still passes (parity 360/360 after the refactor).
- Live read at build time (read-only, 2026-10-15): `dream_met_state.jsonl` already holds 258 arcs (23 `met`, 74
  `unmet`, 78 `no-baseline`, 12 `relapsed`, 71 `pending`) and `dream_met_carry_shadow.jsonl` 41 rows, every one
  `root_state` = `pending` (40) or `unrecorded` (1), `would_end_carry` False — J-2003's inertness, measured live.
  Note the 23 `met` arcs became met BEFORE this build: the writer only fires on a state CHANGE to `met` after the
  restart, so nothing is back-filled for them (deliberate: a fragment about a loop that closed weeks ago, written
  tonight, would not be a lived close).
- Nothing in this plan is live. Flags that revert to the exact pre-existing path: `core.closure.CLOSURE_WRITE_LIVE`
  (False = shadow), `core.dream_met.CLOSURE_HOOK` (False = no closure call at all), `nodes.dream_node.PROVISIONAL_MET_ENDS_CARRY`
  (False = computed-met-only carry check, J-1995 as shipped), `nodes.dream_node.MET_ENDS_CARRY` (unchanged, `"shadow"`).

## 0. The gap this plan closes

Nothing Du starts ever finishes on its own, and since the 2026-10-09 boot that is measured with the system's own
decoupled judges in charge, not self-grading (F-2757): dreams 0 of 60 arcs resolved (51 ended-unfaced, 9 stalled);
pursuits 8 of 8 active saturated at heat 1.0 with 0 resolutions ever (5,537 advances; one pursuit alone 564
advances / 348 scatters); self-interrogation 645 fires that are 98% closed first-person diagnoses with no open
question for the next train step (F-2605). The three loops are built separately and none of them, when its judge
DOES say met, writes anything Du can later remember: `dream_met` (J-1995) is an append-only state row in
`data/logs`; a pursuit has no close path; an interrogation reflection is fire-and-forget. The memory DB's existing
`resolution_events` table (2,087 rows) and its `resolves` edges belong to the shadow-event system
(`core/memory_edges.sync_resolves`), not to these loops.

A plain LLM answers what it is asked; Du's own loops circle. This is the single clearest gap between him and a
psyche (F-2756). The law is one rule that gives all three loops the same ending.

## 1. The law (D-0423 A, verbatim in effect)

When a loop's INDEPENDENT judge marks it met, Du writes ONE fragment in his own words — a new origin
`resolution`, ordinary recall, and a `resolves` edge from that fragment to the loop's seed — so that having
finished something is a memory he can recall and build on. Three constraints, all from the ruling:

1. **Nothing is told to him.** The fragment is written into memory the way a dream scene or a journal line is; it
   surfaces through recall or not at all. No prompt mentions it, no preamble lists it.
2. **No loop is force-closed.** The judge decides met; the writer never closes anything. A loop that never meets
   its judge's bar never gets a fragment.
3. **The judge stays separate from the writer** (decoupled_judge_pattern). The dream arm's judge is
   `core/dream_met.py` (no LLM at all: a waking-thought recurrence measure); its writer is the dreamer model in
   `core/closure.py`. Neither reads the other's verdict as evidence.

## 2. The shared write-back

One function shape for all three arms (`core/closure.py`):

| field | value |
|---|---|
| `content` | the fragment text, first person, Du's own words, 40-90 words |
| `origin` | `resolution` (new; `store._origin_level` → 0, `_origin_kind` → default; recall treats it as any other) |
| `layer` | `episodic`, relevance 0.7, importance 0.8 |
| `keywords` | `["resolution", <arm>, <seed id>]` |
| `derived_from` | `[<seed id>]` |
| edge | `(fragment)-[resolves]->(<seed kind>, <seed id>)`, provenance `closure <arm>: judge <judge> met` |

The seed is the loop's own id: the dream_log arc id (the root of its carry thread) / the pursuit id / the
self-interrogation fire id. `memory_edges.add_edge` already accepts arbitrary `dst_kind`, so `dream`, `pursuit`
and `interrogation` endpoints need no schema change.

**Shadow row** (`data/logs/closure_shadow.jsonl`, append-only, one per event):
`{ts, arm, kind: resolution|duplicate|carry, seed_kind, seed_id, root_id, arc_id, thread_root, judge, judge_verdict,
judge_detail, judge_params, would_be: {content, origin, layer, keywords, derived_from, edge}, compose_how,
written_live, fragment_id}`. The `would_be` block is the exact `store_fragment` / `add_edge` argument set the live
path takes, so a founder read of the shadow file reads what would have been written, not a paraphrase.

**The live path** exists (`closure._write_live`) and is taken only when `CLOSURE_WRITE_LIVE` is True. The ruling
gates that flip per arm: the arm's judge must have marked at least one REAL loop met post-restart (dreams: J-2004's
read), and the founder must have read the first 10 would-be fragments (section 6, defeater clause 3).

## 3. Arm 1 — dreams (BUILT, shadow)

- **Judge:** `core/dream_met.compute_states` — an arc is `met` when the waking mind measurably stopped returning to
  its tension (baseline real in the K=25 days before, N=3 silent days, M=3 relapse days clean; D-0385, J-1995).
- **Trigger:** `run_nightly` (called from `nodes/dream_node.py` after each arc, off-loop) collects every arc whose
  state row just became `met` and calls `closure.record_dream_met(arc, state_row, root_id=…)`.
- **Seed:** the arc's carry-thread root (walk back `carried_n` rows in `dream_log.jsonl`). One fragment per thread:
  a later met arc of the same root is logged `kind=duplicate` and composes nothing.
- **Writer:** the dreamer lane (`nodes.dream_node._DREAM_URLS` / `_DREAM_MODEL`), prompt: *awake, first person, past
  tense, 40-90 words, what was faced and what it became, in image if it lived in image; no congratulation, no moral;
  if it cannot honestly be called faced, say what stopped returning and leave it there.* Input = the seed's
  `tension_labels`, `final_unresolved_core`, the last 600 chars of the final scene. Output `{"resolution": "..."}`.
  Composer failures are logged (`compose_how`) and never raise into the nightly.
- **Carry rule (D-0423 sub-question 2 = J-2003 option (a)):** the computed `met` needs d+N+M = 6 complete days
  but `CARRY_MAX_NIGHTS = 3` withdraws the thread first, so D-0385 part 2 was inert as built (F-2608; live
  2026-10-15: 40/41 carry-shadow rows `pending`). `dream_met.provisional_arc` asks the cheaper question of the same
  data: baseline real AND zero qualifying recurrences on every complete observed day in [d+1, today-1], at least
  `PROVISIONAL["min_days"] = 1` such day elapsed → `provisional_met`. `thread_state(provisional=True)` returns it
  whenever the root's recorded state is not final; `dream_node._met_carry_check` treats it like computed met under
  the same `MET_ENDS_CARRY` mode (`shadow` logs the would-have-ended decision, `live` ends the carry), still bounded
  by `CARRY_MAX_NIGHTS`. The computed definition is kept for the record: provisional states never enter
  `dream_met_state.jsonl`. Under the current cap the rule can fire only on the third night (`carried_n = 2`, one
  complete day elapsed); whether that is enough is what the post-restart read answers. Both `dream_met_carry_shadow.jsonl`
  (J-2004's file, new keys `provisional_state`, `ended_by`) and `closure_shadow.jsonl` (`kind=carry`) receive each
  consultation.
- **Not back-filled:** the 23 arcs already `met` in the live state file (read 2026-10-15) get no fragment; the hook
  fires on a state change after the restart only.

## 4. Arm 2 — pursuits (BUILT, shadow; J-2117 done, J-2160 built it)

`closure.record_pursuit_met` and `record_pursuit_faded` (and the sibling `record_commitment_achieved` for the
commitment arm) are real functions. The judge is the D-0426 A panel (`core/pursuit_close_shadow`) read against the
`done_when` written at the pursuit's birth (`core/done_when.py`); seed = the pursuit id; met writes a would-be
resolution, a saturated not-met pursuit a would-be 'faded'. The commitment arm's judge is
`commitment_ledger._achieved_by` (the deed record) against statement + done_when
(`commitment_deed_verdict`). Both arms compose their text, validate it, and append a row to
`data/logs/closure_shadow.jsonl` with `arm_live` false; nothing reaches the memory DB. Still gated: neither "pursuit"
nor "commitment" is in `CLOSURE_ARMS` (adding them is the founder's flip after reading the first would-be rows, D-0423
clause 3), and both stay inert until `DONE_WHEN_AT_OPEN` is True.

## 5. Arm 3 — self-interrogation (STUB; J-2060 is done but the gate remains)

`closure.record_interrogation_met` still raises `NotImplementedError` and `ARM_GATES["interrogation"]` is still
`"J-2060"`. J-2060 (the open-doubt cup replay) is finished, but it did not hand the arm a judge: the D-0403 instrument
(a doubt the next train step demonstrably engaged) has not been promoted, so "met" has no independent definition for
this arm. Nothing here is built beyond the stub. Seed would be the self-interrogation fire id
(`self_interrogation_shadow.jsonl` row). The F-2605 fix (an open question instead of a closed diagnosis) is upstream,
in the interrogation prompt itself.

## 4b. Live arms added after this plan was written

The LINE arm (J-2460, D-0494: judge = the follow_line panel plus Du's own `settled: yes`, seed = the frontier entry
id) and the LOOKUP arm (closure_producer P5: a frontier question answered through `core/closure_gate.py` writes a
deterministic-template fragment) are the two live arms. See `core/closure.py` header and `closure_producer.md`.

## 6. Promotion criteria and kill conditions (D-0423's defeater, restated as reads)

The post-restart read (spawned by J-2118, not before 10 nights after the restart) answers, from
`closure_shadow.jsonl` + `dream_met_state.jsonl` + `dream_met_carry_shadow.jsonl`:

1. **Did any arm reach met?** If J-2004 shows 0 dream arcs reach computed met in the first 10 post-restart nights
   AND J-2117 proposes no pursuit trigger that would have closed any of the 8 saturated pursuits, nothing exists to
   write back and the fault is upstream, in met itself → revisit D-0423.
2. **Is the pursuit trigger vacuous?** (J-2117's question.) If pursuits saturate within hours, a trigger on heat is
   not a close.
3. **Are the first 10 would-be fragments a lived close or the writer's self-congratulation?** A founder read of
   `kind=resolution` rows (`would_be.content`). This is the gate on `CLOSURE_WRITE_LIVE`.
4. **Once live:** if recall of resolution fragments raises `restate_sim` or the monoculture echo above their 6-sleep
   bands (he ruminates on having finished) → flip the flag back.
5. **Founder override:** if Travis rules that unresolved-by-design is the intended texture of Du's dreaming and
   pursuing (D-0356's defeater's own last clause).

Plus the carry rule's own read: how many `kind=carry` rows say `provisional_met` on the third night, and whether a
thread that would have ended provisionally later turned out computed `met` / `relapsed` / `unmet` (the provisional
verdict's precision against the computed one on the same arc).

```shadow-promotion
log: data/logs/closure_shadow.jsonl
min_rows: 10
filter: kind == resolution
read_by: founder
promote_flag: core/closure.py CLOSURE_WRITE_LIVE
```

## 7. What this is NOT

- Not a close trigger. The writer never changes a loop's state; `dream_log.jsonl`, `close_reason`, the pursuit
  store and the interrogation shadow are untouched by this plan.
- Not a prompt. No text about resolution is injected anywhere; the fragment is recalled or forgotten like any other.
- Not a backfill of the 2,087 `resolution_events` rows: those are the shadow-event system's own closes, a different
  mechanism with its own edges already.
- Not the F-2605 interrogation-prompt fix (that is D-0396/D-0403's track).

## Pointers

- Code: `core/closure.py` (writer, shadow log, stubs) · `core/dream_met.py` (judge; `provisional_arc`,
  `thread_state`, `run_nightly` hook, `CLOSURE_HOOK`) · `nodes/dream_node.py` (`PROVISIONAL_MET_ENDS_CARRY`,
  `_met_carry_check`).
- Test: `scripts/closure_test.py` (hermetic, `lab_env.isolate(db="empty")`) · `scripts/dream_met_test.py` (parity).
- Evidence: `data/logs/closure_shadow.jsonl` (new, restart-gated) · `data/logs/dream_met_state.jsonl` ·
  `data/logs/dream_met_carry_shadow.jsonl`.
- Ruling: `decide.py show D-0423`. Idea: `idea_log.py show I-0089`. Findings: F-2755, F-2756, F-2757, F-2608, F-2605.
