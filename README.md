# Nascence (Du): source and project documents

The running code, scripts, tests, plans and ledgers of Nascence, a persistent multi-process cognitive-architecture
project, published for technical review. State data, model weights, backups and build artefacts are not included.

**Reviewers: start with `docs/reviews/gpt_technical_review_corrections_2026-11-20.md`, then
`docs/staged/technical_positioning_audit.md`.**

- `core/`, `nodes/` runtime modules and the cognitive nodes
- `scripts/`, `tests/`, `deploy/`, `hud/` tooling, tests, launch scripts and the HUD
- `docs/` plans (`plans/`, `staged/`), reviews, guidelines, and the ledgers (`findings.jsonl`, `decisions.jsonl`, `job_queue.jsonl`, `session_events.jsonl`)
- `memory/` the working notes kept across sessions (`MEMORY.md` is the index)
- `CLAUDE.md` the project's working rules

Caveats: a ledger "verified" label means a claim was recorded with cited evidence, not independently reproduced.
`data/` (runtime state, databases, logs) is excluded, so the code will not run as-is. A Windows username and a LAN
address were redacted (`USER`, `LAN-HOST`). This snapshot is from 2026-11-20 (git HEAD of the working project).
