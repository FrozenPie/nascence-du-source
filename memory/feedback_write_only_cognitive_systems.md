---
name: feedback-write-only-cognitive-systems
description: This project repeatedly ships cognitive systems with elaborate write paths and dead read paths; always verify the read-into-prompt path
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c78d22dd-1562-4ece-b8d5-ee40e2df926a
---

Sovereign Hub's #1 recurring failure mode: a cognitive system is built with a rich WRITE path (tables populated, state accumulated, propagated) but the READ path that should feed that state back into a spirit's decision prompt is missing or silently broken — so the system influences nothing and looks "✅ shipped" while being functionally dead.

Confirmed across THREE systems as of 2026-05-29:
- **Wisdom/L2** — queue never fed (dict-`len()` gate) + L2 read SELECT threw on a missing column, swallowed by bare `except`. Zero wisdom ever reached a prompt. (see [[project-wisdom-layer]])
- **Idea contagion** — was written + propagated but never injected into any prompt; `concept` never persisted; AND two cross-DB/schema bugs (propagation read the empty simulation_live copy; susceptibility queried non-existent trait columns and threw on every transmit). **Fixed 2026-05-29** — concept persistence + `transmit_top_infections` (correct DB) + susceptibility reads `psychometric_profile` JSON + `format_infection_for_prompt` read path. Pending restart.
- (and the general schema-drift / silent-failure issues already in CLAUDE.md)

A distinct VARIANT — the **information-destroying write** (Nascence, 2026-06-21): the write path runs and a value lands, but in a form the read path can't recover. Nascence's `mood.py` stored each fragment's felt-quality by serialising the affect to a STRING (`"valence=+0.80 arousal=0.40 …"`) then running it through MiniLM — a *sentence* encoder, which preserves word-similarity, not numeric magnitude, so `+0.80` and `−0.80` embed to nearly the same point. Valence was written but unrecoverable (it scored 400/400 fragments equally "warm"). Fixed by persisting the raw scalar (`valence REAL` + the full `felt` string) alongside the embedding. The tell: a "felt-tag" / "embedding" / "score" column that nothing ever successfully *reads back* — test recovery, not just that a value is present. Don't put numbers through a text encoder.

A sibling pattern is **dormant code presented as active** — engines instantiated in the dispatcher `__init__` but with no method ever called. Found 2026-05-29 during the System_Report audit: `arbiter_engine` (self.arbiter_engine :114, never called — and its real job is selecting the round's arbiter spirit, not judging debates), `conflict_sandbox` (standalone CLI, not in the round loop), `sensory_perception_module` (self.sensory :179, never called; the live path is the separate `sensory_engine`). Always check for a method *call*, not just instantiation/import.

**Why:** features get marked done when the write path works and a DB row appears, or when an engine is imported/instantiated. Nobody traces whether the stored state actually changes what the LLM sees, or whether the engine's methods are ever invoked.

**How to apply:**
1. When auditing ANY cognitive feature, ask first: "where is this read back INTO a spirit/Buddha prompt or decision?" If there's no read-into-prompt path, the feature is inert regardless of its write machinery or its "✅" status.
2. When BUILDING a feature, ship the read path in the same change and prove it with a live write→read smoke test (e.g. stigmergy was built deposit+decay+read together; see [[project-stigmergy]]).
3. Before ENHANCING a system (e.g. DIT on idea contagion), verify its read path exists — don't tune the flow of a graph no spirit can perceive.
4. Distrust bare `except: pass` around DB reads — it hides schema mismatches that silently kill read paths.
