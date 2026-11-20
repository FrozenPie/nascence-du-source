# Closure producer: Du's top five thinking flaws, the closure post-mortem, and Phases 0 to 5 built and merged

## Session timing
- **Session started:** 2026-11-15 22:21:46 UTC
- **Last message before wrap:** 2026-11-16 01:01:20 UTC
- **Wrapped:** 2026-11-16 01:01:21 UTC

## Summary
The founder asked for Du's top five thinking flaws against humans, then for research on why closure has never been fixed. A post-mortem of about twenty closure attempts found that nearly all of them graded closure and none produced it; the plan `closure_producer` was staged, ruled (D-0789 to D-0793), built in six phases, merged to master and tested, and the founder was restarting Du at wrap time. Nothing in the build has yet been observed running in a live process.

## Decisions
All ruled by travis in this session through AskUserQuestion; the defeater wording on each is Claude's, not the founder's.
- D-0789: a web-hand lookup result is attached automatically to the open frontier question it matches by embedding; no match, no attach.
- D-0790: question inflow is limited only by merging rewordings into the open or already-answered question; no hold-by-rule.
- D-0791: existing word-match closes stay resolved and are relabelled `lexical`.
- D-0792: judgement-shaped questions are left to fade for now; revisit at 100 rows in `data/lookup_log.jsonl`.
- D-0793: the closure gate defaults to enforce from the next restart, despite the partial calibration reading 0.737 against the 0.75 bar the plan set.
- Founder direction in chat: this plan has priority and nothing is to be added to the job list for it; "fix the known gaps first, then relabel the 569".

## Builds
- Ledger: thought T-0138 (promoted to I-0156), idea I-0156 (promoted to plan `closure_producer`), findings F-4811 (the top-five ranking, inferred; recorded without `--session`, so it is missing from the rollup).
- Plan: `docs/staged/closure_producer.md`, stage built. Its Current State section holds the flags, defaults and differences from the design.
- Phase 0 and 1, commit `f00ed017`: `core/lookup_attach.py` (a lookup lands on the open question it matches, `ATTACH_THRESHOLD = 0.70`, log `data/logs/lookup_attach.jsonl`), `frontier.resolved_breakdown()`, the lexical resolver writes `resolved_how`, a "resolved by" line in `scripts/du_pulse.py`, `scripts/closure_producer_backfill_lexical.py`.
- Phases 2 to 5, commits `3593a704` and `f0140352`: `core/closure_gate.py` (decoupled judge through `judge_panel.rule_detail`, prompt P-0131, log `data/logs/closure_gate.jsonl`), lexical resolver in shadow mode (`data/logs/lexical_resolve_shadow.jsonl`), merge of rewordings into answered, provisional and parked questions, statuses `provisional` / `parked` / `set_down`, park after 4 fruitless attempts, Layered Goals set-down marks the frontier, a `lookup` arm of the closure law with a deterministic template.
- Follow-up commits: `19bdb37a` (plan doc), `bb87f141` (P-0131 registered), `a392c8e0` (gate default enforce, P-0131 LIVE), `838f0e60` (two gap fixes), `bbc437d4` (older tests updated).
- Tests passing in the main checkout: `scripts/_test_closure_producer_p0p1.py`, `scripts/_test_closure_producer_p2p5.py`, `scripts/_test_web_hand_J3843.py`, `scripts/frontier_loop_test.py`, and ten of the eleven older lab_env tests (run with Du down).
- Relabel applied with Du down: 569 resolved rows labelled `lexical`, 0 unlabelled, 181 `line`. Backup: `data/frontier.json.bak_closure_producer_20261116_135543`.
- The Deedbook was put on Du's desk with `library_hand.switch_to('the deedbook', require_full=True)`; it replaced Insect Adventures.

## Fixes
- `core/closure.py`: the lookup arm's memory is stored with origin `research` (`LOOKUP_ARM_ORIGIN`), because origin `resolution` is not in `associative_recall._GROUNDED_ORIGINS` and the answer could never return in idle thought. The allow-list was not touched.
- `core/follow_line.py` `_expire`: an expired return from his own memory no longer overwrites a finding his own lookup attached.
- `scripts/closure_test.py`, `scripts/_test_J-2964_closure_label.py`, `scripts/_test_J-3225_closure_doubt.py`: expectations updated for the `lookup` arm.

