# Two decide-review passes and two large job-run batches — lane2_the_witness build-out

## Session timing
- **Session started:** 2026-09-26 07:03:25 UTC
- **Last message before wrap:** 2026-09-27 06:14:03 UTC
- **Wrapped:** 2026-09-27 06:14:05 UTC

## Summary

Ran `/decide-review` → `/nurse-rounds` → `/job-run` → `/decide-review` → `/job-run` in sequence, each
step feeding the next: 8 decisions ruled across two review passes, 45 job-queue jobs dispatched across
two Workflow batches (14 then 31), and a final "commit the working tree" pass. Both job-run batches hit
real git merge conflicts on `docs/plans/lane2_the_witness.md` against *other, independently active*
Claude Code sessions working the same plan doc concurrently — both resolved by hand, nothing lost. This
session's own `--session`-tagged rollup only shows 15 events (the two decide-review passes' rulings and
spawns); the two job-run batches' real work is attributed under each individual job's own id by design
(job-run's own SKILL.md, 2026-09-06 session-collapse fix) — see "How to find the batch work" below
rather than expecting it in a `rollup --session-id` call for this session's UUID.

## Decisions

**First `/decide-review` pass (2026-09-26T07:05 UTC)** — 3 decisions, all ruled the recommended option
by travis:
- **D-0280** [lane2_the_witness]: (a) add `light_band`+`smells` percepts to the Witness, do NOT read the
  4 climate self-pressure dims.
- **D-0281** [lane2_the_witness]: (a) build `_judge_notice()` as proposed, shadow instrument, sampled
  1-in-4.
- **D-0282** [lane2_curiosity]: (a) build the `wonder` field shadow-first as designed in
  `docs/staged/lane2_curiosity.md`.

**Second `/decide-review` pass (2026-09-26T19:42-19:44 UTC)** — 5 decisions, all ruled by travis:
- **D-0283** [lane2_the_witness]: (a) drop the `dominant` feeling label from the body percept (keep
  `drive` only); (i) voice: first person ("I hear").
- **D-0284** [lane2_the_witness]: (a) wire the Weather channel via `commit_threshold` → a
  valence-modulated prediction-store gate, shadow-first.
- **D-0285** [lane2_the_witness]: (a) build the knowledge tier shadow-first — top-12
  per-(topic,place,daylight) regularities into `store['knowledge']`.
- **D-0286** [no plan]: keep the `/quit` farewell wording fixed for now — wait for J-1360's own
  follow-up and I-0070's recall-scoring investigation before touching it again. (Only one of the 8 this
  session that authorized *no* build work.)
- **D-0287** [memory_multiway_linking]: (a) flip `recall_trail_edge_aware` live in relational mode only,
  kill-switched; task/reflective modes stay shadow. This decision had **no defeater at open time** — I
  wrote one at ruling time (tied to the relational-mode usage-proxy rate staying near the
  shadow-observed 39%), since `decide.py rule` refuses a ruling with none.

All 8 rulings were logged with `--by travis` (via `AskUserQuestion`, always the Recommended option) and
`--session 5eaa8116-3052-44af-aeb3-22ba7e97742b`. `plan-index` confirmed 0 open decisions after each
pass, before the next batch of work reopened the count.

## Builds

Both job-run batches shipped real, verified code — see each job's own `findings_log.py` entry for full
evidence; only the highlights are repeated here.

