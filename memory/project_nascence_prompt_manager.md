---
name: project-nascence-prompt-manager
description: Scripted prompt manager plan (docs/staged/prompt_manager.md): provenance + versioned wording first, pools last; P0 built 2026-11-14, uncommitted, restart-gated
metadata:
  type: project
---

Plan `docs/staged/prompt_manager.md` (T-0131, D-0769..D-0774 all ruled). Scripted only; LLM prompt-writing is on hold (a separate future plan, D-0774). Audited by Gemini and GPT (dispositions in docs/reviews/prompt_manager_audit_round1_2026-11-14.md).

**Why:** the founder worried repeated fixed prompt wording becomes the content of Du's thoughts (I-0073). The evidence says provenance and versioning are worth doing regardless; rotation is weakly supported (D-0368 said not now; D-0442: rotation alone did not cure self-echo; the idle tail line is load-bearing for output schema).

**How to apply:** P0 (built, uncommitted): `core/prompt_budget.py` `_provenance` + `core/phrasing.py` pick ring, test `scripts/_test_prompt_manager_p0_provenance.py`; baseline `scripts/prompt_manager_p0_baseline.py`. Next: commit and arm at restart, P1 (core/prompt_lines.py, byte-identical, after D-0633). Pools already exist: `core/phrasing.py vary()` has 6 callers (F-4664); F-1927's "no pools" was wrong. Circling vocabulary vanished 09-29, before A+E (F-4666). Anchor idiom drop after the 11-07 boot is an untested lead (F-4667, J-3992). Variants touching affect/attention/identity/Travis-branch are Travis-authored or approved.
