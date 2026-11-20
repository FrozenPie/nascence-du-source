# Nascence: corrections and fresh facts for the technical review (2026-11-20)

Paste this back to the reviewer. Every figure below was measured in the repo on 2026-11-20 unless marked
"not re-measured". Finding ids (F-NNNN) are entries in `docs/findings.jsonl`; each one cites its own evidence.

## 0. What the review was based on, and what changed

The review used the System Overview "Build 2.0", dated 2026-10-19. That is a month old and it was
generated from static inspection, not from running anything. Please re-read the review's verdicts with the
figures below, not the overview's.

| Figure | Overview (Oct 19) | Measured 2026-11-20 |
|---|---|---|
| core/ modules | 272 | 340 (top-level `core/*.py`) |
| nodes/ files | 16 | 17 |
| scripts | 588 | 1,374 (`scripts/*.py`, same top-level method) |
| Core + nodes lines of code | 122,573 | 172,562 (recursive count, so not exactly comparable) |
| Findings | 3,130 | 5,257 |
| Findings marked verified | 2,887 (92.2%) | 4,755 (90.4%); inferred 495; guessing 7 |
| Jobs | 2,428 | 4,483 (4,077 done, 394 open, 12 in progress) |
| Decisions | 486 | 898 (878 ruled, 20 open) |
| Git history | not stated | 3,676 commits since 2026-08-27 |
| Tests | not stated | 16 test files in `tests/` |

The live / shadow / lab split (200 / 79 / 9) was **not re-derived**. It depends on the boot commit and
flag state, so treat it as unknown today.

"Verified" in this ledger means a claim was recorded with cited, checkable evidence (a file, a command that
was run, a log line). It is our own record of our own checks. It is not independent reproduction.

## 1. Corrections to the review's assumptions

### 1.1 Dosed coupling is not an operating dose-and-consume mechanism today

This is the most important correction, because the review ranked dosed coupling as the top candidate.

- The overview wrote that "consumers read dosed cups/buckets". That is the design, not the state.
  `docs/plans/dosed_coupling.md` (state verified 2026-11-20) says: Phase 0 and Phase 1 are live, meaning
  loops **publish** typed coordinate tuples to a registry and a ride log. Phase 2 (residual cups, a hub,
  speech-concurrency) is **drafted and not ruled**. Dosed reading by consumers is not built beyond one
  shadow-only reader (the Lane 2 Witness cup).
- `data/coupling_rides.jsonl` now holds 258,734 rows: 181,136 publish, 41,740 probe, 35,197 ride,
  674 would-ride. The overview's "111,412 coupling rows" counted publish rows and was already stale. These
  are log rows. They are not a count of consumers receiving doses.
- F-3305 (2026-10-30): coalition mining over the ride log found nothing. The pre-declared null was not
  beaten on both halves of the data (`FALSIFIED_NO_COALITION`). At that time the log had only two
  reader-source pairs, both Witness, and 11,006 of 12,139 rides were empty.
- F-1304 (2026-09-13): the "two of four behaviour metrics out of band" were **guard bands** (cycles per
  day, commitments per day, idle-thought gap, Witness break rate). They exist to check that coupling does
  not distort behaviour. They are not an efficacy measure. Two of four were out of band and worsening.
- The overview credited a "0.48 to 0.82 lift" next to coupling (F-0845). That is the share of stream-drive
  rows tagged as grounded, after a grounding-tag fix (J-0581). It has nothing to do with coupling efficacy.
- F-2925 (2026-10-16): in the Phase 2 paired shadow read, the two gates agree on 97.9% of moments but their
  firing sets overlap with Jaccard 0.10. The agreement is a low-base-rate artefact.
- F-4480 (2026-11-14): the kill rule as written trips on the four climate lines. A decision is open on
  whether to kill the rule or change the bar.

So the status is: a well-specified design law with live publishing, no demonstrated benefit, and several
mixed or negative reads. "Potentially distinctive" is fair. "Strongest candidate" rests on the overview's
overstatement. Please redo that ranking on this basis.

### 1.2 UDMS is a different project from what the review described

