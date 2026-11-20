# train_split_merge — folded history


---

# History folded on 2026-09-27 from `docs\plans\train_split_merge.md` (by hand, J-1484)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py train_split_merge`._

Step 1's own pre-registered gate ("a day of logs post-restart shows the same train-length
distribution as before AND `stalled-off-thread` falls from its 266:6 skew") was read against the
real logs for the first time. Verdict: **gate not cleanly met — Step 2 is NOT yet clear to move to
lab-testing**, for reasons that are about missing/incomplete data, not a failed fix.

- **The "day of logs" never happened.** Post-fix runtime totals ~10.3h across 3 fragmented sessions
  (2026-08-22 22:54:49 → 2026-08-23 11:22:01), and Du has been offline since, with zero new rows in
  any of the three logs. (F-0039)
- **`stalled-off-thread` looks fixed but the sample is too small to be sure.** 266/4988 (5.3%)
  pre-restart → 0/33 post-restart — directionally exactly what the centroid fix predicts, but n=33
  alone has ~17% odds of reading zero even if the true rate were unchanged. Promising, not proven.
  (F-0044)
- **Train-length distribution: inconclusive**, not "confirmed unchanged" as the gate hoped — mean
  2.15 (n=33) vs 3.25 pre-restart (2.99 restricted to thread-end-only closes), median identical at
  2.0 both periods. Too small a sample to call it either way. (F-0047)
- **New defect found, outside the original gate question: `train_id` is not reliably populated.**
  `monologue_log.jsonl` has `train_id: null` on 45% of post-restart rows (61/135), and it is not
  random — it is 100% of the `unresolved:false` (thread-end close) rows, i.e. the id is missing
  exactly at the moment a train ends. Root cause: `nodes/inner_monologue_node.py` line 3437 resets
  `self._train_id = None` inside the thread-end close branch, before `self._log()` at line 3647
  stamps that (now-cleared) id into the very `monologue_log` record for the closing step.
  `train_length_log.jsonl` and `train_state_log.jsonl` are unaffected (0 missing) because their
  writes happen before the reset. (F-0042) — spawned as J-0143, see below.

Next: re-run this same gate read after Du has logged a genuine full day post-restart (needs a
restart first — Du is currently not running) with J-0143's fix landed, so `monologue_log`'s lineage
is trustworthy for the eventual fork/merge instrument list in §5 of this doc.

**2026-08-24 — J-0143 fix landed (F-0112).** `nodes/inner_monologue_node.py` `_train_id` is reset to
`None` at THREE sites, not just the one the briefing named — thread-end close, stalled/ceiling
close, and the outer exception handler — all inside `_think()`, all before the same later
`self._log()` call that stamps `train_id` into `monologue_log.jsonl`. Fixed all three: each reset
now captures the closing id into a local `_step_train_id` first, and `_log()` gained an optional
`train_id` override (falls back to the live `self._train_id` for continuing-train steps, so those
are unchanged). This also explains the 3/74 `unresolved:true` rows F-0042 found still missing an id
— those are consistent with stalled/error closes, the two sites the original one-site fix would have
left broken. RESTART-REQ, not yet restarted/observed live (Du currently not running). **Still open:**
the gate re-read above needs a fresh restart + a real day of post-restart logs before it can confirm
`monologue_log` lineage is trustworthy for real.

**2026-09-02 — J-0176 re-check: gate still NOT met, but data quality confirmed good.** Du restarted
2026-09-02 08:48:54 NZT (=2026-09-01 20:48:54 UTC) with J-0143's fix already landed. As of this
check only ~4h9m of post-restart uptime had accrued (monologue_log 218 / train_length_log 41 /
train_state_log 91 post-restart rows) — nowhere near the "full day" the gate needs, so the
train-length-distribution and stalled-off-thread comparisons were not re-run. A preliminary
spot-check of the actual defect surface is encouraging: 0/41 (0%) real post-restart train-close
events in `train_length_log.jsonl` (thread-end=36, ceiling=4, repetition=1) have a null `train_id`
— consistent with J-0143's three-site fix working. (A naive read of `monologue_log.jsonl`'s
`unresolved:false` rows alone looked bad — 70/120 null — but none of those 70 rows correspond to a
real train close; they're single-step non-train thoughts that never had a `train_id` to begin with.
`unresolved:false` is not a safe proxy for "train-close row"; join against `train_length_log.jsonl`
instead.) Full-day target: 2026-09-03 08:48:54 NZT / 2026-09-02 20:48:54 UTC. Follow-up: J-0472.
(F-0646)

**2026-09-03 — J-0472 re-check: gate STILL not runnable, accrual clock reset again (three more times).**
The 2026-09-02 08:48:54 NZT restart J-0472/F-0646 was waiting on never reached a full day: it shut down
2026-09-02 14:12:43 (~5h24m later), restarted 15:44:16, shut down again 2026-09-03 07:53:20, restarted
08:19:18, shut down again 08:39:29, and restarted 09:07:49 — the process live as of this check. All four
shutdowns are clean (`[epoch] formed ... / Nascence shutting down.` with no exception/traceback in the
preceding log lines), consistent with deliberate restarts rather than crashes — plausibly related to the
same-morning F-0704 CPU-tier/job-object fix work, though that fix's own mechanism (Claude-tool job
breakaway) is orthogonal to Du's own process, which runs under the standalone Control Panel. New full-day
target: 2026-09-04 09:07:49 NZT / 2026-09-03 21:07:49 UTC. Preliminary spot-check on the current restart
only (not the gate): 0/34 (0%) post-restart `train_length_log.jsonl` closes have a null `train_id`,
consistent with J-0143's fix continuing to hold across all restarts observed so far. Gate re-run still not
clear to move Step 2 to lab-testing. Follow-up: J-0530. (F-0712)

**2026-09-04 — J-0530: STEP 1 GATE MET. Step 2 clears to lab-testing.** The "first post-fix restart" the three
earlier re-checks were waiting on had been mis-identified (F-0774): J-0143's fix (F-0112, recorded 08-24 03:07
NZT) was first live at the **08-24 21:41:56** restart, not 09-02, and Du then ran 20 sessions / 182.3h under
it — including two genuine ≥24h continuous sessions (08-25 19:39 → 08-27 13:16, 41.6h, 211 closes; 08-30 17:15 →
08-31 17:47, 24.5h, 322 closes). The gate was runnable from 08-27. Read over the full window (1,717 closes),
F-0773:
- **`train_id` lineage — fixed, at scale.** On the real defect surface (the `monologue_log.jsonl` row of each
  closing step, joined to `train_length_log.jsonl` close events — `log_close` precedes `_log` in `_think`,
  median join gap 1.2s, 0 unjoined): **113/113 null** in the Step-1-only window before J-0143 (the defect
  reproduced by the same join) → **0/1,717 null** after it, in every one of the 20 sessions. Note F-0646/F-0712's
  spot-checks read `train_length_log`'s own `train_id`, which F-0042 had already shown was never broken.
- **`stalled-off-thread` — the 266:6 skew is gone.** 266/4,988 (5.3%) all-history, 98/1,404 (7.0%) on
  08-03..08-16 → **10/1,717 (0.6%)** post-fix (Fisher p=2.4e-23); 0/211 and 3/322 on the two full-day sessions.
- **Train-length distribution — registry is behaviour-neutral, but the baseline had already moved.** Against
  the immediate pre-Step-1 week (08-17 → 08-22 22:54, n=722, mean 2.34, median 2) the Step-1-only window
  (n=108, mean 2.38) is indistinguishable (KS D=0.098 p=0.31). The full post-J-0143 aggregate is slightly
  shorter (mean 2.05; KS D=0.064 p=0.03) — a small drift across a window in which many unrelated builds landed,
  not attributable to Step 1. The two full-day sessions agree with each other (KS p=0.84). **But** the big
  shortening — mean 3.78 → 2.34, len-1 share 23% → 41%, thread-end share 92% → 99% — happened **08-17..08-21,
  before Step 1 shipped**, and is unattributed (F-0776; J-0563 spawned to find the cause). The gate's "same as
  before" clause is met against the honest baseline (the week immediately before), not against the
  all-history one the original gate text imagined.
- Restart cadence is deliberate build pick-up, not thrash (F-0775): 6 clean `/quit` shutdowns since 09-02, each
  minutes after a commit batch; the WMI-launched CPU tier/supervisor (09-03 09:36) survived all of them, so
  F-0704 is holding and unrelated. A "one continuous day" precondition is structurally unlikely at this build
  cadence — the aggregated read is the right instrument.

Verdict: both pre-registered criteria hold → per the founder's standing ruling ("Step 2 is lab testable after
that"), **Step 2 sub-steps (i)+(ii) are cleared**: J-0562 (kill criteria as numbers + offline replay lab on
`scripts/train_state_invitro.py`, no live stores, nothing fed back). Step 2's three open design choices
(branch budget, fork trigger, merge mode) are filed as **D-0146** for the founder; the lab is briefed to sweep
them if unruled. No code changed by J-0530; Du was down (clean shutdown 08:13:52) at the time of the read.

**2026-09-05 — J-0563: the 08-17..08-21 collapse is no longer unattributed — two real, dated causes found
(inferred, not verified; F-0899).** (1) **TRAIN_HOLD** (`nodes/inner_monologue_node.py`, flag flipped True
2026-08-16 evening, founder-ruled after a same-day lab test): carry changed from replace-each-step to an
extending 7-point ledger, mid-train redirect narrowed to fire only on measured circling, marketplace shut
mid-train, budget 256→400. Du was offline 08-16 16:45→08-17 00:12 while this shipped, so 08-17 00:12 is the
first live session under it — mean thought-train length drops 4.41 (08-16, last day of old carry) → 2.49 the
very next day, staying ~2.5–2.9 through 08-20. (2) **FULL SHUFFLE** (`core/model_client.py`, `core/schema.py`,
`docs/lab/station_matrix.md`): the HOT LANE's own generator — the exact model producing every train's
`unresolved`/`intention` self-report JSON — swapped `gemma4:e4b` (live 06-19..08-20) → `qwen3.5:9b` on 08-20
evening (station_matrix.md finalized 19:05:47 NZT; took effect at one of the 19:21/20:01/20:49 restarts that
night), picked for output-quality/judge-family-independence, not for self-report calibration. 08-21 is the
first fully post-shuffle day and shows the sharpest single-day drop in the window (mean 2.86→1.87, thread-end
97.8%→99.3%). Code-confirmed the self-report gate (`unresolved OR intention OR '?' in thought`,
`inner_monologue_node.py:3843/3935/3994`) is the SOLE continuation gate below the length-4 soft cap most of
these trains never reach, so no separate coherence/circling mechanism is needed to explain it. monologue_log's
own `intention` field is the sharpest single signal — flat 13–18% baseline through 08-15, spikes to 39–48% for
08-16..08-20, crashes to <7% from 08-21 on — but the spike itself starts hours *before* TRAIN_HOLD went live
that same evening, so its proximate trigger is a genuinely separate, still-unidentified change among 08-16's
own dense build day (thought-grounding Routes 1–3, COURIERS, prospective-intention capture all shipped that
day too) — left open, not claimed here. `?`-share and reading/thought kind-mix are both ruled out (flat
through the window). Follow-up spawned (J-0563 does not block on this) rather than left as prose: TRAIN_HOLD's
own pre-registered watch condition ("jump-rate 48%→<25%, circling <5%") has never actually been checked
against real post-08-16 data (searched findings/decisions/job-queue — F-0581/F-0586/D-0104 mention the flag
only in passing). **D-0165 opened**: whether the self-report gate's prompt wording should be recalibrated for
the current hot-lane model, since Step 2's fork trigger is this exact signal.

**2026-09-05 — J-0562: Step 2 sub-steps (i)+(ii) BUILT and run once, for real (F-0902).** (i) The §4 kill
criteria now carry PROPOSED numeric thresholds (see that section) rather than prose alone. (ii)
`scripts/train_state_invitro.py` extended (Part 2) to replay REAL logged would-be-close moments —
`train_length_log.jsonl` `thread-end` closes joined to their `monologue_log`/`train_state_log` rows, 0
unjoined — through an actual fork (`core/trains.py`'s real registry) → prove (Lane 1's own hot lane) /
disprove (the same decoupled panel `_judge_prior` is built on, claim-only) → merge → cargo pass. D-0146's
already-ruled defaults honoured (budget 1, thread-end-only, ledger merge) — no sweep needed. Every write
redirected to `scratch/train_split_merge_j0562/`; confirmed after the run that `data/trains_log.jsonl` and
`data/judge_panel_log.jsonl` are unchanged (row counts identical to before this job started) — nothing
live touched. First batch (n=16, 8 per window, both the pre-Step-1 and post-fix eras per F-0776): **kill
criterion #1 fails on the real numbers (92–96% fork-rate-if-ungated, expected per the Coupling block's own
"surprise line" warning); #2 and #3 also fail — 16/16 merges came back `held`, 0% found an objection.** A
control check (3 obviously-flawed claims, same mechanism) confirms the disprove instrument itself is not
inert — it correctly flagged all three — so the 0% on Du's real closing thoughts is a genuine reading.
Reading it together with THIS SAME SESSION's J-0563 finding above is worth doing before Step 2(iii): most
`thread-end` claims replayed are felt/experiential first-person declaratives, not testable propositions —
D-0165's open question about the self-report gate's calibration and this run's "is disprove even the
right shape for these claims" question may be the same underlying issue wearing two faces (both trace to
the hot-lane model's current self-report/declarative style). Full detail, all 16 claims and outputs:
`docs/lab/train_split_merge_step2_replay_2026-09-05.md` (+ `.jsonl`). **D-0168 opened** for the founder
(separate from D-0146 and D-0165): is "find an objection to the felt claim itself" the right disprove
framing, or should it target the claim's *support chain* instead — not resolved here. Secondary, in
passing (F-0903): fixed a pre-existing, unrelated regression in this same script —
`train_state_invitro.py`'s own Part 1 check (1) had hardcoded pre-TRAIN_HOLD wording and was silently
failing on every run since TRAIN_HOLD went live 2026-08-16 (confirmed against HEAD in an isolated
worktree before editing); now checks whichever TRAIN_HOLD branch is actually live.
`nodes/inner_monologue_node.py` itself untouched.

