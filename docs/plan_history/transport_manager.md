# transport_manager — folded history


---

# History folded on 2026-09-27 from `docs\plans\transport_manager.md` (plan-compact, 1 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py transport_manager`._

## Current State — verified 2026-08-29
J-0338 built `core/transport_manager.py` in full: `observe()`, `evaluate()`, `dispatch_tick()`,
time-weighted EMA baselines (`HALF_LIFE_DAYS=14.0`, builder-chosen concrete value — the plan
posed the decay-stickiness question without itself proposing a number, see the module's own
docstring), the `MIN_SAMPLES=20`/`MIN_AGE_DAYS=3`-whichever-later cold-start gate, and
`DISPATCH_THRESHOLD=1.5` (conservative — requires ~2.5x baseline, not just the 2x trigger floor
that makes something a candidate at all). Verified via `scripts/_test_transport_manager.py`,
11/11 synthetic-line assertions passing (novelty fires once and is exempt from
DISPATCH_THRESHOLD; cold start blocks spike/drought even past MIN_SAMPLES until MIN_AGE_DAYS
also clears; a real burst is detected as spike; a real silence is detected as drought purely
from elapsed clock time, no new occurrence needed; dispatch_tick returns the single
highest-weight candidate and logs every tick to `data/transport_shadow.jsonl`, fired or not).

Step 2 of the Build order below is wired: `core/sound_knowledge.py:note_exposures` calls
`transport_manager.observe()` once per EVENT bank (`sound:{key}:{location}`, per-place per
D-0064 param 4) — verified live by import-and-call smoke test. BEDS (continuous presences) are
deliberately excluded from observation, matching `couriers.sound_echo`'s own reasoning that a
near-continuous presence has no spike/drought shape worth judging.

**CORRECTED 2026-09-02 (J-0386/F-0645) — the claim below did not survive contact with the live
codebase at the time; kept struck-through rather than deleted so the record is honest about what
happened. See the RE-WIRED note directly below it for the current, real state.**
~~**Verified 2026-08-29 (J-0374):** the periodic caller is live —
`core/orchestrator.py`'s `_substrate_loop` (background task started from `start_background()`)
now increments a `_transport_ticks` counter each ~5s tick and calls
`transport_manager.dispatch_tick()` once every 12 ticks (~60s)...~~ **This was never actually
persisted.** J-0386's gate-check (2026-09-02) found `data/transport_shadow.jsonl` still holding
exactly the 1 row from J-0374's own live smoke test (`2026-08-29T00:53:19 UTC`, unchanged since —
matches the smoke-test row this section describes), and `grep`/`git log -p --all` on
`core/orchestrator.py` show `dispatch_tick`/`_transport_ticks` appear NOWHERE in the file or in
any commit in this repo's history. The interim wiring at `core/orchestrator.py:2691-2695`
(`_cour.context_echo() or _cour.sound_echo()`) is still byte-identical to pre-J-0374. This matches
the already-documented self-inflicted git-reset incident chain from that session
(F-0486/F-0510/F-0511/F-0515) — J-0374's edit to `orchestrator.py` was apparently lost there and,
unlike the items the `3470b4d` checkpoint commit explicitly named and reconstructed, was never
caught. Full evidence: finding F-0645.

**RE-WIRED AND COMMITTED 2026-09-02 (J-0473, commit `6bf7d5b`):** `core/orchestrator.py`'s
`_substrate_loop` again increments a `_transport_ticks` counter each ~5s tick and calls
`transport_manager.dispatch_tick()` once every 12 ticks (~60s), same shape J-0374 originally
described, wrapped in the same fail-open `try/except` style as every other block in the loop.
Verified this time (learning from the loss above): `py_compile` clean,
`scripts/_test_transport_manager.py` 11/11 still passing, an isolated tick-counter logic
simulation confirmed `dispatch_tick` fires exactly once per 12 simulated ticks, and — the specific
anti-repeat check this job's briefing required — `git show 6bf7d5b -- core/orchestrator.py`
was read back to confirm the `+_transport_ticks`/`+dispatch_tick()` lines are really inside the
commit, and a post-commit `git diff -- core/orchestrator.py` returned empty (nothing left
uncommitted in the working tree). Du restarted 2026-09-02 08:48:54 NZT, before this commit, so
this wiring takes effect on Du's *next* restart (restart-gated, per this repo's own convention) —
real shadow accrual has not started yet as of this edit landing.

**Left for a follow-up job (Step 4, swap not attempted this pass):** `core/orchestrator.py:2671`'s
interim wiring (`_cour.context_echo() or _cour.sound_echo()`) is UNCHANGED; the dispatcher does
not replace it yet. That swap (Build order Step 4: "Courier D + delivery, still shadow-gated by
`TRANSPORT_LIVE` for a further watch period") is a real, separate edit to a 40+-dependent hub
module (`core/orchestrator.py`, confirmed via `udms_get_change_dossier` — see finding F-0448) and,
more importantly, is explicitly gated on Build order Step 3 ("Founder reads a day ... of
`transport_shadow.jsonl`") — a gate that cannot be satisfied until real shadow data has actually
accrued from a live Du process running this new wiring (i.e., after Du's next restart past
`6bf7d5b`). A fresh gate-check job (not a reopened J-0386) should be spawned for a day after
that restart, not from J-0473's commit timestamp or J-0374's old one — neither reflects when a
running process with this code actually started ticking.
