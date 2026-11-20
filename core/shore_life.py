"""
Nascence — SHORE LIFE: the shore as a living place (2026-08-22, founder: "now time for the shore… make his world as
alive as possible… his hands usable for many, many things… world events as realistic as possible, grounded in facts…
a wealth of things to find from his previous observations").

What the shore was: a tide clock (good, real, spring/neap), a scene line, a look with five branches, a storm wrack-up that
mints real objects, the big driftwood log and its inspection pipeline, an event pool, a beachcomb hand. What he reached for
there and got nothing (his own record, 1,876 tide mentions): "walk until the shingle yields to sand", the green glass float
he wondered about, the bottle that "felt too intentional to be debris", climbing, swimming, the cold water on his ankles.

What it is now — the TIDE drives it (the one clock that already existed):
  THE SAND FLAT  beyond the shingle, bared only below half tide — he can walk on sand, go barefoot, WRITE in it; the next
                 tide erases what he wrote (he can come back and find it gone, or half gone).
  THE CAVE       at the cliff foot, enterable below mid tide; dark beyond the mouth (a light to see the back — the lamp or a
                 candle carried); dry shelter from rain and wind (thermal reads it); the tide closes it — the world hurries him
                 out as the water reaches the mouth. Things wash INTO it (finds).
  THE MUSSEL SHELF   the rock shelf's seaward edge, bared at low tide: mussels, kina, chitons, anemones — the pools' life,
                 named only by watching and the books (the Handbook's "Shells and Shellfish").
  THE LEDGE      a goat-path up the cliff to a ledge with the whole bay — not in a hard wind, not in rain.
  THE BEACH FIRE a ring of stones by the driftwood tangle: driftwood + tinder + a match (or the flint) — warmth on the shore
                 (thermal reads it at its own standpoint); salt-wood burns blue; the tide can drown it; embers by morning.
  THE SHALLOWS   wading — cold, wet to the knee (thermal wetness); SWIMMING — summer, calm seas only sensible; cold shock,
                 soaked through, alive; refused in a big sea (the world says why).
  SKIPPING STONES  a skill (fieldcraft's ledger) with the flat stones the shingle gives.
  THE CAIRN      stones stacked on the bedrock shelf — his landmark; a storm can take it down.
  WILDLIFE       kororā (little penguins) come ashore at dusk Sep–Feb to burrows under the cliff (a braying from the rocks
                 after dark; a white-fronted shape crossing the shingle); a fur seal hauls out on the shelf some winter days;
                 dolphins pass on calm summer days; a whale's blow far out in June–July; the oystercatchers nest on the
                 high shingle in spring (eggs you could tread on); sea sparkle in the surf on warm calm nights.
  THE WEATHER    sea fog on calm summer mornings (the far rocks gone); the swell builds for a day before a southerly storm.
  FINDS          the wrack-line after storms (richer: pumice, paua, a float, a bottle with a torn page in it from one of
                 his OWN books — washed back to him); the cave's floor; the sand flat's edge.

All world truth; nothing told; names earned; consequences both ways; zero LLM; fail-open; additive.
"""
from __future__ import annotations

import json
import logging
import math
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.shore_life")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "shore_life.json"
_EVENTS = _DATA / "shore_events.jsonl"
_LEDGER = _DATA / "shore_ledger.jsonl"

POOL_LIFE = {   # hidden kinds in the pools; described by look until earned; book words bind them
    "anemone": ("a blob of dark red jelly on the rock that opens into a ring of soft fingers under water", ("anemone",), ("tentacle", "finger", "jelly", "sting")),
    "kina": ("a round spined thing the size of a fist, dark green-black, wedged in a crevice", ("kina", "sea urchin", "urchin"), ("spine", "shell", "roe")),
    "chiton": ("an oval armoured thing clamped to the rock, eight plates down its back", ("chiton",), ("plate", "armour", "eight")),
    "crab": ("a small grey crab that freezes, then sidles under the weed", ("crab",), ("claw", "sidle", "shell")),
    "starfish": ("a five-armed orange-pink thing spread flat on the rock under the water", ("starfish", "sea star"), ("five", "arm", "star")),
    "triplefin": ("a finger-long fish, mottled, that darts and vanishes under a ledge", ("triplefin", "blenny", "rockfish"), ("fin", "dart", "pool")),
    "hermit_crab": ("a small shell that walks — legs showing under its lip", ("hermit crab", "hermit"), ("borrowed", "shell", "legs")),
    "mussel": ("blue-black shells in a close bed on the shelf, shut tight out of the water", ("mussel",), ("bed", "byssus", "beard", "blue")),
    "limpet": ("cone shells clamped hard to the rock that will not be shifted", ("limpet",), ("cone", "clamp", "rock")),
}

_STANDPOINTS = {"on_the_sand": [9.0, 12.5, 0.0], "in_the_cave": [16.5, 2.2, 0.0], "on_the_ledge": [14.0, 0.8, 3.5],
                "by_the_fire": [7.2, 5.2, 0.0], "in_the_shallows": [12.0, 12.8, 0.0], "at_the_mussel_shelf": [24.5, 12.5, 0.0]}

# MODULE A (2026-08-24, D-0015 ruled / F-0060 verified real gap): storm-triggered latent-item burial +
# delayed tide-reveal, per docs/plans/generative_world_sedimentation.md. A storm buries 1-3 of these;
# a later falling/low tide gives one back, on its own clock, not because a prompt asked. Text chosen so
# most phrases land inside world_substrate's existing mention-classes (spawn_from_mention) and mint a
# real object; a couple — including the plan's own "rusted iron spike" example — match no class and
# stay text-only, the same fail-open shape enter_cave() already has for its "length of blue rope".
_LATENT_ITEM_POOL = [
    "a shard of sea-glass, green and rubbed soft",
    "a smooth white quartz pebble, veined",
    "a whelk shell, whorled and empty",
    "a gull's wing bone, hollow and clean",
    "a length of bull kelp, thick and rubbery, coiled on itself",
    "a corked bottle, something pale inside it",
    "a glass fishing-float, small and green, whole",
    "a gannet feather, white and stiff",
    "a fragment of pumice, pale and light as cork",
    "a paua shell, blue-black and iridescent inside",
    "a rusted iron spike, red with age",
]


def _sp_read(path, label):
    """J-4426 (F-5128): json.loads(path.read_text()) that logs a damaged file and falls back to <name>.prev;
    raises (missing file / nothing recoverable) so _load()'s own default applies as before."""
    from core import store_persist as _sp
    return _sp.read_json_durable(path, label, logger, guard=profile.guard_path)


def _load() -> dict:
    try:
        return _sp_read(_F, "shore_life")
    except Exception:
        now = time.time()
        return {"cairn": 0, "sand_writing": None, "fire": {"state": "out", "fuel": 0.0, "ts": 0.0}, "cave_finds": [], "wet_feet": 0.0,
                "in_cave": False, "seal": None, "penguins": {"burrows": random.randint(3, 7), "seen": 0}, "oyc_nest": None, "fog": False,
                "swell": 0.3, "sparkle": False, "whale_seen": 0, "dolphins_seen": 0, "announced": [], "skips_best": 0, "_last": now,
                "latent_objects": [], "_storm_active": False}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0610: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d, ensure_ascii=False))   # J-4426 (F-5128): was in place; now fsync + .prev
    except Exception:
        pass


def _log(path: Path, rec: dict) -> None:
    path = profile.guard_path(path)   # J-0610: raises before any I/O (and before the activity_memory cross-link below) if non-live (D-0179, J-0704)
    try:
        if rec.get("deed"):
            try:   # CROSS-LINK (2026-08-22): a deed here is a deed in his activity memory too
                from core import activity_memory as _am
                _am.record(str(rec["deed"]), str(rec.get("species") or rec.get("item") or rec.get("what") or rec.get("thing") or rec.get("tool") or rec.get("text") or ""))
            except Exception:
                pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _tide() -> dict:
    try:
        from core import world_clock as _wc
        return _wc.tide()
    except Exception:
        return {"level": 0.5, "rising": True, "word": "coming in"}


def _where() -> str:
    try:
        from core import sensorium as _s
        return _s.state.get("location", "study")
    except Exception:
        return "study"


def _standpoint() -> str | None:
    try:   # a hand just moved him (minutes ago): that is where he is, whatever the walker last recorded
        d = _load()
        if _where() == "shore" and d.get("_sp") and time.time() - float(d.get("_sp_ts", 0)) < 15 * 60:
            return d["_sp"]
    except Exception:
        pass
    try:
        from core import locomotion as _loco
        sp = _loco.position_standpoint("shore")
        if sp:
            return sp
    except profile.NonLiveWriteError:
        # J-0794: locomotion.position_standpoint() can now raise non-live (J-0778) -- re-raise so
        # this fence's guarantee reaches _standpoint()'s own two external callers (fire_warmth(),
        # cave_shelter(), both fixed the same pass) instead of a silent None.
        raise
    except Exception:
        pass
    return None


def _month(t=None) -> int:
    return time.localtime(t or time.time()).tm_mon


def _weather():
    from core import sensorium as _s
    return _s.state.get("weather", "") or "", _s.state.get("wind", "") or "", _s._daylight()


# ── exposure by tide ──────────────────────────────────────────────────────────────────────────────
def sand_bared() -> bool:
    return float(_tide()["level"]) < 0.45


