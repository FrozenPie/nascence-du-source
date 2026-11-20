# Du's spider-web thread: why he never looked it up, and the lookup nudge (J-4075)

## Session timing
- **Session started:** 2026-11-16 01:56:28 UTC
- **Last message before wrap:** 2026-11-16 02:17:15 UTC
- **Wrapped:** 2026-11-16 02:17:16 UTC

## Summary
Travis pasted a Du log excerpt (14:38 to 14:42 local) about spider webs and asked whether the chain was good and whether he got answers. The answer was no: evidence found nothing, so J-4075 was run to make an empty-evidence factual question point Du at his lookup hand. That was built as one sentence in the follow-line return, committed as `a2c2827e`, and is not live until Du restarts.

## Decisions
- D-0794 (ruled by travis, via a direct question in this session): a system nudge is allowed for this one case, overriding D-0661 option (d), the earlier "no offer line in his prompt" ruling. He chose it over a diegetic pointer (encyclopedia object, About You v3) and over telling Du in chat. The 14-day defeater on D-0794 was drafted by Claude and is NOT confirmed by Travis.

## Builds
- `core/follow_line.py`: `lookup_nudge()` plus a `lookup` item in `render()`, wired in `run()` (cargo key `lookup_nudge`, also logged under `stops.lookup_nudge` in `would_return` rows of `data/logs/follow_line_shadow.jsonl`). Default mode live; `NASCENCE_LOOKUP_NUDGE=shadow|off` overrides. The sentence is "No book or memory of yours covers it. You can look a thing up for yourself: say whether you ask Wikipedia or the web."
- `scripts/_test_J-4075_lookup_nudge.py`: 13 of 13 checks pass. `scripts/follow_line_test.py` still passes 82 checks; only its live-store canary fails.
- Commit `a2c2827e` holds the code, the test and five ledgers.

## Findings
- F-4821 (verified): before J-4075 nothing routed an empty-evidence factual question to the lookup hand. "Settled partly" in follow_line only records the part of the question Du's own thought said it answered; it is not a grounds verdict. The hand was live from his 14:01 boot (pid 38068, after `core/web_hand.py` mtime 08:18) but had never fired, since `data/lookup_log.jsonl` does not exist.
- The spider thread itself (T-0141): his questions got sharper (generic, then high-wind predation, then redundancy vs elasticity, then "grain versus fear"), but no facts were gained. His library is Fabre's Life of the Spider, which does not cover it. The 14:42 thought stored raw (`deliberation_skipped_no_emissary`).
- [INFERRED] The canary failure in `scripts/follow_line_test.py` comes from the live Du writing to its logs during the run, not from this change; it flipped between one and two failing canary lines across runs.

## Open
1. Restart Du so the nudge loads. Blocked on founder; no job. Next action: restart, then check `data/logs/follow_line_shadow.jsonl` for `stops.lookup_nudge`.
2. J-4077: read the first fires after restart (did he look up within 30 minutes, was the question factual, did the web-hand parser's `_NOT_THE_WEB` spider/web filter reject a spider question). Gated on 4 live hours.
3. J-4076: were the redundancy-vs-elasticity and high-wind questions ever answered later? Gated on 6 live hours.
4. Confirm or replace the defeater on D-0794 (`decide.py show D-0794`).
5. [OPEN] Whether D-0789's automatic attach lands a lookup result on the spider question. Not tested end to end; J-4077 should check `data/logs/lookup_attach.jsonl`.

## Warnings
- The working tree holds other sessions' uncommitted work (humanity scorecard files, `docs/lab/J-3325_data`, `docs/lab/J-4074_data`, T-0139 scripts, an mp3, lock files). Commit by explicit path only; do not stash or reset.
- The nudge deliberately breaks the "nothing hints" law for one case. If Du starts treating the line as an instruction, D-0794's defeater applies.

## Pointers
- `C:\Nascence\core\follow_line.py` (search `lookup_nudge`)
- `C:\Nascence\core\web_hand.py`, `core\lookup_attach.py`, `core\actions.py` line 655 (the `lookup` hand)
- `C:\Nascence\docs\guidelines\du_hands_manual.md` (how the hand is described to him)
- `C:\Nascence\data\nascence.log` 14:32 to 14:55 on 2026-11-16 (the thread)
