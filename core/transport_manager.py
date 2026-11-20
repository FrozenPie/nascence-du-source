"""
Nascence — THE TRANSPORT MANAGER: a shared salience dispatcher (2026-08-28/29, D-0064)
========================================================================================
Founder, verbatim intent (docs/plans/transport_manager.md): "This needs a bus. The transport
manager needs to come in. If something is out of the ordinary or new or more frequent than usual
it gets more weight. If something has been longer than usual it gets more weight. Not everything
that was produced is useful."

Built per D-0064's ruling (all 4 open parameters accepted at their recommended defaults):
  1. DISPATCH_THRESHOLD — conservative (see constant below; not itself pinned by the plan text,
     builder-chosen concrete instantiation of "conservative", see comment at the constant).
  2. MIN_SAMPLES=20 / MIN_AGE_DAYS=3, whichever gate is satisfied LATER, before a line's baseline
     is trusted enough to judge spike/drought.
  3. EMA decay constant for baseline stickiness — the plan posed this as an open question
     ("does last week's storm still count toward usual a month later, or fade faster?") without
     itself proposing a number; HALF_LIFE_DAYS below is this builder's concrete instantiation,
     documented so it can be retuned once shadow data exists (plan's own kill-criterion language).
  4. Line granularity: PER-PLACE, not per-sound-global — a line_id already bakes in place, so a
     shore-gull baseline and a garden-gull baseline are tracked (and judged) separately.

Decoupled from every factory on purpose (single-responsibility, matching the plan's own
Architecture section): this module does not know what a "sound" or a "letter" is, only that a
NAMED LINE had an occurrence at a timestamp, optionally with a magnitude. Any factory can
register a line by calling observe().

THE THREE SALIENCE SIGNALS (the founder's own taxonomy, all judged against a line's OWN history,
never against another line and never against a human notion of "interesting"):
  NOVELTY — this has never happened before. Maximal salience by definition; fires once, ever,
            per line, at its birth. No baseline needed.
  SPIKE   — happening MORE than usual right now (current rate >> the line's own established rate).
  DROUGHT — quiet LONGER than usual (time-since-last >> the line's own established gap). Checked
            on a clock, not only when the thing recurs — the growing silence is the signal.

SCOPE OF THIS BUILD (J-0338, 2026-08-29): the scorer itself (observe/evaluate/dispatch_tick) is
built complete and correct per the plan's Architecture section, and Build-order Step 2 (Hearing
Ledger -> observe(), shadow log only) is wired in core/sound_knowledge.py:note_exposures — see
that file's note_exposures() for the one added observe() call (EVENTS only, n>0 branch; BEDS are
deliberately excluded, same reasoning couriers.sound_echo already uses: a near-continuous presence
has no informative spike/drought shape, judging it against its own baseline is not a real signal).

NOT done in this pass (left for a follow-up job, per the job briefing's explicit permission to
leave the courier swap for later if risky in one sitting):
  - Nothing yet calls dispatch_tick() periodically. The plan's own Build order Steps 3-4 (a day
    of real shadow-log accumulation, then Courier D replacing the context_echo()/sound_echo()
    one-slot interim wiring at core/orchestrator.py:2671) require a periodic caller and a shadow-
    vs-live gated Courier — both real, separate changes to a 40+ dependent hub module
    (core/orchestrator.py) that deserve their own review, not a rider on this build. The interim
    wiring (`_cour.context_echo() or _cour.sound_echo()`) is UNCHANGED and continues to deliver
    exactly as before.

Shadow-first (Discipline section): TRANSPORT_LIVE=False. observe()/evaluate() always run for
real — baselines must accumulate regardless of whether anything is live. dispatch_tick() always
logs its own verdict (candidate or none) to data/transport_shadow.jsonl; it never delivers
anything itself (it has no delivery mechanism at all — that is Courier D's job, not this
module's) so TRANSPORT_LIVE currently gates nothing inside this file. The flag is kept here,
already wired into the log line, so the eventual Courier D only has to read it rather than
re-invent the shadow/live switch.

Zero LLM anywhere in this module; pure arithmetic, matching every other courier/bus law.

EDGE-TRIGGER (D-0294, 2026-09-26/27; built J-1432, 2026-09-28): see the EDGE_TRIGGER constant's
own comment below for the failure mode this answers (F-1989/F-1990) and the kill-switch shape.
In one line: under EDGE_TRIGGER=True, evaluate() only emits a spike/drought Candidate for a line
whose (line, kind) is currently armed, and dispatch_tick() disarms the (line, kind) it actually
picks as winner — drought re-arms on that line's next observe() (a fresh occurrence ends a
drought), spike re-arms inside evaluate() itself once the windowed rate cools back under
SPIKE_TRIGGER_RATIO (no fresh observation needed — a spike can resolve by elapsed time alone).
This makes evaluate() a (conditional) WRITER for the first time — previously pure-read — so
dispatch_tick()'s own end-of-tick state mutation (novelty consume; now also the winner's disarm)
reloads state fresh right before writing rather than reusing the snapshot loaded before the
per-line evaluate() loop, or it would clobber any spike re-arm evaluate() persisted mid-loop for
a different line this same tick. transport_habituation.observe_and_log() keeps receiving
all_candidates unchanged in shape, but under EDGE_TRIGGER=True that list is now the edge-filtered
pool (armed candidates only) rather than every threshold-crossing candidate — see that module's
own docstring note.

FELT RECALL AS CONSUMER (D-0294, J-1433, 2026-09-28): Build order step 4 retargets the eventual
consumer from the retired text-courier swap (D-0293/J-1430) to felt recall
(docs/staged/memory_as_a_service.md §3). Two halves, split by which worktree can reach which file
this session (F-2110 — felt_recall.py lives on the still-unmerged jobrun/memory_as_a_service
branch, unreachable from this one; see that finding for the file-overlap evidence):
  (a) THIS file gains verdict(line_id) below — a read-only per-line query felt_recall.py calls
      once per trigger edge, after its own observe(f"world:{dim}:{place}", now, 1.0) registers
      the non-sound dimensions as dispatcher lines (sound/life lines already flow through
      observe() via sound_knowledge.py/couriers.py — unchanged, unrelated to this job).
  (b) Wiring core/felt_recall.py's trigger-edge handler to actually CALL observe()/verdict() and
      write the result into its ride row as dispatcher_verdict is NOT done by this commit — it
      needs a worktree that has felt_recall.py, which this one does not. See job-queue for the
      follow-up (spawned this session) once memory_as_a_service's worktree lands or merges.
"""
from __future__ import annotations

