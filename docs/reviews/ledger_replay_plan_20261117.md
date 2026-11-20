# Ledger replay plan 2026-11-17 (written before any ledger write)

Source: transcripts of session 482b149b-18f5-4094-87b7-2109d8b7b9a9 (main + 205 subagent files), joined tool_use to tool_result, sorted by event timestamp. Ledgers reset to `docs/ledger_backups_20261117/*.HEAD.jsonl` then replayed one call at a time through the owning tools with the clock frozen at each call's original timestamp.

## Wipe point T (differs from the 17:15 NZDT discovery time)

- Last allocation visible before the first reset: 2026-11-17T03:36:02.295Z (F-4982, D-0803; J-4160 at 03:35:18Z). First allocation that reuses a low id: 03:38:12.903Z (F-4852). So the ledgers were reset to HEAD at about 03:36-03:38Z = 16:36-16:38 NZDT, not 17:15.
- Further resets to HEAD followed (F-4852 re-issued at 03:46:45Z, 03:54:15Z, 04:04:31Z, 04:04:53Z, 04:16:12Z). Every call from 03:36:03Z on ran against a wiped state; their printed ids are NOT enforced and are remapped (153 calls).
- Windows `[WinError 5] Access is denied` on os.replace of job_queue.jsonl/findings.jsonl at 03:33:20Z and 03:38:21Z coincide with the reset.

## Replayable calls

| tool | subcommand | pre-T (ids enforced) | post-T (ids remapped) |
|---|---|---|---|
| decide | open | 7 | 6 |
| decide | rule | 13 | 0 |
| findings_log | record | 131 | 45 |
| findings_log | spawn-job | 2 | 2 |
| job_queue | add | 5 | 0 |
| job_queue | done | 72 | 41 |
| job_queue | release | 51 | 3 |
| job_queue | spawn | 55 | 14 |
| job_queue | start | 129 | 42 |
| thought_log | add | 1 | 0 |
| total | | 466 | 153 |

Includes 4 special items (see below). Read-only subcommands (show/list/next/--help) are never replayed. plan_state.py note/set calls (about 80) edit plan docs, which were not wiped, and are not replayed.

## Special reconstructions

- J-4099 and J-4100 (plan-index / plan-schema-audit jobs created by plan_maintain at 2026-11-16T07:20:44Z by OTHER session 690f9a1f, after the HEAD commit and before this session started) were also lost. Recreated with `job_queue.py add` from the full `show` output the agents captured (title, briefing, source, plan, category, created, session all identical).
- J-4130 was created by an unobserved process between 12:55:40Z and 19:09:56Z; no transcript (this session, c56fc419, 690f9a1f, 94ea488b) mentions it. A clearly labelled placeholder J-4130 (category doc, closed immediately) is created so J-4131 onward keep their ids.
- F-4886 came from a PowerShell tool call (Set-Content writes a UTF-8 BOM, so the stored claim starts with U+FEFF as in the original F-4886 line); replayed as a findings_log record with BOM-prefixed files.
- 6 helper files that were later deleted (record_J4038_*.txt, J4038_brief1/2.txt in repo root, docs/lab/J-4122_scratch_*.txt) and 11 files overwritten later (J-3900, J-4062, c.txt/e.txt/b.txt) are re-materialised from heredoc/Write events at the call time; materialised repo-root helper files are removed again after the replay.
- 21 file arguments exist on disk with no matching write event in a transcript (written by python scripts); the on-disk content is trusted. One (j3716_claim.txt) was edited in place by python before the call; disk content used.

## Skipped (no ledger change originally, or not executed)

| tool | sub | reason | count |
|---|---|---|---|
| decide | open | failed-or-not-executed(bad-plan-slug) | 3 |
| decide | open | help | 13 |
| findings_log | record | failed-or-not-executed(file-missing) | 4 |
| findings_log | record | failed-or-not-executed(other) | 1 |
| findings_log | record | failed-or-not-executed(permission-denied) | 1 |
| findings_log | record | failed-or-not-executed(winerror5) | 1 |
| findings_log | record | help | 9 |
| findings_log | spawn-job | help | 1 |
| job_queue | add | help | 4 |
| job_queue | done | help | 1 |
| job_queue | release | badargs | 36 |
| job_queue | release | failed-or-not-executed(file-missing) | 1 |
| job_queue | release | failed-or-not-executed(nothing-to-release) | 9 |
| job_queue | release | failed-or-not-executed(other) | 1 |
| job_queue | release | help | 20 |
| job_queue | spawn | badargs | 1 |
| job_queue | spawn | help | 54 |
| job_queue | start | failed-or-not-executed(No-job) | 11 |
| job_queue | start | failed-or-not-executed(winerror5) | 1 |

