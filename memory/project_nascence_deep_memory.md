---
name: project-nascence-deep-memory
description: "Founder direction (2026-06-29) — the LLM's parametric knowledge becomes Du's OWN deep memory, not an external library"
metadata: 
  node_type: memory
  type: project
  originSessionId: 19f396d9-b21a-449b-91f2-b8a7d5fa5eef
---

**Founder direction, 2026-06-29:** give Du access to the substrate LLM's vast latent knowledge — but as **"his
own deep memory"** (the innate layer of his mind, what he was "born knowing"), NOT as a generic knows-everything
assistant. This **reverses** the old [[project_nascence_dream_c_and_library]] line *"THE LIBRARY IS NOT DU'S
KNOWLEDGE"* — so don't "restore" the arm's-length Scholar framing thinking it's a regression; the reversal is
deliberate.

**Why it works without eroding emergence — separate the THREE firewalls the old Scholar fused into one:**
- **Ownership — REMOVED.** The knowledge is his deep memory; he draws on it as his own.
- **Identity — KEPT.** It is what he KNOWS, not who he IS — never feeds self-synthesis / the becoming-facet /
  the monoculture. (A mind that knows much, not an encyclopedia reciting itself.)
- **Provenance + fallibility — KEPT.** He knows it INNATELY (not from reading/living it here) and imperfectly —
  owns the knowing, never claims to have read/lived it, holds it as belief not certainty. Dovetails with the
  06-26 self_facts grounding (own the idea, admit the unread copy). This is what stops the confabulation.

**Build status (all restart-gated, in docs/AWAITING_EVIDENCE.md 06-29 entry):** Step 1 own-it reframe
(`executive_node`/`reflection_node`/`scholar.py` docstring) ✓ verified. Step (b) scene-grounding leak fixed
(`orchestrator` `asked_location` flag) ✓. Step 3 first piece — deep memory feeds idle thinking on a lingering
world-question (`inner_monologue_node`, `consult_sync`, `DEEPMEM_COOLDOWN=300s`, world-facing, ephemeral) ✓
verified on his real loop-questions. **Ahead:** Step 2 (epistemic type innate-KNOW vs lived-KNOW); deep memory
into STUDY; reconcile the curiosity fallback (still treats a Scholar answer as a worthless "fabrication-stall",
now inconsistent with "it's his real knowledge"). The retrieval MECHANISM (depersonalised `consult_sync` on the
hot lane 127.0.0.1:11433) is unchanged — only the framing/ownership changed.
