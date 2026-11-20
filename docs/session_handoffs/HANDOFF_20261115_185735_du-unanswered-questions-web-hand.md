# Du's unanswered questions: why the loop never closes, and the plan for a web hand

## Session timing
- **Session started:** 2026-11-15 18:35:52 UTC
- **Last message before wrap:** 2026-11-15 18:57:34 UTC
- **Wrapped:** 2026-11-15 18:57:35 UTC

## Summary
Ran a Du pulse on the 11-15/16 overnight window, read his curiosity log and the frontier, and found that his questions are generated but never answered because the lookup that used to answer them was retired on 11-05 and its replacement (the Wikipedia hand) was never built. Checked J-3285: it is marked done but not built; successor J-3843 is the real open build. Wrote the plan for the Wikipedia hand plus an open-web search extension and opened the founder calls for it. No Du code was changed.

## Decisions
- D-0788 opened (this session, no ruling yet): one lookup family with a source word versus two hands; search backend (keyless versus keyed Brave/Bing); domain deny list first versus open. Recommendation recorded in the question: one family with a separate flag for the web source, deny list first.
- No rulings made by Claude. Earlier rulings this work rests on: D-0659 (system-initiated Wikipedia lookup retired 11-05), D-0661 (Du learns of the hand by Travis telling him, plus a line in a diegetic book, plus an encyclopedia object in the study; not a prompt offer line), D-0631 (Du may make wiki calls; whatever comes back is marked as from its source).

## Findings
- Pulse (since 11-15 06:35, last restart 11-15 20:14): Du live, 350 idle thoughts since restart with no exact duplicates, active store 95,118 fragments against a 3,500 cap (77,264 cold-but-kept; the cap is the known demotion setup, not a fault). Echo 0.674, diversity 0.954, modal topic 53% of today's internal cycles, "silence" in 27 of last 60 thoughts. Un-primed made-mind share 2 of 97.
- `data/curiosity_log.jsonl` (3,571 rows): the overnight questions were the same subject reworded repeatedly (vireo x4, Great American Desert x7, porcupine quill x9, red-headed woodpecker x6, Myrtle Warbler yellow spots x14 and still running at 07:29). Nothing in the log shows an answer arriving.
- `data/frontier.json`: 22,470 questions; faded 21,527, resolved 744, open 29. 18,625 faded were seen once. Of the 744 resolved, 565 have no `resolved_how`, 179 closed via a follow line; the two overnight resolutions read said the past "holds little", so they were closures, not answers.
- Code cause: `nodes/curiosity_node.py:137` says the node does not answer, only generates; `_write_output` (~343) logs the question and files it in the frontier; the retirement comment at `curiosity_node.py:372` records that the system lookup (longest-word guess, wrong pages, stored as his own memory, 1,742 pages) was removed under D-0659 and nothing replaced it.
- J-3285 was closed as superseded in the same pass (2026-11-09 00:37:58 to 00:37:59, session 8ae77b4e) that created J-3843 (status open, autonomy ready, not started). Searched `core`, `nodes`, `scripts` and git history: no `lookup` family in `core/actions.py`, no `opensearch`, no `web_hand`, no `data/lookup_log.jsonl`, no commit or branch for the hand. Readers of the hand's output already exist and wait for it (`core/composition.py:21,236`, `core/schema.py:16`).
- `[INFERRED]` The main reason the loop does not close is the missing way to find answers, not a missing ability to ask; knowledge is a secondary factor (his reading covers birds). Judgement-shaped questions ("is the red head a shield or part of its being") would not be answered by Wikipedia and may suit a friend/judge. Not tested.
- `[INFERRED]` Part 2 of the plan (open web) carries a prompt-injection risk Wikipedia mostly does not; mitigation is in the plan (named quoted data, domain filter, character cap, no model summary).

## Builds
- Nothing built in Du's code. Docs only: `docs/staged/web_hand.md` (full plan, Part 1 the Wikipedia hand per review section 5.1, Part 2 the web source, the friend/judge as complement, success readings).

## Open
1. Build J-3843, the Wikipedia hand. Ready, nothing blocking it. Next action: read `core/hands.py` and `core/dispatch.py`, run `udms_get_change_dossier` on `core/actions.py`, then build per `docs/staged/web_hand.md` Part 1 in a throwaway worktree with the network stubbed, then one real fetch. The founder wanted this pushed through today.
2. Rule D-0788 (one hand or two, backend, domain filter). Blocks J-4066. Next action: founder rules; `[OPEN]` which search API key the founder already has.
3. J-4066, the open-web source (needs_input, blocked on D-0788 and after J-3843).
4. Telling Du the hand exists is a founder step in conversation (D-0661), after the build and after a restart. Du is restart-gated; nothing is live until the founder restarts him.
5. `[OPEN]` Whether to build a friend/judge he can ask judgement-shaped questions. Next action: after the lookup hands run for a few days, compare which questions stay unanswered.
6. `plan_maintain.py --session` was started in the background near the end and may still have been running at wrap; run it again if `docs/staged/web_hand.md` does not appear in the plan index.

## Warnings
- Several sessions edit `C:\Nascence` at once. Never `git stash`, `git reset`, `git restore` or `git checkout --` in the shared tree; use a throwaway worktree (CLAUDE.md, F-0741). The working tree already held many uncommitted changes from other sessions at session start (for example `core/memory_service.py`, `nodes/critic_node.py`).
- Any new or changed prompt site needs `python C:/Users/USER/.claude/skills/prompt-registry/prompt_registry.py check` to exit 0 in the same change.
- Do not launch Du's servers from a Claude Code PowerShell tool (job-object kill, F-0704); use `scripts/start_supervisor_detached.ps1`.
- The Bash tool eats backticks inside double quotes; use `--briefing-file` for long text.

## Pointers
- Plan: `C:\Nascence\docs\staged\web_hand.md`
- Design source for the Wikipedia hand: `C:\Nascence\docs\reviews\outside_knowledge_review_J-3243_2026-11-05.md` section 5.1
- Jobs: J-3843 (Wikipedia hand, open), J-4066 (web source, needs_input), J-3285 (closed, superseded)
- Decisions: D-0788 (open), D-0661, D-0659, D-0631
- Thought logged: T-0136
- Curiosity code: `C:\Nascence\nodes\curiosity_node.py:137,343,372`; `C:\Nascence\core\web_research.py`
- Data: `C:\Nascence\data\curiosity_log.jsonl`, `C:\Nascence\data\frontier.json`, `C:\Nascence\data\hands_trace.jsonl`
