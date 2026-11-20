---
name: project-udms-feedback-loop
description: UDMS is under active co-development with a sibling FreshStart/UDMS session — verify its verdicts and report defects back rather than silently working around them
metadata: 
  node_type: memory
  type: project
  originSessionId: 4595f5ad-65f2-480a-8d83-32786682d18c
  modified: 2026-08-28T22:50:31.283Z
---

UDMS (`C:\UDMS`, MCP server `udms` wired into this repo via `.mcp.json`) is being actively developed
by a sibling session in the FreshStart/UDMS project, not a finished third-party tool. As of
2026-08-29, a real feedback loop is established and working: this session verified two UDMS leads
(F-0462, F-0463) skeptically instead of trusting or silently dismissing them, found the verdicts
didn't hold as stated, and reported the mechanism back — which led directly to 2 of 3 real fixes
shipped in UDMS commit `4e526d1` the same day (function-scoped/deferred imports now exempt from
cycle detection; doc-audit's independence-claim detector now requires an explicit bound assertion).
A third fix (cycle-warning reporting was untargeted, always returning the first cycle anywhere in
the repo) came from this session independently noticing the SAME unrelated `heavens.py`↔
`world_clock.py` cycle flagged on nearly every dossier call regardless of target file, across ~20
calls in one session.

**Why:** the other session's own framing: "tool flags, you verify, tool improves — is the whole
design." Nascence-side skepticism is a designed input to UDMS's own development, not a workaround
to route around a black box. See [[project-plan-portfolio-audit]] for the session this pattern
emerged in.

**How to apply:**
- When a UDMS verdict (dossier CRITICAL flag, doc-audit contradiction, hygiene dead-function claim)
  smells wrong, verify it concretely (read the actual code/imports/doc text) and if it doesn't hold,
  say so with the specific mechanism — don't just quietly work around it. That report is genuinely
  useful upstream.
- **The MCP server's scan snapshot is taken once per Claude Code session, at `udms` MCP process
  start.** A sibling session's UDMS updates (even a same-day commit) do NOT apply to an
  already-running session's MCP tools until that session restarts. If load-bearing UDMS work is
  needed mid-session after a known update, use the CLI directly instead: `python udms.py <cmd>
  C:\Nascence` run from `C:\UDMS` (commands: `scan`, `check`, `doc-audit`, `hygiene`, `battery`,
  `discover-regimes`, `similar-history`, `calibrate`) — this always runs current code.
- **The "every dossier flags an unrelated heavens.py↔world_clock.py cycle, always dismiss it"
  heuristic this session taught several agents was specific to a real UDMS bug (untargeted cycle
  reporting), now fixed as of `4e526d1`.** Once a session actually restarts its `udms` MCP server
  after this fix landed, stop applying that dismissal habit — a CRITICAL cycle warning is real
  again and should be checked properly, not pattern-matched away.
- Ranked/TEMPORAL-layer evidence (git co-change PMI) stays discounted specifically because
  Nascence's own git history is still thin (~22 usable commits as of 2026-08-29), not because the
  ranker is broadly unreliable — this project's CLAUDE.md tracks the current ranker-vs-churn-baseline
  win rate; check it before assuming this discount still applies far in the future.
- STATE/CONTRACT-layer evidence (real imports, real shared state) has been reliable every time this
  session used it — keep trusting it as close to ground truth, it's not ranked or probabilistic.