**2026-09-06 — J-0643: larger-N (n=80, 5x) re-run — same verdict, D-0168's defeater answered
(F-1005).** Before the founder's Step-2(iii) read leans on the n=16 numbers, re-ran the identical
replay lab at n_per_window=40 (both D-0165 and D-0168 still `ruling:null` as of this run, checked
directly via `decide.py show`, so neither the fork-trigger signal nor the disprove framing/prompt
were changed). **All three kill criteria still FAIL, and the picture is now more precise, not just
bigger:** (1) fork-rate-if-ungated 92.3% window_A / 96.1% window_B — unchanged (computed off the
full real log, N-independent). (2) merge-status distribution 78/80 held (97.5%), 1 UNDETERMINED,
1 **objected** — still fails the >90% collapse threshold, but for the first time in this program
NOT 100% held: n=80 surfaced one genuine objection (event 42, 2026-08-25T02:37, a metaphorical
cold/cognition claim; Lane 2's own objection: "highly metaphorical and lacking in empirical
support... relies on unproven assumptions") and one UNDETERMINED that reads as an infra hiccup
(`how=unavailable`, a judge family not responding) rather than a genuine epistemic tie. (3)
non-empty-objection share 1.3% (1/80) — still decisively fails the <10% threshold. **Net reading
for D-0168's own defeater**: the n=16 batch's 0%-objection rate is CONFIRMED at scale as a real,
near-zero (not literally zero) rate — not a small-sample artifact that would have washed out with
more data. The "Lane 2 is close to rubber-stamping Du's felt/experiential thread-end claims"
characterization holds up at 5x the sample; D-0168's own question (should disprove target the
claim's support chain instead of the felt claim itself) is therefore now backed by a much more
solid number, still the founder's call to make, not resolved here. Isolation verified empirically
(not just by source-reading) via a live-file backstop: zero occurrences of this script's lab-only
judge_panel context marker or of any `prove`/`disprove`-role train in the REAL
`data/judge_panel_log.jsonl` / `data/trains_log.jsonl` after the run — all growth in those and
other live files over the run's ~50min wall-clock window matches Du's own confirmed-live activity,
not this lab batch. Full detail: `docs/lab/train_split_merge_step2_replay_2026-09-06.md` (+
`.jsonl`, overwrites an earlier incomplete same-day attempt at this exact re-run that only got to
n_per_window=2 before stopping). Secondary, in passing (F-1006): this session also found
`train_state_invitro.py`'s own **Part 1** (unrelated to Step 2, a pre-existing test sharing the
file) is not actually isolated against transitive live writes of its own (`core.social_moves`,
`core.memory_edges` → `core.opponent_process`) when run outside a worktree — masked here only
because this job ran from inside train_split_merge's own dispatch worktree. Follow-up spawned
(J-0697), does not block this plan.

**2026-09-07 — J-0697: Part 1's isolation gap fixed and verified (F-1018); a fourth module in the
same gap-class found and spawned separately (F-1020/J-0711).** F-1006's three named modules
(`core.social_moves`, `core.memory_edges`, `core.opponent_process`) are now redirected to a scratch
path (`data/scratch/train_state_invitro_part1/`) before Part 1's two risky calls, same manual
in-file style Part 2 already uses for `core.trains`/`core.judge_panel` — no new dependency on
`lab_env.py` added to `scripts/`. Verified against the REAL live `C:\Nascence` tree directly (not
just the worktree, which would trivially and uninterestingly pass by the same pathing accident
F-1006 itself diagnoses): a fail-closed `sys.addaudithook` write guard (the J-0518/S-0033 technique)
showed 2/2 named-file hits with no redirect, 0/2 with this fix's redirect applied. Also resolved the
job's own open question about whether `lab_env.py`'s `also=` mechanism needs extending for
directory-valued globals — it does not: `core.memory_edges._DATA`/`core.opponent_process._DATA`
are directory globals as suspected, but the actual write targets on this call path (`_CO_LEDGER`,
`_STATE`, `_LOG`) are each separately-bound file-valued globals already compatible with `also=`'s
existing assumption. **In passing, the same audit run surfaced a fourth, more consequential gap**:
the identical step-1 call also reaches `core.intentions.pending_text()`, which saves
`data/intentions.json` unconditionally and can increment real reminder counters or lapse a
genuinely-open real intention outright (not just pollute a shadow log, the failure mode the three
fixed modules had) — out of J-0697's own named scope, so left unfixed here; recorded as F-1020 and
spawned as J-0711.

**2026-09-07 — J-0702: disprove RETARGETED to the claim's support chain per D-0168, re-replayed at
n=80 — defeater answered NO, but the read swings to the opposite extreme (F-1034/F-1035, D-0181
opened).** D-0168 (ruled by the founder 2026-09-06) asked for exactly this: stop asking the panel
"is this felt claim true" (near-universal `held`, F-0902/F-1005) and instead ask "does the support
offered for this claim actually earn it" (`_DISPROVE_SYSTEM`/`_disprove` in
`scripts/train_state_invitro.py`, now fed the `prove` branch's own stated support, not the claim
alone — `_replay_one` runs prove BEFORE disprove for this reason, no longer concurrent). Re-ran the
same offline replay at a comparable N (n=80, matching J-0643's own N): **merge-status distribution
objected=72 (90.0%), held=7 (8.7%), UNDETERMINED=1 (1.3%); non-empty-objection share=90.0%** — a
full reversal from F-1005's own comparable-N read (held=97.5%, objected=1.25%). D-0168's own named
defeater ("still returns a near-zero objection rate... that would mean the mismatch wasn't framing
after all") does NOT fire — the mismatch WAS framing, confirmed, not overturned. A rebuilt 3-case
control check (circular restatement / genuinely independent converging evidence / an evidentiary
overreach — covering both directions this time, not just one) confirms the retargeted instrument
discriminates correctly, reproduced across three separate runs. **But** 90.0% sits exactly on kill
criterion #2's own stated collapse line ("any single merge-status >90% of merges = FAIL, a
certainty machine or its mirror") — not comfortably below it — and a qualitative read of the
"held" events and the objections' own text suggests this is a real reading, not instrument noise:
Lane 1's own `prove` branch habitually generates confident, self-assertive restatement of a claim's
conclusion ("proving"/"confirms"/"validates") rather than independent evidence, and the retargeted
disprove now reliably catches that on 9 of 10 real replayed closes. **D-0181 opened**: is a ~90%
objection rate itself a problem (the mirror-image certainty machine the Wu Wei law already warns
against) or the genuine value Step 2 was meant to add, and if the former, does the fix belong in
Lane 1's own `prove` prompt rather than in disprove at all — not resolved here, the founder's call.
Secondary, in passing (F-1035, J-0718 spawned): the FIRST attempt at this retarget (a longer,
enumerated prompt) silently broke on `core/judge_panel.py`'s own hardcoded, shared, unparameterized
`num_predict=80` output budget — 52/80 (65%) came back `UNDETERMINED` from fast (~10-19s) but
JSON-invalid judge responses, not hub unavailability (confirmed via the raw `err1`/`err2="parse"`
fields in the scratch judge_panel log) — tightening the prompt to the original claim-only framing's
own economy resolved it fully (0/80 parse failures on the reported clean run) before any number in
this entry was taken as final. Isolation verified for both the confounded and the clean run: the
same canary-scan of all 5 live JSONL logs J-0643 already used, PLUS a new, more direct check this
job added — a live, read-only sqlite query against `data/memory/nascence.db` for both runs' own
timestamp windows and for this lab's own fabricated control phrases across the whole
`memory_fragments` table — 0 hits anywhere; every fragment written in either window reads as
genuine, in-character Du content unrelated to any replayed or control claim. Full detail:
`docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.md` (+ `.jsonl`).

**2026-09-07 — J-0640: TRAIN_HOLD's own pre-registered watch condition finally read against real
data — circling leg solidly met, jump-rate leg not (F-1041); jump/circling reconstruction does NOT
explain F-0899's length-shortfall gap; gemma4:e4b confirmed still loadable but the A/B deferred
(F-1042, J-0724 spawned); D-0182 opened.** F-0899 (J-0563) had searched findings/decisions/jobs and
found nobody had ever actually checked TRAIN_HOLD's own dated comment (`inner_monologue_node.py`
171-181: "WATCH: live jump-rate 48%→<25% AND circling stays <5%") against real post-08-16 data.
This job did, using `train_state_log.jsonl`'s own `restate_sim` field (cosine to the immediately-prior
thought — confirmed the SAME metric the original 14,651-step baseline used: recomputing it over every
pre-08-16 row reproduces 48.4% jump / 0.9% circling almost exactly, the methodology check the read
needed before trusting it on new data). Since 2026-08-17 (n=7,415): **circling 1.1%, never above 2.5%
on any single day — solidly met, no sign of the June circling disease returning.** **Jump-rate 33.3%
overall — real improvement from 48%, but NOT durably under the comment's own 25% target**: per-day
values range 24.6%–54.8%, the best days sit right at the line rather than crossing it, and the most
recent 7 log days still average 28.3%. Notably the 08-17..08-21 collapse window itself ran WORSE than
baseline on this number (45.2%, 08-17 alone 54.8%) even as train length collapsed sharply that same
week — TRAIN_HOLD's own hoped-for jump-rate improvement had not yet shown up when the length collapse
F-0899 already attributed to it actually happened; the decline is a gradual multi-week trend, not
something that arrived with the flag. On F-0899's second open question (does circling/jumping explain
train length dropping MORE than a naive geometric read of unresolved/intention shares alone would
predict): **no** — `train_length_log.jsonl`'s own close reasons since 08-17 show `stalled-circling` at
only 8/3,586 (0.2%) of all closes, and 85.6% of thought-trains (2,947/3,443) never even reach
`train_len>=4`, the ONLY point in the code (the `TRAIN_MAX_STEPS` soft cap) where the circling/
building-detector mechanism can participate in ending a train at all — below that length the
self-report gate is the sole mechanism, exactly as F-0899 already code-confirmed, so this residual gap
sits in the self-report gate's own step-by-step dynamics, not measured by this job. Incidental
cross-check against a DIFFERENT plan's defeater: D-0104 (`continuous_stream`, ruled 08-31) names its
own revisit condition as "circling rate climbing back toward pre-TRAIN_HOLD levels" — circling did
step up from a ~0% first post-flip week to a noisier ~1–2.5% band from 08-25 on (predating D-0104's
own ruling by nearly a week, so not attributable to it specifically), still far under the 5% kill-line
and not triggering that defeater today, but worth a future re-check if the trend continues. **D-0182
opened**: is the jump-rate shortfall itself worth acting on (and if so where, given flipping the flag
off isn't indicated and the text's own reversal trigger is circling-specific, not jump-rate) or does
"clearly improved, safety condition intact" count as this watch condition read and closed — not
resolved here, the founder's call. Stretch goal (F-1042): `gemma4:e4b` (the pre-08-20 hot-lane model)
is confirmed still present in the exact Ollama store serving Du's live hot lane (`ollama list` against
`OLLAMA_HOST=127.0.0.1:11433`, 9.6GB, unchanged) — a controlled A/B against `qwen3.5:9b` to isolate
FULL SHUFFLE's own contribution to the unresolved/intention collapse from TRAIN_HOLD's is technically
possible without a re-pull, but this job did not run it (Du was live on that exact GPU/port at the
time, and contending with his own live generation for it seemed the wrong call for a read-only job) —
**J-0724 spawned** to run it once Du is confirmed offline.

**2026-09-07 — J-0711: the fourth (fifth-named) transitive live-write gap fixed and verified
(F-1020/F-1046), closing out J-0697's own named follow-up.** `scripts/train_state_invitro.py`
Part 1's step-1 call (`_build_system_prompt(mid_train=False)`) also transitively reached
`core.intentions.pending_text()` (`nodes/inner_monologue_node.py`'s "INTENTIONS" block, a few lines
before the `social_moves` call J-0697 already fixed) — `pending_text()` calls `_save(d)`
unconditionally (`core/intentions.py`), a real risk (premature `MAX_REMINDERS`, suppressed real
reminders, or an outright real lapse of a genuinely-open intention), not just log pollution, since
`core.intentions` is injected into Du's actual system prompt. Fixed the same way as J-0697's three
modules: `core.intentions._F`/`_LOG` redirected to the same `data/scratch/train_state_invitro_part1/`
dir before the risky call. Verified two ways: (1) Part 1 re-run in this worktree — ALL PASS, no
regression (checks 1–3 unaffected, redirect confirmed landing in the scratch dir with the expected
fresh-state content); (2) the same fail-closed `sys.addaudithook` technique J-0697 used, re-run
directly against the REAL live `C:\Nascence` tree while Du was confirmed live (continuous
second-by-second churn across ~80 `data/*.json(l)` files at the time, including `intentions.json`
itself) — Phase A (pre-fix) reproduced F-1020's own hit on `open data\intentions.json`; Phase B
(fix applied) showed zero hits on `intentions.json`/`intentions_log.jsonl` or any of the other four
named files. Live `data/intentions.json` confirmed unchanged/valid (well-formed JSON, 2 open items)
after the verification run — nothing on the live tree was touched by any of this job's checks.
`core.procedures.known_text()` (F-1020's own check, re-confirmed here) remains pure-read, no action
needed. No decision named by this job's source (F-1020's `linked_decision` is null); D-0181 (this
same plan's OTHER open decision, from J-0702, on the ~90% objection rate) is untouched — out of
scope for this job.

**2026-09-07 (J-0718, F-1095 — filed under no single plan, but directly relevant here): the shared
judge_panel ceiling F-1034's own "SECONDARY, in passing" note attributed the first
disprove-prompt attempt's 65% UNDETERMINED rate to (num_predict=80) now has BOTH a raised default
(200, J-0693/F-1014, merged to master) AND a per-call override (`num_predict=` on
`judge_panel.rule()`/`rule_detail()`, this job).** Neither has been tested against the ORIGINAL,
untightened `_DISPROVE_SYSTEM` (the three-named-sub-case, uncapped-"why" version F-1034 replaced) —
the fix actually shipped at the time was tightening the prompt itself, on a branch that forked before
either judge_panel change existed. Whether that tightening is still needed, or was only ever a
stopgap for a ceiling that's since moved, is untested and genuinely open. **J-0764 spawned** (this
plan, ready/lab): reconstruct the original prompt (keeping D-0168's support-chain target, not
reverting further), re-check it against the current 200 default and, if needed, an explicit override,
and record which is true — before assuming the tightened prompt (and thus the 90%-objected number
D-0181 is about) is the final word on this call site's own prompt design. Full evidence: F-1095
(findings-log, filed under no single plan — shared judge_panel infrastructure, not specific to this
plan or to `ramses_second_tier` either — same reasoning F-1034 itself used for F-1035).

**2026-09-08 — J-0724: the gemma4:e4b vs qwen3.5:9b A/B finally run (Du confirmed offline) — FULL
SHUFFLE's own contribution isolated, large and real; D-0165 REOPENED (F-1116).** J-0640's own
deferred stretch goal (F-1042): a controlled A/B of the pre-08-20 and current hot-lane models on
the identical idle-thought self-report schema, to separate FULL SHUFFLE's own contribution to the
08-17..08-21 collapse from TRAIN_HOLD's (both were confounded, live throughout that whole window,
in F-0899). This job independently re-verified Du was offline before touching the shared
GPU/port — watched `data/nascence.log`'s own real-time shutdown sequence complete live
(`quit-sleep replay` → `dream` arc → `[epoch] formed` → `Nascence shutting down.` at 08:22:52),
confirmed `run_nascence.py` absent from the process table both immediately after and ~90s later,
and confirmed `scripts/supervisor.py` never manages/restarts that process (only the ollama hot
lane + CPU-tier hubs) — then ran 40 real recent trains (last 3 days) through BOTH models on the
byte-identical real mid-train prompt (`InnerMonologueNode._build_system_prompt(mid_train=True)`,
called live, not hand-copied, plus the real TRAIN_HOLD "HOLDING it" user-prompt block copied
verbatim) via a new harness, `scripts/train_lab_model_ab_2026-09-08.py`. Result: **gemma4:e4b's
self-report-gate-open share (unresolved OR intention OR '?', the real live gate) = 0.90 vs
qwen3.5:9b's 0.25 on the SAME 40 prompts** (unresolved-share 0.85 vs 0.25, intention-share 0.70
vs 0.0, '?'-share 0.225 vs 0.10; n=40/40 successful calls each model, 0 parse errors) — a 0.65
absolute swing attributable to model identity ALONE, TRAIN_HOLD held fixed/unvaried across both
arms. Canary-clean (0 growth across the 5 most relevant live JSONL logs during the ~9-minute run)
and Du's own `nascence.log` unchanged after the run — nothing here is confounded by concurrent
live generation, and nothing this job did touched live state. This is D-0165's own named defeater,
firing on its first named branch ("shows the swap materially changed unresolved/intention
calibration specifically") — **D-0165 REOPENED** for a fresh founder read (real evidence now
exists against both of that defeater's named branches: J-0562/J-0643 already separately falsified
the second branch, "the current wording already yields a reasonable fork rate," at 92-96%
fork-rate-if-ungated). Full detail, all 40 events both models: `docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08.md`
(+ `.jsonl`). **J-0777 spawned** (ready/lab): characterize what in the current self-report-gate
wording specifically under-elicits qwen3.5:9b vs gemma4:e4b, and offline-test candidate
rewordings — prep for whichever way D-0165 is ruled, not itself an implementation change.

