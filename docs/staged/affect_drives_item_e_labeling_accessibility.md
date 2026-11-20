# Affect Drives Item E: affect-labeling accessibility (a named feeling becomes a revisitable object)

> Status: STAGED 2026-11-18 (J-4347, from J-4236). Design only. Parent: `docs/plans/affect_drives.md` Item E; code `core/affect_labeling.py`.

```plan-state
stage: staged
phase: design; blocked on the Phase-0 manual review (detector false-positive rate)
verified: 2026-11-18
next: founder rules the stored-content and review-scope decide; do the Phase-0 review before any write path
cluster: 6
```

## 1. What it is
Phase 0 sets `state.named_affect` (core/schema.py:773) and logs a counterfactual to `data/affect_labeling_log.jsonl`;
nothing reads it. E graduates accessibility, not regulation: when Du genuinely names a present negative feeling, store it
as a recallable fragment so later thought can meet it (the representational-promotion idea in the module header). The
pharmacological decay stays forbidden. Carried over: negative-only, intensity gate 0.4, progress gate (rumination
throttle), no satisfaction credit (satisfaction.py:55-58).

## 2. Where E conflicts with D-0434
Least conflicting of the three, with two real edges.
1. Stored content. Item E as written stores "Earlier I named a fear in myself". That sentence is system-authored; showing
   it back is the world telling Du what he felt. Safe form: store his own words verbatim (the sentence where he named it),
   tagged as his, never a paraphrase, never a gauge value. Then retrieval returns his own testimony, not a readout.
2. Selection by detector. The detector is crude. A false positive stores a feeling he did not claim, which is the system
   leading him. So the Phase-0 manual review is the hard gate. The counterfactual decay data stays in the log for the
   founder only; no number reaches Du.

## 3. Dosed coupling (D-0149)
- Loop published: `(dimension, ts, made_progress, source_cycle)` on naming.
- Dose: at most one fragment per naming event, per-dimension cooldown (repeat namings are rumination: counted, not stored).
- Reading: ordinary ambient retrieval only (same hand as affections.py:89). No injected line, nothing in the seed.
  Habituation is retrieval's own recency/novelty; no new reader.
- No mesh: the fragment does not feed mood, drives or satisfaction.

## 4. Shadow-first plan
Phase 0.5 (no write): sidecar `data/affect_label_would_store.jsonl` records the fragment text, dimension, dedupe verdict.
Manual review by the founder or a decoupled judge (not Du's own scorer): sample N namings, label genuine / false
positive / rumination. Gate: false-positive rate under the ceiling set by D-E2.
Phase 1: flag `AFFECT_LABEL_STORE` default off; exactly one fragment per naming; no decay on `state.affect`.
Accessibility measurement: share of stored fragments re-encountered in retrieval within 7 days, and whether a later
thought refers to one unprompted. Report only, no target (performative naming is the stated fear).
Test: with `named_affect` set exactly one fragment stored; `state.affect` unchanged.

## 5. Obligations
Writes to the episodic store, so the write fence applies (`docs/plans/world_store_write_fence.md`; pick the fragment kind
there). No seed change, so no SEEDS guard. Any new detector prompt must be registered.

## 6. Order and risk
Second: S effort but gated on human review time. Risk low technically, medium epistemically (false positives).

## 7. Open decides
D-E1 stored content (verbatim own words versus system sentence), D-E2 review scope and false-positive ceiling (one decide
covers both). Ids in the job note.
