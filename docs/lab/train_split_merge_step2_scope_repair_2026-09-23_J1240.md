# Train Split/Merge -- Step 2 second-call repair, J-1240 (D-0213, arm d)

## J-1240 reading (2026-09-23)

D-0213 was re-ruled by Travis 2026-09-23 (independently re-verified via `decide.py show D-0213` before this job started): "Hold -- wait for J-1240 (the gemma4:12b model-swap test on the scope_only second-call's own contract) before deciding further ... Only the model half remains untested." J-1205 (same day) tested two prompt-wording candidates against TIEBREAK (granite3.1-moe:3b, :11437) on this call site's own `_SCOPE_SYSTEM` contract and found neither repaired its constant `scope_only=False` vote (0.0% True share on 144 fresh draws under arm (c), same 4/8 battery score as the unfixed prompt). This job tests the MODEL half of D-0213's own defeater: does a DIFFERENT model in the same seat give this call site's own question a real, content-sensitive vote? Candidate: gemma4:12b, D-0176/J-0842's own best-evidenced alternate (fit+stable on a DIFFERENT call site's contract, `commitment_ledger.scan_shadow`).

**Hub address correction (verify-before-calling).** The dispatch briefing named the candidate's address as `http://LAN-HOST:11439` ("Ramses"). That address does not answer at all (`URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>`, confirmed by direct probe before any judge call was made). The real hub is `http://127.0.0.1:11439` (LOCAL, this machine's own Threadripper/Bonsai CPU tier) -- confirmed reachable and serving `gemma4:12b` by the same probe (models=['gemma4:12b']), and cross-referenced against seven other places in this tree that all independently agree on `127.0.0.1:11439` (`core/judge_panel.py`, `core/model_client.py`, `core/left_lane.py`, `core/deliberation.py`, `core/librarian.py`, `core/peers.py`, and `scripts/d0176_scan_bakeoff.py` itself -- the very bake-off the briefing cites as its source). See this script's own docstring for the full trace. All calls below went to the verified real address, never the wrong one.

**Arms tested** (all three, unlike a single-arm run -- J-1205's own arm (c) showed NO promise over arm (a) on granite: battery 4/8 both, unanimous-match 37.0% vs 37.9%, statistically indistinguishable -- so this job does not guess which wording to prefer and instead mirrors J-1205's own full design, changing only the hub):

- **(a) bool_first** -- the LIVE wording, unchanged. Baseline.
- **(b) why_first** -- pure key-order swap, J-1198's own control on granite.
- **(c) polarity** -- the polarity-explicit rewording J-1205 tested as THE candidate fix.

**Isolation.** `lab_env.isolate(also=[(judge_panel, ["_DATA","_LOG"])], db="empty")` wrapped every real hub call, entered AFTER `core`/`core.judge_panel` were already imported+cached from the WORKTREE (module resolution: `core`=`C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad\wt_train_split_merge\core\__init__.py`, `core.judge_panel`=`C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad\wt_train_split_merge\core\judge_panel.py`), so `lab_env`'s own later `sys.path` prepend of the live `C:\Nascence` cannot make a later `core.*` submodule import resolve outside the worktree. `core/judge_panel.py`'s own live `TIEBREAK` constant (`http://LAN-HOST:11437`, granite) was read for the record only, never called, never mutated -- this script's own separate `CANDIDATE_URL` is used solely by this script's own local `HUB_URL` mapping. Write-audit (`sys.addaudithook` watching all of `C:\Nascence\data` and `C:\Nascence\docs`): 0 write-shaped events this process. Backstop: real `nascence.db` unchanged=False, real `judge_panel_log.jsonl` unchanged=False. Infra rules matched J-1205's runner: timeout >= 300s; timeout/http/exception treated as infrastructure, retried 3x with backoff (20/60/180s), never a verdict; 'parse' is a real, counted outcome. Du state before/after (not a gate for this job -- CPU hubs only, no hot lane, same precedent as every prior job in this plan): rc=1 (UP-or-UNKNOWN); VERDICT: UP-or-UNKNOWN / rc=1 (UP-or-UNKNOWN); VERDICT: UP-or-UNKNOWN.

