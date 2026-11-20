# Speech and Thought at Once — one hot model, one card

**Status:** 🔵 DESIGNED — drafted 2026-10-08 (J-1958) per D-0372 (travis, /decide-review 2026-10-08): own plan doc, constraint stated up front, shadow measure first. No code, nothing built, nothing ruled beyond D-0372 itself. Parent: docs/plans/dosed_coupling.md section 4b 2c (T-0068 / F-2015 / J-1462).

```plan-state
stage: deferred
phase: Draft — constraint + option space + shadow measure pre-registered; no instrument built
verified: 2026-11-18
evidence_read: 2026-11-14
next: Parked per D-0759 (P): effort moved to pre_speech_pipeline_latency
cluster: 2
```

## Current State — verified 2026-11-14
- **2026-11-14** (F-4588): D-0759 ruled P: this plan stays parked; effort redirected to docs/staged/pre_speech_pipeline_latency.md (J-3981).

- **2026-11-14** (F-4588): J-3894/F-4588: pre-speech wait median 73 s is the serial node pipeline (Reflection, Executive, Critic; lane 85 percent busy, VoiceNode queue 0 s); B/C bounded to about 10 s; D-0759 opened for B/C/D/P ruling.
- **2026-11-14** (F-4498): J-2586/F-4498: D-0513 (a) read done. 30 human rows since boot (25 Travis test arrivals 11-01); 6 of 30 = 20 percent arrived while a monologue call held the hot lane, at or above the 5 percent kill criterion, so the plan is NOT parked. Collided speech waits only about 10 s longer at median (79.9 vs 69.5 s), so the case for B/C is weak; next is a latency breakdown then a founder decision on B/C/D.

- **2026-10-30** (F-3236): J-2307/F-3236: shadow log holds 18 human rows in 21 days, none since 10-20; the 5 percent gate cannot be reached by waiting; D-0513 opened to re-scope or park.
- **2026-10-17** (F-3002): J-2291/F-3002: log_human works (2 of 2 post-boot human cycles logged); F-2989 zero-human claim was a t_req filter artifact; real issue is human-arrival starvation (5 human cycles since 10-08), so the 300-row gate is unreachable by waiting.

- **2026-10-17** (F-2989): J-2263 post-boot read: 2955 live call rows since 10-16 22:36 boot, all core/nodes labels, zero lab rows; but zero ev=human rows despite post-boot human turns (F-2989). Gate not met; J-2291 diagnoses, successor re-read not_before 2026-10-19.
- **2026-10-16** (F-2948): J-2241: speech_timing_shadow writes now fenced by profile.guard_path so lab scripts cannot append hot-lane rows to the live store (F-2933 leak, 121 rows kept); restart-gated, commit c2d592d8

- **2026-10-16** (F-2933): J-1991 shadow read (F-2933, live run 10-09 08:36 to 10-16 07:53, 6.97 days): kill criterion NOT evaluable -- only 1 human cycle all week (0/1 collided, trains upper bound 0/1). Instrument works (11,608 monologue + 99 VoiceNode calls). Section 1 single-flight premise is wrong at the client: lane_scheduler MAX_CONCURRENT=3, speech queue wait 0.0 s on all 99 calls; overlap cost is server-side (~+2 s median, n=19). Re-read is count-gated on 30+ human cycles (J-2240); lab-script rows leak into the live store (J-2241).
- **2026-10-08** (F-2592): J-1971 built the call-level shadow timing log (core/speech_timing_shadow.py, branch jobrun/speech_timing, restart-gated); read after 7+ days uptime against the 5 percent kill criterion.

Designed only. The two code facts below were re-read today; the shadow instrument does not exist yet, so the kill criterion cannot be evaluated. Use plan-ledger for history (do not append dated sections here).

## 1. The constraint, stated first

