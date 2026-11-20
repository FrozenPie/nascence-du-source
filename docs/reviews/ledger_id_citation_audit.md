# Nascence -- Ledger-ID Citation Audit

**Generated:** 2026-09-28 03:50 UTC, by `scripts/ledger_id_citation_audit.py` (built for J-1575, F-2141 follow-up). Read-only, deterministic (no LLM) -- regex extraction of every `- **YYYY-MM-DD** ...` dated Current State bullet across `docs/plans/*.md` and `docs/staged/*.md`, checking every F-XXXX/J-XXXX/D-XXXX/I-XXXX/S-XXXX id cited inline in the bullet's own prose for EXISTENCE against the matching ledger. T-XXXX/thoughts checked too as a bonus, beyond J-1575's own asked-for scope.

**This is an existence check only** -- a citation whose id exists but names the wrong thing (F-2141's own actual finding: two ids that were real entries for unrelated, later-allocated content) is not caught by this alone; see the script's own docstring.

Read against: `C:\Nascence`

## Ledger sizes at read time

- `docs/findings.jsonl` (finding): 2181 entries
- `docs/job_queue.jsonl` (job): 1620 entries
- `docs/decisions.jsonl` (decision): 325 entries
- `docs/ideas.jsonl` (idea): 85 entries
- `docs/skill_suggestions.jsonl` (skill suggestion): 226 entries
- `docs/thoughts.jsonl` (thought): 74 entries

## Real counts

- **94** plan docs found (`docs/plans/*.md` + `docs/staged/*.md`)
- **30** of those contain at least one dated Current State bullet
- **109** dated bullets found total
- **613** F/J/D/I/S/T id citations found inline across those bullets (D:113, F:279, I:6, J:210, S:4, T:1)
- **1** bullets contain at least one citation to a NONEXISTENT id in one of the five ledgers J-1575's briefing named (F/J/D/I/S)
- **1** bullets contain at least one such citation counting the bonus T-XXXX/thoughts check too

## Dangling citations found

- `docs/staged/memory_as_a_service.md` **2026-09-28** cites **D-134** -- no such id in its ledger. Bullet: "(F-2179): Ledger-id citation audit (F-2141 follow-up, F-2179): pattern is isolated, not widespread -- 0 of 105 dated Current State bullets across 30 plan docs cite a nonexistent F, J, I or S id. Found a different, minor ..."