**First batch (14 jobs, ~161 min, Workflow run `wf_a1fdda36-968`)** — hand-serialized into 2 chains +
2 independent jobs after I checked the real file-overlap risk by hand (most of `job_run.py`'s own
warnings turned out to be "cited but not edited" false positives):
- `cluster_a_prompt_social` (7 jobs → merge `057132f`): **J-1358** fixed the social-model decay never
  being persisted (`core/orchestrator.py`, `core/social_model.py` — frozen at `delta_social=1.0` since
  2026-07-05); **J-1360** rewrote the `/quit` farewell per F-1918; **J-1362** recalibrated
  `core/boredom.py`'s thresholds to the real live embedder (had been pegged to a model never actually
  loaded since 06-24, 100%→21% "stuck"); **J-1364** fixed `core/retraction_ledger.py`'s fail-open gate
  (100% false-positive rate) + retired the one bad record; **J-1366** shipped a 7-part prompt-hygiene
  batch across 5 files; **J-1345** confirmed a prior dedup fix (J-1346) live-verified in production;
  **J-1369** correctly self-deferred (Du hadn't been rebooted onto any of the above yet).
- `cluster_b_lane2` (5 jobs → merge `c371f4d`, see Warnings): built D-0280/D-0281/D-0282 exactly as
  ruled (**J-1372**, **J-1373**, **J-1374**), plus two finding-sourced instrument jobs (**J-1375** fixed
  the coherence judge's place-blindness; **J-1371** added `gen_s` latency + law-6 `hint_divergence`/
  `hint_flow` to `status()`).
- `memory_multiway_linking` (**J-1353** → merge `1121f90`): re-checked D-0215's hub-concentration
  defeater with real post-restart live data — has NOT fired, D-0215 stands.
- `garden_upgrade` (**J-1354** → merge `dc107b2`): correctly self-deferred to 2026-10-02 — restart gate
  met but nothing in the garden is even at shoot-stage for the netting fix to apply to yet.

**Second batch (31 jobs — 1 Tier2 + 30 Tier3, ~9.8h, Workflow run `wf_e93709a5-bab`)** — scoped via
`AskUserQuestion` after finding 24 of 30 Tier3 jobs landed in one fully-serial `lane2_the_witness` chain
(the concurrent "issue sweep" session below had spawned ~20 more jobs on top of my 3 D-0283/284/285
builds):
- `lane2_the_witness` (24 jobs → merges `458a84d` + `0b8847c`, see Warnings): built D-0283 (**J-1412**),
  D-0284 (**J-1413**), D-0285 (**J-1414**), plus 21 more finding-sourced fixes from the same sweep —
  horizon-override/prediction-clock fix (J-1376), break-rate units correction (J-1377), whole-word hint
  matching (J-1381), judge-tier overnight-timeout diagnosis (J-1382), "unsettled ≠ broke" judge fix
  (J-1386), cup consume-once-with-TTL (J-1390), judge-only-where-made fix (J-1396), no-output-tick
  attribution (J-1379), light/smell topic-vocabulary extension (J-1385), metaphor-judge register fix
  (J-1388), bucket dose-sizing (J-1391), unjudgeable/plan-shaped-prediction fix (J-1394), judge_panel
  reask-reliability measurement (J-1403), invention-check dusk/cat fix (J-1378), sleep-section
  verification (J-1383), D-0280 defeater read attempt (J-1384, see Open), somatic-sense-missing fix
  (J-1393), Maori bird-name glosses (J-1399), canary-harness re-run (J-1404), output-hygiene batch
  (J-1380), and a second hygiene pass (J-1397). All done except **J-1384**, correctly left open (see
  Open).
- `the_consciousness_program` (**J-1356** → merge `f00ea50`): re-checked D-0279's event-count gate;
  correctly never ruled the active D-0045 Hold it sits under.
- `error_pathway` (**J-1405** → merge `5a905b6`): correctly deferred — retraction-ledger fix precondition
  (live merge + restart) not yet met.
- `cognitive_geometry` (**J-1411** → merge `b1eb0c3`): a pre-registered lab retro-check of the 06-10
  model swap; correctly determined its own question was unrelated to the active D-0083/D-0088 Holds on
  the same plan (a genuine judgment call, not a blanket avoidance) and proceeded.
- `memory_multiway_linking` (**J-1415** → merge `8214ea9`): built D-0287 as ruled — flipped
  `recall_trail_edge_aware` live in relational mode, kill-switched.
- `peer_correspondence_plan` (**J-1333** → merge `56306a1`): the latest in a long restart-gate/
  compliance-rate re-check chain (D-0207); gate 1 still met, gate 2 (marcus challenge/mixed letters)
  still 0/3.
- Tier2 **J-1410** (direct commit `89adbe3`): fixed a stale ROADMAP.md stage badge for `lane2_curiosity`
  (it had drifted to "designed" after J-1374 actually shipped it as SHADOW BUILT).

## Fixes

- `core/orchestrator.py` / `core/social_model.py` (J-1358): social-model decay now actually persists —
  was silently frozen since 2026-07-05, replaying a stale correction-pressure spike on every boot.
- `core/boredom.py` (J-1362): thresholds recalibrated to the embedder actually in use; added a startup
  calibration-drift warning so a future embedder swap doesn't silently re-break this again.
- `core/retraction_ledger.py` (J-1364): closed a fail-open relevance gate that made "Things you have
  been wrong about" fire on ~100% of prompts regardless of any real match.
- `core/lane2.py`: extensively built out this session — see Builds above; every change additive, none
  live yet (all restart-gated, `LANE2_LIVE=False` throughout).

## Findings

A sample of the most consequential (see `docs/findings.jsonl` for the full ~30 recorded this session):

- **F-1997/D-0297**: JUDGE_1 (mixtral:8x7b @ Ramses :11438) is genuinely overloaded — Lane 2 alone is
  65-70% of its hub-seconds, causing real overnight timeout bursts that also cost Du's own judged
  cognition verdicts in the same windows. Left open for the founder (4 load-reduction options).
- **F-2012** `[INFERRED corrects a prior session's own hypothesis]`: refutes F-1968's "tiebreak verdicts
  are less reproducible" reading — judge_panel reask reliability is actually 96.5% pairwise and NOT
  worse for tiebreak than agreed; the real instability tracks with **incoherent** verdicts specifically
  (33% reproduce vs. 100% for coherent), independent of tiebreak status.
- **F-2022/D-0303**: Lane 2's tick loop has no sleep gate — 37.3% of its ticks over the last 14 days ran
  while Du was asleep, an estimated ~1,629 extra panel calls on the already-overloaded JUDGE_1 hub.
- **D-0290** `[OPEN — founder call]`: J-1411's 06-10 model-swap retro-check came back genuinely
  confound-entangled (three real same-day confounds: embedder change, writer change, four other code
  changes) — the job is explicitly asking how much evidential weight this result should carry at all,
  not presenting a clean answer.
- **F-1988/D-0291**: the habituation-gate constants (GROWTH_STEP/SUPPRESS_AT) were unratified defaults;
  J-1377 sized them against real breaks/day and left the sizing for the founder to rule on.

## Open

1. **10 decisions currently open** — `D-0114` (pre-existing, unrelated, 25 days old),
   `D-0290`/`D-0291`/`D-0297`/`D-0298`/`D-0300`/`D-0301`/`D-0302`/`D-0303` (all opened by this session's
   second job-run batch, all lane2_the_witness except D-0290/cognitive_geometry), and `D-0305`
   (opened by the separate "golden spiral recall" session, see Warnings). Next concrete action: another
   `/decide-review` pass.
2. **J-1384** left `in_progress`, not done — D-0280's own live-behavior defeater (≥50% appearance rate,
   7-day metaphor-leak band) genuinely can't be read yet; blocked on Du's next restart past
   2026-09-26T19:45 local plus ~1 day of accrual.