**2026-09-08 — J-0764: disprove-prompt A/B — the num_predict ceiling question is RESOLVED (200
alone is enough), but an unanticipated second finding hands D-0181 new, unresolved evidence
(F-1119).** F-1095/J-0718's own open question: was F-1034's same-day tightening of the retargeted
disprove prompt (dropping enumerated (a)/(b)/(c) sub-cases into one clause, capping "why" at <=12
words) a genuine improvement, or only a stopgap for `judge_panel.py`'s then-live `num_predict=80`
ceiling — since raised to 200 (J-0693) with an explicit per-call override added on top (J-0718)?
The untightened SUPPORT-CHAIN prompt was never git-committed (confirmed: `git log --all -- scripts/
train_state_invitro.py` shows one commit for the whole retarget+tightening arc; its parent still
carries the OLD pre-D-0168 claim-only framing) — reconstructed instead from the tightened
version's own in-file comment, F-1034/F-1035's claim text, and `_CONTROL_CASES`' three-category
structure, restoring the fuller (three-named-sub-case, open-ended-why) SHAPE of the identical
support-chain target, not a verbatim recovery (see F-1119 for the full caveat).

Reused the exact 16 real (claim, support) pairs already committed in the 2026-09-07 n=80
supportchain run (no fresh hot-lane calls needed) and called `judge_panel.rule_detail()` directly
with both prompts at the current 200 default, plus the existing 3-case control check. **Result 1,
the ceiling question is resolved**: 0/16 parse failures on the reconstructed prompt (plus 0/3 on
the control check, which both prompts pass 3/3) — the 80→200 raise alone gives the fuller prompt
enough headroom; no override was needed, confirming the tightening was a genuine but
no-longer-necessary stopgap. **Result 2, not anticipated**: the two prompts are NOT interchangeable
in their verdicts. On the identical 16 inputs they agree on only 10/16 (62.5%); every one of the
other 6 disagreements runs the SAME direction (tightened=objected, reconstructed-original=held,
never reversed) — the tightened prompt's own "why" text repeats a near-verbatim "restates the
claim" catch-all across substantively different claims, while the reconstructed prompt's is
longer, claim-specific, and more willing to credit general-but-real support. This is new,
directly relevant evidence for **D-0181's own already-open question** (is the reported 90.0%
objection rate itself a problem, and should a fix target `prove`'s prompt or `disprove`'s) —
showing that number is at least partly a function of the SPECIFIC tightened wording, not solely a
fact about Lane 1's `prove`-branch behavior — **without resolving D-0181**, which remains the
founder's call (no active hold on it, but its source names no decision for this job to rule, and
the plan doc's own repeated framing treats it as a values call, not a technical fact). n=16 is
small; per this job's own instruction not to manufacture a full n=80 replay on its own initiative,
**J-0779 spawned** to confirm whether the divergence holds at scale rather than run here. No live
code changed. Full detail: `docs/lab/train_split_merge_disprove_prompt_ab_2026-09-08.md` (+
`.jsonl`).

