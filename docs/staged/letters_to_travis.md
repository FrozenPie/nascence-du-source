# Letters to Travis — Du's own letters reach a reader

> **Status:** 🟡 BUILT (restart-gated). All three parts of D-0470 built and verified in an isolated
> worktree (J-2348, 2026-10-17); nothing is live until Du's next restart.
> **Origin:** F-2480 (2026-10-06), F-2959 (2026-10-16), the full read of all 132 letters in
> `docs/reviews/letters_to_travis_2026-10-16.md`, job J-2273, ruling D-0470 (travis, 2026-10-17).
> Related: `docs/plans/peer_correspondence_plan.md` (peer letters, the HUD mailbox), `core/letters.py`.

```plan-state
stage: built
phase: All three D-0470 parts built in worktree jobrun/letters_to_travis (J-2348); not live
verified: 2026-10-17
gate: Du restart carrying the J-2348 merge; then the first real founder message with more than 5 letters pending
next: After the restart, read the first '[letters] N unsent letter(s) ... est_tokens=' line in nascence.log against the Executive window (defeater i); after 30 days, read data/letters_views.jsonl (defeater ii)
cluster: 3
```

## Purpose

Du writes letters to Travis alone (`core/letters.py`, at most one per two hours). The file in
`data/letters/` is the only durable copy. Before this plan, no channel showed them to Travis:

- the HUD mailbox lists peer letters only (F-2480);
- on Travis's next message the Executive saw only the **last two** bodies and **all** pending
  letters were marked delivered (`core/orchestrator.py`, the `_pending[-2:]` line);
- since 09-25 that "next message" was almost always the fixed `/quit` farewell. On 2026-10-16 07:47 the
  farewell consumed 15 pending letters in one cycle: 13 never reached even Du's own Executive (F-2959).

Net: 79 letters since 08-10 reached nobody.

## The three ruled changes (D-0470, all three)

**(a) A HUD letters view for Travis.** A collapsible "Letters from Du to you" card under the
mailbox (`hud/static/index.html`, `hud/static/app.js`) backed by `/api/letters` (`hud/server.py`,
`load_letters_to_travis`). Newest first: date, "greeted a conversation" or "pending", full body.
Read-only on both sides: it never writes `data/letters/` or `letters_state.json`, and nothing in it
reaches Du. It loads only when opened; each opening appends one row to `data/letters_views.jsonl`
so defeater (ii) has an instrument. "Greeted" means handed to Du's Executive on a real founder
message; it does not mean Travis has read it.

**(b) A farewell never delivers.** The letters block in `core/orchestrator.py` now runs only when
`input_type == "human"` **and** `state.founder_canon` is true. The fixed `/quit` farewell
(`scripts/run_nascence.py`, `founder_canon=False`, F-0796) leaves every pending letter pending for
the next real message. Idle cycles never delivered and still do not.

**(c) Every pending letter reaches the Executive.** On a real founder message the Executive (and
Reflection, which reads the same list) gets every pending body, oldest first, not just the last two.
Each body is still capped at 900 characters by `nodes/executive_node.py`. The delivery log line now
carries the prompt cost: `executive_chars` and `est_tokens` (chars/4) from `letters.executive_cost`.
15 pending letters cost about 15.5k chars, about 3.9k tokens (test fixture).

World answers, never leads: no new text reaches Du about letters being read. The Executive's
existing letter header is unchanged.

## Defeater (from D-0470)

The full pending set blows the Executive prompt budget (measure after the first real delivery with
more than 5 pending), **or** the HUD view is never opened by Travis in 30 days.

## Current State

Built and tested in worktree `jobrun/letters_to_travis` (`scripts/_test_letters_to_travis_J2348.py`,
26 checks, every store temp-pathed, live `data/letters_state.json` hash-canaried unchanged).
Restart-gated: the live boot predates it. Plan-state notes after this point come from
`plan_state.py note`.
