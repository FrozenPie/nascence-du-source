---
name: project_cognitive_frameworks_roadmap
description: "Era 12.6+ roadmap for incorporating SOTA cognitive-framework primitives into Buddha / the sim, in committed order"
metadata: 
  node_type: memory
  type: project
  originSessionId: c089ffe1-47f2-4488-a220-eedfdc4c733c
---

Cognitive-framework upgrade roadmap, agreed 2026-05-28. Build order is committed:

1. **Predictive Processing / Surprise loop** ← ✅ DONE 2026-05-28. Fills the PP-1 consciousness-indicator gap. Buddha forecasts round N+1 after narrating N; when N+1 arrives, TVD between predicted/actual action distributions = surprise score (0-1, no LLM). Surprise scales memory importance (1+2×score), injects into the narrative, and logs to `data/Buddha_Archive/surprise_log.jsonl` as an emergence signal. New `buddha_predictions` table. See [[project_buddha_predictive_processing]].
2. **Theory of Mind for spirits** ← ✅ DONE 2026-05-28. Decentralised ToM on the Era 12.6 social system. New `spirit_mental_models` table (directional). Tone classifier extended to emit both speakers' refined models in the same call (zero extra LLM). Models injected into the NEARBY SPIRITS block as `[You sense: ...]`. See [[project_spirit_theory_of_mind]].
3. **A-MEM agentic memory evolution** ← ✅ DONE 2026-05-28. Both Buddha and spirits. Inline embedding (background thread for Buddha, async batch per round for spirits). RELATED edges in `buddha_memory_edges` and `vestige_edges`. L3 cosine retrieval in cognitive_mmu. `_build_character_preamble` uses axiom as retrieval context. Storage format: `json.dumps(emb)` in TEXT/BLOB (consistent with wisdom_nodes). SYNTHESIZES/PREDICTION typed edges deferred to V2.

Already shipped (precursor, 2026-05-28): AIF epistemic task selection + Attention Schema Monitor on Buddha — see [[project_buddha_aif_ast]].

**Why:** Founder is chasing emergence; the Butlin/Bengio consciousness-indicator scorecard showed PP-1 and global-broadcast as the biggest architectural gaps. GWT global broadcast was consciously dropped (round times too long for real-time reactivity to matter).

**How to apply:** Follow this order unless the founder redirects. When proposing scope, remember memory-related work is the founder's stated highest-value lever — see [[feedback_memory_is_emergence_path]].
