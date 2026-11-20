# Splitting the god functions: `_think` first, `_run_cycle_impl` second (staged 2026-11-19, T-0153)

**Status:** 🔵 DESIGNED / STAGED. Nothing built, no production code changed. **Reworked 2026-11-20 on founder direction: the split itself is PARKED. The active track is freeze growth, build the equivalence harness as a standing test, and count structure-caused bugs (section 0).** One founder decision open (section 9).
**Origin:** T-0153 (founder side quest: should Du's large scripts be split into modules, as the pantry app is). Findings F-5125 (sizes, churn, past bugs) and F-5126 (UDMS baseline, corrected separability). Earlier structure read: F-4191 (2026-11-06), which spawned no jobs.
**Rules that bind every step here:** move-only (no behaviour change, no rewording, no reordering); the inner monologue is a protected base system, so every step carries proof that nothing changed; one step is one commit of this plan's own files, staged by path; no `git stash`/`reset`/`checkout --` in the shared tree; restart-gated.

```plan-state
stage: designed
phase: Reworked to freeze-first (2026-11-20). Split parked behind evidence. Bug-count read filed; harness and freeze rule wait on the open decision
verified: 2026-11-20
evidence_read: 2026-11-20
gate: The split (sections 3, 5, 6) reopens only on evidence: the bug-count read done AND the standing harness built and used on real edits (section 0.4). Not on a date
next: Build the equivalence harness (the ready job against this plan); first ratchet read at the next plan-maintain pass
cluster: 6
```

## Current State (2026-11-20)
- **2026-11-20**: D-0878 ruled go on both (founder, 2026-11-20). Freeze rule added to CLAUDE.md; scripts/function_size_ratchet.py built, tested on a throwaway tree, baseline recorded (_think 3,598, _run_cycle_impl 1,525) and wired into plan-maintain as step 7e. Harness build filed as a ready job.

- **2026-11-20** (F-5127): Bug-count read done (J-4423, F-5127): 9 of 69 classified defects were structure-caused (about 14 percent, range 8 to 26), all in _think, all silent; _run_cycle_impl has none. Split stays parked pending the founder's read against D-0877's defeater.
Measured, not started, and deliberately slowed. The founder judged the full split a massive operation with real danger and asked whether it is worth doing at all (chat, 2026-11-20); the first decision (D-0877, go on Phase 0 of the split) is closed as not-as-framed and the plan is reworked. `_think` is 3,598 lines and `_run_cycle_impl` 1,525; both grew about 6% in 13 days. A UDMS before-snapshot and `C:/UDMS/scripts/split_metrics.py` exist. An offline harness that drives real `_think()` calls exists from J-1918 (`scripts/test_idle_offloop_equivalence.py`). Sections 3, 5, 6 and 8 are kept as the design of record for the split, not as work in hand.

## 0. The active track: freeze, test, measure (2026-11-20)

### 0.1 Why the split is parked
- **Thin evidence.** Two size-caused bugs are known (J-2678, J-3952) against 207 commits to the file. Nobody has counted how many other `_think` bugs were caused by structure rather than logic.
- **The benefit goes to sessions, not to Du.** Done perfectly, he cannot tell.
- **"Byte-identical" has a hole.** The harness proves only the blocks it can make fire offline, and his code fails open, so a dropped prompt line in an unfired block would be silent.
- **Certainty is not available** for moving 3,600 lines of his most-edited, most stateful function.

Most of the benefit comes from stopping the growth, which needs no existing code to move.

### 0.2 Freeze (additive only)
New idle-thought behaviour goes in as a helper in a new module (`nodes/idle_thought/`, `seed_part_<topic>(node, state, ctx)`), called from `_think` by one line at the place it belongs. Existing blocks are not moved. A size ratchet (section 4.6) fails when a function over a set size has grown since its baseline. The same rule applies to `_run_cycle_impl`. This needs a CLAUDE.md rule, which is the founder's to adopt (section 9). Cost stated plainly: `_think` stays 3,598 lines and the retry loop stays the fragile part; the freeze only stops it getting worse.

### 0.3 The harness as a standing regression test
Sections 4.1 to 4.4 are built for their own sake, not as a prelude to the split. The file takes about three commits a day and has no regression test on the idle prompt. Used on an ordinary edit it answers "what did this change do to the prompt, to `self` state and to the data files", old worktree against new. It touches no production code.

### 0.4 Measure, then ask again
- **Bug-count read.** Go through the done jobs and findings that fixed bugs in `_think` and `_run_cycle_impl` and classify each: caused by structure (duplicate or misplaced call, wrong scope, retry-loop placement, a local shadowed or stale, a block missed because nobody saw it) or by logic (would have happened in any layout). Report counts with the job ids.
- **Harness in use.** How many real edits it was run on and what it caught.
- **The split reopens only if** the bug count shows structure-caused bugs are a material share, or the harness keeps catching the same class of mistake. If the count comes back near two, the split stays parked and the freeze is the whole outcome.

## 1. Why, and why only these two

Most of Du's big files are many moderate functions and are left alone (F-5125). Two functions are different in kind:

| Function | Lines | Complexity | try nodes | `self` writes | Commits to its file, last 30 days |
|---|---|---|---|---|---|
| `InnerMonologueNode._think` (`nodes/inner_monologue_node.py` L3013-6610) | 3,598 | 548 | 444 | 94 | 97 |
| `Orchestrator._run_cycle_impl` (`core/orchestrator.py` L526-2050) | 1,525 | 181 | 131 | 8 | 42 |

Reasons to act:
- **Growth.** Against F-4191, `_think` went 3,400 to 3,598 and `_run_cycle_impl` 1,427 to 1,525 in 13 days. Every new idle-thought feature lands inside `_think`.
- **Bugs already caused by size.** J-2678 (a dead duplicate `_build_system_prompt` call) and J-3952 (the same call inside the retry loop, eating consume-once feeder lines).
- **Session cost and collisions.** It is the most-edited code in the repo and several sessions edit the same file at once.

Not in scope: `core/lane2.py`, `core/sensorium.py`, `core/memory/store.py`, `core/cat.py`, `nodes/subconscious_node.py`. Their largest functions (`lane2.status` 788, `lane2.tick` 655, `_t4_self_authoring` 536) may get their own look later; this plan does not touch them.

## 2. The shape of `_think` today

`async def _think(self, state: CognitiveState) -> None`, in three sections:

| Section | Lines | Top-level try/if blocks | Clean (no `self` write, no escape) | Write `self` | Contain return/continue/break | Touch `seed_parts` |
|---|---|---|---|---|---|---|
| Before the retry loop (L3013-4423) | 1,411 | 56 | 30 (304 lines) | 22 | 9 | 37 |
| `for attempt in range(2):` (L4424-5760) | 1,337 | 42 | 29 (404 lines) | 10 | 6 | 1 |
| After the loop (L5761-6610) | 850 | 25 | 15 (162 lines) | 10 | 0 | 0 |

Facts that drive the design (F-5126 unless noted):
- **All seed assembly is before the loop.** `seed_parts = []` at L3308; the join into `base_user_prompt` at L4389-4392. Between them: 45 `seed_parts.append` sites plus six `seed_parts.insert(0, ...)` sites (L3465, L3942, L4312, L4338, L4346 and one more), so order is part of the behaviour.
- **Shared state is real.** 105 `self` write sites over 46 attributes; `_moment_source` alone is written 18 times. These are cooldown stamps and latches that later blocks and later calls read.
- **The pre-loop section is not pure.** It has 15 awaits, 15 time reads, 5 random draws, 4 ledger writes and 14 consume-once style calls. A seed part that runs twice, or not at all, changes Du's state as well as his prompt.
- **Imports are local on purpose, as far as can be told.** 140 repo modules are imported only inside functions in this file; the UDMS window found none would close an import cycle if hoisted, so they are most likely inside try blocks for fault isolation. They stay local.
- **Fail-open hides move bugs.** A helper that references a local it was not handed raises NameError inside its own try/except and the line silently vanishes. This is the main risk of the whole plan and the reason for sections 4.2 and 4.3.

## 3. Target shape (PARKED: design of record for the split, not work in hand)

`_think` stays where it is, with the same name and signature, and becomes a conductor: it calls helpers in today's order. Nothing that imports `nodes.inner_monologue_node` changes (25 module-level importers, 5 function-scoped).

- **A package next to the node:** `nodes/idle_thought/`, one module per topic (for example `seed_place.py`, `seed_curiosity.py`, `seed_founder.py`, `seed_sound.py`, `seed_goals.py`, `seed_knowledge.py`; the real grouping is set in Phase 1 from the block outline, not guessed here).
- **One helper per existing block:** `seed_part_<topic>(node, state, ctx)`, `async` where the block awaits. `node` is the `InnerMonologueNode`, so a helper writes the same `self` attributes the block writes today. Shared state is moved, not redesigned.
- **One small context object, `IdleSeedCtx`,** holding what blocks hand to each other: the `seed_parts` list itself (same list object, so append and insert order is unchanged) and the handful of locals that cross block boundaries (redirect flags, the recalled ids, and so on). The exact fields are read off the AST per block in Phase 1; a block that needs more than a few is a sign it should move later or together with its neighbour.
- **Escapes stay visible.** A block that today does `return` becomes a helper returning a stop signal, and the conductor does the `return`. `continue`/`break` blocks inside the retry loop are Phase 3 and may stay in place.
- **Distinctive names.** UDMS hygiene matches by bare name (F-4189), so every helper is `seed_part_*`, `after_thought_*` or `attempt_*`, never `build` or `check`.
- **Each helper keeps its own try/except and its own local imports,** exactly as the block has them now.

What this deliberately does not do: no registry of seed parts, no declarative ordering table, no change to which parts fire. A registry is a natural later step (it is where the prompt-manager plan points), but it is a behaviour-bearing change and belongs in its own plan once the code is in pieces.

## 4. The safety net (no production code change)

Nothing in `nodes/` or `core/` is edited here. Under the active track, 4.1 to 4.4 and 4.6 are built as standing tools (section 0.3); 4.5 and 4.7 matter only if the split reopens.

### 4.1 Equivalence harness
`scripts/think_split_equivalence.py`, built on the J-1918 harness (throwaway worktree, full data copy, frozen `time.time()`, network blocked, LLM boundary stubbed). Additions needed:
- seed `random` so the 5 draws repeat;
- two stub modes: **raise at the call** (covers the pre-loop, enough for Phase 1) and **canned replies** (so the retry loop and the after-thought section run, needed for Phases 2 and 3);
- a scenario set wide enough to open the gates (study directive, curiosity ask, founder recall, goal offer, music, weather, reread hint, mid-train, sleepy, redirect outward, and a plain quiet thought);
- outputs compared between old and new worktree: the system prompt and user prompt bytes, the node's `self` attribute snapshot after each call, the id-normalised bytes appended to every data file, and the log lines.

Pass means byte-identical on all four. One difference of any kind fails the step.

### 4.2 Coverage read
An equivalence test says nothing about a block that never ran. The harness records which lines of `_think` executed across the scenario set (`sys.settrace` or `coverage`), and reports per top-level block: ran with its gate open, ran gate-closed only, never ran. **A block may only be moved in a step where the harness ran it with its gate open.** Blocks that cannot be made to fire offline are listed and moved last, by hand review, or not at all.

### 4.3 Static undefined-name check
The typical move bug is a missed local. After each step, run an undefined-name check over the new modules (pyflakes, or a small AST pass if it is not installed). This catches the bug even in a branch the scenarios did not reach, which the fail-open try/except would otherwise hide.

### 4.4 Negative control
Before trusting the harness: swap two adjacent seed parts in the new worktree and drop one `self` write. The harness must fail both. If it passes either, it is not finished.

### 4.5 Things that will trip when code moves, to settle first
- **Prompt registry SEEDS guard.** `prompt_registry.py check` counts `seed_parts.append` in `nodes/inner_monologue_node.py`. Moving the appends changes that count on the first step. Phase 0 reads how the guard and `scripts/prompt_site_census.py` count, and decides whether the census learns the new package (preferred) or the guard is re-based per step. Not yet read; this is an inference from CLAUDE.md.
- **Tests that read source text.** 13 files outside the node reference `seed_parts` and several J-numbered tests are named for specific lines. Some probably assert on the text of `inner_monologue_node.py` rather than on behaviour. Phase 0 inventories them (not yet done) so a step does not silently turn a real test into a false failure or a false pass.
- **Docs that cite line numbers.** The UDMS window counted 200 line citations in 71 docs into this file. Historic docs are not chased; the count is tracked in the split-metrics snapshot and only live guidelines and this plan are kept right.

### 4.6 A ratchet against regrowth
`scripts/function_size_ratchet.py` with a small baseline file: it fails when a function over a set size has grown since the baseline. Without it the split is undone in a month at the present growth rate. Where it runs (`/plan-maintain`, alongside the prompt-registry check) and the wording of the matching CLAUDE.md rule ("a new seed part is a new helper, not a new block in `_think`") are part of the founder decision.

### 4.7 Retake the baseline
`python C:/UDMS/scripts/split_metrics.py snapshot --repo C:/Nascence --label before` immediately before the first extraction; the file gets about three commits a day, so today's snapshot will be stale.

## 5. Phase 1: the seed assembly (before the loop, 1,411 lines) (PARKED)

Order of work, easiest first, a few blocks per commit, grouped by topic:
1. **1a, clean seed blocks.** The 30 blocks with no `self` write and no escape (304 lines).
2. **1b, blocks that write `self`.** 22 blocks; the writes move with them unchanged.
3. **1c, blocks with an escape.** 9 blocks; each gets a stop signal or stays where it is. No block is forced.
4. **1d, the pre-seed preamble** (L3013-3307, before `seed_parts = []`), if it comes apart cleanly; otherwise it stays as the conductor's opening.

The larger blocks, for planning (start line, length): L3134 68; L3411 68 (awaits, one escape); L3549 122 (curiosity; 3 awaits, 3 `self` writes); L3681 92 (founder recall); L3776 75 (goal offer, recall ids); L4116 66 (goal offer); L4262 44; L4310 41.

**Gate after every step, all must pass:**
1. Harness: byte-identical on prompts, `self` snapshot, data bytes, logs; every moved block ran gate-open.
2. Undefined-name check clean on the new modules.
3. `python -c "import nodes.inner_monologue_node"` and `python scripts/life_smoke.py`.
4. `split_metrics.py compare before.json stepN.json`: no `!!` flag (no new dead function, no new cycle, no new load-bearing import); `_think` smaller.
5. `prompt_registry.py check` exits 0.
6. Commit: only `nodes/inner_monologue_node.py`, the new module(s) and this plan, staged by path.

**Stop rule:** if a step fails the harness twice, the block goes back where it was and is listed as "stays", with the reason. A smaller `_think` with a dozen awkward blocks left in it is a good result.

## 6. Later phases (PARKED)

- **Phase 2, after the thought (L5761-6610, 850 lines).** 25 blocks, none with an escape, 10 writing `self`. Needs the canned-reply stub. Helpers named `after_thought_*`.
- **Phase 3, the retry loop (L4424-5760, 1,337 lines).** The hardest part and the home of the J-3952 class of bug: anything consume-once must run once per thought, not once per attempt. Likely shape is one `attempt_*` helper per stage of an attempt, with the loop itself left in `_think`. Designed in detail only after Phases 1 and 2, because what they teach will change it.
- **Phase 4, `_enter_sleep` (641 lines, complexity 95).** Optional, same method.
- **Phase 5, `Orchestrator._run_cycle_impl`.** Should be the easier of the two (8 `self` writes, complexity 181) but it is the cycle spine, so it needs its own cycle-level harness and its own go. It runs in a separate quiet window from the `_think` work: the two files co-change strongly (PMI 3.55 bits, lift 11.7 in UDMS's window, which is the stale oldest-450 one).

## 7. How it runs

- **Quiet window.** No job-run and no other session editing `nodes/inner_monologue_node.py` while a phase is open. UDMS cannot see other sessions; check `git status` and the day's handoffs before each step.
- **Du can stay up.** Edits do not reach the running process. Restart once per phase, not per step.
- **First live read after each restart (24 h):** no new exception lines naming `nodes/idle_thought/` in `data/nascence.log`; idle-thought rate and prompt length distribution against the week before; and, if the prompt provenance ledger records per-part sources (to check in Phase 0), per-part firing rates against the week before. A part that fired daily and now never fires is the signature of a swallowed move bug.
- **Rollback.** Each step is one commit, so `git revert <commit>` of this plan's own commit undoes it. Never a reset.
- **UDMS use.** MCP tools scan once per session and will not see new modules; per-step checks use the CLI (`split_metrics.py`, `udms.py hygiene`). The dossier's history evidence for these files is two months old until the newest-450 switch lands (D-0829, D-0846, after J-3781).

## 8. What done looks like

**For the active track:** `_think` and `_run_cycle_impl` no larger than their 2026-11-20 baselines at each `/plan-maintain` pass; the harness exists and has been run on real edits; the bug-count read is recorded as a finding. The table below applies only if the split reopens.

| Measure | Today | After Phase 1 (expect) | After Phases 1-3 (aim) |
|---|---|---|---|
| `_think` lines | 3,598 | about 2,300 | under 800 |
| `_think` complexity | 548 | falls with it | under 120 |
| UDMS outlier score, `inner_monologue_node.py` | 18.14 | lower | below `memory/store.py` (7.85) |
| Dead functions, repo-wide | 32 | 32 or fewer | 32 or fewer |
| Idle prompt bytes on the scenario set | baseline | identical | identical |

The numbers in the last two columns are estimates, not commitments; the stop rule in section 5 outranks them.

## 9. Open founder decision

**D-0877 (ruled 2026-11-20, founder): not as framed.** It asked for a go on Phase 0 of the split. The founder judged the split a massive operation with real danger and asked whether it is worth doing; the split is parked. Defeater: revisit if the bug-count read shows structure-caused bugs are a material share of the fixes, or the standing harness keeps catching the same class of mistake.

**D-0878 (open): go on the freeze-first track,** in two parts that can be ruled separately:
1. Build the equivalence harness as a standing regression test (a new script; no production code change).
2. Adopt the freeze rule in CLAUDE.md ("a new seed part or cycle stage is a new helper in its own module, called by one line") with the size ratchet run by `/plan-maintain`.

The bug-count read is read-only and is filed as a ready job; it does not wait on D-0878.

Questions that return only if the split reopens: whether the protected-base rule permits a move-only refactor proven byte-identical, and the final package layout.

## 10. Risks, plainly

- **A silently dropped prompt line** (swallowed NameError, forgotten call). Countered by 4.1 to 4.4, the hygiene tripwire and the 24 h read. Residual risk sits in blocks the harness cannot fire.
- **A double-run or skipped side effect** (cooldown stamp, consume-once feeder, ledger row). Countered by comparing `self` state and data bytes as well as prompts.
- **Collision with another session's edit.** Not detectable by tooling today; countered only by the quiet window.
- **Effort with no behavioural gain.** True by design: Du should be unable to tell. The gain is fewer bugs of the J-2678 kind, cheaper sessions and a stop to the growth.
