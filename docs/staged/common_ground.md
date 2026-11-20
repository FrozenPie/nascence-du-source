# Common Ground — the failed-to-object ledger (staged 2026-10-30)

**Status:** 🟡 SHADOW (built, flag OFF, restart-gated). Parent plan: [guidance_learning](../plans/guidance_learning.md).
Idea I-0101 (from thought T-0105; F-3218 item 2). Built by J-2523.

```plan-state
stage: shadow
phase: SHADOW flag off, restart-gated
verified: unknown
next: Flip COMMON_GROUND_SHADOW (restart-gated), then read the failed_to_object share once 7 exchanges accrue
```


## 1. What it is

A per-exchange record of the conversation's coordination state. For each human exchange (Travis's turn plus Du's
finalized Voice reply) it records each claim, who asserted it, and what the other party did with it, so that a claim
Du merely let pass stays distinguishable from one both parties accepted. Interlocutors are fallible: an un-objected
claim must not harden into shared ground. Not memory, not a readout: the live state of one exchange, read by nothing.

## 2. Statuses (one per claim)

| status | asserted by | rule (lexical_v1) |
|---|---|---|
| user_said | Travis | Du's reply did not take it up at all (no content overlap, no cue) |
| failed_to_object | Travis | Du's reply took it up (overlap >= 0.34 and >= 2 shared content tokens) with no assent and no objection cue |
| both_accepted | Travis | an explicit assent cue on it (or a turn-opening assent answering the last claim) |
| corrected | Travis | an explicit objection cue on it (or a turn-opening objection answering the last claim) |
| du_inferred | Du | a reply assertion that restates nothing in Travis's turn; Travis's next turn resolves it (resolves_prev) |

Reply sentences that restate a Travis claim are uptake evidence (echo), not new claims. Each claim also carries
taken_up, hedged, cue, overlap and revise_if (the revision condition). open_questions records who asked and whether
the reply took the question up; assumed_unverified lists failed_to_object and hedged claims.

## 3. Why deterministic, not the hot model

It runs on the human path right after Voice, where Travis is waiting; condensed_thought's one-call twin budget was set
for idle ticks. A lexical rule is reproducible (the read can hand-check every label against the rule that produced
it), costs nothing (every exchange, not a 0.25 sample), and can be replayed over history read-only
(replay() over data/founder_conversation_log.jsonl). Known weakness: lexical uptake misses paraphrase and reads a
poetic echo as uptake. If the read finds the share real but the labels noisy, a rate-gated LLM extractor is the
follow-up, not a retune of these thresholds (they are declared in the module header and fixed).

## 4. Code

- `core/common_ground_shadow.py`: flag COMMON_GROUND_SHADOW (False); observe_exchange() returns None, one append to
  data/common_ground_shadow.jsonl via core.shadow_log; replay() writes only to a caller-named file outside data/.
- `core/orchestrator.py`: hook in the human-output block (after the companion exchange signal), behind the flag,
  fail-open.
- `scripts/_test_common_ground_shadow_j2523.py`: hermetic (isolate(), write spy, live hash canaries, wiring, imports).

## 5. Coupling block (dosed_coupling §5)

- **Publishes:** one row per human exchange to data/common_ground_shadow.jsonl only (origin common_ground_shadow,
  witness_only true). Nothing on CognitiveState, no cargo, no bus, no prompt block.
- **Reads at:** the human-output stop only, from two strings already final there (raw_input and the Voice output);
  no new line, no new dose, no store read.
- **Surprise line:** none (observe-only). A later phase may treat a rising failed_to_object share as a surprise line
  for the conversation, but only after the read, and only by founder ruling.
- **Ride log:** every row carries {stop: human_exchange, line: common_ground, dose: row}.
- **No readout (D-0434):** no gauge, count or status from this ledger is ever rendered to Du.

## 6. Read gate

A 7-exchange read of the failed_to_object share once the shadow file holds 7 rows (job spawned by J-2523). Baseline
for comparison: the replay over 95 historical exchanges (2026-09-02..2026-10-20), F-finding cited in the plan-state
note. The flag must be set True (one line, restart-gated) before any row can accrue.

## 7. What this is NOT

Not a correction mechanism, not a sycophancy filter, not memory. It never changes what Du says or remembers.