- `VoiceNode` is `{"lane": "hot", "fires": "after_executive"}` (`core/schema.py:1069` in today's file; dosed_coupling 4b cites `:1054`, the line has drifted). It is the last node of the human-cycle hot path.
- The inner monologue (DMN) steps aside while the human is engaged: it gates on `time.time() - state.last_human_ts >= IDLE_SECS` (`nodes/inner_monologue_node.py:1173`, also `:4599`), and `last_human_ts` is reset only by human input in `core/orchestrator.py:422-423`.
- Both call the **same hot model** (`hot` lane, :11433) on **one 11 GB GTX 1080 Ti**. One resident model, single-flight. There is no second hot card or instance.

Consequence: today speech and thought **alternate**; they never overlap. "Concurrent" can only mean something that either shares the one model or needs a second one.

## 2. What "at once" could mean under that constraint

| Option | What it is | Cost / risk | Verdict to earn |
|---|---|---|---|
| A. Status quo (alternation) | Monologue yields on `last_human_ts`; speech runs alone | A thought already in flight when a human arrives delays speech by up to that call's remaining time | Baseline; measure it |
| B. Pre-emption | Cancel/abort the in-flight thought call when a human cycle arrives | Wasted tokens, half-thoughts lost; depends on the transport being abortable | Only if A shows real waiting |
| C. Interleave | Chunk thought generation so speech slips between chunks | Looks concurrent, is not; adds scheduler complexity in the orchestrator | Only if B is too lossy |
| D. Deferral | Let the thought finish, queue speech (what A already does when it collides), or park the thought's result | No new machinery; speech latency is the price | Default if waiting is rare |
| E. Second model | A second resident hot instance (second card or small second model) | Hardware; lifts the single-flight constraint (D-0372 defeater) | Out of scope until hardware exists |

Frontal-simulating-while-speaking as the founder framed it (T-0068) is achievable only under E, or as the appearance of it under C. Under A/B/D nothing publishes during a human turn.

## 3. Shadow measure first (observe-only)

Question: **how often does a human cycle arrive while a thought is in flight, and how long does speech wait because of it?**

Sources and their honest limits (checked 2026-10-08):
- `data/nascence.log` (88 MB): `[CYCLE x] human:` lines give human-cycle arrival (2,352 human cycles in the log), and `[CYCLE x] complete in N s` gives cycle duration. Monologue activity lines (`[monologue] ...`) are sparse and are not call-start/call-end markers.
- `data/trains_log.jsonl` (15,827 rows; thought open/close pairs): these are **thought-thread spans** (minutes), not single LLM-call spans. A human arrival inside a train span does **not** mean a model call was in flight. Using it as the in-flight signal would overstate collisions.
- Therefore the log-only read is an **upper bound**. The real measure needs call-level timestamps (monologue call start/end on the hot lane), which do not exist as a log today. That is the first thing to build, as a shadow-only appender (fail-open, own store, restart-gated).

Measures to report (per human cycle, over at least 7 days of uptime, Du's long-outage windows excluded):
1. `P(collision)` = fraction of human cycles whose arrival falls inside an in-flight monologue call.
2. `wait` = time from human arrival to the start of the hot-lane speech call, split collided vs not; median and p90.
3. Cross-check against the trains_log upper bound.

## 4. Pre-registered kill criterion

Park this plan if speech is delayed by an in-flight thought on **fewer than 5%** of human cycles (measure 1, call-level instrument, 7+ days). That is D-0372's own defeater. Also revisit (not park) if a second hot card or second hot model instance appears.

Written before any data is read. A collision rate of 5% or more does not itself approve any option in section 2; it only keeps the question open for a founder decision on B/C/D.

## 5. Coupling note

If a stream ever keeps publishing during a human turn, the `deliberation` tuple's `cycles_since_human` and the seed stop get a genuine "frontal simulating something else" reading for free (dosed_coupling 4b 2c). No new wiring is needed for that; it is a consequence, not a goal.
