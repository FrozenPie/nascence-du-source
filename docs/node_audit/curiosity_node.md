# curiosity_node — node audit

- **Role:** Grows side-research themes and open questions off Du's recent study/reading material and unresolved inner tensions (subconscious_state.json). Each run produces up to 5 questions + 3 research_directions. When urgency > 0.6 it raises `interrupt_requested` on CognitiveState. It also performs external web research: if a pending frontier pursuit exists it calls `web_research.lookup_targeted` (then `scholar.consult_sync` as fallback) and attaches the finding to the frontier question; otherwise it grows a "grounding twig" off a recent study subject via `web_research.lookup`. New world-questions are posted to `frontier.note_question` for future pursuit. Observe-only records land in `data/curiosity_log.jsonl` and `data/twig_log.jsonl`.

- **Fires when:** (a) **Dissonance ignition** — `orchestrator._on_dissonance_ignition` calls `nodes["curiosity"].run(state)` when accumulated climate dissonance crosses the ignition threshold and no cycle is active; the first valid question then triggers `run_cycle(question, input_type="internal")`. (b) **Urgency interrupt** — if the node self-rates urgency > 0.6, it sets `state.interrupt_requested = True` / `interrupt_source = "curiosity"`, and the substrate loop's stale-interrupt sweeper clears it after ~5 minutes if unconsumed. (c) **Passive feed** — after every completed cycle, `orchestrator._update_background_nodes` calls `nodes["curiosity"].add_theme(theme)` to accumulate themes (capped at last 30). The node runs on the CPU lane (no GPU reservation); LLM call is via `NodeBase.run`.

- **Reads / touches:**
  - `data/subconscious_state.json` — pulls tensions pool for seed selection (sqrt-flattened salience, recency penalty, anti-relock)
  - `core.memory.store.recent_world_material()` — study notes / book passages / lookups as the grounded question source
  - `core.frontier.pending_pursuit()` — picks the current open frontier question to research toward
  - `core.web_research` (`lookup_targeted`, `lookup`, `term_from_question`, `store_finding`) — Wikipedia/external lookup
  - `core.scholar.consult_sync` — parametric fallback when Wikipedia can't answer the specific question
  - `core.frontier.attach_finding` / `note_question` — closes pursuit loop and opens new world-questions
  - `core.schema.CognitiveState.background_curiosities` — writes questions+directions here for downstream nodes

- **Writes / feeds:**
  - `state.background_curiosities` (list[str]) — consumed by:
    - `inner_monologue_node.py:726` — first item prepended as "A question lingering in you:" in monologue seeds
    - `inner_monologue_node.py:1153` — all items checked for note_question calls
    - `dream_node.py:239` — first 6 items used as dream themes
    - `subconscious_node.py:915` — self-referential items used as active-imagination seeds (Priority 2 after tensions)
    - `orchestrator._on_dissonance_ignition:1966` — valid questions (non-placeholder, len>12) trigger autonomous internal cycles
  - `data/curiosity_log.jsonl` — firewalled observe-only record (read by `scripts/session_digest.py` only)
  - `data/twig_log.jsonl` — firewalled twig record (read by `scripts/du_pulse.py` twig gauge only)
  - `core.frontier` — new open questions + pursuit findings (the primary durable world-engagement output)
  - `core.memory.store` via web_research.store_finding — origin='research' fragments in memory store

- **Built / last updated:** Earliest dated comment in file: `2026-06-09` (varied-seed anti-attractor rewrite). Latest dated comment: `2026-06-15` (study-material grounded seed + world-research closing loop). File mtime: `2026-06-16 10:27:15`. The node was therefore actively developed through mid-June 2026.

- **Fleshed-out vs stub:** Genuinely fleshed out. 316 lines, 8 methods. Has: system_prompt, prompt builder with two seed tracks (study material + inner tensions), seed selection with weighted sampling and anti-relock, web research with pursuit-first / grounding-fallback / scholar-fallback, frontier integration, interrupt signalling, and two firewalled observability logs. The read paths into downstream nodes (inner_monologue, dream, subconscious) are all real and verified in code. Not a stub.

- **Flesh-out opportunities:**

  1. **Gap: contradiction gate routing is a dead write.** `contradiction_gate.evaluate` routes abstract/non-concrete tensions to `route="curiosity"` (e.g. river/LLM loops from `meta_awareness_node`). This verdict is logged to `_SHADOW` but **never forwarded to `curiosity_node.add_theme` or any curiosity input.** The curiosity node receives no signal from the gate — the two systems are unconnected. Abstract tensions that the gate explicitly labels "should go to curiosity" never reach it. Wiring fix: in `meta_awareness_node.py` (or wherever the gate verdict is acted on), when `verdict["route"] == "curiosity"`, call `orchestrator.nodes["curiosity"].add_theme(snippet)`. Same for `prediction_error.py` if it ever routes to curiosity.

  2. **No memory of prior curiosity output.** `add_theme` receives the perception summary from each cycle, not what curiosity actually generated last time. If curiosity asked "What drives the tension between X and Y?" that question does not re-enter the next curiosity cycle as a prior thread. A small ring-buffer of past questions (like `_recent_themes`) seeded from `curiosity_log.jsonl` on startup would give curiosity a sense of its own trajectory and reduce redundant re-generation.

  3. **Urgency interrupt is structurally fragile.** The substrate loop clears `interrupt_requested` after ~5 minutes (60 × 5s ticks) regardless of source. If a curiosity urgency interrupt fires during a user cycle and that cycle takes more than 5 minutes, the interrupt evaporates silently. No re-queueing, no logging of the evaporation. The curiosity question that triggered it is lost. Could be improved by re-injecting the high-urgency question to `frontier.note_question` before clearing.

  4. **Scholar fallback is unverified / ephemeral by design.** When Wikipedia fails, the scholar's parametric answer is attached to the pursuit with the prefix "(from my own knowledge, not yet verified)". This is the right discipline, but there is no follow-up mechanism that schedules re-verification. The unverified finding sits on the frontier question permanently unless a future curiosity cycle happens to hit the same pursuit and Wikipedia is available then. Low priority but worth noting.