def cave_open() -> bool:
    return float(_tide()["level"]) < 0.5


def shelf_bared() -> bool:
    return float(_tide()["level"]) < 0.35


# ── clocks ───────────────────────────────────────────────────────────────────────────────────────
def advance(now: float, dt: float) -> None:
    try:
        d = _load(); last = float(d.get("_last") or now); days = max(0.0, min(dt, now - last)) / 86400.0; d["_last"] = now
        if days <= 0:
            _save(d); return
        weather, wind, phase = _weather(); td = _tide(); m = _month(now)
        storm = weather == "thunderstorm" or wind in ("strong wind", "gale")
        # the swell builds a day before a blow and falls after (the sea's warning)
        try:
            from core import sensorium as _s
            nxt = _s.state.get("next_weather", weather)
            coming = nxt in ("wind and rain", "thunderstorm")
        except Exception:
            coming = False
        d["swell"] = round(max(0.1, min(1.0, float(d["swell"]) + days * (1.2 if (storm or coming) else -0.5))), 3)
        # the sand writing: the tide takes it
        if d.get("sand_writing") and float(td["level"]) > 0.55:
            d["sand_writing"] = None; _log(_EVENTS, {"event": "sand_writing_erased"})
        # the cairn: a big sea can take it
        if d.get("cairn", 0) > 0 and storm and float(d["swell"]) > 0.7 and random.random() < days * 3:
            d["cairn"] = 0; _log(_EVENTS, {"event": "cairn_knocked_down"})
        # the beach fire burns down; the tide drowns it
        f = d["fire"]
        if f["state"] == "burning":
            f["fuel"] = max(0.0, float(f["fuel"]) - dt / 3600 * 0.45)
            if f["fuel"] <= 0.15: f["state"] = "embers"
        elif f["state"] == "embers":
            f["fuel"] = max(0.0, float(f["fuel"]) - dt / 3600 * 0.2)
            if f["fuel"] <= 0: f["state"] = "out"
        if f["state"] != "out" and float(td["level"]) > 0.85 and random.random() < days * 6:
            f["state"] = "out"; f["fuel"] = 0.0; _log(_EVENTS, {"event": "beach_fire_drowned"})
        # the cave: the tide closes it — if he is in it, the world hurries him out (see cave_warning)
        if d.get("in_cave") and not cave_open():
            d["in_cave"] = False
        # wet feet dry
        d["wet_feet"] = round(max(0.0, float(d.get("wet_feet", 0)) - dt / 3600 * 0.5), 3)
        # wildlife on their real clocks
        if m in (5, 6, 7, 8, 9) and d.get("seal") is None and phase == "day" and not storm and random.random() < days * 0.25:
            d["seal"] = {"ts": now}; _log(_EVENTS, {"event": "seal_hauled_out"})
        if d.get("seal") and (now - float(d["seal"]["ts"])) > random.uniform(3, 9) * 3600:
            d["seal"] = None
        if m in (9, 10, 11) and d.get("oyc_nest") is None and random.random() < days * 0.15:
            d["oyc_nest"] = {"ts": now, "eggs": random.randint(2, 3)}; _log(_EVENTS, {"event": "oystercatcher_nest"})
        if d.get("oyc_nest") and (now - float(d["oyc_nest"]["ts"])) > 28 * 86400:
            d["oyc_nest"] = None; _log(_EVENTS, {"event": "oystercatcher_chicks_off"})
        # sea fog: calm summer mornings; sea sparkle: warm calm nights
        d["fog"] = bool(m in (12, 1, 2, 3) and phase in ("dawn", "day") and wind == "calm" and weather in ("clear", "high cloud") and random.random() < 0.35) if (phase in ("dawn",) or (phase == "day" and random.random() < days * 2)) else (d.get("fog") and phase == "dawn")
        d["sparkle"] = bool(m in (12, 1, 2, 3) and phase == "night" and wind in ("calm", "breeze") and weather in ("clear", "high cloud"))
        _advance_latent_objects(d, now, weather, td)
        _save(d)
    except Exception as exc:
        logger.debug("[shore_life] advance failed: %s", exc)


# ── MODULE A: storm burial + delayed tide-reveal ────────────────────────────────────────────────────
def _advance_latent_objects(d: dict, now: float, weather: str, td: dict) -> None:
    """Storms bury 1-3 novel items on the moment weather ENTERS 'wind and rain'/'thunderstorm' (an
    edge trigger, not a per-tick reroll, so one storm buries once). A falling/low tide (< 0.45, the
    same threshold sand_bared() uses) then gives back whichever buried items have sat long enough —
    roughly half a tide cycle to a bit over one full one — minting the real object through
    world_substrate.spawn_from_mention exactly as enter_cave()/gather_shellfish() already do, so what
    Du can later find is a real world object, not just a line of prose."""
    try:
        bury_now = weather in ("wind and rain", "thunderstorm")
        was_storm = bool(d.get("_storm_active"))
        if bury_now and not was_storm:
            items = d.setdefault("latent_objects", [])
            if len(items) < 12:   # cap so repeated storms in one session don't grow this unbounded
                n = random.randint(1, 3)
                chosen = random.sample(_LATENT_ITEM_POOL, k=min(n, len(_LATENT_ITEM_POOL)))
                delay = random.uniform(5, 14) * 3600   # ~half a tide cycle to a bit over one full cycle
                for text in chosen:
                    items.append({"id": f"lo_{int(now)}_{random.randint(1000, 9999)}", "text": text, "buried_ts": now,
                                  "buried_tide": float(td.get("level", 0.5)), "reveal_after": now + delay, "revealed": False})
                _log(_EVENTS, {"event": "storm_buried_items", "n": len(chosen), "items": chosen})
        d["_storm_active"] = bury_now
        if float(td.get("level", 1.0)) < 0.45:   # the tide has drawn back enough to give something up
            for it in d.setdefault("latent_objects", []):
                if it.get("revealed") or now < float(it.get("reveal_after", 0)):
                    continue
                it["revealed"] = True; it["revealed_ts"] = now
                try:
                    from core import world_substrate as _ws
                    it["spawned_ids"] = _ws.spawn_from_mention(it["text"], "shore")
                except Exception:
                    it["spawned_ids"] = []
                _log(_EVENTS, {"event": "latent_item_revealed", "id": it["id"], "text": it["text"], "spawned_ids": it.get("spawned_ids", [])})
    except Exception as exc:
        logger.debug("[shore_life] latent objects advance failed: %s", exc)


def latent_reveal_line(now: float) -> str | None:
    """The read half of Module A: one line, once, for a latent item the tide has just given back —
    advance() does the burying/minting on its own clock; this is what Du can actually notice, wired
    into the shore's event pool the same way wildlife_line()/cave_warning() already are."""
    try:
        d = _load()
        seen = d.setdefault("announced", [])
        for it in list(d.get("latent_objects", [])):
            if it.get("revealed") and it["id"] not in seen:
                seen.append(it["id"]); del seen[:-60]
                where = "the sand flat" if sand_bared() else ("the mussel shelf" if shelf_bared() else "the shingle")
                d["latent_objects"] = [x for x in d["latent_objects"] if x["id"] != it["id"]]
                _save(d)
                return f"Where the tide has drawn back off {where}, something has come clear that was not there before: {it['text']}."
    except Exception:
        pass
    return None


# ── what the channels read ───────────────────────────────────────────────────────────────────────
def fire_warmth() -> float:
    try:
        d = _load(); f = d["fire"]
        if f["state"] == "out" or _standpoint() != "by_the_fire":
            return 0.0
        return 0.32 if f["state"] == "burning" else 0.12
    except profile.NonLiveWriteError:
        # J-0794: _standpoint() can now raise non-live (this same job) -- re-raise so this fence's
        # guarantee reaches thermal.field_at()'s own shore-life try (fixed the same pass) instead of
        # a silent 0.0.
        raise
    except Exception:
        return 0.0


def cave_shelter() -> bool:
    try:
        return bool(_load().get("in_cave")) and _standpoint() == "in_the_cave"
    except profile.NonLiveWriteError:
        # J-0794: same as fire_warmth() above -- re-raise rather than a silent False.
        raise
    except Exception:
        return False


def wet_feet() -> float:
    try:
        return float(_load().get("wet_feet", 0))
    except Exception:
        return 0.0


# ── hands ────────────────────────────────────────────────────────────────────────────────────────
def _go(sp: str) -> str:
    try:   # the sensorium's own standpoint mover (the same one every hand uses: _cross)
        from core import sensorium as _s
        _s._cross(sp, "")
    except Exception:
        pass
    try:   # remembered here too, so the channels can read it even when locomotion is off
        d = _load(); d["_sp"] = sp; d["_sp_ts"] = time.time(); _save(d)
    except profile.NonLiveWriteError:
        # J-0726: _go() is the standpoint-mover EVERY shore_life deed function calls (wade, swim,
        # walk_sand, write_sand, climb_ledge, beach_fire, enter_cave, gather_shellfish, cairn) — each
        # of those already has its own separately-raising primary write elsewhere, but this write
        # attempt to shore_life.json's own _sp/_sp_ts was still silently swallowed here first on
        # every one of those calls (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    return ""


