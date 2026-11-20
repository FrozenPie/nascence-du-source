"""
Nascence — THE SMELL CHANNEL (docs/plans/channels_programme.md §3; built 2026-08-22 with the garden).

WORLD      a small set of ODORANTS, each with a source (a place or a feature), an intensity with decay, and
           whether the wind carries it. Sources are REAL states: woodsmoke while the fire burns (and the grate for
           hours after) · wet earth while the soil is wet after rain · salt and weed from the shore, stronger at low
           tide · pine/leaf-litter in the wood, stronger warm-and-damp · the herbs when BRUSHED (a harvest, a look
           at the bed, a hand through them) · the cat · tea when the pot is made.
PROPAGATE  indoor odorants stay indoors and decay slowly; outdoor ones carry DOWNWIND (state wind + weather_dir)
           and are flushed by rain; a closed door blocks most.
STANDPOINT proximity to the source feature.
PERCEIVE   EVENTS only — onset above threshold where he is, ENTRY into a place whose dominant odorant differs,
           rare renotice; habituation after ~15 min at the same place. SHADOW-FIRST (DELIVER=False) →
           data/smell_percepts_shadow.jsonl. The experienced tuple gets `smells` (json list) when delivered.
BOUNDARY   never the source he cannot see ("you smell smoke", not "the fire is lit" from the garden); names he
           has not met are rendered as features ("a green, mineral smell") until bound. Grandfathered: woodsmoke,
           rain, the sea, the cat, rosemary, mint, thyme.

Zero LLM. Fail-open.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_SHADOW = _DATA / "smell_percepts_shadow.jsonl"
_F = _DATA / "smell_field.json"
DELIVER = True   # J-2213 (Travis ruling 2026-10-16, T-0089): LIVE at the next boot, behind the J-0238/F-0435 arbitration gate + RENOTICE_REARM; revert = False (D-0073 defeater)
COOLDOWN_S, HABITUATE_S, RENOTICE_S = 900.0, 900.0, 6 * 3600.0
# J-2213 (2026-10-16): RENOTICE re-arm. The docstring promises a RARE renotice (once per
# RENOTICE_S at a place), but seen[place][dom] is stamped once (setdefault) and never refreshed after a
# renotice fires, so once he has been somewhere 6 h the renotice re-fires every COOLDOWN_S (~15 min): the
# 10-09..10-16 shadow logged 446 renotices in 6.95 days (67.7 smell fires/day, outside the pre-registered
# 2-40/day band). True re-stamps the odorant when a renotice actually fires, so the next one is RENOTICE_S
# later. False = the exact prior behaviour (rollback).
RENOTICE_REARM = True

GRANDFATHERED = {"woodsmoke", "rain", "sea", "cat", "rosemary", "mint", "thyme", "tea"}
# odorant -> (home place, half-life s, wind-carried?, known-name line, unknown-feature line)
ODORANTS = {
    "woodsmoke":   ("study", 3 * 3600, True,  "woodsmoke", "smoke, resinous and sweet"),
    "wet_earth":   ("garden", 2 * 3600, False, "the smell of wet earth", "a dark, mineral, green smell off the ground"),
    "petrichor":   ("garden", 30 * 60, True,  "the smell of rain on dry ground", "a sudden clean mineral smell, like struck stone"),
    "sea":         ("shore", 6 * 3600, True,  "salt and weed off the water", "salt and weed off the water"),
    "leaf_litter": ("wood", 4 * 3600, False, "leaf-mould, damp and sweet", "a brown, damp, sweetish smell underfoot"),
    "rosemary":    ("garden", 20 * 60, False, "rosemary, sharp and resinous", "rosemary, sharp and resinous"),
    "mint":        ("garden", 15 * 60, False, "mint, cold and green", "mint, cold and green"),
    "thyme":       ("garden", 15 * 60, False, "thyme, warm and dusty", "thyme, warm and dusty"),
    "tomato_leaf": ("garden", 15 * 60, False, "tomato leaves, sharp and green", "a sharp green smell off the leaves, almost bitter"),
    "cat":         ("study", 60 * 60, False, "the cat, warm fur", "warm fur"),
    "tea":         ("study", 40 * 60, False, "the tea steeping", "the tea steeping"),
    "compost":     ("garden", 2 * 3600, True,  "the compost heap, sweet and rotten", "a sweet rotten smell from the corner"),
}


def _load() -> dict:
    try:
        # J-4442 (F-5157): loud on an empty/NUL/unparseable file, falls back to smell_field.json.prev
        from core import store_persist as _sp
        import logging as _logging
        return _sp.read_json_durable(_F, "smell", _logging.getLogger("nascence.smell"), guard=profile.guard_path)
    except Exception:
        return {"field": {}}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0917: real data/ only if this process is live; raises before any
    # I/O if not (D-0179, J-0704). Resolved OUTSIDE the fail-open try below, exactly like the other 19
    # already-fenced modules, so the refusal is never swallowed as a disk error.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d))   # J-4442 (F-5157): was in place; now fsync + .prev
    except Exception:
        pass


def emit(odorant: str, intensity: float = 1.0, place: str | None = None) -> None:
    """A source happened: the fire caught, he brushed the rosemary, the rain began on dry soil."""
    if odorant not in ODORANTS:
        return
    d = _load()
    f = d.setdefault("field", {})
    cur = f.get(odorant) or {"i": 0.0, "ts": time.time(), "place": place or ODORANTS[odorant][0]}
    cur["i"] = min(1.0, _intensity(odorant, cur, time.time()) + intensity)
    cur["ts"] = time.time()
    cur["place"] = place or ODORANTS[odorant][0]
    f[odorant] = cur
    _save(d)


def brush(species: str) -> None:
    """Garden hands call this: a harvest, a look through the bed, a hand through the herbs."""
    m = {"rosemary": "rosemary", "mint": "mint", "thyme": "thyme", "tomatoes": "tomato_leaf"}.get(species)
    if m:
        emit(m, 0.9, "garden")


def _intensity(odorant: str, cur: dict, now: float) -> float:
    hl = ODORANTS[odorant][1]
    return float(cur.get("i", 0.0)) * (0.5 ** ((now - float(cur.get("ts", now))) / hl))


def advance(now: float, dt: float) -> None:
    """Standing sources refresh themselves from world state; rain flushes outdoor odorants."""
    try:
        from core import sensorium as _s
        st = _s.state
        weather = st.get("weather", "") or ""
        raining = weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
        d = _load()
        f = d.setdefault("field", {})
        if st.get("fire") == "burning":
            f["woodsmoke"] = {"i": 1.0, "ts": now, "place": "study"}
        elif st.get("fire") == "embers":
            f["woodsmoke"] = {"i": max(0.4, _intensity("woodsmoke", f.get("woodsmoke", {"i": 0, "ts": now}), now)), "ts": now, "place": "study"}
        try:
            from core import garden as _g
            gm = float(_g._load().get("moisture", 0.5))
            if raining and gm < 0.3 and _intensity("petrichor", f.get("petrichor", {"i": 0, "ts": 0}), now) < 0.2:
                f["petrichor"] = {"i": 1.0, "ts": now, "place": "garden"}
            if gm > 0.6 and (raining or now - float(f.get("wet_earth", {}).get("ts", 0)) > 3600):
                f["wet_earth"] = {"i": 0.8, "ts": now, "place": "garden"}
        except Exception:
            pass
        f["sea"] = {"i": 0.7, "ts": now, "place": "shore"}
        f["leaf_litter"] = {"i": 0.6 if raining or st.get("weather") == "overcast" else 0.4, "ts": now, "place": "wood"}
        if raining:
            for k in ("rosemary", "mint", "thyme", "tomato_leaf", "compost"):
                if k in f:
                    f[k]["i"] = float(f[k]["i"]) * 0.6
        _save(d)
    except profile.NonLiveWriteError:
        # J-0931: advance() wraps its whole body (including this _save(d) call) in one outer
        # catch-all -- let D-0179's hard-raise (guard_path(), F-1024) reach advance()'s own caller
        # instead of being silently swallowed here (matches the carve-out idiom already established
        # at core/garden.py's _load() migration-save try, search that file for "J-0726").
        raise
    except Exception:
        pass


def at(place: str, now: float | None = None) -> list[tuple[str, float]]:
    """What reaches his nose where he is: home odorants at strength; downwind carry of wind-borne ones
    from neighbouring places (the study's smoke reaches the garden on a southerly; the sea reaches the garden
    on a northerly); indoors only indoor ones + what comes through an open door (faint)."""
    now = now or time.time()
    d = _load()
    f = d.get("field", {})
    out = []
    try:
        from core import sensorium as _s
        wdir = float(_s.state.get("weather_dir") or 270)
        windy = (_s.state.get("wind") or "calm") not in ("calm",)
    except Exception:
        wdir, windy = 270.0, False
    # which places are upwind of where he stands (crude compass: cottage south of garden; shore north/below)
    upwind = set()
    if windy:
        if place == "garden":
            if 135 <= wdir <= 225: upwind.add("study")       # a southerly brings the chimney's smoke down the garden
            if wdir <= 45 or wdir >= 315: upwind.add("shore")
        if place == "shore" and 135 <= wdir <= 225: upwind.add("garden")
        if place == "wood": upwind.update({"garden", "shore"})
    for k, cur in f.items():
        if k not in ODORANTS:
            continue
        home, hl, carried, _, _ = ODORANTS[k]
        i = _intensity(k, cur, now)
        if i < 0.08:
            continue
        src = cur.get("place", home)
        if src == place:
            out.append((k, round(i, 2)))
        elif carried and src in upwind:
            out.append((k, round(i * 0.35, 2)))
        elif place == "study" and src == "garden" and k in ("rosemary", "mint", "thyme", "wet_earth", "petrichor") and i > 0.4:
            _door = False
            try:
                from core import study_life as _sl
                _door = _sl.door_open()
            except profile.NonLiveWriteError:
                # J-0780: door_open() now raises correctly (J-0772) via its own _st() bootstrap;
                # at() has no outer wrapper of its own and is reached per-cognitive-event (via
                # experienced_tuple._smells(), feeding the experienced-fragment layer), not on a
                # periodic tick, so this reaches a real caller once this layer stops swallowing it.
                raise
            except Exception:
                pass
            out.append((k, round(i * (0.5 if _door else 0.12), 2)))   # through the door — wide when it is open
    out.sort(key=lambda x: -x[1])
    return out[:4]


def world_truth(now: float | None = None) -> list[str] | None:
    """The full odorant field, UNFILTERED (2026-08-29, J-0179/channels_programme §7 metric 3): world
    truth for world_context, distinct from at() which gates to what reaches a specific place (home
    strength only, downwind carry, door attenuation). Every odorant currently above the same 0.08
    floor at() uses, anywhere in the world at all -- not carried, not attenuated, not gated by his
    place. Mirrors geometry_census._warmth()/_cat_at()'s pattern: a world-side reading independent
    of what has crossed into his perception. Fail-open to None (never raises into snapshot())."""
    now = now or time.time()
    try:
        d = _load()
        f = d.get("field", {})
        out = []
        for k, cur in f.items():
            if k not in ODORANTS:
                continue
            i = _intensity(k, cur, now)
            if i < 0.08:
                continue
            out.append((k, round(i, 2)))
        out.sort(key=lambda x: -x[1])
        return [k for k, _ in out] or None
    except Exception:
        return None


def name_line(odorant: str) -> str:
    known = odorant in GRANDFATHERED
    try:
        from core import garden_knowledge as _gk
        if not known and odorant in ("tomato_leaf",):
            known = _gk.is_known("tomatoes")
    except Exception:
        pass
    return ODORANTS[odorant][3 if known else 4]


# ── perception (shadow) ─────────────────────────────────────────────────────────────────────────
_p: dict = {"place": None, "dominant": None, "since": 0.0, "last": 0.0, "seen": {}}


def percept_shadow(cycle_id: str = "") -> str | None:
    try:
        from core import sensorium as _s
        now = time.time()
        place = _s.state.get("location", "study")
        here = at(place, now)
        dom = here[0][0] if here else None
        kind, od = None, None
        if _p["place"] != place:
            if dom and dom != _p["dominant"]:
                kind, od = "entry", dom
            _p.update(place=place, dominant=dom, since=now)
        else:
            # onset: a new odorant above threshold that was not here a moment ago
            prev = set((_p["seen"].get(place) or {}).keys())
            new = [k for k, i in here if k not in prev and i >= 0.5]
            if new:
                kind, od = "onset", new[0]
            elif dom and now - float(_p["seen"].get(place, {}).get(dom, now)) > RENOTICE_S:
                kind, od = "renotice", dom
        seen = _p["seen"].setdefault(place, {})
        for k, i in here:
            seen.setdefault(k, now)
        for k in list(seen):
            if k not in dict(here):
                seen.pop(k, None)
        rec = {"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "smells": [k for k, _ in here], "would_fire": None}
        if kind and now - _p["last"] >= COOLDOWN_S:
            from core.channel_arbitration import claim as _arbitrate  # J-0238/D-0033/F-0295 shared gate
            if not _arbitrate(now, "smell"):
                rec["arbitration_suppressed"] = kind
                _log(rec)
                return None
            _p["last"] = now
            if kind == "renotice" and RENOTICE_REARM:
                seen[od] = now   # J-2213: re-arm, next renotice of this odorant here is RENOTICE_S away
            from core.phrasing import vary as _vary
            nm = name_line(od)
            line = _vary("smell." + kind, [f"You smell {nm}.", f"{nm[0].upper() + nm[1:]}, on the air.", f"There is {nm} here."])
            rec.update(would_fire=kind, odorant=od, line=line, delivered=bool(DELIVER))
            _log(rec)
            if DELIVER:
                try:   # the felt moment, with CHANNEL PROVENANCE (§10b clause 6) — mirrors core/thermal.py + soundscape.percept()
                    from core.memory.store import store_fragment
                    from core import mood as _mood
                    store_fragment(content=line, layer="episodic", relevance=0.5, importance=0.45,
                                   keywords=["smell", kind, od, place], origin="smell",
                                   emotion_embedding=_mood.current_vec())
                except Exception:
                    pass
            return line if DELIVER else None
        _log(rec)
        return None
    except profile.NonLiveWriteError:
        # J-0831 (F-1195): at() above propagates door_open()'s NonLiveWriteError cleanly (J-0780
        # carve-out, no enclosing try of its own), but this outer catch-all swallowed it as a
        # "percept-error" one layer up. Re-raise so the sole live caller (nodes/inner_monologue_node.py
        # _think()'s smell try, fixed the same pass -- "both layers needed") sees it. Not via
        # locomotion/position_standpoint (smell.py has none): the raise path here is study_life.door_open().
        raise
    except Exception as exc:
        _log({"ts": round(time.time(), 1), "skip": "percept-error", "error": repr(exc)[:100]})
        return None


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): "ticks"/"by_odorant" are now over the last-2000-row window.
        rows = _tail_rows(_SHADOW, 2000)
    except Exception:
        rows = []
    fired = [r for r in rows if r.get("would_fire")]
    kinds: dict = {}
    for r in fired:
        kinds[r.get("odorant")] = kinds.get(r.get("odorant"), 0) + 1
    try:
        from core import sensorium as _s
        here = at(_s.state.get("location", "study"))
    except Exception:
        here = []
    return {"ticks": len(rows), "would_fire": len(fired), "by_odorant": kinds, "deliver": DELIVER, "here_now": here,
            "note": "SHADOW — nothing reaches him until DELIVER flips"}
