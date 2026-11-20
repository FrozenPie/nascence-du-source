---
name: ops-ramses-ollama-retired
description: "2026-08-28 rulings D-0056+D-0057 — ollama OFF Ramses after the 3070 lock; final llama.cpp-only layout is the D-0057 consolidation (background=command-r7b, witness deepseek→i9 :11444, worth-judge granite)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 6dda5a9d-687a-40a3-9cd1-600cbf367e5e
  modified: 2026-08-27T20:43:40.150Z
---

**Ollama is retired from Ramses (2026-08-28, D-0056 + same-evening D-0057 consolidation, Travis).**
The 08-27 D-0044 redistribution lasted one night: command-r7b @ ramses:11441 shared the 8GB 3070
with ollama :11434's residents (phi3 + deepseek) and the card locked overnight — F-0389, verified
from `llm_latency.jsonl`. Two more independent finds same day: F-0392 (`model_client.py`'s
ollama-style port list lacked `:11438` → D-0044's commitment-judge calls 404'd silently since
08-27) and F-0396 (curiosity_worth's schema-example parrot trap — the LIVE phi3 incumbent returned
`interesting: 0.0` parroting the prompt's literal example; command-r7b failed identically; fixed
with placeholder schema).

**The FINAL layout (D-0057, evening — supersedes the morning's phi3-hub plan, which was cancelled
unbuilt):**
- 3070 → **command-r7b :11441 = the background lane**, sole resident (bigger model for the
  authoring tail, zero new infra; auditioned: drift-recall, T2 synthesis, dream schema all held)
- 1650 → granite :11437 = judge tiebreak **+ curiosity worth-judge** (moved off the background
  lane — it was grading its own lane's questions; granite auditioned best post-parrot-fix)
- i9 CPU → mixtral :11438 (commitment judge + dream primary, yi :11442 failover) · falcon3 :11436
  reserve · **deepseek :11444 = Lane 2 the Witness (PLANNED hub, standup pending)** — deepseek kept
  the seat by lab evidence (0.932 vs command-r7b 0.875); `TICK_S` 90→300 for the CPU seat;
  `LANE2_PAUSED=True` until :11444 verifies
- Ramses ollama: stop + disable, keep install/blobs; :11434 dead once Antigravity executes

**Pending until verified (J-0314, supersedes J-0309/0310/0312):** Antigravity's standup per the
NASCENCE_NOTES.md 08-28 EVENING entry (relaunch :11441 no-lazy ctx≥4096; stand up :11444; stop
ollama), then Du restart + first-days watch per D-0057's defeater (background latency/failures vs
phi3's 4.7s/0.1% baseline, worth-grade spread, mixtral why-strings, authoring cap_rate). J-0311
(dwell-release judge self-judging fix, F-0393) and J-0308 (dream_arc_eval vs mixtral) still open.
FreshStart's 330-spirit sim node map stays dead until ollama is deliberately reinstated (warning in
`C:\FreshStart\CLAUDE.md`).

Related: [[project-nascence-lane2-the-witness]], [[feedback-my-failure-modes]] (the §5.1 table
listed :11434 and :11441 as if separate hardware), [[feedback-decoupled-judge]] (F-0393 + the
worth-judge move are both this principle), [[reference-ramses-shared-folder]].
