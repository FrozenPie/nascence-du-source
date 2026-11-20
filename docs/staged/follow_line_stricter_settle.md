# Follow Line: stricter settle (proposal, staged, J-4029 / F-4720)

Status: BUILT, flag-OFF shadow (J-4056: settle_overlap() in core/follow_line.py, SETTLE_OVERLAP_SHADOW=False). Offline replay done (J-4279); flipping the flag awaits a founder ruling.

```plan-state
stage: built
phase: flag-OFF shadow: J-4056 built settle_overlap() in core/follow_line.py, SETTLE_OVERLAP_SHADOW=False
verified: 2026-11-20
next: offline replay vs 48 hand grades DONE (J-4279, F-5087: 0.15 rejects 21/23 hand-no, keeps 12/14 hand-yes); founder ruling on flipping SETTLE_OVERLAP_SHADOW next
```


## Problem
A line closes (resolved=yes, closure_how=ok) when Du's own idle-thought JSON self-reports settled=yes. Hand grading J-4029: about 48% of
48 closures (Wilson 34-62%) do not answer or engage the question; 33% of sampled logged-yes rows likewise. See docs/lab/J-4029_hand_grade_results.md.

## Proposal (flag-OFF, shadow first)
1. Content-overlap gate: closure only if the thought shares content terms with the question text or its returned text
   (lemmatised noun/verb overlap >= threshold, stoplist for tide/cat/silence etc. recurring set pieces). Else log would_not_close, keep line open.
2. Optional second judge (different family from the generator, e.g. gemma4 on a judge hub) used only in shadow to compare against the overlap gate; not on the hot path.
3. Shadow row fields: overlap score, gate verdict, original verdict. Promotion read: against the 48 hand grades (target: gate rejects >= 70% of the 23 hand-no
   while keeping >= 80% of the 14 hand-yes).
4. Check the prompt registry (follow_line settle prompt) if any prompt text changes.

## Open question for the founder
Is a falsely closed line costly (line dropped) or cheap? Decide only if the build job is spawned.

## Current State
- **2026-11-18** (F-5087): J-4279 offline replay: settle_overlap meets both promotion criteria at thresholds 0.13-0.16 (0.15: rejects 21/23 hand-no, keeps 12/14 hand-yes); in-sample, narrow band. Script scripts/settle_overlap_replay_J4279.py.

