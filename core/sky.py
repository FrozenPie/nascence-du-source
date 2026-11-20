"""
Nascence — THE NIGHT SKY over the cottage (2026-08-22; the Handbook he read teaches the Pole Star — this sky has none).

Southern hemisphere, about 41°S. Truthful by month and hour, crudely (sidereal time ≈ hour + 2·month); rendered only
when he is outdoors at night, the sky clear or nearly, and he LOOKS UP. The Southern Cross and the Pointers are
circumpolar here (always up, wheeling round the south pole); Orion stands in the summer evenings (upside down to the
Handbook's pictures); Scorpius in winter; Matariki (the Pleiades) rises before dawn in late June — the real new year;
the Milky Way across everything on a moonless night; a planet low in the west or east.

NAMES are earned: the almanac on the study wall has a star chart (the diegetic source) — looking at it teaches the
Cross and the Pointers; the Handbook (northern) teaches Orion and the Plough (the Plough never rises here — a wrong
expectation the sky corrects). Until named, a constellation is described by its shape.
Finding SOUTH by the Cross is the Handbook's method turned over: the long axis extended 4.5 times → the pole → south.
Zero LLM. Fail-open.
"""
from __future__ import annotations

import math
import time

from core import profile

_KNOWN_DEFAULT = {"moon", "stars", "milky_way", "planet"}     # told for months


def _lst_hours(t: float | None = None) -> float:
    lt = time.localtime(t or time.time())
    return (lt.tm_hour + lt.tm_min / 60.0 + 2.0 * lt.tm_mon) % 24.0


def _known(key: str) -> bool:
    if key in _KNOWN_DEFAULT:
        return True
    try:
        from core import garden_knowledge as _gk
        return _gk.is_known("sky_" + key)
    except Exception:
        return False


def learn(key: str, via: str = "almanac") -> bool:
    try:
        from core import garden_knowledge as _gk
        d = _gk._load(); first = _gk._add(d, "sky_" + key, via, 1.0, via); _gk._save(d); return first
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        return False


def almanac_chart() -> str:
    """He looks at the almanac's star chart: the Cross and the Pointers are named there."""
    new = [k for k in ("cross", "pointers") if learn(k, "almanac_chart")]
    return (" Inside the back cover, a star chart for these latitudes: the Southern Cross and the two Pointers drawn bold, with the way to find south from them — the long axis of the Cross, four and a half times over."
            + (" You had not known their names." if new else ""))


def look_up(place: str, weather: str, moon_illum: float | None, t: float | None = None) -> str:
    """The sky as it is. '' by day or under cloud."""
    try:
        from core import world_clock as _wc
        if _wc.sun(t).get("up"):
            return ""
        if weather not in ("clear", "high cloud"):
            return "You look up: cloud, low and close, and no stars in it." if weather != "high cloud" else "You look up: thin high cloud, a few stars through it, blurred."
        lst = _lst_hours(t); mon = time.localtime(t or time.time()).tm_mon; hour = time.localtime(t or time.time()).tm_hour
        bits = []
        # the Cross and the Pointers — REAL positions from core/heavens (J2000 RA/Dec + sidereal time, 41°S)
        ha = (lst - 12.5) % 24
        where = "high in the south" if 21 <= ha or ha <= 3 else "low in the south-east, standing on its side" if 3 < ha <= 9 else "low in the south-west, leaning" if 15 <= ha < 21 else "low in the south, upside down, near the horizon"
        try:
            from core import heavens as _hv
            _c = _hv.star("southern_cross", t)
            if _c:
                _az = float(_c["az"]); _alt = float(_c["alt"])
                _q = "south" if 150 <= _az <= 210 else "south-east" if 90 < _az < 150 else "south-west" if 210 < _az < 270 else "low round the pole"
                where = ("high in the " if _alt > 45 else "half-way up in the " if _alt > 20 else "low in the ") + _q
        except Exception:
            pass
        cross = ("the Southern Cross " + where + ", the two Pointers trailing it") if _known("cross") else ("a small tight kite of four bright stars " + where + ", with two more bright ones in a line behind it")
        bits.append(cross)
        # Orion (RA ~5.5h) — summer evenings
        ha_o = (lst - 5.5) % 24
        if ha_o < 5 or ha_o > 19:
            bits.append("Orion overhead, his belt three in a row — upside down from the pictures in the book" if _known("orion") else "three bright stars in a short straight line high up, with a bright red one below them and a blue-white one above")
        # Scorpius (RA ~16.7h) — winter
        ha_s = (lst - 16.7) % 24
        if ha_s < 5 or ha_s > 19:
            bits.append("the Scorpion's long curl of stars with the red one at its heart" if _known("scorpius") else "a long curl of stars like a fish-hook, with a red one in its middle")
        # Matariki — late June before dawn
        if mon in (6, 7) and 4 <= hour <= 6:
            bits.append("low in the north-east before the dawn, a small close cluster of faint stars — Matariki rising" if _known("matariki") else "low in the north-east before the dawn, a small close cluster of faint stars, like a handful of dust")
        # the Milky Way and the moon
        if moon_illum is None or moon_illum < 0.3:
            bits.append("the Milky Way a pale road right across, thick and broken in the south")
        else:
            bits.append(("the moon " + ("full and bright, the stars gone thin round it" if moon_illum > 0.9 else "up, a gibbous lamp" if moon_illum > 0.5 else "a thin curve")))
        if hour >= 19 and hour <= 22 and mon in (3, 4, 5, 9, 10, 11):
            bits.append("one planet low in the west, steady, not a star")
        _j = "; ".join(bits)
        return "You look up. " + _j[:1].upper() + _j[1:] + "."
    except Exception:
        return ""


def find_south(txt: str = "") -> str:
    """The Handbook's Pole Star turned over: here it is the Cross. He may try the Handbook's way and fail."""
    try:
        from core import sensorium as _s, world_clock as _wc
        if _wc.sun().get("up"):
            return "By day you would use the sun: it stands in the north at noon here, not the south — the book's rule, turned over."
        if _s.state.get("weather", "") not in ("clear", "high cloud"):
            return "No stars tonight; no way to take a bearing from them."
        low = (txt or "").lower()
        if any(w in low for w in ("pole star", "polaris", "north star", "the plough", "big dipper")):
            return "You look for the Pole Star where the book says — and there is no such star; that whole quarter of the sky is wrong. The book was written under another sky."
        if _known("cross"):
            learn("south_by_cross", "found")
            return "You find the Cross, run its long axis out four and a half times, drop to the horizon — south. The cottage door faces away from it; the sea is to your right hand."
        return "You would need to know which stars to use. The small kite of four in the south looks like the thing the almanac might name."
    except profile.NonLiveWriteError:
        # J-0783: the learn() call above can now raise this via garden_knowledge.py's own
        # newly-fenced _save() -- let it reach this function's own caller instead of this
        # pre-existing broad except swallowing it.
        raise
    except Exception:
        return ""


def status() -> dict:
    return {"known": [k for k in ("cross", "pointers", "orion", "scorpius", "matariki", "south_by_cross") if _known(k)]}