- UDMS (`C:\UDMS`) is a **separate code-analysis tool**: structural and temporal dependency analysis over a
  repository's AST and git history, with a co-change PMI model, dossiers and hygiene scans. It is wired
  into the Nascence workflow through an MCP server so that edits can be checked for blast radius.
  It is not a mathematical substrate for Nascence's transitions.
- The "5,855x speedup" (F-0600) is a point-query speedup of an additive **sidecar index over a linear scan**:
  `scripts/geometry_tuple_p1_run_transition_index.py`, weather field only, 31,111 rows, 248 transitions,
  100% point-query correctness. It shows an index is faster than scanning. It says nothing about the
  representation's accuracy or generality, so the review's Koopman and manifold-learning comparison does
  not apply to it as stated.
- The "geometry" work that is Nascence's own is the geometry-tuple store (`geometry_tuples.jsonl`) and the
  plan `docs/plans/cognitive_geometry.md`. UDMS's persistent-homology routine is **imported** to analyse
  it (F-0414: a rolling Betti-number read over 22,886 tuples; beta_0 flat at 1, beta_1 declining about
  20-30%). That is a measurement of Du's own concept co-occurrence graph, with no comparison against any
  baseline method.
- The review's "calibrated intrinsic dimension estimate" is a finding about Du's own data over time
  (F-0413/F-0414), not a method contribution.

Please drop UDMS from the "independent technical contribution" list as framed, and treat the geometry-tuple
work as an unvalidated internal analysis.

### 1.3 The memory latency number

- 581 ms to 157 ms (F-2972) is the **median** over 60 real query heads, on a sqlite `.backup()` copy
  holding a 41,923-row active pool, in a single test process. Max latency was 314 ms, the first call after
  process start was about 930 ms, and results were identical to the old path on 60 of 60 queries.
- The pool has since grown. F-5122 (2026-11-19) counts 188,174 rows, of which 87,203 are cold. I have
  **not re-measured latency** on today's pool, so 157 ms should not be quoted as current.
- The same finding (F-5122) matters for the review's memory discussion: cold storage is a hard wall. The
  main recall path excludes cold rows entirely, nothing re-warms a row on recall, and only the associative
  trail has a harder-but-possible path (activation threshold 0.22 against 0.13). So the memory design is a
  threshold system with a hard cutoff, not a graded forgetting curve.

### 1.4 The sleep speedup

2,775 s to 10.0 s is the replacement of a Python all-pairs dot loop with a blocked float32 matrix
computation. That is a vectorisation fix, not a design contribution. The sleep architecture is a separate
question, and the review is right to keep the two apart.

### 1.5 Fault tolerance: the review's gap is confirmed with a real incident

F-5128 and F-5129 (2026-11-19/20): a hard crash zero-filled 19 state files in `data/` and left a 715 MB
SQLite WAL. The relaunch spent 5 min 6 s replaying the WAL. The process then loaded the blank files **with no
warning in the log** and restarted several from empty (for example a 16.2 MB state file became 174 bytes).
No intact copy existed inside the repo's own backup scripts. The files were recovered only because Windows
shadow copies happened to exist (4 h 15 min old). So: no atomic-write or checksum discipline for these
files, and no corruption detection on load. Also: 16 test files for 340 core modules, so the "connect
the evidence ledger to repeatable tests" point is correct, and the gap is large.

**CORRECTION to the paragraph above (checked later the same day).** The sentence "no atomic-write or
checksum discipline" was too strong. What the code showed before the crash was this: the writers I checked
(spring_ledger, opponent_process, world_manifest, transport_manager, cat, life, fieldcraft, the
garden/shore/wood life modules, smell, climate_engine, light_sidecar and others) already wrote through a
`.tmp` file and `os.replace`, which is an atomic rename. What was missing was `fsync` before the rename, so
after a hard crash NTFS could keep the renamed name but lose the data, which is how the files came back
zero-filled. There was also no previous generation to fall back to, and the load paths returned an empty
default on any read error without warning (for example `core/goals.py`, F-5131). Fixes were built the same
night, and are **restart-gated, not yet running**: J-4426 / F-5157 added `write_text_durable` (tmp, flush,
fsync, replace, keep the outgoing file as `<name>.prev`, never rotate an empty or NUL file into `.prev`) and
`read_json_durable` (loud warning, move the bad file aside, fall back to `.prev`). J-4442 / F-5166 moved the
second batch of files onto them, and J-4427 / F-5156 extended `scripts/backup_memory.py` to the 16 files.
Still missing against the reviewer's five gates: schema and invariant validation beyond "non-empty and
parses", checksummed generation manifests, cross-process write locking (the locks are in-process threading
locks), crash-injection tests, and a restore drill. I did not check that every one of the 19 files' writers
was converted. Also, `scripts/` holds 669 files named `_test*` or `test_*`. Many are one-off lab and replay
scripts rather than regression tests, but the "16 test files" figure understates the checking that exists.

