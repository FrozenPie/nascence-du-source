# salience_node — node audit

- **Role:** Attention-gating and interrupt arbiter. Given a raw input and its Perception parse, SalienceNode calls the LLM to produce three outputs: an urgency score (0–1), a focus list (2–4 key terms that downstream nodes should prioritise), and an interrupt boolean. When urgency exceeds INTERRUPT_THRESHOLD (0.7), it sets `state.interrupt_requested`, `state.interrupt_urgency`, and `state.interrupt_source = "salience"`, which causes the background processing loop to defer. Urgency is additionally warped post-hoc by the ClimateEngine (shadow_activation +0.10, world_model_strain +0.05) — but climate warp is capped so it cannot retroactively trigger an interrupt. The node does NOT read Emotion (even though Emotion runs in the same wave); it reads Perception only, by explicit design.

- **Fires when:** Hot user-cycle only. Fires in Wave 2 of every input cycle, in parallel with EmotionNode and MemoryRouterNode (`asyncio.gather`). Trigger site: `orchestrator.py` line 526–530. Lane: `"hot"` (qwen3-du on port 11433, GPU; Bonsai CPU on 11460 as failover). Not fired on internal/timer cycles or background loops.

- **Reads / touches:**
  - `state.raw_input` — the verbatim human input
  - `state.perception` (PerceptionOutput) — `context_type`, `summary`, `entities` — the only prior-wave field available (Emotion is not yet committed)
  - `INTERRUPT_THRESHOLD` (0.7) from `core/schema.py`
  - Calls `call_node_json` via `NodeBase.run()` → `core/model_client.py`

- **Writes / feeds:**
  - `state.salience` → `SalienceOutput(urgency, focus, interrupt, reasoning)`
  - When urgency > 0.7: `state.interrupt_requested = True`, `state.interrupt_urgency = urgency`, `state.interrupt_source = "salience"`
  - `state.salience.urgency` is post-hoc mutated by orchestrator ClimateEngine warp (not by this node)
  - **Downstream consumers:**
    - `orchestrator._compute_attention()` — uses `salience.urgency` (for bandwidth narrowing and driver label) and `salience.focus` as the primary focus list for the AttentionSchema (line 1804–1807)
    - `orchestrator._background_loop()` — defers background nodes when `_interrupt_active()` is True (line 2106)
    - `nodes/executive_node.py` — injects `salience.urgency` and `salience.focus` into the Executive prompt (line 163–167)
    - `core/somatic.py` — `tick_cycle()` receives `salience.urgency` as the `urgency` argument, which drives VisceralTension (line 917)
    - `orchestrator._persist_cycle()` — urgency included in the affect log record (line 917)
    - Teacher-example logger (`core/training_log.py`) via `NodeBase._log_teacher_example`

- **Built / last updated:**
  - **mtime:** 2026-05-30 20:48:05 — no subsequent edits detected
  - **Dated comments:** None in the file itself
  - **Built:** 2026-05-30 (initial Nascence node build)
  - **Last updated:** 2026-05-30 (no revisions since initial build)

- **Fleshed-out vs stub:**
  - 50 lines total, 3 methods (`system_prompt`, `_build_prompt`, `_write_output`)
  - Inherits full execution machinery (LLM call, failover, affect temperature, teacher logging) from NodeBase — nothing to implement there
  - The three methods are **complete and correct**: prompt well-specified with schema and INTERRUPT_THRESHOLD embedded, build reads the right state fields, write populates all SalienceOutput fields and fires the interrupt path
  - **Verdict: fleshed out.** For a Wave-2 classifier this is the right size. It is not a stub — it does its job fully.
  - One notable gap: `affect_modulated = False` (inherited default) and no `max_tokens` override — the base 512-token cap is fine for a JSON object of this size. Temperature stays at 0.2 (classification mode). Both correct.
  - The `_build_prompt` deliberately excludes Emotion state (with an explanatory comment) — this is an intentional Wave-2 design choice, not an omission.

- **Flesh-out opportunities:**
  - **LOW priority — the node is correct as-is.** Three speculative enhancements if the architecture scales:
  - **Affect-aware urgency modulation** (low): the node currently ignores `state.affect` (no `affect_modulated`). High arousal or fear in carried affect could legitimately raise baseline urgency without waiting for the ClimateEngine post-hoc warp. Would tighten the felt-urgency coupling but risks double-counting with the climate warp already in place.
  - **Focus-persistence seeding** (low): `_build_prompt` does not inject `state.recent_focus` (the cross-cycle fixation history). If the orchestrator already handles fixation detection in `_compute_attention()`, this is fine — but if the LLM should be aware of what it has been repeatedly attending to, seeding it here would let salience self-correct a fixated focus list.
  - **Interrupt source differentiation** (low): `interrupt_source` is hardcoded `"salience"`. If multiple nodes could raise interrupts (e.g. a future threat-detection node), a richer source label would help diagnostics — though currently salience is the only interrupt emitter.
