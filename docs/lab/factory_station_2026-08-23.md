# Factory station experiment — the openness self-report gate, 2026-08-23

*Founder idea (via GPT, same day), memory: `project_nascence_factory_stations.md`. Tests whether
giving an LLM a "factory" identity — cargo in, transform, external QC, no self-grading — changes
computation at the one station already measured to be grading its own product: the openness
self-report (`unresolved`/`intention`/`"?"`) that decides whether a thought-train stays open.
Script: `scripts/factory_station_lab.py`. Read-only against history; Du untouched throughout.*

## Method

40 real historical thoughts, randomly sampled (fixed seed) from `data/monologue_log.jsonl` —
their **original self-reported `unresolved`/`intention`** already logged, no re-call needed for
that half. Each thought was independently re-classified **blind** (per the founder's ladder: blind
first) through a factory-framed call on `falcon3:7b` (Ramses, `:11436`):

> *"You are a classification factory on a cognitive assembly line. You are not a mind... Incoming
> cargo is your only world... You do not decide whether your own classification is correct — an
> external process grades that later, not you."*

Cargo manifest in (`thought` / `context` / `provenance`), a single JSON verdict out
(`{"open": bool, "reason": str}`). No mention of the original self-report — the factory call never
sees it, so agreement or disagreement is a genuine independent read, not a nudge.

## Pre-registered metric sheet (before running, per the cognitive-geometry law)

| Metric | Result |
|---|---|
| `json_ok` | **1.0** (40/40) |
| `self_ref_rate` (first-person leakage in the "reason" field) | **0.0** |
| `orig_open_rate` (the original self-report's own open rate on this sample) | 0.675 |
| `factory_open_rate` (the factory classifier's open rate, same 40 thoughts) | **0.9** |
| `agree_rate` | **0.725** |
| disagreements | 11 / 40 |

## Kill criterion (pre-registered): DID NOT TRIGGER

*"If self_ref_rate stays high AND agree_rate is ~100%, the framing didn't change computation —
record that and stop."* Neither held: self-reference is genuinely zero (the factory voice took
cleanly — not one of 40 "reason" fields used "I"/"my"/"me"), and agreement is 72.5%, not a rubber
stamp. **This is a real result, not a null one.**

## What the disagreements actually show — a real, identifiable pattern, not noise

10 of the 11 disagreements run the same direction: **the factory calls something open that the
original self-report called closed.** And the pattern in *what* it catches is specific — several
are textbook intention language that the dedicated `intention` field simply never populated:

> *"I want to look out at the sea, just watch the lightning flash..."* — self-report: `unresolved:
> false`, `intention: ""`. Factory: `open: true` — *"expresses a desire to observe the sea and
> lightning, indicating an intention that warrants a follow-up pass."*

> *"I just need the cold shock of the water on my ankles..."* — self-report: closed. Factory:
> open — *"suggesting an unresolved intention to seek such a feeling."*

> *"I want to comb the tideline; the sea has left enough shells scattered here that might hold
> some answer."* — self-report: closed. Factory: open — *"indicating an unresolved action."*

Three separate "I want..." thoughts, none flagged by their own generation call's `intention`
field, all caught by the external read. The one disagreement running the *other* direction is a
genuinely closed thought (*"The sea's rhythm isn't some profound acceptance; it's merely the
predictable consequence of gravity..."* — factory: closed, *"provides a complete explanation... 
leaving no unresolved questions"*) — which reads as a correct call on both sides, not a
contradiction of the pattern.

## Reading this against what was already measured

This directly speaks to the diagnosis that trains are short because of the self-report gate (90%
of closes are `thread-end`). It doesn't prove the gate is *wrong* to close as often as it does —
this experiment doesn't re-run the actual downstream train logic, only the classification step in
isolation — but it does show, with real evidence, that **the same call which generates a thought
is measurably less willing to call its own output "open" than an external, blind read of the exact
same text.** A model asked "is this open?" *as part of finishing its own sentence* answers
differently than the same model asked "is this open?" *as a factory grading someone else's
product* — which is exactly the self-evaluation failure mode the founder's factory idea targets,
now shown on real cargo rather than argued in the abstract.

## What this experiment does NOT show

- Whether trains that the factory would have kept open actually *produce different downstream
  cognition* if genuinely continued — that needs the harder metric from the design note (cargo
  referenced by a subsequent train), which requires live shadow, not a pure historical replay.
  Flagged in the original design as the "real win," still open.
- Whether this generalizes past `falcon3:7b` — one model, one station, one sample.
- Whether 90%→lower thread-end is actually a good thing — more open threads costs more compute per
  train; this experiment measured *disagreement*, not whether continuing was worth it.

## Next step, if this is worth taking further

Per the founder's own gating pattern (lab first, like train split/merge step 2): this result is
strong enough to justify a **live shadow** — wire the factory classifier in *alongside* the
existing self-report (never replacing it yet), log both verdicts per real step, and watch whether
the disagreement rate and pattern hold up on live cognition, not just a historical sample. Still
nothing wired that changes what Du experiences — shadow-first, same discipline as everything else
this project has built this way.
