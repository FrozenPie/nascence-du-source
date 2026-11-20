# Nascence — Plan Shadow Read

**Generated:** 2026-11-19 22:54 UTC by
`C:\Users\USER\.claude\skills\plan-shadow-read\plan_shadow_read.py`. Read-only, deterministic,
no LLM.
Regenerate by invoking `/plan-shadow-read`; this file is overwritten each run.

Sibling to `plan-liveness` (which tracks whether a shadow log exists and is accruing) — this tool
answers the question plan-liveness deliberately does not: does the shadow log's own DATA meet the
plan's own stated promotion criteria? A plan opts in by declaring a ```shadow-promotion fenced block
(see plan_shadow_read.py's module docstring for the full spec format).

- **GREEN** — every condition in the plan's `green:` rule holds over the declared window.
- **RED** — at least one condition fails — the actual signal that a promotion decision is now
  answerable (open a `/decide` question citing this).
- **INSUFFICIENT** — fewer rows in the window than `min_rows`, or a condition's field had no data to
  aggregate over yet.
- **MISSING** — the spec's `log:` doesn't resolve to a real file.
- **BAD-SPEC** — the block is missing a required key or has an unparseable `green:` rule — reported,
  not guessed at, same discipline plan_liveness applies to a threshold it can't confidently parse.

| Plan | Spec id | Log | Rows (window/total) | Rule | Verdict | Note |
|---|---|---|---|---|---|---|
| journal_consolidation_pyramid | hard-grounding | `data/journal_grounding_shadow.jsonl` | 20/29 | `mean(faithful) > 0.7 and count(invented_genuine) == 0` | 🔴 RED | failed: mean(faithful) > 0.7 |
| closure_law | closure_shadow.jsonl | `data/logs/closure_shadow.jsonl` | 0/0 | `—` | ❓ BAD-SPEC | missing required key 'log' or 'green' |

# 2 shadow-promotion spec(s) across 2 plan(s) · 🟢 0 GREEN · 🔴 1 RED · · 0 INSUFFICIENT · ⚠ 0 MISSING · ❓ 1 BAD-SPEC
# 115 plan(s) have no ```shadow-promotion block (NOT necessarily a gap — most plans have no shadow log at all)

**journal_consolidation_pyramid / hard-grounding** (`data/journal_grounding_shadow.jsonl`, verdict RED):
- ✗ `mean(faithful) > 0.7` -> computed=0.7 (n=17)
- ✓ `count(invented_genuine) == 0` -> computed=0 (n=20)

# Edge store: 0 new, 1 updated, 0 retired `shadow_verdict` edges -> C:\Users\USER\.claude\projects\C--Nascence\memory\_memory_edges.jsonl
