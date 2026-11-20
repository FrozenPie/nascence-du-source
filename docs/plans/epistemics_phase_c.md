# PLAN — Epistemics Phase C, reopened (2026-08-23)

> **Status: 🟡 C0 Path 1 BUILT, shadow/restart-gated, unverified live (J-1343, 2026-09-25).** Code
> exists in `core/competence.py` + the `orchestrator.py` startup wiring; verified via isolated unit
> tests only (temp-pathed store, mocked witness call, real local embedding scoring) — Du has not been
> restarted since, so it has never run a single real cycle. C1 and Path 2 (proactive sampling) remain
> design-only, per the doc's own sequencing.

```plan-state
stage: shadow
phase: C0 Path 1 contradiction-triggered BUILT and wired into start_background, restart-gated, zero live cycles yet; C1 and Path 2 remain design-only
verified: 2026-11-07
evidence_read: 2026-09-25
gate: data/accuracy_observations.jsonl source=tier3_model >= 50 rows
next: Once Du restarts: let C0 Path 1 accrue real accuracy_observations.jsonl rows (source tier3_model), then re-run bootstrap_report.py; Path 2 stays gated on measuring real 3070 VRAM headroom
cluster: 2
```


> **History folded** — 1 dated Current State section(s) (2026-09-24 … 2026-09-24) moved to `docs/plan_history/epistemics_phase_c.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py epistemics_phase_c`.

## Current State — verified 2026-11-07

- **2026-11-07** (F-4344): UNFIRED (J-3469, F-4344): the bridge from shadow-event and competence sources into the provenance ledger was never crossed: source_model.source_of_event and verification_of_competence_source (core/source_model.py:138,143) have zero callers, so no code reads source tier3_model. D-0532 keeps the Tier-3 probe gathering. Wire-or-retire is D-0700.
- **2026-10-30** (F-3314): Causal debt read J-2533: scripts/causal_debt_read.py; only 405 of 934 standing conclusions walkable, all leaves are shadow events, median grounded share 0.0, top ungrounded leaf under 183 insights; test unrunnable (1 retraction); sibling of F-3248 d07

### What we have
- C0 Path 1 (contradiction-triggered Tier-3 witness probe) BUILT in `core/competence.py`, wired into
  `orchestrator.start_background()` (J-1343, 2026-09-25) — restart-gated, verified only via isolated
  unit tests (27/27 checks), never run against live Du.
- Uses a dedicated `command-r7b` endpoint (`:11441`), deliberately bypassing the shared failover
  chain to stay non-circular with the model being witnessed.

### What we need
- A real Du restart before this code executes even once; no `accuracy_observations.jsonl` rows with
  `source=tier3_model` exist yet on the live store.
- C1 (calibration consumption) and Path 2 (proactive sampling) remain fully design-only, gated on
  resolving the 3070's real VRAM headroom (measured at 96.6% used pre-build).

### What we're doing next
- Once Du restarts: let C0 Path 1 accrue real rows, then re-run `bootstrap_report.py` (current
  baseline: n=12, stability does NOT predict accuracy) with the new tier3_model evidence folded in.

Parent design: `docs/archive/epistemics_plan.md` (consolidated 2026-06-07). This document proposes
how to build Tier 3 — which the parent plan designed but never implemented — now that the
constraint that shaped it (one GPU) has changed.

## Why this is being reopened, not just resumed

The parent plan names exactly one decision left to humans: *"How much Tier 3 (external witness)
are we willing to pay for?"* It was answered conservatively — **"minimum, async-probe only"** —
for two named reasons: broader use would be *"a synchronous, latency-heavy, API-dependent
bottleneck"* on the one 1080 Ti the hot lane also needs.

Both reasons weaken now:
- **Latency** — Tier 3 was already designed to fire async, during sleep. Ramses capacity that
  isn't the hot lane's own GPU costs nothing the design wasn't already paying for.
- **API-dependence** — Ramses's hubs are local LAN calls (`nascence_cpu_server.py`), not paid
  external APIs. That cost evaporates.

And there's real data now, not just freed-up reasoning to act on. Phase B (stability engine) has
been running: **303 stability observations**. But the bootstrap circuit — the parent plan's own
*"headline metric of the whole program"* — has only **27 accuracy observations, 12 paired**
(joined by cycle_id). Ran it (2026-08-23):

```
paired (both, by cycle): 12
correct − incorrect stability: -0.049
pearson(stability, accuracy) : -0.476
VERDICT: stability does NOT predict accuracy — systematic confident error dominates
```

**Read carefully — n=12 is too small to trust alone.** This is a signal to watch, not a
conclusion. But it's trending toward the exact case the parent plan built Tier 3 to catch:
stability failing as an accuracy proxy. If it holds up, Tier 2 alone cannot be trusted to gate
anything — which makes building Tier 3 more urgent, not just cheaper.

> **[Section removed 2026-08-31]** A fabricated benchmark claim (confidence=verified, citing scripts/modules that do not exist) was quarantined from here per F-0593/D-0105 — see `docs/lab/fabricated_benchmark_claims_2026-08-25.md`.

---

The parent plan's phase table doesn't mark Phase C as built — because it isn't. **There is no
Tier 3 code today.** This draft is not "widen an existing trigger" — it's the first build. That
matters for sequencing: since the constraint that would have argued for "build it narrow, widen
later" no longer fully applies, this proposes building it born-wide (both trigger paths from day
one) rather than the two-step the original scarcity would have forced.

## Two sub-phases, keeping the parent plan's own observe-before-connect discipline