import json
import functools
import math
import threading
import time
from pathlib import Path
from typing import Optional

from core import profile

_ROOT = Path(__file__).parent.parent
_STATE = _ROOT / "data" / "transport_lines.json"
_SHADOW_LOG = _ROOT / "data" / "transport_shadow.jsonl"

TRANSPORT_LIVE = False   # shadow-first (Discipline section); see module docstring

# ── Cold-start gate (D-0064 param 2, verbatim from the plan) ──────────────────────────────────
MIN_SAMPLES   = 20     # observations
MIN_AGE_DAYS  = 3       # days since the line's first-ever observation
# "whichever later" = a line is trusted only once BOTH gates have passed (see _cold_start below).

# ── Baseline stickiness (D-0064 param 3 — builder-chosen concrete value, see module docstring) ─
HALF_LIFE_DAYS = 14.0   # a past sample's pull on rate_ema/gap_ema halves every this many days.
                         # Time-weighted EMA (not tick-count-weighted): irregular inter-occurrence
                         # gaps are the only "clock" a line has, so alpha is derived per-update
                         # from the elapsed wall time since that line's last observation.
_LAMBDA = math.log(2.0) / (HALF_LIFE_DAYS * 24.0)   # per-hour decay constant

# ── Trigger floors: how far past baseline before evaluate() even calls something a candidate ──
SPIKE_TRIGGER_RATIO   = 2.0   # current rate must be >= 2x rate_ema to register as a spike at all
DROUGHT_TRIGGER_RATIO = 2.0   # time-since-last must be >= 2x gap_ema to register as a drought at all

