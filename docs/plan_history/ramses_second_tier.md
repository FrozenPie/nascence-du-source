# ramses_second_tier — folded history


---

# History folded on 2026-09-27 from `docs\plans\ramses_second_tier.md` (plan-compact, 2 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py ramses_second_tier`._

## Current State — updated 2026-09-03 (J-0500, from F-0692)

**2026-09-21 (J-0890 interim read, F-1637): the supervisor restart gate is now MET and the first 4.8 h of the
new run are clean — but the 24 h watch is only 20% done, so J-0890 stays open.** The current supervisor is PID
9752 (started 2026-09-21 09:28:51 by the founder's standalone Control Panel Full Start, parent = explorer.exe's
powershell, not a Claude session), which postdates the J-0836 commit `9c2bd40` (09-11 12:46) and runs master's
`scripts/supervisor.py` (clean vs HEAD) with `CPU_HEALTH_TIMEOUT = 10.0` on judge1/judge2/dreamer (hot_ollama
3.0). In 4.84 h `data/supervisor.log` (7 lines, one run header, all four lanes adopted) has zero `health check
failed` / `is DOWN` / `killed` lines and the three hub PIDs are the original 09:28:46-51 processes, so no
false-positive restart; the watchdog loop is provably alive (+108 network I/O ops in a 34 s sample). The hubs
went through real slow episodes with no failed check: dreamer :11442 one 278 s load inside one 570.0 s chat
(both above F-1248's 47 h baseline max of 72 s / 522.6 s), judge1 a 77 s load and a 103.2 s chat, judge2 chats
≤ 25 s. D-0194's defeater has NOT fired (clause 2 also holds: all three live hub command lines equal
`_cpu_hub_spec()` field-for-field, argv order aside). Caveats: the hubs were launched by `launch_servers.ps1`
and adopted, so the supervisor's own relaunch path was not exercised live (F-1248's fake-hub harness stands
for it); and `data/supervisor.log` is rewritten by every supervisor start, so this run's log is lost if the
supervisor is restarted before the read. **Re-read at/after 2026-09-22 09:28:51 if PID 9752 is still up**
(repeat F-1637's read-only checks: supervisor CreationDate, `data/supervisor.log` failure-line grep, per-hub
`[chat]`/`loaded in` stats from each hub's latest `(port binds first)` line), then record the closing finding
and mark J-0890 done.

**2026-09-19 (J-0708 read, F-1567 / F-1569): CONFIRMED WORKING — the 80→200 num_predict fix removed the parse failures on real traffic (0 of 5,563 post-restart rulings, ≈19 expected), the cap is NOT behind the timeouts that also appear in the window, and a separate JUDGE_1-hub problem is now quantified.** Gate met two independent ways: the live `core/judge_panel.py` has `_NUM_PREDICT = 200`; the first master commit carrying the 200 literal is merge `c57cdb8` (2026-09-07 12:04:05 +1200); the first Du restart after it is 2026-09-08 16:42:00 NZST (first row with J-0718's `num_predict` key: 16:42:37); the current process (PID 35412, 2026-09-18 23:37:12) is later still. Window = 5,563 rows over 10.8 d wall clock / ≈171 h of live runtime (six run segments), every row `num_predict=200`. **Parse:** err1 0/5,563, err2 0/5,563, err3 0/840 tiebreak attempts, vs pre-fix 6 (0.198%) / 1 (0.033%) / 4 of 542 (0.74%) → 11.0 / 1.8 / 6.2 expected; P(0 err1 parse at the old rate) = 1.6e-5 (1.7% even at its lower 95% bound); parse-prone contexts `resolved` 5/36 → 0/61, `advances` 5/475 → 0/965. **Timeouts:** err1 timeout is 427/5,563 = 7.7% vs 0.40% pre-fix, but 399 of them sit in five contiguous all-timeout runs (two whole-hub wedges on 09-16 16:55→19:59 and 22:17→09-17 08:45, plus three short 09-18/19 runs) with JUDGE_2 healthy, 409/427 sit at the 90–100 s ceiling, and `llm_latency.jsonl` shows the same hub's other tenants (dream_node, commitment_ledger — neither using this cap) failing at ~300 s in those hours; in the ≈109 live hours right after the fix (09-08 → 09-16 07:53) err1 timeout was 13/3,757 = 0.35% vs 0.40% pre-fix — no increase. **200 stands.** One cost worth knowing: JUDGE_1's successful-call latency rose inside identical contexts (lane2 s1 p50 7.9→11.0 s, p95 30.4→38.8) while JUDGE_2's did not — mixtral now finishing answers it used to truncate; p99 is still ≈35 s under the 90 s ceiling but the margin is thinner whenever the hub degrades. `du_pulse`'s judge line prints coherently (`recent-50 … [timeout:13]`; the 500-window `err_causes {timeout:30}` equals a hand tally of the same rows; recomputed from a scratch copy of the log, nothing live touched). **New and separate (F-1569): the shared Ramses hub :11438 itself** — 23% of panel rulings since Du's 09-16 restart returned `unavailable`, and a second slowdown began ≈03:00 today (commitment_ledger median 31 s vs a 12 s baseline; last-50 unavailable 26%, just under du_pulse's 0.3 flag). D-0121's defeater ("queued/slow/timed-out calls … attributable to the shared per-hub lock") is plausibly fired, but the lock attribution is still inferred (F-1445; Ramses-side hub logs unreachable from here) and D-0101's FREEZE makes any re-homing a founder call — **no decision was touched by this job; J-1150 spawned** (needs_input: Ramses-side logs). Correction to F-1567's text: its "8 days right after the fix" is 7.6 calendar days / ≈109 live hours. **J-0708 recommended done.**

**2026-09-12 (J-0890 attempted, F-1256): restart gate still NOT met — no new information, correctly
left open.** Re-checked both of J-0836/F-1248's own named gate clauses directly rather than trusting
the 09-11 read to still hold: master's `scripts/supervisor.py` still carries `CPU_HEALTH_TIMEOUT =
10.0` (clause 2, true), but the live supervisor is still the same PID 8924 process from 2026-09-09
13:24:27 (`Get-CimInstance Win32_Process`, cross-checked against `data/supervisor.log`'s own single
unbroken 7-line run — one "starting" header, three "adopted already-healthy" lines, no second startup
and no `health check failed`/`is DOWN -- restarting`/`killed python process` line anywhere) —
chronologically before the J-0836 commit (`9c2bd403`, 2026-09-11 12:46:31 +1200) that added the
timeout, so clause 1 (a restart since that commit) is still false. Per the job's own gate instruction,
the `data/supervisor.log`/`data/logs/cpu_tier_114*.log` deep read stays correctly skipped this pass —
reading it now would only redescribe the pre-J-0836 run this plan already recorded on 09-11, not
answer J-0890's actual question. D-0194/D-0127 both remain `ruled` (confirmed via `decide.py show`,
no hold field); `decide.py list --open --plan ramses_second_tier` returns none — nothing to rule or
open here. **J-0890 left open/in_progress**; the next session should re-run the same two-clause check
fresh at that time rather than trusting this note, exactly as this entry did for 09-11's. Full
evidence: F-1256 (findings-log).

**2026-09-11 (J-0836, F-1248): D-0194's watchdog extension was already built under D-0127 — J-0836 added
only the generous health timeout, restart-gated.** D-0194 (ruled 2026-09-09) is a duplicate of D-0127
(ruled 2026-09-02): J-0495 and J-0496 were same-second twin jobs from F-0684, and J-0496 shipped
`scripts/supervisor.py`'s `_CPU_TIER`/`_cpu_hub_spec()` (commit 3ce7fb6, `--log` fix 4ce39e6) nine days
before D-0194 was opened. The live supervisor (PID 8924, started 09-09 13:24) already ensures + watches all
four local servers and its launch recipe matches the three running hubs' command lines field-for-field.
D-0127/D-0194's shared defeater (false-positive kill of a merely-slow hub) has not fired in ~47 h of that
run: 241 model loads (max 124 s) and 2,045 chats (max 522.6 s) at the old 3.0 s per-check timeout with zero
`health check failed` lines in `data/supervisor.log` — `/api/tags` is an async constant that never waits on
the gen lock. J-0836 nevertheless added the belt-and-braces D-0194 asked for: a per-spec `health_timeout`
(`CPU_HEALTH_TIMEOUT = 10.0` s on the three hubs; hot_ollama keeps 3.0 s) and a `sweep()` extraction so
the real 2-fail → `kill_on_port` → relaunch path is testable — verified 16/16 against a fake hub on
:11499 (slow 5 s hub survives; wedged hub is killed and relaunched). **RESTART-GATED:** the running
supervisor predates the commit; the 10 s timeout takes effect only when the founder next restarts it via
`scripts/start_supervisor_detached.ps1` or the Control Panel — see the verify job spawned from F-1248.

**J-0500 built (F-0721, verified):** `core/judge_panel.py`'s `_ask()` no longer collapses every
failure to `(None, None)` — it now returns `(verdict, why, err, elapsed_s)`, with `err` ∈
timeout/http/parse/exception classifying WHY a judge went unanswered (asyncio timeout — usually
queued behind F-0176's idle-unload-reload lock, not a dead hub — vs connection refused/reset vs a
judge that answered but broke the JSON/bool contract vs anything else). `rule_detail()` writes
`err1/err2/s1/s2` (+`err3/s3` on a tiebreak) into `judge_panel_log.jsonl` alongside the existing
`why1/why2`, additive-only. `judge_panel.status()`'s per-window summary now tallies `err_causes`,
and `scripts/du_pulse.py`'s judge-panel line prints a `[cause:count]` breakdown next to the
`unavailable` rate — the exact "cannot be diagnosed from data" gap F-0692 hit by hand. Also added:
an `HH:MM:SS.mmm` prefix on `scripts/nascence_cpu_server.py`'s `[chat]`/`[generate]`/`[cpu-tier]`
print lines, so `data/logs/cpu_tier_*.log` can now be time-joined against `judge_panel_log.jsonl`.
**Not done in this pass:** `deploy/ramses/nascence_cpu_server.py` (the Ramses-side copy, serving
JUDGE_1 mixtral @ :11438) was left un-timestamped — it already carries an unrelated pre-existing
drift from `scripts/` and isn't auto-synced, so folding the fix in was scope creep past this job;
see **J-0526**. **Verify by reading 50 new rows after a restart (the job's own acceptance test) is
still open** — this pass could only verify the classifier and logging mechanics directly (a
synthetic unreachable-hub probe, cleaned from the live log after); it needs Du's live process to
actually restart and accrue real `err1/err2` rows before the F-0176 diagnosis (timeout-dominated
vs http-dominated) can be confirmed against real traffic. See **J-0525**.

**2026-09-03 13:40 (J-0525 attempted, F-0727): acceptance read NOT possible yet.** Du's live process
(`run_nascence.py`, started 09:07:36) predates the `judge_panel.py` edit (12:38) — all 11,075 rows in
`judge_panel_log.jsonl`, including the 25 written after the edit, are still the old shape with **zero**
`err1/err2` rows, so there is nothing real to classify. Precondition unmet, not a defect; J-0525 stays
open until the next Du restart. Two notes for that read: (a) the only `unavailable` cluster since 09:07
is 10 rows at 09:19–09:31, all `v2=None`, exactly the F-0704 dead-CPU-tier window (killed 09:18,
supervisor relaunch 09:36) — those would classify as `err2=http` (dead hub), **not** F-0176 contention;
(b) the ~130 rows since the relaunch have 0 `unavailable` (recent-50: agree 0.88), so "the next 50 rows"
may hold no failures at all — the F-0176 timeout-dominance question needs a window that actually
contains failures. Also: the local hub logs the cross-log join was built for are currently dark
(`data/logs/cpu_tier_11440.log` last written 09:15; `data/cpu_tier_11440.log` 0 bytes) because the running
supervisor (09:36) predates J-0520's `--log` wiring — that half of J-0500's payoff is supervisor-restart-gated
too (J-0520's territory). `du_pulse`'s `[cause:count]` rendering re-checked in isolation on a temp copy of
the real log: correctly suppressed on real data, prints `[timeout:1, http:1]` with a synthetic err row.

**2026-09-03 (J-0527, F-0741): the mid-J-0500 "revert" of `judge_panel.py`/`du_pulse.py`/`nascence_cpu_server.py`
was not a Ramses-tier defect** — a concurrent job-run agent's `git stash`/failed `pop`/`git checkout stash@{0} --`
in the shared tree (transcript-attributed, F-0741). The re-applied J-0500 edits are byte-identical to the stash's
copies, so nothing from this plan was lost. Toolchain guard added to CLAUDE.md + job-run SKILL.md; nothing further
for this plan.

**2026-09-05 (J-0535, F-0912): the F-0176/D-0039 "queued-but-alive" contention pattern (previously measured
only on the local judge CPU tier, :11439/:11440) is now also confirmed on `command-r7b` @ LAN-HOST:11441 —
the background lane itself, not just its judge-tier neighbours.** Chasing an unrelated question (why
`core/essay_lesson.py`'s capstone essays hadn't fired since before a 09-03 fix), an isolated live repro found
`essay_lesson.compose()` taking 353.7s and 562.0s (two separate runs) to complete a real essay via this hub —
slow but NOT down (`/api/tags` answers in <0.1s both times; one bare probe hit `transport error ... TimeoutError()
— failing over` then answered on the local qwen3.5 fallback in 20.9s total). `data/nascence.log` independently
shows the same `LAN-HOST:11441` transport-timeout line recurring unprompted on 09-04/09-05. Net effect: 4 real
finished books have sat un-essayed for 33+ hours because real (idle-tick-triggered, restart-exposed) attempts
apparently aren't surviving the multi-minute compose() call, even though two standalone uninterrupted repros both
finished cleanly. This is the SAME mechanism D-0039 is weighing for the judge tier (raise the timeout vs.
cap/stagger concurrent load) — just observed on a different hub, and with a different failure shape (a live
capstone silently abandoned mid-flight rather than a judge_panel `unavailable` verdict). See F-0912/F-0913
(findings-log), J-0645 (follow-up analysis: confirm the abandoned-mid-flight mechanism, spawned), and the new
open decision below on whether the background lane needs the same visibility D-0039's instrumentation gave the
judge tier. Full evidence: F-0912.

**2026-09-06 (J-0645, F-0953, D-0169 RULED): the abandoned-mid-flight hypothesis is NOT confirmed — the real
mechanism is schedule-opportunity scarcity, and the real backlog is 10 books, not 4.** A live re-check found
essayed count still 85 and zero `[essay]` log lines across a fresh 16.5h *uninterrupted* uptime window
(2026-09-05 16:42→2026-09-06 09:13, zero restarts) — ruling out "it just needs a quiet stretch" too. The actual
cause: `core/essay_lesson.py pending_book()`'s own `live_since=2026-06-23` gate permanently hides **6** older
finished books (2026-06-17→23) from the live path by original design ("left for the deliberate backfill"); of
the 4 recent books, the *only* reachable trigger is a school-gated call site good for a single 45-minute
weekday-morning window (9:00–9:45am, `core/school.py`), and the one such window since they finished (Fri 09-04)
was missed by Du being down 08:13–11:37 that whole morning — not by any attempt starting and getting cut off.
The other call site (`_remediation_stream`) is structurally starved for backlog books: `school.py`'s own
ungated per-tick curriculum advance always rolls the current-book pointer past a finished book first. Positive
finding: `scripts/backfill_essays.py` (already built 2026-06-23 for exactly this, routed through the healthy
hot lane, not the contended Ramses hub) `--dry-run`-verified live and clean against all 10 books. D-0169 ruled:
skip (C)'s interruption-resilience engineering (unwarranted — no real attempt has yet been observed to fail);
spawned two follow-ups instead — widen the bare `except Exception: pass` at both `_essay_lesson` call sites to
at least log `BaseException`/`CancelledError` (cheap visibility), and run the real backfill against the 10-book
backlog once Du's live process is confirmed stopped (the script has no cross-process lock on
`reading_state.json`/`essay_lesson_state.json`). Full evidence: F-0953.

**2026-09-06 (J-0667, F-0973): the real backfill run (D-0169's option (D), the spawned follow-up)
attempted this pass, deferred — Du's live process was confirmed actively running, not the "confirmed
stopped" precondition D-0169's own ruling and the job's own briefing both require before touching
`reading_state.json`/`essay_lesson_state.json` with no cross-process lock.** Checked two independent
ways rather than trusting one: (a) the project's own log-line convention — `data/nascence.log`'s last
"Nascence shutting down." line is 2026-09-05 16:42:49, but the file's actual tail is live monologue/
competence lines timestamped 2026-09-06 15:57:37–15:57:55, about a minute before the check, with no
shutdown between; (b) an independent process-list check (`Get-CimInstance Win32_Process`, not
log-derived) found `run_nascence.py` (PID 20692) running continuously since 2026-09-05 19:15:10 (~20.7h
uptime), alongside the full supervised stack (supervisor, JUDGE_1/JUDGE_2/dreamer CPU hubs, HUD server).
Both agree: not stopped. Per this batch's own ground rule, the job did not force the run or stop Du
itself — only a fresh `--dry-run` was re-run (re-confirmed zero-write via essay_lesson_state.json's
mtime/essayed-count unchanged before/after), which found the backlog byte-for-byte unchanged from
F-0953: still the same 10 books, same note/char/file counts. No new eligible weekday morning window
has occurred since Fri 09-04 (09-06 is a Sunday). **J-0667 left open/in_progress** — the real run
(`--limit 1` test, then the rest) is still the right next action, just not yet, and needs re-checking
Du's live-process state fresh at attempt time rather than assuming this reading still holds. Full
evidence: F-0973 (findings-log).

**2026-09-06 (J-0668, F-0985): D-0169's other spawned follow-up — the cheap CancelledError-visibility
fix — is LANDED, restart-gated, unverified live.** Both `_essay_lesson()` call sites in
`nodes/inner_monologue_node.py` (`_remediation_stream` at line 1477; the school-gated reading-period
branch at line 2070 — both unshifted from the briefing's line refs) now catch `asyncio.CancelledError`
separately, log `logger.warning("[essay] _essay_lesson interrupted mid-flight (cancelled)")`, and
re-raise (cancellation semantics still propagate to `core/orchestrator.py`'s `stop_background()`
correctly — nothing is swallowed, only logged first), before falling through to the existing bare
`except Exception: pass`. `udms_get_change_dossier` run first per this repo's cognitive-node rule:
PURE_SCALAR_TWEAK, risk_tier LOW, 96.5% confidence, no SCC cycle; `core/orchestrator.py` confirmed as
a real CONTRACT-layer dependent (consistent with it owning the `task.cancel()` this fix concerns), no
dependent specific to `_essay_lesson()` beyond the two named sites. `git diff` shows exactly 6 added
lines (3 per site), both sites structurally identical; `py_compile` clean. Per the job's own scope,
this is NOT a claim that anything has been fixed live — D-0169/F-0953 already established no real
`_essay_lesson` interruption has occurred yet to exercise this against, and this node's live process
does not hot-reload, so the log line takes effect only on Du's next restart, and only proves itself
the next time a restart actually interrupts an in-flight essay attempt. Full evidence: F-0985
(findings-log).

**2026-09-06 (J-0608, F-0969): F-0176/F-0692's JUDGE_2-timeout diagnosis is CONFIRMED by real traffic,
at much lower severity than the original spike — D-0039's "Wait" ruling stands, not defeated.** Re-ran
F-0834's own method (Counter over `err1`/`err2`, `err1`-key-present filter) against the full current
`data/judge_panel_log.jsonl` (13,575 rows, no tail-sampling) rather than F-0834's 1,368-row snapshot:
985 new post-J-0500 rows have accrued (2,353 total, 2026-09-03T06:39→2026-09-06T03:47), carrying 9 new
real failures beyond F-0834's original 2 (11 total, past the job's own "10+" threshold). **JUDGE_2
(falcon3, local :11440) failures have reappeared — 4, zero at F-0834's snapshot — and cluster as
`timeout` (3 of 4)**, matching the original mechanism rather than refuting it: two rows share an
identical `ts` (2026-09-05T14:35:24.3Z, contexts `lane2:coherence`/`lane2:metaphor`) and an identical
`s2=90.74s`, i.e. two concurrent judge calls both queued onto JUDGE_2 and both timing out at the same
elapsed point — direct evidence of `nascence_cpu_server.py`'s one-lock-per-hub queuing, not a dead hub.
**But severity is down roughly two orders of magnitude**: `how` over the window is
`{agreed:1957, tiebreak:385, unavailable:9, split_no_tiebreak:2}` — a 0.38% unavailable rate, not
F-0176's original 66–80%-in-90-minutes spike. D-0039's own defeater ("reopens if the recent-50
unavailable_rate instrument shows the spike recurring on a future night") is judged NOT met by this
data; D-0039 was not reopened. **New, separate pattern found**: JUDGE_1 (mixtral, Ramses :11438) now
shows a `parse`-dominant signature (4 of 5 real failures), all at fast elapsed times (15–18s, nowhere
near the 90s timeout) — a distinct, unconfirmed contract-breaking issue (candidate cause: the fixed
`num_predict=80` decode budget truncating a verbose mixtral answer), not the F-0176 mechanism. See
F-0969 (findings-log) for the full row-by-row evidence; J-0675 spawned to chase the JUDGE_1 parse
pattern specifically.

**2026-09-06 (J-0675, F-0994): the num_predict=80 truncation hypothesis F-0969 left unconfirmed is
now CONFIRMED by direct live repro against the real JUDGE_1 hub, not just inferred.** Root cause:
`deploy/ramses/nascence_cpu_server.py`'s `/api/chat` maps `options.num_predict` straight to
llama-cpp-python's `create_chat_completion(max_tokens=..., response_format={"type":"json_object"})`
— on this stack, `response_format="json_object"` does **not** rescue a completion cut off mid-stream
by `max_tokens`; it just truncates, leaving an unterminated-string JSON blob. A forced-verbose live
probe against JUDGE_1 (LAN-HOST:11438) at `num_predict=80` returned `eval_count=80` (exactly the
cap) and content ending mid-string — `json.loads` raises `JSONDecodeError: Unterminated string...`,
precisely `_ask()`'s own `err="parse"` catch. 8 fresh real production-shaped "advances" prompts
(3 from pursuit 390eabac itself, 5 from other live pursuits) all completed cleanly at 19–49 of the
80-token budget — the failure is a genuine rare tail (~0.17%) that a handful of fresh trials didn't
land in by chance — but a timing model fit to those 8 clean calls (elapsed_s ≈ 2.13 + 0.1705·eval_count,
cross-validated: it predicted the forced-truncation trial's own elapsed to within 0.4s) puts all
**three** real `pursuit:*`-context JUDGE_1 failures F-0969 logged (15.21s/15.9s/17.03s) at an
estimated ~77–87 generated tokens — right at the 80-token ceiling, not the ~20–35 tokens a fast
wrong-shape answer would need. Re-reading F-0969's other logged parse rows through the same lens:
TIEBREAK/granite's 2 parse failures (3.06s/4.73s, ~5–15 est. tokens) are a clearly **different**,
fast, non-truncation mechanism — confirms they're unrelated, as F-0969 hedged — while JUDGE_2's one
parse failure (16.23s, ~82 est. tokens) falls in the *same* near-ceiling bucket as JUDGE_1's, meaning
the cause is the single shared `num_predict=80` literal in `_ask()`'s one payload dict (used by all
three hubs), not something mixtral-exclusive at the code level — though mixtral hits it most often in
practice, plausibly because its other duties (dream-primary, commitment-defeater) trend longer-form.
Cost/benefit: raising `num_predict` costs ~nothing in the common case (a ceiling, not a fixed cost)
and stays well inside the existing 90s `TIMEOUT_S` even in a worse-than-observed tail. **J-0693
spawned** (build: raise/parameterize `num_predict` in `_ask()`, then watch `judge_panel.status()`'s
`err_causes` after Du's next restart to confirm `parse` drops without new `timeout` appearing). No
decision opened — a costed, low-risk parameter fix, not a founder-level call. Full evidence: F-0994
(findings-log).

**2026-09-06 (J-0644, F-0972): the self_predict() digit-anchor rephrase (J-0535/F-0913's own
prescribed fix) is APPLIED — `core/essay_lesson.py self_predict()`'s scale description now reads
"one = ...; zero = ..." / `{"grounding": <a number between zero and one>}`, byte-for-byte the text
F-0913 already validated fixes the parroting bug on real command-r7b traffic (4/4 → 0.000 old, 3/3 →
0.5 rephrased, same hard input). No bare `0.0`/`1.0` substring remains in the prompt (verified by
extracting the literal source); file compiles clean; the edited `self_predict()` runs without
crashing on both a hard non-essay input and F-0913's own saved real full essay. **Could not
independently re-confirm the command-r7b-specific numbers today**: `command-r7b` @
`LAN-HOST:11441` gave `ConnectionRefusedError` (actively refused, not a timeout) at every check
across a ~7-minute span (15:51–15:58), a different symptom shape than F-0912's own "slow but not
down" characterization one day earlier — every isolated test call failed over to the local
`qwen3.5:9b` hot lane instead, which never pinned to 0.000 on either the old or new prompt (0.1–0.2
throughout), so today's own numbers aren't comparable to F-0913's. The behavioral fix claim rests on
F-0913's already-verified command-r7b evidence, unchanged; only the code-level correctness of
applying that exact fix is newly verified. **Restart-gated like a8d48fa**: no module hot-reload, a
running background-lane process won't see this until it restarts. Full evidence: F-0972
(findings-log). The command-r7b refused-connection observation itself is flagged as a small separate
follow-up (see job-queue), not folded into this entry further.

**2026-09-06 (J-0680, F-0996): the command-r7b refused-connection state J-0644/F-0972 hit
(2026-09-06 03:51–03:58 UTC / 15:51–15:58 NZST) was TRANSIENT, confirmed by a fresh recheck, not
just assumed.** A direct recheck ~2.5h later (06:19–06:20 UTC / 18:19–18:20 NZST) found the hub
fully healthy on two independent live methods run from this box (never touched the Ramses machine
itself, per this plan's own working-method boundary): a raw TCP connect (`Test-NetConnection`,
succeeded) and 4 separate `/api/tags` HTTP calls over ~15s (all 200, ~0.05–0.06s total, ~2ms
connect — a live hub, not a queued-but-slow one). Real production traffic in `data/llm_calls.jsonl`
corroborates independently: command-r7b served real callers (`lane2`, `subconscious_node`,
`inner_monologue_node`, `CuriosityNode`, `symbolic_reading`) continuously from 05:40:05Z through
06:05:31Z UTC with no visible gap, ending only ~14 minutes before this job's own direct check —
i.e. the hub was already back to normal before this recheck even ran. Upper bound on the outage:
at most ~1h42m (03:58Z last-observed refusal → 05:40Z first-confirmed-healthy real call).
`\\ramses\D\Du\NASCENCE_NOTES.md` is unchanged since 2026-08-28 08:41 — no new Antigravity entry
about this window, consistent with an unannounced ordinary hub reload rather than a reported
incident; nothing escalated since the hub is confirmed healthy now. This is a DIFFERENT failure
shape than the F-0176/D-0039/F-0912 "queued-but-alive" contention pattern this plan already tracks
(a TCP-level refusal means nothing was listening, not a slow-but-answering hub under load) — but
D-0039 itself is untouched by this: that ruling concerns judge-tier timeout policy under
contention, not a one-off refused-connection blip that has already resolved. No follow-up job
spawned and no decision opened — the briefing's own "if reachable again... record and close"
contingency is exactly what happened. Full evidence: F-0996 (findings-log).

**2026-09-06 (J-0680 continued, F-1004): CORRECTION — F-0996's "transient, resolved" read did not
hold. The refused-connection pattern resumed ~35 minutes later and is a second, longer, still-live
episode, not a closed one-off.** A fresh independent recheck (~08:50–08:51 UTC, ~2.5h after F-0996's
own healthy read) found command-r7b refusing again on two separate live tools (PowerShell
`Test-NetConnection`: `TcpTestSucceeded=False`/`PingSucceeded=True`; a separate `curl -v`:
"Connection refused" — with a same-breath control call to the local hot lane succeeding instantly,
ruling out a tooling artifact). Reading the real `data/llm_calls.jsonl` with F-0972/F-0996's own
established method (a command-r7b attempt immediately followed by a different-model attempt at the
identical call site = failed over) makes the shape precise: 0/28 (0.0%) failed 06:05–06:55 UTC
(F-0996's own clean window, unchanged) versus **54/100 (54.0%) failed 06:55–08:52 UTC**, still
44.4% (8/18) failing in the final 30 minutes — not tapering off. First new failure: 06:55:49 UTC.
Every failed call still failed open correctly to the local `qwen3.5:9b` hot lane within 2–7s (no
consumer left hanging — this plan's own fail-open design working as intended), so this is a
latency/model-substitution cost hitting essentially every `core.schema.SERVE_CHAINS["background"]`
consumer, not a capability outage. The failure signature is also distinct from F-0176/D-0039's
already-documented local-CPU-tier pattern: successes and failures interleave within seconds of each
other at different call sites (e.g. one call succeeds, a different one refuses 2s later, a third
succeeds 1s after that) — consistent with either a Ramses-side crash/restart loop, or this hub
having a much smaller effective concurrency ceiling than the local hubs' queue-then-90s-timeout
behavior (refusing a second in-flight connection outright rather than queuing it). Not distinguished
by this check. **J-0696 spawned** to characterize which, next time the pattern is caught live, and
to weigh whether the background lane deserves the same call-level err-classification J-0500 gave
`judge_panel` (an idea F-0912/J-0535 flagged as "the new open decision below" but that was never
actually opened — confirmed via `decide.py list --open --plan ramses_second_tier`, no match). A
short factual note was added to `\\ramses\D\Du\NASCENCE_NOTES.md` per its own standing "add new
entries... sign with — Nascence" convention, since nothing there yet reflected this window. No
decision opened here — no real founder-level tradeoff has surfaced yet, only an uncharacterized
reliability pattern; D-0039 remains untouched (it concerns judge-tier timeout policy specifically).
Full evidence: F-1004 (findings-log).

**2026-09-07 (J-0696, F-1008): command-r7b flapping RESOLVED, root cause identified, independently
verified — not just taken on Ramses's word.** Ramses (Antigravity) posted to
`\\ramses\D\Du\NASCENCE_NOTES.md` that command-r7b (:11441) was still running its pre-consolidation
`--lazy --idle-unload 900` config — every 15 min idle it evicted itself, and a call landing during
the cold-reload/teardown window under `get_gen_lock()` got refused at the TCP layer, exactly
F-1004's signature. Relaunched eager, no `--lazy`/`--idle-unload`, sole 3070 tenant. **Verified
independently from this side:** 5 consecutive `/api/tags` checks 2s apart, all HTTP 200 in ~50ms;
`data/llm_calls.jsonl` shows the only 2 post-fix command-r7b calls both succeeded (thin sample —
worth a follow-up look once real overnight volume accrues, same as F-0996's premature "resolved"
call should have gotten). This settles J-0696's crash-loop-vs-concurrency-ceiling question in favor
of a third, now-named mechanism (idle-unload eviction cycling), not either literal hypothesis.
**Separately, Ramses also stood up the long-dormant D-0057 deepseek-r1:7b hub on :11444** (i9 CPU).
Independently verified genuinely ready, not just reachable: `/api/tags` confirms model identity;
a production-shaped `/api/chat` call using Lane 2's own real params (`core/lane2.py`'s
`MAX_TOKENS=1400`, `NUM_CTX=4096`, temp 0.2) returned a valid, coherent completion in 58.4s —
comfortably inside `TICK_S=300s`. (Two earlier default-`num_predict` probes appeared to hang for
30s/60s with nothing returned; a `num_predict=30` probe proved the hub was healthy all along —
deepseek-r1 spends its budget on a `<think>` block before `content`, the exact trap
`parse_json_loose`'s own docstring already documents. Not a new bug, a test-methodology miss on my
first attempt.) **This directly matters to D-0058**, which was already reopened 2026-09-05
(F-0926) on its own "echo disease" defeater and is sitting open for a founder `/decide-review`
between tolerating/patching command-r7b's tide-topic template lock or moving the Witness seat to
deepseek — the reopened defeater's own "if :11444 is ready now" branch is, as of today, true. Note
also: this plan's own top-of-file freeze language (D-0101, 2026-08-30: "J-0314 ... closed moot ...
nobody is chasing that standup right now") is now stale on that one clause — someone (Ramses,
unprompted) did chase and complete the :11444 standup. That freeze status and D-0058's reopened
status are in real tension (D-0101 says no more reshuffling; D-0058's own defeater being met is an
argument for reshuffling) — left for the founder's `/decide-review` to weigh, not resolved here.
One minor citation flag: Ramses's note credits part of the fix to "J-0526 complete" — Nascence's
own J-0526 is an unrelated, still-`in_progress` job; doesn't change the substantive (independently
verified) technical claim. Full evidence: F-1008 (findings-log).

**2026-09-07 (J-0693, F-1014): the num_predict=80 truncation fix J-0675/F-0994 costed is BUILT —
`core/judge_panel.py`'s `_ask()` shared payload literal raised 80 → 200, uniform across JUDGE_1/
JUDGE_2/TIEBREAK.** Chose the uniform bump over parameterizing `_ask()` per-hub (the job briefing's
two offered options): lowest code churn, and F-0994's own evidence already showed JUDGE_2 hitting
the same near-ceiling signature at least once, while TIEBREAK's parse failures are a separately-
confirmed fast non-truncation mechanism this raise cannot affect either way. `udms_get_change_dossier`
run first (ELEVATED/HIDDEN_HISTORICAL_DEPENDENCY, no SCC cycle); every listed dependent confirmed to
reach this literal only through `rule()`/`rule_detail()`, none hardcoding `num_predict` itself, so the
fix stays fully contained to one file/one line (+ a documenting comment). Verified statically this job
— `py_compile` clean, and `inspect.getsource()` on the freshly-imported live function confirms the
executed body reads 200 with no `80` remaining (no network calls made this check). Both server-side
copies (`deploy/ramses/nascence_cpu_server.py`, `scripts/nascence_cpu_server.py`) re-read to confirm
neither clamps `num_predict` below the new value. Committed to the `ramses_second_tier` job-run
worktree (`jobrun/ramses_second_tier`, commit `6beccc1`) — **not yet merged to the live tree, and
restart-gated like every other judge_panel/lane2 fix in this plan**: this module doesn't hot-reload,
so nothing changes for real traffic until the branch merges and Du's process restarts afterward.

A full-corpus re-read of the live `data/judge_panel_log.jsonl` this job (14,251 rows, read-only, same
whole-file-Counter method as F-0969/F-0994 rather than a tail sample) both set the pre-fix baseline for
the follow-up watch job and independently corroborates F-0994 with fresh, out-of-sample data: 4 more
real parse failures accrued in the ~15 hours after F-0994 closed (JUDGE_1 parse 4→6, TIEBREAK parse
2→4, JUDGE_2 parse unchanged at 1) — one new JUDGE_1 row (2026-09-06T08:45:40Z, `pursuit:e091591a`,
15.4s) lands at an estimated ~78 tokens by F-0994's own timing fit, squarely in the near-80-ceiling
truncation bucket the fix targets, postdating F-0994's own record so it wasn't reused evidence. Current
full-corpus baseline (since J-0500's err1/err2/err3 fields began): `err1={timeout:12,parse:6}`,
`err2={timeout:5,parse:1}`, `err3={parse:4}`. No decision opened — matches F-0994's own conclusion,
re-confirmed against this job's decision_flags (no active holds, no open decisions to weigh). **J-0708
spawned**: read `judge_panel.status()`/`data/judge_panel_log.jsonl` again once the merge + a real Du
restart are both independently confirmed and traffic has accrued, compare post-restart rows against
this baseline, and record whether `parse` actually dropped without a new `timeout` appearing in its
place (F-0994's own flagged risk if the cap went too high). Full evidence: F-1014 (findings-log).

**2026-09-07 (J-0718, F-1095): the num_predict 80→200 raise just above (J-0693, F-1014) IS merged to
master** — `git show master:core/judge_panel.py` confirms it (merge commit `c57cdb8`,
2026-09-07T12:04:05+12:00) — correcting that entry's own "not yet merged" note. Still restart-gated:
J-0708 (still open) is the live re-verification step, and neither that raise nor the addition below
has been exercised by Du's actual running process yet.

Separately — this job's own source is a DIFFERENT finding (F-1035, from J-0702's train_split_merge
lab, unrelated to this plan) — found the shared, one-size ceiling above still had no per-call
override, so `core/judge_panel.py`'s `_ask()`/`rule()`/`rule_detail()` now also accept an optional
`num_predict` parameter, defaulting to 200 (this section's own value, via a new `_NUM_PREDICT`
constant) — NOT the 80 F-1035's own job briefing named, which was accurate only because F-1035 was
recorded ~27 minutes before this section's own fix reached master (see F-1095 for the exact
timeline; defaulting to 80 as literally briefed would have silently undone the raise above for every
caller). Every caller listed in this section keeps getting exactly 200, unaffected. Also added:
`rule_detail()`'s own return dict now carries `err1`/`err2`/`err3` (previously log-row-only) for a
caller that wants ITS OWN call's failure cause without reading `judge_panel_log.jsonl` by hand — the
`[cause:count]` aggregate this section already gave `du_pulse` (J-0500, above) is untouched. Verified
in isolation (21/21 checks, no live hub traffic, live store canary-scanned clean). Committed to
`jobrun/judge_panel_param` (commit `bacf4e2`), not yet merged. Full evidence: F-1095 (findings-log).
**J-0764 spawned** (plan `train_split_merge`, not this one): now that both a higher default and an
explicit override exist, is train_split_merge's own F-1034 prompt-tightening still needed, or can
its original fuller prompt run clean — untested until now, genuinely open either way.

**2026-09-08 (J-0708 attempted, F-1152): the live re-verification is NOT YET CONCLUSIVE — real
traffic has only just started accruing, and 41 rows isn't enough to say anything.** Both hard
preconditions independently confirmed true this pass (not assumed): the live tree's
`core/judge_panel.py` `_NUM_PREDICT` reads 200, not 80; Du's live process (`run_nascence.py`, PID
17216) started 2026-09-08 16:41:23 local, after both the J-0693 fix (master commit `c57cdb8`) and
J-0718's param addition (`bacf4e2`) — confirmed two independent ways (`Get-CimInstance
Win32_Process`'s own `CreationDate`, cross-checked against `data/nascence.log`'s "Nascence shutting
down." → "Memory store initialised"/"Nascence is awake." lines). A full-file (not tail-sampled) read
of `data/judge_panel_log.jsonl` found 41 rows in the ~73 minutes since that restart — all
`num_predict:200`, **zero** `err1`/`err2`/`err3` of any kind, `how={agreed:33,tiebreak:8}` — a clean,
fix-consistent result, cross-checked against `judge_panel.status()`'s own "recent" sub-summary
(matches). But it is **not a statistically meaningful sample**: at the pre-fix baseline combined
err1-or-err2 rate this plan already established (~0.17% over 14,251 rows, F-0994/F-1014), the
expected error count in 41 rows is ~0.07 — under 1 in 10 — so a zero-error run this small looks the
same whether or not the fix actually changed anything. Also confirmed (useful context, not the
answer): the 796 rows between F-1014's baseline cutoff and this restart ran under the *same single
continuous pre-restart process* the whole time (no restart in between, checked directly against
`data/nascence.log`) — so that whole window, despite the fix already being on disk, was still served
by the old in-memory 80-cap code, exactly as this module's no-hot-reload behavior predicts, and
explains why it still shows old-code-shaped errors (`err1={timeout:5,parse:3}`, `err3={parse:2}`).
**J-0708 left open** rather than force a conclusion from a thin read (mirrors J-0525's own precedent
in this same plan, §"2026-09-03 13:40" above); **J-0807 spawned** to re-run the identical read once
several more hours of uptime accrue on this same restart. Full evidence: F-1152 (findings-log).

**2026-09-09 (J-0807, F-1188): CONFIRMED WORKING — the num_predict fix is holding on real traffic,
and the one failure the re-read caught is a different, already-solved mystery, not a new one.** Same
restart (PID 17216, 2026-09-08 16:41:23 local) independently reconfirmed still current by two methods
(`Get-CimInstance Win32_Process`; `data/nascence.log`'s shutdown/awake lines) — now 531 rows over
15.54h, not J-0708's 41 rows over 73 minutes. All 531 carry `num_predict=200`; **zero** parse failures
on JUDGE_1/JUDGE_2/TIEBREAK — against a pre-fix parse-only baseline (7/14,251 = 0.049%) that would
predict only ~0.26 expected events in a sample this size, a clean zero is real signal. Cross-checked
against a live `judge_panel.status()` call (agrees exactly). **One real failure occurred** (`err1=
timeout`, JUDGE_1, `context=lane2:prediction`, `s1=1104.55s`) — but tracing it down closed the loop on
a DIFFERENT open thread rather than opening a new one: it's the same soft-timeout-ceiling mechanism
F-0834/J-0607 already diagnosed 2026-09-04 (aiohttp's `ClientTimeout(total=90)` can't fire until Du's
single asyncio event loop frees up, and a lane2 call in-flight right as Du enters its Sleep pipeline
gets caught behind it) — except F-0834/J-0607 had only n=1 to go on. This job found the full picture:
**10 rows / 7 distinct incidents** of this exact signature across the whole log's history
(2026-09-03→09-08), every one `err=timeout` on JUDGE_1 from one of lane2's 3 call sites and no other
judge_panel caller; 4 independently checked directly against `data/nascence.log` and all 4 land
immediately after an "entering Sleep State"/"sleep replay" line pair, each followed by a whole-process
activity gap (everything silent, not just judge_panel) matching the row's own elapsed time almost to
the second. Also confirms the mechanism is independent of `num_predict`'s value, not caused by the
raise: 3 of the 4 verified incidents ran under the *old* 80-cap code (same continuous pre-restart
process, 2026-09-05 19:15→09-08 08:22, never restarted to pick up the fix), same multi-hundred-second
overrun as the new 200-cap occurrence. **No action on `num_predict` itself** (200 stands — the
briefing's own "consider lowering it" contingency doesn't apply, since the overrun isn't generation-time
at all: 200 tokens ≈ 35s worst case per this file's own comment, nowhere near the 780–1104s observed).
**No new job spawned** for the sleep/event-loop pattern either — **J-0621** (`data_store_hygiene`,
in_progress, targets the `ClimateEngine` 60MB-per-5s-tick parse F-0853 already flagged as a plausible
contributor to this same congestion) already carries, as its own point 4, the exact check this pattern
needs ("post-flip read... J-0607 overrun pattern absent") once `SUBC_LIGHT_READ` flips — reconfirmed
still `False` live as of this read, so that check hasn't run yet; this finding's 7-incident count (up
from J-0607's original 1) is there for whoever runs it. Full evidence: F-1188 (findings-log).

## Current State — verified 2026-08-27 (all hubs probed live, §5 drafted per D-0044)

**D-0044 (Travis, 2026-08-27):** "We have about 7 llm nodes available now we set up all the ramses
ones. We should be looking at redistributing our load to these in a new plan (maybe existing)." This
plan is the existing home; §5 below is that draft (J-0303). **Du's restart is gated on this
redistribution being worked out** (founder, same session). Every hub was probed with a real
`/api/tags` call this session — the inventory in §5.1 is measured, not assumed. D-0039 (judge-tier
false-unavailable) stays ruled WAIT, but §5's tiebreak move would dissolve its cause if adopted.
Related evidence: F-0381 (dream-node yi:34b bottleneck confirmed: 227 calls, mean 184s, 16.3% fail —
the fabric's worst profile; and the stale-config sweep list).
