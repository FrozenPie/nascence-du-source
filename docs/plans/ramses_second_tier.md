# PLAN — the Ramses second tier

```plan-state
stage: live
phase: Tier layout FROZEN live (D-0101); a third recurring Judge1 (:11438) outage under live investigation, blocked on Travis pulling Ramses-side hub logs
verified: 2026-11-14
evidence_read: 2026-10-15
next: founder starts a fresh supervisor (Du down or via Control Panel) so J-2113 takes effect; J-2116 reads 72 h after that; the sitting-judge same-input A/B lab job (from F-2737) decides D-0354's revisit
cluster: 2
```


*Opened 2026-08-20. Status: 🟢 **LIVE, FROZEN 2026-08-30 (§5.6, D-0101) for the background/judge/dream
layout — the tier stays exactly as currently deployed for THOSE roles; no further reshuffling there
("we have shuffled too much," founder).** Standing layout: `falcon3:7b` @ :11436 (reserve, unwired) ·
`granite3.1-moe:3b` @ :11437 (judge tiebreak + curiosity worth-judge) · `mixtral:8x7b` @ :11438
(commitment defeater + dream primary) · `command-r7b` @ :11441 (background lane, sole 3070 tenant).
**UPDATE 2026-09-07 (D-0058 re-ruled via decide-review, F-1008): the Lane2/Witness seat MOVED OFF
command-r7b** — D-0101's "nobody is chasing that :11444 standup" line above is now stale; Ramses
(Antigravity) stood it up unprompted, it was independently verified ready, and the founder ruled to
move the Witness there now that the stopgap's own echo-disease defeater (F-0926) had also fired.
`core/lane2.py`'s `BASE_URL`/`MODEL` are repointed to deepseek-r1:7b @ :11444 (RESTART-REQ, not yet
picked up by Du's live process as of this note). D-0101's freeze itself was never about the Witness
seat specifically — that's always been governed by D-0057/D-0058, not by this plan's own §5.6 — so
this move does not violate the freeze; the freeze's background/judge/dream layout is untouched.
History: D-0056 §5.4 retired ollama after the 08-27/28 lock (F-0389) and move 1's silent /v1 404
(F-0392); D-0057 §5.5 consolidated the background lane onto command-r7b that evening; D-0058 same
evening stop-gapped the Witness onto it too, then moved off it 2026-09-07 — see §5.6 for the full
freeze and `docs/plans/lane2_the_witness.md` for the Witness seat's own history.
Companion to `docs/transit_timetable.md` (the station layer) and `deploy/ramses/` (the standup package).*

> **History folded** — 2 dated Current State section(s) (2026-08-27 … 2026-09-03) moved to `docs/plan_history/ramses_second_tier.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py ramses_second_tier`.

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/decoupled_judge_pattern.md` — its shipped shadow judges (dream
resolution, active-imagination novelty) call `core/judge_panel.py`'s `rule_detail()`, so they land on JUDGE_1 `:11438` and
TIEBREAK `:11437` like every other panel caller, and the rule there is one decoupled judge per subsystem, built bottom-up.
Count them when reading `:11438` contention (D-0297 puts Lane 2 at 67% of panel-call volume; these sit in the remainder).

## 0. THE PROBLEM, as measured — not as assumed

Three findings from 2026-08-20, all from instruments rather than inference:

1. **The station load is inverted against the hardware.** 17 LLM stations sit on the 3070's **8192**
   window (including `_author` at 1400 tokens and `_think` at 1600); 11 sit on the 1080 Ti's **24576**
   window (including a temp-0.1 solve). `docs/transit_timetable.md` §1.
2. **The 1650 Super is already serving, undirected.** Resident VRAM on Ramses was pushed to
   **9.82 GB** against a 3070 that is 8 GB. Ollama has been spreading across both cards by load order,
   not by design — and the 4th model partially spilled to system RAM, locating the ~10 GB ceiling.
3. **The i9-11900K and its 48 GB are genuinely idle.** Nothing serves on Ramses but `:11434`.

**So the diagnosis is not "not enough resources." It is "nobody is allocating."** That is the same
finding as the missing signal box in the timetable, one layer down the stack: no dispatcher decides
which station runs where in software, and ollama decides which card by arrival order in hardware.

### A correction that shapes this plan
An earlier draft proposed `qwen2.5-coder:14b` on the i9 as "~4x phi3:mini's parameters." **It is a
CODER model**, as is `qwen3-coder:30b` — the only two large models on Ramses. Both are a poor fit for
the synthesis and reflection stations this tier is meant to serve. The largest **general** model
already pulled is `deepseek-r1:8b` (5.23 GB). So the zero-download upgrade is 3.8B → ~8B, not 14B+.
A real large-model jump requires pulling one (Phase 1c), and that should be an explicit decision, not
a side effect.

## 1. WORKING METHOD — how we operate on Ramses

The founder has access to Ramses and can put **Claude Code** on it. That dissolves the standup
friction (no SSH — tried and failed; no SMB — enumeration errors 1702).

**Two sessions, one contract.** The Ramses session does standup and verification ON Ramses. The
Nascence session (this one) owns Du's code and the wiring decisions. They meet at one interface: an
HTTP endpoint that either answers `/api/tags` or does not.

- **Ramses Claude never edits Nascence code.** It has no repo and no context for the laws that govern
  it (erosion, decoupled judge, shadow-first). Its job ends at "the hub serves."
- **Nascence Claude never assumes the hub works.** It verifies from here with a real call before
  anything points at it.
- Antigravity is on Ramses but is **not** to be used for this (founder's standing position since its
  upgrade — see `project_antigravity_off_project`).

**Getting the files there** — three options, cheapest first:
1. Ramses Claude writes them from the spec (they are ~200 and ~20 lines).
2. Serve them briefly from the Nascence box: `python -m http.server 8123` in `C:\Nascence`, then
   `curl http://10.1.1.47:8123/scripts/nascence_cpu_server.py -o ...` on Ramses. Stop the server after.
3. Manual copy.
Option 2 is exact and reversible; option 1 risks drift from the real file.

## 2. PHASES — and what each one is gated on

