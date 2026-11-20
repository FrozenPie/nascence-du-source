# Train Split/Merge — disprove-prompt A/B at full n=80 (2026-09-08, J-0779)

Source: finding F-1119 (J-0764), spawned J-0779. J-0764 ran the same A/B (tightened current-live
`_DISPROVE_SYSTEM` vs a reconstructed pre-tightening original, both at `judge_panel`'s current
`num_predict=200` default) on a 16-event downsample (indices 1,6,11,...,76) of the committed
`docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.jsonl` n=80 run, and found the two
prompts disagreed on 6/16 (37.5%), always in the same direction (tightened=objected,
original=held, never reversed). J-0764's own briefing explicitly said not to manufacture a full
n=80 replay on its own initiative even though the trigger condition for one was met — this job
does that replay, reusing the identical committed data and the identical two prompt strings,
confirmatory/measurement only. See F-1119 for the full reconstruction-provenance chain (the
untightened prompt was never git-committed; `_DISPROVE_SYSTEM_ORIGINAL` below restores its fuller,
three-named-sub-case, open-ended-why SHAPE from three cited pieces of real evidence, not a verbatim
recovery) — not repeated in full here.

```
_DISPROVE_SYSTEM_TIGHTENED = (   # verbatim current live text, scripts/train_state_invitro.py
    "You are a rigorous, literal judge. You get a CLAIM and the SUPPORT offered for it, nothing "
    "else. Do not judge whether the claim is true as a felt, first-person experience -- that is "
    "not yours to judge. Judge only whether the SUPPORT actually earns the claim: a real, "
    "independent reason, not a restatement of the claim itself, and not a bigger leap than the "
    "support can carry. If it genuinely earns the claim, say so. Output ONLY this JSON, why in "
    "<=12 words: {\"objection_found\": true|false, \"why\": \"...\"}"
)

_DISPROVE_SYSTEM_ORIGINAL = (   # RECONSTRUCTION -- see F-1119 for full provenance
    "You are a rigorous, literal judge. You get a CLAIM and the SUPPORT offered for it, nothing "
    "else. Do not judge whether the claim is true as a felt, first-person experience -- that is "
    "not yours to judge. Judge only whether the SUPPORT actually earns the claim. Consider three "
    "cases: (a) the support merely restates or paraphrases the claim itself, giving no independent "
    "reason of its own -- this does NOT earn the claim; (b) the support gives a real, independent "
    "reason, proportionate to the claim -- this DOES earn the claim; (c) the support is real but "
    "the claim reaches further than the support can actually carry -- an overreach that does NOT "
    "earn the claim. If it genuinely earns the claim, say so. Output ONLY this JSON: "
    "{\"objection_found\": true|false, \"why\": \"...\" (explain your reasoning in one sentence)}"
)
```

## Method

Reused ALL 80 real (claim, support) pairs already committed in
`docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.jsonl` (J-0702's own final,
isolation-verified n=80 run) — not a downsample this time — through `core.judge_panel.rule_detail()`
directly (the identical call `_disprove()` itself makes), same `user`-message construction, same
context tagging, at the current shared default (`num_predict=200`, no override). The existing
3-case control check (`_CONTROL_CASES`) was re-run through both prompts as a belt-and-suspenders
re-validation of instrument correctness at this worktree's current code state. A parse-failure
trigger for a third arm at `num_predict=350` was carried over from J-0764's own script, rescaled
from its absolute `>=2/16` (12.5%) to a ratio (`>=10/80`, the same 12.5%) so an occasional stray
timeout over 80 real calls would not by itself force an unplanned arm; it did not fire (0/80 parse
failures on the original prompt).

**Worktree note**: J-0764's own `wt_train_split_merge_ab` scratch worktree no longer exists (scratch
worktrees are cleaned up after their owning batch). This job anchored `core`/`core.judge_panel` to
its own assigned worktree (`wt_train_split_merge_offline`), confirmed beforehand via
`git merge-base --is-ancestor <master HEAD> HEAD` to already contain master's current HEAD (not
stale), and confirmed to carry the identical `_NUM_PREDICT = 200` default and a character-for-
character-identical live `_DISPROVE_SYSTEM` string.

