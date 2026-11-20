# self_interrogation — folded history


---

# History folded on 2026-09-27 from `docs\plans\self_interrogation.md` (plan-compact, 2 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py self_interrogation`._

## Current State update (2026-08-24, J-0164 — F-0164)

**Question 2's counterfactual harness is now built and has produced its first real (partial) read.**
`scripts/self_interrogation_counterfactual.py` — read-only, writes only to
`data/lab/self_interrogation_counterfactual/` and its own report, never wired into live behavior —
joins each fired shadow-log row to its source thought in `train_state_log.jsonl` (matched on text
prefix + ts within 10s; unique match, no false positives found in spot checks) and asks a SECOND,
independent `judge_panel.rule_detail` call (never Du, never the original genuine-grader) whether Du's
real next thought shows any sign of being affected by the reflection's concern.

**First read: 18/32 fires processed, then stopped.** Not because the harness failed, but because the
CPU-tier judge hubs are under heavy contention tonight — a system-wide issue independently found and
already tracked as **J-0191/F-0162** (JUDGE_1/gemma4:12b/:11439 timed out on 10/16 attempted calls in
this run alone, 0/16 for JUDGE_2/falcon3:7b/:11440 — this session's numbers corroborate, not duplicate,
that finding). Of the 18: 2 unmatched (no train_state_log row found for those two specific fires —
verified as a real data gap via direct substring search, not a harness bug), 10 judge-unavailable
(the contention above), and **6 reached a real verdict**: 4 agreed "not affected", 2 (both
`genuine=True`) split with no tiebreak.

**Net: question 2 still has no decisive answer yet — but for a new reason.** The genuine=True
population (the one this question actually cares about) has **0/2 decisive verdicts** in this first
partial read, purely because both available genuine=True fires hit judge splits, not because the
signal points either way. This is real progress (the tautology F-0071 identified is broken — the
harness can now, in principle, produce a real answer) but not yet an answer. **J-0192** spawned to
finish the remaining ~14 fires once judge-hub contention eases; that read is what D-0031's first
defeater clause is waiting on. D-0031 remains open — its second clause (post-fix genuine-rate n
reaching ~30-50 resolved fires) is untouched by this job and still thin (n=10 post-fix per the
2026-08-24 entry above).

## Current State update (2026-08-24, J-0192 — F-0186)

**Question 2 now has a decisive, non-tautological answer.** J-0192 re-ran
`scripts/self_interrogation_counterfactual.py` (idempotent continuation) during a genuinely quieter
judge-hub window (confirmed against `data/judge_panel_log.jsonl`: 0/10 unavailable in the 10 calls
immediately preceding the run vs. 31/50 unavailable across the broader recent window) and it
completed the full sweep cleanly: **32/32 shadow-log fires processed** (up from 18/32).

The **genuine=True** bucket — the population this question actually cares about — went from 0/2
decisive verdicts to **9/17 decisive** (`agreed` or `tiebreak`; the rest are 2 `split_no_tiebreak`,
4 `unavailable`, 2 `unmatched`). Of those 9 decisive verdicts, **only 1 shows the next real thought
step affected by the reflection's concern; 8/9 (89%) show no detectable effect.** Full breakdown in
the regenerated `docs/lab/self_interrogation_counterfactual_report.md`.

**Reading this:** even judge-confirmed-**genuine** self-interrogations essentially never visibly move
Du's next real thought — an 11% affected rate on the one population where an effect would matter most.
This empirically corroborates F-0071's structural inference (fire-and-forget wiring means nothing
downstream reads the reflection) rather than assuming it by construction, which is exactly the gap
this harness (J-0164) was built to close. It does **not** contradict the favorable genuine-rate trend
(F-0070) — those are two different questions (is the reflection itself specific/genuine, vs. does it
move anything downstream) and this read answers only the second.

**D-0031 status:** its first defeater clause ("J-0164's counterfactual harness produces its first real
read") is now fully satisfied — this is that read, not a partial one. Its **second clause** (post-fix
genuine-rate n reaching ~30-50 resolved fires, a different data channel from this counterfactual read)
remains untouched by this job and is still thin. **D-0031 therefore stays open** — recorded as
progress toward it (F-0186 links to D-0031), not a ruling. A founder call is still needed on whether
this near-zero downstream-effect signal, combined with the still-thin genuine-rate n, is enough on its
own to decide Phase 1 either way, or whether the second clause should still be waited on.