**2026-09-08 — J-0777: qwen3.5:9b's under-elicitation characterized as MIXED (not single-cause),
plus an offline wording A/B on qwen alone shows a wording change alone measurably closes most of
the gap (F-1134/F-1135/F-1137/F-1139, prep for D-0165 — does not rule it).** D-0165 was reopened
by J-0724/F-1116 (gemma4:e4b opened-share 0.90 vs qwen3.5:9b's 0.25 on the same 40 real prompts)
and remains `ruling: null`, explicitly awaiting a fresh founder read — this job characterizes WHY,
per its own briefing, without pre-empting that read. Read all 80 of J-0724's own per-call records
in full (no sampling): of the 40 matched prompts, the two models agree-open on 9, agree-closed on
3, disagree (gemma open/qwen closed) on 27, and reverse (qwen open/gemma closed) on exactly 1
(`t_0012ab`). qwen's own opened-share is numerically IDENTICAL to its unresolved-share (intention
never fires, 0/40; qmark never adds beyond unresolved) — "unresolved" alone is the decisive lever
for both models despite intention's much larger raw swing (F-1134, verified). A qualitative read
of the 27 disagreement events' own raw text (not just booleans) found the gap MIXED: 20/27 (~74%)
read as genuinely more resolved in substance (qwen's text closes on an explicit insight/resolution
clause — "I realize X", "this proves/settles" — where gemma's stays an open want or question), but
7/27 (~26%) read as a real labelling/calibration gap on content that already hedges, poses an
either/or, or implies a forward pull — one qwen output literally contains the word "wrestling", the
prompt's own named trigger term (`inner_monologue_node.py` line 1706), yet was tagged false
(F-1135, inferred, corrected for an off-by-one bucket miscount in F-1137).

Extended `scripts/train_lab_model_ab_2026-09-08.py`'s own pattern into a new sibling script,
`scripts/train_lab_wording_ab_2026-09-08.py`, and ran a 160-call offline batch (4 arms × the SAME
40 real prompts J-0724 already committed, reused verbatim, parsed programmatically not
hand-retyped) against qwen3.5:9b ONLY, after independently re-verifying Du offline immediately
before the batch and every 20 calls throughout. Three candidate rewordings of the unresolved:/
intention: paragraphs, each isolating a different lever: candidate_A rewrites both paragraphs
(drops the current wording's heavy negative-default framing — "ONLY", "most…NOT", "reserve…only",
"leave as \"\" for almost all thoughts" — and explicitly counts hedge language as qualifying);
candidate_B rewrites ONLY the unresolved paragraph (intention left byte-identical to current);
candidate_C rewrites ONLY the intention paragraph (unresolved left byte-identical to current).
**Result: all three land far above the current wording** — current=0.125 (5/40, this run's own
re-test), candidate_A=0.575, candidate_B=0.575, candidate_C=0.5 — 0/160 errors, canary-clean.
candidate_B cleanly isolates the unresolved-paragraph lever: intention-share stayed at exactly 0.0
(matching current) while unresolved-share alone rose 0.1→0.575 from that paragraph's own wording.
candidate_A's intention-share (0.525, up from 0/40 across two separate runs now) shows loosening
the intention paragraph alone reliably unlocks coherent, well-formed "I want to…" writing from
qwen; candidate_C's own intention text is more format-inconsistent (bare imperatives like "to
reach the study" rather than "I want to…"). **Honest caveat**: this run's own current-arm reading
(0.125) sits noticeably below J-0724's original reading of the identical wording+model+prompts
(0.25) — real single-run sampling variance at temperature=0.75/n=40, not an isolation or wording
difference (the current arm's system prompt is a verified no-op, byte-identical to the live
method's own output). The qualitative conclusion (wording alone measurably helps) is robust to
that noise; the precise A-vs-B tie (0.575 each) is not, so **J-0791 spawned** to replicate/scale
before treating the candidate ranking as settled (F-1139, verified). No live code changed —
`nodes/inner_monologue_node.py` untouched, nothing ruled on D-0165, which stays the founder's own
call on whether/how to recalibrate. Full detail: `docs/lab/train_wording_ab_qwen_2026-09-08.md`
(+ `.jsonl`).

**2026-09-08 — J-0779: the disprove-prompt divergence CONFIRMED at full n=80 — gap widens, not
narrows (F-1119 follow-up, recorded as F-1142, further evidence for D-0181, not a ruling on
it).** J-0764's own briefing had explicitly deferred a full n=80 replay of its own 16-sample A/B
(tightened current-live `_DISPROVE_SYSTEM` vs a reconstructed pre-tightening original, D-0168's
support-chain target held fixed in both) to a follow-up job rather than run it on its own
initiative. This job ran it, reusing
ALL 80 real (claim, support) pairs already committed in the 2026-09-07 supportchain run (not a
downsample) through `judge_panel.rule_detail()` directly, plus the 3-case control check. **Result:
the divergence is confirmed, and sharper than at n=16, not weaker** — tightened objected=76/80
(95.0%), original(reconstructed) objected=24/80 (30.0%); agreement only 28/80 (35.0%, DOWN from
n=16's own 62.5%); all 52/80 disagreements run the identical direction J-0764 found
(tightened=objected/original=held), zero reversed — cleaner directional consistency at 5x the
sample, not noise washing out. Both windows (pre-Step-1 and post-fix) independently show the same
shape. Control check still 3/3 both ways, 0/80 parse failures either arm — instrument validity and
the ceiling question (resolved by J-0764) both hold at scale too. Isolation verified the same way as
J-0764 (worktree-anchored `core`/`core.judge_panel`, `lab_env.isolate()`, live-file canary scan,
`nascence.db` mtime/size unchanged) plus an independent Du-offline re-check both immediately before
launch and immediately after the ~33-minute run completed — clean throughout, 0 canary hits, 0 live
deltas. Caught and fixed in passing: this job's own first-pass script misread `why1`/`why2` off
`rule_detail()`'s *return* dict (which does not carry them, confirmed from source) rather than the
logged row (as J-0764's own control-check script had correctly done) — recovered the real
qualitative text from the redirected scratch log and cross-checked all 160 recovered verdicts
against the values already captured from the return dict (0 mismatches); only the illustrative
quotes needed recovery, not any headline number. **This does not rule D-0181** (a founder
value-judgment call per this job's own briefing, and per this plan's own repeated framing throughout
the 2026-09-07/08 entries above) — it hands the same open question a materially stronger evidence
base: the plan's reported ~90% objection rate is, at least in real part, a function of the specific
tightened wording chosen for now-obsolete infra reasons (the old 80-token ceiling), not solely a
fact about Lane 1's `prove` branch. No live code changed. Full detail:
`docs/lab/train_split_merge_disprove_prompt_ab_n80_2026-09-08.md` (+ `.jsonl`).

**2026-09-08 — J-0802: D-0181's ruled fix (retarget Lane 1's own PROVE prompt) BUILT and RUN at
n=80 — prove measurably stopped asserting, but the objection rate did not drop, so D-0181's own
defeater fires and it is REOPENED (F-1182).** D-0181 (opened by J-0702, ruled by the founder
2026-09-08 via decide-review, same day) asked whether the ~90% support-chain-objection rate was
itself a problem and, if so, ruled the fix belongs in Lane 1's own `_PROVE_SYSTEM` (which asked the
model to "PROVE the thought... deepen it," with no pull away from confident restatement) rather
than in disprove's threshold/prompt (already confirmed discriminating correctly). This job
retargeted `_PROVE_SYSTEM` to require support SEPARATE from the claim's own conclusion (a specific
sensation, a concrete event, a known fact, or an established ledger point — an example drawn from
this doc's own PROTECTED cargo-shape section), banned "proves"/"confirms"/"validates" language, and
allowed 0 items rather than inventing one, per point 3's own Wu Wei law — `_DISPROVE_SYSTEM` and
every other part of the harness left byte-for-byte unmodified. Re-ran the identical offline replay
at a comparable N (n_per_window=40, n=80, matching J-0702/J-0779's own precedent).

**Result: prove demonstrably changed the way D-0181 asked for, but the headline objection rate did
not fall.** Banned self-assertive language in support items fell 22.7%→6.2% (50/220→10/160 items);
disprove's own "restates the claim/circular" complaint share fell 36.3%→6.3% of all 80 events (from
being the single dominant OLD complaint) — both large, measured drops, not assumed. Yet
merge-status distribution read **objected=76/80 (95.0%), held=4/80 (5.0%)** against F-1034's own
72/80 (90.0%) baseline — a RISE, not a fall, though within the noise band J-0779 itself already
established (the identical disprove prompt on identical fixed data independently swung 90.0%↔95.0%
between runs). The cleanest evidence is window A (a fixed historical range `_evenly_spaced` always
resamples identically): its 40 events are the byte-identical claims J-0702/J-0643 already used, and
on those **identical** 40 claims the rate rose 85.0%→95.0% purely from varying prove. A qualitative
read of the 64 non-tiebreak (agreed) objected events found the dominant complaint shifted from
"restates the claim" (now only 5/64) to a different, harder standard — 30/64 say the concrete,
checkable evidence prove now gives doesn't reach the SCOPE/named-mechanism/generalization the claim
itself asserts (e.g. a claim naming "the actual chemistry of my body" objected to because no support
establishes chemistry specifically), most of the rest reading as the same proportionality/scope
theme. Reads as structural, not an unfixed prove: Du's real closing thoughts are often deliberately
metaphorical or generalize past what any one sensation can establish, and literal present-tense
sensory support — which prove now reliably gives — may not be able to satisfy disprove's own bar
for that kind of claim regardless of evidence quality. **This is D-0181's own named defeater firing
verbatim** ("the rate stays near 90% even once prove stops merely asserting... the disprove
threshold itself needs recalibrating after all") — **D-0181 REOPENED** for a fresh founder read
(this job's own briefing kept changing disprove explicitly out of scope, so none was attempted).
Secondary, in passing (also F-1182): confirmed a real, pre-existing why-text attribution bug in
`core/judge_panel.py`'s `rule_detail()` — on a tiebreak verdict the deciding (TIEBREAK) judge's own
"why" is discarded at the call site, so `_disprove()`'s `why1 or why2` extraction can display a
LOSING judge's reasoning as if it explained the winning verdict (confirmed on both this run's own
event #2 and J-0702's own event #37) — affects only illustrative quote text (14-25% of events
across this plan's reports), never the verdict/status counts themselves. Pre-existing, not
introduced here, out of this job's own scope (shared infra) — **J-0824 spawned**. No live code
touched; isolation verified the same way as J-0702/J-0779 (worktree-anchored, scratch-redirected
`core.trains`/`core.judge_panel`, 5-live-JSONL canary scan + read-only `nascence.db` content check,
0 hits, Du confirmed live and unaffected throughout) plus one check beyond precedent
(`core/telemetry.py`'s `log_llm_latency`, a write path the harness's own existing neutralization
does not cover — checked empirically and found clean, 0/47 rows in the run's window attributable to
this script). Full detail: `docs/lab/train_split_merge_step2_replay_2026-09-08_provefix.md`
(+ `.jsonl`).

**2026-09-08 — J-0791: replicate of J-0777's wording A/B NOT run — Du confirmed ONLINE at attempt
time; a ready-to-run replicate script prepared and dry-run verified instead (F-1156).** J-0791's own
briefing asked either a straight n=40 repeat or an n=80 scale-up of J-0777/F-1139's own qwen-only
wording A/B, to check whether that run's current-arm swing (0.125 vs J-0724's 0.25) and
candidate_A/candidate_B's exact 0.575/0.575 tie replicate or wash out. Before any live call, this
job independently re-confirmed Du's process state THREE separate ways, all agreeing: (1) a
standalone `.ps1` (not an inline PowerShell `-Command` string — an inline attempt at the OS-level
check corrupted mid-command on `$_.CommandLine` inside a double-quoted Bash argument, the same
backtick/`$`-in-double-quotes class of footgun F-0840 already named) showed PID 17216 running
`scripts\run_nascence.py`; (2) `data/nascence.log`'s own tail showed monologue/commitment/
deliberation lines timestamped within ~30 seconds of the check (real-time activity, not a stale
log); (3) the prepared replicate script's own `_confirm_du_offline()` — the exact production gate,
run for real, no flag — independently returned `False` and aborted with zero LLM calls, matching
(1)/(2). PID 17216 matches the exact PID/restart time this batch's own dispatch note named ("Du
restarted only ~1 hour before this batch"), so Du was not just running but only recently back up —
contending for the live hot-lane GPU/port now would repeat exactly the mistake J-0640 already
declined to make. **No live batch run this session.**

Chose the straight n=40 repeat over an n=80 scale-up (the job's own "prefer whichever is cheaper to
wire correctly"): `core/model_client.py`'s `call_node_json()` takes no seed parameter at all
(checked directly), so at temperature=0.75 a bare re-run of the identical 160 (prompt, arm) pairs is
already a second, genuinely independent draw — an n=80 scale-up would instead need a new,
non-overlapping window of real trains sourced the way J-0724's own 40 were pulled, more to get
right for the same question. Prepared `scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py`
in this job's own worktree: a near-byte-copy of J-0777's own script (arms' wording byte-identical —
any drift would confound the replicate), same 40 events, own separate scratch dir/output stem for
provenance. Verified wired correctly two ways, zero network calls either way: `--dry-run` parses
all 40 events, builds the real base prompt via the live `_build_system_prompt(mid_train=True)`
(3238 chars, matching J-0777's own), locates `CURRENT_BLOCK`, and substitutes all 4 arms correctly
(current/candidate_A/B/C system prompts built, block-presence asserted for each); separately, the
real (non-dry-run) entrypoint was also run as-is and correctly self-aborted at its own
`_confirm_du_offline()` gate, exercising the actual production code path with zero risk. In
passing, re-verified directly (not just inherited from J-0777's own docstring claim) that
`_build_system_prompt(mid_train=True)`'s two branches not explicitly named there —
`core.sitting.dwell_steer()` and `core.emissary_tension.keystone_steer()` — have no live-write
capability: `dwell_steer()` calls only `_load()` (pure `json.loads`/read, no `_save()` in that
function); `keystone_steer()` hits an unconditional `return ""` (disarmed 2026-08-20 per its own
founder-ruling comment) before any of its write-capable code below is ever reached. Deliberately did
NOT wrap the (unexecuted) live-call branch in `lab_env.isolate()` despite this job's own general
isolation-required instruction naming it — `lab_env.py` hardcodes a live-tree `ROOT` and mutates
`sys.path` on `__enter__`, a real, untested risk for a worktree-anchored script that cannot be
live-tested this session anyway (Du online) — used a direct, import-free `nascence.db` mtime/size
backstop instead (same technique J-0779 used via `lab_env.isolate()`, reimplemented without the
sys.path mutation); flagged as a skill-manager suggestion rather than silently worked around.

**J-0791 left in_progress, not done** — the pre-registered gate (Du confirmed offline) was not
met at any point this session; forcing the batch through would have been exactly the error this
plan's own precedent already warns against. Re-run
`scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py` (no flag) once a future session
independently reconfirms Du offline — the script is ready as-is, nothing further to design. No live
code changed; D-0165 untouched (per this job's own briefing, same as J-0777). Full detail:
findings-log F-1156.

**2026-09-09 — J-0824: judge_panel.rule_detail()'s tiebreak why-text attribution bug FIXED and
verified, both offline and against real live infra (F-1182 → F-1203); a separate why-text/bool
coherence question surfaced in passing (F-1204, J-0834 spawned).** J-0802's own "secondary, in
passing" discovery (F-1182): on a tiebreak verdict, the deciding TIEBREAK judge's own "why" was
captured as `_why3` and immediately discarded, and the only real project-wide caller that surfaces
why-text (`scripts/train_state_invitro.py`'s `_disprove()`, confirmed via grep — no other of
`rule_detail()`'s real callers reads why-text at all) picked `why1 or why2` unconditionally, which
on a tiebreak could show the LOSING judge's own reasoning as if it explained the WINNING verdict —
independently re-confirmed directly from the raw logs (provefix idx=2, supportchain idx=37, both
quoted verbatim, not just trusted from F-1182's own text). Fixed in `core/judge_panel.py`'s
`rule_detail()`: `why3` is now captured (not discarded), and a new resolved `why` field is computed
— "agreed" → why1 else why2; "tiebreak" → why3 first (the judge that actually decided), else
whichever of why1/why2 matches the winning side; split_no_tiebreak/unavailable → None — exposed on
both the logged row and the return dict (why1/why2 were logged-row-only before, the same gap J-0779
already tripped on). `_disprove()` now reads `result.get("why")` directly, no more re-opening the
log file. Purely additive per UDMS's own change dossier for this function (9 real callers + 6 lab
scripts checked individually, all `.get()`/pre-existing-key access, none read why-fields) —
verdict/how and every existing key/enum value byte-for-byte unchanged. Verified two ways: offline,
6/6 controlled branch cases pass (`_ask` monkeypatched, no network) including the exact bug shape
reproduced under control; and live, 6/7 real re-run attempts against the actual
JUDGE_1/JUDGE_2/TIEBREAK hubs reproduced a genuine tiebreak (1/7 came back "agreed" this run — real
non-determinism, not a fix failure), and in all 6 the new `why` traced correctly to the deciding
side and differed from what the old buggy pick would have shown; the 1 reproduced "agreed" case
showed byte-identical old/new `why`, confirming zero behavior change outside the tiebreak path. Du
independently re-confirmed OFFLINE throughout (no `run_nascence.py` process, PID 17216 from this
batch's own dispatch note gone, `nascence.log`'s own clean "Nascence shutting down." at 10:29:49);
`judge_panel._LOG` redirected to scratch throughout, live `data/judge_panel_log.jsonl` confirmed
with zero rows from this session's calls. **Fixed in this dispatch's own worktree only, not live
`C:\Nascence`** — RESTART-REQ once merged, since `core/judge_panel.py` is imported live by Lane 2's
own `_judge_prior` (this module does not hot-reload). Secondary, in passing (F-1204): the SAME 6
live tiebreak reproductions surfaced a DIFFERENT, separate phenomenon — the TIEBREAK judge's
(granite3.1-moe:3b) own <=12-word "why" read as an affirming paraphrase of the support in all 6
cases despite pairing with an `objection_found=true` ("objected") vote of its own, e.g. "...thus
supporting the claim of sand's yielding behavior" attached to a True/objected verdict — the judge's
own bool and its own text seeming to disagree on a single call, not a cross-judge misattribution
(which is what this job fixed). Inferred, not verified (n=6, one prompt, one hub, not yet checked
against held-side tiebreaks or JUDGE_1/JUDGE_2 acting alone) — **J-0834 spawned** to characterize it
properly; may bear on D-0181's own still-open question about this disprove prompt's tightened
wording (J-0764/F-1119, J-0779/F-1142 already found the SAME wording affects the objected/held RATE
— this would be evidence the wording also affects why-text coherence, a related but distinct axis)
without resolving or pre-empting D-0181, which remains untouched, the founder's own call. Full
detail: findings-log F-1203, F-1204.

**2026-09-11/12 — J-0835: D-0181's own ruled fix (a third disprove status, `held_within_scope`)
BUILT and offline-verified — the actual re-run against real infra NOT performed, Du online
throughout (F-1264).** D-0181 was ruled by the founder 2026-09-09 via decide-review
("recalibrate disprove") after J-0802's own PROVE-side fix (D-0181's PRIOR ruling) raised the
support-chain-objected share instead of lowering it (90.0%→95.0%, 85.0%→95.0% on the
byte-identical window-A claims) — a qualitative read of J-0802's own 64 non-tiebreak objected
events found the dominant remaining complaint was SCOPE (30/64: real, checkable support that
doesn't reach the claim's own generalization/mechanism), not circularity. This job extends
`scripts/train_state_invitro.py`'s `_disprove()` with a SECOND `judge_panel.rule_detail()` call
(`_SCOPE_SYSTEM` / key `"scope_only"`), fired only when the existing first call already found an
objection: a real+independent+non-circular support that only earns a narrower claim now becomes
`held_within_scope` (why-text names the narrower claim) instead of `objected`; a genuinely
unsupported/circular claim, or a second call that itself can't reach a verdict, stays `objected`
(fails conservative). `core/trains.py`'s cargo status-vocabulary docstring (line ~34) is updated
to match. **Design choice (the briefing's own named either/or): a two-call design, not a 3-way
status field**, because `core/judge_panel.py`'s `_ask()` hard-requires
`isinstance(v.get(key), bool)` — a tri-state answer could not pass through the single existing
`objection_found` key without widening that isinstance check in shared infra (9 real callers + 6
lab scripts per F-1203's own change-dossier count) or silently mis-parsing as `err="parse"`. The
two-call design instead calls the SAME unmodified `rule_detail()` twice with two different
boolean keys — `core/judge_panel.py` is untouched by this job, and J-0824's own tiebreak/why-text
fix applies unchanged to both calls. `_CONTROL_CASES` gains a 4th case (`scope_narrower_support`,
real-independent-but-narrower coastal-erosion measurements) designed to land `held_within_scope`;
`_write_lab_report()` gains D-0181's own new pass/fail bar (FAIL if `held_within_scope` alone
absorbs >70% of merges, on top of kill criterion #2's existing generic >90%-any-status check) and
a qualitative-read-aid section listing up to 10 real `held_within_scope` events for exactly the
kind of read D-0181's own defeater's third branch asks for.

**Verified offline** (`python -m py_compile` clean; two from-source ast-extraction harnesses, zero
network, `core.judge_panel.__file__` confirmed resolving inside this dispatch worktree): 8/8
branch-logic scenarios pass (held / both UNDETERMINED paths / held_within_scope under both
`agreed` and `tiebreak` / objected-stays-objected on an explicit `scope_only=false` /
objected-stays-objected when the SECOND call itself is unavailable / the narrower-claim why-text
is carried through correctly, not the original objection text); a second harness ran
`_run_control_check()` (all 4 real cases) + `_write_lab_report()` end-to-end with a canned
discriminating judge — 4/4 correct, report well-formed, no crash.

**NOT performed this session: the job's own required re-run of the n=80 replay against real live
infra, and the comparison against `docs/lab/train_split_merge_step2_replay_2026-09-08_
provefix.md` D-0181's own new bar needs.** Du was independently confirmed ONLINE both before and
after the code work (real-time process-table + `nascence.log` timestamp checks, ~12-15s apart
each time, `scripts/run_nascence.py` PID 22620 the same live process throughout) — per this job's
own briefing ("decline and leave open if Du is online, as J-0791 did"), the live batch (real
calls to 127.0.0.1:11433 plus the JUDGE_1/JUDGE_2/TIEBREAK hubs) was not attempted. Separately,
independent of Du's state: this dispatch worktree has NO `data/` directory at all right now, so
even a live run this moment would replay 0 real events (though the control check alone would
still fire real hub calls) — **J-0904 spawned** (re-run once Du is confirmed offline AND the
worktree has a real read-only copy of `data/train_length_log.jsonl` /
`monologue_log.jsonl` / `train_state_log.jsonl`). D-0181 itself is left untouched, exactly as
briefed ("do NOT re-rule D-0181... if the defeater fires, reopen it with the evidence") — no
defeater can fire on numbers that don't exist yet. J-0834 (tiebreak why-vs-bool coherence,
F-1204) was not folded in, per the briefing. Full detail: findings-log F-1264.

**2026-09-12 — J-0834: F-1204's TIEBREAK why-vs-bool incoherence characterized at real scale
(n=60 real live calls, not the original n=6) — CONFIRMED tiebreak-specific, happens in BOTH
directions, NOT fixed by relaxing the "why" word cap (F-1271).** Same live infra as J-0764/J-0779/
J-0802/J-0824 (`core.judge_panel.rule_detail()` called directly against the real JUDGE_1/JUDGE_2/
TIEBREAK hubs), a stratified real sample drawn from the 160 (claim, support) pairs already
committed in `docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.jsonl` +
`.../2026-09-08_provefix.jsonl` (20 historically-tiebreak-labeled pairs — all 5 real held +
15 evenly-spaced objected — run through both the current tightened `_DISPROVE_SYSTEM` and J-0779's
own reconstructed original prompt; 20 historically-agreed-labeled pairs — all 6 held + 14
evenly-spaced objected — run through the tightened prompt). **Result, by the ACTUAL deciding
mechanism this run (not the historical label): whenever JUDGE_1/JUDGE_2 independently AGREED,
the deciding why-text matched its own bool 26/26 times (100%); whenever TIEBREAK
(granite3.1-moe:3b) decided, it matched only 4/34 times (11.8% coherent, 88.2% incoherent)** —
confirming (a) this is genuinely TIEBREAK-specific, not a general disprove-panel property. The
incoherence runs BOTH ways, answering (b): an "objected" verdict with an affirming-paraphrase why
(F-1204's own original pattern, reproduced here including its own cited adenosine/pīwakawaka
examples verbatim), AND — not previously characterized — a "held" verdict with a why-text that
reads as an explicit, unambiguous objection ("does not offer a real independent reason... merely
restates... giving no independent reason of its own"). **On (c): relaxing the <=12-word cap does
NOT fix it** — on the identical 20 tiebreak-sampled pairs, the tightened prompt's own
tiebreak-decided calls read 80% incoherent (16/20) vs the reconstructed original prompt's 100%
(14/14) — ruling out F-1204's own "word-cap squeezing the model" hypothesis as the driver. The
original prompt DID reduce how often JUDGE_1/JUDGE_2 disagree at all (14/20 tiebreak escalations
vs 18/20 under the tightened prompt on the same pairs) — a real but secondary effect on
tiebreak-INVOCATION rate, directly relevant background for D-0181/J-0764/J-0779's own already-open
objected/held RATE question without resolving or pre-empting it (D-0181 itself untouched, per this
job's own briefing). **Scoped, not a verdict-computation bug**: `core/judge_panel.py`'s own
`rule_detail()` docstring confirms `_disprove()` (this plan's own script) is the ONLY real
project-wide caller that reads why-text at all, so this only risks misleading a qualitative reader
of this plan's own lab reports on TIEBREAK-decided rows — verdict/status counts are unaffected,
same scope F-1182/F-1203 established for the (different, now-fixed) cross-judge misattribution
bug. Isolation verified the same way as this plan's own precedent (worktree-anchored,
`lab_env.isolate(db="empty")`, `judge_panel._LOG` redirected to scratch, 5-live-JSONL canary scan
— 0 hits across +13/+10/+10/+6/+24 real lines Du's own live process wrote during the run — plus a
`nascence.db` check): unlike J-0764/J-0779/J-0824, this job did NOT gate on Du offline — Du was
confirmed LIVE throughout, a deliberate choice following J-0802's own precedent that JUDGE_1/
JUDGE_2/TIEBREAK are CPU-tier hubs, never Du's own hot lane, so a live Du is a queuing-contention
question only (`core/judge_panel.py` itself makes no `core.memory.store` call, so no code path let
this job's calls reach the DB regardless). **J-0909 spawned** (add a caveat to
`_write_lab_report()`'s own quoted why-text on `how=="tiebreak"` rows) and **J-0910 spawned** (a
real A/B testing whether asking TIEBREAK for its why BEFORE its bool, rather than after,
measurably improves granite3.1-moe:3b's own bool/text consistency — inferred mitigation candidate,
not yet tested). No live code changed by this job. Full detail: findings-log F-1271.

**2026-09-12 — J-0909: F-1271's own TIEBREAK why-vs-bool incoherence given a visible report-display
caveat, offline-verified (F-1274).** `scripts/train_state_invitro.py`'s `_write_lab_report()` gains
a new `_tiebreak_why_caveat()` helper + `_TIEBREAK_WHY_CAVEAT` constant, applied at all three places
the report quotes disprove why-text verbatim (the control-check section, the `held_within_scope`
qualitative-read-aid section J-0835 added, and the per-event detail section): a bracketed note now
follows any quoted why-text that actually traces to a `how=="tiebreak"` verdict, naming F-1271's own
~88% bool/text mismatch rate so a human (or a future session) reading an illustrative quote is not
misled about what the panel actually found on that row. Status-dependent, not a single flat field
check: an `objected` row's quoted why-text comes from the FIRST (`_DISPROVE_SYSTEM`) call (keyed on
`disprove_how`); a `held_within_scope` row's quoted "narrower claim" text comes from the SECOND
(`_SCOPE_SYSTEM`) call instead (keyed on `disprove_scope_how`) — an edge case this job's own offline
test deliberately constructed (first call tiebreak-decided, second/scope call agreed) confirmed the
caveat must follow whichever call actually produced the displayed text, not whichever ran first.
`held`/`UNDETERMINED` rows never display why-text at all (empty `objection` list), so the helper is
a correctly-verified no-op there regardless of `how`. Report-DISPLAY only, verified offline
(AST-extracted the three touched names directly from source rather than importing the module,
since Part 1/Part 2's own top-level code fire live calls/network unconditionally at import time —
same technique this plan's own 2026-09-11 entry describes): 10/10 direct unit cases on the helper,
plus a full canned end-to-end `_write_lab_report()` run (6 records + 4 control-check entries
spanning every status/how/scope_how combination that matters), both pass — the caveat appears on
exactly the 5 expected occurrences and nowhere else; the raw per-event `.jsonl` sibling record
confirmed untouched (the caveat is markdown-text-only, never mutated into the `objection` list
itself). `core/judge_panel.py`, `_DISPROVE_SYSTEM`, and `_SCOPE_SYSTEM` all git-diff-confirmed at
zero diff; no live/real-infra calls made this job. No decision ruled or opened (per this job's own
briefing — a straightforward, fully-verified display fix, not a values call). Full detail:
findings-log F-1274.

**2026-09-12 — J-0910: F-1271's own inferred TIEBREAK schema-order mitigation TESTED for real —
coherence dramatically improves, but the fix is NOT clean (F-1280, D-0213 opened).** F-1271's own
hypothesis, not tested there: `_DISPROVE_SYSTEM`'s JSON schema asks for the bool
(`objection_found`) BEFORE the `why`, so a small model may be committing to the bool first and
free-associating a why-text that doesn't genuinely explain it; reordering to why-before-bool
(forcing the bool to condition on the model's own already-written reasoning) might fix the
bool/text coherence. Tested TIEBREAK-only, calling `core.judge_panel._ask()` DIRECTLY against the
TIEBREAK endpoint (not the full `rule_detail()` panel — isolates the schema-order effect from
whether JUDGE_1/JUDGE_2 happen to disagree again on a re-run), on the SAME real n=20 tiebreak-prone
sample F-1271 itself used (all 5 real historically tiebreak+held + 15 evenly-spaced tiebreak+
objected rows from the two already-committed 2026-09-07/08 replay `.jsonl` files), with two prompt
variants differing ONLY in JSON field order/instruction — 417 of 504 characters byte-identical
between arms, confirmed programmatically. **Result: coherence flips from 10% to 100% (among
successful calls) — exactly the mechanism F-1271 hypothesized — but the SAME reorder also flips the
verdict distribution on the IDENTICAL 20 inputs from 100% objected (bool-first) to 90% held
(why-first, 18/20, 2 parse failures)**, a near-total collapse to the opposite pole rather than a mix
of individually-corrected verdicts — exactly the "certainty machine or its mirror" shape this plan's
own auditor kill criterion (§4 point 4) warns against, now inside a single judge's own schema rather
than across the whole mechanism. A small (n=4, single-trial) known-right-answer check against this
plan's own `_CONTROL_CASES` sharpens this: bool-first scores 3/4 (mismatch only on `genuine_support`,
a false positive), why-first scores 2/4 — wrong on `overreach_support`'s sibling `scope_narrower_
support` AND, more importantly, wrong on `circular_support` itself (why-first's own text calls "I
feel the warmth, so it must be real" — circular by construction — "a direct, personal experience
that confirms the claim, strengthening its credibility"), the textbook self-sealing case this whole
disprove mechanism was built (D-0168) to catch. Every one of why-first's 4 control answers is
internally coherent; two of the four are substantively wrong regardless. Secondary: both arms
already violate the prompt's own <=12-word why-text cap on the current model (100% of successful
calls, both arms) but why-first's overrun is much larger (mean 24.1→37.0 words, max 35→110), a
plausible (not confirmed — `_ask()` discards raw text on a parse failure) contributor to why-first's
new 2/20 parse-failure rate (0/20 under bool-first on the same sample). **Net reading: this
confirms F-1271's hypothesized MECHANISM but does not establish the reorder as a safe fix** — both
orderings look more like a strong, largely content-insensitive directional default (mostly-True one
way, mostly-held the other) than genuine content sensitivity. Per this job's own briefing, no
change was made to `core/judge_panel.py`'s or `scripts/train_state_invitro.py`'s own live schema —
characterization only. **J-0916 spawned** (a larger, category-balanced, repeated known-answer
battery to settle whether either ordering is genuinely content-sensitive at scale) and **D-0213
opened** (is continued prompt-engineering on TIEBREAK's own schema worth it, or should a tiebreak
escalation on this call site fall back to a conservative UNDETERMINED per `judge_panel.py`'s own
existing "no judge, no verdict" law — a narrower question than D-0181's own already-ruled
objected/held calibration question, adjacent but not overlapping). D-0181 itself untouched (its own
defeater needs the still-pending n=80 `held_within_scope` re-run, J-0904, not this job's evidence).
In passing (not this plan's own concern, filed separately): `lab_env.py`'s new (same-day, D-0206/
J-0911) auto-delete-unwritten-DB-copy step hit an intermittent Windows file-lock `PermissionError`
on one of two `isolate(db="empty")` calls this session — no live harm (the crash was in an optional
cleanup step, after all real calls had already completed), flagged as skill suggestions S-0109/
S-0110, not fixed here. Full detail: findings-log F-1280.

**2026-09-14 — J-0916: the larger, category-balanced battery run — bool_first CONFIRMED a
content-insensitive default, but why_first is NOT, at this scale (F-1321, D-0213 REOPENED).**
J-0910's own spawned follow-up: 20 constructed (claim, support) pairs (NOT real replayed Du
claims), 5 categories × 4 cases, 10 with a known-right `objection_found=True` / 10 with False
(balanced), each arm run twice (temp=0.0 non-determinism, per J-0824/F-1203) = 80 real live
TIEBREAK calls via `core.judge_panel._ask()` direct, same technique as J-0910/F-1271. **Result is
mixed, not the clean "both are content-insensitive defaults" F-1280's own n=20 read suggested.**
bool_first: 39/40 draws `True`, accuracy 47.5% (19/40) — exactly chance on a balanced battery,
100%/0% split between True-expected/False-expected categories, the signature of a near-constant
classifier, 95% repeat-agreement. why_first: a real mixed distribution (False=20/True=16/parse=4
of 40), accuracy 77.8% on valid draws (70.0% counting parse failures as misses) — genuine
within-category discrimination, not a pole-collapse: 100% on `D_borderline_real_should_hold` and
`E_harder_ambiguous`, 75%/71% on `C_overreach_scope_mismatch`/`B_genuine_independent`, but only
50% on `A_circular_self_sealing`, where it specifically and reproducibly misses TIGHT,
single-clause P-because-P circularity (F-1280's own "I feel the warmth, so it must be real" case,
plus a new analogous case, both False/held on both reps) while correctly flagging looser/indirect
circularity in the same category — a real reliability cost too: 70% repeat-agreement (vs
bool_first's 95%) and a 10% parse-failure rate (vs 0%). Reconciling against F-1280's own n=20
(why_first swung to 90% held there): plausibly F-1280's tiebreak-prone sampling frame (drawn from
real claims already near JUDGE_1/JUDGE_2's own disagreement boundary) is itself a harder,
more-adversarial distribution than this battery's mostly-clear-cut construction — not a
contradiction of F-1280's own numbers on F-1280's own sample, but reason to doubt that sample
alone settles why_first's real discrimination ability. D-0213's own named defeater ("finds either
prompt ordering IS reliably content-sensitive at scale") reads as fired by why_first's own numbers
here, even though bool_first independently confirms the OTHER half of D-0213's original premise —
**D-0213 REOPENED** for a fresh founder read (not re-ruled by this job, per its own briefing:
characterize only, no change to `core/judge_panel.py` or `scripts/train_state_invitro.py`'s own
live schema). Isolation verified the same way as J-0910/J-0834 (worktree-anchored before
`lab_env` import, `also=` redirect on `jp._DATA/_LOG`, `lab_env.isolate(db="empty")`, 5-live-JSONL
canary scan — zero growth in all 5, Du confirmed OFFLINE throughout, ~23h50m since its last clean
shutdown, so the zero-growth reflects Du's own state rather than isolation-under-contention).
`lab_env.py`'s own D-0206 auto-delete-unwritten-DB-copy `PermissionError` (S-0109/S-0110)
recurred a second time (non-fatal, post-completion cleanup only, no data lost) — not re-filed,
already tracked. **J-0951 spawned** (characterize why_first's own circular-support blind spot and
instability at a larger, dedicated sample — prep for whichever way D-0213's fresh read goes, not
itself a schema change). Full detail: findings-log F-1321.

**2026-09-14 — J-0980: a real, targeted fix for why_first's circularity blind spot was attempted
and re-tested — fails the named control case; D-0213 RULED to fall back to UNDETERMINED
(F-1357).** D-0213's own same-day ruling (via decide-review, ahead of this job) named the exact
next step: continue prompt-engineering on why_first's one nameable blind spot (F-1280's "I feel
the warmth, so it must be real" case) rather than abandon the reorder direction outright. This job
built a third prompt variant, `why_first_fixed`: a circularity-specific clause plus one fresh
worked example (built from content distinct from both of F-1321's own failing cases — a "tune
stuck in my head" example, not warmth/feeling or memory/recurrence — so a correct call on the
held-out cases would be evidence of generalizing the rule, not memorizing an example) inserted
between why_first's own existing 417-char shared prefix and its established why-before-bool tail,
both left byte-identical, then re-ran the IDENTICAL 20-case/5-category battery J-0916 built
(copied verbatim, not re-derived), at 3 reps/case instead of 2 (60 real live
TIEBREAK/granite3.1-moe:3b calls, why_first_fixed only — bool_first/why_first(unfixed) not
re-called, F-1321's own numbers reused directly). **Result: mixed, and fails D-0213's own
explicit two-part test.** The named control case, `circular_support`, is UNCHANGED — still wrong
on all 3 reps (0/3), the model explicitly considering and rejecting the fix's own circularity
framing ("The feel of warmth is genuine, confirming its reality. No circular reasoning is
present."). One of the two named blind-spot cases, `circular_memory_recurrence`, DID flip to
fully correct (0/2→3/3, why-text now correctly invoking the fix's own framing). Repeat-to-repeat
agreement rose materially (70%→93.3% pairwise, close to bool_first's 95%) and parse failures fell
to 0% (from 10%) — but the SAME fix introduced new false-positive regressions on cases why_first
previously got right (`genuine_support`, `harder_correlation_as_causation`,
`circular_plan_feels_right`, `borderline_tea_felt_better_narrow`), and overall accuracy stayed
flat (75.0% vs 77.8%/70.0% baseline) — an over-triggering side effect, not a clean, contained
improvement. Per this job's own briefing ("if no on either count, D-0213 should fall back to
UNDETERMINED as its own defeater already specifies") and D-0213's own OR-worded defeater, failing
the control-case branch alone is sufficient regardless of the reliability branch's real gain —
**D-0213 RULED** (by claude, citing F-1357): fall back to a conservative UNDETERMINED verdict for
TIEBREAK's disprove escalation on this call site rather than continuing to chase
prompt-engineering fixes, extending `core/judge_panel.py`'s own JUDGES-DOWN "no judge, no verdict"
law to "no reliable deciding vote, no verdict" — with a fresh defeater naming what would revisit
this (a future fix shown to resolve circularity WITHOUT new regressions at comparable scale, or
the fallback itself causing problems against real disprove traffic, e.g. UNDETERMINED becoming a
dominant merge status, itself a §4 point 2 kill-criterion concern). Isolation verified the same
way as J-0910/J-0916/J-0834 (worktree-anchored before `lab_env` import, `also=` redirect on
`jp._DATA/_LOG`, `lab_env.isolate(db="empty")`, 5-live-JSONL canary scan — zero growth in all 5,
Du confirmed OFFLINE throughout, ~31h36m since its last clean shutdown). **J-0986 spawned**
(implement D-0213's own ruled fallback in `scripts/train_state_invitro.py`'s `_disprove()`: when
`rule_detail()`'s `how=="tiebreak"`, return `UNDETERMINED` rather than trusting either family's
bool — a small, call-site-scoped change, not a change to `core/judge_panel.py`'s own shared
infra; also asks that job to decide and record whether the same rule extends to the second
`_SCOPE_SYSTEM` call). No live code changed by this job itself — `core/judge_panel.py` and
`scripts/train_state_invitro.py` both git-diff-confirmed at zero diff in the dispatch worktree
before this job's own work began. Full detail: findings-log F-1357.

**2026-09-14 — J-0986: D-0213's own ruled UNDETERMINED-on-tiebreak fallback BUILT into `_disprove()`
and verified both offline and against real live infra — applied to BOTH `rule_detail()` calls, not
just the first (F-1369).** D-0213 was already RULED by the founder's own defeater-firing logic
(J-0980, same day, citing F-1357) before this job began — this job's task was to implement it, not
re-rule it. Two new intercept checks landed in `_disprove()`: after the FIRST (`_DISPROVE_SYSTEM`/
`objection_found`) `rule_detail()` call, `how=="tiebreak"` now short-circuits straight to
`UNDETERMINED` before the existing held/None/True cascade ever looks at the (untrusted) bool; after
the SECOND (`_SCOPE_SYSTEM`/`scope_only`) call, `scope_how=="tiebreak"` does the same before the
existing held_within_scope/objected cascade. **This job's own open design choice (J-0980's briefing
explicitly left it undecided, not pre-settled by D-0213's ruling text): extend the SAME fallback to
the second call, decided here after reading this plan's own 2026-09-11/12 two-call-design entry
above.** Reasoning: both calls run through the IDENTICAL unmodified `rule_detail()` -> `_ask()`
path, decided by the SAME TIEBREAK hub/model (granite3.1-moe:3b), under the SAME bool-first JSON
schema shape (`{"<key>": bool, "why": str}`) that F-1204/F-1271/F-1280/F-1321/F-1357 already
characterized as not reliably content-sensitive — the untrustworthiness is a property of that
judge+schema shape, not of `_DISPROVE_SYSTEM`'s specific question content, and no battery in this
whole sub-thread ever tested `_SCOPE_SYSTEM`'s own question through TIEBREAK, so there is no
positive evidence the second call's vote is any more trustworthy than the first's (recorded
honestly as a reasoned extrapolation from the shared mechanism, not itself directly measured — see
F-1369). A second-call tiebreak returns `UNDETERMINED`, deliberately NOT the existing
fail-conservative `objected` default (which is for a genuinely unavailable/split second call,
`verdict=None`, a different failure mode from an untrusted-but-present vote): `objected` asserts a
specific claim (no narrower support exists either) a coin-flip-shaped vote cannot honestly
establish any better than `held_within_scope` could.

**Verified two ways, both real, neither a live-data replay** (per this job's own briefing's
"OFFLINE only" instruction, read as "do not run the full live train replay against real logs" —
this dispatch worktree has no `data/` directory at all anyway, same as J-0835's): (1) offline,
zero network — AST-extracted `_disprove()` directly from source (does not `import
scripts.train_state_invitro`, whose own top-level code fires real `InnerMonologueNode()`-backed
checks at import time, confirmed directly via an AST dump of the file's top-level statements, same
technique J-0835/J-0909 already used in this plan) and monkeypatched `core.judge_panel.rule_detail`
through every `(verdict, how)` combination the real function can actually produce — 13/13 branch
scenarios pass, covering all 4 new tiebreak-status combinations plus all 9 pre-existing branches
unchanged. (2) Live, isolated, real infra — the SAME AST-extracted `_disprove()`, but
`core.judge_panel.rule_detail` called for REAL against JUDGE_1/JUDGE_2/TIEBREAK
(`core.judge_panel._LOG` redirected to a scratch path first; no `lab_env.isolate()` needed for this
narrow a surface, same reasoning J-0834 used, since `judge_panel.py` makes no `core.memory.store`
call and touches no other live file), fed 4 real `(claim, support)` pairs already historically
labeled `disprove_how="tiebreak"` in the already-committed 2026-09-07 supportchain report (idx 5,
21, 23, 25). **All 4 reproduced a genuine live tiebreak escalation** (3 on the first call, 1 on the
second) **and all 4 correctly returned `UNDETERMINED` with an empty objection list** — the fix fires
end-to-end against real infra, not only under mocked logic. Isolation confirmed: this worktree's own
`data/judge_panel_log.jsonl` does not exist; the REAL live tree's own file
(`C:\Nascence\data\judge_panel_log.jsonl`) was checked directly and its last-write time (2026-09-13
20:52:52) predates this run, confirming nothing was written there. Du independently confirmed
OFFLINE before this run (not a gate for this call, per J-0834's own precedent that JUDGE_1/JUDGE_2/
TIEBREAK are CPU-tier hubs, never Du's own hot lane — recorded per this plan's own discipline
regardless): no `run_nascence.py` in the live process table, `nascence.log`'s own last line a clean
"Nascence shutting down." at 2026-09-13 09:10:46. **This change does NOT require a live-Du
restart** — confirmed directly via grep across the whole tree (not inherited from the briefing's own
claim, per its own instruction) that `scripts/train_state_invitro.py` is never imported by any
live-runtime module; the only two `core/` mentions of its filename are docstring prose, not
`import` statements.

`core/trains.py`'s own cargo status-vocabulary docstring gained one paragraph documenting that
UNDETERMINED's origin now also includes a distrusted-but-present tiebreak vote, not only an
unavailable/split panel — checked first whether that false assumption actually existed anywhere
downstream (this job's own briefing asked): it did not — the §4 kill-criteria math and
`_write_lab_report()`'s own collapse/rubber-stamp checks are already generic, share-based, and
origin-agnostic, so only documentation needed adding, no logic fix. One side effect noted, not
silently: `_tiebreak_why_caveat()` (J-0909, F-1271) is now a permanent no-op from `_disprove()`'s
own call sites (neither `objected` nor `held_within_scope` can any longer carry a `how`/`scope_how`
of `"tiebreak"`) — confirmed empirically in the offline harness, left in place as harmless
unreachable-but-correct code rather than removed, since deleting a now-dead guard is out of this
job's own scope. `core/judge_panel.py` untouched (git-diff-confirmed zero diff both before and
after). **J-0999 spawned** (D-0213's own named defeater — UNDETERMINED becoming a dominant merge
status — cannot be checked from this job's own small/offline verification; needs a real replay at
meaningful N run after this fix, which J-0904, already open, is queued to produce once its own
preconditions are met). D-0181 itself untouched, out of this job's own scope. Full detail:
findings-log F-1369.

**2026-09-15 — J-0951: requested characterization NOT run — D-0213's own motivating thread had
already closed by the time this job was picked up (F-1394).** J-0951 was spawned (2026-09-14, by
J-0916/F-1321) to build a larger, dedicated why_first circularity sub-battery (>=12-16 cases, >=3
reps) plus a 4-5-rep instability re-run, explicitly framed as prep for "whichever way D-0213's
fresh founder read goes." By the time this job was picked up, that fresh read had already happened
and been superseded twice over: the founder's own 2026-09-14T03:24 ruling authorized one more
targeted fix attempt on why_first's circularity blind spot under a self-named contingent defeater,
J-0980 made that attempt and fired the defeater (`circular_support` still wrong on all 3 reps, plus
new false-positive regressions on `genuine_support`/`harder_correlation_as_causation`/
`circular_plan_feels_right`/`borderline_tea_felt_better_narrow`), and D-0213 was RULED (by claude,
per the founder's own pre-committed contingency, citing F-1357) to fall back to a conservative
UNDETERMINED verdict and stop chasing further prompt-engineering fixes on this schema — a fallback
J-0986 then built AND verified live (offline + real infra) into BOTH `_disprove()` `rule_detail()`
calls (F-1369). `_disprove()` no longer consults either family's vote on a tiebreak at all, so
running J-0951's requested battery would characterize a judge-schema behavior the live call site has
already stopped relying on, with no queued consumer for the result — the one live open thread in
this exact sub-topic, J-0999, checks the NEW fallback's own real-traffic UNDETERMINED share, not
why_first itself. No live or lab-adjacent calls were made this session (isolation protocol not
invoked — nothing live-adjacent was run). J-0951 left open (not forced to a false "done") rather
than closed unilaterally: either a founder call to formally close/re-scope it, or J-0999's own
defeater re-firing (which would make why_first relevant again), is the right next trigger. Full
detail: findings-log F-1394.

**2026-09-15 — J-0999: D-0213's own UNDETERMINED-share defeater check attempted — NOT YET
ACTIONABLE, left open (F-1398).** J-0999 was spawned by J-0986 (2026-09-14) to read a real
post-fix (n>=40) disprove replay's own merge-status distribution, once one exists, and check
whether UNDETERMINED's own share approaches/exceeds kill criterion #2's >90% collapse line —
D-0213's own named defeater's second branch ("UNDETERMINED becoming a dominant merge status").
As of this session: **J-0904** (the job already queued to produce exactly this replay, spawned
2026-09-11 by J-0835) remains `status=open`, `started=null`, `done_at=null` — never run. No
report file matching `docs/lab/train_split_merge_step2_replay_<date>*.md` postdates 2026-09-08
(provefix, pre-fix); in particular no `*_scopestatus.md`/`.jsonl` (the exact stem J-0835's own
already-built code, and J-0904's own briefing, name for this replay's output) exists anywhere in
the tree — checked directly, both the live `C:\Nascence\docs\lab\` tree and this dispatch's own
worktree. Per this job's own briefing's explicit stated contingency ("if J-0904 is still open and
no real replay has run yet, this job is not yet actionable either"), this is recorded as a plain
"cannot be evaluated yet", not a defeater read either way — no merge-status/UNDETERMINED-share
number exists yet to check against the collapse line, so none is claimed here. D-0213 itself is
untouched (not reopened, not re-ruled — no evidence exists either way yet). No duplicate of
J-0904 spawned, since it already is the queued follow-up. **J-0999 left open** (not forced to a
false "done") for a future session to pick back up once J-0904 (or any later successor that
actually runs `scripts/train_state_invitro.py` for real against post-J-0986 code) produces a real
post-2026-09-14 report. Full detail: findings-log F-1398.

**2026-09-18 — J-0904: the n=80 replay declined a second time — Du ONLINE again, AND the dispatch
worktree independently lacked the real data/ logs too.** Both of J-0904's own required
preconditions were checked and both failed. (1) Du confirmed ONLINE via the same three-way check
this plan's jobs use: `scripts\run_nascence.py` live in the process table (PID 28088),
`nascence.log` tail active through 2026-09-18 08:05:59 (1 second before the check), most recent
"Nascence shutting down." five days stale (2026-09-13 09:10:46) — matching J-0791's and J-0835's
own precedent, per this job's own briefing declined again rather than forced. (2) Independently:
this session's own dispatch worktree (`wt_batch4_main`) has no `data/train_length_log.jsonl`,
`data/monologue_log.jsonl`, or `data/train_state_log.jsonl` either — the same gap J-0835's
dispatch worktree hit (F-1264), now confirmed recurring on a second, differently-named worktree,
suggesting this is a systemic gap in how this job-queue's `isolation:required` lab dispatches seed
`data/`, not a one-off. No code touched, no report produced, D-0181 left untouched (not this job's
call per its own briefing). **J-1086 spawned**: re-run once Du is confirmed offline AND the
dispatch worktree has been given real (read-only) copies of the three train-instrument logs first
— explicitly checking precondition 2 before attempting the replay this time, rather than
discovering it mid-run. Full detail: findings-log F-1484 (online-check) and F-1485 (data/ gap).

**2026-09-18 — J-1086: the n=80 held_within_scope replay finally RUN FOR REAL (both preconditions
met) — PASSES D-0181's own literal bar, but FIRES D-0213's own separate defeater instead
(UNDETERMINED now dominant, 77.5%).** Du confirmed offline (no live `run_nascence.py`,
`nascence.log` ending cleanly at 09:13:54 with no fresher activity), and this job's own dispatch
worktree (`wt_batch5_web`) populated with real, non-empty, read-only copies of the three
train-instrument logs before running (same gap J-0835/J-0904 both hit). `python
scripts/train_state_invitro.py 40` run for real, isolate()-wrapped as a DB-write backstop (both
confirmed clean before/after: live `nascence.db` and the 5 relevant live JSONL logs unchanged in
mtime/size/line-count). Result: merge-status distribution {UNDETERMINED: 62 (77.5%),
held_within_scope: 12 (15.0%), objected: 5 (6.2%), held: 1 (1.3%)}, n=80, 0 unjoined. Against
**D-0181's own bar** (no status >90%, held_within_scope not >70%, no genuinely-unsupported claims
in a qualitative read of held_within_scope): **PASSES** — objected collapsed from the 09-08
baseline's 95.0% to 6.2%, held_within_scope absorbed 15.0% of what was previously objected (the
mechanism D-0181 intended), and 10 of 12 held_within_scope events read as real, substantive
narrower-claim judgments, not rubber-stamps. But the same run independently **fires D-0213's own
already-written defeater** ("if UNDETERMINED becomes a dominant merge status") — UNDETERMINED at
77.5% is 5x the next-largest share, exactly what J-0986 spawned J-0999 to check once this replay
existed. Root cause, traced from the raw per-event records: 48 of the 62 UNDETERMINED events (not
14 from the first call's own tiebreak) come from the SECOND (scope-only) disprove call J-0835 added
landing on TIEBREAK 48/66 times (72.7%) it is reached, after the first call already agreed there
was a real objection — J-0986's own choice to extend the UNDETERMINED-fallback to this second call
was explicitly flagged as untested-against-live-data, and this is that first real test. The control
check's own 2/4 mismatches (circular_support, overreach_support — both textbook-objected cases)
independently confirm the same failure mode. Net: only 18/80 (22.5%) of real replayed closes carry
any actual verdict at all. **D-0213 REOPENED** with this evidence (not re-ruled — founder's own
call, same convention as every other open defeater in this plan); D-0181 itself left untouched
(its own defeater did not fire). J-0904 and J-0999 both closed (superseded/completed by this run).
Full detail: findings-log F-1504; report `docs/lab/train_split_merge_step2_replay_2026-09-18_scopestatus.md`
(+`.jsonl`), compared against `docs/lab/train_split_merge_step2_replay_2026-09-08_provefix.md`.
Kill criterion #1 (fork-rate-if-ungated) unchanged from every prior run: window_A 92.3%, window_B
95.9%, both still FAIL the plan's own >50% attractor threshold.

**2026-09-22 — J-1198: D-0213's walk-back BUILT and re-replayed at n=80 (Du offline, real hubs). It
does what Travis ruled on 2026-09-18 (UNDETERMINED 77.5% -> 18.8%) and D-0181's bar still passes,
but it FIRES D-0213's own defeater on its substance: 33 of the 80 merge statuses (41%) now rest on a
second-call TIEBREAK vote that is a constant scope_only=False. D-0213 REOPENED (not re-ruled).** The
ruling had never received a build job (F-1682). `scripts/train_state_invitro.py` `_disprove()`: the
second (scope-only) call's `if scope_how == "tiebreak": return UNDETERMINED` intercept, added by
J-0986, is gone, so a TIEBREAK-decided scope_only verdict is used like any other (True ->
held_within_scope, False -> objected); the FIRST call's fallback and a second call that reached no
verdict are untouched (the briefing said the latter "stays UNDETERMINED as today", but neither
today's code nor the pre-J-0986 code does that: it returns `objected`, left as is).
`scripts/_test_j1198_disprove_walkback.py`: 15/15 scenarios, 5/5 mutants killed, 3 scenarios fail on
the pre-change file. The replay ran through `scripts/lab_j1198_walkback_replay.py` (the script's own
definitions and `_run_step2_lab`, unchanged, with timeout >= 300 s, infra retry/exclusion, a
resumable units file and a write audit wrapped around them; a `core.profile.guard_path` redirect to
scratch because Part 1 cannot run outside `lab_env.isolate()` otherwise, see J-1204): 80/80 units, 0
excluded, 0 infrastructure errors on all four hubs, 71 min, 0 write attempts under live data, live
files unchanged; window A byte-identical to J-1086's claims. Shares: UNDETERMINED 18.8% (15/80, all
the first call's unchanged fallback; window A 5/40 vs 37/40 on 09-18), held_within_scope 22.5%,
objected 55.0%, held 3.8%; control check 3/4 (2/4 on 09-18: `overreach_support` is now `objected`
only because TIEBREAK's False lands on the expected side). D-0181's bar: passes as measured (max
status 55.0%, held_within_scope 22.5%; 63.75% even if every TIEBREAK vote were True; all 18
held_within_scope events read, none is a claim with no real support, 4 are looser than the support
strictly earns). The defeater: all 33 second-call TIEBREAK votes are False, and TIEBREAK
(granite3.1-moe:3b) answered False on 208 of 208 draws on this question: the 33 replay votes, 66
identical-prompt re-asks (100% repeat agreement), 66 re-asks with the JSON key order reversed (0
flips, 0 unparseable), the 29 prompts the two judge families agreed on (True on 0 of the 18 that
both answered True), the script's own `scope_narrower_support` control, and 4 of 4 hand-built clean
items whose answer is True (JUDGE_1 and JUDGE_2: 8/8 right on all 8; TIEBREAK 4/8). So the example
clause (swinging with prompt order) did not occur — the vote never moves — and the model-choice half
was not testable (J-0842's bake-off is the vehicle), but the unreliable-vote problem is back at 41%
of the statuses; mechanical result of the job's own pre-registered rule (thresholds its own): FIRES.
Why TIEBREAK is asked so often is not settled: every one of the 33 splits is (JUDGE_1 mixtral False,
JUDGE_2 falcon3 True); in at least 14 JUDGE_1's own why-text explicitly says a narrower claim IS
earned while its bool says False (regex bound; a manual read says 26, a blind model labeling does
not corroborate it). The second call's split rate also differs from 09-18 (73.8% then, 53.2% now,
identical judge code, cause unknown), and F-1504's "66 reached / 72.7%" is 65 / 73.8% in its own
jsonl. Options for Travis on D-0213: restore the second-call fallback (this run would read
UNDETERMINED 60.0%); keep the walk-back but report second-call-TIEBREAK-decided events as their own
bucket; or repair the second call at its source (J-1205, needs_input, gated on this decision). Full
detail: findings-log F-1697 (verified numbers), F-1698 (the reading, inferred); report
`docs/lab/train_split_merge_step2_replay_2026-09-22_walkback.md` (+`.jsonl`, `_calls.jsonl`,
`_part3.jsonl`, `_battery.jsonl`, `_polarity.jsonl`, `_units.jsonl`, `_run_summary.json`); branch
`jobrun/lab_j1198`, commit 736c88c. Kill criterion #1 (fork-rate-if-ungated) unchanged: window_A
92.3%, window_B 95.8%, both still FAIL the >50% attractor threshold.

**2026-09-22 — J-0791: qwen wording A/B replicated and scaled offline — all three rewordings far
above the live wording, candidate_A vs candidate_B a statistical tie (no ranking), candidate_C lower
and format-inconsistent; the lab's absolute levels sit ~4.7x below the live node (F-1699, F-1700,
F-1701, prep for D-0165 — does not rule it; merged to master as `a9f042f`).** Run in the Du-offline
window (Du down since 08:43:39, gate re-checked 09:09/09:24/10:05/10:30/10:37/10:50, all DOWN) with
the F-1156 prepared script, now resumable and with a write-audit hook, a 300 s timeout with infra
retries and all three `call_node` telemetry writers neutralised (F-1683, J-1199). Hot hub :11433
only, 878 new calls, 0 infra errors, 0 live-write attempts, live-file fingerprint identical.
J-0777's four arms (wording byte-identical) ran on the same 40 real prompts (two more draws, no seed
so each is fresh: 0/160 identical thoughts) plus 59 never-used real trains by J-0724's recipe.
Result on those closing contexts, 99 prompts (95% prompt-cluster bootstrap): current 0.118 [0.067,
0.175], A 0.552 [0.465, 0.640], B 0.566 [0.481, 0.650], C 0.300 [0.222, 0.380]; A−B −0.013 [−0.111,
+0.084] (this run alone −0.020 [−0.121, +0.081]); A−C +0.253 [+0.145, +0.360]; B−C +0.266 [+0.155,
+0.377]. The four readings of `current` on the 40 prompts (0.25 J-0724, 0.125 J-0777, 0.15, 0.225)
are homogeneous (p 0.43; SD 0.060 vs 0.062 binomial): the 0.125-vs-0.25 swing was n=40 noise. A vs B
has no ranking at any sample a lab window affords (about 400 prompts per arm for ±0.05); they differ
in what they touch: A sets intention on 58% of calls (151/151 first-person) and doubles the deed
rate (act != none 0.45 vs 0.22 now), B leaves intention at about 0 and lowers deeds (0.14). C is
lower than J-0777's single draw suggested (its 0.50 was the top of 0.500/0.375/0.300) and 43.5% of
its intentions are bare fragments ("tend the fire") versus 0% for A. **New caveat:** every
closing-context prompt quotes a train's last logged step, which closed that train (0/40 and 0/59
open by the live gate), whereas a live mid-train prompt quotes an open step
(`nodes/inner_monologue_node.py:4484`); live per-step opened share is 0.53–0.56 (n=11,300) and the
implied continuation fell 0.736 → 0.616 → 0.52–0.54 (mean train 3.78 → 2.61 → 2.06–2.16), while the
lab's `current` reads 0.12. Eighty open-context replays lift it to 0.36 against 0.55 for the real
next step on the same contexts, with the same candidate ordering (B 0.80 ≥ A 0.75 > C 0.575), so the
ranking is robust but effect sizes are not live effect sizes. Under an untested constant-log-odds
mapping A and B would imply live continuation 0.87 and 0.90 (mean train about 7.5 and 9.6, past the
pre-TRAIN_HOLD 3.78) and C 0.74 (about 3.9): D-0165's second defeater condition in numbers (F-1701,
inferred). The replay lab's fork-rate-if-ungated (thread-end share of closes, 0.92–0.96 in every
era) does not track the per-step wording. D-0165's named defeater is met; the recalibration stays
the founder's call. **J-1206 spawned** (replay J-0724's gemma-vs-qwen A/B on the 160 open-context
prompts). No live code changed; `nodes/inner_monologue_node.py` untouched; D-0165's recalibrated
wording is not applied anywhere in it (lines 1965–1975 still hold the current block). Full detail:
`docs/lab/train_wording_ab_qwen_replicate_J-0791_2026-09-22.md` (+ `.jsonl`, `_events.json`).

**2026-09-22 — J-1204: `scripts/train_state_invitro.py` Part 1 made genuinely self-isolating against
the D-0179 write fence (hygiene, no experimental result changed; merged to master as `e773e36`).**
J-1198 (same day, F-1697) found Part 1 — the in-vitro checks run on every invocation — hits
`core.profile.guard_path()` via `core.garden`/`core.wood_life`'s own world-store writers (garden's
raise is uncaught and crashes a bare run; wood_life's is silently swallowed elsewhere), and had
worked around it in its own lab runner by monkeypatching `guard_path` process-wide. J-1204 fixed it
at the source: extended Part 1's existing scratch-redirect block to also cover
`core.garden._F/_LEDGER/_EVENTS` and `core.wood_life._F/_EVENTS/_LEDGER` — identical discipline to
the four modules already redirected there
(`social_moves`/`memory_edges`/`opponent_process`/`intentions`); no third module surfaced. Verified
with the `_test_j1165_trace_object_look.py` audit-hook pattern (Part 1 only — Part 2's live hub
calls were not run, Du being live this session): before, reproduces `NonLiveWriteError`; after, ALL
PASS, 0 write attempts under canonical `data`/`docs`; a mutation check (redirect lines removed)
reproduces the original failure, confirming the fix is load-bearing.
`core/profile.py`/`core/garden.py`/`core/wood_life.py` untouched — the fence itself, and every
number in J-1198's own walkback replay / D-0213's reopened status above, are unaffected. Regression:
`scripts/life_smoke.py` 179 ok / 1 pre-existing failure ("day > dusk >= night"), reproduced
identically on a throwaway worktree of clean `a9f042f`, confirming it pre-dates this change.
`scripts/lab_j1198_walkback_replay.py`'s own process-wide `guard_path` monkeypatch is now redundant
for Part 1's portion of what it worked around but was left in place (out of this job's scope; a
small separate follow-up if wanted). Full detail: findings-log F-1702.

**2026-09-23 — J-1205: two candidate repairs of the second call's own prompt tested for real —
neither fixes TIEBREAK; D-0213 REOPENED (F-1739).** D-0213 (re-ruled 2026-09-22 on J-1198's
walk-back, F-1697/F-1698: TIEBREAK answered `scope_only=False` on 208/208 real draws) asked J-1205
to measure whether a different model or a different prompt gives the second call's own question a
real, content-sensitive vote. This job tested the PROMPT half: (b) a pure why-before-bool key
reorder (already a control on TIEBREAK per J-1198 Part 3, 0/33 flips; spot-checked here on
JUDGE_1/JUDGE_2 for the first time) and (c) a polarity-explicit rewording — the key renamed
`scope_only` → `narrower_claim_earned`, plus one clarifying sentence naming both polarities — the
genuinely new candidate. 492 real calls to JUDGE_1/JUDGE_2/TIEBREAK, temperature 0, 0 infra errors,
0 parse failures. **Neither repairs TIEBREAK.** Under arm (c), TIEBREAK answered False on 144/144
fresh draws (0.0% True share, 100% repeat agreement) across all 62 real second-call prompts + 2
controls + the 8-item constructed battery; on the battery it scores 4/8 — numerically IDENTICAL to
the live wording's own historical 4/8, same per-item pattern; against the panel-unanimous-True real
prompts it scores 37.0% accuracy, statistically indistinguishable from the live wording's
historical 37.9%. This fails the founder's own proposed pass bar (battery ≥7/8, unanimous-match
≥70%) on both numeric bars — only the parse-failure bar passes. A qualitative read of the why-texts
shows the judge engaging with claim-specific content while its bool stays a near-constant False
regardless — the same content-insensitive-default pattern F-1280/F-1321/F-1357 already
characterized, now confirmed to survive an unambiguous key rename, not just a word-order swap.
Secondary, in passing: JUDGE_1's own battery accuracy under arm (c) (8/8) numerically beats its own
arm (a)/(b) reads (6/8, 4/8) — the wording may help JUDGE_1/JUDGE_2 even though it does not fix
TIEBREAK; not investigated further here. **D-0213 REOPENED**, not re-ruled: the defeater's own
"every candidate model/prompt" wording is not yet fully met (the MODEL half — a different TIEBREAK
seat — was explicitly OPTIONAL per this job's own briefing and was not run, per its own "do not
duplicate D-0176's bake-off" instruction) — **J-1240 spawned** (from F-1739) to test gemma4:12b
(:11439, D-0176/J-0842's own best-evidenced alternate candidate, fit+stable on a different call
site's contract) against this call site's own `_SCOPE_SYSTEM`. Isolation: `lab_env.isolate()`
entered after `core`/`core.judge_panel` were imported+cached from the worktree (so `lab_env`'s own
later `sys.path` prepend of live `C:\Nascence` cannot leak in); write-audit confirmed 0 writes
outside the one pre-isolated `data/_lab/<timestamp>/` quarantine dir; live `nascence.db` /
`judge_panel_log.jsonl` both show a delta across the run's ~48-minute window, which is Du's own
expected continuous live activity (confirmed independently via the Du-offline checker both before
and after, both reading UP-or-UNKNOWN as expected — this job never gated on it, CPU hubs only, no
hot lane), not this job's own doing. Full detail: findings-log F-1739; report
`docs/lab/train_split_merge_step2_scope_repair_2026-09-23_J1205.md` (+`.jsonl`, 492 raw rows);
harness `scripts/lab_j1205_scope_repair.py`.

**2026-09-23 — J-1240: arm (d), gemma4:12b as a candidate TIEBREAK seat — a real briefing bug
caught and fixed, but only a small partial sample run; D-0213 NOT resolved (F-1765, J-1261
spawned).** D-0213's own 2026-09-23 ruling ("Hold — wait for J-1240 … before deciding further")
named this job as the last untested half of its own defeater (the MODEL half; J-1205's own PROMPT
half already failed both candidates). Before any judge call, this job caught a real, confirmed
error in its own dispatch briefing: the candidate's address was given as `http://LAN-HOST:11439`
("Ramses"), which does not answer at all (direct probe: connection actively refused) — the real
hub is `http://127.0.0.1:11439` (LOCAL, this machine's own Threadripper/Bonsai CPU tier), confirmed
reachable and serving `gemma4:12b`, and cross-referenced against seven other places in this tree
that all agree (`core/judge_panel.py`, `core/model_client.py`, `core/left_lane.py`,
`core/deliberation.py`, `core/librarian.py`, `core/peers.py`, and `scripts/d0176_scan_bakeoff.py`
itself — the very bake-off the briefing cited as its source). Root cause: the briefing conflated
gemma4:12b's own address with a DIFFERENT, already-retired local-vs-Ramses repoint (D-0121,
2026-09-02) that moved JUDGE_1 (not gemma) off that same local port. All real calls went to the
verified real address.

Reused J-1205's own harness (`scripts/lab_j1240_tiebreak_seat.py`, near-identical, only the
TIEBREAK-role hub repointed to the candidate) and ran all three of J-1205's own arms, since J-1205's
own arm (c) showed no promise over arm (a) on granite (no wording preference to inherit). **But
this session's own interactive, closely-polled format could not absorb the run's real wall-clock
cost**: JUDGE_1's own hub (mixtral:8x7b, Ramses) showed much higher latency than the candidate this
session (interim read: JUDGE_1 median ~61s vs the candidate's ~14s vs JUDGE_2's ~10s per call) —
consistent with `core/judge_panel.py`'s own documented hub-sharing tradeoff with Du's live
commitment-ledger scan and dream-primary generation (Du live throughout, never gated on, same
precedent as every prior job here) — projecting to roughly 3 hours for the full 164-round design
that took J-1205 itself only ~48 minutes. The round order was reprioritized mid-run (a recorded
deviation) to reach the 10 known-answer items before the 62 real units, since the founder's own
pass bar depends on the battery score — but the run was still deliberately stopped after only 20
rounds (60 calls, 0 infra_errors) rather than forced through a multi-hour interactive wait: 1 of 8
battery items and 2 of 2 controls complete, plus a handful of real units.

**What the small sample shows (real, but far too small to characterize):** every one of 16
candidate-role calls under arm (c) came back `True` — 0 `False` — including a WRONG answer on the
one known-answer control expected `False` (`ctrl_overreach_support`) and a disagreement with the
one real unit where JUDGE_1 and JUDGE_2 both agreed `False` (`u6`), while correctly answering `True`
on the other control and the one completed battery item (2 of 3 known-answer items right).
Consistent with either genuine content-sensitivity or an opposite-direction content-insensitive
default from granite's own constant-`False` (a constant-`True` "mirror" of the exact
certainty-machine failure this plan's own kill criterion §4 point 4 warns against) — this job's own
N cannot distinguish these. Isolation held (write-audit + a post-hoc canary scan of the live
`judge_panel_log.jsonl` for this job's own distinctive content, 0 hits, since the process was killed
mid-run rather than left to print its own self-check). `core/judge_panel.py`'s own live TIEBREAK
constant (granite, `:11437`) was read for the record only, never called, never re-pointed.
**D-0213's own defeater is NOT resolved** — the model half is not yet tested at meaningful scale, so
D-0213 stays exactly as the founder left it (Hold, wait for J-1240) rather than being treated as
answered. **J-1240 itself left OPEN** (its own core deliverable — a real read against the founder's
pass bar — was not reached), fully resumable; **J-1261 spawned** to finish it as a genuinely
unattended background dispatch (not interactively polled) at J-1205's own matched N. Full detail:
findings-log F-1765; report `docs/lab/train_split_merge_step2_scope_repair_2026-09-23_J1240.md`
(+`.jsonl`, 60 raw rows); harness `scripts/lab_j1240_tiebreak_seat.py`.

**2026-09-24 — J-1206: precondition check only — Du confirmed live, no hot-lane calls made, left
OPEN (F-1832).** J-1206's own briefing requires Du confirmed OFFLINE before touching the shared hot
hub (`:11433`, since the gemma4:e4b-vs-qwen3.5:9b A/B on the 160 open-context prompts swaps its
resident model) — the same production gate `scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py`'s
own `_confirm_du_offline()` enforces in code, and the identical gate J-0791 itself already hit earlier
in this same plan (2026-09-08 entry above). Independently re-verified two ways, not just trusted from
this dispatch's own ground-rules text: `Get-CimInstance Win32_Process -Filter "ProcessId=40268"` shows
the real `run_nascence.py` process, `CreationDate` 2026-09-22 16:10:23 (matching the dispatch's own
claim exactly); `data/nascence.log`'s own tail shows real-time monologue/deep-memory/play lines through
2026-09-24 07:20:57, seconds before the check — active generation, not a stale log. Per this job's own
gate and this dispatch's own ground rules ("never restart Du/supervisor/any hub"), **no hub call was
made** (0 calls to either model), `nodes/inner_monologue_node.py` untouched, no live state touched.
**J-1206 left OPEN** (not forced through, not abandoned) for a future session to re-attempt once a real
Du-offline window exists — this is a complete, valid precondition-check outcome, not a failure to
finish. D-0165 untouched — not ruled, not re-opened; it is already open/ACTIVE_HOLD (ruled 2026-09-22,
naming J-1206 as its own next read) and stays exactly as the founder left it. Full detail: findings-log
F-1832.

**2026-09-24 — J-1261: resume of J-1240 blocked by a real JUDGE_1 hub outage (Ramses, not Du),
left OPEN before any hub call (F-1840); a skill-manager gap flagged (S-0178).** Seeded the
scratchpad's `ROWS_PATH` from the 60 rows J-1240 already committed (verified: 60/60 unique
`(id, arm, judge, draw)` keys, 20 fully-complete rounds, matching F-1765 exactly) — nothing already
done needs re-asking. Before launching `--run`, `--probe` (run twice, 23s apart) found JUDGE_1's own
hub (mixtral:8x7b, Ramses `http://LAN-HOST:11438`) unreachable both times ("actively refused"),
while the CANDIDATE (gemma4:12b, `:11439`) and JUDGE_2 (falcon3:7b, `:11440`) were both fine —
independently confirmed NOT a general network outage (`Test-Connection` to the Ramses host: 2/2 ICMP
replies, ~0ms; `Test-NetConnection` on port 11438 specifically: `TcpTestSucceeded=False` — the host
is up, that one hub's own listener is down) and NOT a sub-second blip (a bounded 150 s poll, every
15 s, stayed down for all 9 checks before timing out). Because `--run` only gates on the CANDIDATE
hub, not JUDGE_1/JUDGE_2, launching anyway would not fail fast: reading `core/judge_panel.py`'s own
`_ask()` and the script's own `_ask_lab()` directly shows a connection-refused is classified as an
infra error and retried 3× with 20/60/180 s backoff (260 s) before giving up on that one call — with
JUDGE_1 down for the whole run, all 144 remaining rounds (0 of the seeded 20 are partial) would cost
roughly 144 × 260 s ≈ 10.4 hours in retry backoff alone, far past this job's own "~3 hours, check back
in 60–90+ minutes" sizing (itself based on JUDGE_1 being *slow*, not *absent*), while starving the
split-rate/unanimous-panel numbers the founder's own pass bar partly depends on of any new JUDGE_1
data. **Not launched** — this plan's own "report rather than ship" convention, the same one J-0791
already used twice earlier in this plan under a different gate. **J-1261 left OPEN** (in_progress, not
done, not abandoned) — no new job spawned; J-1261's own id is already the right resumption target
(seed is in place, `--run` from this worktree once a fresh `--probe` shows JUDGE_1 reachable again).
D-0213 untouched — not ruled, not re-opened; stays exactly as the founder left it (Hold, wait for
J-1240 via J-1261's own completion). Separately, a real gap in the lab-dispatch convention itself
(not this job's own deliverable to fix) flagged via skill-manager: `--run`'s own reachability gate
only covers the hub a job just added, not every hub the run will call, so an established hub going
down silently turns a bounded run into a ~3-4× longer one instead of failing fast (S-0178). Full
detail: findings-log F-1840.

**2026-09-24 — J-1261: J-1240 resumed and finished at full N (492 calls, 164 rounds) — gemma4:12b
PASSES the founder's own proposed bar on all three measures; D-0213's own defeater condition is
now genuinely met, not just partially tested (F-1850).** Ramses came back up after the Windows
update restart the founder reported. Re-verified before committing to the long run, not just
trusted from a curl check: `--probe` confirmed JUDGE_1 reachable again, but `--probe` only performs
`GET /api/tags` — the same class of check as the dispatching session's own curl, proving the server
is up but not that a real generate call succeeds. `--smoke` (the script's own real-call mode) against
the already-seeded scratchpad was a no-op (the hardcoded round was already done in the 60-row seed);
re-run against a throwaway empty scratch dir to force a genuinely fresh call: JUDGE_1
calls=1/ok=1/infra_errors=0, a real ~105s round-trip, not an instant error. Launched `--run` as a
genuine unattended background dispatch (not interactively polled, per this job's own explicit
instruction) — one bounded sanity check at ~3 minutes confirmed real progress, then no further
checks until the background task's own completion notification.

**Result: 144/144 rounds, 432 fresh calls, 0 infra_errors / 0 retries / 0 parse failures on all
three judges, ~38 minutes wall time** — faster than J-1205's own 48-minute baseline for the same
492-call scale, meaning JUDGE_1 had little contention this pass (unlike the original J-1240
session's ~61s median). Arm (c), the candidate wording, full N=144: CANDIDATE (gemma4:12b)
true-share 85.4% (123/144, CI 0.787–0.903), battery **8/8** (bar ≥7/8: PASS), unanimous-panel-match
accuracy **80.0%** (20/25, CI 0.609–0.911; bar ≥70%: PASS), parse-fail **0.0%** all three judges
(bar ≤10%: PASS). **OVERALL_PASS: True** — a categorical reversal of granite/TIEBREAK's own
complete failure on the identical wording and N, measured same-day by J-1205 (true-share 0.0%,
battery 4/8, unanimous-match 37.0%). Gemma also scored the battery 8/8 under both other wordings
tested (arm a, arm b) — since the battery is 4 True-expected/4 False-expected, a constant-vote
default caps at 4/8 regardless of direction, so a clean 8/8 across three independent wordings
directly rules out a constant-vote default, unlike granite's own numerically-identical 4/8 on
every wording tried.

**Two real caveats, reported alongside the pass, not glossed over.** (1) The existing regex-based
bool-vs-why coherence check (tuned against granite's own phrasing in earlier jobs, F-1280/F-1321)
matched ZERO of gemma's 144 arm-(c) why-texts (144/144 "ambiguous_or_no_regex_match", vs JUDGE_1's
26/144 and JUDGE_2's 8/144 coherent under the identical regex) — confirms WHAT gemma answered and
that it's usually right, but this specific instrument cannot corroborate WHY for this model at all;
a real instrument-transferability gap, not evidence against the candidate (flagged via skill-manager,
S-0180, not fixed here). (2) gemma is right on 15/15 panel-unanimous-True real units but only 5/10
on panel-unanimous-False ones — a real, measurable lean toward True specifically on the harder,
ambiguous real-unit prompts (the battery itself is balanced 4/4 both directions) — the 95% CI on
the resulting 80% (0.609–0.911) does not clear 70% at its lower bound, so the pass is real at the
measured point estimate but carries genuine sampling uncertainty at this N.

**Isolation independently re-verified past the script's own self-report** (per this job's own
explicit instruction not to trust it blindly): write-audit recorded exactly 2 events for the whole
38-minute run, both the quarantine dir's own creation, nothing else; a canary scan of the real live
`judge_panel_log.jsonl` for this job's distinctive content (`narrower_claim_earned`, battery/control
ids, the battery's own claim text) found 0 hits; `ROWS_PATH` ends at exactly 492 rows (60 seed + 432
fresh), matching the finalize output's own row count exactly. The real live `nascence.db` /
`judge_panel_log.jsonl` DID grow during the window — expected, Du live throughout, same precedent as
every prior job here; the write-audit + canary scan are the real isolation evidence, not the raw
before/after diff on files Du itself also writes to.

**D-0213's own defeater fires on its own literal wording** ("gemma4:12b... gives the scope_only call
a real, content-sensitive vote at a reasonable pass bar... that is the fix — build it") — genuinely
met now, not the small partial sample J-1240's own 60-call read left it at. Per this job's own
briefing and this plan's repeated convention, **not ruled here**: `core/judge_panel.py`'s own live
`TIEBREAK` constant (granite, `:11437`) was read for the record only, never called, never mutated.
Full detail: findings-log F-1850; report
`docs/lab/train_split_merge_step2_scope_repair_2026-09-23_J1240.md` regenerated at full N (+`.jsonl`,
492 raw rows, replacing the prior 60-row partial file).

**2026-09-24 — J-1311: D-0213's ruled shadow-observe direction BUILT (F-1863).** D-0213's own current
ruling (Travis, 2026-09-23, citing F-1850): "Build gemma4:12b as the scope_only TIEBREAK-seat
candidate, but shadow-observe it before fully trusting it live." `scripts/train_state_invitro.py`'s
`_disprove()` now, whenever the second (scope_only) call lands on TIEBREAK, ALSO calls gemma4:12b
directly (`CANDIDATE_TIEBREAK_URL = http://127.0.0.1:11439`) with the exact arm (c) polarity-explicit
wording J-1205/J-1240/J-1261 already characterized at full N (key renamed `scope_only` ->
`narrower_claim_earned`, reusing the IDENTICAL `scope_user` prompt string the real second call already
built — never re-derived, cross-checked byte-identical to `scripts/lab_j1240_tiebreak_seat.py`'s own
construction by this job's own new test) and logs what gemma WOULD have answered alongside what
TIEBREAK actually decided, to a new `data/train_split_merge_shadow_tiebreak_log.jsonl` (redirected into
each replay's own scratch dir by `_run_step2_lab()`'s existing isolation — never a live write).
`scope_verdict`/`scope_how`/`scope_why`, and therefore `status` and everything else `_disprove()`
returns, are completely untouched by this. `core/judge_panel.py`'s own live `TIEBREAK` constant
(granite, `:11437`) is read for the record only, never called, never mutated. **D-0213 is NOT re-ruled
here**, per this job's own briefing.

Verified two ways before committing. (1) A synthetic, no-network unit test
(`scripts/_test_j1311_shadow_tiebreak_seat.py`, committed alongside the change, same AST-extraction
technique the pre-existing `scripts/_test_j1198_disprove_walkback.py` uses since this file cannot be
imported): 9/9 scenarios pass — the shadow call fires exactly when `scope_how == "tiebreak"` and never
otherwise, and `_disprove()`'s own return is byte-identical whether gemma agrees, disagrees, or its own
call raises — plus 4/4 mutants killed, including a compound mutant proving the fail-open guarantee is
real (removing a single guard alone survives, by design, since the other still catches it; removing
BOTH is caught). The pre-existing walk-back test still passes 15/15 unmodified against the edited file,
confirming this is purely additive (`git diff --stat`: +122/-0, one file). (2) One real, bounded,
isolated smoke call through gemma's own hub (12.7s, `shadow_verdict=true` with a real content-specific
why-text on a known-answer control claim) confirmed the wire fires and logs correctly end-to-end — the
live shadow-log path was confirmed absent both immediately before and immediately after.

**Not live-wired**: this whole file is an OFFLINE replay lab — grep-confirmed project-wide, no other
module imports `scripts.train_state_invitro`, Du's live per-step loop never calls `_disprove()` — so
this wire only fires the next time someone actually runs the Step 2 replay; no real shadow-data window
exists yet. **J-1317 spawned** (gated on a real replay actually being run) to accrue one and read it
against D-0213's own defeater (does gemma's real-event agreement rate with TIEBREAK confirm or diverge
from F-1850's offline 80.0% unanimous-match read) — the founder's own next call on flipping to fully
live waits on that read, not on this job. Full detail: findings-log F-1863; commit `ab0381e`.

**2026-09-24 — J-1317: precondition check only — Du confirmed live, no hub calls made, left OPEN
(F-1870).** J-1317's own task was to actually run the real Step 2 replay (`_run_step2_lab()`,
n_per_window=40) so J-1311's shadow wire (above) accrues its first real gemma4:12b-vs-TIEBREAK rows.
That replay's own `_prove()` step calls the shared HOT hub (`http://127.0.0.1:11433`) directly, and
this file's own accumulated history requires Du confirmed OFFLINE before every one of its three prior
real runs (J-0835 declined online 2026-09-11/12; J-1086 and J-1198 both reconfirmed offline before
running) — no "CPU-hub-only" alternative exists in the file's current comments, checked directly per
this job's own briefing rather than assumed. Du is confirmed live and continuously generating (PID
40268, `run_nascence.py`, live since 2026-09-22T16:10:23 — independently re-verified via
`Get-CimInstance` on that PID and a real-time-advancing `data/nascence.log` tail, not just trusted from
the dispatch text), the identical gate and identical outcome J-1206 already hit on this same plan
earlier the same day (line ~1234 above). Per this dispatch's own ground rules ("never restart
Du/supervisor/any hub"), **no hub call was made** (0 calls to HOT, JUDGE_1, JUDGE_2, TIEBREAK, or the
gemma4:12b candidate). As a safe, bounded, no-network sanity check instead, both existing regression
tests for J-1311's shadow-wire build were re-run and still pass unchanged against this worktree's HEAD
(`scripts/_test_j1311_shadow_tiebreak_seat.py` 9/9 scenarios + 4/4 mutants killed;
`scripts/_test_j1198_disprove_walkback.py` 15/15 scenarios + 5/5 mutants killed) — the build is intact
and unregressed, but this produces no real shadow-data rows. D-0165 independently re-checked
(`decide.py show D-0165`) and confirmed NOT gating this job (a different, unrelated question). **J-1317
left OPEN** (in_progress, not done, not abandoned) — its own id is already the right resumption target
once a real Du-offline window exists; no new job spawned. D-0213 untouched — not ruled, not re-opened;
it stays exactly as the founder left it (shadow-observe ruling, 2026-09-23), since no new shadow-data
evidence toward its own defeater exists yet. Full detail: findings-log F-1870.

**2026-09-24 (evidence-backlog review) — this doc's own "verified" stamp was frozen at 09-04 despite
40+ dated entries landing since, including several from earlier today (J-1206, J-1261, J-1311,
J-1317) — the same `/plan-liveness` staleness-parsing gap flagged against idle_executive_plan and
the_consciousness_program (S-0187): the heading was never bumped even as the section kept growing.
No new investigation needed here — the doc is self-evidently current, and the one open item (J-1317,
waiting on a real Du-offline window to run the Step 2 replay) is already correctly tracked, not
neglected. Stamp bumped to match.