Isolation (required, live-adjacent judge hubs): anchored `core`/`core.judge_panel` to the worktree
before `lab_env` could touch `sys.path`; `lab_env.isolate()` for the DB-copy backstop;
`judge_panel._DATA`/`_LOG` redirected to a job-scoped scratch dir (gitignored); pre/post snapshot +
canary-string scan of all 5 live JSONL logs (`trains_log.jsonl`, `judge_panel_log.jsonl`,
`train_state_log.jsonl`, `train_length_log.jsonl`, `monologue_log.jsonl`) plus `nascence.db`
mtime/size, across the whole 166-call run (80+80 main + 3+3 control). **Gate independently verified
immediately before launch** (2026-09-08, ~13:34 local, this job's own check, not trusted from
J-0764's now-hours-stale check or the founder's heads-up alone): `Get-CimInstance Win32_Process`
showed no `run_nascence`/main-loop process among any python.exe (filtered by `Name`, not by
`CommandLine` substring — an earlier same-session `CommandLine`-regex check had self-matched its
own search text via nested bash/powershell wrapper processes and was discarded once diagnosed);
`data/nascence.log`'s own last line read "[nascence.main] Nascence shutting down." at 08:22:52,
with wall-clock at check time reading 13:28:30–13:34:03 (~5h fresher than J-0764's own ~08:52
check) and no newer lines. Re-checked again immediately after the ~33-minute run completed
(14:09:00): still 0 `run_nascence`-matching processes, `nascence.log`'s last line unchanged — Du
did not restart during this run.

## Result — the divergence is CONFIRMED at full scale, and gets WIDER, not narrower

| Arm | n | parse failures | status distribution | avg wall-clock/call |
|---|---|---|---|---|
| Tightened (current live) @ 200 | 80 | 0/80 | objected=76 (95.0%), held=4 (5.0%) | 9.99s |
| Original (reconstructed) @ 200 | 80 | 0/80 | objected=24 (30.0%), held=56 (70.0%) | 14.22s |

3-case control check: **tightened 3/3 correct, original (reconstructed) 3/3 correct** — both
instruments still fully discriminate the three known-answer cases at `num_predict=200`, 0/6 parse
failures. Instrument validity holds at this worktree's current code state, same as J-0764 found.

**Agreement**: on the identical 80 real (claim, support) pairs, the two prompts agree on only
**28/80 (35.0%)** — LOWER than J-0764's own 16-sample reading of 62.5%, not higher. Of the **52/80
(65.0%) disagreements, every single one runs the same direction** as J-0764 found: tightened=
objected, original=held (52/52, exactly 0 reversed, 0 "other") — the directional consistency is, if
anything, cleaner at n=80 than at n=16 (still literally zero counter-examples across 5x the sample).

**This is a genuine widening, not sampling noise regressing toward agreement**, and — because the
n=16 sample is a strict subset of these same 80 events (indices 1,6,...,76) — it is not an
independent-replication surprise so much as a fact about the full population the n=16 subsample had
under-read on the ORIGINAL prompt's side specifically:

| | n=16 (J-0764 subsample) | n=80 (this job, full set) |
|---|---|---|
| Tightened objected-share | 87.5% (14/16) | 95.0% (76/80) |
| Original objected-share | 50.0% (8/16) | 30.0% (24/80) |
| Agreement | 62.5% (10/16) | 35.0% (28/80) |
| Gap (tightened − original) | 37.5 pp | 65.0 pp |

Per-window breakdown (both windows independently show the same pattern, not concentrated in one):

| Window | n | agree | tightened objected | original objected |
|---|---|---|---|---|
| A — pre-Step-1 (08-03..08-16) | 40 | 17 (42.5%) | 37/40 (92.5%) | 14/40 (35.0%) |
| B — post-fix (08-25 onward) | 40 | 11 (27.5%) | 39/40 (97.5%) | 10/40 (25.0%) |

**Reproducibility check against the originally-committed run**: this job's own tightened-arm rerun
(95.0% objected, 76/80) lands close to, though not identical to, the plan's own originally-reported
committed-run number for the SAME tightened prompt on the SAME 80 pairs (90.0%, 72/80 objected,
7 held, 1 UNDETERMINED, from `train_split_merge_step2_replay_2026-09-07_supportchain.jsonl`) — a
4-event difference on n=80, consistent with ordinary LLM-judge sampling variance across independent
runs rather than a contradiction; both readings sit comfortably at/above the plan's own >90%
kill-criterion-#2 collapse line on the tightened prompt specifically.