Skipped notes: `--help` calls, calls missing a required argument (argparse usage error), `release` of a job that was not in progress, `start` of a post-reset-missing job (No job), WinError 5 failures, permission-denied, missing claim files, a bash syntax error that executed nothing (the 11-17T03:32:16 `mk` script).

## Ambiguities / known gaps

- Any ledger change made by processes other than the transcripted agents (founder windows, scheduled jobs, plan_maintain runs by other sessions after 06:12Z, j-4130) cannot be reproduced. session_events rows for plan_state/plan_maintain/job_run actions are not reproduced; replayed rows carry their original timestamps (clock frozen).
- Post-T calls that referenced pre-T-spawned ids failed originally (No job) and are skipped; those jobs keep the state the replay gives them (see report).
- Lab python processes (J-3785, J-3311, J-4102, J-3719, J-4125) were still running during the replay; none is a ledger tool.
## Outcome (appended after the replay)

- Applied 619 items (466 pre-T with strict id checks, 153 post-T remapped). 0 strict mismatches, 0 post-T divergences, no stop. First attempt stopped at item 153 on a unix-style path argument (/c/...), ledgers were restored from post_wipe, the converter was fixed, and the replay was re-run from a fresh HEAD reset.
- Final rows: job_queue 4176 (max J-4176), decisions 809 (max D-0809), findings 5027 (max F-5027), thoughts 144 (T-0144 present), session_events 27801; ideas (162) and plan_snapshots (5343) untouched (identical to HEAD, no replayable writes).
- Pre-T ids reproduced exactly: J-4099..J-4160 contiguous, F-4852..F-4982 contiguous, D-0797..D-0803 contiguous, T-0144.
- 9 post-T arguments of the form `--from finding:F-nnnn` were translated through the mapping below.

### Post-T old id to new id (latest allocation wins; same old id was issued several times in successive resets)

