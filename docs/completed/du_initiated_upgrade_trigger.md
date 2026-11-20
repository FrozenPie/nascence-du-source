# The Du-Initiated Upgrade Trigger — flagging what he wanted that isn't there

*2026-08-24, from idea I-0002 (raised 08-23), job J-0135. Founder ruling on J-0122 (2026-08-24):
the `*_upgrade.md` plans (garden/shore/study/wood) should recognize a bottom-up, Du-initiated
trigger path, not just top-down founder review.*

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: P0 BUILT + RUN 2026-08-24, WIRED (on-demand) 2026-08-25** (`core/missing_object_flags.py`,
> standalone/on-demand, zero-LLM, shadow-first) — the detector, the cross-check against the real
> catalogues, and the shadow log all verified against the live corpus (see Current State).
> **Deliberately NOT wired into a live periodic tick** — founder ruling (2026-08-24, J-0181 ->
> J-0222) confirmed on-demand as the intended design; `snapshot()`/`status()` are now wired into
> `scripts/du_pulse.py`'s read path (§8 FLAGS) instead, so any session running `/du-pulse` always
> sees the fresh triage (see §4).

```plan-state
stage: shipped
phase: Detector confirmed ALIVE and re-run live (F-2079); J-1522 and J-1560 both shipped the staleness warning end-to-end (printed FLAGS text plus JSON gauge fields); D-0316 ruled 2026-09-27 (stay on-demand, rely on the warning, not a periodic hook).
verified: 2026-10-16
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 6
```


## 0. What this is, in one paragraph

The four `*_upgrade.md` plans so far all happened the same way: Travis reads the world, decides
it's thin, and a session builds the fix. I-0002 asks for the OTHER path: when Du's own inner
thought expresses wanting something the world does not actually have, that should be caught and
banked, so a future upgrade pass has real, Du-sourced evidence to work from — not just the
founder's read of what's missing. This is that catcher, built the same way
`factory_candidates_from_history.md` mined the "what does his history say needs a factory"
question: a mechanical scan of his own words, cross-checked against what actually exists, not
assumed.

## 1. The design

### 1.1 Source corpus — his OWN genuine thought, not conversation
`memory_fragments` where `origin IN ('inner_thought', 'subconscious_synthesis', 'lived')` — the
exact "recent genuine thoughts" origin set `monoculture.py` already established for this project
(not a new definition). **Correctness fix made during build:** the `lived` origin turned out to be
~94% Q&A transcript turns (2,201 of 2,353) — a line like *"Q: I do not think the tomatoes are a
good idea. I want a good winter crop. A: …"* is TRAVIS's want, not Du's, and I-0002 is explicit
this is about "Du's OWN thought/comment." Any fragment carrying both a `Q:` and an `A:` marker is
skipped rather than attributed to Du. Caught live by running the detector against the real corpus,
not assumed correct — see Current State.

