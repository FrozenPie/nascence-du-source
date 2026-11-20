# Dream Overhaul — Experiment A, first read (2026-09-17, J-1059)

**Status: PRELIMINARY (N=2 seeds, not the pre-registered N=20).** The four-arm in-vitro A/B
(`docs/staged/dream_overhaul.md` sec 6) was built and run for real against the live dream engine.
This document reports the first 8 arcs (2 seeds × 4 arms) that completed inside this job's session;
the run (`scripts/dream_experiment_a.py --n-seeds 6 --tag pilot6`) kept going in the background past
that point (PID 1737/1738 at write time, not guaranteed to survive this session ending) and may have
produced more rows at `data/_lab/.../` / the scratchpad results file below by the time anyone reads
this — re-run the summary query in "Pointers" before trusting numbers beyond what's in this table.

## Method

- **Engine:** `nodes/dream_node.py` (worktree `wt_coupled_cluster_2`, commit eb2f8b3 — post-J-1057
  Phase 1 instrumentation). `DreamNode._gen_episode()` called directly in a custom 3-scene loop
  (mirroring `scripts/dream_arc_test.py`'s own established pattern), NOT `synthesise()` — this means
  Phase 1's own `_log_transition()`/`dream_probe.log_seed_pairs()` side-effect logs are never reached
  (they live inside `synthesise()`'s loop body only), on top of `commit=False` already skipping
  `_store_episode`/`_bridge_final`/`_ground_symbols`/`_log_arc` (verified by reading `synthesise()`).
- **Isolation (job-queue `isolation=required`):** `lab_env.isolate()` redirects
  `core.memory.store.DB_PATH` to a copy before any read; `core.telemetry`'s three write globals
  (`_CALLS`, `_STATIONS`, `_LAT`) are also redirected via `isolate(also=...)`. Single-call smoke test
  confirmed the DB copy byte-identical pre/post (lab_env's own D-0206 check fired "deleted — unwritten").
  Backstop: `C:\Nascence\data\memory\nascence.db` mtime is printed before/after the whole run by the
  script; not yet re-checked against this partial run since it is still going (see "Status" above) —
  the follow-up job should confirm this once the process actually exits.
- **Seeds:** day residue via `core.night.dream_lag_material(now=<hist>, k=2)` at `hist = now - i*86400`
  for i in 0..5 ("6 real nights", i.e. 6 distinct historical `now` timestamps 1 day apart); tension
  pulled ONCE from the live `subconscious_state.json` snapshot at freeze time and reused for every seed
  (no historical-tension reconstruction path exists — `_load_top_tensions` has no `now` parameter).
  All 6 seeds this run had 0 tension blocks (chronic_mass below `TENSION_CHARGE_FLOOR` at freeze time)
  — real, not a bug, matches the plan's own "most dreams run on pure residue" expectation, but it does
  mean this pilot says nothing about the tension-bearing ~1/4 of real nights.
  Recalled fragments (`associative_recall.recall_fragments`, k=6) and the dormant-fragment pick (D-0231
  rule) both DO vary per seed, keyed on that seed's own day-block text.
- **Dormant candidate pool** (before filtering): 17,770–17,961 for seeds 0–2, matching the plan's own
  independently-stated "≈ 20,000 candidates" (`docs/staged/dream_overhaul.md` line 31) — cross-check
  passed, gives real confidence the D-0231 origin/age/chapter filter was implemented correctly.
- **Arms:** A0 current engine (materials + recall re-fed every scene) · A1 no re-feed after scene 1 ·
  A2 no re-feed + dormant fragment in scene 1 · A3 dormant + re-feed kept (isolates the dormant effect
  from the re-feed effect). 3 fixed scenes every arm (open/develop/close — the real engine's own
  deterministic phase sequence when `MIN_EPISODES==MAX_EPISODES==3`, verified by reading `synthesise()`
  rather than assumed). Scope choice, documented not hidden: `memories` (the recalled-fragment block)
  is scene-1-only in EVERY arm here, including A0 — only `materials` (day residue) is the re-feed
  variable this run tests, matching the plan sec 6 table's own single "re-feed" column.
- **Cost so far:** 8 arcs × 3 scenes = 24 real calls to the dreamer hub (mixtral:8x7b @ LAN-HOST:11438,
  live and reachable this session), ~146s/arc mean, ~24 min wall for these 8 rows.
- **Judge shadow:** NOT run this pass (briefing sanctions omitting + saying so) — time budget went to
  getting a real end-to-end mechanics check instead; the follow-up job should add it if the judge hubs
  (11439/11440, both up this session) are still up when it runs.

## Results (N=2 seeds, 8 arcs)

| arm | n | mean turnover | mean dormant_contact | mean recent_contact | mean wall_s |
|---|---|---|---|---|---|
| A0 (current engine)      | 2 | 0.6703 | 0.3419 | 0.5013 | 146.8 |
| A1 (no re-feed)           | 2 | 0.8244 | 0.3747 | 0.5005 | 169.3 |
| A2 (no re-feed + dormant) | 2 | 0.7375 | 0.3535 | 0.4827 | 141.4 |
| A3 (dormant, re-feed kept)| 2 | 0.7098 | 0.3169 | 0.5264 | 145.8 |

Per-seed detail (turnover, the D-0232 comparison):

| seed | A0 | A1 (>A0?) | A2 (>A0?) | A3 (>A0?) |
|---|---|---|---|---|
| 0 | 0.6500 | 0.7917 (yes) | 0.7000 (yes) | 0.7738 (yes) |
| 1 | 0.6905 | 0.8571 (yes) | 0.7750 (yes) | 0.6458 (**no**) |

## Reading against the pre-registered thresholds (plan sec 6)

**Threshold 2 (D-0232's defeater) — A1/A2 turnover above A0 on the same seeds:** MET on this pilot,
cleanly: A1 > A0 in 2/2 seeds, A2 > A0 in 2/2 seeds. A3 (dormant only, re-feed kept) is NOT
consistently above A0 (1/2) — a useful specificity check the plan's own arm design was built to give:
it is the RE-FEED manipulation that moves turnover, not the dormant seed riding along with it, which
is exactly what D-0232's question is asking. **This reads as real signal even at n=2**, because the
comparison is *paired within-seed* (4 independent same-seed comparisons, all in the predicted
direction for the arms the hypothesis actually predicts) rather than 2 independent samples — but n=2
seeds is still far short of the pre-registered 20, and no seed here carried a tension block, so this
says nothing about tension-bearing nights.

**Threshold 1 (D-0231's defeater) — dormant_contact ≥ 0.30 in ≥ 1/3 of A2/A3 arcs:** literally MET,
4/4 (100%) of A2/A3 arcs clear 0.30. **But the plan's own instruction to also score the A0/A1 floor
against the same un-seeded fragment turns out to matter a lot here**: the floor (A0/A1, dormant
fragment never seeded) ALSO clears 0.30 in 4/4 arcs, and its mean (0.3583) is *higher*, not lower,
than the seeded arms' mean (0.3352). At this N, seeding the dormant fragment does not distinguishably
raise scene-to-dormant cosine above what an ordinary dream narrative already sits at against a
loosely-related cold fragment. **This is a genuine caveat, not just an underpowered-N problem**: 0.30
cosine may simply be a common similarity floor for this embedder (paraphrase-multilingual-MiniLM-L12,
384-dim) between any two moderately-related pieces of Du's own text, in which case the pre-registered
0.30 absolute threshold is not discriminating and D-0231's defeater condition should be re-read as "the
seeded-vs-floor DELTA, not the absolute threshold" before the fuller run is trusted either way.

## Limitations (disclosed)

1. **N=2, not 20.** Every number above is a very small sample; treat directionally, not as a settled
   read. Confidence recorded as `inferred`, not `verified`.
2. **Day-residue collision:** seeds 0–2 shared one day-block hash and seeds 3–5 shared another (only 2
   distinct day-residue conditions across the 6 frozen seeds, not 6) — the corpus's real fragment
   density near "now" is sparse enough that 1-day steps in `dream_lag_material`'s `now` did not always
   change its top-k window. A fuller run should space `now` further apart, or draw it from REAL
   historical `dream_log.jsonl` arc timestamps (once enough Phase-1-instrumented nights exist) instead
   of arbitrary daily offsets.
3. **No tension-bearing seed tested.** All 6 frozen seeds had 0 charged tension blocks; the ~1/4 of
   real nights that do carry a tension are untested here.
4. **The dormant_contact floor caveat above** — needs the fuller N before either D-0231 direction
   (cold-eligible vs warm-only, or retune the threshold to a relative delta) is safe to act on.
5. **No judge-panel shadow read** this pass (time budget).

## Pointers
- Script: `scripts/dream_experiment_a.py` (this worktree).
- Frozen seeds: `<scratchpad>\dream_exp_a_seeds_J1059_pilot6.json` (job-queue scratchpad, not committed
  — contains real fragment content, kept out of git deliberately).
- Full results (append-only, may have grown past 8 rows): `<scratchpad>\dream_exp_a_results_J1059_pilot6.jsonl`.
- Run log: `<scratchpad>\dream_exp_a_run_J1059_pilot6.log`.
- Finding: F-<see findings_log> (this session, J-1059).
- Decisions this bears on (NOT ruled by this job — see its own ground rules): D-0231 (dormant rule),
  D-0232 (dream shape).
