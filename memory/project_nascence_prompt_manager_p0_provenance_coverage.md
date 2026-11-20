---
name: project-nascence-prompt_manager_p0_provenance_coverage
description: Prompt manager P0 provenance covers only the idle-thought station by design; widening needs a founder ruling (J-4309, F-5085)
metadata:
  type: project
---

Plan `docs/staged/prompt_manager_p0_provenance_coverage.md`. `data/prompt_provenance.jsonl` (3385 rows on 2026-11-20) is all `inner_monologue.idle_thought`; about 30% of top-station calls.

**Why:** plan section 10b says Level 1 on the idle station only until overhead is measured; no measurement is recorded and Q7 has no D-id.

**How to apply:** options are a thin `observe_call` hook in `core.model_client`/`NodeBase`, per-site calls, or stay idle-only. Needs a ruling before code. Parent: project_nascence_prompt_manager.md.