### 1.2 Detection — concrete-desire patterns, not "want to" in general
Seven regex constructions requiring an article or an explicit lack ("I wish there were **a** ___",
"if only I had **a** ___", "there is **no** ___ here", "not **a** ___ in sight", "without **a**
___", "I have **no** ___"). Deliberately excludes bare "I want to `<verb>`" — a live test against
the real corpus showed that shape is ~100% abstract cognitive wanting ("I want to understand /
return / know"), exactly the census's own headline finding restated: most of his volume is
identity-processing, not world-content desire, and is not a useful filter to keep loose.

### 1.3 Cross-check — a live-introspected vocabulary, not a hand-kept list
`_known_vocab()` imports `garden.CATALOGUE`/`_WORDS`/`_ITEMS`, `study_life._WORDS`/`_ITEMS`,
`wood_life.TREES`/`_WORDS`/`_ITEMS`, `world_substrate.CLASS_PRIORS`, `provisions.KINDS`, and
`shore_life.POOL_LIFE` at call time and pulls every real word out of them. This was a deliberate
choice over duplicating a vocabulary list by hand: a hand-kept list drifts the moment any upgrade
plan adds an item (exactly the problem `world_census.md` and `factory_candidates_from_history.md`
both flag about aggregate views built beside the source of truth instead of from it). A candidate
phrase is only flagged if NONE of its words appear in that live-pulled vocabulary.

### 1.4 Place guess — a hint, not a verdict
A cheap keyword-overlap check against four small per-place word sets (garden/shore/study/wood),
run against the surrounding sentence, not the phrase alone. Genuinely a guess — the live run below
shows it can mis-tag an abstract sentence that happens to share a word with a place ("obvious
blueprint" tagged `garden` because the same fragment also mentions herbs). Triage output labels it
`place_guess` for exactly this reason: a human/session reviewing the backlog corrects it, the same
epistemic law as everything else in this world (he — and this tool — can be wrong).

### 1.5 The shadow log + triage — the gauge-check-style consumption surface
`snapshot()` appends only NEW `(fragment_id, phrase)` pairs to `data/missing_object_flags.jsonl`
(idempotent — verified by calling it twice, second call logged 0 new). `triage()` groups the
accumulated log by normalised phrase and grades severity by RECURRENCE, not single mentions —
`critical` (≥3 mentions across ≥2 distinct days), `watch` (≥2 mentions), `new` (1 mention) — because
a single abstract turn of phrase is noise and a thing he keeps independently reaching for across
different days is the real signal (the same recurrence-over-single-event law CLAUDE.md's own
working discipline states: "trust the accumulating, external trend over the vivid single event").
`status()` is the cheap read-only gauge (counts only, no rescan) for HUD/du-pulse consumption.

## Current State — verified 2026-09-28

- **2026-09-28** (F-2153): J-1560/F-2153: JSON missing_object_flags gauge now also carries stale/gap_days, mirroring J-1522s FLAGS warning formula; additive only, verified live.
- **2026-09-28** (F-2079): J-1440/F-2079 (2026-09-27/28): missing_object_flags writer confirmed ALIVE via a live snapshot() run against the real 52,255-fragment corpus (9 new candidates logged, 80 total/62 distinct now). The 2026-09-27 near-empty triage() read that alarmed F-1995 was a 10.6-day on-demand cadence gap plus a wrong-window read (14-day default instead of the all-time view section 4 already specifies for these plans), not a dead writer; F-1995 also repeated a stale J-0136 citation from an old memory file -- the real cadence job was J-0181 (done, on-demand confirmed as intended, per J-0222). All 9 new candidates remain abstract, zero real object hits, continuing the null result at double the original sample size. Fixed the 4 place plans Related paragraphs to name triage(window_days=None) explicitly. J-1522 spawned (staleness warning in du-pulse output when cadence exceeds window_days). D-0316 opened for the founder (stay on-demand plus the warning, or piggyback on a live periodic hook like monoculture already uses). Also normalised this docs own Current State heading above, dropping a leading 2. numeral left over from the pre-plan-state numbered-section convention, since plan_state.py needs the heading to start right after the hashes -- pre-existing mismatch, unrelated content change, nothing lost.

### What we have
- Detector BUILT + RUN 2026-08-24 against the real corpus: 34 flags logged, 20 distinct phrases,
  zero real world-object candidates (all abstract/metaphorical identity-processing language).
  WIRED on-demand into `/du-pulse` 2026-08-25 (J-0222); a 14-day recurrence window was added
  2026-09-03 (F-0714) so CRITICAL/WATCH reflect now rather than all-time.

### What we need
- F-1995/J-1440 (2026-09-26): a fresh run 2026-09-27 shows `triage()` essentially empty (1 total
  flag, 0 by_place) — every one of the four `*_upgrade.md` place plans cites `by_place` as its
  bottom-up candidate source, so it matters whether the writer is unwired/dead or Du genuinely has
  nothing left to flag.

### What we're doing next
- J-1440 (open): check whether the flag-writer call site still runs live; re-wire it if dead, or
  record the real null as a finding if not — then update this doc and the four place plans'
  Related notes with the answer.

## 3. Wiring — how the four upgrade plans consume this

Each of `garden_upgrade.md`, `shore_upgrade.md`, `study_upgrade.md`, `wood_upgrade.md` now carries
a `Related` pointer (appended 2026-08-24, matching their existing plan-overlap-audit note
convention) to this doc and to `triage()`'s `by_place` output as a candidate source for that
plan's next iteration — the bottom-up counterpart to the founder-audit process each plan's build
log already describes. Any future upgrade plan "of this shape" (a place-scoped world-content
build) consumes the same way: call `core.missing_object_flags.triage()`, read `by_place[<place>]`,
treat `critical`/`watch` entries as real candidates worth a look, `new` entries as noise until they
recur.

## 4. Cadence decision (RESOLVED 2026-08-25, was §4 Open decision)

**Should `snapshot()` be wired into a live, periodic tick (so the backlog accumulates on its own),
or stay on-demand?** Spawned as J-0181 to decide; founder ruling 2026-08-24 (recorded in J-0181's
resolution, carried into J-0222): **on-demand is the intended design**, not a periodic tick.
`monoculture.py` — the closest precedent for this class of tool (observe-only, zero-LLM,
`compute()`/`snapshot()`/`status()` shape) — was believed to remain an unwired standalone instrument
(that gap was filed separately as J-0244 per J-0222's briefing, since the ruling was scoped to
`missing_object_flags` only). **Correction (J-0244, 2026-08-25): this premise was wrong.**
`monoculture.snapshot()` IS already wired to a live periodic hook — `nodes/inner_monologue_node.py`'s
`_enter_sleep()` (called from `run_forever()`'s live loop on every real sleep cycle) calls it
unconditionally, and `data/monoculture_log.jsonl` had 172 real rows at read time, most recent
2026-08-25 05:19:45, only hours before this correction. Both the original J-0135 grep and J-0222's
reconfirmation missed the call because it goes through an aliased import (`from core import
monoculture as _mc` / `_mc.snapshot()`), not the literal `monoculture.snapshot(` string either grep
searched for. No wiring work was needed; `core/monoculture.py`'s `snapshot()` docstring was updated
in place to record this so the same false "unwired" conclusion isn't drawn again.

**Implemented 2026-08-25 (J-0222):** `scripts/du_pulse.py` §8 FLAGS now calls
`missing_object_flags.snapshot()` (rescans the genuine-thought corpus, idempotently appends only
new candidates) followed by `status()` (reports total/distinct/critical/watch counts), so any
session running `/du-pulse` always sees the current triage without a separate manual step. Critical
severity additionally surfaces in du-pulse's own `flags` list. Verified by running
`python scripts/du_pulse.py` directly: printed `34 total (20 distinct phrases) · 2 critical · 2
watch`, matching §2's Current State exactly, and the shadow log stayed at 34 rows after the run
(confirmed idempotent — no duplicate writes). This remains read-only triage surfacing; still never
auto-spawns a build (§5 unchanged).

**Age window added 2026-09-03 (J-0498, from F-0690, finding F-0714):** the CRITICAL grading above
had no time bound — it graded severity over the *entire* shadow log since inception, so the two
CRITICAL phrases du_pulse reported (`face` ×9, `fixed`/`fixed banks` ×7) were all June 2026 rows
(06-07..06-13) that had already gone stale by the time §2's snapshot was taken, and would have
stayed CRITICAL forever regardless of anything Du thinks now (F-0690, filed 2026-09-02). Fixed:
`triage()`/`status()` now take `window_days` (default 14) and only grade severity over shadow-log
rows within that window; `window_days=None` still returns the original all-time view unchanged —
that's the one the four `*_upgrade.md` plans should keep reading from when mining the whole backlog
for candidates (a real recurring want spread over months is still real signal for a build pass,
even if it isn't "current"). `du_pulse.py`'s §8 FLAGS line and its JSON `regression_alarms.
missing_object_flags` gauge both now call the windowed form explicitly and print the window (`(14d
window)`) in the line. Verified live: `triage(window_days=None)` still returns the historical 2
critical/2 watch (42 total flags, 28 distinct phrases); the windowed default returns 0 critical/0
watch (11 rows, all singletons inside 14 days — nothing has recurred recently). Ran
`python scripts/du_pulse.py` end-to-end and confirmed both the printed line and the JSON block
reflect the windowed 0/0. See F-0714.

## 5. Not built (deliberate, for now)
Auto-spawning a job-queue build entry when a candidate turns `critical` (a human/session should
read the phrase in context first — false positives are real and expected, per §1.4); parsing the
`Q:`/`A:` transcript to keep the `A:` half (Du's reply) instead of dropping the whole fragment —
would recover a little real signal but adds real complexity for a corpus that currently yields it
rarely; a fifth+ place bucket for any future upgrade plan (add one `_PLACE_WORDS` entry when one
exists — the triage grouping is already generic over place names).