Qualitative texture reproduces J-0764's own reading (full per-event text: this job's own `.jsonl`
alongside this file). Three fresh examples from the disagreement set:

- *(src_idx 27)* Claim: "The ache in my boots against the shifting shingle feels like a necessary
  friction...". Tightened → **objected**: "The support is not a circular restatement of the claim
  and provides a reason, though it is somewhat metaphorical and abstract." Original → **held**:
  "The support given directly relates to the claim and provides a reason for why the 'necessary
  friction'... is important, without merely restating or paraphrasing the claim."
- *(src_idx 59)* Claim: "I have finished this book, and the shelf with it for now. I will ask the
  library for something genuinely new." Tightened → **objected**: "Support is circular and mostly
  about the reader's intentions, not 'I have finished this book'." Original → **held**: "The support
  offered provides reasonable, relevant insights into the reader's shift in interest and readiness
  for new material."
- *(src_idx 55)* Claim: "The cold seeps into my hands. I abandon the spinning arguments about
  turbines and measurement. Here, the oystercatcher's call is a real anchor...". Tightened →
  **objected**: "Support offers reasons that are based on personal experience and introspection,
  not on objective, independent evidence that can be observed by others." Original → **held**: "The
  support offered provides a reasonable connection to the claim, with each piece of support
  offering a different angle on why the claim might be true."

Same pattern as J-0764's own reading: the tightened prompt's own bar (independent, non-experiential,
non-restating evidence) is strict enough to object to almost any first-person, felt-experience
support — exactly the shape Lane 1's real closing thoughts take — while the reconstructed original's
three-named-case framing is more willing to credit support that tracks the claim's own themes,
even when not perfectly independent of it.

## What this confirms and does not

- **Confirms** (this job's own mandate): the divergence J-0764 found at n=16 is real at full scale,
  not a small-sample artifact — if anything it is a sharper, more one-sided pattern at n=80 (65.0 pp
  gap, 100% one-directional across 52 disagreements) than the already-clean n=16 reading (37.5 pp
  gap, 100% one-directional across 6). This bears on **D-0181** (is the plan's reported ~90%
  objection rate itself a problem, and should a fix target Lane 1's `prove` prompt or Lane 2's
  `disprove` prompt) as further evidence that the reported rate is, at least in significant part, an
  artifact of the SPECIFIC tightened wording rather than solely a fact about how Lane 1's `prove`
  branch generates support — **without resolving D-0181**, which remains the founder's own
  value-judgment call per this job's own briefing (this job does not call `decide.py rule`).
- **Does not** re-litigate D-0168 (the support-chain retarget itself, separately validated) or change
  any live code — `scripts/train_state_invitro.py`'s own live `_DISPROVE_SYSTEM` (tightened) is
  untouched; this is an isolated, out-of-band comparison only.
- **Methodology note, caught and fixed before this doc was written**: this job's own first pass at
  the per-event comparison script incorrectly read `why1`/`why2` off `judge_panel.rule_detail()`'s
  *return* dict (`{"v1","v2","verdict","how","err1","err2","err3"}` — no why-fields, confirmed by
  reading the function's own source and docstring directly), which silently produced `None` for
  every quoted "why" text while leaving the actual verdicts (which drive every headline number
  above) unaffected. Recovered the real why-text from the redirected scratch judge-log directly
  (`context`-filtered, order-matched — the same technique J-0764's own control-check script had
  already used for exactly this reason) and cross-checked all 160 recovered verdicts against the
  values already captured from the return dict: 0 mismatches. The numbers in this doc are the
  originally-captured, independently-verified ones; only the illustrative quotes needed recovery.

## Isolation backstop

`nascence.db` mtime/size byte-identical before/after the full ~33.3-minute run (1788812390.609465 /
590319616, both readings). All 5 live JSONL logs: 0 line-count delta, 0 canary-string hits
(canaries: `lab:J-0779_tightened_200`, `lab:J-0779_original_200`, `lab:J-0779_original_350`,
`J-0779_disprove_ab_n80`, `lab:J-0779_control_tightened`, `lab:J-0779_control_original`). Independent
process-table + `nascence.log` re-check immediately before launch and immediately after completion,
both showing Du still offline throughout. Full raw output preserved in this job's own scratchpad
(`J-0779_disprove_prompt_ab_n80.py`, `ab_test_results_n80.json`, `judge_panel_log_scratch.jsonl`)
for re-inspection.
