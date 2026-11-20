# CLAUDE.md — Nascence project-tooling rules
> **Scope of this file:** how a Claude Code session should use the planning/tracking toolchain built
> 2026-08-23 (job-queue, decide, idea-log, findings-log, the plan-index family, skill-manager,
> session-wrap/resume). This file does **not** describe Du's own cognitive architecture — that lives
> in `docs/ROADMAP.md`, `docs/plans/`, `SESSION_HANDOFF.md`, and the code itself. Read those for what
> Du **is**; read this for how an assistant session should behave **while working on this project**.
>
> The toolchain itself lives outside this repo, at `C:\Users\USER\.claude\skills\` — these are
> Claude Code assistant tools, not part of Du. This file is the one piece that belongs *in* the repo,
> because `CLAUDE.md` is what a Claude Code session auto-loads on start.

## First thing every session

Before anything else, **the very first user message gets logged as a Thought via `/thought-log`** —
this is NOT a rule in this file; it's enforced by the founder's own global
`C:\Users\USER\.claude\CLAUDE.md` (applies to every project, every session, not just this one).
Resolving a real ambiguity a 2026-08-23 handoff flagged: if you're looking for "the thought-log rule"
and don't see it below, that's correct — it deliberately lives in the global file, not here, so it
fires even in sessions whose working directory isn't `C:\Nascence` (most of this toolchain's own
sessions run from elsewhere and reach in via absolute paths — see any skill's own SKILL.md).

Then run **`/session-resume`**. It reads the most recent `/session-wrap` handoffs and cross-checks
them against the live tools (nothing in a handoff should be trusted as current without that check —
see its own `SKILL.md`). If nothing relevant turns up, it says so plainly — that's a real answer, not
a failure to dig deeper.

## The rules (founder ruling, 2026-08-23)

**1. Log as you go — don't reconstruct at the end.**
Every mutating action across this toolchain already logs a real timestamp to
`docs/session_events.jsonl` live (job-queue, decide, the plan-index family, gauge-check,
memory-links, skill-manager, idea-log, findings-log) — you don't have to do anything extra for those.
What's *not* automatic is this session's own narrative: raise ideas, findings, and jobs through the
tools below **as they come up in conversation**, not by trying to remember them at `/session-wrap`
time. The entire `backfill` job category (30+ open the day this rule was written) exists because that
reconstruction step got skipped in the moment, not because anyone forgot to care.

**2. An idea that isn't a plan yet goes in `/idea-log`, not just a sentence in chat.**
```
python idea_log.py add "..." --tags a,b
```
Promote it once a real plan doc exists: `idea_log.py promote I-0003 --to-plan SLUG`.

Added 2026-08-23, same day: a musing that isn't even framed as an idea yet — the very first raw
thought of a session — goes in `/thought-log` one rung earlier (`thought_log.py add "..." --tags a,b
--session <uuid>`). It promotes forward into an idea (`--to-idea I-0004`) or straight to a plan
(`--to-plan SLUG`) once it's actually shaped. See "First thing every session" above for when this
fires automatically.

**3. A plan being drafted goes in `docs/staged/`, a plan that's live goes in `docs/plans/`.**
Already-existing convention — both directories are scanned by the whole plan-index family
(`plan-index`, `plan-liveness`, `decide`, `plan-schema-audit`), so a plan in `docs/staged/` is not
invisible to the toolchain, it's just correctly marked as not-yet-committed. Move the file when it
graduates; don't invent a third bucket.

**4. A finding must say how sure you are — and act on what it surfaces.**
```
python findings_log.py record --claim "..." --evidence "..." --confidence verified|inferred|guessing --by claude
```
`--confidence verified` is **refused** without real, checkable evidence cited (a file, a command
actually run, a log line quoted) — this is CLAUDE.md's own "I know / I infer / I'm guessing" rule
enforced structurally, not left as something to remember. If a finding surfaces follow-up work — a
test to run, a lab experiment, a fix — spawn it immediately, don't let "we should test this" evaporate
at the end of a response:
```
python findings_log.py spawn-job F-0012 --kind test --title "..." --briefing "..."
```

**5. A rough edge in a skill itself gets suggested, not silently fixed or silently dropped.**
Noticing a tool's own flag is confusing, a check is missing, or two steps should be one — while doing
*other* work — is common. Don't derail to fix it (scope creep on whatever you were actually doing) and
don't just mention it and lose it:
```
python skill_manager.py suggest --skill NAME --text "..." --source "job:J-0001"
```
Open suggestions show up in `docs/skill_index.md`'s own Suggestions section; review and resolve them
(`skill_manager.py resolve S-0003 --status applied|declined --why "..."`) periodically, the same way
`/decide-review` clears the decision backlog in one sitting.

## Every LLM prompt is registered — adding, removing or renaming one means updating the registry

Added 2026-10-31 (founder ruling, T-0115). `docs/prompt_registry.jsonl` is the single list of every prompt Du
sends to a model: 112 rows covering 118 prompt sites, found by `scripts/prompt_site_census.py` (AST: calls through
`core.model_client`, the `call_json` parameter convention, raw posts to `/api/chat`, `judge_panel.rule` /
`rule_detail` callers, and every `NodeBase` subclass). Before it existed the previous census saw 38 sites and
four of the six most-fired prompts were invisible.

**The rule:** a change that adds, removes, renames or moves a prompt site registers it in the same change, and
before the session ends this must exit 0:
```
python C:\Users\USER\.claude\skills\prompt-registry\prompt_registry.py check
```
Red output names each problem (NEW, STALE, DUP, SEEDS) with the command that fixes it. Adding a part to the idle
thought's seed assembly (`seed_parts.append` in `nodes/inner_monologue_node.py`) changes a counted guard and shows
up as SEEDS. Do not hand-edit `docs/prompt_registry.jsonl`; use the tool (`add`, `set`, `retire`). When you
materially change a registered prompt, `set P-NNNN --investigation stale --note "..."` so its old verdict is not
read as current. `/plan-maintain` runs the same check.

Statuses mean what the code does, not what the name says: LIVE, SHADOW (log only), LIVE-PROVISIONAL, DORMANT,
DEAD, WRITE-ONLY, UNCLASSIFIED. Several instruments named "shadow" are live in effect; read where the output goes.
Full how-to, granularity rules, and the per-prompt investigation protocol: `docs/guidelines/prompt_registry.md`.
The first inventory of what each prompt says and how often it fires: `docs/reviews/du_prompt_inventory_2026-10-31.md`.

## `_think` and `_run_cycle_impl` are frozen: new behaviour goes in a helper, not a new block

Added 2026-11-20 (founder ruling D-0878, plan `docs/staged/god_function_split.md`, F-5125 / F-5127).
`InnerMonologueNode._think` (3,598 lines) and `Orchestrator._run_cycle_impl` (1,525 lines) were growing about 6%
every two weeks. Nine past defects in `_think` came from its layout and every one was silent: a line added where it
could not reach the prompt, a call that ran once per retry, two distant blocks doing the same job.

**The rule:** a new idle-thought seed part, post-thought step or cycle stage is written as a function in its own
module (`nodes/idle_thought/` for the idle thought; name it `seed_part_<topic>`, `after_thought_<topic>` or
`attempt_<topic>`, never a bare `build` or `check`), with its own try/except and its own local imports, and is called
from the big function by one line at the place it belongs. It is not written as a new block inside the function.
Existing blocks stay where they are: moving them is the parked split (D-0877), not something to do in passing.

Before the session ends this must exit 0:
```
python scripts/function_size_ratchet.py check
```
GREW names the function and by how much. If the growth has to stay (the one-line call to a new helper, a fix inside
an existing block), record it with `accept --why "J-NNNN: what grew and why it could not live outside"`. The reason
is kept in `docs/function_size_baseline.json`; do not hand-edit that file. If a function shrank, run `accept` too, so
the lower size becomes the baseline. `/plan-maintain` runs the same check (step 7e).

## Before editing a file with real architectural weight: check blast radius with UDMS

Added 2026-08-27. **UDMS** (`C:\UDMS`, a separate sibling project — structural+temporal
dependency analysis over the actual AST and git history, not a planning tool) is wired in here as
an MCP server (`.mcp.json` at this repo's root, server name `udms`). On first use in any session,
Claude Code will show a one-time trust prompt for it — approve it (or run `/mcp` to approve later
if missed).

**When you're about to edit a file that isn't obviously leaf-level/isolated** — a cognitive node
(`CriticNode`, `ExecutiveNode`, etc.), anything in a shared registry/engine/store module, anything
you'd guess several other files import or co-change with — call the `udms_get_change_dossier` MCP
tool with `target_spec` set to that file's repo-relative path (e.g.
`"core/somatic.py"` or `"core/somatic.py:120-180"` for a specific range) *before*
making the change. It returns real static-AST dependencies, shared-state read/write overlap, and
git co-change history for that file — the kind of "who else touches this" question that's easy to
get wrong from memory alone on a 500+ file codebase. `udms_classify_regime` and `udms_doc_audit`
are also available for a whole-repo read; `udms_query_pmi` checks two specific files' co-change
history directly.

**UPDATE 2026-08-30:** the MCP tool set changed. `udms_get_impact_radius` was dropped (it returned
only a strict subset of what `udms_get_change_dossier` already includes — no reason to reach for it
separately). One new tool was added, wrapping capability that previously existed only in
UDMS's CLI. (A second, `udms_similar_history`, was added then DROPPED from the MCP manifest 2026-11-14,
D-0735 ruling a / F-4185: its unbanded DTW over commit-activity vectors was shift-invariant and showed no signal
beyond same-commit PMI; the research module and CLI `similar-history` remain, but do not look for the MCP tool.)
The kept tool is `udms_hygiene`
(no required args) finds dead functions, orphan classes, and structural outliers across the whole
repo's Python and Delphi/Pascal source — worth a call before assuming a file is safe to leave alone,
not just before editing one. Also fixed the same session: a real cold-start latency tail (fresh MCP
server processes were blocking up to 60s on their first call) is now resolved by a topology cache —
the first `udms_get_change_dossier` call in a new session should be fast again unless something in
this repo actually changed since the last one.

**Session warm-up (D-0686, J-3571, 2026-11-13):** the FIRST tool call of any session that will edit `core/` or `nodes/` is one `udms_get_change_dossier` call on the file it is about to touch (or a cheap `udms_query_pmi` if no file is known yet). Reason: from Claude Code 2.1.299 the harness closes a not-yet-used MCP server's stdin at the end of a turn, and every subagent spawned afterward lacks the `mcp__udms__*` tools; one early call keeps the server alive for later subagents (F-4175, `C:/UDMS/docs/audits/dossier_usage_stop_2026-11-06.md`).

**Read the dossier's evidence layer, don't just read pass/fail:**
- `STATE` and `CONTRACT` layer hits are real, 100%-certain evidence (an actual import, inheritance
  edge, or shared read/write state key) — always worth checking, not just a suggestion.
- `TEMPORAL` and `STATIC` layer hits are probabilistic (git co-change PMI, or a weaker fallback
  signal) — worth a look, but genuinely uncertain, not a guarantee.

**Ranked-ordering trust level (rewritten 2026-11-16, J-3471, from the Nascence-native measurement).**
Read the dossier in two parts. STATE/CONTRACT hits are exact and are acted on as before. The ranked
`investigation_targets` list is a **reading prompt, not an edit prediction**. It was measured on Nascence itself:
397 logged dossier calls joined to the Claude Code transcripts (F-4077 first pass, then the pre-registered
rerun J-3453 / F-4398 / F-4399 / F-4400, audit `C:\UDMS\docs\audits\dossier_followthrough_prereg_2026-11-07.md`).
Result, pooled (the main-thread group was too small to score): the served list beats a shuffled-list null on reads
(6.5% vs 2.9% precision, z +10.6) and on edits (4.3% vs 2.4%, z +5.9), but the effect is small in absolute terms,
comes mostly from reviewer workflows and fixer reads, and fixer edits show nothing (F-4400). F-4077's first-pass
"no better than another call's list" reading was largely an own-file artefact (F-4399), and removing the hubs does
**not** help (z falls), so do not discount a list for its hubs. Six hub files fill 26.8% of all target slots
(`core/orchestrator.py`, `nodes/inner_monologue_node.py`, `core/schema.py`, `core/sensorium.py`,
`docs/roadmap.md`, `core/memory/store.py`); expect them in nearly every list, and they are weak evidence about
*this* change. Nascence's own git history is still young, so the TEMPORAL channel is thin; the dossier runs mostly on
static/state evidence. The earlier Delphi result (ranker beat the commit-count baseline on 4 of 5 Delphi repos,
`ranker_vs_churn_baseline_finding_2026-08-27.md`) is history only, not evidence about Nascence. A re-score with
more editing-session calls is queued (J-3781). **Usage-log trap:** `C:\UDMS\data\mcp_usage_log.jsonl` `ts` is NZ
local time, 12-13 h behind UTC; convert before joining it to transcripts or git. Treat the dossier as one more input
that catches things memory alone would miss, not a substitute for reading the file and its obvious callers.

**Nascence-specific scoping (`.udms.json` at this repo's root, added 2026-08-29):** UDMS reads a
per-repo config declaring which directories are NOT code/documentation — here it excludes `data/`
(Du's own writings are Du's mind, not docs about the codebase), `.claude/`, `scratch/`,
`graphify-out/`, `public_repo/`, `docs_site/` from the relevant scans. Measured effect: engine
init 39.5s → 11.5s, and `doc-audit` went from chewing 2,400+ of Du's essays to auditing the ~330
REAL docs — where it immediately found a genuine contradicted claim (a lab report asserting
independence between `core/self_interrogation.py` and `nodes/inner_monologue_node.py` where a
real AST dependency exists) and a large stale-reference population in plan docs. `doc-audit` is
now effectively an automated cousin of `/plan-files-audit` — worth running when plan docs feel
stale. Edit `.udms.json` if directory meanings change; keys: `doc_exclude_dirs`,
`code_exclude_dirs` (directory names, matched against any path component, case-insensitive).

**Also available beyond the MCP tools** (run from `C:\UDMS`): `python udms.py battery C:\Nascence`
(the full diagnostic raft with a per-repo verdict), `python udms.py hygiene C:\Nascence` (dead
functions/orphan classes — currently surfaces ~58 confirmed-unreferenced functions in core/, LEADS
to verify against live wiring, not verdicts: this project's own write-only-systems history says
check before deleting), and `python udms.py calibrate C:\Nascence` (opt-in weight fitting — will
honestly refuse on this repo until the commit history is much deeper). Dossiers on `.py` targets
now also include per-function structural motif tags (FaultBarrier, StateAccumulator, etc.).

**Two practical things to know:**
- The first real tool call in a fresh session takes ~12s cold (post-scoping; was 30-70s) — it's
  pre-warmed in a background thread as soon as the MCP server process starts, so in practice it's
  usually already done by the time you actually call it.
- That scan snapshot is taken **once per Claude Code session** (whenever the `udms` MCP server
  process starts) — if you make many commits mid-session, the dossier keeps analyzing the
  session-start state until the session restarts. For a long session with heavy commit activity,
  a fresh session picks up the latest history.
- Every real tool call is now logged to `C:\UDMS\data\mcp_usage_log.jsonl` (arguments, latency,
  status, full result-or-error) — added 2026-08-27 specifically so real usage against this repo
  can surface UDMS bugs/upgrade candidates. You don't need to do anything with this file; it's for
  UDMS's own maintenance, not part of this project's toolchain. If a UDMS tool call ever seems
  wrong, slow, or crashes, it's worth mentioning back so the log can be checked.

## Which tool for which fact

| You have... | Use |
|---|---|
| A raw musing, not even framed as a question yet | `/thought-log add` |
| An idea that isn't a plan yet | `/idea-log add` |
| A plan actively being drafted | `docs/staged/<slug>.md` (not a new bucket) |
| A question only the founder can rule on | `/decide open` — or, if it surfaced mid-exploration of an idea/thought rather than a scoped plan question, `job_queue.py add --autonomy needs_input` |
| An investigation result | `/findings-log record` |
| Confirmed follow-up work | `/job-queue add`/`spawn`, or `findings_log.py spawn-job` |
| A big batch of open jobs to work through at once | `/job-run` (tiers + dispatches agents, vs. `job-queue next`'s one-at-a-time) |
| A rough edge in a skill/tool | `/skill-manager suggest` |
| "What's ready to work on right now" | `/job-queue next` (one job) or `/job-run` (a batch) |
| "What's waiting on the founder" | `/decide list --open` (or `/decide-review` for a batch pass) — also check `job_queue.py list --needs-input` |
| "What plans exist / are stale" | `/plan-index` |
| "Catch me up on other sessions" | `/session-resume` |
| A new, renamed or removed LLM prompt, or "where is the prompt that does X" | `prompt_registry.py check` / `add` / `list` / `show` (skill `prompt-registry`; rule above) |
| "I'm done for now" | `/session-wrap` |
| "What skills exist at all" | `/skill-manager list` or `docs/skill_index.md` |

## Conventions this toolchain enforces — work with them, not around them

- **No ruling without a defeater** (`/decide rule`) — a ruling with no named revisit condition is
  refused outright, the rule that stops "PARKED until X" silently outliving X.
- **No "verified" without evidence** (`/findings-log record`) — see rule 4 above.
- **Never hand-edit a `.jsonl` store directly.** Every store here (`job_queue.jsonl`,
  `decisions.jsonl`, `ideas.jsonl`, `findings.jsonl`, `session_events.jsonl`, `skill_suggestions.jsonl`,
  `_memory_edges.jsonl`, `plan_snapshots.jsonl`) is written by its owning tool for a reason — atomic
  writes, edge-graph sync, live event logging all happen there. A hand edit skips all of it silently.
- **A ruling made by Claude is never recorded as the founder's.** `/decide rule --by` is required with
  no default, specifically because a defaulted `--by travis` used to silently misattribute rulings.

## Never launch Du's servers from a Claude Code tool without escaping the job object

Added 2026-09-03 (F-0704). The Claude Code desktop app runs its **PowerShell tool inside a Windows
Job object with breakaway disabled**. Anything started from it — `launch_servers.ps1`,
`supervisor.py`, a hub via `Popen(..., DETACHED_PROCESS)`, even a grandchild whose parent already
exited — stays in that job and is **killed when the Claude app restarts** (its own auto-update did
exactly this at 09:18 on 2026-09-03: Judge1/Judge2/Dreamer hubs and the D-0127 watchdog all died at
once; Du, started from the standalone Control Panel, survived and fail-opened on the dark tier all
morning). The Bash tool is *not* in a job today, but don't rely on that.

If a session needs to bring the local tier up, run
```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_supervisor_detached.ps1
```
It starts `scripts/supervisor.py` through WMI (`Win32_Process.Create`, a child of WmiPrvSE — in no
caller job), and since D-0127 the supervisor ensures + watches all four local servers (hot :11433,
judge1 :11439, judge2 :11440, dreamer :11442). Verify with `netstat -ano | findstr 1143` and
`data\supervisor.log`. Otherwise ask the founder to use the Control Panel ([1] or [2]) — it is a
standalone window, not job-confined.

**Caveat added 2026-09-24 (J-1295, F-1821):** in at least one automated/sandboxed job-run session's own
execution environment, the exact `cmd.exe /c ... && python ... >> log 2>&1` wrapper this script's own
`$cmd` line above uses via WMI `Win32_Process.Create` reported success (`ReturnValue=0`, a real PID) but
the wrapped `python.exe` child never actually started — no process, no output, ever. Verified step by
step, isolating each layer: WMI→cmd.exe→echo (a cmd builtin) worked; WMI→python.exe direct worked;
WMI→cmd.exe→python.exe (a real child process) failed silently every time tested. A WMI-launched
`powershell.exe` wrapper instead (PowerShell's own `& python.exe args *>> log`, no cmd.exe involved) was
verified to work reliably in that same session, including named parameters and an inherited environment
variable — see `scripts/dream_exp_a_target_launcher.ps1` / `scripts/dream_exp_a_watchdog_launcher.ps1`
for verified working examples of that pattern. **NOT established** whether this is specific to that
automated/sandboxed session or would also affect the founder's own interactive desktop session — the
cmd.exe pattern above has apparently worked for every real relaunch in this job chain since J-1119 and
presumably for this real script too, or F-0704's own account would have surfaced a failure. Because of
that, `start_supervisor_detached.ps1`'s own launch mechanism is **deliberately left unchanged** here —
swapping it for the powershell.exe pattern needs a real confirming test from an interactive session
first (this note is documentation/caveat only, not a production change). If this script, or anything
else using this same WMI+cmd.exe pattern, ever appears to succeed (`ReturnValue=0`) but the process it
should have started never actually comes up, this silent-failure mode is the first thing to suspect —
try a powershell.exe wrapper instead before assuming a different cause. Full evidence: F-1821, job
J-1267 (`docs/staged/dream_overhaul.md`'s 2026-09-23 J-1267 note).

**Update 2026-09-24 (J-1300, F-1893): the "NOT established" question above is now answered — this is
a GENERAL Windows/WMI issue, not specific to an automated/sandboxed job-run session.** Reproduced from
a genuinely interactive session (directly driven turn-by-turn, not a Workflow-dispatched background
subagent — the exact distinction the note above left open) using the identical isolation steps: the
`cmd.exe /c python.exe ... >> log 2>&1` pattern failed silently 2 of 2 times, identically to the
automated-session read. This script's own launch mechanism is therefore a real, live risk, not just a
job-run curiosity — **still deliberately left unchanged here**: D-0277 opened for the founder's own
call on whether/when to swap it for the already-verified powershell.exe-wrapper pattern.

**Update 2026-09-24 (J-1341, F-1894): the fix has now shipped.** D-0277 (travis) ruled build-and-verify;
`start_supervisor_detached.ps1`'s own `$cmd` line now launches a new `scripts/start_supervisor_launcher.ps1`
via a WMI-launched `powershell.exe` wrapper (no `cmd.exe` involved) instead of the `cmd.exe`-wrapper shape
described above. Verified end-to-end via 4 real WMI `Win32_Process.Create` launches across two passes (a
scratchpad prototype, then the real committed file), against a disposable target script only, never the
real `supervisor.py` — reliable child start every time, separate append-mode stdout/stderr files
preserved, no stray processes. A further real difference from `dream_exp_a_target_launcher.ps1`'s own
pattern was found and fixed during this verification: PowerShell's native `2>>` redirection on a real
external command wraps every stderr line as a formatted `ErrorRecord` instead of passing it through raw
the way `cmd.exe`'s own `2>>` did — the shipped launcher uses `System.Diagnostics.Process` directly with
async output-event handlers instead, avoiding that silent format change (and a related synchronous-read
deadlock risk). D-0277's own defeater (a new failure mode the cmd.exe pattern didn't have) was checked
for and not found in the final, shipped mechanism. Full evidence: F-1894, job J-1341
(`docs/staged/dream_overhaul.md`'s 2026-09-24 J-1341 note).

## Never run `git stash` / `git reset` / `git checkout --` / `git restore` in the shared C:\Nascence tree

Added 2026-09-03 (J-0527, F-0741; the same mechanism explains F-0723 and the "unexplained git
reset" of 2026-08-29, commit 3470b4d). **Several Claude Code sessions and job-run agents work in
the SAME working tree at once**, and none of this repo's toolchain skills ever runs a git
mutation — every incident so far was one agent's ad-hoc `git stash && python <smoke test>; git
stash pop` to check whether a failure pre-existed its edit. `git stash` captures EVERY other
session's uncommitted edits (2026-09-03 12:37: 26 files, including J-0500's judge_panel.py work
and 8 other agents' ledger writes); the pop then conflicts on whatever they wrote in between, the
agent "resolves" by `git checkout stash@{0} -- <paths>` (which also STAGES those paths), and the
other sessions see their files silently at HEAD with no error anywhere. `git stash`, `git reset`,
`git checkout -- <path>`, `git checkout <tree-ish> -- <path>`, `git restore`, `git clean` all
leave no reflog trail a later reader can attribute; only `git fsck --unreachable` ever showed the
WIP commits.

If you need to know whether a failure pre-exists your edit, **never touch the shared tree** —
check out HEAD into a throwaway worktree in your scratchpad and run the test there:
```
git worktree add -q <scratchpad>\wt_head HEAD
cd <scratchpad>\wt_head && python scripts\life_smoke.py
cd C:\Nascence && git worktree remove --force <scratchpad>\wt_head
```
(`git diff`/`git status`/`git stash list`/`git show` are read-only and fine.) A commit of your own
files, explicitly staged by path, is the only legitimate way to change what the shared tree holds.

## Pointers

- `docs/skill_index.md` — what tools exist, when to reach for each (regenerate: `skill_manager.py scan`).
- `docs/job_queue.jsonl` / `job_queue.py next` — what to work on right now.
- `docs/decisions.jsonl` / `decide.py list --open` — what's blocked on a founder call.
- `docs/session_events.jsonl` — the live timestamped log everything above writes to.
- `~/.claude/skills/` — every tool this file refers to lives here, one directory per skill, each with
  its own `SKILL.md` carrying the full "when and why."
