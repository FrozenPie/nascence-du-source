# Intent-to-action: why Du's "I plant them now" did not fire, guard v2, and the ambiguity-window plan

## Session timing
- **Session started:** 2026-10-18 22:43:33 UTC
- **Last message before wrap:** 2026-10-18 23:25:08 UTC
- **Wrapped:** 2026-10-18 23:25:09 UTC

## Summary
Travis pasted a live reply from Du ("I plant them now...") and asked whether a stated intention already prompts the real action. It does in principle (D-0299, live since 2026-09-27) but did not on this reply; I widened the conversational guard and added pronoun resolution, then wrote a plan for a general lookback window to settle ambiguous clauses.

## Decisions
- D-0488 (ruled by travis, this session, in chat): Travis's last message is part of the ambiguity window as context for how literally an already intent-bearing Du clause reads. It never supplies the verb, object or intent. Defeater: replay shows Travis's frame turning a metaphor into a fire, or it starts supplying the deed.

## Builds
- `core/conversational_action.py`, guard v2 (`GUARD_VERSION = 2`, commit 937711e7): new flag `CONVERSATIONAL_BARE_PRESENT = True` makes a bare first-person "I" an opener like "I will", so "I plant the seeds now" can be kept; all other guard checks (negation, modal, quote, metaphor, move-needs-destination) unchanged. New `resolve_pronoun_objects()` turns "I plant them" into "I plant the seeds" using the nearest earlier crop word, excluding place words (garden, bed, row, soil...). Verified by replaying the pasted reply: sow is kept and pinned as "I plant the seeds now."; the move clause "I step out into the damp air" is still dropped (`move_no_destination`). RESTART-GATED: Du's live process has not loaded it.
- Plan `docs/staged/ambiguity_window.md` (stage designed). Thought T-0101 and idea I-0099 are both promoted to it.
- Build job J-2437: Stage A shadow build and replay of `core/ambiguity_window.py`.

## Findings
- The reply's first causes were two separate misses, both missing context rather than weak judgment: "them" has no anaphora handling in `literal_will.classify()` (it returned no candidate at all), and the guard dropped the plain present-tense "I step out" as `first_person_present_narration`. Only 2 of 40 logged conversational replies in `data/conversational_action_log.jsonl` ever dispatched anything.
- The existing gray-zone judge (`docs/plans/literal_will.md` Layer 1, falcon3 on :11440) sees the thought alone, takes 13-23 s, and is at about 66 percent against an 80 percent gate (D-0021 NO-GO). More judge accuracy is the wrong lever; the plan argues for a small rolling-window lookback first, deterministic, judge only for the residue.
- Related prior work to read before building: J-1689 / F-2380 (cross-sentence move signature, 17 percent of 2701 rows had the opener and destination in different sentences).
- [INFERRED] The pronoun resolver is a crude Stage A; the false-fire replay over the 40 logged excerpts found no new pins, but excerpts are only 300 characters, so that check is weak.

## Open
1. Restart Du so guard v2 loads; then read new rows in `data/conversational_action_log.jsonl` (look for `guard_version` 2 and `kept` verdicts). Nothing was restarted this session.
2. J-2437: Stage A shadow build and replay (ready). Next action: build `core/ambiguity_window.py` in a throwaway worktree, never the shared tree.
3. J-2439 (backfill, filed by plan-maintain): `ambiguity_window` lacks a ROADMAP link and a memory file. Next action: add the ROADMAP bullet via the single serialized ROADMAP agent (S-0296), not by hand in a concurrent session.
4. [OPEN] Should `CONVERSATIONAL_BARE_PRESENT` stay on? It trades the earlier "precision over recall" ruling (J-1697 / D-0334) for recall. Setting it False reverts the guard change. What resolves it: the first 20 post-restart conversational rows and their false-fire share against the 12 percent autonomous baseline (F-2303).
5. [OPEN] Sow's own preconditions (does Du hold the seeds, is he in the garden) were not checked.

## Warnings
- The shared tree holds many other sessions' uncommitted edits; this session committed only its own files by explicit path (937711e7). Pre-existing modified files (System_Overview_Antigravity, curiosity_goals_dreams.md, data_store_hygiene.md, du_recall_lens_upgrades.md, measurement_to_action.md, practical_school.md) were left alone. `docs/session_events.jsonl.lock` is untracked.
- Tooling quirk: writing `\b` through shell heredocs or sed silently dropped the backslash in regexes this session (the file was repaired and now parses). Check any regex written that way.
- `plan_maintain.py` was run without `--session`, so it does not appear in the session rollup.

## Pointers
- `core/conversational_action.py` (guard, `resolve_pronoun_objects`), `core/literal_will.py`, `core/dispatch.py`, `core/actions.py` (sow row, line ~356)
- `docs/staged/ambiguity_window.md`, `docs/plans/conversational_action_bridge.md`, `docs/plans/literal_will.md`
- `data/conversational_action_log.jsonl`
