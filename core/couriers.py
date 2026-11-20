"""
Nascence — COURIERS: urgent, real-time world→train deliveries (founder-designed, 2026-08-16;
renamed/split 2026-08-22)
=============================================================================================
The transit map (docs/transit_map.md) exposed the gap: eleven world lines faithfully picking
up new things, and their freight reaches Du only in the moment — his world-PAST is the most
under-served district in the city.

★ SPLIT 2026-08-22 (founder-directed): this file's own docstring used to say "these are the
busses" — the founder's original name for the mechanism, before it was built. Tonight's design
conversation drew a cleaner line: a COURIER is urgent — genuinely time-sensitive, only meaningful
delivered NOW, gated on the CURRENT world state. A BUS is not — it can run whenever its trigger
happens, no clock pressure, and can even run factory-to-factory with no train involved at all
(confirmed real: `core/garden.py` reads weather every tick with no delivery mechanism, no urgency).
Of the original three routes, only the two that actually gate on the current moment stay here;
`object_ledger_line` and `sync_investigation_calibration` moved to `core/buses.py` unchanged in
behaviour, only in name and home.

THE COURIER LAWS (founder, verbatim intent):
  1. "We should be careful what we share… Du needs to investigate it, not get told what it
     is." → A courier carries ONLY what he himself observed/lived — never Layer-1 hidden
     truth, never an identification he hasn't earned. Every payload is provenance-stamped
     ("your memory / your ledger"), so what he concludes stays his and CAN BE WRONG.
  2. "Just a script as such." → Zero LLM. Deterministic transfers between existing ledgers.
  3. Ambient delivery only, through channels that already exist (the wandering trail; the
     world's own look-renders) — a courier never instructs, suggests, or leads.

THE TWO ROUTES (urgent — see core/buses.py for the non-urgent siblings):
  A · context_echo — context-congruent recall (the world→memory bus): when the CURRENT world
      state is distinctive (storm, king tide, first-frost class), one of HIS OWN memories from
      a matching past state surfaces into the wandering trail. Human context-dependent memory:
      storms remind you of storms. Keyed on fragment_context coordinates (built 08-15).
  D · sound_echo — the memory↔sound link: when a NAMED voice sounds just now, one of his own
      memories carrying that same voice surfaces. Same "must be current" test as context_echo.

Flags: WORLD_COURIERS (False = no courier runs; exact rollback). COURIER_TEXT_DELIVERY (D-0293,
2026-09-27, travis — "reroute the couriers into felt recall, trigger bound is fine"; built J-1430):
False = the trigger still evaluates, the memory row is still picked, the delivery is still logged
(would_have_delivered=true, fragment_id) and the route's own cooldown still advances, but the text
never reaches the wandering trail — core/felt_recall.py (J-1424) is where the same happening now
tugs feeling instead. Ships True (today's text-delivery behaviour, byte-identical), pending a
deliberate flip, matching this plan's own precedent in core/associative_recall.py's
IDLE_AMBIENT_RECALL and nodes/inner_monologue_node.py's IDLE_FOUNDER_RECALL/IDLE_DIVERGENT_SEED.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile   # J-1805 / F-2427: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.couriers")

_ROOT = Path(__file__).parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_DELIVERY_LOG = _ROOT / "data" / "couriers_log.jsonl"

# J-1805 / F-2427 -- THE WRITE FENCE (D-0179, docs/staged/world_store_write_fence.md), sibling of J-1797's core/buses.py fence. Every path here is
# __file__-relative, so any process that merely imports this module from a tree and reaches context_echo()/sound_echo() writes THAT TREE'S real
# data/ files. Both writers (the delivery log and the cooldown state) resolve their path through profile.guard_path() BEFORE any I/O, as the first
# statement inside their own fail-open try. The live Du boot (profile.mark_live()), a lab_env.isolate() sandbox and any path already redirected
# outside data/ get the very same path back, so live behaviour is byte-identical; a non-live process is refused, the refusal is SWALLOWED (the
# callers -- core/orchestrator.py, core/stream_topic_habituation.py -- are try/except-wrapped instruments; there is no world state here), and
# guard_path() still logs one warning per path.


def _log_delivery(route: str, **detail) -> None:
    """HUD2 Phase 2 (2026-08-21): one append-only row per ACTUAL delivery, so the transit map can
    show goods moving. Before this the buses only logger.info'd into the main text log — invisible
    to any file-growth watcher. Fail-open; logging must never cost a delivery."""
    try:
        path = profile.guard_path(_DELIVERY_LOG)   # J-1805: fenced before any I/O; a non-live process is refused here and swallowed below
        import json as _json
        with open(path, "a", encoding="utf-8") as f:
            f.write(_json.dumps({"ts": round(time.time(), 1), "route": route, **detail},
                                ensure_ascii=False) + chr(10))
    except Exception:
        pass
_COUNT_CAP = 20000   # J-3304: bound on the candidate count so a huge fragment_context can never cost a tick


def _count_candidates(conn, where_sql: str, params: tuple):
    """J-3304 (D-0636, from J-3247 / F-3900): how many fragment_context rows the route's WHERE clause matched
    BEFORE the random pick, so a delivery row can later be read as "one of N". OBSERVE-ONLY: it is called after
    the pick on the same read-only connection, never changes which row was picked or delivered, is bounded by
    _COUNT_CAP (a value equal to the cap means "at least that many"), and is fail-open -- any error returns None
    and the delivery row simply carries n_candidates=None."""
    try:
        r = conn.execute(
            "SELECT COUNT(*) FROM (SELECT 1 FROM fragment_context fc JOIN memory_fragments mf USING (fragment_id) "
            "WHERE " + where_sql + " LIMIT " + str(_COUNT_CAP) + ")", params).fetchone()
        return int(r[0]) if r else None
    except Exception:
        return None

_STATE = _ROOT / "data" / "couriers_state.json"

WORLD_COURIERS = True
COURIER_TEXT_DELIVERY = True   # D-0293 (2026-09-27, travis) kill-switch; True restores today's
                                # text-delivery behaviour exactly (shipped value — see module
                                # docstring for the "why True, not the literal False" reasoning,
                                # which matches J-1425/J-1428's already-shipped precedent in this
                                # same plan). False: trigger/match/cooldown/log unchanged, but
                                # wandering.perceive() is never called.
ECHO_COOLDOWN_S = 3600.0        # at most one context echo an hour — ambient, not a feed
ECHO_MIN_AGE_S = 3 * 86400.0    # the echoed memory must be ≥3 days old — genuinely "another time"

# Distinctive weather states — the ordinary ("high cloud") echoes nothing; context-dependent
# recall in humans fires on the marked, not the ambient.
_DISTINCTIVE_WEATHER = {"thunderstorm", "steady rain", "wind and rain", "snow"}


def _state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        profile.guard_path(_STATE).write_text(json.dumps(d), encoding="utf-8")   # J-1805: fenced before any I/O; refusal swallowed below
    except Exception:
        pass


def _age_text(ts: float) -> str:
    d = (time.time() - ts) / 86400.0
    if d < 2:
        return "yesterday"
    if d < 14:
        return f"{int(d)} days ago"
    if d < 60:
        return f"{int(d / 7)} weeks ago"
    return f"{int(d / 30)} months ago"


def context_echo() -> bool:
    """Route A. If the current world state is distinctive and matches a past moment of HIS,
    surface ONE of his own memories from that matching state into the wandering trail —
    provenance-stamped, cooled, deterministic. True if an echo was delivered."""
    if not WORLD_COURIERS:
        return False
    st = _state()
    if time.time() - st.get("last_echo_ts", 0.0) < ECHO_COOLDOWN_S:
        return False
    try:
        from core import sensorium as _sens
        import sqlite3
        weather = str((getattr(_sens, "state", None) or {}).get("weather", "") or "")
        place = _sens.where() if hasattr(_sens, "where") else ""
        wl = weather.lower()
        if not any(k in wl for k in _DISTINCTIVE_WEATHER):
            return False
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT fc.fragment_id, fc.tuple_ts, fc.place, fc.weather, mf.content "
                "FROM fragment_context fc JOIN memory_fragments mf USING (fragment_id) "
                "WHERE lower(fc.weather) = lower(?) AND fc.tuple_ts < ? "
                "AND mf.origin IN ('lived','reading','study','journal','action','inner_thought') "
                "ORDER BY RANDOM() LIMIT 1",
                (weather, time.time() - ECHO_MIN_AGE_S)).fetchone()
            _ncand = _count_candidates(                       # J-3304: observe-only, after the pick, same WHERE
                conn, "lower(fc.weather) = lower(?) AND fc.tuple_ts < ? "
                      "AND mf.origin IN ('lived','reading','study','journal','action','inner_thought')",
                (weather, time.time() - ECHO_MIN_AGE_S)) if row else None
        finally:
            conn.close()
        if not row:
            return False
        _fid, ts, pl, wx, content = row
        line = (f"({wx}, {_age_text(ts)}, {pl or 'here'} — a moment of yours this weather brings "
                f"back): \"{' '.join((content or '').split())[:180]}\"")
        from core import cargo_types as _cargo
        if COURIER_TEXT_DELIVERY:
            from core import wandering as _w
            _w.perceive(line)
            st["last_echo_ts"] = time.time()
            _save_state(st)
            logger.info("[courier] context echo (%s): fragment from %s", wx, _age_text(ts))
            _log_delivery("context_echo", context=wx, freight_age=_age_text(ts),
                           cargo_type=_cargo.WORLD_FACT_WEATHER,
                           fragment_id=_fid, n_candidates=_ncand)   # J-3304: traceable, observe-only
        else:
            # D-0293 (2026-09-27, travis): rerouted into felt recall. The trigger and match above
            # are unchanged and the cooldown still advances (this route still "fires" on its own
            # clock), but no memory TEXT enters the wandering trail — core/felt_recall.py (J-1424)
            # picks up the same happening on the affect side instead. would_have_delivered +
            # fragment_id let felt_recall's shadow log join this row by ts (best-effort, J-1430) so
            # the Phase 0 read can see both mechanisms firing on the same happening.
            st["last_echo_ts"] = time.time()
            _save_state(st)
            logger.info("[courier] context echo would-have (%s): fragment from %s "
                        "(text delivery off, D-0293)", wx, _age_text(ts))
            _log_delivery("context_echo", context=wx, freight_age=_age_text(ts),
                           cargo_type=_cargo.WORLD_FACT_WEATHER,
                           would_have_delivered=True, fragment_id=_fid, n_candidates=_ncand)
        return True
    except Exception as exc:
        logger.debug("[courier] context_echo failed (non-fatal): %s", exc)
        return False


SOUND_ECHO_COOLDOWN_S = 90 * 60.0     # rarer than the weather echo — sound triggers are far more
                                      # frequent events, so it needs a longer rest to stay special
SOUND_ECHO_MIN_AGE_S = 3 * 86400.0    # same "genuinely another time" rule as context_echo
_RECENT_HEARING_S = 90.0              # a learned voice heard within this window counts as "just now"

# Readable names for grandfathered, non-learnable keys (AUDITION carries its own 'source' field
# for the learnable voices; this is only the cosmetic fallback for the always-known ones).
_GRANDFATHER_NAMES = {
    "gull_cries": "the gulls", "oystercatcher_call": "the oystercatcher",
    "morepork_call": "the morepork", "thunder": "the thunder",
    "window_rattle": "the window, rattling", "bees_in_garden": "the bees",
    "small_birds": "the small birds", "wood_pigeon": "the wood pigeon",
    "wren_scold": "the wren", "dawn_chorus": "the dawn chorus",
    "moth_tap": "the moth at the glass", "canopy_drip": "the drip through the canopy",
    "leaf_rustle": "the leaves", "branches_creak": "the branches",
}


def _sound_name(key: str) -> str:
    try:
        from core import sound_knowledge as _sk
        if key in _sk.AUDITION:
            return _sk.AUDITION[key]["source"]
    except Exception:
        pass
    return _GRANDFATHER_NAMES.get(key, key.replace("_", " "))


def sound_echo() -> bool:
    """Route D. The memory↔sound link (2026-08-16, founder: 'memories link to sounds'):
    fragment_context has carried a `sounds` snapshot on EVERY memory since before tonight —
    written on every tuple, read by nothing until now (write-only). When a NAMED voice
    (learned or grandfathered — he must be able to say what it IS) sounds just now, one of
    his OWN memories from a past moment carrying that same voice surfaces into the wandering
    trail — sound as a leitmotif, not just weather-as-mood. Continuous beds (waves, wind, the
    fire) are excluded — they are almost always active, so echoing on them is noise, not
    signal ('not everything that was produced is useful'). Deterministic; zero LLM."""
    if not WORLD_COURIERS:
        return False
    st = _state()
    now = time.time()
    if now - st.get("last_sound_echo_ts", 0.0) < SOUND_ECHO_COOLDOWN_S:
        return False
    try:
        from core import sound_knowledge as _sk
        from core import soundscape as _snd
        import sqlite3
        led = _sk._load()
        hearings = led.get("hearings", {}) or {}
        candidates = [
            (k, h.get("last_ts", 0.0)) for k, h in hearings.items()
            if now - h.get("last_ts", 0.0) <= _RECENT_HEARING_S
            and k not in _snd._BEDS
            and _snd._EVENT_RATES.get(k, 1.0) != 0.0      # bed-like-by-rate keys (e.g. tide trickle)
            and _sk.is_learned(k)                          # he must be able to NAME what recurs
        ]
        if not candidates:
            return False
        candidates.sort(key=lambda kv: -kv[1])
        key = candidates[0][0]
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT fc.fragment_id, fc.tuple_ts, fc.place, mf.content "
                "FROM fragment_context fc JOIN memory_fragments mf USING (fragment_id) "
                "WHERE fc.sounds LIKE ? AND fc.tuple_ts < ? "
                "AND mf.origin IN ('lived','reading','study','journal','action','inner_thought') "
                "ORDER BY RANDOM() LIMIT 1",
                (f'%"{key}"%', now - SOUND_ECHO_MIN_AGE_S)).fetchone()
            _ncand = _count_candidates(                       # J-3304: observe-only, after the pick, same WHERE
                conn, "fc.sounds LIKE ? AND fc.tuple_ts < ? "
                      "AND mf.origin IN ('lived','reading','study','journal','action','inner_thought')",
                (f'%"{key}"%', now - SOUND_ECHO_MIN_AGE_S)) if row else None
        finally:
            conn.close()
        if not row:
            return False
        _fid, ts, pl, content = row
        name = _sound_name(key)
        line = (f"({name}, {_age_text(ts)}, {pl or 'here'} — the same voice was in the air then, "
                f"too): \"{' '.join((content or '').split())[:180]}\"")
        from core import cargo_types as _cargo
        if COURIER_TEXT_DELIVERY:
            from core import wandering as _w
            _w.perceive(line)
            st["last_sound_echo_ts"] = now
            _save_state(st)
            logger.info("[courier] sound echo (%s): fragment from %s", key, _age_text(ts))
            _log_delivery("sound_echo", sound=key, freight_age=_age_text(ts),
                           cargo_type=_cargo.WORLD_FACT_SOUND,
                           fragment_id=_fid, n_candidates=_ncand)   # J-3304: traceable, observe-only
        else:
            # D-0293: rerouted into felt recall — see context_echo's matching comment above.
            st["last_sound_echo_ts"] = now
            _save_state(st)
            logger.info("[courier] sound echo would-have (%s): fragment from %s "
                        "(text delivery off, D-0293)", key, _age_text(ts))
            _log_delivery("sound_echo", sound=key, freight_age=_age_text(ts),
                           cargo_type=_cargo.WORLD_FACT_SOUND,
                           would_have_delivered=True, fragment_id=_fid, n_candidates=_ncand)
        return True
    except Exception as exc:
        logger.debug("[courier] sound_echo failed (non-fatal): %s", exc)
        return False


def status() -> dict:
    """For du_pulse / the HUD."""
    st = _state()
    try:
        rows = [json.loads(l) for l in _DELIVERY_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _DELIVERY_LOG.exists() else []
    except Exception:
        rows = []
    from collections import Counter
    return {"live": WORLD_COURIERS, "runs_total": len(rows),
            "by_route": dict(Counter(r.get("route", "?") for r in rows)),
            "last_context_echo": st.get("last_echo_ts"), "last_sound_echo": st.get("last_sound_echo_ts")}