### Phase 0 — collect the data (runs in PARALLEL; blocks Phase 2, not Phase 1)
Du restarts with the instruments already built and runs for a day.

- Read `telemetry.job_status()` (HUD `prompt_jobs`) for **`cap_rate` per station**.
- **The pre-registered question:** do `inner_monologue_node:3660` / `:3676` (the 1100/1400-token
  authoring stations on the 3070's 8192 window) show a non-zero `cap_rate` while the 1080 Ti's
  stations sit near 15% utilisation?
- **If yes** — re-platforming is justified and Phase 2 targets those first.
- **If no** — the inversion is ugly but harmless, and Phase 2 shrinks to the classifier stations only.
  **Say so and do less.** This is a real possible outcome, not a formality.

Nothing in Phase 1 requires Du to be stopped, so standup proceeds while this runs.

### Phase 1a — the i9 CPU hub (do first; lowest risk, no GPU involved)
`deploy/ramses/` is written and ready. **BENCHMARKED 2026-08-20 — see `docs/lab/node_benchmark.md`.**

The open uncertainty ("30 seconds or 300?") is closed, and it needed no Ramses-side setup: ollama's
`num_gpu: 0` forces CPU offload, so the i9 was measured through the endpoint already serving.

| node | model | tok/s | warm wall | finishes? |
|---|---|---|---|---|
| Ramses i9 CPU | `llama3.1:8b` | **6.94** | **8.7-11.2s** | **yes, 3/3** |
| Ramses i9 CPU | `deepseek-r1:8b` | 6.44 | 47s | **NO, 0/3** |
| Ramses i9 CPU | `qwen2.5-coder:14b` | 3.76 | 27.8-36.1s | yes |
| Local Threadripper | `llama3.1:8b` | ~7.4 | 9.9-12.1s | yes |
| Ramses 3070 GPU | `deepseek-r1:8b` | 47.6 | 6.5s | (capped) |

**Verdict: VIABLE.** ~10s per complete answer against 600-2700s clocks is a ~2% duty cycle, and the
i9 runs at **~94% of the Threadripper tier Du already depends on**.

**MODEL CORRECTED to `llama3.1:8b`.**

> **★ THIRD CORRECTION (2026-08-20, station matrix — `docs/lab/station_matrix.md`): `llama3.1:8b` is
> VETOED for this tier by task fitness.** The throughput benchmark chose it (6.94 tok/s, valid JSON
> 3/3) — but the i9 hub's intended payload is the Deep Line's SYNTHESIS stations, and the matrix
> measured `llama3.1:8b` as the **worst integrator of all 33 models: 0.05 coverage** (a fluent insight
> touching almost none of the seven specifics — the reality-thin failure mode). Fast at the wrong job.
>
> **Current pick: `mistral:7b-instruct`** — synthesise coverage 0.71, judge accuracy 1.0 (discriminates,
> `FTFT`), non-reasoning (no thinking-tax on CPU), same size class (4.37 GB vs 4.92). **Throughput verified on the actual i9
> (2026-08-20, num_gpu:0 through the live endpoint): 7.40 tok/s, valid JSON 3/3, ~17-22s per
> synthesis-shaped answer — FASTER than the vetoed llama3.1:8b's 6.94.** The fitness pick costs
> nothing in throughput; it is strictly better on both axes. Gate closed.

> **⚠ FOURTH correction required before wiring (2026-08-21): the mistral pick has a PLATFORM problem.**
> Overnight the local judge panel was 100% unavailable (114/114) because **hub-mistral does not hold
> JSON key contracts on the llama-cpp serving stack** — it wraps verdicts in `{"assistant":...}` shells.
> Its throughput here was verified via OLLAMA `num_gpu:0`, but Phase 1a SERVES via the same
> `nascence_cpu_server` hub stack that just failed locally. Before seating any model on the i9 hub,
> **audition it with the target contracts ON the hub platform** (the probe script pattern:
> panel/defeater/librarian keys). Local audition result for reference: `falcon3:7b` held 4/4 contracts
> + both defeater golds on the hub and now holds local judge-2. Quality option to speed-test alongside:
> `command-r7b` (0.86 coverage, Cohere lineage — also serves judge-independence).
>
> The sequence of corrections is itself the lesson: coder-tuned → lab-winner-on-wrong-platform →
> throughput-winner-at-wrong-job. **A model is chosen per (model, station, platform) triple, and every
> single-axis benchmark so far picked wrong.** This plan previously specified `deepseek-r1:8b` on the strength
of its Lane 2 lab win. That lab measured quality **on a GPU**, where its reasoning cost 6.3s. On CPU,
reasoning tokens *are* generated tokens: deepseek burned its full budget thinking and produced no
valid JSON on 3/3 runs; at the ~1400 tokens it needs that is **~218s per call** versus llama3.1's
~10s. **A lab result does not transfer across a platform change.**

- `pip install llama-cpp-python fastapi uvicorn` — **RISK:** on Windows this may want MSVC build
  tools if no prebuilt wheel matches the Python version. If it fights, that is the whole Phase 1a
  risk and it surfaces in the first five minutes.
- Copy `nascence_cpu_server.py` + `resolve_blob.py` + `launch_ramses.ps1`, run the launcher.
- **Model:** `deepseek-r1:8b` (5.23 GB) — largest general model already present, and it won the Lane 2
  model lab outright (`docs/lab/lane2_model_lab.md`). Note it is a REASONING model: it needs a large
  `num_predict` and emits JSON in a fenced block. `core.lane2.parse_json_loose` already handles both;
  anything else pointing at this hub must too.
- `--lazy --idle-unload 900`, `--threads 14` (i9 is 8C/16T — leave headroom for ollama on `:11434`).
- **Port 11436.** Verified free.
- **Exit test:** `curl http://LAN-HOST:11436/api/tags` answers from the Nascence box.

### Phase 1b — the 1650 Super hub (harder; needs a CUDA build)
- Needs CUDA-enabled `llama-cpp-python` on Ramses. This is the real toolchain job.
- `nascence_cpu_server.py --gpu-layers 99` (flag added 2026-08-20, default 0 so local hubs are
  unchanged). **All layers or none** — partial offload is precisely the CPU/GPU split the founder
  avoids llama.cpp-less setups for.
- 4 GB fits `llama3.2:1b` (1.32) or `gemma:2b` (1.68), both already pulled.
- **Port 11437.**

### Phase 1b-bis — pull NEW model FAMILIES (founder, 2026-08-20: "even more families to work with")

Not variety for its own sake. **Family diversity is already load-bearing here**: `judge_panel` pairs
llama3.1 with qwen2.5 deliberately, and `core/lane2.py` picked deepseek explicitly because a
same-family checker is a rubber stamp (self-preference bias). But every model in play today is a
transformer trained on heavily overlapping web corpora — llama, qwen, gemma, phi, mistral, yi,
deepseek. The decoupled-judge principle is currently **nominal**: two judges that share blind spots
agree for the wrong reason, and `split_no_tiebreak` cannot tell that from real consensus.

Genuinely distinct lineages worth pulling (full table + rationale in
`deploy/ramses/RAMSES_CLAUDE_BRIEF.md` §4):

- **Cohere `command-r7b`** — built for grounded generation; most lineage-distinct option available.
  **UPDATE 2026-08-23:** already pulled and live on port 11441, serving for `epistemics_phase_c.md`'s
  Tier-3 witness work (verified via `Test-NetConnection` + `/api/tags`) — ahead of this plan's own
  gate, which still requires it win a lab task before being adopted here. The two uses are separate:
  epistemics_phase_c consumes it directly for cross-model verification; this plan's "genuinely
  distinct lineage" case for wider adoption is still open.
- **IBM `granite3.1-dense:8b`** — enterprise data mix unlike anything present
- **AI2 `olmo2:7b`** — fully open training data, genuinely independent
- **`mixtral:8x7b`** for the 48 GB CPU — MoE with ~13B active params/token. **Now backed by measured
  scaling** rather than reputation: the i9 does 6.94 tok/s at 8B and 3.76 at 14B (ratio 0.54 against a
  parameter ratio of 0.57 — near inverse-linear), which extrapolates to **~4.3 tok/s for mixtral's 13B
  active** (~30s per answer, viable) versus **~1.85 tok/s for a dense 30B** (~70-160s, marginal).
  A dense 30B on this CPU is a poor trade; the MoE is the one that works.

**Gate:** a new family earns a place by winning a lab on a real task, the way `deepseek-r1:7b` did in
`docs/lab/lane2_model_lab.md` — not by being new. `scripts/lane2_model_lab.py` already does exactly
this and re-scores from saved raw data, so adding candidates is cheap and the comparison stays honest.

### Phase 1c — pull a large general model? (DECISION, not a task)
48 GB of idle RAM can hold a 32B. Nothing that size and general is on Ramses today. Pulling one
(~20 GB) is a deliberate choice with a real download cost, and it should follow Phase 1a proving the
hub serves at all. **Do not bundle this into 1a.**

### Phase 2 — move stations (GATED on Phase 0)
Candidates, in confidence order:

| Move | To | Gate |
|---|---|---|
| 6 classifier stations (`peers:489` 40tok/0.0, `librarian:78` 120/0.0, `commitment_ledger:348` 150/0.2, `deliberation:145` 200/0.1) | 1650S (1b/2b model) | Phase 1b up. **Ungated by cap_rate** — these are classification wearing a chat interface and the case does not depend on truncation |
| Deep Line synthesis (`_t2_synthesise`, `_t5_compile`, `_synthesise_theme`, `_self_relate_check`) | i9 CPU hub | Phase 1a up. Their clocks are 600–2700s, so CPU latency is irrelevant |
| `_author` 1100/1400tok, `_think` 1600tok | 1080 Ti — **or** stay | **Only if Phase 0 shows truncation.** The 1080 Ti is `MAX_LOADED=1` and deliberately exclusive to gemma; that exclusivity ended the July eviction disease. Do not reopen a closed wound on a hypothesis |

Each move is one entry in `SERVE_CHAINS` plus a lane change at the call site. **One at a time, with a
day between**, so a regression has an unambiguous cause.

### Phase 3 — the signal box (design, not yet scoped)
The Deep Line wakes every 30s; the Idle Line fires after 75s of quiet; both do heavy work on the same
platform and **neither knows the other exists**. Phases 1–2 add capacity, which makes contention less
likely but does not make it *managed*. Distinct from the planned Transport Manager: that dispatches
**freight by novelty**, this dispatches **trains by contention**. Shadow-first if built.

## 3. RISKS

| Risk | Mitigation |
|---|---|
| **`MAX_LOADED=1` is NOT armed on the local hot lane** (found 2026-08-20: phi3 loaded alongside pinned gemma — 8.66/11.26 GB). `launch_servers.ps1`'s env vars only apply if IT started ollama; the running instance was not started by it | Restart ollama once via `launch_servers.ps1` to adopt them. Nothing broke (both fit), but a third model would evict gemma — the original July failure |
| `llama-cpp-python` won't install on Ramses (Windows/MSVC) | Surfaces immediately; Phase 1a is otherwise cheap. Fall back to a second pinned ollama for 1b only |
| The new hub becomes a new SPOF | Every consumer must fail open. Ramses already naps — `left_lane` fail-opens correctly and now logs `repr(exc)` so the cause survives |
| i9 hub starves ollama on `:11434` | `--threads 14` of 16, `--lazy`, `--idle-unload 900` |
| 48 GB exhausted | Same RAM rule as the local tier: lazy hubs, one model each, idle-unload |
| Re-platforming on a hunch repeats July | Phase 2's heavy moves are gated on `cap_rate`; classifier moves are not, because their case is independent |
| Two Claude sessions drift | Ramses Claude's remit ends at the HTTP endpoint; it never edits Nascence code |

## 4. OPEN — founder decides

1. **Phase 1c** — pull a large general model onto Ramses, or stay with `deepseek-r1:8b`?
2. **File transfer** — the brief HTTP server (exact) or have Ramses Claude write the files (risks drift)?
3. **Ordering** — Phase 1a alone first, or 1a+1b together? (1b's CUDA build is the only hard part in
   the whole plan; doing it second keeps a working hub as the fallback.)
4. **Phase 3** — scope the signal box now, or after the tier is live and we can see whether added
   capacity made contention moot?
5. **[2026-08-24, J-0191/F-0176/D-0039] Item 4 got its first real data point, and it's a live "yes"
   for contention — before the tier is live.** `judge_panel`'s existing local CPU-tier hubs (JUDGE_1
   gemma4:12b :11439, JUDGE_2 falcon3:7b :11440 — the exact pattern this plan's "no dispatcher decides
   which station runs where" diagnosis describes, one layer down) hit ~66-80% `how=unavailable` across
   a real ~90-minute overnight window. Root cause confirmed by reading `nascence_cpu_server.py`: each
   hub serializes every request (idle-reload + inference) through ONE `asyncio.Lock` — a concurrent
   burst right after an idle-unload reload queues requests behind each other, and `judge_panel.py`'s
   `TIMEOUT_S=90` turns a queued-but-alive hub into a false "unavailable" verdict. This is the SAME
   under-capacity symptom this plan exists to fix, now measured on the tier that already exists — real
   evidence for whichever way D-0039 (raise the CPU-tier timeout vs. cap/stagger concurrent overnight
   sessions per the standing "3 at a time was tried and was too much" ruling) gets ruled, and for how
   urgently Phase 1+ capacity is needed. See F-0176 (findings-log) and D-0039 (decide) for full evidence.
   Built as part of this: `judge_panel.status()` now reports `unavailable_rate`/`v1_null_rate`/
   `v2_null_rate` + a recent-50 sub-summary, wired into `scripts/du_pulse.py` — so the NEXT contention
   spike (on this tier or the future Ramses one) is visible in the pulse instead of requiring a raw-log
   read by hand.

6. **[2026-08-24, J-0214/F-0287] D-0039's "wait and see, check Antigravity's Ramses notes" premise
   is DEFEATED — reopened.** The founder recalled infra issues around 2026-08-24 01:00–03:00 that
   Antigravity might have written up and possibly already fixed. Checked both halves of that lead:
   - **Antigravity's channel has nothing.** `\\ramses\D\Du\NASCENCE_NOTES.md` and every file in that
     shared folder are untouched since **2026-08-23 13:34 NZST** — over 12 hours before the window in
     question. No note, no fix, nothing written about it.
   - **The real local event is a different bug on different hardware.** `data/nascence.log` shows a
     real incident 02:22–02:56 (`TimeoutError`/`ClientConnectorError('network name no longer
     available')` against `127.0.0.1:11439`, briefly `:11442`), with the **local** `cpu_tier_1143x`
     hub processes visibly restarted 02:42–02:49 (`.log.err` files rewritten within 5s of each
     other). But `core/deliberation.py:13` confirms JUDGE_1/JUDGE_2 (`:11439`/`:11440`) were
     **"repointed off Ramses" onto `127.0.0.1` back on 2026-08-20** — 4 days before this incident.
     Antigravity has no visibility into or role in this tier; it lives entirely on the local box.
   - **And the restart didn't even fix D-0039's actual symptom.** After 02:49, connection-refused
     errors stopped, but plain `TimeoutError` (`judge_panel.py`'s `TIMEOUT_S=90` firing on a
     queued-but-alive hub — D-0039's exact mechanism) recurred at 03:11/03:25/03:27/03:50/03:52/
     03:54/03:56.

   **D-0039 reopened** — the founder still needs to choose between option A (raise the CPU-tier
   timeout) and option B (cap/stagger concurrent overnight sessions); neither is resolved by anything
   Antigravity did, because Antigravity did nothing here. Full evidence: F-0287 (findings-log).

---

## 5. THE 2026-08-27 REDISTRIBUTION DRAFT (J-0303, per D-0044) — founder review required

### 5.1 Verified hub inventory (probed live this session, `/api/tags`, 2026-08-27 evening)

| Hub | Hardware | Serving | State | Today's consumer |
|---|---|---|---|---|
| `local:11433` | 1080 Ti 11GB | 40-model ollama; primary `qwen3.5:9b` | **UP** | Hot lane / Self — 8,533 calls, mean 10.1s, 0.7% fail |
| `local:11439` | local CPU | `gemma4:12b` | down (Du's stack stopped) | JUDGE_1 — 318 calls, 14.0s, 1.6% |
| `local:11440` | local CPU | `falcon3:7b` | down (Du's stack stopped) | JUDGE_2 — 221 calls, 9.1s, 0.9% |
| `local:11442` | local CPU/offload | `yi:34b-v1.5` | down (Du's stack stopped) | Dreamer + judge tiebreak — 227 calls, **184s mean, 16.3% fail** |
| `ramses:11434` | Ramses general ollama | many (incl. `phi3:mini`) | **UP** | Background lane — 3,784 calls, 4.7s, 0.1% |
| `ramses:11436` | Ramses CPU | `falcon3:7b` | **UP, idle** | none (nothing wired — by design) |
| `ramses:11437` | 1650 Super 4GB | `granite3.1-moe:3b` | **UP, idle** | none |
| `ramses:11438` | Ramses CPU | `mixtral:8x7b` | **UP, idle** | none |
| `ramses:11441` | 3070 8GB | `command-r7b` | **UP, idle** | none |

Load figures: full `data/llm_latency.jsonl` read, 13,083 rows, 2026-08-20 → 08-27.

### 5.2 Proposed moves — each gated on the JSON-contract audition (§1's law; the `mistral:7b-instruct` lesson)

1. **Commitment judge/defeater → `mixtral:8x7b` @ ramses:11438** (J-0281, already queued; 08-25
   benchmark: mixtral beats phi3:mini on this judgment). Low volume, so mixtral's CPU latency is
   acceptable. *This settles D-0044's judge-model question inside the plan, per its defeater.*
2. **Dream synthesis off `yi:34b` @ 11442** — the worst profile in the fabric (184s, 1-in-6 fails;
   F-0381). Audition **`command-r7b` @ ramses:11441 (3070, GPU)** as primary candidate, `mixtral`
   @ 11438 as second. Keep yi:34b as explicit fallback. Expected: mean minutes → tens of seconds,
   failures → ~1%. The dream pipeline is untimed background work, so even a modest model on GPU
   dominates a 34B on CPU offload.
3. **Judge tiebreak off `yi:34b` @ 11442 → `command-r7b` @ ramses:11441** — a genuine third family,
   GPU-fast. Today the tiebreak shares the dreamer's slow CPU hub, which is exactly where D-0039's
   false-unavailable spiral lived. (If dream synthesis also lands on 11441, that's fine — both are
   low-volume; or put tiebreak on `granite3.1-moe` @ 11437 as the third-family alternative.)
4. **JUDGE_2 `falcon3:7b` → ramses:11436 (the dedicated falcon3 hub)** — same model, different box:
   cuts local CPU contention and the single-request serialization behind D-0039. Audition + shadow
   first; JUDGE_1 (`gemma4:12b`) stays local.
5. **Background lane stays `phi3:mini` @ ramses:11434** — 3,784 calls at 4.7s/0.1% is healthy; only
   the commitment-judge subset moves (item 1). No change to the hot lane (`qwen3.5:9b` @ 11433).
6. **`granite3.1-moe` @ 11437 held in reserve** — no consumer assigned; candidate for future light
   classification lanes. Do not wire something to it just because it is idle.
7. **New consumer to seat (added 2026-08-27 evening):** the B1 **dwell-release judge**
   (`core/sitting.py judge_dwell_release()`, built J-0300/F-0382, fires per idle thought while
   dwelling — low volume, judgment-shaped). Assign it a node at wiring time; natural candidates are
   the background lane (:11434) or the reserve granite hub (:11437) — pick by the same audition.
8. **Config consolidation sweep during wiring** (from F-0381): six core files still carry
   `qwen2.5:7b` strings (`lane2.py`, `left_lane.py`, `model_client.py`, `schema.py`, +2), three
   carry hardcoded `11441`, odd ports `11460`/`11470` appear in 2/1 — classify each as live
   default / dead fallback / stale while touching the routing, not as a separate blind sweep.

### 5.3 Sequencing and the restart gate

**FOUNDER RULED + MOVES 1–3 WIRED, 2026-08-27 evening:** Travis approved command-r7b for both the
dreamer and the tiebreak, moves 1–3 as the restart gate, "then we look at doing more." All three
auditions passed on the real hubs with the real contracts (tiebreak boolean+why 10.2s with a correct
refusal; defeater legitimate/class/why 24.9s with a correct "everything flows" rejection; dream
schema fully populated 21.3s vs yi's 184s mean). Wired same session, py_compile + import-verified:
- Move 1: `core/schema.py` SERVE_CHAINS +`judge_mixtral` → ramses:11438; `core/commitment_ledger.py`
  `_judge_defeater` uses it (background-lane fallback preserved). J-0281 done.
- Move 2: `nodes/dream_node.py` `_DREAM_URLS` → [ramses:11441, local:11442-failover],
  `_DREAM_MODEL="command-r7b"`, `_DREAM_NUM_GPU=None`. Follow-up: J-0305 (dream_arc_eval re-run).
- Move 3: `core/judge_panel.py` `TIEBREAK` → ramses:11441 (the Ramses GPU hub — the 08-20 local-
  capacity ruling that retired the *local* :11441 does not bind a Ramses hub).

**The restart gate is MET.** Moves 4–8 remain drafted-not-wired, to be looked at after Du is back
and the first live days confirm 1–3. First-days watch list: dream latency/failure on :11441
(expect tens of seconds, ~1% fail), tiebreak `unavailable` rate (D-0039's instrument), commitment
defeater verdicts carrying mixtral's `why` strings.

### 5.4 THE 2026-08-28 CORRECTION — ollama off Ramses (D-0056, founder-ruled, wired same session)

The 08-27 placement survived one night. Two independent failures found 2026-08-28:

1. **F-0389 (the 3070 lock):** §5.1's inventory listed `ramses:11434` ("general ollama") and
   `ramses:11441` ("3070 8GB") as if separate hardware — but ollama's residents (phi3:mini ~3.9GB +
   deepseek-r1:7b ~5GB, Lane 2) live ON the 3070 (NASCENCE_NOTES 08-23 nvidia-smi: 7918/8192MiB).
   Moves 2–3 added command-r7b (~5GB) to the same card. No pairing of the three fits 8GB. Overnight:
   dream calls to :11441 failed 210/300/300s, phi3 @ :11434 failed 121s (llm_latency.jsonl, ok:0).
2. **F-0392 (move 1 never worked):** `model_client.py`'s ollama-style port list lacked `:11438`, so
   `judge_mixtral` calls fell to `/v1/chat/completions` — HTTP 404 on the hub (verified live). Every
   commitment-defeater call since 08-27 silently failed open to None.

**Founder ruling (D-0056):** ollama retired from Ramses entirely (stop + disable, keep install/blobs).
The relayout, all auditioned with real contracts before wiring:

| Workload | Was (08-27) | Now (08-28) | Audition |
|---|---|---|---|
| Background lane (phi3:mini) | Ramses ollama :11434 (3070) | **new llama.cpp hub :11443, 3070 SOLE tenant** | pending hub standup (same model, same ctx 4096) |
| Judge tiebreak | command-r7b :11441 (3070) | **granite3.1-moe :11437 (1650)** — §5.2's own named alternative, third family (IBM) | PASS: correct refuse 4.3s + correct accept 1.0s, coherent whys |
| Dreams | command-r7b :11441 (3070) | **mixtral :11438 (i9 CPU)** — §5.2's own second candidate; yi :11442 failover kept | PASS: 52.9s, full schema, valid movement (vs yi 184s mean) |
| Lane 2 (deepseek-r1:7b) | Ramses ollama :11434 | **PAUSED** (`lane2.LANE2_PAUSED=True`) — no Ramses GPU can hold it beside phi3 | J-0310 (needs founder ruling to re-seat or close) |
| command-r7b :11441 | dreams+tiebreak | **manual-only reserve, out of the default launcher** | — |

Code: `core/schema.py` (background → :11443), `core/model_client.py` (port-list fix incl. :11436-38
+ :11443 entries + truthful hub model labels for telemetry), `core/judge_panel.py` (TIEBREAK),
`nodes/dream_node.py` (_DREAM_URLS/_DREAM_MODEL), `core/lane2.py` (pause gate). All py_compile-clean.
Ramses-side tasks handed to Antigravity via NASCENCE_NOTES.md (08-28 entry). Follow-ups: J-0308
(dream_arc_eval vs mixtral, supersedes J-0305), J-0309 (post-standup fabric verification — includes
the F-0392 proof: first-ever mixtral `why` strings), J-0310 (Lane 2 re-seat).

### 5.5 THE 2026-08-28 EVENING CONSOLIDATION (D-0057, founder-ruled, wired same session)

Hours after §5.4, the founder challenged phi3's necessity ("why not command-r7b for all this?").
The honest answer: phi3's original selection reason (smallest model that co-fits a shared card) died
when the card went single-tenant — what remained was incumbency. Evidence gathered before ruling:

- **Witness lab vs command-r7b** (`docs/lab/lane2_model_lab_command_r7b.md`, harness/prompt = today's
  live versions): score **0.875** — 2nd place behind deepseek's 0.932 (perfect JSON, zero hedging,
  but distinct 0.833 with visible echo + static 0.167). Founder: deepseek keeps the Witness.
- **Background contract auditions vs command-r7b @ :11441**: drift-recall PASS (anchor survives),
  T2 synthesis PASS (style rules held), dream schema PASS (earlier same day). One FAIL that turned
  into a bigger find: curiosity_worth returned 0.0 for everything — and so did the LIVE incumbent
  phi3 on its own contract (**F-0396**, the schema-example parrot trap; both models copied the
  literal `0.0` example). Fixed with placeholder schema; granite @ :11437 auditioned best on the
  fixed prompt (0.8/0.0/0.8 with real reasons) and takes the station — which also cures a quiet
  self-judging smell (the background lane was grading its own lane's curiosity questions).

**The ruled layout (final):** 3070 = **command-r7b :11441, background lane, sole resident** (phi3
hub :11443 cancelled unbuilt) · witness deepseek → **planned i9 hub :11444**, `TICK_S` 90→300
(measurement-choice change — flag when reading `lane2_shadow.jsonl` across the boundary), lane2
PAUSED until :11444 verifies · worth-judge → **granite :11437** · dreams/tiebreak/defeater unchanged
from §5.4. Code: `schema.py`, `model_client.py` (incl. :11444 planned entry), `lane2.py`
(URL/tick/pause), `curiosity_worth.py` (placeholder schema + `_JUDGE_URLS`). All py_compile-clean.
Follow-ups: **J-0314** (single consolidated verification job — supersedes J-0309/J-0310/J-0312),
J-0308 (dream_arc_eval), J-0311 (dwell judge re-seat, unaffected). Audition coverage caveat is in
D-0057's defeater: 3 of ~13 background contract shapes were auditioned; the rest are watched live.

**J-0305 arc-eval verdict (2026-08-28, F-0391):** `scripts/dream_arc_eval.py` re-run against
command-r7b @ :11441 (2 arcs × 3 scenes; judge llama3.1:8b + embed nomic-embed-text @ ramses:11434):
schema **1.00** and JSON **6/6** meet the mistral-small3.1 bar; rich 1.0; mean scene latency
**21.9s** (17.5–27.6s) vs yi's live 184s mean / 16.3% fail. **Below the bar on develop: 3.5 vs
4.5** (arcs 4.0/3.0); transform 0.09 / opening 0.32 (mistral's transform/opening were never
recorded, so no direct comparison there). No revert trigger — no schema collapse, no 1-scene arcs,
no JSON failures — command-r7b stands as primary, yi:34b stays failover. Adds *dream develop /
imagery movement* to the first-days watch list: if live dreams read as re-rendered scenes rather
than moving arcs, the revert is one line (`_DREAM_URLS` order).

**J-0308 arc-eval verdict (2026-08-29, F-0532, supersedes J-0305 — dreamer moved to mixtral per
D-0056):** `scripts/dream_arc_eval.py` re-run against **mixtral:8x7b @ ramses:11438** (2 arcs × 3
scenes; judge llama3.1:8b + embed nomic-embed-text @ ramses:11434, both confirmed live via
`/api/tags` before running): schema **1.00** and JSON **6/6** meet the mistral-small3.1 bar; rich
1.0. **Below the bar on develop: 4.0 vs 4.5** (arcs 4.0/4.0) — short of the bar, but **+0.5 over
command-r7b's 3.5**. transform 0.19 (arcs 0.15/0.22) / opening 0.34 — no mistral-small3.1 baseline
for either, but both beat command-r7b's 0.09/0.32. No revert trigger — no schema collapse, no
1-scene arcs, no JSON failures — consistent with the passing contract audition (52.9s, full schema,
valid movement, §5.4). mixtral stands as primary dreamer; yi:34b @ :11442 stays failover. Same
develop/imagery-movement watch item as J-0305 carries forward — the revert is still one line
(`_DREAM_URLS` order).

### 5.6 THE 2026-08-28/30 STOPGAP + FREEZE (D-0058, D-0101) — never previously recorded in this plan

**Gap found 2026-08-30:** D-0058 was ruled the same evening as §5.5's D-0057 consolidation, but this
plan doc never got updated with it — a session revisiting J-0314 (below) caught the drift between
what the plan said ("final") and what `core/lane2.py` actually runs.

**D-0058 (2026-08-28, founder, in-session):** "Yes, I want it on command for the moment. We will
look another time at changing it to deepseek." Stopgap seat for the Witness while :11444 (the D-0057
deepseek/i9 hub) remained unbuilt: `LANE2_PAUSED` flipped `False`, Lane 2 runs on `command-r7b @
:11441` — the same hub as the background lane — instead of staying paused for :11444. Accepts the
known quality gap (command-r7b 0.875 vs deepseek 0.932, `docs/lab/lane2_model_lab_command_r7b.md`)
and shared-hub contention, in exchange for the Witness ticking that day instead of waiting on
Antigravity. **D-0057's deepseek preference was deferred, not overturned** — its defeater: revisit
when :11444 answers a real verification call, or sooner on echo-disease/contention symptoms.

**D-0101 (2026-08-30, founder, in this session):** "For the moment, llms are staying as they are. We
have shuffled too much." Generalizes D-0058's Lane2-specific stopgap into a freeze across the whole
tier — no further Ramses model/port changes are being actively pursued, :11444 included. Full ruling
+ defeater: `python decide.py show D-0101`.

**Consequence for J-0314:** that job's entire premise (wait for Antigravity's `NASCENCE_NOTES.md`
report on the :11444 standup, THEN flip `LANE2_PAUSED`) was already moot before this session even
started — the flag has been `False` since D-0058, un-gated on :11444, and D-0101 confirms nobody is
chasing that standup. **Closed done, superseded by D-0058/D-0101, not by anything Antigravity did.**

**Standing layout, current as of this freeze** (matches `core/model_client.py`'s `_PORT_MODEL` table
exactly — check that file directly if this ever needs re-verifying):

| Port | Model | Role(s) |
|---|---|---|
| `:11436` | `falcon3:7b` | reserve, unwired — by design |
| `:11437` | `granite3.1-moe:3b` | judge tiebreak (`core/judge_panel.py`) + curiosity worth-judge (`core/curiosity_worth.py`) |
| `:11438` | `mixtral:8x7b` | commitment defeater (`core/commitment_ledger.py`) + dream primary (`nodes/dream_node.py`, yi:34b @ :11442 failover) |
| `:11441` | `command-r7b` | background lane, sole 3070 tenant (`core/schema.py`) + Lane2/Witness (D-0058 stopgap) |
| `:11444` | `deepseek-r1:7b` | **not live** — D-0057's planned seat, standup never happened, not being pursued (D-0101) |

## Current State — verified 2026-11-14
- **2026-11-14** (F-4684): J-3979 (D-0761 B) built in worktree commit 03d601ee: supervisor excuses read-phase timeouts under 2 GB free RAM; restart-gated. Part C is J-3980.

- **2026-11-14** (F-4615): J-2116 72h read of D-0420 B+D (463 supervised hours, 10-16 to 11-14): defeater clauses 1, 2, 3 fired; 4 and 5 clear. Snapshots identified free-RAM exhaustion (23 of 43 hot snapshots ram_avail<2GB; correction to F-4616: 9 of the 12 hot probes at or above 5 s fall in that set, not 8 of 9) as the cause of slowdowns. 11-07 08:09 hot_ollama restart was a false alarm (killed_pids=[], relaunch bind error). Decision D-0761 opened, RAM-consumer job spawned. supervisor.py untouched.
- **2026-10-30**: D-0341 re-check 10-30 (J-2103): Ollama.lnk still present but disabled in StartupApproved; no tray running, app.log unchanged since 10-08, no respawn loop across 4 reboots since 10-15; D-0341 defeater 1 not tripped

- **2026-10-16**: 2026-10-16: D-0341's intent is met -- Ollama.lnk is still in Startup but its StartupApproved registry flag is DISABLED (byte 3) and no tray process runs; Travis confirmed it only opens by hand. J-2103 keeps only its post-boot respawn-loop log half.
- **2026-10-16**: J-2105 / F-2871: same-input A/B of sitting judge on :11441 (60 inputs x2 arms x2 repeats): release G 55.0 vs N 65.0; between-arm agreement 75.0 not lower than within-arm 73.3 -> live rise not attributed to grammar; supports D-0419 (a). Not ruled.

- **2026-10-15**: D-0419 RULED (a) and D-0420 RULED B+D by travis (decide-review, session 192678f4, 2026-10-15). D-0354 stands unchanged (no-grammar-first on :11441; the sitting-judge A/B lab job decides any revisit). J-2113 built D-0420: supervisor hot_ollama probe two-phase (connect 3.0 s / read 10 s via HOT_READ_TIMEOUT + read_timeout spec key), slow-but-passed and 1/2 lines carry a bounded host snapshot; 2-consecutive rule and CPU hubs unchanged; tests 27/27 + observability 56/56; commits e652233/d324495. NOT LIVE until the founder next starts the supervisor (pid 16480 keeps 3.0 s). J-2116 = 72 h post-start defeater read.
- **2026-10-15** (F-2740): 2026-10-15 J-1942 / F-2740: the 72 h hot_ollama supervisor read (217.1 supervised h, 52,095 sweeps): 1 hot kill, a dead process (tray quit 10-08 08:47), 0 wedge kills, 0 false kills; 3 isolated timeout-read 1/2 failures all cleared by the 2-consecutive rule, the two with a log answered 200 at 2.995 s and 3.081 s inside a 13.5 min ollama slowdown (cause unidentified); the 10 s hub budget absorbed 8 dreamer probes of 3.0 to 5.8 s. D-0420 opened (widen the hot read-phase budget + log host snapshot on slow probes). Current :11433 ollama has no log (Control Panel Start-Process hidden).

- **2026-10-15** (F-2737): J-1876 read D-0354 defeater on 6 days of Du uptime of no-grammar-first :11441: parse-fail >10% for active_imagination 18.1% (149/822) and inner_monologue part writer 56.4% (66/117) = met; sitting-judge release 84.5% vs 64.3% prior (p=0.0006) = met, Curiosity q/call 2.99 vs 3.04 = not; timeouts 0.09% (was 17.5%) = passes; mean wall per call 7.4 s vs 39.1 s so D-0354 holds in substance; D-0419 opened, J-2105 A/B spawned
- **2026-10-15** (F-2733): J-1769 D-0341 follow-through read 10-15: Startup Ollama.lnk STILL PRESENT (Travis's action not done), tray not running since 10-08 08:47, no respawn loop (app.log 11 KB, 0 'ollama exited' vs 227,877 baseline; one clean supervisor restart 10-08, killed_pids=[]); defeater (1) not tripped.

- **2026-10-08** (F-2625): J-1850: essay backfill cleared the last 5 pre-live_since books (essayed 132->137, backlog empty).
- **2026-10-08** (F-2589): J-1967 (F-2589): D-0387 only half done - tray exited 10-08 08:47, 0.35.1 on GPU via Control Panel ollama, but Startup Ollama.lnk still present (v0.40.0 applies at next tray start); decision opened.

- **2026-10-07** (F-2563): J-1729 read the first 4 calendar days of data\logs\supervisor_events.log (10-03 23:25 -> 10-07 23:34; 80 lines, all read): only ~39 h of real supervision (4 segments, each starting/stopping with a Du run; 9,321 sweeps), ~37 h Du-live incl. 4 clean farewell quit-sleeps. hot_ollama: 0 kills, 0 slow-but-passed, hourly failed=0 and late_max=0.0s in all 39 summaries, worst probe 1.394 s vs the 3.0 s budget (a daily ~22:06/~08:55 /api/tags stall, gone in the 10-07 run); the single failed probe (10-05 11:45:49 err=refused) was a whole-tier teardown with Du down, 10 min before a Windows Update reboot. No slow-but-alive kill -> the hot-lane timeout-tolerance /decide is NOT opened; D-0194's defeater still unfired; F-2280's wedge-vs-starvation question stays open on evidence. J-1942 re-reads once cumulative supervised time passes 72 h. Side finding F-2564: D-0341 option C is still not done - Ollama.lnk present, the tray app owns :11433 again since the 10-06 boot (seg4 adopted its child), and it has v0.40.0 auto-update downloaded; 0.35.1 drives the 1080 Ti only via the cuda_v12 fallback. J-1943 (needs_input) asks Travis to do C and pin/GPU-check the version.
- **2026-10-07** (F-2516): J-1880: single-endpoint judge callers (sitting.judge_dwell_release, competence tier-3 witness) now fast-fail via read-only model_client.lane_is_tripped while the J-1832 Ramses breaker is open; merged-not-live, no hot-lane fallback (F-1907). Commit 698495c on jobrun/single_endpoint_failfast.

- **2026-10-07** (F-2503): 2026-10-07 J-1832 built (merged-not-live, restart-gated): per-lane circuit breaker in core/model_client.call_node_json (3 consecutive >=30 s timeouts -> skip lane 300 s, one half-open probe; fail-open, single-endpoint chains unchanged; transitions to new uncapped data/lane_breaker.jsonl). Trace replay over 22 stall windows: skips ~2,084 of 2,844 in-stall attempts, ~56 h of 120 s waits; adds no hot-lane calls for the same traffic (80% already failed over to :11433 after the wait). core/sitting.py:210 judge (20% of in-stall attempts) is single-endpoint by design and still pays 120 s.
- **2026-10-07** (F-2498): J-1840 (D-0354 build, merged-not-live): :11441 first call_node_json attempt now goes out without format=json; retries re-send with it (worktree commit dc5c2bc). json_mode rows in llm_latency.jsonl carry g; new llm_json_parse_fail.jsonl feeds the defeater read. Real-code replay of 46 J-1829 prompts on Ramses: 46/46 parsed, 5 retried (all active_imagination), p50 1.7 s. Restart-gated; 7-day defeater read spawned.

- **2026-10-07** (F-2494): 2026-10-07 J-1830: deploy/ramses/nascence_cpu_server.py (repo copy; worktree commit fb66ece, merged-not-deployed) now drops callers that have gone, stops generating between tokens at --max-gen-seconds (default 150) or on disconnect, logs wait/gen separately and serves GET /api/status; abandon test on a local test hub: next call waited 19.4s on the old file vs 0.13s on the new. Ramses still runs the old file; deploy needs a Ramses hub restart (founder) and J-0526 drift sync.
- **2026-10-03** (F-2355): J-1688 built supervisor.py observability (commit 6bfdd7d, restart-gated): timestamped append-only events log, failed-probe budget/elapsed/error/phase, pre-kill host snapshot and outcome lines, hourly summary; decision logic untouched; Ollama tray-app respawn race flagged as D-0341; live-log follow-up J-1729 deferred to 2026-10-07

- **2026-10-03** (F-2279): J-0890 closed - D-0194 defeater not fired: CPU_HEALTH_TIMEOUT 10 s is live and about 351 h of new-code supervision across four supervisor runs had zero CPU-hub watchdog restarts; the only watchdog kill was hot_ollama on 09-30 (F-2280, cause unattributed), build J-1688 spawned for supervisor logging
- **2026-09-28** (F-2198): F-2198: D-0297 (plan=lane2_the_witness, ruled 2026-09-27) already addressed the JUDGE_1 :11438 contention question with fresher tier-wide evidence (244 timeouts on 09-26 alone) and declined D-0121's move-the-hub option for now, choosing to sample Lane 2's own metaphor judge instead. J-1150 stays open for the hub-log root-cause diagnosis but should read D-0297 first.

### What we have
- Tier layout live and FROZEN since 2026-08-30 (D-0101) — see the standing-layout table in §5.6 above;
  no port/model change is being actively pursued.
- A third recurring Judge1 (mixtral:8x7b @ Ramses :11438) outage, found 2026-09-22 (F-1569/F-1445,
  J-1150): 3 long unavailable-run windows in 6 days (09-16 twice, 09-21→22), 606 of 635 unavailable
  rulings since 09-15 sitting inside those runs, 100% `err1` timeouts — recurrent, not a one-off.

### What we need
The hub-side evidence only Ramses holds: the :11438 server's own `--log` file for the 3 outage
windows, plus Ramses process/Task-Scheduler/Event-Viewer history for the same times (was the hub
restarted, by what). `\\ramses\D\Du\` is unreachable from this machine, so this is a founder/Antigravity
pull, not something this session can fetch.

### What we're doing next
J-1150 stays open (`needs_input`), blocked on Travis pulling those logs to
`C:\Users\USER\ramses_hub_logs\`. Once they arrive: identify what's holding the hub's one-per-hub
asyncio lock in each window, then check D-0121's defeater (real contention → move Judge1 to its own
hub) before opening a `/decide` with J-1150's four named options (own hub, request deadline, watchdog,
shorter timeout) — D-0101's freeze means any re-homing still needs an explicit founder call.