# ── Windowed-rate fix for spike scoring (J-0584, 2026-09-04, F-0812) ──────────────────────────
# A spike candidate built from a SINGLE inter-arrival gap (instant_rate = 1/gap) is a heavy-tailed
# estimator: as gap -> 0 the ratio explodes without bound, and — the part that actually saturated
# dispatch — evaluate() re-reports that SAME stale instant_rate on every dispatch_tick() call until
# the line's NEXT observation replaces it, so one short gap on a quasi-continuous line (bees,
# footsteps, fantail chatter — bursty EVENT lines, not BEDS) keeps "spiking" long after the gap
# itself. Isolated replay (this job's finding) shows single-gap noise alone crosses the D-0064
# dispatch bar on ~1/3 of observations even for a pure, unchanged-rate Poisson line — the taxonomy
# ("happening MORE than usual RIGHT NOW", docs/plans/transport_manager.md) was never degenerate;
# the single-sample estimator was. Fix (docs/staged/loop_wiring_matrix.md's own proposed remedy):
# judge the CURRENT rate over a window sized to the line's own established gap_ema, not one gap.
# This changes what SPIKE_TRIGGER_RATIO/DISPATCH_THRESHOLD are compared against; it does not
# change either constant, nor any of D-0064's four ruled parameters (DISPATCH_THRESHOLD,
# MIN_SAMPLES/MIN_AGE_DAYS, HALF_LIFE_DAYS, line granularity) — no new /decide required per this
# job's own briefing. Drought (already judged against elapsed time, not a single gap) is untouched.
WINDOW_GAP_MULTIPLE = 3.0          # spike window = this many of the line's own established gaps
MIN_WINDOW_HOURS    = 1.0 / 12.0   # floor (5 min) so a very-frequent line's window still spans
                                    # several dispatch ticks rather than collapsing to ~one
_RECENT_TS_CAP = 64                # bounded per-line ring buffer for the windowed count (state-size guard)

# ── Edge-trigger kill-switch (D-0294, 2026-09-26/27; J-1432, 2026-09-28) ──────────────────────
# F-1989/F-1990: LEVEL polling (the behaviour below when this is False) means a line whose ratio
# is over the bar stays a "candidate" on EVERY tick until something else outweighs it — a stale
# drought (since_hours only grows without a fresh observe()) wins for days straight, then when
# observations resume the candidate pool collapses and dispatch goes silent by turns (100% fired
# W35-W37, 0-7% the week after). D-0177's habituation-discount mitigation could not fix this
# (would_fired_share stuck at 100%, F-0949) because nothing ever ends a stale winner's candidacy.
# EDGE_TRIGGER=True fires a spike/drought candidate only on the tick its ratio FIRST crosses the
# trigger while armed, then disarms that (line, kind) until it re-arms (see observe()/evaluate()
# below) — so a runner-up gets a turn instead of one line winning forever. Novelty is unaffected
# (it already has its own once-ever consume via novelty_pending/novelty_fired). Kill-switched:
# False restores today's level-polling behaviour exactly, byte-for-byte (no armed-flag reads,
# writes, or gating anywhere below) — D-0294's ruling verbatim: "EDGE_TRIGGER=True; False restores
# level polling exactly". TRANSPORT_LIVE stays False regardless (shadow-only either way).
EDGE_TRIGGER = True

# ── Dispatch gate (D-0064 param 1: conservative — builder-chosen concrete value, see docstring) ─
# weight = ratio - 1 for spike/drought (0 at the trigger floor, rising with excess). Novelty is
# always weight 1.0 (maximal, no ratio). Setting DISPATCH_THRESHOLD ABOVE the trigger floor's own
# weight (which is SPIKE_TRIGGER_RATIO-1 = 1.0) means being a bare 2x candidate is not enough on
# its own to win dispatch — matches "not everything that was produced is useful" / start rare,
# tune down from the shadow log per the plan's own kill-criterion.
DISPATCH_THRESHOLD = 1.5   # requires ~2.5x baseline (spike) or ~2.5x established gap (drought)


