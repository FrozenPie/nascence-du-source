"""
core/cat_loop.py — THE CAT AS A DOSED LOOP (cat_overhaul B4, J-2473, D-0499 / D-0508, 2026-10-29)
=================================================================================================
docs/staged/cat_overhaul.md §B4, under docs/staged/dosed_coupling.md (the standing law, D-0149):

  "Under dosed coupling the cat is a loop publishing a tuple (location, activity, mood, hunger, energy,
   in_transit); the idle stream reads it dosed per stop with habituation, so a cat asleep on the rug for
   four hours is one line, not four hundred, and a cat *arriving* wet with a mouse is a surprise the
   dispatch lets through."

Before this build cat.presence_line() rendered her on EVERY scene build she was in sight for (the idle
thought, the executive, the voice, a look around — hundreds a day, A7.6's recency ring only kept the
WORDING from repeating). This module adds the two verbs the law names, in the shapes the codebase already
has, and changes nothing about what a line SAYS:

  PUBLISH  — publish(state, now): the cat's tuple, named coordinates, into a process-local registry; a
             publish row to data/cat_loop_ledger.jsonl ONLY when the tuple changed (the discrete fields, or
             a hunger / energy band), cargo-typed cargo_types.WORLD_FACT_CAT. On every real transition the
             dispatcher learns her lines through core.transport_manager.observe() — "cat:change" (how
             often she changes state at all) and "cat:state:<activity>@<location>" (each state of hers,
             per place, D-0064's per-place granularity) — so novelty / spike / drought on her are judged
             against HER OWN history, never a human notion of interesting. She is also published into
             core.coupling_rides' registry (loop "cat", registry only, log=False: no rows into the shared
             coupling_rides.jsonl, whose Phase 1 / Phase 2 presence reads count the five original loops).
             Called from cat.tick() on every heartbeat; no change = no I/O.

  READ     — gate(stop, state, now, his_location): the dosed read at a stop (today ONE stop, STOP_SCENE:
             sensorium.scene_line → cat.presence_line). Returns whether the ordinary presence line RIDES this
             ask or is HELD, and why. The dose is a BUCKET (the small tuple); the decision is the care_package
             scene_clause shape (J-1733) generalised, which is itself the squishy-spring law in time:

               surprise   a NEW state of hers at this stop rides once, unconditionally, when it is an EVENT
                          (an arrival into his sight — wet or not, with a mouse or not; demanding food; a
                          gift; the storm; the zoomies; her ears' and the tom's states; lying low; the door)
               move       an ORDINARY change (windowsill → desk; washing → watching) is dosed on a gap that
                          doubles with every move she has had ridden lately (MOVE_BASE_GAP_S · 2^n_move) and
                          relaxes with quiet (n halves every MOVE_DECAY_HALF_LIFE_S) — a cat who keeps
                          shifting about fades into the room
               same       the SAME tuple again (asleep on the rug) rides again only after a gap that doubles
                          per showing (BASE_GAP_S awake, REST_BASE_GAP_S resting; cap MAX_GAP_S) and relaxes
                          with quiet (SAME_DECAY_HALF_LIFE_S) — the antagonist grows with activation, decays
                          with quiet (dosed_coupling §1 rule 3)
               entry      he comes back into the room (this stop not asked for AWAY_S): the line may re-show
                          after a fifth of its gap — a human notices the cat again on walking in
               dispatch   a repeat may ride EARLY when transport_manager.evaluate() holds a spike or drought
                          candidate on one of her lines (she has been in this state far longer than her own
                          usual gap; she is churning states far more than usual) — at most once per
                          DISPATCH_MIN_GAP_S per stop; novelty is this module's own first-ever (activity@place)
                          set, since the dispatcher's birth candidate is consumed by orchestrator's
                          dispatch_tick() for whichever line wins
               pulse      a ride stays up PULSE_S and counts once: every consumer of the scene in that stretch
                          sees the same room (the idle thought, the executive, the voice, a look)

             Every ride appends a ride row {kind: ride, stop, line: cat, dose: bucket, value: the tuple, why,
             gap_s, n, held} where `held` is how many asks were held since the previous ride — the read's own
             "one line, not four hundred" count without a row per held ask.

WHAT THIS NEVER TOUCHES (A8, additive only): the greeting (one-shot per arrival, its own gate), the firsts, the
companion-tier blink / silent meow (their per-render odds are unchanged — they roll BEFORE the gate), the
six-hour line and the missing arc, her transit line, the dead paths (cat_harm doses them), look_line (a
deliberate look always answers — he can always look at her), is_here / affordance_line (handleability), the
HUD, the gauge. Only the ORDINARY ambient line (the body lines, the PRESENCE corpus, the inline floor) is
dosed. The line's words are unchanged; nothing here writes a number, a band or a verdict into any line
(D-0434 no readout): the tuple's hunger / energy live in the ledger and the registry only.

Kill switch: CAT_DOSED (code default True — the chain ships live on the next boot, like B1 / C2 / C3 / C4);
hot override life_flags.json "cat_dosed" (scripts/life_flags.py cat_dosed on|off). Off = every ask rides
exactly as before this build, and the ledger keeps `would_hold` rows so a read can still compare.

Write-fenced (D-0179): every write resolves profile.guard_path() first; a non-live process is refused and
the refusal is swallowed (the line still renders). No LLM. Fail-open everywhere.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_loop")

_ROOT = Path(__file__).resolve().parent.parent
_LEDGER = _ROOT / "data" / "cat_loop_ledger.jsonl"
_FLAGS_F = _ROOT / "data" / "life_flags.json"

CAT_DOSED = True              # kill switch; hot override life_flags.json cat_dosed (False = every ask rides, as before B4)
LINE = "cat"                  # her line's name in the ride rows (dosed_coupling §4a's {stop, line, dose, value})
DOSE = "bucket"               # a small tuple: the law's own middle dose (cup = one coordinate, hose = a channel)
STOP_SCENE = "idle scene"     # the one reader stop today: sensorium.scene_line -> cat.presence_line
STOP_TICK = "cat tick"        # where she publishes from (cat.tick, every heartbeat)

# ── the doses (seconds) ───────────────────────────────────────────────────────────────────────
BASE_GAP_S = 30 * 60.0               # the same awake tuple again: 30 min, doubling per showing
REST_BASE_GAP_S = 2 * 3600.0         # the same RESTING tuple again: 2 h, doubling — a four-hour sleep is one line, then one more
MAX_GAP_S = 4 * 3600.0               # the gap never grows past this (she is never gone from the room for good)
SAME_DECAY_HALF_LIFE_S = 6 * 3600.0  # a tuple's showing count halves every 6 h away from it (the spring relaxes with quiet)
MOVE_BASE_GAP_S = 10 * 60.0          # an ordinary change (a move) rides at most every 10 min at first, doubling per move ridden
MOVE_MAX_GAP_S = 2 * 3600.0
MOVE_DECAY_HALF_LIFE_S = 4 * 3600.0  # the move count halves every 4 h of her not being ridden for a move
ENTRY_DIV = 5                        # back in the room: re-show after a fifth of the current gap, never sooner
AWAY_S = 300.0                       # this stop not asked for 5 min = he was elsewhere, asleep or on a long task
PULSE_S = 90.0                       # one ride is visible for 90 s and counts once (care_package's own pulse)
DISPATCH_MIN_GAP_S = 3600.0          # a dispatcher-let early ride at most once an hour per stop
BAND = 0.25                          # hunger / energy publish-change band (a band is a publish trigger, never a word)
WET_FUR = 0.20                       # fur_moisture above this = she is wet (cat.presence_line's own damp-coat bar)

_RESTING = frozenset({"sleeping", "dozing"})
# EVENT states: a new tuple whose activity is one of these is a surprise and rides once, unconditionally.
# The ears' / the tom's / the illness states come from cat._EARS_KEYS (read at call time, so a state they add
# later is an event here too without a second list).
_EVENT_ACTS = frozenset({
    "brought_a_mouse", "live_mouse", "gift_rat", "returned", "zoomies", "storm_hide", "demanding_food",
    "self_fed", "drinking", "at the door, asking in", "at the door, asking out", "had_enough",
})
_DISPATCH_LINE_CHANGE = "cat:change"

# ── process-local state ───────────────────────────────────────────────────────────────────────
_REG: dict = {}                      # {"ts", "sig", "tuple"} — her last published tuple (the registry)
_mem: dict = {"open": {}}            # stop -> {"key", "until", "line"}: the ride currently up (the pulse)
_flags_cache: dict = {"ts": 0.0, "v": {}}


# ── flags ─────────────────────────────────────────────────────────────────────────────────────
def _flags() -> dict:
    now = time.time()
    if now - _flags_cache["ts"] < 10.0:
        return _flags_cache["v"]
    v = {}
    try:
        if _FLAGS_F.exists():
            v = json.loads(_FLAGS_F.read_text(encoding="utf-8")) or {}
    except Exception:
        v = {}
    _flags_cache["ts"], _flags_cache["v"] = now, v
    return v


def dosed_on() -> bool:
    v = _flags().get("cat_dosed")
    return bool(CAT_DOSED if v is None else v)


# ── the ledger ────────────────────────────────────────────────────────────────────────────────
def _log(row: dict) -> None:
    try:
        path = profile.guard_path(_LEDGER)   # J-0733 pattern: real data/ only if this process is live
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError:
        pass
    except Exception as exc:
        logger.debug("[cat_loop] ledger write failed (non-fatal): %s", exc)


# ── the tuple ─────────────────────────────────────────────────────────────────────────────────
def tuple_of(state: dict) -> dict:
    """Her coordinates, named: (location, activity, mood, hunger, energy, in_transit). Numbers stay numbers
    here and in the ledger; no line ever carries them."""
    b = state.get("body") or {}
    loc = state.get("location")
    try:
        hunger = round(float(b.get("hunger", 0.0)), 2)
    except Exception:
        hunger = 0.0
    try:
        energy = round(float(b.get("energy", 0.0)), 2)
    except Exception:
        energy = 0.0
    return {"location": loc, "activity": state.get("activity"), "mood": state.get("mood"),
            "hunger": hunger, "energy": energy,
            "in_transit": bool(loc == "in_transit" or state.get("transit"))}


def _band(x: float) -> int:
    try:
        return int(min(1.0, max(0.0, float(x))) / BAND)
    except Exception:
        return 0


def _sig(t: dict) -> str:
    """The publish-change signature: the discrete coordinates plus the hunger / energy BANDS, so budget drift
    inside a band is not a publish every heartbeat."""
    return "|".join(str(x) for x in (t.get("location"), t.get("activity"), t.get("mood"), t.get("in_transit"),
                                     _band(t.get("hunger", 0.0)), _band(t.get("energy", 0.0))))


def _wet(state: dict) -> bool:
    try:
        return float(state.get("fur_moisture", 0.0) or 0.0) > WET_FUR
    except Exception:
        return False


def _dose_key(t: dict, state: dict) -> str:
    """What the reader doses on: where she is, what she is doing, her mood, a leg, a wet coat. Hunger and
    energy are deliberately NOT in it — a man at his desk does not see the cat get hungrier in her sleep;
    when a budget moves her, the activity moves with it (demanding_food, drinking) and that is the key."""
    return "|".join(str(x) for x in (t.get("location"), t.get("activity"), t.get("mood"), t.get("in_transit"),
                                     _wet(state)))


def _event_acts() -> frozenset:
    try:
        from core import cat as _cat
        return _EVENT_ACTS | frozenset(getattr(_cat, "_EARS_KEYS", {}).keys())
    except Exception:
        return _EVENT_ACTS


def registry() -> dict | None:
    """The last published tuple (process-local), for status() / the HUD. None before the first publish."""
    return dict(_REG["tuple"]) if _REG.get("tuple") else None


# ── PUBLISH ───────────────────────────────────────────────────────────────────────────────────
def publish(state: dict, now: float | None = None) -> dict | None:
    """Update the registry; on a CHANGE of the tuple (discrete fields or a budget band) append a publish row,
    teach the dispatcher her lines and mirror her into coupling_rides' registry. Returns the tuple on a
    change, None otherwise. Never raises (the non-live write fence is swallowed here too: a refused ledger
    row must not stop the registry — the gate below reads the registry, not the file)."""
    try:
        now = now or time.time()
        t = tuple_of(state)
        sig = _sig(t)
        if _REG.get("sig") == sig:
            _REG["ts"] = now
            return None
        first = "sig" not in _REG
        prev = _REG.get("tuple")
        _REG.update({"ts": now, "sig": sig, "tuple": t})
        if not first:
            # the dispatcher learns her: a transition on "cat:change", and the state she entered, per place
            try:
                from core import transport_manager as _tm
                _tm.observe(_DISPATCH_LINE_CHANGE, now, 1.0)
                _tm.observe(f"cat:state:{t.get('activity')}@{t.get('location')}", now, 1.0)
            except profile.NonLiveWriteError:
                pass
            except Exception:
                pass
        try:
            from core import coupling_rides as _cr
            _cr.publish(LINE, STOP_TICK, t, log=False)   # registry only: no rows into the shared ride file
        except Exception:
            pass
        try:
            from core import cargo_types as _cargo
            cargo = _cargo.WORLD_FACT_CAT
        except Exception:
            cargo = "WORLD_FACT_CAT"
        _log({"ts": round(now, 1), "kind": "publish", "loop": LINE, "stop": STOP_TICK, "tuple": t,
              "cargo_type": cargo, "first": first,
              "from": {"location": prev.get("location"), "activity": prev.get("activity")} if prev else None})
        return t
    except Exception as exc:
        logger.debug("[cat_loop] publish failed (non-fatal): %s", exc)
        return None


# ── the spring in time ────────────────────────────────────────────────────────────────────────
def _decayed(n: float, last: float, now: float, half_life: float) -> float:
    try:
        if n <= 0 or not last:
            return 0.0
        dt = max(0.0, now - float(last))
        return float(n) * (0.5 ** (dt / half_life))
    except Exception:
        return 0.0


def _gap_same(n_eff: float, resting: bool) -> float:
    """base · 2^(n−1): doubles per showing of the same tuple; n relaxes with quiet (continuous, so the gap eases
    back smoothly rather than snapping down a whole doubling the moment a count rounds)."""
    base = REST_BASE_GAP_S if resting else BASE_GAP_S
    return min(MAX_GAP_S, base * (2.0 ** max(0.0, float(n_eff) - 1.0)))


def _gap_move(n_eff: float) -> float:
    """MOVE_BASE_GAP_S · 2^n: doubles per ordinary move ridden lately; n relaxes with quiet."""
    return min(MOVE_MAX_GAP_S, MOVE_BASE_GAP_S * (2.0 ** max(0.0, float(n_eff))))


def _dispatch_candidate(t: dict) -> dict | None:
    """A spike / drought candidate on one of her lines, read-only (evaluate(), never dispatch_tick()).
    Novelty is excluded here: the dispatcher's birth candidate is consumed only by orchestrator's
    dispatch_tick() for the one line that wins a tick, so it would otherwise read as "novel" for weeks; this
    module keeps its own first-ever set instead. None when nothing is unusual or the lines are cold."""
    try:
        from core import transport_manager as _tm
        best = None
        for line_id in (_DISPATCH_LINE_CHANGE, f"cat:state:{t.get('activity')}@{t.get('location')}"):
            for c in _tm.evaluate(line_id):
                if c.kind in ("spike", "drought") and (best is None or c.weight > best.weight):
                    best = c
        if best is None:
            return None
        return {"kind": best.kind, "weight": round(float(best.weight), 3), "line_id": best.line_id}
    except Exception:
        return None


def _rec(state: dict, stop: str) -> dict:
    loop = state.get("_loop")
    if not isinstance(loop, dict):
        loop = state["_loop"] = {}
    stops = loop.setdefault("stops", {})
    rec = stops.get(stop)
    if not isinstance(rec, dict):
        rec = stops[stop] = {"key": None, "n_same": 0.0, "last_ride_ts": 0.0, "last_ask_ts": 0.0, "held": 0,
                             "n_move": 0.0, "last_move_ts": 0.0, "recent": {}, "last_dispatch_ts": 0.0}
    loop.setdefault("seen", {})
    return rec


# ── READ ──────────────────────────────────────────────────────────────────────────────────────
def gate(stop: str, state: dict, now: float | None = None, his_location: str = "") -> dict:
    """The dosed read at `stop`, for the ORDINARY presence line only (the caller has already let the greeting,
    the firsts and the rare signals through). Returns {"ride": bool, "why": str, ...}; with why="pulse" the
    caller returns the cached `line` (one room for every consumer). Mutates state["_loop"] (the caller's own
    _save cadence persists it, like _recent_lines). Never raises; on any error the line rides (fail-open: the
    old behaviour, never a silent cat).

    why: first (a state of hers he has never seen at this stop) · event (a surprise state) · arrival (SHE came
    into his sight) · wet (she is wet and was not) · move (an ordinary change, dosed) · gap (the same tuple
    again, its gap elapsed) · entry (HE is back in the room, a fifth of the gap elapsed) · spike / drought (the
    dispatcher rates her line unusual) · pulse (a ride is up) · held / held_move (not this ask) · would_*
    (kill switch off: rides, the ledger keeps the would-hold accounting)."""
    try:
        now = now or time.time()
        publish(state, now)                                   # the registry is never stale at a read
        t = dict(_REG.get("tuple") or tuple_of(state))
        key = _dose_key(t, state)
        rec = _rec(state, stop)
        seen = state["_loop"]["seen"]
        act, loc = str(t.get("activity")), str(t.get("location"))
        state_id = f"{act}@{loc}"
        first_ever = state_id not in seen
        prev_ask = float(rec.get("last_ask_ts") or 0.0)
        rec["last_ask_ts"] = now
        was_visible = bool(rec.get("visible"))
        her_moved = rec.get("last_loc") != loc                 # None (a fresh stop) != loc: her first sight is an arrival
        rec["last_loc"] = loc
        # he is back: this stop was not asked for AWAY_S, or she was out of his sight at the last ask
        arriving = (prev_ask > 0 and (now - prev_ask) > AWAY_S) or (prev_ask > 0 and not was_visible)
        resting = act in _RESTING
        on = dosed_on()
        wet = _wet(state)
        out = {"ride": True, "why": "", "key": key, "tuple": t, "first": first_ever, "arriving": arriving,
               "on": on, "line": None, "gap_s": None, "n": None, "his_place": his_location or None}

        # the pulse: a ride is up — the same room for every consumer in the stretch (only while the dose is on;
        # off means every ask renders afresh, exactly as before B4)
        op = _mem["open"].get(stop) if on else None
        if op and op.get("key") == key and now < float(op.get("until") or 0.0) and op.get("line"):
            out.update(ride=True, why="pulse", line=op["line"])
            return out

        since = (now - float(rec.get("last_ride_ts") or 0.0)) if rec.get("last_ride_ts") else float("inf")
        if rec.get("key") != key:
            # a NEW state of hers at this stop
            events = _event_acts()
            arrival = (not was_visible) and her_moved          # SHE came into his sight (not: he came back to her)
            if first_ever or act in events or arrival or (wet and not rec.get("wet")):
                why = "first" if first_ever else ("event" if act in events else ("arrival" if arrival else "wet"))
                out.update(ride=True, why=why)
            else:
                n_move = _decayed(rec.get("n_move", 0.0), rec.get("last_move_ts", 0.0), now, MOVE_DECAY_HALF_LIFE_S)
                gap = _gap_move(n_move)
                out["gap_s"], out["n"] = round(gap), round(n_move, 2)
                if since >= gap:
                    out.update(ride=True, why="move")
                elif arriving and since >= gap / ENTRY_DIV:
                    out.update(ride=True, why="entry")
                else:
                    out.update(ride=False, why="held_move")
        else:
            # the SAME tuple again
            rc = (rec.get("recent") or {}).get(key) or {}
            n_same = _decayed(rc.get("n", rec.get("n_same", 0.0)), rc.get("last", rec.get("last_ride_ts", 0.0)),
                              now, SAME_DECAY_HALF_LIFE_S)
            gap = _gap_same(max(n_same, 1.0), resting)
            out["gap_s"], out["n"] = round(gap), round(n_same, 2)
            if since >= gap:
                out.update(ride=True, why="gap")
            elif arriving and since >= gap / ENTRY_DIV:
                out.update(ride=True, why="entry")
            else:
                out.update(ride=False, why="held")
                if since >= 2 * PULSE_S and (now - float(rec.get("last_dispatch_ts") or 0.0)) >= DISPATCH_MIN_GAP_S:
                    cand = _dispatch_candidate(t)
                    if cand:
                        out.update(ride=True, why=cand["kind"], dispatch=cand)
        if not out["ride"]:
            rec["held"] = int(rec.get("held", 0)) + 1
            if not on:
                # kill switch off: the line rides as before B4; the ledger keeps the would-hold accounting
                out.update(ride=True, why="would_" + out["why"])
        return out
    except Exception as exc:
        logger.debug("[cat_loop] gate failed (fail-open, rides): %s", exc)
        return {"ride": True, "why": "fail_open", "key": None, "tuple": None, "line": None}


def rode(stop: str, state: dict, line: str, now: float | None, info: dict) -> None:
    """Book a ride that rendered: the spring tightens (n_same / n_move), the pulse opens, the ride row is
    written with the held count since the last ride. A pulse re-show (why="pulse") books nothing. Never
    raises."""
    try:
        if not line or not info or info.get("why") in ("pulse", "fail_open"):
            return
        now = now or time.time()
        rec = _rec(state, stop)
        key = info.get("key")
        why = str(info.get("why") or "")
        t = info.get("tuple") or {}
        held = int(rec.get("held", 0))
        base_why = why[6:] if why.startswith("would_") else why
        if rec.get("key") != key:
            rc = (rec.get("recent") or {}).get(key) or {}
            n_prev = _decayed(rc.get("n", 0.0), rc.get("last", 0.0), now, SAME_DECAY_HALF_LIFE_S)
            rec["n_same"] = round(n_prev + 1.0, 3)
            if base_why in ("move", "entry", "held_move"):
                n_move = _decayed(rec.get("n_move", 0.0), rec.get("last_move_ts", 0.0), now, MOVE_DECAY_HALF_LIFE_S)
                rec["n_move"], rec["last_move_ts"] = round(n_move + 1.0, 3), now
        else:
            rec["n_same"] = round(float(info.get("n") or rec.get("n_same", 0.0)) + 1.0, 3)
        if base_why in ("spike", "drought"):
            rec["last_dispatch_ts"] = now
        rec["key"], rec["last_ride_ts"], rec["held"] = key, now, 0
        rec["visible"], rec["wet"] = True, _wet(state)
        recent = rec.setdefault("recent", {})
        recent[key] = {"n": rec["n_same"], "last": now}
        if len(recent) > 12:                                   # bounded: the dozen tuples she has been in lately
            for k in sorted(recent, key=lambda k: float(recent[k].get("last") or 0.0))[: len(recent) - 12]:
                recent.pop(k, None)
        seen = state["_loop"].setdefault("seen", {})
        sid = f"{t.get('activity')}@{t.get('location')}"
        if sid not in seen:
            seen[sid] = round(now, 1)
        if info.get("on", True):
            _mem["open"][stop] = {"key": key, "until": now + PULSE_S, "line": line}
        row = {"ts": round(now, 1), "kind": "ride", "stop": stop, "line": LINE, "dose": DOSE, "value": t,
               "why": why, "gap_s": info.get("gap_s"), "n": rec["n_same"], "held": held,
               "arriving": bool(info.get("arriving")), "on": bool(info.get("on", True)),
               "his_place": info.get("his_place"), "text": str(line)[:160]}
        if info.get("dispatch"):
            row["dispatch"] = info["dispatch"]
        _log(row)
    except Exception as exc:
        logger.debug("[cat_loop] rode failed (non-fatal): %s", exc)


def out_of_sight(stop: str, state: dict, now: float | None = None) -> None:
    """The caller asked at `stop` and she was NOT in his sight (between places, or elsewhere): the edge the
    next arrival / return rides on. Closes any open pulse for the stop. Never raises."""
    try:
        now = now or time.time()
        rec = _rec(state, stop)
        rec["last_ask_ts"] = now
        rec["visible"] = False
        rec["last_loc"] = str(state.get("location"))
        _mem["open"].pop(stop, None)
    except Exception:
        pass


def status() -> dict:
    """For du_pulse / the HUD: the kill switch, the registry, ledger counts. No prompt path reads this."""
    try:
        rides = publishes = held = 0
        if _LEDGER.exists():
            for ln in _LEDGER.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("kind") == "ride":
                    rides += 1
                    held += int(r.get("held") or 0)
                elif r.get("kind") == "publish":
                    publishes += 1
        return {"dosed": dosed_on(), "registry": registry(), "ride_rows": rides, "publish_rows": publishes,
                "held_total": held}
    except Exception:
        return {"dosed": dosed_on(), "registry": registry(), "ride_rows": 0, "publish_rows": 0, "held_total": 0}