**Inputs.** 62 real second-call user prompts + 2 real known-answer control prompts, both read verbatim from the already-committed `docs/lab/train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl` (prompt-builder integrity re-verified), plus 8 hand-built known-answer battery items (reproduced verbatim from `scripts/lab_j1198_scope_battery.py`'s own `ITEMS`). Arm (c) ran fresh on all 72 (2 draws, temperature 0); arms (a)/(b) ran fresh on the 10 known-answer items only (1 draw) -- unlike J-1205, there is no history to reuse for the CANDIDATE seat (gemma4:12b has never been asked any of these prompts before this job), so JUDGE_1/JUDGE_2 were also called fresh everywhere in this run rather than mixed with J-1205's own differently-dated data, keeping this report self-contained and internally comparable.

### Arm a_bool_first -- (a) live wording, unchanged -- baseline

Prompts: the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh. `TIEBREAK` in this table means the CANDIDATE seat (gemma4:12b (local, Threadripper/Bonsai CPU tier -- verified 2026-09-23, NOT the live :11437 TIEBREAK)), never the live granite TIEBREAK.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 10 | 4 | 6 | 0 | 0.4 (0.168, 0.687) | 0.0 | 0/0 (None) | 7/8 |
| JUDGE_2 | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 8/8 |
| TIEBREAK | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 8/8 |

_For reference (not recomputed here, cited verbatim from J-1205's own already-published report): granite3.1-moe:3b (the live TIEBREAK) on this SAME arm's wording scored True share 0.0, battery 4/8 (n=10)._

### Arm b_why_first -- (b) pure why-before-bool key order -- control, not a candidate (J-1198)

Prompts: the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh. `TIEBREAK` in this table means the CANDIDATE seat (gemma4:12b (local, Threadripper/Bonsai CPU tier -- verified 2026-09-23, NOT the live :11437 TIEBREAK)), never the live granite TIEBREAK.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 10 | 9 | 0 | 1 | 0.9 (0.701, 1.0) | 0.1 | 0/0 (None) | 4/8 |
| JUDGE_2 | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 6/8 |
| TIEBREAK | 10 | 6 | 4 | 0 | 0.6 (0.313, 0.832) | 0.0 | 0/0 (None) | 8/8 |

_For reference (not recomputed here, cited verbatim from J-1205's own already-published report): granite3.1-moe:3b (the live TIEBREAK) on this SAME arm's wording scored True share 0.0, battery 4/8 (n=10)._

### Arm c_polarity -- (c) polarity-explicit key + one clarifying sentence -- THE candidate fix

Prompts: all 72 (62 real units + 2 real controls + 8 battery), 2 draws, fresh. `TIEBREAK` in this table means the CANDIDATE seat (gemma4:12b (local, Threadripper/Bonsai CPU tier -- verified 2026-09-23, NOT the live :11437 TIEBREAK)), never the live granite TIEBREAK.

| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |
|---|---|---|---|---|---|---|---|---|
| JUDGE_1 | 144 | 42 | 102 | 0 | 0.292 (0.224, 0.371) | 0.0 | 72/72 (1.0) | 7/8 |
| JUDGE_2 | 144 | 112 | 32 | 0 | 0.778 (0.703, 0.838) | 0.0 | 70/72 (0.972) | 8/8 |
| TIEBREAK | 144 | 123 | 21 | 0 | 0.854 (0.787, 0.903) | 0.0 | 71/72 (0.986) | 8/8 |

_For reference (not recomputed here, cited verbatim from J-1205's own already-published report): granite3.1-moe:3b (the live TIEBREAK) on this SAME arm's wording scored True share 0.0, battery 4/8 (n=144, unanimous-match 0.37, repeat-agree 1.0)._

## JUDGE_1 / JUDGE_2 split rate -- fresh this session (all 62 real units, arm c)

- n=62, agree=25, split=37 (split rate 0.597), unanimous-True=15, unanimous-False=10. (For reference, J-1205's own fresh arm-(c) read the same day: n=62, split rate 0.565, unanimous-True=17, unanimous-False=10 -- JUDGE_1/JUDGE_2 do not depend on which model sits at TIEBREAK, so this is a same-wording, same-day freshness check, not expected to differ meaningfully.)

## CANDIDATE (gemma4:12b) vs. the unanimous panel -- the only ground-truth-ish signal in the real prompts

- arm (c), this job: n_unanimous_true=15, CANDIDATE said True on 15 of them; n_unanimous_false=10, CANDIDATE said True (wrongly) on 5 of them; overall accuracy 0.8 (CI (0.609, 0.911)).
- _For reference: granite (the live TIEBREAK), same arm, J-1205's own fresh read: overall accuracy 0.37 (CI 0.215-0.558)._

## Pass bar (J-1205's own briefing's proposed numbers, same bar applied here to arm (c))

CANDIDATE matches the constructed battery >= 7/8: **True** (8/8). CANDIDATE matches the panel-unanimous-True prompts >= 70%: **True** (0.8). No parse-failure rate above 10%: **True** ({'JUDGE_1': 0.0, 'JUDGE_2': 0.0, 'TIEBREAK': 0.0}). **OVERALL: True** (the founder's own bar to rule on -- not this job's call to declare "fixed").

## Hub reachability probe (run before any real judge call)

```json
{
 "JUDGE_1": {
  "url": "http://LAN-HOST:11438",
  "reachable": true,
  "models": [
   "mixtral:8x7b"
  ],
  "expected_model_present": true,
  "err": null
 },
 "JUDGE_2": {
  "url": "http://127.0.0.1:11440",
  "reachable": true,
  "models": [
   "falcon3:7b"
  ],
  "expected_model_present": true,
  "err": null
 },
 "CANDIDATE(gemma4:12b)": {
  "url": "http://127.0.0.1:11439",
  "reachable": true,
  "models": [
   "gemma4:12b"
  ],
  "expected_model_present": true,
  "err": null
 },
 "WRONG_BRIEFING_ADDR(LAN-HOST:11439)": {
  "url": "http://LAN-HOST:11439",
  "reachable": false,
  "models": [],
  "expected_model_present": null,
  "err": "URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>"
 }
}
```