### C0 — Tier 3 itself, shadow/observe-only (build this first)

Two trigger paths into one probe function, both writing to the SAME accuracy pipeline that
already exists and needs no changes:

**Path 1 — contradiction-triggered (the parent plan's original design).** When a Tier-4
correction/confirmation lands (`observe_cycle`'s existing C-signal block, `core/competence.py:551`)
and it *disagrees* with what Tier 2 stability implied — i.e. stability was high but the user just
corrected it, or stability was low but the user just confirmed it — queue a Tier-3 probe on that
cycle's original question. Rare by construction (needs a live human correction to fire at all).

**Path 2 — proactive sampling (new, the actual reopening).** A small, deliberately modest rate of
ordinary knowledge-domain cycles get sampled for a Tier-3 check regardless of any contradiction —
mirroring exactly how Tier 2 already self-enqueues from `observe_cycle` (`core/competence.py:598-603`,
`enqueue_stability`). This is what actually grows the bootstrap corpus past n=12 without waiting
on rare user corrections. Start conservative — e.g. 1-in-N knowledge cycles, tuned once real
volume is visible, not guessed upfront.

**The probe itself:** cross-model only for v1 (not web search — more moving parts, its own
question for later). Send the same question `command-r7b` (Ramses, `:11441`) as an independent
witness — genuinely distinct lineage (Cohere) from whatever generated the original answer, which
is what makes this non-circular per the parent plan's own law (*"the thing being measured cannot
be allowed to grade itself"*). Score its independent verdict against the original claim; treat
agreement as accuracy evidence toward 1.0, disagreement toward 0.0 — the exact same shape Tier 4
already uses.

**Logging — no new schema.** Call the existing `_record_external_accuracy(domain, measured,
source="tier3_model", cycle_id, question)` (`core/competence.py:613`) — it already accepts a
`source` tag (`"tier1_eval"`, `"tier4_user"` today) and already writes to
`data/accuracy_observations.jsonl` in the shape `bootstrap_report.py` already parses. Nothing
downstream needs to change to start accumulating real paired data faster.

*(Source tag corrected 2026-08-23, found by the day-investigation-audit workflow: this originally
said `source="tier3_witness"`, but `core/source_model.py`'s pre-existing
`_COMPETENCE_SOURCE_TO_VERIFICATION` mapping — built in an earlier design pass, not referenced
anywhere else in this doc — only recognizes the literal string `"tier3_model"` for
`Verification.EXTERNAL_WITNESS` classification. Had C0 shipped with the original tag, its logged
observations would have silently fallen through unclassified instead of registering as external-
witness evidence. Fixed here before any code exists to inherit the bug.)*

**Background loop shape — mirror `run_stability_loop` exactly** (`core/competence.py:652`): a
bounded queue (`self._tier3_queue`, same pattern as `_stability_queue`), an idle-gated asyncio
loop with the same heartbeat-logging discipline (queue depth / idle window / interrupt / skip
reason every tick — this is what let Phase B's health be legible from the HUD without guessing).

**Stays observe-only.** C0 feeds no behaviour — no confidence capping, no abstention, no
world_model_strain. Its only job is to make the bootstrap corpus real (aim for something like
50-100 paired examples before trusting a re-run — not a hard gate, just "enough to stop being
n=12") and then **re-run `bootstrap_report.py` and get an honest answer.**

### C1 — calibration consumption (only after C0 has real data)

Everything the parent plan describes for Phase C proper — cap confidence where accuracy is
unknown, low stability triggers abstain/hedge, an accuracy-surprise spike feeds
`world_model_strain`, layer-contradictions feed T4 — gets designed against what C0's re-run
actually shows, not against the n=12 hint. If the stability↔accuracy correlation stays negative
or near-zero with real data, the consuming logic should weight direct Tier-3 accuracy evidence
over the stability axis, which is exactly the *"safely measured, nothing downstream contaminated"*
outcome the parent plan built this whole bootstrap circuit to produce if things went this way.

## The gate before any of this goes live — not a formality

Antigravity's own benchmark today found the 3070 **already at 96.6% VRAM (7918/8192 MiB)** —
ollama has `phi3:mini` *and* `deepseek-r1:7b` both resident there, more occupied than assumed.
`command-r7b` passed its own verification call, so it works in isolation — but Path 2 (proactive
sampling) would make it a *regular* consumer, not an occasional test, and that's exactly the kind
of load the VRAM contention question (already flagged in `NASCENCE_NOTES.md`) needs answered
before it's real. Recommended sequencing:
1. Build C0's code, Path 1 only (contradiction-triggered) — rare enough that it's very unlikely to
   meaningfully contend with Lane 2, safe to enable close to immediately.
2. Resolve the 3070 headroom question for real (concurrent `deepseek-r1:7b` + `command-r7b` load,
   measured, not assumed) before turning Path 2 (proactive sampling) on.
3. Once both paths are live and producing real data, re-run the bootstrap and decide C1 from there.

## Open questions this draft doesn't resolve (flagging, not deciding)

- The exact proactive sampling rate for Path 2 — needs real volume data to tune, not a guess.
- Whether `command-r7b`'s Q4_K_M quantization (as actually pulled) materially changes its
  reliability as a witness versus what "Cohere command-r7b" abstractly promises — worth a small
  spot-check once it's live, same discipline as everything else this project has learned the hard
  way not to assume.
- Whether Path 1's contradiction detection (stability high + correction, or stability low +
  confirmation) needs its own threshold tuning, or can reuse `_STABILITY_*` constants as-is.
