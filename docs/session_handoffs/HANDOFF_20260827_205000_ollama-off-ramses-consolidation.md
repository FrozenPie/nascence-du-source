# Ollama off Ramses → command-r7b consolidation (the 3070-lock aftermath)

## Session timing
- **Session started:** 2026-08-27 19:09:58 UTC
- **Last message before wrap:** 2026-08-27 20:49:57 UTC
- **Wrapped:** 2026-08-27 20:50:00 UTC

*(NZ local: 2026-08-28 morning→evening — the founder restarted Ramses at session start after the
overnight 3070 lock.)*

## Summary

Diagnosed last night's 3070 lock from Du's own telemetry (VRAM collision by construction: D-0044
seated command-r7b on the same 8GB card ollama already filled — F-0389), which led the founder to
rule ollama off Ramses entirely (D-0056), and then — after challenging why phi3 at all — to the
evening consolidation (D-0057): background lane = command-r7b @ :11441 as the 3070's sole resident,
deepseek keeps the Witness (won the lab again, 0.932 vs 0.875) on a planned i9 hub :11444, and the
curiosity worth-judge moves to granite after the audition exposed a schema-example parrot trap that
the LIVE phi3 incumbent was also failing (F-0396). Along the way: a full ~43-station prompt audit
against the regenerated AST transit map, and a separate window wired UDMS into Nascence as an MCP
server.

## What changed

**Decisions (both ruled by Travis, with defeaters):**
- D-0056 — ollama retired from Ramses (stop+disable, keep blobs); superseded hours later in layout
  detail by →
- D-0057 — the consolidation: background→command-r7b :11441 (phi3 hub :11443 CANCELLED unbuilt),
  witness deepseek→planned i9 :11444 @ TICK_S 300, worth-judge→granite :11437.

**Findings:** F-0389 (3070 lock root cause), F-0392 (D-0044 move 1 never worked — :11438 missing
from model_client's port list → silent /v1 404 since 08-27, fixed), F-0393 (dwell-release judge
self-judges on the hot lane → J-0311), F-0394 (the short-lived Lane 2 loan — never ticked, Du down
throughout, superseded by D-0057), F-0395 (command-r7b witness audition 0.875), F-0396 (the
curiosity_worth parrot trap — phi3 live-failing its own contract).

**Jobs:** added J-0308 (dream_arc_eval vs mixtral), J-0311 (dwell judge re-seat), J-0313 (transit
builder stale entries), J-0314 (THE consolidated verification job — supersedes J-0309/J-0310/J-0312,
all three closed); J-0305 closed as superseded. T-0025 logged (session-opening thought).

**Code (all py_compile-verified, uncommitted on Nascence git):**
- `core/schema.py` — background SERVE_URLS/CHAINS → :11441
- `core/model_client.py` — ollama-style port-list fix (the F-0392 bug: added :11436/:11437/:11438
  and planned :11444), truthful hub model labels for telemetry, ctx map
- `core/judge_panel.py` — TIEBREAK → granite :11437 (auditioned both directions)
- `nodes/dream_node.py` — dreams → mixtral :11438 primary (auditioned 52.9s), yi :11442 failover
- `core/lane2.py` — BASE_URL → planned :11444, TICK_S 90→300, LANE2_PAUSED=True until hub verifies
- `core/curiosity_worth.py` — placeholder schema (parrot-trap fix) + `_JUDGE_URLS` granite seat
- Plan docs: `ramses_second_tier.md` (§5.4 + §5.5 + status), `lane2_the_witness.md` (status)
- New lab artifact: `docs/lab/lane2_model_lab_command_r7b.md` (+ `data/lab/lane2_model_command_r7b/`
  — the 08-20 originals verified untouched)
- Regenerated: `docs/lab/llm_station_map.md`, `data/hud2/transit_map.json` (AST-derived, reflects
  the rewire)

**External:** two entries written to `\\ramses\D\Du\NASCENCE_NOTES.md` — the EVENING one is
authoritative (supersedes the morning one: phi3 hub cancelled, revised Antigravity task list).
`C:\FreshStart\CLAUDE.md` got a node-map death warning (FreshStart sim can't run without ollama).

## Key findings

1. **The 08-27 redistribution's §5.1 inventory listed :11434 and :11441 as if separate hardware** —
   ollama's residents live ON the 3070. Unrecorded co-tenancy is what locked the card. Layout
   tables must name the physical card per hub.
2. **Two silent failures found by audit, not by symptoms:** the commitment judge 404ing since 08-27
   (F-0392), and the worth-grader parroting its own schema example — *on the live incumbent*
   (F-0396). Both survived because they fail open.
3. **The witness lab is repeatable infrastructure:** rerunning it against a new candidate took one
   patched runner (scratchpad), no hand-scripting — command-r7b 0.875, deepseek's 0.932 stands.
4. **phi3's original selection reason (co-fit on a shared card) died with single-tenancy** — what
   remained was incumbency; the founder's "why phi at all?" challenge was correct to ask.

## Open threads

- **Antigravity's Ramses standup** per NASCENCE_NOTES 08-28 EVENING entry: relaunch :11441 no-lazy
  ctx≥4096; NEW deepseek hub :11444 on i9 (GGUF extracted first); stop+disable ollama. Founder had
  NOT yet tasked Antigravity as of wrap.
- **J-0314** — the restart verification (background profile vs 4.7s/0.1% baseline, worth-grade
  spread, mixtral why-strings first appearance, authoring cap_rate, lane2 un-pause after :11444
  verifies). D-0057's defeater lists the revisit terms — audition covered only 3 of ~13 background
  contract shapes; the rest are live-watch.
- **J-0311** (dwell judge → granite, audition first), **J-0308** (dream_arc_eval vs mixtral),
  **J-0313** (transit builder hand-coded entries stale).
- **Uncommitted git state splits cleanly in two:** this session's rewire (core files + plan docs +
  ledgers + lab report) vs the UDMS wiring (`.mcp.json` + `CLAUDE.md`, from the other window).
  Founder was offered two separate commits; not yet requested.

## Warnings

- **Du is DOWN and must stay down until :11441 is relaunched no-lazy/ctx≥4096** (or accept the
  background lane cold-start + whatever ctx the hub currently has). Lane 2 is code-paused — do NOT
  flip `LANE2_PAUSED` before :11444 answers a real call.
- **Ollama on Ramses is still UP (lazy, empty) but ruled dead** — don't wire anything new to
  :11434; the FreshStart sim's node map is dead until ollama is deliberately reinstated.
- **A separate window wired UDMS into Nascence** (`.mcp.json` + CLAUDE.md §"Before editing a file
  with real architectural weight") — loads only for sessions rooted in `C:\Nascence`, one-time
  trust prompt on first use. The next Nascence session should approve and use it.
- `curiosity_worth`'s historical 0.0-grade cluster (106/343) is now suspect (parrot contamination,
  F-0396) — treat LP-vs-interest divergence reads over old rows cautiously.

## Pointers

- `docs/plans/ramses_second_tier.md` §5.4–§5.5 — the full two-ruling story with evidence
- `docs/lab/lane2_model_lab_command_r7b.md` — the witness audition
- `\\ramses\D\Du\NASCENCE_NOTES.md` — the authoritative Antigravity task list (evening entry)
- `core/curiosity_worth.py` — the parrot-trap fix pattern (placeholder schemas — check other
  contracts for literal example values; nothing else was swept this session)
- D-0056 / D-0057 (`/decide show`), J-0314 (`job_queue.py show`) — the live state