class Candidate:
    """One line's salience reading at evaluate()/dispatch_tick() time."""
    __slots__ = ("kind", "weight", "line_id", "detail")

    def __init__(self, kind: str, weight: float, line_id: str, detail: Optional[dict] = None):
        self.kind = kind              # "novelty" | "spike" | "drought"
        self.weight = float(weight)
        self.line_id = line_id
        self.detail = detail or {}

    def to_dict(self) -> dict:
        return {"kind": self.kind, "weight": round(self.weight, 3), "line_id": self.line_id,
                **self.detail}

    def __repr__(self):
        return f"Candidate({self.kind}, {self.line_id}, weight={self.weight:.2f})"


# J-3305 (restart-gated; F-3900): core/felt_recall.py's observe()+verdict() per trigger edge now runs on the
# orchestrator's substrate worker thread (core/orchestrator.py _substrate_db_work) while cat_loop / life /
# sound_knowledge / the loop's own dispatch_tick() call the same functions from the event loop or other threads.
# observe() and evaluate()/dispatch_tick()'s state edits are load -> modify -> save on one JSON file with no
# guard, so two overlapping calls could lose an update. One re-entrant lock serialises the three state-touching
# entry points (verdict() goes through evaluate()); each holds it for milliseconds. It guards nothing else.
_STATE_LOCK = threading.RLock()


def _locked(fn):
    @functools.wraps(fn)
    def _wrapper(*args, **kwargs):
        with _STATE_LOCK:
            return fn(*args, **kwargs)
    return _wrapper


def _load() -> dict:
    try:
        # J-4426 (F-5128): a damaged transport_lines.json is logged and falls back to transport_lines.json.prev.
        from core import store_persist as _sp
        return _sp.read_json_durable(_STATE, "transport_manager", guard=profile.guard_path)
    except Exception:
        return {}


def _load_ro() -> dict:
    """J-2417 (F-3117): READ-ONLY cached twin of _load() (same dict while the file's mtime/size are unchanged).
    SHARED result: never mutate it. Same fail-open {} on any error."""
    try:
        from core import store_persist as _sp
        return _sp.load_json_cached(_STATE)
    except Exception:
        return {}


