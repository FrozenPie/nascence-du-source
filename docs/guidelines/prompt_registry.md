# The prompt registry: every LLM prompt in Du's loops, registered, found, and investigated

Created 2026-10-31 (T-0115, founder ask). Companion files:
- Registry (the list): `docs/prompt_registry.jsonl`. Written only by `~/.claude/skills/prompt-registry/prompt_registry.py`.
- Detector (what is actually in the code): `scripts/prompt_site_census.py`.
- First full inventory (what each prompt says, with real call counts): `docs/reviews/du_prompt_inventory_2026-10-31.md`.

## 1. The rule

**Any change that adds, removes, renames or moves an LLM prompt must register it in the same change.**
That means: a new call through the model client (`call_node`, `call_node_json`, any `call_json` parameter
call), a new raw post to `/api/chat`, a new `judge_panel.rule` / `rule_detail` caller, or a new `NodeBase`
subclass. It also means a new part in the idle thought's seed assembly (`seed_parts.append` in
`nodes/inner_monologue_node.py`), which changes a counter the check watches.

Before the session ends, from `C:\Nascence`:

    python C:\Users\USER\.claude\skills\prompt-registry\prompt_registry.py check

must print `OK` and exit 0. If it prints NEW, STALE, DUP or SEEDS lines, each line carries the exact command
that fixes it. Do not leave it red. `/plan-maintain` runs the same check, so a red registry shows up in the
next maintenance report as well.

A prompt that is not in the registry cannot be investigated, compared with its neighbours, or noticed when it
breaks. That is the whole reason for the rule: on 2026-10-31 the first complete census found 118 prompt sites
where the previous census had found 38, and four of the six most-fired prompts had been invisible.

## 2. How to register

New prompt (the `check` output prints this line for you, filled in):

    python C:\Users\USER\.claude\skills\prompt-registry\prompt_registry.py add --name "what it is for" \
        --family idle_satellite --keys "core.some_module:some_function" --kind call --status SHADOW \
        --lane "hot :11433 qwen3.5:9b" --inventory "why it exists, who calls it" --session <this session's id>

- `--keys` are census keys: `module:Qual.function`, plus `#<system-arg text>` when one function holds more than
  one prompt. Get the exact keys from `prompt_registry.py census`. Several keys in one row are separated by `;;`.
