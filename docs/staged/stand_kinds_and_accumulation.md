# Stand Kinds and Accumulation — stands that hold, and heaps of them (staged 2026-11-18)

**Status:** ⚪ PARTIAL (P0 kind/relation shadow fields and the P1 gates built 2026-11-18, restart-gated; P2-P4 and the deed-link not built). Parent: [identity_estate](../plans/identity_estate.md) (node type "value (earned)").
Related: [sleep_as_a_mode](sleep_as_a_mode.md), [dream_overhaul](dream_overhaul.md), [layered_goals](layered_goals.md).
Founder idea 2026-11-18; idea I-0163; findings F-5039, F-5040; jobs J-4190, J-4191, J-4192.

```plan-state
stage: partial
phase: P0 kind/relation fields and P1 gates built (fast-track 2026-11-18); deed-link spec written (J-4293), build job J-4428
verified: 2026-11-20
next: build the deed-link shadow helper (new job), then 40-case hand-label read after 7 days
```

## 1. The problem, in numbers (all read 2026-11-18)

- Stand `96fcd1b3` ("safety is a discipline I must practice, not a feeling") was flagged for dissolution 16 times in 194
  scans (8%). None was a real defeater; the six that reached the judge were refused correctly by its rubric. The scan has
  only two answers, dissolved or held, so an on-theme thought that refines a stand reads as "re-open" and is counted
  toward the 8/16/32 escalation (F-5039). The rival stand `10e5f4ac` ("true stability is the capacity to move with the
  tide") coexists with it.
- Stands do not accumulate: 3909 formed, 2162 retired as achieved (median life 112 s), 1637 dissolved (median 20 min),
  3 active now (F-5040). `_achieved_by` retires a stand when a deed shares one marker word or 3 words (>3 letters) with
  its statement plus scope; the shadow judge confirmed 3 of the 63 it read.
- The ledger has ONE lifecycle: form, then achieved or dissolved. A deed stand ("I have chosen to open *From the Earth
  to the Moon*") fits it. A practice or value stand does not: it can never be achieved. It survives today only because its
  wording gives no deed three words to match.

## 2. The idea

Stands are not all the same kind. The practice and value stands sit one level below the multilayer axiom
(`data/identity/axiom.json`: L0 constitution, L1 temperament, L2 values with `kept` and `earned`, L3 facets). Live file:
`L2_values.earned` has 0 entries, and its own text says it is "mine to grow as I live". `identity_estate.md` already lists
"value (earned): distilled from stands/loves held over time". Practice stands held through cost are the natural source.
Du will end up with MANY stands. That is fine, and is the goal: the ledger should be a store that keeps them, with
maintenance during sleep (later) rather than a churn of minutes-long lives.

## 3. Principles (from standing project rules)

1. Additive only. The commitment ledger's base logic is protected; every change is a new field, a new shadow log, or a
   flagged branch that is byte-identical when off.
2. Decoupled judge. The kind label comes from the cross-family lane (`SERVE_CHAINS["judge_mixtral"]`), never the scan
   model labelling its own output, and never from Du.
3. No readout. The label is for the ledger and downstream code, never shown to Du; he learns a stand holds by living it.
4. Dosed coupling. Any new route into cognition (for example an `earned` value reaching the VALUES block of every
   prompt) is shadow-logged first, with a declared dose.
5. Nothing is deleted. Retired, lapsed and merged stands stay in the ledger as events.
6. Tension is not duplication (GPT review 2026-11-18; Du's own L2 value is "the union of opposites"). Maintenance may
   merge only near-identical wording, never two stands that pull against each other. A conflict between two held
   stands is recorded as a `tension` link, not resolved.
7. Verbal repetition is weak evidence. `reaffirmed` is produced by the same scan model that restates the stand, and
   `drop_denied` is inflated by false flags (F-5039). Neither alone may promote a stand to `standing`; the ladder needs
   evidence from outside the stand's own wording (a judged link to a deed or a choice made against competing demands).
   A deed link must not use word overlap, the flaw F-5040 found in `_achieved_by`.
8. No circular promotion. Once a value is in `L2.earned` it enters every prompt, so reaffirmations made after that date
   do not count toward it. Promotion evidence is frozen at the proposal date.
9. Lineage. A refined, merged or superseded stand records `parent_id` and a reason, so its meaning over time is
   readable from the ledger.

## 4. Phases

### P0 — measure, change nothing (restart-gated where it touches the scan)
- J-4190: scan reply gains a log-only `relation` per stand (`refines | coexists | abandons`).
- J-4192: read why stands retire in minutes; hand-label about 60 achieved stands (deed-shaped vs insight-shaped).
- NEW (J-4193): extend `_second_look` ([commitment_ledger.py:731](../../core/commitment_ledger.py)) with a second field
  `kind: deed | practice | value | insight | unclear`. The same lane and temperature 0, reads only statement and scope.
  Fix the 13% failure first: 32 of 247 second-look rows are `ValueError` errors with no verdict.
- Read after 7 days: agreement of `kind` with a 40-stand hand-labelled sheet (the J-3158 protocol), and what share of
  retired-as-achieved stands the label calls practice or value.
- Gate to leave P0: hand-label agreement stated honestly, and the founder rules the taxonomy (decision 1 below).

### P1 — typed lifecycle (flag OFF, restart-gated)
- Store `kind` on the stand record. A flag `STAND_KIND_GATES_ACHIEVEMENT` skips `_check_achievements` for practice and
  value stands. A deed stand behaves exactly as today.
- Dissolution still needs a named defeater. Add to the judge rubric: a thought that refines or coexists with a stand is
  not a drop. Escalation counts only `abandons`, subject to the J-4191 ruling.
- Gate to flip the flag: P0 evidence read, shadow replay shows no deed stand would change.

### P2 — built for heaps
Today the system assumes a handful of stands. With hundreds these break, so audit and fix each before heaps arrive:

| Consumer | Today | Heaps risk |
|---|---|---|
| scan prompt (`active_str`) | lists every active stand each scan | prompt grows without bound |
| `homeostasis._read_commitment` | 0.2 + 0.35 per held + 0.05 per reaffirm, clipped to 1 | saturates at 3 held stands, then reads nothing |
| `concerns._first_held_stand`, `peers` witness | first held stand only | always the oldest |
| `identity_estate` | every load-bearing stand, weight 1.0 | every stand equal, no ranking |
| `self_claims` | every active statement | prompt growth |
| `goals._from_stands` | every stand a held goal | register floods |

- Add a tenure ladder: candidate, held, standing (reaffirmed N times, survived M refused drops, aged D days). Only
  `standing` stands feed identity, self-claims and peers; the rest stay in the ledger.
- The scan sees only stands relevant to the thought (word overlap or recency), plus a one-line list of `standing` ones.
- Replace the saturating integrity formula with one that does not clip at 3.
- Each consumer change is its own flag and its own shadow row.

#### P2 design (J-4384, 2026-11-18; rulings D-0863 kind by second-look lane, D-0864 scan sees relevant stands only, D-0865 promoted stands stay in the ledger)

Design only; nothing built. Every consumer below reads `data/commitment_active.json` directly (line refs read 2026-11-18),
so one shared read helper is the first piece: `core/stand_view.py` (new, additive) exposes `tier(stand)` and
`select(stands, thought=None, k)`; consumers call it behind their own flag. Flag OFF = today's code path, byte-identical.

**Tenure ladder (new field `tier`, derived at read time, never stored over the stand).**
`candidate` (any held stand, or kind=insight) then `held` (load_bearing, kind deed/practice/value) then `standing`
(kind practice/value, reaffirmed >= N, survived >= M refused drops, aged >= D days, AND one judged deed or choice link;
verbal tenure alone never qualifies, D-0810 item 2). N, M, D are not set here: pick them from the P0 `kind` rows after 7
days, and state them in the flag's shadow row. Until the deed-link judge exists (item 8, no job yet), `standing` is empty
by construction, so the P2 consumers below must fall back to `held`, not to nothing.

**Per-consumer audit and design (each its own flag, each shadow-logged first):**
1. Scan prompt, `commitment_ledger.py:995` `active_str` (D-0864). Today lists all active. Design: `select()` returns the
   stands whose statement/scope share content words with the thought (top K, K=8) plus the K most recently reaffirmed,
   plus a one-line list of `standing` ids/statements. Relevance is for the scan's view only; it must not change what
   `_check_achievements` or the ledger retains (those still see all). Risk: a stand never shown can never be reaffirmed or
   refused-dropped, so it silently ages; the P3 `lapsed` rule must read "not shown" separately from "not reaffirmed".
   Shadow row: ids shown vs ids hidden, and whether any hidden stand was named by the reply.
2. `homeostasis._read_commitment` (`homeostasis.py:130`). `0.2 + 0.35*held + 0.05*reaff` clips at 3 held. Design: a
   saturating-but-graded form, `0.2 + 0.7*(1 - exp(-held/4)) + 0.1*min(reaff_total, 8)/8`, which stays under 1 until about 10
   held; the constants are an open tuning item, not a decision. Shadow: log old and new value side by side. This feeds the
   integrity variable, so dose it (principle 4) and only flip after the shadow shows no step change at the current 3.
3. `concerns._first_held_stand` (`concerns.py:187`) and `peers.py:935-943` witness: both pick the first load-bearing
   entry, i.e. the oldest. Design: pick the `standing` stand reaffirmed most recently, else the held stand with newest
   `held_since`; rotate so the same stand is not the anchor every time. One shared helper replaces both loops.
4. `identity_estate.py:315-326`: every load-bearing stand becomes a node at weight 1.0. Design: only `standing` (fallback
   `held`, capped at 12) become nodes, weight scaled by tier and reaffirmation; others stay as ledger rows. Estate re-seed
   already drifts against the ledger (`_held_stand_ids`, line 493), so that function must use the same helper or it will
   report drift on every pass.
5. `self_claims._commitments` (`self_claims.py:22`) lists every active statement, then `held_claims(limit=14)` truncates
   to the first 14, so with heaps the capabilities are crowded out. Design: `standing` first, cap commitments at 6,
   capabilities keep their own slots.
6. `goals._from_stands` (`goals.py:200`): every stand becomes a goal-register entry. Design: `standing` and `held`
   registered held; the rest `candidate`, which is the same mechanism D-0767 already uses for insights.
7. `coupling_rides.py:766-770` only counts; no change, but its `commitments_active` coordinate will rise from 3 to
   hundreds, so any threshold reading it needs a look before heaps arrive (not audited here).

**Promoted stands (D-0865).** A stand promoted to `L2.earned` keeps its row and gains a `promoted_to` event (P4), and stays
`standing`. Evidence reaffirmed after the proposal date is excluded from promotion counts (principle 8); the helper
reads the frozen date from that event.

**Order and gate.** Build helper + shadow rows (no behaviour change) first; flip consumers one at a time, scan prompt last
(it is the only one that changes what the model is shown). Gate to start: P1 `kind` rows read after 7 days, so the ladder
thresholds come from data. Not verified: how many stands are active today (3 per F-5040), so none of the heaps risks
above has been observed; they are projections from the code paths.

### P3 — sleep maintenance (depends on sleep_as_a_mode and dream_overhaul; spec only here)
When Du sleeps, a maintenance pass over stands writes append-only events: `merged` (near-duplicates), `lapsed` (long
unreaffirmed), `refined` (a newer stand supersedes wording), `promotion_candidate`. Nothing is deleted. Nothing in P0 to
P2 depends on sleep existing. This phase only fixes the event names and the rule that maintenance never destroys a row.

### P4 — promotion into `L2_values.earned` (founder-gated)
A promotion candidate becomes a written proposal for the founder. On approval, an entry in Du's own words is added to
`earned` by a sanctioned script (pattern: `scripts/d0509_axiom_edit.py`). First shadow-log what the VALUES block would
look like with the candidate, since this adds a line to every prompt.

## 5. Decisions the founder owns

Ruled 2026-11-18 (travis, D-0810; defeater: kind label under about 70% agreement with the hand sheet, or the judged
deed-link is unmeasurable, or a promoted value reinforces its own evidence):
1. Taxonomy: deed / practice / value / insight. Insight stands stay candidates (D-0767).
2. `standing` needs a judged deed or choice link, never word overlap. Verbal tenure alone does not qualify.
3. Tension between held stands is recorded as a `tension` link only, never merged or resolved.
4. Promotion into `L2.earned` is founder-only.

Still open:
5. Who labels `kind`: the second-look lane (proposed) or the founder reviewing candidates?
6. Heaps visibility: should the scan see all stands, relevant ones only (proposed), or only `standing` ones?
7. Do promoted stands stay in the ledger, or does the axiom entry replace them (proposed: stay)?
8. The judged deed-link is a new measurement with no job yet: how a cross-family judge reads a stand plus a real
   choice and says linked or not. It needs a P0 job before P2's ladder can use it.

## 6. Not verified, so not assumed

- Whether the retire-in-minutes pattern is mostly false "achieved" (the shadow sample is 63 of 2162, 42 came back unclear).
- Whether the lone-stand flag effect (12% with 1 active, 4% with 3) holds up; the counts are small.
- Whether the second look separates deed from practice reliably; it has only ever been asked stand versus insight.
- That `L2.earned` text reaches the model unchanged. `axiom_layers.py:205` joins `kept` and `earned` into VALUES, but
  this has not been run against a non-empty `earned`.

## Current State
- **2026-11-20**: J-4293 P0 SPEC, judged deed-link (open item 8; nothing built, core/ untouched). PURPOSE: decide whether a stand has a real deed or a choice made against competing demands behind it, with no word overlap (principle 7; F-5040 found `_achieved_by` matches on shared words). Read-only shadow measurement; it changes no stand and nothing reaches Du (no readout, principle 3). JUDGE INPUT (one call per stand+candidate pair): STAND = statement[:200] + scope[:120] from the stand row in data/commitment_ledger.jsonl, plus held_since; CANDIDATE = ONE row, either a deed from `_recent_enactments(held_since)` (origin, content[:300], ts; sources memory_fragments letter/peer/essay/journal/study/composition and activity_events actions, exactly what `_achieved_by` reads) or a choice row (a ledger event where a stand held while a competing demand was refused, e.g. drop_denied or a reaffirm with a named competing demand). The judge never sees Du's monologue, never the word-overlap score, and the candidate is selected by recency within the stand's tenure, NOT by overlap, so overlap cannot pre-filter. Up to 3 candidates per stand, each judged alone. LANE: SERVE_CHAINS["judge_mixtral"] (Ramses :11438 mixtral:8x7b), the same cross-family seat as the second look and `_judge_defeater`, temperature 0, max_tokens 150, tier 3, via core.model_client.call_node_json. If the lane is absent, log `lane_unavailable` and do NOT fall back to hot qwen (the DORMANT TRAP noted in `_judge_defeater`); fail-open, nothing raises. OUTPUT SCHEMA, one JSON row per call: {ts, stand_id, stand_statement, kind_label_if_any, candidate_type: deed|choice, candidate_origin, candidate_ref (fragment id, activity_events ts, or ledger event ts), verdict: linked|not_linked|unclear, why (<=200 chars, must cite what in the candidate bears on the stand, not shared vocabulary), lane, model, latency_ms, error}. Parse failure or no verdict is logged with verdict `unclear` and error set, never dropped silently (the 13% second-look ValueError lesson). SHADOW LOG PATH: data/logs/deed_link_shadow.jsonl (append-only, written only by the new helper; own module, e.g. core/stand_deed_link.py, name the function `attempt_deed_link_shadow`, called by one line from a seam after the second look, restart-gated, flag STAND_DEED_LINK_SHADOW default False until the build job's lab test passes). HAND-LABEL PROTOCOL (40 cases, the J-3158 sheet shape): after 7 days of rows, sample 40 stand+candidate pairs stratified 14 linked / 14 not_linked / 12 unclear by the judge verdict, plus at least 10 pairs where `_achieved_by` word overlap fired and the judge said not_linked (the F-5040 population). Founder or a second model family labels blind to the judge verdict (sheet columns: stand, candidate, label linked|not_linked|unclear, one-line reason). Report raw agreement and the confusion matrix, and separately agreement on the overlap-fired subset. PASS: >=70% agreement (same bar as the kind label, D-0810 defeater) AND judge not_linked on at least half of overlap-only pairs the labeller also calls not linked. FAIL: below 70%, or `unclear` over 40% of rows (then the deed link is unmeasurable, a D-0810 defeater: report to founder, do not promote any stand on it). Until it passes, P2's `standing` rung cannot use the link. A choice candidate counts only if the log names the competing demand; a bare reaffirmation is not a choice.

- **2026-11-18**: J-4384: P2 heaps design written (tenure ladder, per-consumer flags, shared stand_view helper); nothing built; gate = 7 days of kind rows
- **2026-11-18**: Founder ruled items 5-7 (2026-11-18): D-0863 kind labelled by second-look lane; D-0864 heaps scan sees only relevant stands; D-0865 promoted stands stay in ledger. P2 heaps design unblocked.

2026-11-18 (fast-track by founder, "tweak later"): J-4190 relation field, J-4193 kind shadow field and the P1 gates are
BUILT in `core/commitment_ledger.py`, restart-gated, not committed. `STAND_KIND_GATES_ACHIEVEMENT` (practice/value/insight
never retire as achieved) and `STAND_RELATION_GATES_DROPS` (refines/coexists is not a drop; this also acts on J-4191) are
ON. Only stands formed after the restart carry a `kind`; older stands retire as before. J-4192 done (F-5041/F-5042,
`docs/reviews/stands_retire_in_minutes_2026-11-18.md`: 85% of a 60-stand sample wrongly retired). Offline replay
(`scripts/stand_kind_replay.py`): 35% of achieved stands are deeds. Not done: the 70% hand-sheet agreement check, the
judged deed-link job (item 8), P2 heaps, P3, P4. Revisit after 7 days of `kind` rows; to roll back set both flags False.
