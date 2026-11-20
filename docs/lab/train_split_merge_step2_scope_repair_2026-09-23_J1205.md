# Train Split/Merge -- Step 2 second-call repair, J-1205 (D-0213)

## J-1205 reading (2026-09-23)

D-0213 was re-ruled by Travis 2026-09-22 (independently re-verified via `decide.py show D-0213` before this job started, not just trusted from the dispatch's own paraphrase): "Repair the second (scope_only) disprove call at its source ... J-1205 ... is now unblocked." J-1198's own walk-back replay (`docs/lab/train_split_merge_step2_replay_2026-09-22_walkback.md`, F-1697/F-1698) found TIEBREAK (granite3.1-moe:3b, :11437) answering the second call's own question `scope_only=False` on 208 of 208 real draws -- a content-insensitive constant, decisive on 33 of the replay's 80 merge statuses (41%). This job tests candidate repairs of that ONE call site's own prompt (never `core/judge_panel.py`, never the first `_DISPROVE_SYSTEM` call) against the real JUDGE_1, JUDGE_2 and TIEBREAK hubs.

**Arms tested** (byte-identical prefix in every arm; only the schema tail -- the JSON key + its own explanatory clause -- differs, the same single-lever-at-a-time discipline this plan's own wording A/B jobs already use):

- **(a) bool_first** -- the LIVE wording, unchanged. Baseline.
- **(b) why_first** -- pure key-order swap (why before the bool), byte-identical to J-1198 Part 3's own `why_first_d1`. Already characterized by J-1198 as a control, not a candidate fix (TIEBREAK: 0/33 flips across two re-asks on the real tiebreak-decided cases) -- this job did not repeat that TIEBREAK check; it adds the JUDGE_1/JUDGE_2 check on the 10 known-answer items that was never run.
- **(c) polarity** -- THE candidate fix: renames the JSON key from `scope_only` (a name whose True/False reading requires holding a double negative in mind) to `narrower_claim_earned`, plus ONE clarifying sentence stating both polarities in plain language. Nothing else changed.
- **(d) a different TIEBREAK seat** -- OPTIONAL per this job's own briefing, NOT run here. D-0176's own bake-off (J-0842, a DIFFERENT call site's contract, `commitment_ledger.scan_shadow`) already tested granite3.1-moe:3b (TIEBREAK's own model, :11437) and found it unfit there too, found gemma4:12b (:11439) fit and stable, found command-r7b (:11441) unreachable (46.5% 7-day failure rate), and left falcon3/mixtral untested (another lab's exclusive hubs that window). No candidate has been tested against THIS call site's own `_SCOPE_SYSTEM` contract -- duplicating a bake-off for a different judge/contract is explicitly out of this job's own scope ("do not duplicate it"); see this report's own follow-up section.

**Isolation.** `lab_env.isolate(also=[(judge_panel, ["_DATA","_LOG"])], db="empty")` wrapped every real hub call, entered AFTER `core`/`core.judge_panel` were already imported+cached from the WORKTREE (module resolution: `core`=`C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad\wt_train_split_merge\core\__init__.py`, `core.judge_panel`=`C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad\wt_train_split_merge\core\judge_panel.py`), so `lab_env`'s own later `sys.path` prepend of the live `C:\Nascence` cannot make a later `core.*` submodule import resolve outside the worktree. `db="empty"` -- this call site makes no `core.memory.store` call at all, confirmed by reading `core/judge_panel.py` directly (no import of `core.profile`/`core.memory` anywhere in it) -- so no live-DB content was ever needed or touched. `lab_env.isolate()`'s own writes are confined entirely to `C:\Nascence\data\_lab\<timestamp>\` -- the ONE subtree `core/profile.py`'s own write-fence (D-0179/D-0200) already treats as pre-isolated/quarantined, not live application state -- verified directly via a `sys.addaudithook` watching all of `C:\Nascence\data` and `C:\Nascence\docs`: 0 write-shaped events this process. Backstop: real `nascence.db` unchanged=None, real `judge_panel_log.jsonl` unchanged=None. Infra rules matched J-1198's runner: timeout >= 300s; timeout/http/exception treated as infrastructure, retried 3x with backoff (20/60/180s), never a verdict; 'parse' (the judge answered but broke the JSON contract) is a real, counted outcome. Du state before/after (not a gate for this job -- CPU hubs only, no hot lane): None / None.

**Inputs.** 62 real second-call user prompts + 2 real known-answer control prompts, both read verbatim from the already-committed `docs/lab/train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl` (prompt-builder integrity re-verified: `build_second_call_prompt()` reproduces real committed prompts byte-for-byte), plus 8 hand-built known-answer battery items (reproduced verbatim from `scripts/lab_j1198_scope_battery.py`'s own `ITEMS`). Arm (c) ran on all 72 (2 draws, temperature 0); arms (a)/(b) reused existing walk-back + Part-3 data for the 62 real prompts (arm (a): full coverage, no new calls -- JUDGE_1/JUDGE_2 from the replay itself, TIEBREAK from the replay's own 33 tiebreak-decided votes PLUS J-1198 Part 3's own direct TIEBREAK asks on the 29 'agreed' units and both controls) and added a fresh, same-session 1-draw check on the 10 known-answer items only (2 controls + 8 battery) for all three judges, so the baseline is not solely a week-old read. A full fresh 64-prompt J1/J2 re-run of arms (a)/(b) was scoped OUT (see the report's own "what was not re-run" note) -- arm (b) is explicitly a control, not a candidate, and arm (a)'s J1/J2 behaviour on the 62 real prompts is already the walk-back's own primary dataset.

### Arm a_bool_first -- (a) live wording, unchanged -- baseline

Prompts: the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh this session.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 10 | 3 | 7 | 0 | 0.3 (0.108, 0.603) | 0.0 | 0/0 (None) | 6/8 |
| JUDGE_2 | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 8/8 |
| TIEBREAK | 10 | 0 | 10 | 0 | 0.0 (0.0, 0.278) | 0.0 | 0/0 (None) | 4/8 |

### Arm b_why_first -- (b) pure why-before-bool key order -- control, not a candidate (J-1198)

Prompts: the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh this session.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 10 | 10 | 0 | 0 | 1.0 (0.722, 1.0) | 0.0 | 0/0 (None) | 4/8 |
| JUDGE_2 | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 6/8 |
| TIEBREAK | 10 | 0 | 10 | 0 | 0.0 (0.0, 0.278) | 0.0 | 0/0 (None) | 4/8 |

### Arm c_polarity -- (c) polarity-explicit key + one clarifying sentence -- THE candidate fix

Prompts: all 72 (62 real units + 2 real controls + 8 battery), 2 draws.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 144 | 45 | 99 | 0 | 0.312 (0.242, 0.392) | 0.0 | 69/72 (0.958) | 8/8 |
| JUDGE_2 | 144 | 112 | 32 | 0 | 0.778 (0.703, 0.838) | 0.0 | 70/72 (0.972) | 8/8 |
| TIEBREAK | 144 | 0 | 144 | 0 | 0.0 (0.0, 0.026) | 0.0 | 72/72 (1.0) | 4/8 |

## JUDGE_1 / JUDGE_2 split rate -- historical arm (a) vs fresh arm (c) (all 62 real units)

- arm (a), historical (the walk-back replay itself): n=62, agree=29, split=33 (split rate 0.532), unanimous-True=18, unanimous-False=11.
- arm (c), fresh this session: n=62, agree=27, split=35 (split rate 0.565), unanimous-True=17, unanimous-False=10.

## TIEBREAK vs. the unanimous panel (the only ground-truth-ish signal in the real prompts)

- arm (a), historical: n_unanimous_true=18, TIEBREAK said True on 0 of them; n_unanimous_false=11, TIEBREAK said True (wrongly) on 0 of them; overall accuracy 0.379 (CI (0.227, 0.56)).
- arm (c), fresh: n_unanimous_true=17, TIEBREAK said True on 0 of them; n_unanimous_false=10, TIEBREAK said True (wrongly) on 0 of them; overall accuracy 0.37 (CI (0.215, 0.558)).

## Pass bar (this job's own briefing's proposed numbers, applied to arm (c))

TIEBREAK matches the constructed battery >= 7/8: **False** (4/8). TIEBREAK matches the panel-unanimous-True prompts >= 70%: **False** (0.37). No parse-failure rate above 10%: **True** ({'JUDGE_1': 0.0, 'JUDGE_2': 0.0, 'TIEBREAK': 0.0}). **OVERALL: False** (the founder's own bar to rule on, per this job's own briefing -- not this job's call to declare "fixed").

## What was NOT re-run, and why

- **Arm (b) on TIEBREAK beyond the 10 known-answer items**: already thoroughly characterized by J-1198 Part 3 on all 33 real tiebreak-decided cases (2 identical re-asks + 1 reversed-order-named variant each) -- 0/33 flips, True share stayed 0.0% under both reorderings. Re-running that exact check here would not add evidence; this job's own briefing itself calls arm (b) "a control, not a candidate fix."
- **Arms (a)/(b) on the full 64 real prompts, fresh this session**: arm (a) is the walk-back replay's own primary dataset (JUDGE_1/JUDGE_2 on all 62+2) plus J-1198 Part 3's own direct TIEBREAK asks on the 29 'agreed' units and both controls -- already a complete, real, dated reading with no gap to fill; re-running it fresh would mostly re-confirm hub stability, not test a candidate. Arm (b) is a control (see above). Both got a fresh, same-session 10-item spot check instead (2 controls + 8 battery, all three judges, 1 draw) so this report's own arm (c) numbers are read against a same-session, not solely a week-old, comparison point.
- **Arm (d), a different TIEBREAK seat**: OPTIONAL per this job's own briefing, and explicitly gated on reading D-0176's own bake-off first without duplicating it (done -- see this report's own arms-tested section). No candidate has been tested against THIS call site's own contract; left as a follow-up job rather than run inside this already-large dispatch.
- **A larger, category-balanced constructed battery** (the shape J-0916/F-1321 built for the FIRST call's own question, n=20 x 2 reps): this job reused the EXISTING 8-item battery (`scripts/lab_j1198_scope_battery.py`) rather than building a new one for the SECOND call's own question, since building and validating a fresh 20-case battery is itself a real, separate undertaking (J-0916's own briefing treated it as one) -- worth doing as its own follow-up if the founder wants a sharper accuracy read than n=8 gives.
