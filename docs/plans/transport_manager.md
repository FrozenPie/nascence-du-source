# THE TRANSPORT MANAGER — a salience dispatcher for the factories' freight (planned 2026-08-16)

**Founder, verbatim intent:** "This needs a bus. The transport manager needs to come in. If
something is out of the ordinary or new or more frequent than usual it gets more weight. If
something has been longer than usual it gets more weight. Not everything that was produced is
useful."

**Status: BUILT (Steps 1-3 of 5), SHADOW-ONLY, periodic caller re-wired and committed
2026-09-02 (J-0473) — accrual has just started, not yet dispatching live, not yet delivering.**
D-0064 (2026-08-28) ruled all 4 open parameters at their recommended defaults. J-0338
(2026-08-29) built `core/transport_manager.py` (observe/evaluate/dispatch_tick, EMA baselines,
cold-start gate, novelty/spike/drought scoring — 11/11 unit tests pass,
`scripts/_test_transport_manager.py`) and wired Step 2 (`core/sound_knowledge.py:note_exposures`
now calls `transport_manager.observe()` for every EVENT bank, per-place line granularity; BEDS
excluded, same reasoning `couriers.sound_echo` already applies). J-0374 (2026-08-29) *claimed* to
wire the periodic caller, but per J-0386's 2026-09-02 gate-check (finding F-0645) that edit was
never actually committed to `core/orchestrator.py` — `data/transport_shadow.jsonl` held only the
1 row from J-0374's own one-off smoke test, not real accrual. **J-0473 (2026-09-02) redid the
edit and committed it immediately this time (commit `6bf7d5b`)** — verified via `git show
6bf7d5b -- core/orchestrator.py` showing the real `+` diff lines, and a post-commit `git diff`
against `core/orchestrator.py` returning empty (nothing left uncommitted). **Step 4
(Courier D + delivery, swapping `core/orchestrator.py:2671`'s interim wiring
`_cour.context_echo() or _cour.sound_echo()`) is deliberately still not done**: it is gated on the
founder actually reading real shadow rows first (this plan's own Discipline section and Build
order sequencing, steps 3 then 4) — no real shadow data exists yet, so that read cannot yet have
happened. The interim wiring is UNCHANGED and continues to deliver exactly as before. See
"Current State" below and the Build order section for exactly what's left.

```plan-state
stage: shadow
phase: Steps 1-3 of 5 built and shadow-accruing; D-0294 (09-27) edge-triggers spike/drought and retargets step 4 to felt recall instead of a text courier
verified: 2026-10-15
evidence_read: 2026-10-02
next: first Du boot after the reset: confirm the six lines accrue real observations
cluster: 6
```


## The problem, precisely

