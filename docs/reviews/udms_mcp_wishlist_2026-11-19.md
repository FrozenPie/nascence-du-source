# UDMS from the Nascence side: tool improvements and a wish list

Written 2026-11-19 by the Nascence window (session 8ef072cf, T-0153), for the UDMS window and the founder. It answers two questions: how the MCP tools could be better, and what I wish UDMS could tell me while working on Du.

**Basis.** Part 1 comes from using the tools today on `nodes/inner_monologue_node.py` and `core/orchestrator.py` (F-5125, F-5126), plus the UDMS handoff `C:\UDMS\docs\handoffs\udms_for_god_function_split_2026-11-19.md`. Part 2 comes from the questions Nascence sessions keep answering by hand. I have not read UDMS's source, so some of this may already exist or be harder than it looks; treat each item as a request to check, not a spec.

## The short version

If only five things were done, I would pick these, in order:

1. The dossier states its own history window and how stale it is for the target (1.1).
2. A compact dossier that says each thing once (1.2).
3. A block-level extraction report for one function (2.1).
4. A writer/reader map for state and data files, to catch write-only systems (2.2).
5. A collision warning from the usage log UDMS already keeps (2.6).

## Part 1. Improving the tools that exist

### 1.1 The dossier should say how old its evidence is

Today's dossier on `inner_monologue_node.py` printed "Confidence: 94.1%" and PMI figures with no date on them. Only the UDMS handoff told me the history window is the oldest 450 of 3,620 commits, holding 34 of this file's 207 commits and none of the 97 from the last 30 days. Every dossier should print one line such as: "History window: 2026-08-27 to 2026-09-10 (450 of 3,620 commits). Target: 34 commits in window, 207 all-time, last in-window commit 2026-09-10." That turns a silent weakness into something the reader can weigh.

### 1.2 Say each thing once

The result carries the same 23 targets twice, once in `dossier_text` and once in `investigation_targets`, and each row repeats a boilerplate "Impact" sentence. One call cost about 5,000 tokens, and a tool result is re-read on every later turn. A default compact form (one line per target: path, layer, direction, PMI) with a `verbose` flag would cut that by most of its size.

### 1.3 The headline should match the body

The archetype read HIDDEN_HISTORICAL_DEPENDENCY, yet all 20 code targets were static CONTRACT hits and there was no temporal layer at all. Rows with PMI 0.00 and lift 0.0 were labelled "ESTABLISHED_CORE (Base-rate controlled, n >= 30)", which reads as strong evidence when it means "never co-changed in the window". Zero co-change should say "no co-change in window". The 94.1% needs a statement of what it is a probability of, or it should go.

### 1.4 Direction and symbols

"Explicit dependency in static AST" does not say which way the edge points. For a refactor these are different questions: files the target imports (what the moved code needs) and files that import the target (what breaks if a name moves). Each row should carry the direction, whether the import is module-level or function-scoped, and the names imported. The handoff's "25 importers at module level plus 5 inside functions" is exactly the figure I wanted, and it came from a side script, not the tool.

### 1.5 Make the line range mean something

`file:3013-6610` only chose which functions were listed; the dependency list was the whole file's. With a range, the dossier could report the imports and calls that occur inside that range. For a 7,233-line file that is the difference between a file-level answer and a useful one.

### 1.6 Recommend tests that exist

"Run targeted unit tests: pytest tests/ -k 'nodes'" is wrong for Nascence: there is no pytest config, and 567 test scripts live in `scripts/_test_*.py`. The step could list the scripts that actually import the target or name its functions, or say plainly that it found none.

### 1.7 Drop or qualify the motif labels

`_think` is tagged DynamicCodeSynthesizer because it calls getattr twice. A label that the handoff has to tell me to ignore should not be in the output.

### 1.8 Hygiene needs a filter and a baseline

The tripwire use (catch an extracted helper nothing calls) needs two things the tool lacks: a path filter ("only this file or directory") and a diff against a saved baseline ("new since last run"). Today I get the first six of 32 repo-wide dead functions, none of them in the file I am working on. The result also lists the same items under both `dead_functions` and `function_tiers.zero_reference`. Bare-name matching (F-4189) forces naming conventions on the caller; matching by module-qualified name would remove that.

### 1.9 A refresh, and a status call

The MCP scans once per session, so modules created mid-session are invisible and a long session reads an old snapshot. Static AST for one file is cheap, so per-file invalidation by mtime, or an explicit `udms_refresh`, would fix the common case. Alongside it, a near-free `udms_status` returning snapshot time, HEAD, history window, and whether UDMS itself is running uncommitted code. That would also serve as the warm-up call that CLAUDE.md now asks for, instead of spending a full dossier on it. The status should say whether the scan reads the working tree or HEAD, because several sessions leave uncommitted edits in this tree at once.

### 1.10 Smaller things