### 1.6 Code health, which the overview did not show

`InnerMonologueNode._think` is 3,598 lines and `Orchestrator._run_cycle_impl` is 1,525 lines. They grew
about 6% every two weeks, and nine past defects in `_think` came from its layout, all silent (a line added
where it could not reach the prompt, a call that ran once per retry, two distant blocks doing the same job).
Decision D-0878 froze both functions and added a size ratchet. A split is parked (D-0877). The review's
"integration complexity: very high" has a cost side that it could not see.

### 1.7 Model layer

The overview lists a Qwen 3.5 9B hot lane plus several judge and background models. I confirmed
`qwen3.5:9b` is still referenced in core, but did not re-audit every lane. On 2026-11-18/19 there was a
benchmark of candidate seats (F-5117, F-5118). Its main caveat: the Ternary-Bonsai CPU numbers came from 3
calls per file with 117-152-token prompts, against real prompts of about 1,000 tokens, so those results are
weak evidence on their own.

## 2. Claims in the review I could not support from the repo

- "I have not found a direct, established equivalent" for dosed coupling: there are no citations behind
  this. Close prior art that the review should address explicitly: blackboard systems, Global Workspace
  Theory implementations (LIDA and related), actor and mailbox models with backpressure, rate-limited
  pub/sub, and token-bucket flow control.
- "Governance: very strong": the ledger discipline is real, but see section 0 on what "verified" means.
  The judge panel uses different model families to avoid self-grading, but F-4663 (2026-11-14) measured
  Cohen's kappa between the two panel judges per verdict key and found it weak, from +0.02 to +0.50 (for
  example genuine +0.03, metaphor +0.08, supported +0.50). F-4673 found agreement not better in the
  current seating. F-4338 found one live prompt agreed with blind gold labels only 53% (kappa 0.18). So the
  model-judge layer is a weak independent check, and the review's "ensemble evaluation" framing flatters it.
- "Persistent relational memory plus identity estate plus temporal consolidation: unusually broad
  integration": plausible, but no ablation exists that shows the combination beats a plain retrieval
  baseline on any shared benchmark.

## 3. What the review got right (keep these)

- No external benchmark exists for memory, retrieval or reasoning. Nothing has been run on LongMemEval,
  LoCoMo or MemoryAgentBench.
- No ablation exists for sleep/replay or for dosed coupling.
- Fault tolerance, schema migration, consistency between live and shadow code, and restart reproducibility
  are weak (1.5 above).
- The world model has no prediction-accuracy or calibration measurement.
- Multimodal perception was not assessed, so "not assessed" is the right label.

## 4. Questions I would like the reviewer to answer next

1. Redo the contribution ranking given sections 1.1 and 1.2. What, if anything, remains a candidate?
2. For dosed coupling as it **actually is** (publish side live, one shadow reader), list the closest prior art
   with citations, and say what experiment would show benefit. Use the existing 258k-row log and the
   pre-registered falsifiers in `docs/plans/dosed_coupling.md` as the starting point.
3. For the memory system, which common benchmark subsets can run against a store with a hard cold wall and
   a threshold-based trail, and what would an honest comparison look like given the latency caveats?
4. Propose a minimal reliability test plan for a persistent multi-process system that writes large JSON
   state files without atomic replace (crash injection, load-time validation, restore drills).
5. Say which claims in your first review you now withdraw or downgrade.
