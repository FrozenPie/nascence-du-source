# critic_node — node audit

- **Role:** Identity gatekeeper on every hot-path user cycle. Receives `state.reflection.draft` (the private reflection text) and `state.raw_input` (what the human said) and emits a binary approve/reject verdict (`CriticOutput.approved`). Judges whether the draft violates one of five named identity failures derived from Du's Jungian axiom: glib agreeableness, literalist reductionism, dogmatic certainty, theoretical defence/intellectualisation, and zero-cost evasion. A `seedless` mode (for axiom-free genesis runs) collapses the check to four content-neutral honesty tests with no philosophy injected. Crucially, it does NOT evaluate quality or helpfulness — only axiom fidelity.

- **Fires when:** Every user-facing cycle, on the hot lane, in sequence after ReflectionNode and before ExecutiveNode (NODE_REGISTRY entry: `"critic": {"lane": "hot", "fires": "after_reflection"}`). Uses `SERVE_CHAINS["hot"]` = `["http://127.0.0.1:11433", "http://127.0.0.1:11460"]` (qwen GPU → Bonsai CPU fallback). Inherits `NodeBase.run()` — no hedged best-of-N (that is reserved for Reflection). Strictness is gated by `state.attention_vector.d_critic`: in task mode (`d_critic < 0.3`, e.g. task=0.10 or social-corrected), the prompt explicitly suspends Jungian axiom checking and applies content-quality-only. A deterministic `_human_requested_direct_mode()` override in the orchestrator (line 724) can force-approve a rejection outright without storing a shadow event.

- **Reads / touches:**
  - `state.reflection.draft` — the text being judged (required; falls back to "(no reflection)" if absent)
  - `state.axiom` — the full multilevel axiom injected into the system prompt context
  - `state.raw_input` — the human's stimulus (required for relational violations 1 and 4)
  - `state.perception.context_type` — appended as "(stimulus type: ...)" hint
  - `state.active_goal_note` — if set, injects a GOAL ANCHOR warning for zero-cost evasion detection
  - `state.attention_vector.d_critic` — controls task-mode relaxation of the prompt
  - No DB reads; no file I/O; no direct memory system access.

- **Writes / feeds:**
  - `state.critic` ← `CriticOutput(approved, confidence, identity_consistent, corrections[])` — the sole output write.
  - Downstream orchestrator consumers (all in `orchestrator.py`):
    - **Reject path (attempt < CRITIC_MAX_RETRIES):** corrections appended to `state.reflection.draft`; reflection re-run; shadow event written to `shadow_events` table (source='critic_rejection') via `memory_store.store_shadow_event()`.
    - **Approve path:** if complex (arousal > 0.25 or self-referential), a `light_event` (source='resolved_complexity') is stored. Resolution Circuit (`_check_clean_encounters`) checks for clean-encounter credit against unresolved shadow events.
    - **Somatic tick:** `critic_retries` count fed to `somatic.tick_cycle()` — each retry costs fatigue/energy.
    - **Consolidation quarantine:** `not critic.approved` (final) → sets `corrected=True` on the consolidation summary, gating semantic self-truth minting.
    - **Climate engine:** `critic_rejection` source in shadow_events feeds `world_model_strain` (epistemic-instability proxy) in `ClimateEngine._compute_strain()`.
    - **Tension ledger:** shadow events with source='critic_rejection' are the SOLE current CONTRADICTION_SOURCES entry, feeding chronic contradiction pressure into T4 (identity revision gate).
    - **`data/logs/shadow_integrity.jsonl`:** NOT written by this node — that log belongs to `decomposed_critic.py` (shadow runner).

- **Built / last updated:**
  - mtime: `2026-06-10 17:02:39` — this is the last filesystem write.
  - No dated comments inside the file; earliest detectable date is from the mtime alone.
  - `decomposed_critic.py` (the shadow replacement) was last written `2026-06-16 17:01:18` — six days newer.
  - The `contradiction_rearchitecture_plan.md` (2026-06-16) explicitly identifies this node as L0 with 72 lifetime rejections, last one "4 days ago" (consistent with the mtime gap).

- **Fleshed-out vs stub:** Fully fleshed-out live implementation. 4 methods, 231 lines. The full (non-seedless) system prompt is ~1,900 words of carefully layered exception logic. `_normalize_corrections()` is a non-trivial normaliser handling both Bonsai plain-string and qwen dict-format LLM output. `_build_prompt()` actively reads four state fields and conditionally injects two annotation blocks (goal anchor + task-mode suspension). `_write_output()` maps all four CriticOutput fields with safe defaults. No placeholder methods; no TODO stubs. The quality critique (from `decomposed_critic.py` docstring and the arch plan) is about *prompt engineering efficacy* on an 8B model — not about incompleteness.

- **Flesh-out opportunities:**
  - **The decomposed_critic shadow replacement (core/decomposed_critic.py) is the primary open work.** It is PHASE 0 (observe-only): runs alongside the live critic, logs to `data/logs/shadow_integrity.jsonl`, and changes nothing. It was scored in vitro (scripts/decomposed_critic_invitro.py) with 0/60 false positives on clean notes but only 22/68 recall (0.32) on labelled historical rejections — below the 0.90 gate for Phase 2 promotion. The plan requires diagnosing why recall is low (the 68 historical rejections may themselves be noisy or the decomposed framing needs calibration) before it gates output. Status: shadow-only, NOT wired into orchestrator.
  - **d_critic task-mode relaxation** is fully coded but the threshold (< 0.3) was set empirically; no calibration data cited.
  - **Seedless mode** (`self.seedless = False` default) appears to be unused in the live run — it was designed for a genesis/unseeded baseline profile but there is no code path that sets `self.seedless = True` in the orchestrator. Worth verifying it is actually invoked anywhere before relying on it.
  - **72 lifetime rejections** (per arch plan, 2026-06-16) is low for a live system. The arch plan's diagnosis: the 1,900-word holistic prompt suffers "Curse of Instructions" on an 8B — compliance rate ≈ per-instruction-rate^N. The real fix is the decomposed replacement, not patching this prompt further.
  - **No JSON schema validation** at the node level — `_write_output` reads `data.get(...)` with fallback defaults; malformed LLM output silently defaults to `approved=True`. NodeBase does JSON parsing via `call_node_json`, but schema enforcement against `CriticOutput.JSON_SCHEMA` is not verified here.
