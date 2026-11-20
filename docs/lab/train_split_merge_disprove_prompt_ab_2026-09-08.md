# Train Split/Merge — disprove-prompt A/B: was the tightening a stopgap or a real improvement? (2026-09-08, J-0764)

Source: finding F-1095 (J-0718), spawned J-0764. Question: J-0702's `_DISPROVE_SYSTEM` (the
support-chain disprove framing, D-0168) was TIGHTENED same-day after its first, fuller attempt hit
~50% parse failures against `core/judge_panel.py`'s then-live `num_predict=80` ceiling (F-1034/
F-1035). That ceiling has since moved: J-0693/F-1014 raised the shared default 80→200 (merged to
master before either of J-0702's own commits), and J-0718/F-1035 added an explicit per-call
override on top of that. Neither had been tested against the ORIGINAL, untightened prompt. This
job does that test.

## Reconstruction note — read before trusting the "original" prompt text below

The literal untightened prompt string was **never git-committed**. `git log --all --oneline --
scripts/train_state_invitro.py` shows only one commit for the whole retarget+tightening arc
(`95f1533`); its parent (`f7b3d47`) predates the D-0168 retarget entirely and still carries the
OLD, pre-D-0168 **claim-only** framing ("You are given a single CLAIM and NOTHING else..."), not
the untightened SUPPORT-CHAIN framing this job needs — confirmed by reading `f7b3d47`'s own
`_DISPROVE_SYSTEM` directly. The untightened support-chain prompt existed only as an in-worktree
edit during J-0702's own session, overwritten before that session's single commit landed.

`_DISPROVE_SYSTEM_ORIGINAL` below is therefore a **reconstruction**, built from three pieces of
real evidence: (1) the current tightened prompt's own in-file comment
(`scripts/train_state_invitro.py` ~L256-268), which explicitly names what was removed — "dropped
the enumerated sub-cases (folded into one clause) and capped 'why' at <=12 words"; (2) F-1034/
F-1035's own claim text ("a longer, more elaborate system prompt (asking the judge to weigh three
named sub-cases and write a fuller 'why')"); (3) the `_CONTROL_CASES` three-category structure
already in the file (circular / genuine / overreach), built the same day for the retargeted
framing — the best available proxy for what the three sub-cases distinguished. The old (pre-D-0168)
claim-only prompt at `f7b3d47` also corroborates the "one sentence" (uncapped) why-field shape
independently. This restores the same semantic target in its fuller, pre-tightening SHAPE, not a
verbatim recovery — flagged here and in the finding, not just asserted once.

