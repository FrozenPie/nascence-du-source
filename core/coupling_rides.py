"""
coupling_rides — Dosed Coupling Phase 1: publish + ride log, observe-only (D-0152 GO, 2026-09-05).

The law (docs/staged/dosed_coupling.md §1): every standing loop PUBLISHES a small typed tuple of
coordinates; NO loop gets a standing view of another; reading is dosed per stop and dispatched by
surprise. Phase 1 builds only the first half — the publishers and the log — so that Phase 2's cups
have something to ride and so that the D-0149 defeater clock (two weeks of ride log) can start.

Registry variant (founder ruling D-0152): the tuples live HERE, in this module's process-local
registry, not as a field on CognitiveState. The ONLY accessor is read(), which writes a ride row.
Phase 1 has zero callers of read() — that is the point. Anything that wants a coordinate later
(Phase 2) has to come through the one door that logs it, so the matrix in
docs/staged/loop_wiring_matrix.md can be re-derived from data/coupling_rides.jsonl, not from another
mapping pass over the code.

Row schema (data/coupling_rides.jsonl, append-only):
  {"ts", "kind": "publish", "loop", "stop", "tuple": {...}}
  {"ts", "kind": "ride",    "stop", "line", "dose", "value": {...}, "what_changed_next": None}

Publishers (every value already computed by its loop; this module only names it and writes it down):
  climate      — ClimateEngine.tick():          9 ClimateField dims by name, dissonance, explore_value,
                                                 ignition_level. Registry every tick; a LOG ROW only when a
                                                 dim moved ≥ CLIMATE_MIN_DELTA or CLIMATE_MAX_GAP_S elapsed.
  stream       — stream_drive.observe():        drive, ignition, grounded, progress, redundancy, train_kind,
                                                 train_len (the shadow row's own fields).
  deliberation — Orchestrator, end of cycle:    recall_confidence, tensions_carried, coherence,
                                                 dissonance_count, think_license, critic_verdict,
                                                 cycles_since_human, input_type.
  witness      — lane2 tick, after _log(rec):   break_rate_24h, grounded_share, distinct_share_24h,
                                                 hint_consumed_24h, n_judged_24h, and (Phase 1,
                                                 D-0241 shadow-first, J-1161, only set on a judged
                                                 break) topic, horizon, cup_would_ride.
  ledgers      — inner_monologue, per thought:  commitments_active, commitments_load_bearing,
                                                 escalations_1h, tension_top3, frontier_open,
                                                 pursuits_active, pursuits_heat_max (read-only collector,
                                                 rate-limited to LEDGERS_MIN_GAP_S).

  si           — self_interrogation, per judged fire (J-2008, D-0396, COORDINATE-ONLY shadow): doubted (bool; True only
                                                 when the decoupled panel judged the reflection genuine), ledger_idx (1-based
                                                 index, in the train's own established-points ledger, of the point that was
                                                 doubted), train_id, cycle. NEVER Du's reflection text (rule 1: coordinates,
                                                 never prose). Age is derived at the stop (now - the tuple's ts).

THE WITNESS CUP IS A CONSUMABLE, NOT A TUPLE (F-1952/J-1390, 2026-09-27): `read(dose="cup")` on the
witness line does NOT return `_REG["witness"]` (that per-tick tuple keeps republishing every ~TICK_S
for the bucket/status() readers, unchanged). It drains a separate one-entry, TTL'd, rate-capped
"witness-cup" slot instead — `publish_witness()` places into it only when the topic-habituation gate
says a break is novel, and the FIRST `read()` call that finds it non-empty and unexpired takes it and
clears it, so a break rides at most once. Before this fix, the cup WAS the per-tick tuple, republished
every lane2 tick (~300-361s) and read by every idle thought inside that window (median gap ~78s,
~46/h) — one break rode into 4-5 consecutive idle thoughts, not the "one candidate, never guaranteed"
§7.3.1 promised. See `read()`/`_consume_cup()`/`_place_cup()` below for the mechanism, mirrored
directly off the Tap-on-the-Shoulder's own consume-once/TTL/rate-cap shape (`core/lane2.py`).

Everything here is fail-open: no publisher may ever raise into its caller, and COUPLING_PUBLISH=False
makes every call a no-op. Pre-registered read (7 days live, §4a): presence ≥ 95% of each loop's own
ticks; four behaviour metrics inside their prior-week band; file < 5 MB/day.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from collections import deque
from pathlib import Path

from core import profile   # J-1821 / F-2453: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.coupling")

# ── flags / tunables (D-0152: GO flips the flag on in the same commit as the build) ────────────
COUPLING_PUBLISH: bool = True
CLIMATE_MIN_DELTA: float = 0.05      # a dim must move this much to earn a climate log row ...
CLIMATE_MAX_GAP_S: float = 60.0      # ... or this much time must pass since the last one
LEDGERS_MIN_GAP_S: float = 600.0     # the collector parses subconscious_state.json (60 MB) + pursuits (9 MB) +
                                     # frontier (4 MB); climate already parses the first every 5 s tick, so
                                     # once per 10 min adds <1% to that existing cost and never blocks a thought
WITNESS_WINDOW_S: float = 24 * 3600.0

# ── the witness CUP's own tunables (F-1952/J-1390, 2026-09-27) ──────────────────────────────────
# Mirrored off the Tap-on-the-Shoulder's OWN constants (core/lane2.py) as starting defaults, same
# "reuse verbatim, retune later from real data" discipline lane2_break_habituation.py already used
# for its GROWTH_STEP/CEILING/etc. -- copied as fresh constants here, not cross-module-imported, so
# each side stays independently retunable (the two channels are symmetric in SHAPE, not fused).
CUP_TTL_S: float = 1800.0            # = core/lane2.py HINT_TTL_S -- unclaimed cup expires after 30 min
CUP_MAX_PLACE_PER_WINDOW: int = 4    # = core/lane2.py HINT_MAX_PUSH_PER_WINDOW -- overall cap on cup
                                     # PLACEMENTS regardless of topic; separate from (on top of) the
                                     # per-topic novelty gate (lane2_break_habituation.observe_break's
                                     # own cup_would_ride) the same way the Tap's own push-rate cap is
                                     # separate from law 4b's per-topic reachability check.
CUP_RATE_WINDOW_S: float = 3600.0    # = core/lane2.py HINT_RATE_WINDOW_S

# ── PHASE 2 SHADOW (D-0370 / D-0371, J-1957, dosed_coupling.md §4b) ────────────────────────────
# COUPLING_PHASE2 gates ONLY extra logging: the residual-gate verdict logged BESIDE the spike-gate verdict
# on the same row, the `probe` rows, and the composed `hub` key. Nothing rides into a prompt or a
# controller; False restores Phase-1 behaviour byte for byte (no `gates` field, no probe rows, no hub).
COUPLING_PHASE2: bool = True
SPIKE_EMA_ALPHA: float = 0.05        # publisher-side spike gate: a coordinate vs ITS OWN running mean ...
SPIKE_Z: float = 3.0                 # ... fires at >= this many running mean-absolute-deviations ...
SPIKE_MIN_N: int = 20                # ... once the coordinate has this many publishes behind it
SPIKE_MAD_FLOOR_FRAC: float = 0.02   # mad floor as a fraction of the observed range (a flat line must not fire on noise)
SPRING_B0: float = 0.15              # residual gate: resting antagonist b, as a fraction of the line's observed range
SPRING_STEP: float = 0.10            # b grows by this each time the gate fires (activation) ...
SPRING_DECAY: float = 0.90           # ... and relaxes toward SPRING_B0 by this factor on each quiet read
SPRING_MAX: float = 0.90
# J-2247 / D-0446 (F-2925): the residual gate's expectation E updates ONLY on a NEW publish of the line, never on a
# re-read of the same published tuple. The idle-seed probe runs every ~67 s while ledgers publish every ~10 min, so the
# old per-read persistence prior compared a value to itself on 74 percent of moments (residual exactly 0). Chosen over a
# slower per-reader EMA because it is parameter-free (no alpha to guess before any data) and gives exactly one residual
# verdict per piece of new evidence; a re-read of the same publish logs fresh=False with residual None and leaves E and
# the spring untouched. Shadow logging only, no consumer. False restores the J-1957 per-read prior byte for byte.
RESIDUAL_E_ON_NEW_PUBLISH: bool = True
# D-0750 (J-3972, F-4480): the residual half of the gate pair is DROPPED on the four climate lines only. On the J-2264
# read completion_tension / identity_pressure had 0 percent residual fire and world_model_strain / novelty_hunger agreed
# with the spike gate over 90 percent (base-rate-bound at 1-5 percent fire shares). The ledgers lines
# (escalations_1h, frontier_open) keep the residual half. Dropped = the entry keeps its spike verdict but residual /
# felt / residual_fire are None, and E and the spring are not touched. False restores the D-0446 behaviour exactly.
RESIDUAL_DROP_CLIMATE: bool = True
RESIDUAL_DROPPED_LINES: dict = {"climate": ("completion_tension", "identity_pressure",
                                            "world_model_strain", "novelty_hunger")}
PROBE_MIN_GAP_S: float = 30.0        # a stop's shadow probe is rate-limited (idle thoughts run ~46/h)
HUB_MIN_GAP_S: float = 0.0           # compose() rides the ledgers collector's own 10-min cadence; no extra limit
# the lines a stop WOULD drink from, shadow only (§4 Phase 2: "one climate dim by name at the idle seed" -- a
# few are probed so the 7-day read has enough moments to compare the two gates on; nothing is returned).
PROBE_LINES: dict = {
    "idle thought seed": [("climate", ["completion_tension", "identity_pressure", "world_model_strain",
                                       "novelty_hunger"]),
                          ("ledgers", ["escalations_1h", "frontier_open"]),
                          ("hub", ["pressure", "momentum", "strain", "load"])],
}

# ── the open-doubt (si) cup, SHADOW ONLY (D-0396, J-2008, docs/staged/dosed_coupling.md 4b) ─────
# self_interrogation.interrogate() publishes a typed COORDINATE -- doubted flag + the ledger index of the point doubted
# + train id -- into the registry key `si`. At the NEXT step of the same train the stop calls si_would_ride(), which
# writes a `kind: "si_would_ride"` row (publisher + eligibility) and returns None: nothing is ever built into a prompt.
# One cup per train, consume-once per publish, TTL'd. The HOLD on live use stands until the lab replay passes
# (scripts/si_open_doubt_cup_replay.py). SI_CUP_SHADOW=False makes both calls no-ops.
SI_CUP_SHADOW: bool = True
SI_CUP_TTL_S: float = 600.0          # a doubt older than this at the next step is stale (median completion 15 s, F-2606)

_ROOT = Path(__file__).resolve().parent.parent
_DATA = _ROOT / "data"
_LOG = _DATA / "coupling_rides.jsonl"

# ── the registry (process-local; the only state this module holds) ─────────────────────────────
_REG: dict[str, dict] = {}
_climate_last_logged: dict = {"ts": 0.0, "coords": None}
_ledgers_last_ts: float = 0.0
_cycles_since_human: int = 0
_witness_window: deque = deque()     # (ts, notice, hinted: bool)
_break_rate_baseline_window: deque = deque()   # (ts, break_rate_24h) -- F-1953/J-1391, trailing
                                     # 7-day baseline feeding the sized bucket dose (option a).
                                     # Same process-local/unpersisted posture as _witness_window just
                                     # above: a restart empties it and it refills over the following
                                     # 7 days of ticks -- deliberate, disclosed (see
                                     # _trailing_break_rate_baseline()'s own docstring), and safe:
                                     # a thin baseline reads the excess as SMALL, never large.

# the witness cup (F-1952/J-1390): ONE entry, newest wins, distinct from _REG["witness"] above (that
# per-tick tuple is untouched, still feeds the bucket + status()/phase1_metric_sheet()). {"topic",
# "horizon", "verdict", "cup_would_ride", "ts"} or None. Process-local, unpersisted, same as _REG --
# a restart just loses whatever sat here unconsumed, same posture as this module's own registry.
_CUP_WITNESS: dict | None = None
_cup_place_log: deque = deque()      # placement timestamps, pruned to CUP_RATE_WINDOW_S on each place

# Phase 2 shadow state -- process-local like _REG; a restart simply starts with no expectation / no history.
_last_seen: dict = {}                # (stop, loop, key) -> value last drunk there  == the reader's persistence prior E
_pub_stats: dict = {}                # (loop, key) -> {"n","ema","mad","lo","hi","spike":{...}}  publisher-side history
_last_pub_seen: dict = {}            # (stop, loop, key) -> registry ts of the publish E was last updated from (J-2247)
_spring: dict = {}                   # (stop, loop, key) -> b, the squishy-spring antagonist of §1 rule 3
_probe_last: dict = {}               # stop -> ts of its last shadow probe
_si_pending: dict | None = None      # the one unconsumed si publish (consume-once, newest wins); process-local like _REG
_si_trains_served: dict = {}         # train_id -> ts of the would-ride row that used this train's one cup (bounded)


# J-1926 / F-2550: publish() runs on the loop thread and on the coupling-ledgers daemon thread (_collect_ledgers); serialise the append.
_APPEND_LOCK = threading.Lock()


def _append(row: dict) -> None:
    try:
        # J-1821 / F-2453 -- THE WRITE FENCE (D-0179): resolved BEFORE the mkdir so a refused (non-live) writer does not even create data/. Live, lab-sandbox and
        # outside-data paths get the same path back (byte-identical); refusal is swallowed by the fail-open except below.
        path = profile.guard_path(_LOG)
        _DATA.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _num(x, nd: int = 4):
    """Round numbers; pass None/bool/str through; recurse into dicts/lists (tension_top3 is a dict)."""
    try:
        if x is None or isinstance(x, (bool, str, int)):
            return x
        if isinstance(x, dict):
            return {str(k): _num(v, nd) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [_num(v, nd) for v in x]
        return round(float(x), nd)
    except Exception:
        return None


# ── the two verbs ──────────────────────────────────────────────────────────────────────────────
def publish(loop: str, stop: str, coords: dict, *, log: bool = True) -> None:
    """Update the registry for `loop` and (unless log=False) append a publish row. Never raises."""
    if not COUPLING_PUBLISH:
        return
    try:
        now = time.time()
        clean = {k: _num(v) for k, v in dict(coords).items()}
        _REG[loop] = {"ts": now, "stop": stop, **clean}
        if COUPLING_PHASE2:
            _track_spikes(loop, clean, now)
        if log:
            _append({"ts": round(now, 3), "kind": "publish", "loop": loop, "stop": stop, "tuple": clean})
    except Exception:
        pass


def read(stop: str, loop: str, keys: list[str] | None = None, dose: str = "cup") -> dict | None:
    """THE ONLY accessor. Returns the requested coordinates and writes a ride row so the read is
    traceable. Never raises; None when nothing is published/consumable or the flag is off.

    dose="cup" on loop="witness" is CONSUME-ONCE (F-1952/J-1390): drains the small witness-cup slot
    (`_CUP_WITNESS`, placed by `publish_witness()` below via `_place_cup()`, TTL'd at CUP_TTL_S)
    instead of `_REG[loop]` -- the first read that finds it non-empty and unexpired takes it and
    clears it, so a break rides exactly once, never into every idle thought inside the old per-tick
    window (see this module's own top docstring). Every other (loop, dose) pair is unchanged:
    `_REG[loop]`'s latest published tuple, same as Phase 1 always worked -- the bucket
    (`dose="bucket"`, `core/climate_engine.py`) and `status()`/`phase1_metric_sheet()` readers still
    see the plain per-tick tuple's own topic/horizon/cup_would_ride fields, untouched by this."""
    if not COUPLING_PUBLISH:
        return None
    try:
        if dose == "cup" and loop == "witness":
            return _consume_cup(stop, keys)
        tup = _REG.get(loop)
        if not tup:
            return None
        value = {k: tup.get(k) for k in keys} if keys else {k: v for k, v in tup.items()
                                                            if k not in ("ts", "stop")}
        row = {"ts": round(time.time(), 3), "kind": "ride", "stop": stop, "line": loop,
               "dose": dose, "value": value, "what_changed_next": None}
        if COUPLING_PHASE2 and loop != "hub":     # hub rides a STANDING allowance (D-0371): no dispatcher gate
            gates = _gates_for(stop, loop, value, tup.get("ts"))
            if gates:
                row["gates"] = gates
        _append(row)
        return value
    except Exception:
        return None


# ── Phase 2 shadow: the two gates, side by side, on identical moments (D-0370) ──────────────────
def _isnum(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _track_spikes(loop: str, clean: dict, now: float) -> None:
    """Publisher-side spike gate (what §4a's cups gate on today): each numeric coordinate against ITS OWN
    running mean / mean-absolute-deviation. Updated on every publish; the verdict of the latest publish is
    what a later read() reports. Also keeps the line's observed range (the residual gate's `scale_key`).
    Never raises."""
    try:
        for k, v in clean.items():
            if not _isnum(v):
                continue
            v = float(v)
            s = _pub_stats.get((loop, k))
            if s is None:
                _pub_stats[(loop, k)] = {"n": 1, "ema": v, "mad": 0.0, "lo": v, "hi": v,
                                         "spike": {"fire": False, "z": None, "ts": now}}
                continue
            rng = max(s["hi"] - s["lo"], 1e-9)
            dev = abs(v - s["ema"])
            denom = max(s["mad"], SPIKE_MAD_FLOOR_FRAC * rng, 1e-9)
            z = dev / denom
            fire = bool(s["n"] >= SPIKE_MIN_N and z >= SPIKE_Z)
            s["spike"] = {"fire": fire, "z": round(z, 3), "ts": now}
            s["ema"] += SPIKE_EMA_ALPHA * (v - s["ema"])
            s["mad"] += SPIKE_EMA_ALPHA * (dev - s["mad"])
            s["lo"], s["hi"] = min(s["lo"], v), max(s["hi"], v)
            s["n"] += 1
    except Exception:
        pass


def _gates_for(stop: str, loop: str, value: dict, pub_ts: float | None = None) -> dict:
    """For each numeric coordinate in `value`: the reader's expectation E (its own last-seen value at this
    stop), residual = value - E, the residual-gate verdict (felt = max(0, |residual|/scale - b), fires when
    felt > 0), and -- beside it -- the publisher-side spike-gate verdict. Updates the persistence prior and
    the per-(stop,line) spring. Returns {} when nothing is numeric. Never raises.

    J-2247 / D-0446: with RESIDUAL_E_ON_NEW_PUBLISH and a known `pub_ts` (the registry ts of the tuple read),
    each gate entry carries `fresh`. fresh=True: first read of that publish at this stop -- E is compared and
    then updated, the spring moves. fresh=False: a re-read of a publish already drunk here -- residual/felt/
    residual_fire are None and neither E nor the spring changes (no new evidence, no verdict). The spike
    verdict is reported either way; the paired read compares the two gates on fresh=True moments only."""
    out: dict = {}
    try:
        for k, v in (value or {}).items():
            if not _isnum(v):
                continue
            v = float(v)
            st = _pub_stats.get((loop, k)) or {}
            exp = _last_seen.get((stop, loop, k))
            sp = st.get("spike") or {}
            if RESIDUAL_DROP_CLIMATE and k in RESIDUAL_DROPPED_LINES.get(loop, ()):
                out[k] = {"expected": None, "residual": None, "felt": None, "residual_fire": None,
                          "spike_fire": sp.get("fire"), "spike_z": sp.get("z"), "residual_dropped": True}
                continue
            pub = pub_ts if RESIDUAL_E_ON_NEW_PUBLISH else None
            if pub is not None and _last_pub_seen.get((stop, loop, k)) == pub:
                out[k] = {"expected": None if exp is None else round(exp, 4), "residual": None, "felt": None,
                          "residual_fire": None, "spike_fire": sp.get("fire"), "spike_z": sp.get("z"),
                          "fresh": False}
                continue
            _last_seen[(stop, loop, k)] = v
            if pub is not None:
                _last_pub_seen[(stop, loop, k)] = pub
            g = {"expected": None if exp is None else round(exp, 4), "residual": None, "felt": None,
                 "residual_fire": None, "spike_fire": sp.get("fire"), "spike_z": sp.get("z")}
            if exp is not None:
                scale = max(float(st.get("hi", v)) - float(st.get("lo", v)), 1e-6)
                b = _spring.get((stop, loop, k), SPRING_B0)
                res = v - exp
                felt = max(0.0, abs(res) / scale - b)
                fire = felt > 0.0
                _spring[(stop, loop, k)] = min(SPRING_MAX, b + SPRING_STEP) if fire else \
                    max(SPRING_B0, SPRING_B0 + (b - SPRING_B0) * SPRING_DECAY)
                g.update(residual=round(res, 4), felt=round(felt, 4), residual_fire=fire,
                         b=round(b, 4), scale=round(scale, 4))
            if pub is not None:
                g["fresh"] = True
            out[k] = g
    except Exception:
        pass
    return out


def probe(stop: str) -> None:
    """Shadow-only: at `stop`, log what the stop WOULD drink (PROBE_LINES) with both gate verdicts, plus
    the hub on its standing allowance (D-0371: logged would-read rows before any stop actually drinks).
    Writes `kind: "probe"` rows -- deliberately NOT `kind: "ride"`, so nothing that counts real rides
    changes -- and returns None, so no caller can use a value. Rate-limited per stop. Never raises."""
    if not (COUPLING_PUBLISH and COUPLING_PHASE2):
        return
    try:
        now = time.time()
        if now - _probe_last.get(stop, 0.0) < PROBE_MIN_GAP_S:
            return
        _probe_last[stop] = now
        for loop, keys in PROBE_LINES.get(stop, []):
            tup = _REG.get(loop)
            if not tup:
                continue
            value = {k: tup.get(k) for k in keys}
            row = {"ts": round(now, 3), "kind": "probe", "stop": stop, "line": loop,
                   "dose": "standing" if loop == "hub" else "shadow-cup", "value": value}
            if loop != "hub":
                gates = _gates_for(stop, loop, value, tup.get("ts"))
                if gates:
                    row["gates"] = gates
            _append(row)
    except Exception:
        pass


# ── the hub: a deterministic composed summary, no LLM, no prose (D-0371) ────────────────────────
def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _sat(x: float, k: float) -> float:
    """x/(x+k): maps a non-negative count/rate onto [0,1) with k as the half-way point."""
    x = max(0.0, x)
    return x / (x + k)


# hub coordinate -> [(loop, key, normaliser)]  (the §4b table, existing coordinates only; plain mean, no weights)
HUB_INPUTS: dict = {
    "pressure": [("climate", "completion_tension", _clip01), ("climate", "identity_pressure", _clip01),
                 ("ledgers", "escalations_1h", lambda x: _sat(x, 3.0))],
    "momentum": [("stream", "progress", _clip01), ("stream", "train_len", lambda x: _sat(x, 8.0)),
                 ("stream", "drive", lambda x: _sat(x, 1.0)),
                 ("deliberation", "cycles_since_human", lambda x: _sat(x, 20.0))],
    "strain":   [("witness", "break_rate_24h", _clip01), ("deliberation", "dissonance_count", lambda x: _sat(x, 3.0)),
                 ("climate", "world_model_strain", _clip01)],
    "load":     [("ledgers", "commitments_active", lambda x: _sat(x, 5.0)),
                 ("ledgers", "tensions_n", lambda x: _sat(x, 60.0)),
                 ("ledgers", "frontier_open", lambda x: _sat(x, 200.0)),
                 ("ledgers", "pursuits_heat_max", _clip01)],
}


def compose() -> dict | None:
    """Publish the sixth registry key `hub` = (pressure, momentum, strain, load): each the plain mean of its
    normalised inputs among those currently published (an input not yet published is skipped, a coordinate
    with no inputs is None). Reads _REG directly -- it IS the registry's own aggregator, not a reader of
    another loop, so it goes through no dispatcher. No LLM, no prose, no new store. Runs from the ledgers
    collector's daemon thread (once per LEDGERS_MIN_GAP_S), never on the event loop. Never raises."""
    if not (COUPLING_PUBLISH and COUPLING_PHASE2):
        return None
    try:
        coords: dict = {}
        for name, inputs in HUB_INPUTS.items():
            vals = []
            for loop, key, norm in inputs:
                v = (_REG.get(loop) or {}).get(key)
                if _isnum(v):
                    vals.append(norm(float(v)))
            coords[name] = round(sum(vals) / len(vals), 4) if vals else None
        publish("hub", "compose", coords)
        return coords
    except Exception:
        return None


def _consume_cup(stop: str, keys: list[str] | None) -> dict | None:
    """The witness cup's own consume-once accessor (F-1952/J-1390) -- called only from `read()`
    above, never directly, so `read()` stays the one door. Always writes a 'ride' row exactly as
    `read()` did before this change (`kind: "ride", line: "witness", dose: "cup"`), whether or not
    the cup had anything to give -- an empty/expired/already-taken read is still a real, traceable
    read attempt, same cardinality as before (this line's tuple was, in practice, always truthy
    after lane2's first-ever tick, so the old path logged a ride row on essentially every call too).
    A SUCCESSFUL consume (topic present) additionally logs one `cup_consumed_would` row to the
    would-ride shadow log (`lane2_break_habituation.log_cup_consumed_would`), UNCONDITIONAL on
    LANE2_LIVE, so P1-1 can read as real consumptions/day rather than gate-passes/day before any
    flip (plan §7.6). Never raises (the caller's own try/except in `read()` already wraps this)."""
    global _CUP_WITNESS
    now = time.time()
    cup, _CUP_WITNESS = _CUP_WITNESS, None      # consume-once: cleared on the FIRST read either way
    taken = cup if (cup and now - float(cup.get("ts") or 0) <= CUP_TTL_S) else None
    value = ({k: taken.get(k) for k in keys} if keys else
             {k: v for k, v in taken.items() if k != "ts"}) if taken else {}
    _append({"ts": round(now, 3), "kind": "ride", "stop": stop, "line": "witness",
             "dose": "cup", "value": value, "what_changed_next": None})
    if taken and taken.get("topic"):
        try:
            from core import lane2_break_habituation as _hab_cup
            _hab_cup.log_cup_consumed_would(taken.get("topic"), taken.get("horizon"), now=now)
        except Exception:
            pass
    return value or None


def _place_cup(topic: str, horizon: str | None, now: float) -> None:
    """Places {topic, horizon, ts} into the witness cup slot -- one entry, newest wins (F-1952/
    J-1390). Called from `publish_witness()` only when the per-topic habituation gate has already
    said `cup_would_ride` -- rate-capped here at CUP_MAX_PLACE_PER_WINDOW/CUP_RATE_WINDOW_S, mirroring
    the Tap-on-the-Shoulder's OWN overall push-rate cap (`core/lane2.py`
    HINT_MAX_PUSH_PER_WINDOW/HINT_RATE_WINDOW_S). This is a SEPARATE layer from the per-topic gate:
    that one suppresses repeats of the SAME topic; this caps total placements regardless of which
    topic, the way the Tap caps total pushes regardless of which topic is pushed. An unconsumed
    prior entry is simply overwritten (newest wins, per this job's own briefing) -- no separate
    'overwritten' bookkeeping; a rejected (rate-capped) placement gets its own log row so the rate
    cap's own real bite is visible without hand-parsing 'ride' rows for absence. Never raises."""
    global _CUP_WITNESS
    try:
        while _cup_place_log and now - _cup_place_log[0] > CUP_RATE_WINDOW_S:
            _cup_place_log.popleft()
        if len(_cup_place_log) >= CUP_MAX_PLACE_PER_WINDOW:
            _append({"ts": round(now, 3), "kind": "cup_rejected", "reason": "rate-limited",
                     "topic": topic, "horizon": horizon})
            return
        _cup_place_log.append(now)
        _CUP_WITNESS = {"topic": topic, "horizon": horizon, "verdict": "broke",
                        "cup_would_ride": True, "ts": now}
    except Exception:
        pass


def publish_si(doubted: bool, ledger_idx: int | None, train_id: str = "", cycle_id: str = "") -> None:
    """Called from core/self_interrogation.interrogate() once the decoupled panel has judged a fire.
    Publishes the COORDINATE only (D-0396, rule 1): doubted flag, 1-based ledger index of the point doubted,
    train id. The reflection text is deliberately not a parameter, so no caller can leak prose through here.
    Registry key `si` + a publish row (loop="si"); arms the one pending would-ride slot when doubted.
    Never raises."""
    global _si_pending
    if not (COUPLING_PUBLISH and SI_CUP_SHADOW):
        return
    try:
        now = time.time()
        idx = int(ledger_idx) if _isnum(ledger_idx) else None
        coords = {"doubted": bool(doubted), "ledger_idx": idx, "train_id": str(train_id or ""),
                  "cycle": str(cycle_id or "")[:8]}
        publish("si", "self_interrogation", coords)
        _si_pending = {"ts": now, "ledger_idx": idx, "train_id": str(train_id or "")} if doubted else None
    except Exception:
        pass


def si_would_ride(train_id: str, train_len: int | None = None) -> None:
    """SHADOW ONLY. Called where the NEXT step of a train builds its mid-thread seed. If an si doubt is pending,
    log whether the open-doubt cup WOULD have ridden here (eligible) or why not, then consume it (one cup per
    publish, one per train). Returns None always -- the coordinate never reaches a prompt (HOLD, D-0396).
    Row: {"kind": "si_would_ride", "stop", "eligible", "reason", "age_s", "ledger_idx", "train_id", "train_len"}.
    Eligibility rate = eligible rows / `si` publish rows with doubted=true. Never raises."""
    global _si_pending
    if not (COUPLING_PUBLISH and SI_CUP_SHADOW):
        return
    try:
        pend = _si_pending
        if not pend:
            return
        _si_pending = None                       # consume-once whether or not it was eligible
        now = time.time()
        age = now - float(pend["ts"])
        tid = str(train_id or "")
        if not tid or tid != pend["train_id"]:
            reason = "train-changed"
        elif age > SI_CUP_TTL_S:
            reason = "stale"
        elif tid in _si_trains_served:
            reason = "train-already-served"
        else:
            reason = "ok"
        eligible = reason == "ok"
        if eligible:
            _si_trains_served[tid] = now
            if len(_si_trains_served) > 200:     # bounded: drop the oldest half
                for k in sorted(_si_trains_served, key=_si_trains_served.get)[:100]:
                    _si_trains_served.pop(k, None)
        _append({"ts": round(now, 3), "kind": "si_would_ride", "stop": "mid-thread step", "line": "si",
                 "eligible": eligible, "reason": reason, "age_s": round(age, 2),
                 "ledger_idx": pend["ledger_idx"], "train_id": pend["train_id"], "train_len": train_len})
    except Exception:
        pass


# ── publishers ─────────────────────────────────────────────────────────────────────────────────
def publish_climate(engine) -> None:
    """Called from ClimateEngine.tick(). Registry every tick; log row rate-limited."""
    if not COUPLING_PUBLISH:
        return
    try:
        field = getattr(engine, "field", None)
        diss = getattr(engine, "dissonance", None)
        coords = dict(field.as_dict()) if field is not None else {}
        coords["dissonance"] = getattr(diss, "value", None)
        coords["explore_value"] = getattr(diss, "explore_value", None)
        try:
            coords["ignition_level"] = engine.ignition_level()
        except Exception:
            coords["ignition_level"] = None
        now = time.time()
        last = _climate_last_logged
        moved = True
        if last["coords"] is not None:
            moved = False
            for k, v in coords.items():
                a, b = last["coords"].get(k), v
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) >= CLIMATE_MIN_DELTA:
                    moved = True
                    break
        do_log = moved or (now - last["ts"]) >= CLIMATE_MAX_GAP_S
        publish("climate", "climate tick", coords, log=do_log)
        if do_log:
            last["ts"] = now
            last["coords"] = {k: _num(v) for k, v in coords.items()}
    except Exception:
        pass


def publish_stream(rec: dict) -> None:
    """Called from stream_drive.observe() with the shadow row it just wrote."""
    if not COUPLING_PUBLISH:
        return
    try:
        coords = {k: rec.get(k) for k in ("drive", "ignition", "grounded", "progress", "redundancy",
                                          "train_kind", "train_len", "source", "would_gap", "actual_gap")}
        publish("stream", "train step", coords)
    except Exception:
        pass


def publish_deliberation(state) -> None:
    """Called from the Orchestrator at the end of each cycle (next to _log_correlation)."""
    global _cycles_since_human
    if not COUPLING_PUBLISH:
        return
    try:
        input_type = getattr(state, "input_type", None)
        if input_type == "human":
            _cycles_since_human = 0
        else:
            _cycles_since_human += 1
        recall = getattr(state, "recall", None)
        scene = getattr(state, "episodic_scene", None)
        critic = getattr(state, "critic", None)
        verdict = None
        if critic is not None and hasattr(critic, "approved"):
            verdict = "approved" if bool(critic.approved) else "rejected"
        coords = {
            "recall_confidence": getattr(recall, "confidence", None) if recall else None,
            "tensions_carried": len(getattr(recall, "tensions", None) or []) if recall else 0,
            "coherence": getattr(scene, "coherence", None) if scene else None,
            "dissonance_count": len(getattr(scene, "dissonance", None) or []) if scene else 0,
            "think_license": bool(getattr(state, "think_license", False)),
            "critic_verdict": verdict,
            "cycles_since_human": _cycles_since_human,
            "input_type": input_type,
        }
        publish("deliberation", "deliberation recall", coords)
    except Exception:
        pass


def _trailing_break_rate_baseline(now: float, break_rate_24h) -> float | None:
    """F-1953/J-1391 -- rolling mean of break_rate_24h over the trailing 7-day window
    (core/climate_engine.py's _WITNESS_STRAIN_BASELINE_WINDOW_S), sampled once per call (this
    function's own caller, publish_witness(), runs once per core/lane2.py tick -- every TICK_S
    there, ~300s, so this window holds at most ~2000 samples, trivial memory). Appends the CURRENT
    sample BEFORE pruning/averaging, so a break-free or low-ratio tick still counts toward the
    baseline, not just break-heavy ticks -- the baseline answers "what has break_rate_24h been
    running at lately", independent of whether THIS tick happens to resolve a judged break.

    Process-local, unpersisted (same posture as this module's own _witness_window): a restart empties
    this and it refills over the next 7 days of ticks. Deliberate, disclosed limitation, not an
    oversight -- a thin/empty baseline makes climate_engine.witness_bucket_value_sized()'s own excess
    computation read SMALL (close to 0, since a short baseline tracks the current ratio closely),
    never dangerously large, so a fresh restart's fail mode is "the sized dose under-reports for a
    while", the safe direction, not the reverse.

    break_rate_24h=None (unresolved this tick) -> the sample is skipped (not appended as 0.0, which
    would corrupt the baseline with a false reading of an unusually LOW day) but the window is still
    pruned and whatever mean is available from prior samples is still returned. Returns None only
    when the window itself is empty (nothing sampled yet, e.g. fresh restart's first tick). Never
    raises (mirrors every other function in this module)."""
    try:
        from core import climate_engine as _ce
        window_s = _ce._WITNESS_STRAIN_BASELINE_WINDOW_S
        if break_rate_24h is not None:
            _break_rate_baseline_window.append((now, float(break_rate_24h)))
        while _break_rate_baseline_window and now - _break_rate_baseline_window[0][0] > window_s:
            _break_rate_baseline_window.popleft()
        if not _break_rate_baseline_window:
            return None
        return sum(v for _, v in _break_rate_baseline_window) / len(_break_rate_baseline_window)
    except Exception:
        return None


def publish_witness(rec: dict, store: dict | None) -> None:
    """Called from lane2's tick right after _log(rec). Rolling 24 h window kept here.

    Phase 1 (D-0241 shadow-first, J-1161, plan §7.4): also computes the per-topic/horizon cut the
    idle-thought-seed cup and the climate bucket both need, and — UNCONDITIONALLY, regardless of
    LANE2_LIVE — grows the lane2_break_habituation gate and writes a would-ride shadow log row on
    every JUDGED BREAK with a resolvable topic. `topic`/`horizon`/`cup_would_ride` land in the SAME
    published tuple, so the two gated read sites (idle-thought seed, climate's world_model_strain
    bucket) each only need their own coupling_rides.read() call — no separate habituation query of
    their own. This function does NOT itself gate anything on LANE2_LIVE: extending what gets
    published, and growing the shadow-only habituation state, are both meant to keep running whether
    or not the flag is set — the two ACTUAL consumer read sites carry the gate instead (see
    nodes/inner_monologue_node.py's idle-thought seed and core/climate_engine.py's _compute_field)."""
    if not COUPLING_PUBLISH:
        return
    try:
        now = time.time()
        _witness_window.append((now, str(rec.get("notice") or "")[:120], rec.get("hint") is not None))
        while _witness_window and now - _witness_window[0][0] > WITNESS_WINDOW_S:
            _witness_window.popleft()
        notices = [n for _, n, _ in _witness_window]
        distinct = round(len(set(notices)) / len(notices), 3) if notices else None
        hinted = sum(1 for _, _, h in _witness_window if h)
        held = broke = 0
        for p in (store or {}).get("prediction") or []:
            jt = p.get("judged_ts")
            if p.get("verdict") in ("held", "broke") and jt and now - float(jt) <= WITNESS_WINDOW_S:
                if p["verdict"] == "broke":
                    broke += 1
                else:
                    held += 1
        judged = held + broke
        break_rate_24h = round(broke / judged, 3) if judged else None
        # F-1953/J-1391: update+read the trailing 7-day baseline on EVERY tick (not only breaks),
        # so it tracks break_rate_24h's own real run rather than only break-moments' snapshots.
        trailing_baseline_24h = _trailing_break_rate_baseline(now, break_rate_24h)
        g = rec.get("grounding") or {}

        # §7.4 — topic via the same _TOPIC_CANON matcher core/lane2.py's _distinct_share_by_topic
        # already uses, run against judged_expect (the due prediction's own text, not this tick's
        # fresh notice); horizon is already on rec as judged_horizon. No new percept read, no new
        # judge call. Only computed on a JUDGED BREAK (prior_verdict == "broke") — a held/cannot_tell/
        # none tick has no break to gate or log.
        topic = horizon = None
        cup_would_ride = None
        try:
            if rec.get("prior_verdict") == "broke":
                from core import lane2 as _l2
                topic = _l2._topic_of(rec.get("judged_expect") or "")
                horizon = rec.get("judged_horizon")
                if topic:
                    from core import lane2_break_habituation as _hab
                    from core import climate_engine as _ce
                    bucket_value = _ce.witness_bucket_value(break_rate_24h)
                    bucket_value_sized = _ce.witness_bucket_value_sized(break_rate_24h, trailing_baseline_24h)
                    gate = _hab.observe_break(topic, horizon, bucket_value,
                                               bucket_would_contribute_sized=bucket_value_sized, now=now)
                    cup_would_ride = (gate or {}).get("would_ride")
                    if cup_would_ride:
                        # F-1952/J-1390: the cup slot is now the consumable dose="cup" reads --
                        # placement is rate-capped separately from this per-topic gate (_place_cup's
                        # own docstring). The per-tick `coords` below still carries topic/horizon/
                        # cup_would_ride regardless (unchanged, for the bucket + status() readers).
                        _place_cup(topic, horizon, now)
        except Exception:
            pass

        coords = {
            "break_rate_24h": break_rate_24h,
            # D-0497 / D-0301 (J-2463, 2026-10-28): the trailing 7-day baseline rides in the tuple so
            # climate_engine's live bucket read can call witness_bucket_value_sized() through the one
            # door read(). A deliberate, founder-ruled widening of the witness schema (plan law 5).
            "trailing_baseline_24h": trailing_baseline_24h,
            "n_judged_24h": judged,
            "grounded_share": g.get("grounded_share") if isinstance(g, dict) else None,
            "distinct_share_24h": distinct,
            "hint_consumed_24h": hinted,
            "verdict": rec.get("prior_verdict"),
            "topic": topic,
            "horizon": horizon,
            "cup_would_ride": cup_would_ride,
        }
        publish("witness", "witness tick", coords)
    except Exception:
        pass


_ledgers_thread = None


def publish_ledgers() -> None:
    """Read-only collector over the ledgers' own files; called per idle thought, rate-limited, and
    run on a daemon thread because subconscious_state.json alone is ~60 MB (~1 s to parse, measured
    2026-09-05, F-0854) — the event loop must never wait on it. Never raises."""
    global _ledgers_last_ts, _ledgers_thread
    if not COUPLING_PUBLISH:
        return
    try:
        now = time.time()
        if now - _ledgers_last_ts < LEDGERS_MIN_GAP_S:
            return
        if _ledgers_thread is not None and _ledgers_thread.is_alive():
            return
        _ledgers_last_ts = now
        import threading
        _ledgers_thread = threading.Thread(target=_collect_ledgers, name="coupling-ledgers", daemon=True)
        _ledgers_thread.start()
    except Exception:
        pass


def _collect_ledgers() -> None:
    """The actual collector body (runs on the daemon thread; also callable directly in tests)."""
    try:
        now = time.time()
        coords: dict = {}
        # commitments
        try:
            items = json.load(open(_DATA / "commitment_active.json", encoding="utf-8"))
            if isinstance(items, dict):
                items = items.get("items", [])
            coords["commitments_active"] = len(items)
            coords["commitments_load_bearing"] = sum(1 for i in items if i.get("load_bearing"))
        except Exception:
            coords["commitments_active"] = coords["commitments_load_bearing"] = None
        # escalations in the last hour (tail of the append-only ledger)
        try:
            esc = 0
            p = _DATA / "commitment_ledger.jsonl"
            if p.exists():
                with open(p, "rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    start = max(0, size - 200_000)
                    f.seek(start)
                    tail = f.read().decode("utf-8", errors="ignore").splitlines()
                    if start > 0:
                        tail = tail[1:]          # drop the partial first line only when we cut mid-file
                for line in tail:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if "ESCALATE" in str(r.get("event", "")) and now - float(r.get("ts", 0)) <= 3600:
                        esc += 1
            coords["escalations_1h"] = esc
        except Exception:
            coords["escalations_1h"] = None
        # tensions: top 3 by chronic_mass
        try:
            s = json.load(open(_DATA / "subconscious_state.json", encoding="utf-8"))
            ts_ = sorted((t for t in s.get("tensions", []) if t.get("chronic_mass")),
                         key=lambda t: float(t.get("chronic_mass", 0.0)), reverse=True)[:3]
            coords["tension_top3"] = {str(t.get("label"))[:60]: _num(t.get("chronic_mass"), 3) for t in ts_}
            coords["tensions_n"] = len(s.get("tensions", []))
        except Exception:
            coords["tension_top3"] = None
        # frontier
        try:
            from core import frontier as _fr
            coords["frontier_open"] = int(_fr.open_count())
        except Exception:
            coords["frontier_open"] = None
        # pursuits
        try:
            pur = json.load(open(_DATA / "pursuits_active.json", encoding="utf-8"))
            if isinstance(pur, dict):
                pur = pur.get("items", [])
            active = [p for p in pur if str(p.get("status", "active")) == "active"]
            coords["pursuits_active"] = len(active)
            coords["pursuits_heat_max"] = max((float(p.get("heat", 0.0)) for p in active), default=0.0)
        except Exception:
            coords["pursuits_active"] = coords["pursuits_heat_max"] = None
        publish("ledgers", "idle seed", coords)
        compose()      # D-0371: the hub rides the ledgers collector's cadence (Phase 2, shadow; no-op if COUPLING_PHASE2 is False)
    except Exception:
        pass