- `--status`: `LIVE` (its output reaches Du's prompts, memory or behaviour), `SHADOW` (log only), `LIVE-PROVISIONAL`,
  `DORMANT` (wired but never fires), `DEAD` (no caller), `WRITE-ONLY` (output is stored and nothing reads it),
  `UNCLASSIFIED` (not yet known; the investigation settles it). A name containing "shadow" proves nothing about
  effect: several "shadow" instruments are live in effect. Read where the output goes.
- Then file the investigation job for it (section 4) and put its id on the row with `set --job`.

Prompt renamed or moved: `check` reports STALE for the old key and NEW for the new one. Fix with
`set P-NNNN --keys "<new key>"`; do not add a second row.

Prompt deleted: `retire P-NNNN --why "..."`. The row is kept, so its history stays findable.

**Granularity.** One row is one designed prompt-job. Stages of one pipeline are one row with several keys (the
three-stage self-revision chain keys are three rows because each stage is its own prompt; the follow-line
judges are one row because they are one chain). When in doubt, one row per distinct system prompt.

**Not detected, so register by hand with a fragment row (`--kind fragment`, no keys):** prompt text that has no
call of its own, such as a block of the idle thought's seed or a block of a system prompt.

**Detector blind spots (add the wrapper's name to `scripts/prompt_site_census.py` when you introduce one):** a
prompt reached through a wrapper function the detector does not know by name; a raw post whose URL is built on
an earlier line; anything outside `nodes/`, `core/` and `scripts/run_nascence.py`.

## 3. When a registered prompt changes

Change its text or its inputs materially and the old investigation verdict no longer describes it. Run
`prompt_registry.py set P-NNNN --investigation stale --note "what changed, job/finding id"` and, if a fix job
caused the change, leave the verdict and the finding id on the row so the history reads straight.

## 4. The investigation protocol (what every `Investigate prompt P-NNNN` job does)

Read-only. Do not edit the prompt in an investigation job. The product is evidence, a verdict, and fix jobs.

**Inputs.** The registry row (`prompt_registry.py show P-NNNN`), its inventory entry in
`docs/reviews/du_prompt_inventory_2026-10-31.md` (search the heading text the row's `inventory` field names),
and the live source. The inventory was written by reader agents and is a lead, not a proof: every line the
reader marked `[INFERRED]`, and every claim you rely on, must be re-checked against the current source with a
quoted line.

**Evidence of real behaviour.** Do not judge a prompt from its text alone. Find what it actually produced:
- Conversation nodes: `data/training/<node>.jsonl` holds the real `system_prompt`, `user_prompt` and `output`.
- Idle thought and seeds: `data/prompt_budget_shadow.jsonl` (which parts fired), `data/monologue_log.jsonl`.
- Idle thought, WHOLE rendered prompt (J-2933 / J-2941, restart-gated): `data/idle_prompt_samples.jsonl` - one row per ~20 idle assemblies plus a watch row (at most one per 30 min per kind) when a `Right now:`, `Travis is here`, cat-felt, thermal, light, smell or listening line fired. A row holds `parts` (full text), `wrapper_head` + `wrapper_tail` (so head + parts joined by newline + tail IS the sent string), `system_prompt_sha1`, `labels`, `trigger`. Read it with `core.prompt_budget.samples_status()`; the file is capped at 500 rows. Real rows to quote (read 2026-11-14, J-3762; match by `ts` to the `llm_calls.jsonl` row from `nodes.inner_monologue_node:4272`, whose `pc` equals the row's `user_prompt_chars`): `Right now:` ts 1794568677.1 (`Right now: Travis has stepped out; the door eases shut behind him.`); `Travis is here` ts 1794088330.6; listening ts 1794273118.8 (`faint hush along the strand`); smell ts 1794572172.8 (`A dark, mineral, green smell off the ground, on the air.`, user_prompt_chars 2256); light ts 1794505183.6 (`The light is coming up out here.`); thermal ts 1794572366.0 (`Warmth reaches you here.`, user_prompt_chars 4553). Rows are matched by trigger, so re-find them with `[r for r in rows if 'smell' in r['trigger']]` (trigger is a list).
- Every station: `data/llm_latency.jsonl` and `data/thought_station_log.jsonl` (when and how often it fired,
  by `module:line(Class)` label; labels drift with edits, so join by function), `data/llm_json_parse_fail.jsonl`
  (parse failures), `data/llm_calls.jsonl` (prompt and window sizes, about one day kept).
- Judges: `data/judge_panel_log.jsonl`. Find a station's own log with `grep -n "jsonl" <its module>`.
- Read at least ten real outputs where any are logged. If none are logged, say so: that is itself a finding
  (an instrument is missing).

**Questions to answer, each with evidence (a quoted line, a count, a sampled output):**
1. *Purpose and necessity.* What job does it do, in one sentence? Is the job still wanted?
2. *Reach.* Where does the output go, and does anything read it? Write-only (stored, never read) is this
   project's most frequent failure: grep for the readers.
3. *Inputs.* List every part of the user prompt with its cap. Flag fossil truncations, mid-word cuts, uncapped
   feeds, a part that arrives twice, raw numbers or raw ids leaking into the text, lines present in nearly
   every call that carry no information, and verdict lines pegged by a stuck instrument.
4. *Instruction quality.* Contradictory rules, stale or engineering text inside the prompt (change-log
   fragments, ticket ids), negation that plants the frame it denies, internal-cycle framing that still says a
   person spoke, examples the model copies.
5. *Lane and budget.* Is the model, window and `max_tokens` right for the job? Is the temperature of the right
   class (0.0 pick, 0.1 to 0.2 judge, 0.4 to 0.6 synthesise, 0.7 and up generate)? Is `think` handled? Does the
   prompt ever hit the cap (window instruments)?
6. *Measured health.* Valid-output rate, parse failures, latency, empty or degenerate outputs, repetition across
   same-day outputs.
7. *Drift.* Docstrings and comments that now lie about the lane, flag or behaviour.
8. *Founder laws.* The world answers and never leads: no hint to Du, ever. No system that acts later on its own.
   Every subsystem is judged by something other than itself (a judge from a different model family). Transfer
   the function, not the mechanism. Base systems are protected and changes are additive.
   Sanctioned exception, the Travis branch (D-0583, 2026-11-02): the drill method hint and worked example
   (`method_hint` in `core/math_drill.py` and `core/music_drill.py`, row P-0024) is teaching authored by Travis
   on 2026-06-22, which the law allows alongside diegetic books. It must stay authored by Travis or a text he has
   approved, never generated by a model; any new hint is added through Travis.

**Outputs, all through the tools (never hand-edit a ledger):**
- One finding per defect or notable fact: `findings_log.py record ... --confidence verified|inferred|guessing`.
  `verified` needs quoted evidence.
- One fix job per confirmed defect: `findings_log.py spawn-job F-NNNN --kind build ...`. Name the hub files in
  the brief and say to run `udms_get_change_dossier` first.
- A founder question goes in as a `needs_input` job, not in chat.
- Close the loop on the registry row:
  `prompt_registry.py set P-NNNN --investigation done --verdict keep|fix|merge|retire|needs_founder --finding "F-NNNN,F-NNNN" --status <settled status> --session <id>`
  and `job_queue.py done J-NNNN --session <id>`.

A verdict of `keep` with no findings is a good outcome. The point of the sweep is to know, not to change.

## 5. Running an investigation job as an agent (the mechanics)

Added 2026-10-31 after the first six pilot jobs. The sweep's session id is `aa94f138-79e2-4f75-92fd-106b1898e0bd`; pass it as `--session` on every ledger call so the work rolls up to one handoff.

1. `python C:\Users\USER\.claude\skills\job-queue\job_queue.py start J-NNNN --session <id>`
2. `python C:\Users\USER\.claude\skills\job-queue\job_queue.py show J-NNNN` (the `briefing` field is the task), then section 4 above.
3. Investigate from the current source and the real logs. Quote evidence. Counts, sampled outputs, quoted lines.
4. Close out through the tools only, in this order: `findings_log.py record` (use `--claim-file` and `--evidence-file` with a temp file for anything with quotes or backticks; `--by claude`; `verified` only with quoted evidence), `findings_log.py spawn-job F-NNNN --kind build|test|lab_experiment|analysis ...` for each confirmed defect, `prompt_registry.py set P-NNNN --investigation done --verdict ... --status ... --finding "F-NNNN,F-NNNN" --session <id>`, then `job_queue.py done J-NNNN --session <id>`.
5. A defect found in a prompt that another row owns: record the finding and note the other row's id in the claim; do not close the other row.

Hard rules:
- Read-only on everything under `C:\Nascence` except through the ledger tools. Never edit code, prompts or data files. Never hand-edit a `.jsonl` ledger. Never run `git stash`, `reset`, `checkout`, `restore` or `clean` in the shared tree. Du is running live.
- Scratch files go in the session scratchpad (`C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-AEHCil\aa94f138-79e2-4f75-92fd-106b1898e0bd\scratchpad\<row id>`). On Windows, Python `print()` of non-ASCII needs `sys.stdout.reconfigure(encoding="utf-8")`, and a heredoc Python string holding a Windows path with `\N` or `\U` fails, so use forward slashes in code strings.
- Data logs run 40 to 60 MB: stream them or read the tail. Never load one whole.
- Verify before asserting; grade confidence verified / inferred / guessing. The inventory is a lead, not proof: the pilot refuted one of its claims (Perception's `subject` is read, at `core/orchestrator.py:2355`).
- A judge verdict base rate, a missing control arm, and whether anything reads the output are the three checks that found the most in the pilots.
- Founder laws bound any recommendation: the world answers and never leads (no hint to Du, ever); no system that acts later on its own; every subsystem is judged by something other than itself; transfer the function not the mechanism; base systems are additive-only.
- Keep the final reply under 200 words: verdict, settled status, finding and job ids, the three or four most important facts with evidence, and what you could not resolve.

Lessons from the first 20 jobs (added 2026-11-01), all part of section 5:
- **Search the ledger before recording.** About 70 findings already exist from the sweep. Run `python C:\Users\USER\.claude\skills\findings-log\findings_log.py list` and search for your prompt id or function name. Extend or correct an existing finding in a new one that cites its id; do not file a duplicate.
- **Ids are authoritative from the tool only.** The ledger was wiped and restored on 2026-11-01 (finding F-3537; map in `docs/reviews/findings_wipe_2026-10-31.md`). Findings F-3466 to F-3536 are the earlier sweep findings under their restored numbers. Never cite an id from memory or from an old report: read it with `findings_log.py show F-NNNN`. Old committed findings (F-0001 to F-3423) are real and keep their numbers.
- **A conditional follow-up is `needs_input`, not `ready`.** If a fix only makes sense when a founder question goes one way, spawn it with `--autonomy needs_input`, or a batch runner will pick it up first.
- **Check the inventory against the code.** The pilot refuted one inventory claim and corrected several caps. Quote the current line.
- **Count what a prompt costs.** Calls a week, median latency, and which lane it competes for. The hot lane is one GPU shared by every conversation node and the idle thought.
- **When one finding changes another prompt's row,** note the other row's id in the claim and leave that row's job to its own investigator.

## 6. Measurement-only judges (added 2026-11-05, J-3193, D-0580)

Some registered judges write a verdict that nothing acts on. That is allowed when the founder has ruled it so, but it
must be said in the code and the docs, and nothing may be wired to the verdict while it is in that state.

- **P-0107, the dream resolution judge** (`nodes/dream_node.py` `_judge_resolution_shadow`, panel verdict on whether
  an arc resolved). Its verdict sets `close_reason` (`resolved` or `ended-unfaced`). Readers: the du_pulse display line
  (`scripts/du_pulse.py`) and the night ledger (`core/night.py`). The carry, `core/dream_met.py` and the closure writer
  do not use the value. Founder ruling D-0580 (2026-11-02): keep as a measurement only, wire nothing to it while the
  wording of the dream prompt and the judge prompt disagree, and re-ask once the resting-ending change (D-0565, J-3177)
  has landed. Evidence: F-3709, F-3719, F-3727.