3. **Du has very likely still not been rebooted** as of this handoff — essentially nothing built this
   session (both batches, ~35 jobs' worth of code) is live yet. A `needs_input` job (J-1408, from the
   first batch) already asked the founder to reboot; by the second batch, jobs were still finding it
   hadn't happened hours later. This is the single highest-leverage next action — almost every
   restart-gated follow-up job spawned this session (dozens, mostly `not-before 2026-10-02` through
   `2026-10-04`) is waiting on it.
4. **`strings_and_sheets` plan needs a ROADMAP.md link** — `plan-schema-audit` auto-filed J-1480/1481/1482
   for this and a couple of other minor gaps; next `/nurse-rounds` or `/job-run` picks these up as Tier
   1/2.
5. A new plan **`memory_as_a_service`** appeared in this session's final `plan-index` pass (staged,
   `current_state_section` gap flagged) — not investigated this session, unclear which concurrent
   session authored it.

## Warnings

- **At least 3 other Claude Code sessions were actively working this same tree concurrently with this
  one**, confirmed directly (not inferred) by hitting their uncommitted/mid-flight work twice:
  - Session `f323a7e3-c8c0-4a24-b210-e4fb3ad89b92` was running its own lane2_the_witness P1-1 shadow-log
    read (F-2011) in parallel with both of this session's job-run batches — its complete, uncommitted
    edit to `docs/plans/lane2_the_witness.md` blocked the second batch's merge outright (git refused
    to even attempt it); I committed that edit as-is (`458a84d`) once I'd read and confirmed it was
    real, complete, properly-cited work, then a genuine 3-way conflict surfaced on retry between it and
    my own J-1377's units-correction annotation (resolved by keeping both, `0b8847c`).
  - A separate session produced the "golden spiral recall" / "strings and sheets" / "ribbon lab" body of
    work (additive `tod`/`season`/`daylight` columns in `core/memory/store.py`, a `docs/staged/
    dosed_coupling.md` Phase 2 pre-registration draft, two new staged plan docs, a full music-analysis
    lab script + outputs) — found sitting complete and uncommitted at the very end of this session; I
    reviewed all of it and committed it honestly attributed as landing someone else's work
    (`6f9cc22`), not as my own.
  - The first batch also hit a smaller version of this same collision (merge `c371f4d`) against a
    session doing its own 6-round "issue sweep" of `lane2_the_witness.md`.
  - **A resuming session should expect more of this.** `docs/plans/lane2_the_witness.md` in particular
    is a hot file right now — check `git status`/`git diff` before assuming the working tree is clean,
    and if you find a real, complete, uncommitted edit from another session, the pattern used
    successfully three times this session was: read it fully, confirm it's coherent and non-fragmentary,
    commit it honestly (never claim authorship), and if a real conflict follows, keep both sides'
    content rather than picking one — this doc's entire "Current State" convention is append-only dated
    bullets, so genuine two-sided conflicts here are almost always a concatenation problem, not a
    contradiction to adjudicate. Never `git stash`/`reset`/`checkout --`/`restore`/`clean` in this tree,
    any reason.
