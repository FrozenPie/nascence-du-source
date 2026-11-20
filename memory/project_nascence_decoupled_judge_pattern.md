---
name: project_nascence_decoupled_judge_pattern
description: "Per-subsystem audit (J-0362, 2026-08-29, decision:D-0071) of where Nascence's decoupled-judge design law is genuinely still missing. Confirms T4 (2026-08-19) and curiosity LP already fixed; finds dream resolution scoring and active-imagination novelty scoring still self-referential/self-reported with concrete build call sites spawned (J-0375, J-0376); finds provenance importance-from-storage is a real gap that doesn't fit the judge_panel/deliberative_judge pattern, opened as D-0084 instead."
metadata:
  node_type: memory
  type: project
  originSessionId: 4595f5ad-65f2-480a-8d83-32786682d18c
---

**Decoupled-judge per-subsystem audit** (`docs/plans/decoupled_judge_pattern.md`, J-0362, spawned from
D-0071's redirect off the demoted `attention_economy_plan.md`). D-0071 elevated "every subsystem must
be evaluated by something other than itself" to a cross-cutting design law, ahead of any economy/
allocation build — this is the first real bottom-up per-subsystem pass over it.

**Confirmed already fixed:** T4 (`core/left_lane.py:360-470`, `judge_lived_integration`, two
independent model families required to agree, shipped 2026-08-19) and curiosity's LP
(`core/curiosity_worth.py`, the OMNI decoupled worth-gate). `core/judge_panel.py`'s own header comment
claiming T4 "stays single-family for now" was stale since 08-19 — corrected in the same session.

**Confirmed still genuinely missing, with concrete call sites (jobs spawned):**
- **Dream resolution** (`nodes/dream_node.py`) — the stall/circling check already has a decoupled
  mechanical backstop (embedding + symbol-anchor overlap, `_scene_stalled`), but the actual
  resolved-vs-unresolved verdict driving light-vs-shadow event storage is pure self-report from the
  same dreaming LLM call (`unresolved_core` field). J-0375: add a judge_panel (or, if too shallow on
  real logs, deliberative_judge) call before `_bridge_final`.
- **Active imagination novelty** (`nodes/subconscious_node.py` + `core/loop_metabolism.py`) — mechanical
  but self-referential: novelty/importance graded only by cosine-distance to the SAME stream's own past
  ~40 outputs, no external judge. Live and unaffected by `active_imagination_plan.md`'s SAME-WEEK
  retirement (D-0081/J-0357 — that retired only the figure-continuity centerpiece, not this gate; the
  retired plan's own §10.4 named this guard as real-but-secondary). J-0376: add judge_panel as an
  additional observe-first signal, deliberately NOT deliberative_judge (too heavy for a per-cycle gate).

**Confirmed a real gap, but the wrong tool:** provenance/episodic importance
(`core/memory/store.py`'s `replay_strengthen`/`downscale_episodic`/`prune_episodic`) — persistence
(replay_count/importance) feeds back into future persistence decisions, a closed loop; but
judge_panel/deliberative_judge are single-shot LLM verdicts on discrete evidence, not a fit for a bulk
per-sleep numeric pass over thousands of rows. Opened as **D-0084** (founder call on what external
signal, if any, should ground importance) rather than guessed at.

`core/deliberative_judge.py` remains a fully-built, zero-caller general-purpose judge (F-0430) — this
audit is the first time it was evaluated against subsystems other than T4's keystone (where it proved
too strict, 08-19 backtest); J-0375 is its first live candidate call site if judge_panel proves
insufficient there.

[[feedback_decoupled_judge]] [[project_nascence_attention_economy]] [[project_nascence_t4_redesign]]