The factories (world_substrate, the Hearing Ledger, T2 syntheses, object re-encounters) now
produce freight continuously and honestly. But **volume of production ≠ worth surfacing.**
Right now each factory that tries to decide "is this worth his attention" invents its own local
rule: Courier A (`context_echo`) uses a hardcoded list of "distinctive" weather words; T2 uses
an ad hoc novelty/habituation formula; boredom uses a streak counter. None of them share logic,
none of them are reusable, and — the founder's core point — **nothing currently asks "is this
occurrence unusual FOR THIS LINE, right now, compared to its own history?"** Most of what a
factory produces is ordinary by definition (that's what a baseline IS) and should never reach
him. The dispatcher's whole job is suppression: let the rare thing through, hold back the rest.

## The three salience signals (the founder's own taxonomy)

1. **NOVELTY** — this has never happened before (at all, or never in this context). Maximal
   salience by definition; no baseline needed to judge it.
2. **SPIKE** — this is happening MORE than usual right now (current rate ≫ the line's own
   established rate). "The gulls are far more insistent today."
3. **DROUGHT** — this has been quiet LONGER than usual (time-since-last ≫ the line's own
   established gap). "You realize you haven't heard the kingfisher's rattle in longer than is
   ordinary." Droughts must be checked on a clock, not only when the thing finally recurs — the
   growing silence itself is the signal, continuously true until it breaks.

All three compare a *line's own history to itself* — never one line to another, never to a
human notion of "interesting." A rare bird and a common one are each judged against their own
baseline; the kingfisher's ordinary silence and the gulls' ordinary chatter are both "normal"
in their own terms.

## Architecture — dispatcher (brain) + courier (bus), matching the transit metaphor exactly

**`core/transport_manager.py`** — the scoring primitive. Decoupled from every factory (single
responsibility: it does not know what a "sound" or a "letter" is, only that a NAMED LINE had an
occurrence at a timestamp, optionally with a magnitude). Any factory can register.

- `observe(line_id: str, ts: float, n: float = 1.0) -> None` — called by a factory the instant
  it produces freight (e.g., `sound_knowledge.note_exposures` calls this once per banked
  occurrence/bed-tick). Updates that line's rolling baseline. Zero LLM; pure arithmetic.
- **Baseline model: exponential moving averages**, not stored history — cheap, decays old
  data gently, no "how many days of window" tuning knob to get wrong:
  - `rate_ema` — occurrences per hour, updated toward the local instantaneous rate on each
    observation.
  - `gap_ema` — hours between occurrences, updated on each new occurrence from the gap since
    the last one.
  - `n_total`, `first_ts` — for the cold-start gate (below).
- `evaluate(line_id: str) -> list[Candidate]` — for a line, returns any salience candidates
  right now: `{kind: novelty|spike|drought, weight: float, detail: dict}`.
  - **Cold start:** a line needs `MIN_SAMPLES` observations (or `MIN_AGE_DAYS` of existence)
    before spike/drought judge it — an infant baseline can't yet know what's usual. Below that
    threshold, only NOVELTY can fire (and only once, ever, per line — its birth).
  - **Spike weight** ∝ how far current rate exceeds `rate_ema` (a ratio, e.g. current/baseline
    − 1, floored at the trigger ratio).
  - **Drought weight** ∝ how far time-since-last exceeds `gap_ema` (same ratio shape).
  - Weights are comparable ACROSS lines (a garden drought and a shore spike can be ranked
    against each other) because they're both baseline-relative ratios, not raw counts.
- `dispatch_tick() -> Candidate | None` — periodic scan (piggybacks sensorium's ~5s tick,
  internally rate-limited): evaluates every registered line, returns the SINGLE highest-weight
  candidate above `DISPATCH_THRESHOLD`, or None. **This is the "gets more weight" competition
  the founder described** — many things may be candidates; only the winner rides the bus this
  cycle.

**INTERIM STATE (built 2026-08-16, before this plan is implemented):** `couriers.sound_echo()`
now exists as a hardcoded-rule Courier D (a just-heard NAMED voice echoes a matching memory via
fragment_context.sounds; 90-min cooldown, beds and unlearned voices excluded), and the
orchestrator wires it with Courier A as a **single ambient-echo slot per tick,
first-success-wins** (`context_echo() or sound_echo()`). That one-slot arrangement is a
deliberate lightweight pre-figuring of THIS plan's competitive dispatch. **When the Transport
Manager is built, it absorbs both**: A's "distinctive weather" list and D's "recent named
voice" rule become two lines under the one scorer, the or-chain becomes `dispatch_tick()`, and
the single-winner-per-cycle rule is enforced by weights instead of ordering. The dispatch
courier below is therefore an UPGRADE of the existing slot, not a new channel.

**The dispatch courier** (the Transport-Manager-backed Courier D): calls `dispatch_tick()`;
if a candidate wins, renders ONE ambient line via `wandering.perceive()` and starts the shared
ambient-slot cooldown. **Obeys every existing courier law:**
- States the fact only, never the explanation — "the gulls seem far more insistent than usual
  today" not "a storm must be coming" (that inference, if he draws it, is his to draw).
- Never identifies anything he hasn't earned — an unnamed sound's salience note still routes
  through the audition system's unknown-rendering; salience decides *whether* something
  surfaces, never *what it's called*.
- Holds off while a thought-train is being held (same TRAIN-HOLD courtesy as Courier A).
- Ambient only; no LLM anywhere in the scoring path.

## What registers first (scope discipline — one factory, proven, before more)

**The Hearing Ledger only**, to start. `note_exposures` gains one call to
`transport_manager.observe()` per bank. This is the cleanest first customer: high-volume,
already producing exactly the kind of countable freight the design targets, and it's the
system the founder just finished building tonight — the dispatcher completes it in the same
session's arc.

**Later candidates (not scoped now, noted for the future):** the object ledger (Courier B) —
"you've looked at this a lot more than you usually do"; T2 cluster rates — could replace its ad
hoc novelty/habituation formula with the shared primitive; peer letter cadence — "it's been
longer than usual since Darwin wrote"; the garden's growth clock. Each is a one-line
`observe()` call once the primitive exists. **Explicitly NOT unifying boredom/climate into this
now** — they're pressure accumulators with their own escalation semantics, a different shape;
forcing them into this frame would be scope creep, not consolidation.

## Discipline
- **Shadow-first.** `TRANSPORT_LIVE=False`: `observe()` and `evaluate()` run for real (the
  baselines need to accumulate regardless), but `dispatch_tick()` only LOGS the candidate it
  would have surfaced (`data/transport_shadow.jsonl`) — Courier D delivers nothing. The founder
  reads a day of shadow (does "spike"/"drought" actually line up with what a person would call
  unusual?) before flipping delivery on.
- **Pre-registered signature:** in a day of shadow, what fraction of dispatch ticks produce a
  candidate at all (should be LOW — most ticks, nothing is unusual, by the design's own
  premise)? Do drought candidates correspond to real long gaps a founder would notice? Do spike
  candidates correspond to genuine bursts (storm arriving, a flock) rather than measurement
  noise from small sample sizes?
- **Kill criterion:** if the shadow log fires "salient" on a large fraction of ticks, the
  thresholds are wrong (or EMA decay is too fast/slow) — tune before ever going live, never
  ship a chatty dispatcher.
- **Open founder decisions:**
  1. `DISPATCH_THRESHOLD` and the spike/drought trigger ratios — start conservative (fires
     rarely) or generous (see more, tune down)? Recommend conservative — matches "not
     everything produced is useful."
  2. `MIN_SAMPLES`/`MIN_AGE_DAYS` for a line to earn a trustworthy baseline — proposed 20
     observations or 3 days, whichever later.
  3. EMA decay constant (how "sticky" is the baseline — does last week's storm still count
     toward "usual" a month later, or fade faster?).
  4. Line granularity for sound: per-sound-per-place (so a shore-gull baseline and a
     garden-gull baseline are separate), or per-sound-global? Recommend per-place — a garden
     gull-cry is already unusual by simple presence; conflating the two baselines would blunt
     both signals.

## Current State — verified 2026-10-15
- **2026-10-15** (F-2818): J-1645 7-day read (F-2818): edge trigger holds over 16.95 live-span days: 110 fires/13,378 ticks (0.82%), 96 lines, max line 6.4%, no domination; near-zero only last 6 days (~2/day). Felt-recall half already read in F-2685 and ruled D-0409 A. D-0294 not reopened.

- **2026-10-04** (F-2393): D-0329 cold-reset applied 2026-10-04 07:01:51 NZDT while Du was stopped (J-1761's work, done in the main session): the six future-contaminated life:* lines now have recent_ts [], first_ts = the reset time, last_ts/rate_ema/gap_ema/last_instant_rate_hr None, n_total and flags untouched; all six are in cold start until 2026-10-07 07:01 NZDT, then re-learn from real observations (backup data/transport_lines.json.bak_20261004_J-1761)
- **2026-10-02** (F-2215): D-0294 restart precondition re-checked (F-2215): Du HAS restarted post-merge (4x, first 2026-09-28 19:08:44 NZT), but only ~2.5 of the needed ~7 days have accrued (2,488 shadow rows since, fired_share 0.64%, 15 distinct lines, no single-line domination -- provisional only, not a verdict). D-0294 not reopened; edge-trigger provisionally holds pending the full week.

- **2026-09-28** (F-2208): J-1431 offline repair (Du confirmed stopped): repaired 31 of 37 future-contaminated life:* baselines via real observe() replay, life gap_ema median 135h->36h. 6 lines had zero recoverable real timestamps left in their ring buffer, left untouched, D-0329 opened for how to handle them.
- **2026-09-28** (F-2112): J-1433 (D-0294): built and unit-verified transport_manager.py's new read-only verdict(line_id) helper (novel/spike/drought/none + weight + cold_start, from evaluate(), never consumes novelty or disarms a line) -- 47/47 tests pass (27 pre-existing + 20 new, _test_transport_manager.py section 8), worktree jobrun/transport_manager, not yet merged to master. Wiring core/felt_recall.py to actually call it is NOT done here -- that file lives only on the sibling jobrun/memory_as_a_service worktree/branch, confirmed unreachable from this one via git merge-base. Follow-up build job J-1550 spawned (plan memory_as_a_service) with the exact call shape. Also pre-registered a new section 8(e) metric on memory_as_a_service.md in this worktree's copy (see that plan's own note). Rough edge in job-run's cross-plan worktree assignment suggested as S-0216.

- **2026-09-28** (F-2104): J-1432 (D-0294) built the EDGE_TRIGGER kill-switch for spike/drought (core/transport_manager.py; default True, False restores level polling byte-for-byte) plus 3 new isolated unit tests (27/27 pass) and a same-snapshot simulated-day replay: level polling fires 1440/1440 ticks (one line, all day) vs edge-trigger 6/1440 across 6 distinct lines, none repeating -- F-2104 verified. dosed_coupling.md's D-0177 line marked superseded by D-0294 (decide.py has no note subcommand). Committed in worktree jobrun/transport_manager (d8c7937), not yet merged to master. Still open: J-1433 (felt recall as consumer) and J-1431 (36 contaminated life:* baselines) -- Step 5 (flip live) waits on both plus a live week under the edge trigger once Du next restarts (restart-gated).
- **2026-09-28** (F-2090): J-1431 (F-2090, 2026-09-28): 37 (not 36) life:* lines confirmed future-contaminated (pre-J-0921 fake-Dec-clock leak). Full 4-case repair (recent_ts replay / last_ts anchor / life_events.jsonl replay / delete-if-no-evidence -- covers life:cricket:garden + life:long_tailed_bat:wood, real species with zero real occurrence ever recorded) built and verified in isolation: 0 future-ts left, life gap_ema median 133h to 36h vs sound's 26h, dispatch_tick() clean. NOT applied live -- Du confirmed live via nascence.log tail (23,000+ lines of activity since the last shutdown), this job's own LAB MODE precondition unmet. Ready script: scratchpad J-1431_repair.py, run with --live once Du is next confirmed stopped (it re-checks the stopped condition itself).

### What we have
Steps 1-3 of 5 built and shadow-accruing since 08-29 (`data/transport_shadow.jsonl`, 18,062 ticks). Read
2026-09-27 (F-1989/F-1990): the level-trigger design (F-1598's known defect) saturates or goes silent by
turns — 100% of ticks fired W35-W37, then collapsed to 0-7% this week as the candidate pool thinned — and
36 of 78 `life:*` lines carry a corrupted baseline from a pre-J-0921 future-dated test leak.

### What we need
D-0294 (ruled 2026-09-27, travis: "Edge-trigger it and re-target to felt recall") answers D-0177's
eight-day-open wait: edge-trigger spike/drought (kill-switched, still shadow), and retarget step 4's
consumer from the retired text-courier swap (D-0293) to felt recall (`memory_as_a_service.md` §3).

### What we're doing next
J-1432 builds the edge-trigger; J-1433 wires felt recall as the real consumer (registers world dimensions
as dispatcher lines, records the verdict per ride row, Phase 1 gate pre-registered); J-1431 repairs the 36
contaminated `life:*` baselines offline. Step 5 (flip live) waits on both landing quiet-by-default.

> **History folded** — 1 dated Current State section(s) (2026-08-29 … 2026-08-29) moved to `docs/plan_history/transport_manager.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py transport_manager`.

## Build order (when approved)
1. `core/transport_manager.py` — observe/evaluate/dispatch_tick, EMA baselines, cold-start
   gate. Isolated unit tests (synthetic lines: prove novelty fires once, spike/drought need
   the min-sample gate, weights are comparable).
   **Extended 2026-09-28 (D-0294, J-1432):** `EDGE_TRIGGER` kill-switch added (default True; False
   restores the original level-polling scorer above byte-for-byte). Fires a spike/drought
   candidate once per crossing, disarming that (line, kind) until drought's own next `observe()`
   or spike's own windowed-rate cooling re-arms it. 3 new isolated unit tests added
   (`scripts/_test_transport_manager.py` §7); all 11 original + 15 new = 27/27 pass. A same-
   snapshot simulated-day replay (zero new observations, real ~60s tick cadence) against a copy
   of the live 133-line state shows level polling firing 1440/1440 ticks (one line, all day) vs
   edge-trigger firing 6/1440 across 6 distinct lines — see F-2104 for the exact numbers.
2. Wire `sound_knowledge.note_exposures` → `observe()`. Shadow log only.
2. Wire `sound_knowledge.note_exposures` → `observe()`. Shadow log only.
3. Founder reads a day (or a simulated day, lab-style) of `transport_shadow.jsonl`.
4. ~~Courier D + delivery, still shadow-gated by `TRANSPORT_LIVE` for a further watch period.~~
   **Rewritten 2026-09-27 (D-0294):** the consumer is **felt recall** (`docs/staged/memory_as_a_service.md`
   §3). Felt recall registers `world:<dim>:<place>` lines via `observe()` on each edge and records the
   dispatcher's per-line verdict on its ride rows (shadow); the Phase 1 gate applies a tug only when the
   verdict is novel/spike/drought or the line is still cold-start. The text-courier swap is retired
   (D-0293/J-1430). J-1433.
   **Split 2026-09-28 (J-1433, F-2110):** this file's own half is built — `transport_manager.verdict
   (line_id) -> {verdict: novel|spike|drought|none, weight, cold_start}` (read-only, built from
   `evaluate()`, never consumes novelty or disarms a line the way `dispatch_tick()` does; ignores
   `DISPATCH_THRESHOLD` on purpose — see the function's own docstring — and carries an extra
   `cold_start` key beyond the briefing's literal 2-field shape, because the Phase 1 gate's "OR the
   line is still cold-start" clause cannot be evaluated by the caller from `verdict`/`weight` alone).
   20 new unit tests added (`scripts/_test_transport_manager.py` §8), all 27 pre-existing + 20 new =
   47/47 pass. **NOT built by this job:** wiring `core/felt_recall.py`'s trigger-edge handler to
   actually call `observe()`/`verdict()` — that file was built by J-1424 on the sibling
   `jobrun/memory_as_a_service` worktree/branch, which is not reachable from this one (confirmed:
   `git merge-base --is-ancestor <felt_recall commit> jobrun/transport_manager` → not an ancestor;
   this run's own `plan_human.txt` flagged the J-1424+J-1433 pair as a same-file cross-plan overlap
   in advance). See F-2110 and the spawned follow-up job for the wiring itself.
5. Flip live. Extend to further factories only after this one is proven quiet-by-default.