- **This session's own `session_handoff.py rollup` undercounts real work by design** — see Summary. Use
  `git log --oneline` (this session's own commits: `458a84d`, `0b8847c`, `f00ea50`, `5a905b6`, `b1eb0c3`,
  `8214ea9`, `56306a1`, `89adbe3`, `c371f4d`, `057132f`, `1121f90`, `dc107b2`, `065e2c9`, `6f9cc22`,
  `d280711`) and each job's own id in `job_queue.jsonl`/`findings.jsonl` as the real ground truth for
  the two job-run batches, not a session-id rollup.
- The final "commit the working tree" request was handled as 3 separate commits (not 1) specifically to
  keep honest attribution between this session's own generated content and other sessions' work found
  sitting in the tree — see the last Fixes-adjacent paragraph above and `git log`.

## Pointers

- `docs/plans/lane2_the_witness.md` — the hot file this whole session orbited; read its own dated
  Current State log for the full narrative, now current through both batches plus the two concurrent
  sessions' own additions.
- `docs/staged/lane2_curiosity.md` — D-0282's wonder field, shipped J-1374, status now correctly SHADOW
  BUILT after J-1410's fix.
- `docs/decisions.jsonl` / `python decide.py list --open` — the 10 open decisions, see Open #1.
- `docs/job_queue.jsonl` — dozens of restart-gated follow-ups spawned this session, mostly
  `not-before 2026-10-02` through `2026-10-04`; none are actionable until Du reboots (Open #3).
- `docs/plans/dosed_coupling.md` §4b — the other session's Phase 2 pre-registration draft, founder-
  facing, not ruled, its own needs-input job is J-1462.