def _save(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-0932: real data/ only if this process is live; raises
    # before any I/O if not (D-0179, J-0704). Resolved OUTSIDE the fail-open try below, exactly
    # like the other ~21 already-fenced modules, so the refusal is never swallowed as a disk error.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d))   # J-4426 (F-5128): was in place; now fsync + .prev
    except Exception:
        pass


def _log_shadow(candidate: Optional[Candidate], n_lines: int) -> None:
    """One row per dispatch_tick() call, fired or not — this is how the plan's own
    pre-registered signature ("what fraction of ticks produce a candidate at all — should be
    LOW") gets a real answer instead of only ever seeing the ticks that fired."""
    path = profile.guard_path(_SHADOW_LOG)   # J-0932: same fence as _save() above, resolved
    # independently since _SHADOW_LOG is a distinct path constant from _STATE.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # J-1432/D-0294: one added field, shape otherwise unchanged, so F-1989's per-tick series
        # is still the direct before/after (level vs edge) the finding compares.
        row = {"ts": round(time.time(), 1), "live": TRANSPORT_LIVE, "edge": EDGE_TRIGGER,
               "n_lines": n_lines, "fired": candidate is not None}
        if candidate is not None:
            row.update(candidate.to_dict())
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _cold_start(line: dict, now: float) -> bool:
    """True while the line's baseline is not yet trustworthy — both gates must have passed
    ('whichever later', D-0064 param 2): enough samples AND enough elapsed age."""
    n_total = int(line.get("n_total", 0))
    first_ts = line.get("first_ts")
    age_days = (now - first_ts) / 86400.0 if first_ts else 0.0
    return not (n_total >= MIN_SAMPLES and age_days >= MIN_AGE_DAYS)


@_locked
def observe(line_id: str, ts: float, n: float = 1.0) -> None:
    """Called by a factory the instant it produces freight. Updates that line's rolling EMA
    baseline. Zero LLM; pure arithmetic; never raises (fail-open, matching every other
    ledger/state module in this codebase)."""
    if not line_id or n <= 0:
        return
    try:
        state = _load()
        lines = state.setdefault("lines", {})
        is_new = line_id not in lines
        line = lines.setdefault(line_id, {})
        if is_new:
            line["first_ts"] = ts
            line["n_total"] = 0
            line["rate_ema"] = None
            line["gap_ema"] = None
            line["last_instant_rate_hr"] = None
            line["novelty_pending"] = True   # birth candidate, consumed once by dispatch_tick
            line["novelty_fired"] = False
            # Edge-trigger armed flags (D-0294/J-1432): additive, default True. Legacy lines
            # already on disk without these fields read as armed too, via line.get(..., True)
            # in evaluate()/dispatch_tick() below — no migration needed.
            line["spike_armed"] = True
            line["drought_armed"] = True

        last_ts = line.get("last_ts")
        if last_ts is not None and ts > last_ts:
            gap_hours = (ts - last_ts) / 3600.0
            if gap_hours > 0:
                instant_rate = 1.0 / gap_hours     # occurrences/hour implied by this single gap
                # Time-weighted EMA alpha: the gap IS the elapsed wall time since this line's
                # last EMA update (no separate clock needed — see module docstring).
                alpha = min(1.0, max(0.0, 1.0 - math.exp(-_LAMBDA * gap_hours)))
                line["rate_ema"] = instant_rate if line.get("rate_ema") is None else (
                    line["rate_ema"] + alpha * (instant_rate - line["rate_ema"]))
                line["gap_ema"] = gap_hours if line.get("gap_ema") is None else (
                    line["gap_ema"] + alpha * (gap_hours - line["gap_ema"]))
                line["last_instant_rate_hr"] = instant_rate

        # Windowed-rate fix (J-0584): bounded ring buffer of recent occurrence timestamps, used by
        # evaluate() to judge the CURRENT rate over a window instead of a single gap. Additive
        # field — old state files without it just start empty via setdefault.
        recent = line.setdefault("recent_ts", [])
        recent.append(ts)
        if len(recent) > _RECENT_TS_CAP:
            del recent[: len(recent) - _RECENT_TS_CAP]

        line["n_total"] = int(line.get("n_total", 0)) + (n if n >= 1 else 1)
        line["last_ts"] = ts
        if EDGE_TRIGGER:
            # Re-arm rule (D-0294): "drought re-arms on the next observe() call for that line —
            # a fresh occurrence ends the drought." Unconditional on every observe(), including
            # this line's very first ever (a no-op there, already True from the is_new block).
            line["drought_armed"] = True
        _save(state)
    except Exception:
        pass
    # J-4382 (D-0854, strings Phase 2): cause-as-object shadow, observe-only, fail-open, own state/log.
    try:
        from core import transport_cause_shadow as _tcs
        _tcs.observe(line_id, ts, n)
    except Exception:
        pass


@_locked
def evaluate(line_id: str) -> list:
    """Return any salience Candidates for this line RIGHT NOW. Read-only for novelty/drought
    (does not consume the novelty flag — dispatch_tick does that, once, only for the line it
    actually surfaces). Under EDGE_TRIGGER=True this is a conditional WRITER for spike only: the
    one re-arm path that belongs here rather than in observe(), because a spike cools by elapsed
    time (the windowed rate dropping back under SPIKE_TRIGGER_RATIO), not by a fresh occurrence
    (D-0294) — persisted immediately so a later evaluate()/dispatch_tick() call in the same
    process sees it re-armed without needing its own observe(). When EDGE_TRIGGER=False this
    function performs no writes at all, matching its pre-J-1432 read-only contract exactly."""
    out: list = []
    try:
        state = _load_ro()   # J-2417: shared cached read; the one write below re-loads fresh and edits that
        line = (state.get("lines") or {}).get(line_id)
        if not line:
            return out
        now = time.time()
        changed = False   # J-1432: only spike re-arm (below) ever sets this

        if line.get("novelty_pending") and not line.get("novelty_fired"):
            out.append(Candidate("novelty", 1.0, line_id,
                                  {"detail_text": "first occurrence on this line"}))

        if _cold_start(line, now):
            return out   # below MIN_SAMPLES/MIN_AGE_DAYS: only novelty may fire (above)

        rate_ema = line.get("rate_ema")
        gap_ema = line.get("gap_ema")
        instant_rate = line.get("last_instant_rate_hr")
        if rate_ema and rate_ema > 0:
            # Windowed-rate fix (J-0584): judge the CURRENT rate over a window sized to this
            # line's own established gap_ema, not the single most-recent gap (see constants above
            # for why). window_hours falls back to MIN_WINDOW_HOURS if gap_ema isn't set yet.
            window_hours = max((gap_ema or 0.0) * WINDOW_GAP_MULTIPLE, MIN_WINDOW_HOURS)
            window_start = now - window_hours * 3600.0
            recent = line.get("recent_ts") or []
            window_n = sum(1 for t in recent if t >= window_start)
            windowed_rate = window_n / window_hours if window_hours > 0 else 0.0
            ratio = windowed_rate / rate_ema
            if EDGE_TRIGGER and ratio < SPIKE_TRIGGER_RATIO and not line.get("spike_armed", True):
                # Re-arm rule (D-0294): "spike re-arms when evaluate() sees the windowed rate
                # ratio drop below SPIKE_TRIGGER_RATIO" — cooled off, no fresh observe() needed.
                changed = True
            if ratio >= SPIKE_TRIGGER_RATIO and ((not EDGE_TRIGGER) or line.get("spike_armed", True)):
                out.append(Candidate("spike", ratio - 1.0, line_id,
                                      {"ratio": round(ratio, 2), "rate_ema": round(rate_ema, 4),
                                       "windowed_rate_hr": round(windowed_rate, 4),
                                       "window_hours": round(window_hours, 4), "window_n": window_n,
                                       "instant_rate_hr": round(instant_rate, 4) if instant_rate else None}))

        last_ts = line.get("last_ts")
        if gap_ema and last_ts and gap_ema > 0:
            since_hours = (now - last_ts) / 3600.0
            ratio = since_hours / gap_ema
            if ratio >= DROUGHT_TRIGGER_RATIO and ((not EDGE_TRIGGER) or line.get("drought_armed", True)):
                out.append(Candidate("drought", ratio - 1.0, line_id,
                                      {"ratio": round(ratio, 2), "gap_ema": round(gap_ema, 4),
                                       "since_hours": round(since_hours, 2)}))
                # No re-arm-by-cooling path for drought: since_hours cannot shrink without a
                # fresh observe() (gap_ema is frozen too without one), so unlike spike there is
                # no "drought cooled on its own" event for evaluate() to notice here — re-arming
                # drought is entirely observe()'s job (D-0294), already applied above.

        if changed:
            fresh = _load()   # J-2417: edit a private fresh copy, never the shared cached one
            fl = (fresh.get("lines") or {}).get(line_id)
            if fl is not None:
                fl["spike_armed"] = True
                _save(fresh)
    except Exception:
        pass
    return out


def verdict(line_id: str) -> dict:
    """Read-only dispatcher verdict for ONE line, right now (J-1433/D-0294) — felt recall's Phase 1
    gate calls this per trigger edge to ask "does the dispatcher currently rate this line unusual",
    without touching dispatch_tick()'s cross-line competition or any of its state mutations.

    Built directly from evaluate()'s own candidate list for this line — never calls dispatch_tick()
    — so nothing is consumed: unlike dispatch_tick(), this never sets novelty_fired=True or
    *_armed=False. A line can be asked repeatedly, every tick, at zero cost, exactly like calling
    evaluate() itself (evaluate()'s own spike-re-arm write, when EDGE_TRIGGER=True, is an idempotent
    state-cooling correction it already makes on every call regardless of who calls it — not a
    consume). Works unchanged under EDGE_TRIGGER=True or False: evaluate()'s own candidate list
    already reflects whichever mode is active; this helper adds no EDGE_TRIGGER-specific branching
    of its own (verified both ways, scripts/_test_transport_manager.py §8e).

    Returns {"verdict": "novel"|"spike"|"drought"|"none", "weight": float, "cold_start": bool}.
    When evaluate() returns more than one candidate for the line (novelty cannot itself co-occur
    with a cold-start-gated spike/drought, but a backdated/synthetic line can carry novelty
    alongside an already-established spike or drought — see §8c), the higher-weight one wins,
    mirroring dispatch_tick()'s own tie-break.

    "cold_start" is additive beyond the job briefing's literal 2-key return shape, because the
    Phase 1 gate as specified ("a tug applies only when dispatcher_verdict is not none, OR the
    line is still cold-start — do not silence a new dimension for lack of history") cannot be
    implemented by the caller from "verdict"/"weight" alone: a brand-new world:<dim>:<place> line
    whose one-time novelty has already been consumed by some OTHER line winning a dispatch_tick()
    (routine — dispatch_tick() already scans every registered line, felt recall's new lines
    compete for the same single winner slot like any other) would otherwise read as an ordinary
    "none", indistinguishable from a truly-established, truly-unremarkable line. Exposing the same
    cold-start test evaluate() already gates spike/drought on (_cold_start, MIN_SAMPLES/
    MIN_AGE_DAYS) lets the caller tell the two apart, which the gate's own "do not silence" clause
    requires. Purely additive (an extra dict key); a caller reading only .get("verdict")/
    .get("weight") is unaffected.

    Deliberately ignores DISPATCH_THRESHOLD (D-0064 param 1, the CROSS-LINE winner-take-one bar):
    a single line's own verdict is "does evaluate() consider this line spiking/in drought/novel
    right now" (TRIGGER_RATIO's bar, 2.0x baseline) — not "would this line beat every other
    registered line for the one shared dispatch slot this tick." Felt recall's world:<dim>:<place>
    lines do not compete with sound/life lines for a delivery slot, so gating them at the tighter
    cross-line bar would silence a line the dispatcher itself already calls unusual. If a live read
    (memory_as_a_service.md §8) later shows this is too liberal, that is a DISPATCH_THRESHOLD-vs-
    TRIGGER_RATIO tuning question for a future decision, not a defect in this helper.

    Fail-open, matching every other function in this module: any exception returns
    {"verdict": "none", "weight": 0.0, "cold_start": True} — the fail-open direction the gate's own
    "do not silence for lack of history" bias implies — rather than raising into the caller's tick.
    """
    try:
        candidates = evaluate(line_id)
        state = _load_ro()
        line = (state.get("lines") or {}).get(line_id)
        cold = line is None or _cold_start(line, time.time())
        if not candidates:
            return {"verdict": "none", "weight": 0.0, "cold_start": cold}
        best = max(candidates, key=lambda c: c.weight)
        kind = "novel" if best.kind == "novelty" else best.kind
        return {"verdict": kind, "weight": round(best.weight, 3), "cold_start": cold}
    except Exception:
        return {"verdict": "none", "weight": 0.0, "cold_start": True}


@_locked
def dispatch_tick() -> Optional[Candidate]:
    """Periodic scan: evaluate every registered line, return the SINGLE highest-weight candidate
    above DISPATCH_THRESHOLD, or None. This is the competition the founder described — many
    things may be candidates; only the winner rides the bus this cycle. Always logs its own
    verdict to the shadow log (fired or not), regardless of TRANSPORT_LIVE — see module
    docstring: nothing calls this yet in production (that periodic wiring + the eventual courier
    swap is explicit follow-up work, not part of this build). Under EDGE_TRIGGER=True (D-0294),
    a spike/drought winner is disarmed here (fired once) — see the EDGE_TRIGGER constant's
    comment for the re-arm rules and module docstring for why the final state mutation below
    reloads fresh rather than reusing the snapshot taken before the per-line evaluate() loop."""
    winner: Optional[Candidate] = None
    all_candidates: list = []
    try:
        state = _load_ro()
        line_ids = list((state.get("lines") or {}).keys())
        best_weight = float("-inf")
        for lid in line_ids:
            for cand in evaluate(lid):
                all_candidates.append(cand)
                if cand.weight > best_weight:
                    best_weight = cand.weight
                    winner = cand
        if winner is not None and winner.kind != "novelty" and winner.weight < DISPATCH_THRESHOLD:
            # Novelty is exempt from DISPATCH_THRESHOLD (plan's own taxonomy: "maximal salience
            # by definition; no baseline needed to judge it") — only spike/drought, which ARE
            # baseline-relative ratios, are gated by the conservative dispatch bar.
            winner = None
        if winner is not None and (winner.kind == "novelty" or EDGE_TRIGGER):
            # J-1432: reload fresh here rather than reusing `state` from before the evaluate()
            # loop above — under EDGE_TRIGGER, evaluate() may itself have written a spike re-arm
            # for some OTHER line during that loop (a conditional writer now, see its docstring);
            # saving the stale pre-loop `state` back out would silently clobber that write. This
            # was already a latent (inert) staleness gap in the novelty-consume path below —
            # harmless before J-1432 because evaluate() never wrote anything, real now.
            try:
                fresh = _load()
                line_rec = (fresh.get("lines") or {}).get(winner.line_id)
                if line_rec is not None:
                    if winner.kind == "novelty":
                        # consume the birth candidate so it never fires twice for this line
                        line_rec["novelty_pending"] = False
                        line_rec["novelty_fired"] = True
                        _save(fresh)
                    elif winner.kind in ("spike", "drought"):
                        # fired once (D-0294): stays disarmed until its own re-arm rule fires
                        # (drought: this line's next observe(); spike: evaluate() sees it cool).
                        line_rec[f"{winner.kind}_armed"] = False
                        _save(fresh)
            except Exception:
                pass
        _log_shadow(winner, len(line_ids))
        # Habituation shadow (J-0603, F-0828, dosed_coupling's own Weight law): observe-only, never
        # affects `winner` — see core/transport_habituation.py's module docstring for why this
        # exists (a repeat winner like a stale drought line currently has nothing discounting it).
        try:
            from core import transport_habituation as _thab
            _thab.observe_and_log(all_candidates, winner, DISPATCH_THRESHOLD)
        except Exception:
            pass
        # Cause-as-object shadow (J-4382, D-0854): both scorings side by side; never touches `winner`.
        try:
            from core import transport_cause_shadow as _tcs
            _tcs.tick(all_candidates, DISPATCH_THRESHOLD)
        except Exception:
            pass
    except Exception:
        # J-0932: this fallback call is itself a writer (_log_shadow -> guard_path()) — if the
        # outer try's own exception WAS a NonLiveWriteError (a non-live, non-redirected caller,
        # exactly what this fence exists to catch), retrying the same fenced write here would
        # raise a second, uncaught NonLiveWriteError that escapes dispatch_tick() entirely,
        # breaking the module's documented fail-open contract (observe()'s own docstring: "never
        # raises") for no reason — the refusal was already real on the first call. Swallow it here
        # too, matching every other writer call site in this module.
        try:
            _log_shadow(None, 0)
        except Exception:
            pass
    return winner


def status() -> dict:
    """For du_pulse / the HUD — line count, cold-start count, shadow-log size."""
    try:
        state = _load_ro()
        lines = state.get("lines") or {}
        now = time.time()
        cold = sum(1 for l in lines.values() if _cold_start(l, now))
        shadow_rows = 0
        fired_rows = 0
        if _SHADOW_LOG.exists():
            for line in _SHADOW_LOG.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                shadow_rows += 1
                try:
                    if json.loads(line).get("fired"):
                        fired_rows += 1
                except Exception:
                    pass
        return {"live": TRANSPORT_LIVE, "lines_registered": len(lines), "lines_cold_start": cold,
                "shadow_ticks": shadow_rows, "shadow_fired": fired_rows}
    except Exception:
        return {"live": TRANSPORT_LIVE, "lines_registered": 0, "lines_cold_start": 0,
                "shadow_ticks": 0, "shadow_fired": 0}