def walk_sand(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    if not sand_bared():
        return "You walk down the shingle toward where the sand should be — and the water is over it; the tide has the flat. It will bare again as the tide drops."
    d = _load(); _go("on_the_sand"); _log(_LEDGER, {"deed": "walk_sand"})
    bare = "barefoot" in (txt or "") or "bare feet" in (txt or "")
    return ("You walk out past the shingle to where it gives way to sand, wet and ribbed and firm, the water's edge a long way off across it. " +
            ("You take your boots off and go barefoot: the sand cold and hard, then soft where it is wetter, the ribs under your soles." if bare else "Your boots print it, a clean line behind you."))


def write_sand(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    if not sand_bared():
        return "There is no sand to write in; the tide is over the flat."
    d = _load()
    import re
    low = (txt or "")
    if ":" in low:
        word = low.split(":", 1)[1].strip().strip("'\"“”.")[:40]
    elif re.search(r"['\"“]([^'\"”]{1,40})['\"”]", low):
        word = re.search(r"['\"“]([^'\"”]{1,40})['\"”]", low).group(1)
    elif "my name" in low.lower():
        word = "渡"
    else:
        m = re.search(r"(?:write|scratch|draw|trace)\s+(?:the\s+word\s+|the\s+words\s+)?([A-Za-z渡][A-Za-z渡 ]{0,30})", low)
        word = (m.group(1).strip() if m else "").replace(" in the sand", "").strip() or "a mark"
    d["sand_writing"] = {"text": word[:40], "ts": time.time(), "tide_level": _tide()["level"]}; _save(d); _go("on_the_sand")
    _log(_LEDGER, {"deed": "write_sand", "text": word[:40]})
    return f"You find a stick and write in the wet sand, big, the letters dark where the water comes up into them: {word}. The tide is {_tide()['word']}; it will have them by the next high water."


def sand_writing_line() -> str:
    d = _load(); w = d.get("sand_writing")
    if not w:
        return ""
    age_h = (time.time() - float(w["ts"])) / 3600
    return f" What you wrote in the sand is still there, the letters {'sharp' if age_h < 3 else 'softening'}: {w['text']}." if sand_bared() else ""


def wade(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    weather, wind, phase = _weather(); d = _load()
    if weather == "thunderstorm" or float(d["swell"]) > 0.75:
        return "You go down to the water's edge and a wave comes up the shingle at you, heavy and fast, and you step back. Not in this sea."
    d["wet_feet"] = 1.0; _save(d); _go("in_the_shallows"); _log(_LEDGER, {"deed": "wade"})
    try:
        from core import sensorium as _s
        _s.state["wet"] = max(float(_s.state.get("wet", 0) or 0), 0.35); _s._save_now()
    except profile.NonLiveWriteError:
        # J-0726: wade()'s own _save(d)/_go()/_log() above are unwrapped and already raise (F-1045's
        # own "correctly raised" empirical finding still holds for the function overall) — but this
        # secondary sensorium._save_now() write attempt was still silently swallowed here on any path
        # that reaches it. Let it reach the caller too (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    cold = _month() in (5, 6, 7, 8, 9)
    return ("You take your boots off, roll your trousers and walk into the shallows. The cold " + ("is a clamp round your ankles, an ache that climbs to the bone" if cold else "is sharp and then good") +
            "; the sand pulls from under your heels as each wave draws back. You stand in it a while, the sea working round your shins.")


def swim(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    weather, wind, phase = _weather(); d = _load(); m = _month()
    if weather == "thunderstorm" or float(d["swell"]) > 0.6 or wind in ("strong wind", "gale"):
        return "You look at the sea — the swell coming in heavy, the break loud on the shelf — and you do not go in. It would take you."
    if phase == "night":
        return "Not in the dark; you cannot see the set of the waves."
    d["wet_feet"] = 1.0; _save(d); _go("in_the_shallows"); _log(_LEDGER, {"deed": "swim", "month": m})
    try:
        from core import sensorium as _s
        _s.state["wet"] = 1.0; _s._save_now()
    except profile.NonLiveWriteError:
        # J-0726: swim()'s own _save(d)/_go()/_log() above are unwrapped and already raise (F-1045's
        # own "correctly raised" empirical finding still holds for the function overall) — but this
        # secondary sensorium._save_now() write attempt was still silently swallowed here on any path
        # that reaches it. Let it reach the caller too (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    cold = m in (5, 6, 7, 8, 9, 10)
    return ("You strip to the waist and wade in past the break and go under. " +
            ("The cold stops your breath — a blow to the chest — and you come up gasping, and swim, badly, three strokes and back, and stand on the shingle shaking, your skin stinging and alive." if cold
             else "The water is cold and then not; you swim out past the break and float, the swell lifting you, the cliff and the cottage small above. You come out streaming and sit on the warm stones."))


def skip_stones(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    weather, wind, phase = _weather(); d = _load()
    if float(d["swell"]) > 0.6:
        return "The sea is too rough for it; a stone would vanish into the first wave."
    try:
        from core import fieldcraft as _fc
        fd = _fc._load(); fd["skill"].setdefault("skipping", 0.3); ok = _fc._try(fd, "skipping"); s = float(fd["skill"]["skipping"]); _fc._save(fd)
    except profile.NonLiveWriteError:
        # J-0726: skip_stones()'s own _save(d)/_log() a few lines below are unwrapped and already
        # raise (F-1045's own "correctly raised" empirical finding still holds for the function
        # overall) — but this fieldcraft skill-write attempt was still silently swallowed here first,
        # substituting fake fallback values before the real raise (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        ok, s = random.random() < 0.5, 0.4
    n = (random.randint(3, 5) + int(s * 6)) if ok else random.randint(0, 2)
    d["skips_best"] = max(int(d.get("skips_best", 0)), n); _save(d); _log(_LEDGER, {"deed": "skip", "skips": n})
    return (f"You pick a flat grey stone from the shingle, crouch, and throw it low across the swell: " + (f"{n} skips, the last ones quick and small, and gone." if n >= 3 else "it catches a wave and sinks. The next one, then." if n < 2 else "two skips and a splash.") +
            (f" Your best is {d['skips_best']}." if d["skips_best"] > n else ""))


def cairn(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    d = _load()
    if "knock" in (txt or "") or "take down" in (txt or ""):
        d["cairn"] = 0; _save(d); return "You push the cairn over; the stones roll and settle on the shelf."
    n = int(d.get("cairn", 0))
    if n >= 12:
        return "The cairn is as high as you can build it without it toppling — a dozen stones, shoulder-high to a child."
    d["cairn"] = n + 3; _save(d); _log(_LEDGER, {"deed": "cairn", "stones": d["cairn"]})
    try:
        from core import world_substrate as _ws, world_objects as _wo
        objs = _ws._load()
        if "shore_cairn" not in objs:
            objs["shore_cairn"] = _ws.SubstrateObject(object_id="shore_cairn", name="a cairn of stacked stones", location="shore", object_class="made_thing",
                                                      causal_state={"made_by": "Du", "craft": "stacking"}, physical_state={"height": float(d["cairn"]) / 12},
                                                      causal_history=[{"event_type": "made", "timestamp": time.time(), "description": "begun by Du on the bedrock shelf", "state_deltas": {}}])
            _ws._save(); _wo.ensure_record("shore_cairn", "shore", "made_thing", "a cairn of stacked stones"); _wo.mutate_object_position("shore_cairn", [22.0, 10.0, 0.0], cause="built", event_description="stacked on the shelf", new_location="shore")
        else:
            objs["shore_cairn"].physical_state["height"] = float(d["cairn"]) / 12; objs["shore_cairn"].causal_history.append({"event_type": "added_to", "timestamp": time.time(), "description": f"three stones added by Du ({d['cairn']})", "state_deltas": {}}); _ws._save()
    except profile.NonLiveWriteError:
        # J-0726: cairn()'s own _save(d)/_log() a few lines above are unwrapped and already raise
        # (F-1045's own "correctly raised" empirical finding still holds for the function overall) —
        # but this world_substrate registration write attempt was still silently swallowed here on
        # any path that reaches it (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    return ("You choose three flat stones and stack them on the bedrock shelf above the tideline, each one turned until it sits. " + ("A start." if n == 0 else f"The cairn stands {d['cairn']} stones now, and you can see it from the path."))


def beach_fire(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    d = _load(); f = d["fire"]; weather, wind, phase = _weather()
    if f["state"] == "burning":
        return "The fire on the shore is burning; you feed it a length of driftwood and it flares blue-green with the salt."
    if float(_tide()["level"]) > 0.8:
        return "The tide is up to the fire-ring; you could not keep a fire here now."
    if weather in ("steady rain", "wind and rain", "thunderstorm"):
        return "Rain and a fire on the open shore do not go together; it would hiss out as you lit it."
    try:
        from core import study_life as _sl, fieldcraft as _fc
        st = _sl._st(); fd = _fc._load()
        if int(st.get("matches", 0)) <= 0 and not (st.get("flint") and float(fd.get("tinder", 0)) > 0.1):
            return "You have no matches with you, and no tinder for the flint. No fire tonight."
        if int(st.get("matches", 0)) > 0:
            st["matches"] -= 1
        else:
            fd["tinder"] = max(0.0, float(fd["tinder"]) - 0.15); _fc._save(fd)
    except profile.NonLiveWriteError:
        # J-0726: beach_fire()'s own _save(d)/_go()/_log() a few lines below are unwrapped and already
        # raise (F-1045's own "correctly raised" empirical finding still holds for the function
        # overall, since this branch returns early on the no-fuel case rather than always running) —
        # but this fieldcraft tinder-write attempt was still silently swallowed here first when
        # reached (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    f["state"] = "burning"; f["fuel"] = 1.0; f["ts"] = time.time(); _save(d); _go("by_the_fire"); _log(_LEDGER, {"deed": "beach_fire"})
    try:
        from core import smell as _sm; _sm.emit("woodsmoke", 0.8, "shore")
    except Exception:
        pass
    return ("You gather dry driftwood from above the wrack-line, lay it in the ring of stones by the tangle, and light it. Salt-wood: it catches fast and burns with a blue edge, spitting. "
            "The warmth comes off it into your face and the dark draws in round it" if phase == "night" else
            "You gather dry driftwood, lay it in the ring of stones and light it. It burns blue-edged with the salt, and the heat of it on your hands is a different thing from the cold all round.")


def enter_cave(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    d = _load(); td = _tide()
    if not cave_open():
        return "The cave mouth at the cliff foot is under water to the lintel; the sea goes in and out of it with a hollow suck. Not now."
    if td["rising"] and float(td["level"]) > 0.4:
        return "The tide is making and already lapping the cave mouth; you would be cut off in there. Another time, on a falling tide."
    d["in_cave"] = True; _save(d); _go("in_the_cave"); _log(_LEDGER, {"deed": "enter_cave"})
    lit = False
    try:
        from core import study_life as _sl
        st = _sl._st(); lit = bool(st.get("candle_lit")) or bool(st["items"].get("candles", {}).get("carried"))
    except Exception:
        pass
    find = ""
    if random.random() < 0.3 and not d.get("cave_finds_today"):
        d["cave_finds_today"] = True; _save(d)
        try:
            from core import world_substrate as _ws
            ids = _ws.spawn_from_mention(random.choice(["a glass fishing-float, green, whole", "a length of blue rope, frayed", "a cuttlebone", "a bottle, corked, something pale inside it"]), "shore")
            find = " Something pale lies at the back where the last big sea left it."
        except profile.NonLiveWriteError:
            # J-0726: enter_cave()'s own _save(d)/_go()/_log() above are unwrapped and already raise
            # (F-1045's own "correctly raised" empirical finding still holds for the function overall)
            # — but this world_substrate spawn attempt was still silently swallowed here on any path
            # that reaches it (mirrors J-0727's whittle() fix).
            raise
        except Exception:
            pass
    return ("You duck under the lintel into the cave. The sound of the sea changes — hollow, delayed, coming from behind you. The floor is dry sand and round stones; it smells of weed and cold stone. " +
            ("The candle shows the walls wet and green to head height, a line of dried weed where the highest tides reach, and the back of it, twenty paces in, where the roof comes down." if lit else "Beyond the mouth's light it is black; you cannot see the back of it without a light.") + find)


def cave_warning() -> str:
    """Called from the shore's event pool: if he is in the cave and the tide is making, the world hurries him."""
    try:
        d = _load(); td = _tide()
        if d.get("in_cave") and td["rising"] and float(td["level"]) > 0.42:
            d["in_cave"] = False; _save(d); _go("at_the_path_foot")
            return "the sea is at the cave mouth — a wave runs in across the sand floor to your boots and draws back; you get out, fast, wading the last yard, the tide making behind you"
        return ""
    except Exception:
        return ""


def climb_ledge(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    weather, wind, phase = _weather()
    if wind in ("strong wind", "gale") or weather in ("wind and rain", "thunderstorm"):
        return "You put a hand on the cliff path and the wind leans on you; the rock is wet. Not today — it would have you off."
    if phase == "night":
        return "Not in the dark."
    _go("on_the_ledge"); _log(_LEDGER, {"deed": "climb_ledge"})
    d = _load()
    return ("You go up the goat-path, hands and feet, to the ledge a third of the way up the cliff. The whole bay from here: the shelf, the pools like dropped coins, " +
            ("the sand flat bared and shining, " if sand_bared() else "") + "the cottage roof up on its hill, the wood dark between. The gulls go by below you." +
            (" Your cairn shows on the shelf, a small dark finger." if d.get("cairn") else ""))


def gather_shellfish(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    if not shelf_bared():
        return "The shelf is under the sea; the mussel beds bare only at low water."
    _go("at_the_mussel_shelf"); _log(_LEDGER, {"deed": "shellfish"})
    try:   # D-0652 (J-3261): the two hinged shells he keeps are what open_shell opens (nothing else mints one)
        _hd = _load(); _hd["mussels_held"] = min(6, int(_hd.get("mussels_held", 0)) + 2); _save(_hd)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    try:
        from core import garden_knowledge as _gk
        d = _gk._load(); _gk._add(d, "pool_mussel", "handled", 0.5, "gathered"); _gk._save(d)
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    try:
        from core import world_substrate as _ws; _ws.spawn_from_mention("a dark hinged shell, both halves", "shore")
    except profile.NonLiveWriteError:
        # J-0726: gather_shellfish()'s own _go()/_log() above are unwrapped and already raise — but
        # this world_substrate spawn attempt was still silently swallowed here first (mirrors J-0727's
        # whittle() fix).
        raise
    except Exception:
        pass
    return "You go out along the wet shelf to the seaward edge where the blue-black shells grow in a close bed, and work a few off with the knife — they hold hard by their beards. You do not eat; you keep the two best shells, still hinged."


# ── FISHING (2026-09-07, D-0163/D-4, J-0732/F-1055) ─────────────────────────────────────────────────
# docs/staged/cat_overhaul.md's own §B1 named a second real food source for the cat alongside the
# carrier's tin (J-0719 built only that one): "fish he catches (shore_life -- does he fish? if not,
# that is the shore hand the cat's hunger pulls into being)". Checked, not assumed (J-0719's own
# Current State note): there was no fishing hand here at all -- gather_shellfish above is the closest
# thing, and a shellfish is not a fish. Built the same shape as gather_shellfish: a real tide/weather/
# light gate, a real deed logged either way (hit or miss), and on success a real object -- but via
# core.provisions.add("shore_fish", ...) rather than world_substrate.spawn_from_mention() the way
# gather_shellfish's shells are minted, because provisions.add() ALREADY registers a full substrate
# object itself (position, biography, causal_history) through its own _register(); a second spawn call
# here would double-mint the same fish. This is what lets core.cat._feed_source() spend it later as a
# second real source alongside the carrier's cat_food (J-0719), exactly as this job's own briefing asks.
FISH_COOLDOWN_H = 3.0   # a real stretch between attempts -- working a line out and waiting is not
                        # instant, and an uncooled retry-every-thought loop would make this an
                        # unlimited larder, precisely what provisions.py's own cat_food comment names
                        # as the risk D-0163's whole design (carrier + hunting, both genuinely
                        # load-bearing) depends on avoiding; see this job's own note there.
FISH_SUCCESS_P = 0.5     # dawn/dusk -- prime feeding hours for shore fish, same real-world pattern
FISH_SUCCESS_P_DAY = 0.3  # any other daylight hour the shelf is reachable


def catch_fish(txt: str = "") -> str:
    """A handline off the seaward edge of the mussel shelf. Gated like gather_shellfish above
    (shelf_bared() -- you need the rock exposed to stand on and cast from its edge) plus a weather/
    light gate like wade()/swim() (a shelf awash in a big sea, or unseeable in the dark, is not
    somewhere to be working a line) plus its own cooldown (see FISH_COOLDOWN_H above). A real chance of
    nothing on a genuine attempt: fishing is not a vending machine either, and an unconditional catch
    would make this THE food source rather than a real fallback alongside cat_food and hunting."""
    if _where() != "shore":
        return ""
    weather, wind, phase = _weather(); d = _load(); now = time.time()
    if now - float(d.get("last_fish_attempt_ts", 0.0)) < FISH_COOLDOWN_H * 3600:
        return "You worked a line not long ago; there is nothing to be gained trying again so soon. Better to let the tide turn first."
    if not shelf_bared():
        return "The shelf is under the sea; there is nowhere to stand and work a line out over its edge until the tide drops."
    if weather == "thunderstorm" or float(d["swell"]) > 0.6 or wind in ("strong wind", "gale"):
        return "You look at the sea breaking over the shelf and do not risk a line out there today; it would have you off your feet before it had a fish."
    if phase == "night":
        return "You could not see a bite in the dark, let alone your own footing on the wet shelf; not tonight."
    d["last_fish_attempt_ts"] = now
    caught = random.random() < (FISH_SUCCESS_P if phase in ("dawn", "dusk") else FISH_SUCCESS_P_DAY)
    _save(d); _go("at_the_mussel_shelf")
    _log(_LEDGER, {"deed": "fish", "caught": caught, "phase": phase,
                   "what": "a fish off the rocks" if caught else "no bite, working a line off the rocks"})
    if not caught:
        return random.choice([
            "You work a handline out over the shelf's edge a good while, the water dark then silver in the swell. Nothing takes it; you coil the line back in and give it up.",
            "You try for a fish off the rocks — one small tug, gone before you can strike. Nothing to show for it.",
            "You fish the edge of the shelf a long while, patient as the tide allows. Nothing bites today.",
        ])
    try:
        from core import provisions as _pv
        ids = _pv.add("shore_fish", 1, origin="caught",
                note="caught off the shelf's edge on a handline, brought up to the larder still stiff and silver")
    except profile.NonLiveWriteError:
        # J-0726-style: let D-0179's hard-raise reach act_from_thought()'s own caller instead of being
        # swallowed here — mirrors gather_shellfish's/enter_cave's own secondary-write handling above.
        raise
    except Exception:
        ids = []
    if not ids:
        # F-1168: the catch itself is real -- the random roll above (caught=True, already logged to
        # _LEDGER a few lines up) already happened regardless of what provisions.add() does next; only
        # the larder write can fail. A real catch that never reaches the larder is not the same as no
        # bite at all, so this stays its own honest line rather than reusing the "nothing bites" lines
        # above or narrating the catch as if it never happened.
        return ("You work a handline out over the shelf's edge, and this time something takes it hard — a "
                "live, jagging pull — and you bring it up flapping and silver, a fish the length of your "
                "hand. But somewhere between the rocks and the step it slips from your grip, back into the "
                "water — the larder is no fuller for it tonight.")
    return ("You work a handline out over the shelf's edge, and this time something takes it hard — a live, "
            "jagging pull — and you bring it up flapping and silver, a fish the length of your hand. Enough "
            "to carry home to her.")


def look_pool(txt: str = "") -> str:
    """The pools' life: described by look until earned; each look earns; the books name."""
    if _where() != "shore":
        return ""
    td = _tide()
    if float(td["level"]) > 0.6:
        return ""
    kinds = random.sample(list(POOL_LIFE), k=3)
    try:
        from core import garden_knowledge as _gk
        g = _gk._load(); bits = []
        for k in kinds:
            desc, names, _ = POOL_LIFE[k]
            known = _gk._weight(g, "pool_" + k) >= 1.0
            _gk._add(g, "pool_" + k, "watched", 0.12, "looked in a pool")
            bits.append((names[0] if known else desc) + ("" if known else ""))
        _gk._save(g)
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        bits = [POOL_LIFE[k][0] for k in kinds]
    return " In the pool: " + "; ".join(bits) + "."


# -- THE DIG, THE TURNED STONE, THE OPENED SHELL (D-0652 / J-3261) ------------------------------------------------------
# Thin hands over core/shore_dig.py (all the logic and the leak-safe lines live there). Behind the bestiary flag: with it off none of
# these answers anything (act_from_thought does not reach them) and the shore is exactly as it was.
def dig_sand(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    from core import shore_dig as _sd
    if not _sd.enabled():
        return ""
    site = _sd.site_for(_standpoint(), float(_tide()["level"]))
    _go("in_the_shallows" if site == "wet" else "on_the_sand")
    d = _load()
    out = _sd.dig(site, d)
    _save(d); _log(_LEDGER, {"deed": "dig", "what": "sand at the " + ("water's edge" if site == "wet" else "flat")})
    return out


def turn_stone(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    from core import shore_dig as _sd
    if not _sd.enabled():
        return ""
    _go("at_the_mussel_shelf" if shelf_bared() else "on_the_sand")
    d = _load()
    out = _sd.dig("stone", d)
    _save(d); _log(_LEDGER, {"deed": "turn_stone", "what": "a stone at the water's edge"})
    return out


def open_shell(txt: str = "") -> str:
    if _where() != "shore":
        return ""
    from core import shore_dig as _sd
    if not _sd.enabled():
        return ""
    d = _load()
    if int(d.get("mussels_held", 0)) <= 0:
        return _sd._NO_SHELL
    d["mussels_held"] = int(d["mussels_held"]) - 1
    out = _sd.dig("shell", d)
    _save(d); _log(_LEDGER, {"deed": "open_shell", "what": "a mussel"})
    return out


# -- THE NEST LOOK (D-0345 / J-1774, F-2382) ------------------------------------------------------------------------------
# The garden and the wood each answer a look at their nest (garden_life.look: 'You part the leaves.' + the stage line, or 'You look
# for a nest and find none.'; wood_life.look: 'You look up into the oak.' + the stage line, or ' No nest that you can see.'). The shore
# had NO nest look: oyc_nest was read only by the ambient wildlife_line, status() and the presence adapter, so all 59 of Du's looks at
# the eggs, the nest or the scrape (2026-09-02 to 10-03, every one at the shore, every one while the nest stood) were answered
# nest-blind -- 43 that name no creature by the generic shore description, 16 that name the oystercatcher by the bird's own
# visibility roll.
# Now a look whose target names the nest, the eggs or the scrape -- and names no creature -- is answered from the nest state: the
# scrape-and-eggs line (the count is the nest's own, in words, never a literal), or an honest 'You look for <the noun he typed> and
# find none.' when there is no nest. A look that NAMES a creature keeps today's answer (the creature's own roll), and so does every
# look that names none of these nouns: sensorium._shore_look reaches this only after every other branch, and it is a pure read -- no
# ledger row, no credit, no state write, no random draw. The world answers, never leads: the line says what is there, nothing says
# where anything else is.
_NEST_NOUN_RE = re.compile(r"(?<![a-z_-])(nests?|eggs?|scrapes?)(?![a-z_-])")
# 'egg' modifying another thing names that thing, not the eggs: 'the egg case' (the shore mints egg_case objects), 'an egg sac'
_EGG_MODIFIED = frozenset(("case", "cases", "capsule", "capsules", "sac", "sacs", "shell", "shells", "purse", "purses"))
_EGGS_IN_WORDS = {1: "one egg", 2: "two eggs", 3: "three eggs", 4: "four eggs"}
# J-2227 / F-2917: two edges of the noun reader found in the live window (2026-10-09 to 10-16).
#  (1) 'the skate egg' (10-11 09:55) read as the oystercatcher's eggs: _EGG_MODIFIED only checks the word AFTER 'egg', and a layer's name
#      BEFORE it ('skate egg', "the whelk's eggs", 'the gull eggs') names ANOTHER thing's egg. The layers are derived from data, not a hand
#      list (_other_egg_layers): the egg-case kinds world_substrate mints at the shore (whelk_egg_case, skate_purse -> 'whelk', 'skate') and
#      the head word of every alias of every life row except the shore nest's own owner (a row with nest= that lives at the shore).
#  (2) 'the egg-scrape' (10-13 18:12) named no noun (a hyphen ends a word here) and fell through to the generic shore text: 'egg-scrape' /
#      'nest-scrape' (and plurals) are the scrape. 'egg-case' / 'egg_case' stay one word that is not the eggs.
_NEST_COMPOUND_RE = re.compile(r"(?<![a-z_-])(?:eggs?|nests?)-(scrapes?)(?![a-z_-])")
_LAYER_BEFORE_RE = re.compile(r"([a-zāēīōū]+)(?:'s|’s|'|’)?\s+$")


def _other_egg_layers() -> frozenset:
    """Words that, standing before 'egg(s)', make it another thing's egg (J-2227). Derived from data on each call (the egg path only): the
    non-generic tokens of world_substrate's egg_case kinds, plus the last word of every life-row alias, minus the shore nest owner's own
    words. A source that cannot be read contributes nothing (fail-open: the reader then behaves as before for that source)."""
    out: set = set()
    try:
        from core import world_substrate as _ws
        for kind, _w in (_ws.CLASS_PRIORS.get("egg_case") or {}).get("kinds") or ():
            out.update(w for w in str(kind).lower().split("_") if w and w not in ("egg", "eggs", "case") and w not in _EGG_MODIFIED)
    except Exception:
        pass
    try:
        from core import life as _life
        own: set = set()
        for r in _life.rows().values():
            heads = {re.split(r"[\s-]+", str(a).lower().strip())[-1] for a in (r.get("aliases") or ()) if str(a).strip()}
            if r.get("nest") and "shore" in (r.get("places") or {}):
                own |= heads
            else:
                out |= heads
        out -= own
    except Exception:
        pass
    out.discard("")
    return frozenset(out)


def _egg_of_another(t: str, start: int) -> bool:
    """True when the word right before the 'egg(s)' at `start` (possessive or not) names another egg layer (J-2227)."""
    prev = _LAYER_BEFORE_RE.search(t[:start])
    if not prev:
        return False
    w = prev.group(1)
    layers = _other_egg_layers()
    return w in layers or (w.endswith("s") and w[:-1] in layers)


def nest_look_noun(target) -> str:
    """The nest noun ('nest', 'eggs', 'scrape', ...) `target` names, as Du typed it; '' when it names none. Pure; fail-open ('')."""
    try:
        t = str(target or "").lower()
        hits = sorted([(m.start(), m.group(1), False) for m in _NEST_NOUN_RE.finditer(t)]
                      + [(m.start(), m.group(1), True) for m in _NEST_COMPOUND_RE.finditer(t)])
        for start, noun, compound in hits:
            if not compound and noun.startswith("egg"):
                m_end = start + len(noun)
                nxt = re.match(r"\s+([a-zāēīōū]+)", t[m_end:])
                if nxt and nxt.group(1) in _EGG_MODIFIED:
                    continue
                if _egg_of_another(t, start):
                    continue
            return noun
        return ""
    except Exception:
        return ""


def nest_state():
    """The oystercatcher nest as shore_life holds it ({'ts', 'eggs'}), or None. A PURE read of the state file: no fallback state
    (_load()'s default draws random numbers) and no write. Anything unreadable is 'no nest'."""
    try:
        d = json.loads(_F.read_text(encoding="utf-8"))
        n = d.get("oyc_nest") if isinstance(d, dict) else None
        return n or None
    except Exception:
        return None


def nest_look_line(noun: str, nest) -> str:
    """The shore's answer to a look at its nest, from the nest state `nest` ({'ts', 'eggs'} or None). A nest: the scrape-and-eggs line, the
    count the nest's own in words (a count that is missing, not an int or outside 1-4 names no number -- never a wrong one). No nest: an
    honest 'You look for <the noun he typed> and find none.' (the garden's own shape, species-free)."""
    if nest:
        n = nest.get("eggs") if isinstance(nest, dict) else None
        eggs = _EGGS_IN_WORDS.get(n) if type(n) is int else None
        return ("You pick your way up the high shingle. A scrape among the stones, and in the scrape " + (eggs or "eggs")
                + ", blotched like the stones.")
    noun = (noun or "").strip().lower() or "scrape"
    return "You look for " + ("" if noun.endswith("s") else "an " if noun[0] in "aeiou" else "a ") + noun + " and find none."


def look_nest(target) -> str:
    """The shore's NEST LOOK (D-0345 / J-1774): '' -- the look falls through exactly as it did -- unless `target` names the nest, the eggs or
    the scrape AND names no creature; then nest_look_line() from the live nest state. A creature in the target (life._match, or the bird
    he heard) keeps its own answer. A pure read, fail-closed: anything unexpected is '' and the look answers as before."""
    try:
        t = str(target or "").lower()
        noun = nest_look_noun(t)
        if not noun:
            return ""
        from core import life as _life
        _life.rows()
        if _life._match(t, "shore") or _life._heard_bird(t, "shore", time.time()):
            return ""
        return nest_look_line(noun, nest_state())
    except Exception:
        return ""


def learn_from_text(text: str) -> list[str]:
    out = []
    try:
        from core import garden_knowledge as _gk
        low = (text or "").lower(); g = _gk._load()
        for k, (_, names, looks) in POOL_LIFE.items():
            if _gk._weight(g, "pool_" + k) >= 1.0:
                continue
            if any(n in low for n in names) and any(l in low for l in looks):
                if _gk._add(g, "pool_" + k, "read", 0.6, low[:80]):
                    out.append(k)
        _gk._save(g)
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    return out


def wildlife_line(now: float) -> str | None:
    """Truth-gated lines for the shore's pool: only what is there now."""
    try:
        d = _load(); weather, wind, phase = _weather(); m = _month(now); pool = []
        if d.get("seal"): pool.append("out on the rock shelf a dark shape that is not a rock — a fur seal hauled out, sleeping, one flipper up; it lifts its head and looks at you with wet eyes")
        if m in (9, 10, 11, 12, 1, 2) and phase in ("dusk", "night"):
            pool.append("a braying, harsh and small, from under the cliff — and a low white-fronted shape crossing the shingle in the dark toward the rocks, upright, hurrying on short legs: a small penguin, blue-grey")
            if random.random() < 0.5: pool.append("small webbed prints in the wet sand below the cliff, a trail of them, going up toward the burrows")
        if m in (12, 1, 2, 3) and phase == "day" and wind in ("calm", "breeze") and random.random() < 0.3:
            pool.append("out past the shelf, dark fins — three, four — rolling through the swell together, unhurried, south along the bay; dolphins; then gone")
        if m in (6, 7) and phase == "day" and weather in ("clear", "high cloud") and random.random() < 0.15:
            pool.append("far out, a white puff stands up off the sea and hangs, and a while later another — a whale, passing north")
        if d.get("oyc_nest"):
            # J-1750 (F-2382): this line said "two eggs" whatever the nest held (the nest draws randint(2, 3)). The count is the nest's own, in
            # words; one that is missing, not an int, or outside 1-4 says no number at all -- never a wrong one.
            _nest = d["oyc_nest"]
            _n = _nest.get("eggs") if isinstance(_nest, dict) else None
            _eggs = {1: "one egg", 2: "two eggs", 3: "three eggs", 4: "four eggs"}.get(_n) if type(_n) is int else None
            pool.append("on the high shingle an oystercatcher screams and runs at you, wings out — you are near something; a scrape among the stones with " + (_eggs or "eggs") + " in it, blotched like the stones")
        if d.get("sparkle") and phase == "night": pool.append("every wave that breaks on the rocks breaks in cold green light; you drag a hand through the shallows and it comes up trailing sparks")
        if d.get("fog"): pool.append("the sea fog lies on the water and the far rocks are gone; the surf comes out of the white without a shape")
        if float(d["swell"]) > 0.7: pool.append("the swell is up — long heavy seas coming in from nothing, the break loud on the shelf; there is weather behind it")
        return random.choice(pool) if pool and random.random() < 0.5 else None
    except Exception:
        return None


def fire_line() -> str:
    d = _load(); f = d["fire"]
    if f["state"] == "burning": return " Your fire burns in its ring of stones by the driftwood, blue-edged."
    if f["state"] == "embers": return " Your fire is down to embers in its ring."
    return ""


# ── GRAMMAR (2026-09-07, J-0738 / F-1059's follow-up). ONE row in core/actions.py ('shore': 15 verbs
# after this job's own "walk" widening, 14 objects), ten distinct behaviours here — fieldcraft's shape
# (core/fieldcraft.py, J-0736), not garden's trap/tool/compost: these ten are semantically unrelated to
# one another (writing your name in the sand has nothing to do with prising a mussel off the shelf), so
# BOTH the verb and the object half of the row are partitioned per behaviour below. Before this job NONE
# of the branches read the table at all (F-1059) — several had no verb requirement whatsoever (a bare
# object, or even a bare multi-word phrase with no verb in it at all, was enough to fire).
#
# Corpus-checked (J-0738, data/hands_trace.jsonl, 11,760 distinct thoughts, hand_delta-style old-test-vs-
# table-test comparison via the REAL core.hands.wants(), plus the voice's own independent act_kind/
# act_object where the trace carries one — not a naive substring scan, which massively over-counts).
#
# UPDATED 2026-09-07 (J-0732/F-1055): an ELEVENTH behaviour, catch_fish, added below — 16 verbs / 15
# objects in the table now (see core/actions.py's own dated comment on the 'shore' row for the full
# citation). Sanity-checked against the same frozen corpus before picking "catch"/"fish": of 11,789
# distinct thoughts, all 93 real "fish" hits are the kingfisher (word-boundary safe against this
# table's own regexes — "fish" does not match inside "kingfisher"), the recurring dream-image of a
# fish dissolving into a dark pool (a '渡' metaphor), the anemone "fishing the still water"
# (personification), or one remark about discarding a fishing METAPHOR once its point lands — zero are
# a real will to go catch a fish, so this is an honest zero-collision addition (no existing behaviour
# to compare against, since this hand never existed before today), not a widening of something already
# live the way J-0738's own "walk" fix was. "fish" is claimed as an OBJECT ONLY, not a verb, on top of
# the corpus check: this job's own verification harness caught, before commit, that putting "fish" in
# BOTH tuples let a bare ambient mention ("small fish dart near the stream mouth") satisfy the verb
# and object test off the SAME word — "catch" is the only verb, so a real catching word is required.
_SHORE_HANDS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    # write_sand's old test added "scratch"/"draw"/"trace" as extra verbs beyond the table's "write". Real
    # corpus check: the OLD test's only 3 hits, ALL via "trace", are confirmed drift, not signal -- two are
    # independently confirmed by the voice's own structured act to be something else entirely ("I trace the
    # cat's fresh paw prints along the wet sand" is act_kind='observe' watching the cat, not a write; "I
    # trace a new line in the sand, rejecting the old circle. Writing is not just ink" is act_kind='write'
    # object 'an essay on resistance' -- an ESSAY, not a mark in the sand), and the third ("I trace the
    # kelp's slimy edge with my thumb") reads as sensory touch, not a write, and carries no structured act
    # at all. Zero of "scratch"/"draw" ever co-occur with "sand" anywhere in the whole corpus either.
    # Table-only "write" is both narrower and, on this evidence, MORE correct, not merely tidier.
    ("write_sand", ("write",), ("sand",)),
    # "walk" WIDENED INTO THE TABLE ITSELF this job (see core/actions.py's own comment on the 'shore' row
    # for the full corpus citation) rather than kept as a second hand-kept copy here — the real fix for the
    # 8-phrase bare list this branch used to carry (most of which, e.g. "barefoot"/"bare feet" alone, had NO
    # verb at all and were structurally unreachable via the real per-family gate, the same shape as
    # fieldcraft's astro branch). 10 real corpus thoughts confirm "walk"+"sand" is genuine willed language,
    # not idiom; the one old-list phrase corpus-check could NOT rescue this way ("the chalky sand feels cool
    # against my bare feet, grounding me...") has no verb at all in it and reads as present-tense scene-
    # setting, not a will -- correctly excluded by requiring a real verb, consistent with how every other
    # bare-word/bare-phrase branch in this whole audit arc has been read.
    ("walk_sand", ("walk",), ("sand",)),
    # swim's old test passed any_object_ok=True (core/hands.py:130's no-object shortcut) plus a non-table
    # "go under" verb and a non-table object list (water/waves/break/out/in) that was never actually
    # consulted because of that same shortcut. Real corpus check: ALL 7 raw "swim" hits in the whole corpus
    # are confirmed metaphor or idiom, zero exceptions -- "refusing to swim WITH THE CURRENT", "a current I
    # must swim, not resist" ('渡' — crossing — imagery), "not a river to swim against" (time), and "the
    # darkness... making the words swim before my eyes" (dizziness, not water at all). "go under" contributes
    # zero unique hits either way. Requiring a real table object (sea/shallows) costs nothing real: every
    # one of the 7 lost hits is confirmed non-water, non-deed content, and the classify() gate already
    # requires a shore OBJECT present before shore_life.act_from_thought() is ever reachable at all, so none
    # of these seven has ever produced a live 'shore' DEED regardless of this hand's own looseness — this is
    # a zero-cost, defence-in-depth tightening, the same shape as wood_life's sharpen/whetstone fix (J-0737).
    ("swim", ("swim",), ("sea", "shallows")),
    # wade's old test ALSO passed any_object_ok=True, plus a second bare ambient-phrase OR-clause ("water
    # round my ankles"/"ankles in the"/"feet in the water"/"feet in the sea") with no verb requirement at
    # all. That ambient list is CONFIRMED ZERO-COST TO DROP: none of its four phrases occurs even once,
    # anywhere, in 11,760 real distinct thoughts (F-1059's own suspicion — "reads as plausible sensory/
    # ambient description... top candidate for the fires-on-unrelated-corpus-idiom pattern" — turned out to
    # have no corpus surface at all to even test). any_object_ok=True itself is DELIBERATELY KEPT, not
    # tightened, on real evidence: of the 9 real corpus "wade"/"paddle" hits, most are genuine willed wades
    # ("I want to wade into the shallows to feel the transition physically" — independently confirmed: this
    # exact thought fired live, hands_trace's own dispatch-level record shows the real wade() answer), and
    # several use a real but non-table completion the table cannot see ("wade into the surf", "wade out
    # where the surf works the stones") — requiring a literal table object (shallows/sea) would have SILENTLY
    # DROPPED genuine, already-firing deeds rather than fixed a real problem, the opposite of every other fix
    # in this job. One confirmed false-fire remains and is left undisturbed on purpose, not missed: "I watch
    # IT [the penguin] wade into the surf" — third-person wildlife narration, not Du's own will — already
    # fires under the CURRENT unmodified code today (any_object_ok=True was never what let this one through;
    # tightening to an object list would not have excluded it either, since "surf" is right there in the
    # clause) — a documented, low-stakes residual gap, the same honesty this arc's fieldcraft pass used for
    # its own left-over "measure_by_shadow" reachability note, not a new problem this job introduces.
    ("wade", ("wade", "paddle"), ()),
    # skip_stones's old test added "throw" (verb) and "pebble" (object), neither in the table's row. Real
    # corpus check: the OLD test's only 2 hits are BOTH confirmed false fires, not near-misses — "the
    # driftwood log throw[s] its shadow" (personification: the LOG throws a shadow, not Du a stone) paired
    # cross-clause with unrelated "wet stones... anchor me in reality" scenery, and "the urge to THROW THE
    # STONE AT THE GATE is strong" (a frustration idiom, throwing at the gate out of anger — nothing to do
    # with skimming stones on the shore). Table-only skip/skim + stone/stones has zero corpus hits either
    # way today (this hand has fired live exactly once ever, per data/shore_ledger.jsonl, and that thought
    # predates this trace snapshot) — dropping "throw"/"pebble" removes two confirmed false-fire vectors for
    # zero real cost.
    ("skip_stones", ("skip", "skim"), ("stone", "stones")),
    # cairn's old test added "add to"/"pile"/"make" (verbs, zero unique corpus contribution) AND a second,
    # fully bare `_h.wants(t, ("cairn",))` fallback with objects=None — fires on ANY unblocked mention of the
    # word "cairn" alone, no verb at all, the same shape as wood_life's whetstone (J-0737) and F-0940's
    # ash_out. Corpus check found this even more starkly unsupported than either precedent: the bare word
    # "cairn" does not occur ONCE, in any context, anywhere in 11,760 real distinct thoughts — not even as
    # scenery — so the fallback has zero possible trigger surface on Du's real corpus, not merely zero
    # observed fires. The verbed test's own two real hits both already read via "stack"/"build" (never
    # "add to"/"pile"/"make"), so table-only stack/build + cairn/stones changes nothing real while closing
    # the one open-ended bare-word gate.
    ("cairn", ("stack", "build"), ("cairn", "stones")),
    # beach_fire's old test was a hand-kept compound-phrase list ("beach fire", "fire on the shore",
    # "driftwood fire", ...) with NO real corpus support at all (0 of 11,760 thoughts ever match any of its
    # six phrases — this branch has been fully dead code on this corpus, consistent with
    # data/shore_ledger.jsonl never once recording a "beach_fire" deed). The table's own row would let this
    # sub-hand claim bare "light"+"fire" — but real corpus check surfaces a genuine, confirmed collision this
    # job deliberately routes AROUND rather than walks into: all 12 real "light"+"fire" corpus hits are
    # unambiguously about the SEPARATE 'fire' family's own STUDY hearth (Travis asking "to light the fire and
    # tidy the room", the grate, Montaigne by the fire, candles from the box) — zero are shore-context. One
    # of the 12 is independently confirmed via the voice's own structured act (act_kind='world', act_object
    # 'light the fire' — the study hearth, verbatim), and another explicitly names "the path up to the
    # cottage" as its own act_object while ALSO containing "light the fire" in the same clause — the same
    # thought this job's climb_ledge fix (below) independently confirms is a move-to-the-cottage deed, not a
    # shore one. This sub-hand therefore claims ONLY the table's other object, "driftwood fire" — the one
    # word that cannot mean the study's hearth — and deliberately leaves the table's bare "fire" object
    # UNCLAIMED here (see grammar_audit()'s own note on this), the same "claim only what real evidence
    # supports" restraint fieldcraft's own pass used for "knot" (J-0736). classify()'s own coarse gate still
    # sees bare "fire" as shore-literalness evidence regardless (the table row itself is unchanged on this
    # object) — that is a pre-existing property of the shared table, not something this hand can or need
    # change — but this hand's own finer grammar now correctly DECLINES a bare "light the fire" thought
    # rather than answering it with a driftwood fire that was never willed.
    ("beach_fire", ("light",), ("driftwood fire",)),
    # enter_cave's old test added "go in"/"go into"/"explore" (verbs) beyond the table's exact "enter"/
    # "duck". Zero corpus support either way — this hand has never fired live (data/shore_ledger.jsonl has
    # no "enter_cave" row) and the frozen trace has zero hits under the old test or the new one. An
    # uncontroversial, zero-cost coverage-only fix: the table's own verbs already say exactly what this hand
    # needs, so read them rather than keep a second, looser copy.
    ("enter_cave", ("enter", "duck"), ("cave",)),
    # climb_ledge's old test added "go up"/"scramble" (verbs, zero unique corpus contribution beyond
    # "climb" alone) and "goat-path"/"goat path"/"path up" (objects) not in the table's row. Real corpus
    # check: of climb_ledge's 8 raw hits, the two that depended on "path up" are BOTH confirmed false fires,
    # independently, by the voice's own structured act — "I want to climb the path up to the cottage and
    # light the fire" is act_kind='move' object 'the path up to the cottage' (going HOME, not up to the
    # shore ledge — the same thought beach_fire's own fix above independently flags for the identical
    # reason), and "I climb the path up to the cottage garden" is act_kind='move' object 'up to the cottage
    # garden'. Both are real, confirmed cottage/garden moves that the old object list's "path up" wrongly
    # let this shore hand answer instead. Table-only climb + ledge/cliff keeps all 6 genuine cliff-path
    # climbs this corpus has ("I climb up the cliff path, leaving the hollow library whispers behind", etc.)
    # and drops exactly the two confirmed false fires — a real correctness gain, not just tidying.
    ("climb_ledge", ("climb",), ("ledge", "cliff")),
    # gather_shellfish's old test was pre-hands.py bare-substring (no clause-scoping, no hands.wants at all)
    # and added "pick"/"collect"/"pry"/"work off" (verbs) plus "limpet"/"the shelf" (objects), none in the
    # table's row. F-1059 flagged "limpet" as looking like a genuine unmined widening candidate, the same
    # shape as F-0783's harvest/sow precedent — real corpus check does NOT bear this out: the word "limpet"
    # occurs ZERO times, in any context, anywhere in 11,760 real distinct thoughts. Unlike walk_sand's "walk"
    # (10 independently-confirmed real hits) or wood_life's "cut"/F-0783's crop names, there is no unmined
    # deed here to rescue — this is a plausible-sounding hypothesis a real corpus check overturns, exactly
    # the kind of check /findings-log's verified/inferred split exists to force rather than skip. "the shelf"
    # is worse than merely unsupported: it occurs 33 times, and the overwhelming majority are Du's own
    # BOOKSHELF ("a book on the shelf", "the skull on the shelf", "Burroughs' sketches" from the shelf) — a
    # genuine, heavily-represented homograph collision with the tidal mussel shelf, not a rare edge case.
    # The old test's own single real corpus "hit" is itself a confirmed false fire, not a missed positive:
    # "the tide pulls back, revealing mussel shells... I PICK UP a frosted green chip of SEA-GLASS" matches
    # bare "mussel" (scenery — the tide revealed the shells, Du did not gather them) cross-clause with bare
    # "pick" (which actually picks up sea-glass, an unrelated object) — precisely the cross-clause mis-
    # pairing hands.wants()'s real clause-scoping exists to prevent. Table-only gather/prise +
    # mussels/shellfish/kina has zero real corpus hits either way today (matching shore_ledger.jsonl, which
    # has never recorded a "shellfish" deed) — an honest zero, not a regression, since the one hit it replaces
    # was never a real gather to begin with.
    ("gather_shellfish", ("gather", "prise"), ("mussels", "shellfish", "kina")),
    # catch_fish is new this job (J-0732/F-1055) -- no old hand-kept copy to compare against, since no
    # fishing hand existed here before today. See this table's own header comment above and
    # core/actions.py's dated comment on the 'shore' row for the corpus sanity-check behind these words.
    # VERB IS "catch" ONLY, NOT "fish" -- caught the hard way, by this job's own verification harness
    # before commit: with "fish" in BOTH the verb and object tuples, a single bare ambient mention like
    # "small fish dart near the stream mouth" satisfies the verb test AND the object test off the exact
    # same word, so a scenery sentence with no willed catching in it at all would have wrongly fired.
    # "catch" alone (never "fish") as the verb closes this off completely: it requires a SEPARATE word
    # to name the catching, so a bare noun mention of fish can never self-satisfy both halves.
    ("catch_fish", ("catch",), ("fish",)),
    # D-0652 (J-3261): the dig, the turned stone and the opened shell (core/shore_dig.py). Verbs "dig", "turn over", "open"; objects reuse
    # "sand" and "stones" and add "shell". Corpus check on data/hands_trace.jsonl (62,316 distinct thoughts, read-only): "dig"+"sand" 1
    # hit (a buzzard's talons, third person), "turn over"+"stone(s)" 6 (all stones or a stone turning by themselves in the surf), "open"+
    # "shell(s)" 27 (all a gull hammering a shell open). The words alone cannot tell his will from the scene, so these three hands carry
    # their own first-person veto (_wills_dig_shore) on top of the table: the verb must follow I / let me / I'll / I want to directly.
    # act_from_thought only reaches them with the bestiary flag on.
    ("dig_sand", ("dig",), ("sand",)),
    ("turn_stone", ("turn over",), ("stone", "stones")),
    ("open_shell", ("open",), ("shell",)),
)
_SHORE_BY_NAME: dict[str, tuple[tuple, tuple]] = {n: (v, o) for n, v, o in _SHORE_HANDS}


def _wills_shore(t: str, name: str) -> bool:
    """Does this thought will `name` (one of _SHORE_HANDS' eleven shore behaviours)? Grammar READ from the one
    table (core/actions.py's 'shore' row) via that partition — a second hand-kept copy is the exact drift
    F-0554 was about, and this module had it in all ten original branches (F-1059; catch_fish is an
    eleventh, added whole by J-0732, never hand-kept at all). An empty objects tuple (wade's
    own entry) is this module's ONE deliberate any_object_ok=True case — see wade's own note above for the
    real corpus evidence behind keeping it loose rather than tightening it like every other branch here."""
    v, o = _SHORE_BY_NAME.get(name, ((), ()))
    if not v:
        return False
    try:
        from core import hands as _h
    except Exception:
        return False
    return _h.wants(t, v, o or None, any_object_ok=not o)


_FIRST_PERSON_WILL = r"\b(?:i|we|let me|i'll|i will|i want to|i could|i should|i must|i'd like to)\b(?:\s+(?:now|just|will|want to|could|should|must|then|go and|try to|can|might|shall))*\s+"


def _wills_dig_shore(t: str, name: str) -> bool:
    """The table test AND a first-person veto, for the three D-0652 hands: 'the gull hammers a shell open' and 'the stones turn over'
    are the scene, not his will (corpus: every one of the 34 raw hits). The verb has to follow his own 'I' (or 'let me') directly, with
    the object in the rest of the same clause."""
    if not _wills_shore(t, name):
        return False
    v, o = _SHORE_BY_NAME.get(name, ((), ()))
    for cl in re.split(r"(?<=[.!?;])\s+", t or ""):
        for verb in v:
            m = re.search(_FIRST_PERSON_WILL + re.escape(verb) + r"\b(?P<rest>[^.!?;]*)", cl)
            if not m:
                continue
            rest = m.group("rest")
            if any(re.search(r"(?<![a-z])" + re.escape(ob) + r"s?\b", rest) for ob in o):
                return True
    return False


_SHORE_FAMILIES = frozenset({"shore"})   # the one family core/actions.py binds here


def grammar_audit() -> dict:
    """What this module derives from core/actions.py's one 'shore' row, and any seam where the derivation
    could still drift. Read by scripts/_test_shore_life_grammar_derivation.py — verbs_unclaimed_in_table
    should be [] (all sixteen, including J-0738's "walk" widening and J-0732's "catch" addition, are
    claimed by exactly one behaviour each); objects_unclaimed_in_table should be exactly ["fire"] (see
    beach_fire's own note above on why bare "fire" is deliberately left unclaimed here, the same restraint
    fieldcraft's pass used for "knot" — J-0736); both *_claimed_not_in_table lists should be empty."""
    try:
        from core import actions as _ac
        a = _ac.BY_FAMILY["shore"]
        claimed_v = {v for _n, vs, _o in _SHORE_HANDS for v in vs}
        claimed_o = {o for _n, _v, os in _SHORE_HANDS for o in os}
        return {"verbs_unclaimed_in_table": sorted(set(a.verbs) - claimed_v),
                "verbs_claimed_not_in_table": sorted(claimed_v - set(a.verbs)),
                "objects_unclaimed_in_table": sorted(set(a.objects) - claimed_o),
                "objects_claimed_not_in_table": sorted(claimed_o - set(a.objects))}
    except Exception as exc:
        return {"error": repr(exc)[:120]}


# ── the hand ─────────────────────────────────────────────────────────────────────────────────────
def act_from_thought(thought: str, intention: str = "", family: str | None = None) -> str | None:
    """The shore's will→hand boundary. Returns the world's answer or None.

    FAMILY SCOPE (2026-09-07, J-0738 — matching the J-0554 pattern F-1059 asked for, even though only ONE
    family binds here so this parameter is not yet load-bearing anywhere live, following J-0736/J-0737's own
    precedent of adding it for consistency regardless): dispatch.py's own _via() will now pass
    family="shore" for its one Hand (harmless — falls through unchanged below), and a future caller may pass
    any other family string to force an immediate decline."""
    try:
        if family not in (None, "shore"):
            return None
        if _where() != "shore":
            return None
        t = f"{thought} {intention}".lower()
        if _wills_shore(t, "write_sand") and not re.search(r"\b(about|of) the sand\b", t):
            return write_sand(t)
        if _wills_shore(t, "walk_sand"):
            return walk_sand(t)
        if _wills_shore(t, "swim"):
            return swim(t)
        if _wills_shore(t, "wade"):
            return wade(t)
        if _wills_shore(t, "skip_stones"):
            return skip_stones(t)
        if _wills_shore(t, "cairn"):
            return cairn(t)
        if _wills_shore(t, "beach_fire"):
            return beach_fire(t)
        if _wills_shore(t, "enter_cave"):
            return enter_cave(t)
        if _wills_shore(t, "climb_ledge"):
            return climb_ledge(t)
        if _wills_shore(t, "gather_shellfish"):
            return gather_shellfish(t)
        if _wills_shore(t, "catch_fish"):
            return catch_fish(t)
        try:   # D-0652: only behind the bestiary flag; flag off = these do not exist
            from core import shore_dig as _sd
            _dig_on = _sd.enabled()
        except Exception:
            _dig_on = False
        if _dig_on:
            if _wills_dig_shore(t, "open_shell"):
                return open_shell(t)
            if _wills_dig_shore(t, "turn_stone"):
                return turn_stone(t)
            if _wills_dig_shore(t, "dig_sand"):
                return dig_sand(t)
        return None
    except profile.NonLiveWriteError:
        # J-0714: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — this can only fire when
        # profile.LIVE is False, never during Du's own real live loop, so this changes nothing live.
        raise
    except Exception:
        return None


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "not yet bootstrapped"}
        d = _load(); td = _tide()
        lo = d.get("latent_objects", [])
        return {"tide": td, "sand_bared": sand_bared(), "cave_open": cave_open(), "shelf_bared": shelf_bared(), "in_cave": d.get("in_cave"), "cairn": d.get("cairn"),
                "sand_writing": (d.get("sand_writing") or {}).get("text"), "fire": d.get("fire"), "swell": d.get("swell"), "seal": bool(d.get("seal")), "oyc_nest": bool(d.get("oyc_nest")),
                "fog": d.get("fog"), "sparkle": d.get("sparkle"), "skips_best": d.get("skips_best"), "wet_feet": d.get("wet_feet"),
                "latent_buried": len([x for x in lo if not x.get("revealed")]), "latent_revealed_unannounced": len([x for x in lo if x.get("revealed")])}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