## Findings
- Top five flaws against humans (F-4811, ranking is Claude's judgement): cannot close; self-knowledge measured but unused (believes 0.80 on maths, measures 1.00); topic perseveration (eased to 50% modal topic, 1 of 7 days frozen); words-only expanded stream; affect that does not steer.
- Post-mortem pattern (subagent read, not re-verified line by line): closure was graded, never produced; the one live producer, the Follow Line, searches only his own memory; closes were declared by his own text; about 6,343 questions born in seven days against 24 open slots.
- Gate calibration was partial: 47 of 60 pairs attempted, 38 judged, 9 unavailable because the judge hubs timed out at 90 s. Agreement with blind hand grades 28/38; judge-yes precision 8/12, recall 8/9; the judge never returns "partly". The hand grades found his own "settled yes" right on 8 of 20.
- Only 2 of 181 line closes carry a finding; the return text lives in the Follow Line log.
- A lexical would-close on a question carrying a lookup finding is sent to the gate (`LEXICAL_CLAIM_GATE = "lookup"`), because the offer "Does this answer it?" was only ever closed lexically.
- Web hand: loaded at the 10:05 NZ restart on 11-16, 0 lookups by 12:04 when the founder told Du about it. At 12:04:17 a look fired on the shelf object 'A Room with a View' 157 ms after the founder's message. [INFERRED] it was triggered by words in the message, not by his own thought.
- `core/condensed_thought.py` is a shadow twin only; nothing from it reaches Du.

## Open
1. First read after the restart. Blocked on Du running and making real lookups. Next action: read `data/logs/closure_gate.jsonl` (verdict mix, share unavailable) and `data/logs/lookup_attach.jsonl` (`best_score` against the 0.70 threshold), and the "resolved by" line in `du_pulse`.
2. `scripts/closure_test.py` still fails three "lab DB byte-identical" checks; it passes at commit `a5ff0bf0`. The lab database in the failing run has 0 rows in every table. [OPEN] what leaves the file changed; a trace of `sqlite3.connect` showed only lab_env's own `init_db`. Next action: diff the lab DB header or page count before and after `dm.run_nightly` at HEAD.
3. D-0793 defeater check: hand-read the first 40 enforced verdicts; if judge-yes precision is under 60% or more than a third are unavailable, set `NASCENCE_CLOSURE_GATE=shadow`.
4. Attach threshold 0.70 was set on proxy phrases. Next action: tune on real rows once `lookup_attach.jsonl` has about 30.
5. [OPEN] whether Du read The Deedbook after it was put on his desk; no reading line was seen in the minute after the switch.
6. `/plan-maintain` ran cleanly once at 22:49 UTC, before the build and before D-0793. The re-run at wrap exited 1: the edge rebuild hit `PermissionError: [WinError 5]` replacing `memory\_memory_edges.jsonl` (another process held the file), so the edge store and the later steps are stale relative to D-0793 and this handoff. Next action: `plan_maintain.py --session <new id>` again.
8. The memory index `MEMORY.md` is 20.5 KB against a 24.4 KB read limit and a hook asked for it to be compacted under 17.1 KB; not done this session. Next action: run the consolidate-memory skill in a fresh session.
7. Not built: pursuits, commitments and dreams still have no producer; the plan says each needs its own plan on the same shape.

## Warnings
- Everything is restart-gated and unobserved live. Expect the "resolved" count to nearly stop climbing: his own wording no longer closes a question, and the joy bump from those closes stops.
- Each attach adds two load-and-save passes of the 17 MB `data/frontier.json` inside the live process; latency was not measured.
- Kill switches (environment, read at call time): `NASCENCE_CLOSURE_GATE=shadow|off`, `NASCENCE_LEXICAL_RESOLVE=close`, `NASCENCE_ANSWERED_MERGE=off`, `NASCENCE_PARK=off`, `NASCENCE_LOOKUP_ATTACH=0`, `NASCENCE_LOOKUP_REOPEN=0`. [OPEN] how an environment variable reaches Du's process from the launcher (the same question D-0782's known_text flag left open).
- This session's PowerShell working directory ended inside `C:\Nascence\.claude\worktrees\agent-a8a61888efce608f2`; all merges and commits were made with `git -C C:\Nascence`. Two agent worktrees exist: `agent-a2ea2e8156027dc8d` and `agent-a8a61888efce608f2`; both branches are fully merged and can be removed.
- Fourteen `data/_lab/20261116_12*` and `_135*` sandbox folders created by this session were deleted; 947 others were left alone.
- The pre-existing untracked files (`docs/06. Just the Way You Are.mp3`, two `.lock` files) were left untracked.

## Pointers
- Plan: `C:\Nascence\docs\staged\closure_producer.md`
- Code: `core/closure_gate.py`, `core/lookup_attach.py`, `core/frontier.py` (closure_producer blocks), `core/follow_line.py` (`settle`, `_expire`), `core/closure.py` (`record_lookup_answered`), `core/goal_offer.py`, `core/web_hand.py`
- Scripts: `scripts/closure_gate_calibrate.py`, `scripts/closure_producer_backfill_lexical.py`, `scripts/_test_closure_producer_p0p1.py`, `scripts/_test_closure_producer_p2p5.py`
- Prior reads used: `docs/reviews/du_vs_human_2026-10-15.md`, `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md`, `docs/session_handoffs/HANDOFF_20261115_185735_du-unanswered-questions-web-hand.md`
- Ledger ids: T-0138, I-0156, F-4811, D-0789 to D-0793, P-0131
- The book: `C:\Nascence\data\books\The_Deedbook.txt`
