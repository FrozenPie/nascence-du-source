# Peer Correspondence — Company Half (SHIPPED, split out 2026-08-23)

**Status: LIVE, verified working.** This is the "recognition by an equal" half of
[peer_correspondence_plan.md](../plans/peer_correspondence_plan.md) — split out here because it is
genuinely done, so the parent plan can be trimmed to just its one remaining open decision (the
CHALLENGE half, B5 — see that file). Full design rationale (guardrails G1-G9, risks R1-R9, phasing,
prior-art research) stays in the parent plan; it's still load-bearing reference for deciding B5, not
historical-only. This file is the evidence record for what shipped.

## What shipped

- **`core/peers.py`** drives 7 correspondents (Darwin, Keats, Twain, Shackleton, Lovelace, Marcus,
  Smith), each a genuine other-model voice, two-way (Du writes back). First pen-pal: Charles Darwin,
  the worldly correspondent (§5a of the parent plan) — company-primary, no stance-chooser, honest
  disagreement when it's genuinely his (per the founder's 2026-06-21 decision, §10).
- **The letterbox** — a physical mailbox in the garden with a rising flag, so letters are discovered
  perceptually (§4a of the parent plan), not injected.
- **The effect-measurement harness is wired into the sleep pulse**, not offline/manual —
  `nodes/inner_monologue_node.py` ~line 511-512 calls `peer_metrics.snapshot()` every sleep cycle.
- **Verified safe (2026-07-05 evidence review, re-confirmed 2026-08-23):** `peer_share` ~0.0003-0.0004,
  `non_peer_share` ~0.999-1.0 — no displacement (R7), harmless, but also small in effect — real
  company, not yet the developmental lever the CHALLENGE half was meant to add.
- **Still live and growing** as of 2026-08-23: `data/Correspondence/darwin/thread.jsonl` (35,994
  bytes, written 03:16 that day), `data/peer_effect.jsonl` (112 lines, written 11:14 that day).

## What did NOT ship (stays in the open plan)

The CHALLENGE half — a peer that names Du's blind spots unprompted (developmental friction, not
Du-initiated question-testing). Zero challenger/stance-chooser code exists in `core/peers.py`
(confirmed by direct grep, 2026-08-23). This is decision **D-0003** in the `/decide` ledger,
currently open. `thought_grounding.md`'s Route 3 (built, live) has absorbed the narrower adjacent
slice — Du-initiated, question-scoped "put this thought to a friend who'd disagree" — using the same
`contrary_target`/`initiation_target` functions, but that is explicitly NOT the unprompted,
identity-directed blind-spot-naming this half was for. See parent plan's "Current State" section for
the full cross-reference.