```
_DISPROVE_SYSTEM_ORIGINAL = (
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

Rather than re-running `_prove()` against Lane 1's live hot lane (127.0.0.1:11433) to generate
fresh support text, this reuses the exact 16 real (claim, support) pairs already computed and
committed in `docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.jsonl` (J-0702's own
final, isolation-verified n=80 run) — evenly spaced indices 1,6,11,...,76 (8 from window A, 8 from
window B). Same claim+support inputs for both prompt variants removes `_prove()`'s own sampling
stochasticity as a confound between arms, and needs zero hot-lane calls. Both prompts were called
through `core.judge_panel.rule_detail()` directly (the identical call `_disprove()` itself makes),
same `user` message construction, same `context` tagging, at the CURRENT shared default
(`num_predict=200`, no override). A pre-registered rule (>=2/16 parse failures) would have
triggered a third arm at `num_predict=350`; it did not fire. The existing 3-case control check
(`_CONTROL_CASES`: circular_support / genuine_support / overreach_support, each with a known right
answer) was also re-run through both prompts, matching the job's own step 2 instruction.

Isolation (required, live-adjacent judge hubs): anchored `core`/`core.judge_panel` to the
`wt_train_split_merge_ab` worktree before `lab_env` could touch `sys.path`; `lab_env.isolate()` for
the DB-copy backstop; `judge_panel._DATA`/`_LOG` redirected to a job-scoped scratch dir
(gitignored, left on disk for inspection); pre/post snapshot + canary-string scan of all 5 live
JSONL logs (`trains_log.jsonl`, `judge_panel_log.jsonl`, `train_state_log.jsonl`,
`train_length_log.jsonl`, `monologue_log.jsonl`) plus `nascence.db` mtime/size, across BOTH runs
(the 32-call main test and the 6-call control-check addendum). **Gate independently verified before
either run**: Du's own process was not in the OS process table (`Get-CimInstance Win32_Process`)
and `data/nascence.log`'s last line read `Nascence shutting down.` ~30 minutes prior with no new
lines since — a genuine completed shutdown, not a frozen mid-sleep state, so this job's own calls
to JUDGE_1 (Ramses, shared with Du's live commitment-defeater/dream-primary calls per
`judge_panel.py`'s own D-0121 comment) had no real contention to cause.

## Result 1 — the ceiling question: RESOLVED. 200 alone is enough; no override needed.

| Arm | n | parse failures | status distribution | avg wall-clock/call |
|---|---|---|---|---|
| Tightened (current live prompt) @ 200 | 16 | 0/16 | objected=14 (87.5%), held=2 (12.5%) | 10.46s |
| **Original (reconstructed) @ 200** | 16 | **0/16** | objected=8 (50.0%), held=8 (50.0%) | 13.95s |
| Original @ 350 (override) | — | not run — arm 2 showed 0 parse failures, well under the 2/16 trigger | | |

3-case control check: **tightened 3/3 correct, original (reconstructed) 3/3 correct** — both
instruments discriminate correctly on all three known-answer cases at `num_predict=200`, 0/6 parse
failures. This directly answers the job's central question: **F-1034/F-1035's historical 65%
(52/80) UNDETERMINED rate on the untightened prompt was a real, but purely infrastructure-side,
symptom of the OLD 80-token ceiling — J-0693's 80→200 raise alone (no per-call override needed)
gives the fuller, three-named-sub-case, open-ended-why prompt enough headroom to complete cleanly.**
The tightening was a genuine stopgap for a ceiling that has since moved, not something independently
required for parse-validity at today's default.

## Result 2 — NOT anticipated: the two prompts are not interchangeable in their VERDICTS

On the identical 16 real (claim, support) pairs, the two prompts agree on only **10/16 (62.5%)**;
on the other **6/16 (37.5%)**, they disagree — and in **every one of the 6 disagreements, the
direction is the same**: tightened=`objected`, original=`held`. Never the reverse. Full per-event
detail: `train_split_merge_disprove_prompt_ab_2026-09-08.jsonl` (this directory).

Qualitative read of the `why` text (both judges' raw responses, not just the verdict) shows a
consistent pattern, not noise:

- **The tightened prompt's `why` text is short and often formulaic** — "Support restates claim; no
  independent reason given" (or a close paraphrase) appears, close to verbatim, across several
  *substantively different* claims (e.g. events 3, 4, 5, 8, 9, 12 in the 16-sample), reading as a
  reflexive default rather than a claim-specific read every time.
- **The reconstructed original prompt's `why` text is longer, more specific to the actual claim
  content, and more willing to credit general-but-real support as sufficient** — e.g. on event 12
  (tightened: "Support relies on restatement of the claim, not independent reasons" → objected;
  original: "The support offered gives reasons that, while not identical to the claim, support its
  general themes of change, fluidity, and interaction" → held). This pattern — the fuller prompt
  explicitly weighing whether support is "proportionate" and "independent" per its own named (a)/
  (b)/(c) cases, rather than defaulting to "restatement" — repeats across the disagreement set.
- On the 3 control cases (deliberately unambiguous), both prompts agree with each other and with
  the known answer — the divergence shows up specifically on **ambiguous, borderline real support**,
  exactly where a 90%-vs-50% objection-rate swing would matter, not on clear-cut cases. This is
  evidence the reconstructed prompt is a working instrument on this sample (validated the same way
  the tightened one originally was), not that it is simply "worse at judging."

**This bears directly on D-0181's own open question** (is the tightened prompt's reported 90.0%
objection rate itself a problem, and if so should a fix target Lane 1's `prove` prompt or Lane 2's
`disprove` prompt/threshold) **without resolving it**: the previously-reported 90.0% (72/80) number
is now shown to be, at least partly, a function of the SPECIFIC tightened wording — not solely a
fact about how confidently Lane 1's `prove` branch asserts rather than evidences. A fuller-reasoning
version of the exact same semantic target, at the exact same `num_predict`, objects roughly HALF as
often on identical real inputs. Whether that makes the fuller prompt "more correct" (less prone to a
certainty-machine collapse, closer to what D-0168 intended) or the tightened one "more correct"
(a deliberately stricter bar) is a design/values call this job does not make — recorded as new
evidence for D-0181, per the founder's own read, not as a ruling.

## What this job does NOT establish

- **n=16 is small.** The 62.5%/37.5% agreement split and the 87.5%-vs-50% objection-rate gap are a
  real, qualitatively-explained, consistently-directional signal (not random noise, given the 3-case
  control check passes 3/3 both ways and every disagreement points the same direction) — but this
  job's own instructions are explicit that a full n=80 kill-criteria replay is NOT this job's to run
  on its own initiative; see follow-up job spawned below.
- **This does not re-validate or invalidate D-0168 itself** — D-0168 asked only whether the
  support-chain RETARGET (vs the old claim-only framing) works, and both this job's control check
  and F-1034's own already answer that independently of the tightening question.
- **No live code was changed.** `scripts/train_state_invitro.py`'s own live `_DISPROVE_SYSTEM`
  (the tightened version) is untouched — this job only ran an isolated, out-of-band comparison
  against it. Whether to actually adopt the fuller shape, keep the tightened one, or do neither
  pending a founder read of real per-event cargo, is not decided here.

## Isolation backstop — both runs

Main A/B (32 calls): `nascence.db` mtime/size unchanged; 0 canary hits across all 5 live JSONL
logs (0 new lines in any of them during the ~6.5-minute run, consistent with Du confirmed offline
throughout). Control-check addendum (6 calls): same result, `nascence.db` unchanged, 0 canary hits,
0 new lines in any live file. Full raw output preserved in this job's own scratchpad
(`J-0764_disprove_prompt_ab_test.py`, `J-0764_control_check_ab.py`, and their `.output` /
`ab_test_results.json` / `control_check_results.json` companions) for re-inspection.