- Expose the function profiler as an MCP tool. It is the fastest and most exact thing I used today, and the CLI route fails inside `C:\Nascence` because both repos have a `core` package.
- Mark hub files in the list ("hub: in 27% of all lists") rather than leaving the reader to remember the six names from CLAUDE.md.
- Log `ts` in UTC ISO form. The NZ-local timestamps have already needed a warning in CLAUDE.md.
- `udms_classify_regime` gives a label that depends on the commit window (F-4186). Fix it or take it out of the manifest.
- `doc-audit` prints the first 10 of 3,875 stale references. Write the full list to a file and return the path, and allow a per-target query: "which docs cite this file's functions or line numbers".

## Part 2. What I wish UDMS could tell me

Ordered by how often the question comes up in Nascence work.

### 2.1 How a giant function comes apart

For one function: its top-level blocks, and for each block the locals it reads from earlier, the locals later code reads from it, the `self` attributes it reads and writes, any return/continue/break that would escape a helper, and whether it mutates a shared list. I built this by hand twice today and the first version was wrong: 115 of 123 blocks looked separable until `self` writes and control flow were counted, which left 74 (F-5126). A tool that had this right would turn the `_think` split from a judgement call into a work list.

### 2.2 Who writes it and who reads it

Nascence's most repeated failure is the write-only system: something is computed, stored and never read, or a method exists and is never called from the live path. I want, for every `self` attribute, state key and data file path in the code, the list of writers and the list of readers. Flags: written and never read; read and never written; read only by scripts. Data files matter most, because much of Du's state crosses modules as `data/*.jsonl` paths that no import edge shows. `.jsonl` is outside UDMS's co-change list today (F-4191), and that is where the hidden coupling lives.

### 2.3 Is it wired into the live loop

Hygiene's tiers stop at one hop. The question asked in nearly every investigation is transitive: starting from `scripts/run_nascence.py` and the orchestrator cycle, is this function reachable through real calls, counting function-scoped imports? And is the path gated by a flag that is currently off? A list of module-level flags (`LANE2_LIVE` and its many cousins) with the code each one gates would answer "is this shadow, live or dormant" from the code. The prompt registry currently records that by hand for 112 prompts.

### 2.4 What reaches the model

Du's behaviour is decided by what text lands in a prompt. A coarse data-flow answer would be valuable: which functions contribute to the strings passed to `call_json` and the model client, and for a changed range, which registered prompt sites (P-NNNN in `docs/prompt_registry.jsonl`) sit in or downstream of it. J-2678 and J-3952 were both bugs of this kind, where lines silently failed to reach the idle prompt.

### 2.5 Where failures go dark

`_think` has 444 try/except nodes. Nascence fails open by design, and the cost is that broken things stay silent, as in the 30-day outage. I want the except blocks that neither log nor re-raise, ranked by how much they wrap, per file. That is a short list of places where a fault would be invisible.

### 2.6 Is someone else in this file right now

Several sessions and job-run agents share one working tree. UDMS already logs every dossier call with its target and time. A line in the dossier such as "another session requested this file 20 minutes ago" plus "this file has uncommitted changes" is nearly free and would prevent real collisions. The handoff lists this as something UDMS does not do; it has the data to do it.

### 2.7 History joined to the ledgers

Commit messages and ledgers carry J-, F- and D- ids. Two uses. First, co-change grouped by job id, so files touched under one job across several commits count as coupled. Second, an incident history per file: the findings and jobs that name it. I found the two `_think` bugs by regex over `job_queue.jsonl`; that should be one query.

### 2.8 Which functions are growing

Size and complexity per function over git history, with the fastest growers listed. I learned that `_think` grew 198 lines in 13 days only because F-4191 happened to record the earlier number. A standing trend would show the next god function while it is still 600 lines.

### 2.9 What is waiting on a restart

Much of Nascence's work is "built, live on next restart". Given Du's last boot time (from `data/nascence.log`) and the reachability in 2.3, UDMS could list the files changed since boot that the live process loads. That is the real pending-restart set, which today is reconstructed from handoffs.

### 2.10 Which tests cover this

For a file or function, the `scripts/_test_*.py` files that exercise it, and the functions with no test at all. This also feeds 1.6.

### 2.11 Where the same code is written twice

Clone detection across the world modules. `garden.py`, `fieldcraft.py`, `shore_life.py` and `study_life.py` each have their own `act_from_thought`, and the big files share many small helper shapes. Knowing which blocks are near-copies says where a shared module is warranted and where a split would only move code about.

## What I would not ask for

- A ranked edit prediction. The measured effect is small (F-4398 to F-4400), and the exact STATE and CONTRACT layers are where the value is. More exact layers beat a better ranker.
- Risk scores and archetypes. A named fact with its evidence is easier to act on than a tier.
- Anything that writes into `C:\Nascence`. Read-only is the reason the tools are safe to call freely.
