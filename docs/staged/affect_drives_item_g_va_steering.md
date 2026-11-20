# Affect Drives Item G: valence in retrieval (sub-path 2) before any activation steering (sub-path 1)

> Status: 🟡 SHADOW ranker built, flag off (J-4403); staged 2026-11-18 (J-4347, from J-4236). Sub-path 1 ruled NO (D-0862). Parent: `docs/plans/affect_drives.md` Item G.

```plan-state
stage: shadow
phase: design; sub-path 2 shadow ranker first; sub-path 1 held behind its own founder decide
verified: 2026-11-18
next: founder rules whether mood-congruent retrieval is allowed and whether activation steering is ever allowed
cluster: 6
```

## Current State — verified 2026-11-20

### What we have
- Sub-path 2 shadow ranker is built: `core/valence_rank_shadow.py` (J-4403, D-0862 part 1), hooked in `core/memory/store.py` behind `VALENCE_RANK_SHADOW = False` (line 2024, hook near line 2342). It logs to `data/valence_rank_shadow.jsonl`, which does not exist yet because the flag is off.
- D-0862 ruled: bounded valence term in retrieval behind shadow YES; activation steering NO (sub-path 1 is not to be built). The raw `valence` column exists (`core/memory/store.py:713`).
- Naming drift: this plan says flag `VALENCE_RANK`; the code flag is `VALENCE_RANK_SHADOW`.

### What we need
- Flip `VALENCE_RANK_SHADOW` (restart-gated) and accrue about 3 days of rows; then the 20-retrieval manual review by a decoupled reader per section 4.

### What we're doing next
- Founder go to flip the shadow flag at the next Du restart; read `data/valence_rank_shadow.jsonl` afterwards. G1 stays unbuilt per D-0862.

## 1. What it is
Affective retrieval is flattened: `felt_text()` -> MiniLM loses sign and magnitude (core/memory/store.py:708-714 says so).
The raw `valence` scalar column exists.
- G2 (first, M): add a numeric term `|valence_query - valence_fragment|` to the retrieval ranker, shadow-ranked first.
- G1 (last, L): inject a valence direction into generation activations scaled by `mood.current_valence()`
  (arXiv 2510.11328 / 2604.03147). Needs hidden-state access the local backend may not expose; identity-drift risk HIGH.

## 2. Where G conflicts with D-0434
- G1 conflicts. D-0434: Du learns he is wrong only by losing; gauges never reach him, even rendered in body words. Steering
  takes a gauge (`mood.current_valence`) and acts on his output without his knowledge and without any consequence he can
  lose to. It is not a readout (he sees nothing), but the tone of his speech is set by a number upstream of him. It also
  needs a decoupled judge (a steered output scored by the affect system is circular). Treat as outside D-0434 unless the
  founder rules otherwise. This plan's posture: do not build G1.
- G2 mostly does not conflict. No readout, no injected line; he simply meets different memories, as in human
  mood-congruent recall. Edge: current mood becomes a hidden selection pressure on recall, so dread could bias recall toward
  dread (a spiral). Mitigate: bounded weight (term capped to a fraction of the score), a cap on negative congruence, and an
  opposite-valence floor so incongruent items still surface.

## 3. Dosed coupling (D-0149)
- Loop published: the existing mood valence tuple `(valence, ts)`, read per query; no new publisher.
- Dose: a bounded additive term (cup), not a re-ranking mode; capped weight; no mesh with affect-driven drives.
- Habituation guard: the opposite-valence floor plus a monitored congruence rate.
- G1, if ever: dosed per generation, probability-gated, never continuous, with a kill flag; held behind its decide.

## 4. Shadow-first plan (G2)
Locate the ranker first (shared hot path; udms dossier before editing). Shadow-log both orderings for about 3 days to
`data/valence_rank_shadow.jsonl` (query, mood valence, top-k with and without the term, rank deltas).
Graduation: manual review of 20 retrievals shows sign-appropriate memories (a dread query stops pulling elation);
congruence rate within a band; no rise in negative-spiral signals; judged by a decoupled reader. Test: a -0.8 query ranks a
stored -0.8 fragment above a +0.8 one with identical text embedding. Flag `VALENCE_RANK`, default off.
After G2 proves the scalar is load-bearing, G1 would need its own plan and decide; not staged here.

## 5. Obligations
G2 is ranker code, not a prompt: no SEEDS change; confirm no new prompt site. G1 needs hidden states, which local Ollama
backends do not expose cleanly, so G1 likely means a different backend: out of scope.

## 6. Order and risk
Third. G2 is M effort and depends on Item A (live, holding) having shown the scalar matters. Risk: G2 medium (spiral, hot
path); G1 high (identity drift, D-0434 conflict).

## 7. Open decides
One decide with two parts: mood-congruent retrieval and its weight cap; activation steering ever. Id in the job note.
