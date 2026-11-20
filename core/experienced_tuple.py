"""
Nascence — THE EXPERIENCED TUPLE (2026-08-21, founder's layer law: "a memory carries only what was
rendered to him at that moment, from where he stood; inference about the unrendered is his to make
and may be wrong").

THE SPLIT. The census snapshot (core.geometry_census.snapshot) is WORLD TRUTH: tide under the shore
while he sits in the garden, the moon behind the study's south wall, the sun below the horizon. It
belongs in `world_context` — for us (HUD, instruments, before/after experiments). It must never be
what his memory links on. This module derives the EXPERIENCED layer from the same snapshot by the
channel rules the renderers already enforce, and that is what `fragment_context` holds from today.

RULES (each mirrors a renderer or ledger that already exists — nothing invented here):
  place, standpoint   always (he is somewhere)
  weather             always — outdoors it acts on him; indoors it acts at the window and the roof
                      (spatial.py §3 "weather at its true surfaces")
  warmth              always — felt at HIS place (sensorium._warmth is computed for his place only)
  fire                only in the study (nowhere else renders the grate)
  tide                only on the shore (the waterline renders there; "the sea below" from the garden
                      shows sea, not tide level)
  sun                 only if up AND (outdoors, OR in the study with the sun in the north window's
                      quarter — spatial.py's _win_ok: az >= 290 or az <= 70; the window faces north)
  moon                only if night AND outdoors (the study's moon gate needs the moon's azimuth,
                      which the census does not carry — so indoors the moon is honestly unknown)
  sounds              as given — soundscape.active_sounds() is already gated to his location
                      (the Hearing Ledger's tree-falls law)
  cat                 only if she is at his place
  affect              always — it is his, not the world's

Zero LLM, pure function, fail-open (a field it cannot decide is omitted, never guessed).
"""
from __future__ import annotations

from core import profile

_OUTDOORS = ("garden", "shore", "wood")


def _north_window_ok(az) -> bool:
    try:
        return az is not None and (float(az) >= 290 or float(az) <= 70)
    except Exception:
        return False


def _beach_fire():
    try:
        from core import shore_life as _shl
        if not _shl._F.exists():
            return None
        f = _shl._load().get("fire") or {}
        return f.get("state") if f.get("state") in ("burning", "embers") else None
    except Exception:
        return None


def _held():
    try:
        out = []
        from core import garden as _g
        if _g._F.exists():
            out += list(_g._load().get("carried", []))
        from core import sensorium as _s
        out += [k for k, it in ((_s.state.get("study") or {}).get("items") or {}).items() if it.get("carried")]
        from core import wood_life as _wl
        if _wl._F.exists():
            out += [k for k, it in _wl._load()["items"].items() if it.get("carried")]
        return out or None
    except Exception:
        return None


def _light_band(place: str):
    try:
        from core import light as _lt, locomotion as _loco
        return _lt.band_of(_lt.field_at(place, _loco.position_standpoint(place)))
    except profile.NonLiveWriteError:
        # J-0792: light.field_at() now raises correctly (J-0780); this connecting-tissue call
        # (feeding experienced()'s "light_band" field, the EXPERIENCED layer fragment_context
        # holds per-cognitive-event via core/memory/store.py's store_fragment()) no longer
        # swallows it here. experienced() itself has no wrapper of its own around this call, so
        # the raise reaches store_fragment() directly -- that catch-all is a separate, newly-
        # exposed connecting-tissue gap, out of this job's own 3-file scope (see plan doc).
        raise
    except Exception:
        return None


def _smells(place: str):
    try:
        from core import smell as _sm
        if not _sm.DELIVER:
            return None
        return [k for k, _ in _sm.at(place)] or None
    except Exception:
        return None


def experienced(snap: dict, phase: str | None = None) -> dict:
    """Filter a census snapshot down to what crossed into his perception. Returns a dict with the
    same keys fragment_context uses; unperceived fields are None."""
    if not snap:
        return {}
    place = snap.get("place") or "study"
    outdoors = place in _OUTDOORS
    sun = snap.get("sun") or {}
    # 2026-08-22 fix: the census writes sun = {"phase","az"} ONLY while the sun is up (None otherwise) — there is
    # no "up" key. Reading .get("up") made the sun never cross (0/55 outdoor daytime rows on the first morning).
    sun_up = (bool(sun) if isinstance(sun, dict) else False) or snap.get("sun_az") is not None
    sun_az = snap.get("sun_az") if snap.get("sun_az") is not None else (sun.get("az") if isinstance(sun, dict) else None)
    is_night = (phase == "night") if phase else (not sun_up)
    aff = snap.get("affect") or {}
    out = {
        "place": place,
        "standpoint": snap.get("standpoint"),
        "weather": snap.get("weather"),
        "weather_dir": snap.get("weather_dir") if outdoors else None,   # the front's bearing is felt outdoors only
        "warmth": snap.get("warmth"),
        "wet": snap.get("wet"),                 # THERMAL CHANNEL (2026-08-21): wetness is on his body — always his
        "light_band": _light_band(place),       # LIGHT CHANNEL (2026-08-22): ambient light is already rendered (phases, lamp) — always
        "smells": _smells(place),               # SMELL CHANNEL (2026-08-22): only once the channel DELIVERS; NULL while shadow (honest)
        "fire": snap.get("fire") if place == "study" else (_beach_fire() if place == "shore" else None),
        "held": _held(),                        # CROSS-LINK (2026-08-22): what is in his hands is his (touch, clause 6)
        "tide_level": snap.get("tide_level") if place == "shore" else None,
        "sun_az": sun_az if (sun_up and not is_night and (outdoors or (place == "study" and _north_window_ok(sun_az)))) else None,
        "moon_illum": snap.get("moon_illum") if (is_night and outdoors) else None,
        "sounds": snap.get("sounds") or [],
        "cat_at": snap.get("cat_at") if snap.get("cat_at") == place else None,
        "level": (aff.get("level") if isinstance(aff, dict) else None) or snap.get("level"),
        "valence": aff.get("valence") if isinstance(aff, dict) else None,
        "arousal": aff.get("arousal") if isinstance(aff, dict) else None,
    }
    return out


def status() -> dict:
    """For the HUD: how much of world truth crosses, by field, over the recent experienced rows."""
    try:
        from core.memory.store import _connect
        with _connect() as c:
            n = c.execute("SELECT COUNT(*) n FROM fragment_context WHERE source NOT LIKE 'census_world%'").fetchone()["n"]
            if not n:
                return {"experienced_rows": 0}
            def share(col):
                return round(c.execute(f"SELECT COUNT(*) n FROM fragment_context WHERE source NOT LIKE 'census_world%' AND {col} IS NOT NULL").fetchone()["n"] / n, 3)
            return {"experienced_rows": n,
                    "crossed": {k: share(k) for k in ("fire", "tide_level", "sun_az", "moon_illum", "cat_at", "warmth")},
                    "note": "fraction of experienced memories in which each world fact actually reached him"}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