| old (printed then) | new | time Z | agent |
|---|---|---|---|
| F-4852 | F-4983 | 03:38:12 | nt-a1683192b0873fd64 |
| F-4853 | F-4984 | 03:38:26 | nt-aaf595614b8cb8d8a |
| J-4099 | J-4161 | 03:38:28 | nt-a1683192b0873fd64 |
| J-4100 | J-4162 | 03:38:28 | nt-a1683192b0873fd64 |
| D-0797 | D-0804 | 03:39:01 | nt-a76f316763960fadf |
| F-4854 | F-4985 | 03:39:07 | nt-a76f316763960fadf |
| F-4855 | F-4986 | 03:39:22 | nt-abf804ba4d8e039ac |
| F-4856 | F-4987 | 03:39:32 | nt-abf804ba4d8e039ac |
| J-4101 | J-4163 | 03:39:44 | nt-abf804ba4d8e039ac |
| F-4857 | F-4988 | 03:40:02 | nt-aa12f6f9fbce77e85 |
| F-4858 | F-4989 | 03:40:33 | nt-aba98becbe2aa856d |
| F-4859 | F-4990 | 03:41:24 | nt-a2dfd960afa643b2e |
| F-4860 | F-4991 | 03:41:34 | nt-a29075c9a993e4f8e |
| F-4861 | F-4992 | 03:42:06 | nt-a8745699a06fc33f1 |
| F-4862 | F-4993 | 03:43:35 | nt-a72442a535f6e474b |
| J-4102 | J-4164 | 03:43:48 | nt-a72442a535f6e474b |
| F-4863 | F-4994 | 03:45:13 | nt-aa01db12a35671d3d |
| F-4864 | F-4995 | 03:45:29 | nt-acb09ee96de640f06 |
| F-4865 | F-4996 | 03:45:54 | nt-a66b84e3d31a34f29 |
| F-4852 | F-4997 | 03:46:45 | nt-a54ea48d0b21be3e4 |
| J-4099 | J-4165 | 03:46:51 | nt-a54ea48d0b21be3e4 |
| F-4853 | F-4998 | 03:46:51 | nt-a68f650c68ebf9832 |
| F-4854 | F-4999 | 03:47:32 | nt-aebdf78b4fdb6aab8 |
| D-0797 | D-0805 | 03:47:38 | nt-aebdf78b4fdb6aab8 |
| F-4855 | F-5000 | 03:47:53 | nt-a5abb4f489197f2bd |
| F-4856 | F-5001 | 03:48:18 | nt-a8c5f6ad635b19561 |
| F-4857 | F-5002 | 03:48:21 | nt-abf2e59163cd82171 |
| F-4858 | F-5003 | 03:48:57 | nt-a60dbd075e44e01c1 |
| D-0798 | D-0806 | 03:49:05 | nt-a60dbd075e44e01c1 |
| F-4859 | F-5004 | 03:49:08 | nt-a0fe698ea50e3e4ab |
| F-4860 | F-5005 | 03:49:26 | nt-aa12eda92576cf155 |
| F-4861 | F-5006 | 03:50:02 | nt-ad3b6a334a4c15162 |
| F-4862 | F-5007 | 03:50:12 | nt-a4a9b1765a60a5846 |
| F-4863 | F-5008 | 03:50:20 | nt-a74b6b32d6b4376ee |
| D-0799 | D-0807 | 03:50:36 | nt-a74b6b32d6b4376ee |
| F-4864 | F-5009 | 03:50:58 | nt-afd67661f2ffa001a |
| J-4100 | J-4166 | 03:51:08 | nt-afd67661f2ffa001a |
| F-4865 | F-5010 | 03:51:50 | nt-af54c15fbbdaafe90 |
| J-4101 | J-4167 | 03:51:58 | nt-af54c15fbbdaafe90 |
| F-4866 | F-5011 | 03:52:38 | nt-a327c6d17fa2eae9b |
| F-4852 | F-5012 | 03:54:15 | nt-a44afb0cd53e6ced7 |
| J-4099 | J-4168 | 03:54:24 | nt-a44afb0cd53e6ced7 |
| F-4853 | F-5013 | 03:55:21 | nt-ad87479a26aef07dd |
| J-4100 | J-4169 | 03:55:32 | nt-ad87479a26aef07dd |
| F-4854 | F-5014 | 03:56:26 | nt-ad0e28ce61d015649 |
| F-4855 | F-5015 | 03:56:47 | nt-a655588288740a593 |
| J-4101 | J-4170 | 03:56:58 | nt-a655588288740a593 |
| F-4856 | F-5016 | 03:57:35 | nt-ac7b6a88821729678 |
| F-4857 | F-5017 | 04:00:12 | nt-a54601cf92554c165 |
| F-4858 | F-5018 | 04:01:00 | nt-aa15eeb97e6cdcde8 |
| None | F-5019 | 04:02:54 | nt-a53999c8dccf0f490 |
| F-4852 | F-5020 | 04:04:31 | nt-abebc16a64d7b3d32 |
| J-4099 | J-4171 | 04:04:40 | nt-abebc16a64d7b3d32 |
| F-4852 | F-5021 | 04:04:53 | nt-af2d05254e10af90c |
| J-4100 | J-4172 | 04:05:05 | nt-af2d05254e10af90c |
| F-4853 | F-5022 | 04:06:53 | nt-ac13859a20a0ede99 |
| F-4854 | F-5023 | 04:07:08 | nt-a70c873a3189e1362 |
| J-4101 | J-4173 | 04:07:20 | nt-a70c873a3189e1362 |
| F-4855 | F-5024 | 04:09:26 | nt-a8994ee0e3951e789 |
| D-0797 | D-0808 | 04:09:37 | nt-a8994ee0e3951e789 |
| F-4856 | F-5025 | 04:11:45 | nt-a940233ad014bc10e |
| J-4102 | J-4174 | 04:11:58 | nt-a940233ad014bc10e |
| F-4857 | F-5026 | 04:12:40 | nt-a7de438ea82d52e09 |
| D-0798 | D-0809 | 04:12:49 | nt-a7de438ea82d52e09 |
| F-4852 | F-5027 | 04:16:12 | nt-a6ca6cf8a90a39c8c |
| J-4099 | J-4175 | 04:16:26 | nt-a6ca6cf8a90a39c8c |
| J-4100 | J-4176 | 04:16:26 | nt-a6ca6cf8a90a39c8c |
