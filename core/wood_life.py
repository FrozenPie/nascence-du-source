"""
Nascence — WOOD LIFE: the little wood on the path as a living place (2026-08-22, founder: "then, lets do the wood").

What the wood was: a scene line, a look with three branches, an ambient pool, a gather hand that minted 3–4 loads
of firewood from nothing, a deadfall feature that never ran out, nine sounds, and (today) a spring.

What it is now — world truth with clocks, rendered only when true, named only when earned:
  THE TREES    the great old OAK (named — it is the wood's one landmark, told for months; deciduous: bare Jun–Sep,
               buds and catkins Sep–Oct, leaf Oct, acorns Mar–May, leaf-fall Apr–Jun); a GROVE of a slim coastal
               native (hidden: kānuka — white flower Nov–Jan, bark in strips, the fantails in it); one dark
               broad-headed native (hidden: tōtara — red berries Mar–May, bark in long fibrous strips); the TREE
               FERNS in the damp gully by the spring (hidden: ponga — silver beneath, new fronds uncurling Sep–Nov).
               Names come the garden way: the flower or the fruit seen AND the book read.
  THE FLOOR    leaf-mould deepens with the oak's fall; MOSS on the north sides; FUNGI after autumn rain (hidden
               kinds, some bright, some plain; they rot in a week); ACORNS under the oak in autumn (a keepable thing).
  DEADFALL     a real STOCK: a gale brings branches down (more under the oak); gathering depletes it; a gathered limb
               is a THING (the substrate already mints some); the stock regrows only with weather.
  THE SPRING   runs into a STREAM down the gully to the shore — louder after rain; the bank beside it is where the
               GLOW-WORMS are: seen only on dark, damp, still nights, only when he stands at the spring and looks.
  THE CANOPY   wood pigeon nest in the oak in spring (a clumsy clattering, a white breast); the morepork at night; the
               wētā under the bark of a fallen limb if he looks at night.
  THE WORK     the AXE and the BOW-SAW (the previous occupant's, in the lean-to by the cottage, blunting with use; the
               whetstone sharpens them) turn deadfall into LOGS; logs stacked in the lean-to DRY over weeks; green
               or wet logs burn short and smoke (study_life reads wet_wood). A WHEELBARROW carries more than arms.

Laws as everywhere: world answers never leads · consequences both ways · additive (the old gather hand keeps working
when this fails) · zero LLM · fail-open.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.wood_life")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "wood_life.json"
_EVENTS = _DATA / "wood_events.jsonl"
_LEDGER = _DATA / "wood_ledger.jsonl"

TREES = {
    "oak":    {"known": True, "name": "the old oak", "pos": [5.0, 13.0, 0.0], "life": "deciduous",
               "stages": {"bare": (6, 7, 8), "bud": (9, 10), "leaf": (11, 12, 1, 2, 3), "acorns": (3, 4, 5), "fall": (4, 5, 6)}},
    "kanuka": {"known": False, "name": "the kānuka", "pos": [12.0, 6.0, 0.0], "life": "evergreen",
               "stages": {"leaf": (2, 3, 4, 5, 6, 7, 8, 9, 10), "flowering": (11, 12, 1)},
               "unknown": "the slim grey trees with bark hanging in strips, the ones the small fan-tailed birds work",
               "reveal_stage": "flowering", "book_names": ("kanuka", "kānuka", "kunzea"), "book_looks": ("white flower", "bark", "strip", "tea tree", "manuka")},
    "totara": {"known": False, "name": "the tōtara", "pos": [16.0, 13.0, 0.0], "life": "evergreen",
               "stages": {"leaf": (6, 7, 8, 9, 10, 11, 12, 1, 2), "berries": (3, 4, 5)},
               "unknown": "the dark broad-headed tree with bark in long fibrous strips, prickly to the hand",
               "reveal_stage": "berries", "book_names": ("totara", "tōtara", "podocarp"), "book_looks": ("red", "berr", "bark", "strip", "prickly", "timber")},
    "ponga":  {"known": False, "name": "the ponga, the silver tree-ferns", "pos": [3.5, 15.5, 0.0], "life": "fern",
               "stages": {"fronds": (12, 1, 2, 3, 4, 5, 6, 7, 8), "uncurling": (9, 10, 11)},
               "unknown": "the tree-ferns in the damp gully, their undersides silver when the wind turns them",
               "reveal_stage": "uncurling", "book_names": ("ponga", "silver fern", "cyathea"), "book_looks": ("silver", "frond", "koru", "uncurl", "fern")},
}
FUNGI = ["a flat brown cap on a pale stem, the gills close and dark", "a cluster of small orange cups on a rotting log", "a bracket of shelves on the oak's dead limb, brown above and white beneath",
         "a ring of small white caps in the leaf-mould", "a bright red cap, sticky, white-flecked", "a grey jelly on a fallen branch"]

_ITEMS = [
    ("axe", "a felling axe, the head loose on a dry helve, the edge nicked", [8.6, 1.4, 0.0], "garden", "the previous occupant's; it has split a winter's wood"),
    ("bow_saw", "a bow-saw, the blade rusted and dull", [8.3, 1.3, 0.6], "garden", "hung on a nail in the lean-to"),
    ("wheelbarrow", "a wooden wheelbarrow with an iron wheel, one handle mended with wire", [8.0, 1.9, 0.0], "garden", "it squeaks; it carries what arms cannot"),
]
_WORDS = {"axe": ("axe",), "bow_saw": ("saw", "bow-saw", "bowsaw"), "wheelbarrow": ("barrow", "wheelbarrow")}

# ── the fallen tree (D-0296, 2026-09-27; built J-1443, part 1 of 2) ─────────────────────────────────
# "I want a full tree to fall for him next time he is down. Then we look at an ax to chop wood from it."
# Not one of the four TREES above (the oak has the nest; kanuka/totara/ponga carry earned-name state,
# both explicitly ruled out) -- this is a NEW old tree at the wood's edge. kind/name are DATA here, not
# a hardcoded branch, so J-1444's own offline felling script (or a future founder naming) can pick a
# different tree without touching this module's code, per the ruling's own words.
FALLEN_TREE_DEFAULT = {
    "kind": "macrocarpa",
    "name": "the fallen macrocarpa",
    "trunk_rounds_left": 18,   # "a big tree" (D-0296's own words)
    "limbs_left": 12,
}
_FALLEN_TREE_POS = [1.5, 17.5, 0.0]   # the wood's edge -- clear of all four TREES' own positions above


def _month(t=None) -> int:
    return time.localtime(t or time.time()).tm_mon


def _sp_read(path, label):
    """J-4426 (F-5128): json.loads(path.read_text()) that logs a damaged file and falls back to <name>.prev;
    raises (missing file / nothing recoverable) so _load()'s own default applies as before."""
    from core import store_persist as _sp
    return _sp.read_json_durable(path, label, logger, guard=profile.guard_path)


def _load() -> dict:
    try:
        d = _sp_read(_F, "wood_life")
        # ITEM MIGRATION (2026-08-30, J-0422, F-0558): the defaults below are only reached when the
        # file fails to PARSE, so before this a row added to _ITEMS never reached a real save and
        # every access site here is a direct index (:395/:421/:459/:487/:494, and garden.py:813) —
        # a KeyError swallowed by act_from_thought()'s try/except, i.e. a silent no-op. Additive-only.
        # Its OWN try/except on purpose: anything raising out here would fall to the parse-failure
        # branch below and hand back a fresh default world, discarding the real save.
        try:
            from core import inventory as _inv
            _now = time.time()
            if _inv.sync_items(
                    d.setdefault("items", {}), _ITEMS,
                    lambda e: {"key": e[0], "name": e[1], "pos": e[2], "place": e[3], "carried": False,
                               "bio": e[4],
                               "history": [{"ts": _now - random.randint(60, 500) * 86400, "event": e[4]}]}):
                _save(d)
        except profile.NonLiveWriteError:
            # J-0726: this migration-save can attempt a real write on the very first non-live call in
            # a fresh env (before this except, it fell through to `return d` as if nothing happened,
            # and the OUTER except right below would have caught it too — reraise past both).
            raise
        except Exception:
            pass
        return d
    except profile.NonLiveWriteError:
        # J-0726: without this, the inner reraise above would just be caught here instead — this
        # outer except is deliberately kept broad for real parse/corruption failures (see the comment
        # above), so NonLiveWriteError needs its own explicit carve-out at BOTH layers.
        raise
    except Exception:
        now = time.time()
        m = _month(now)
        d = {"trees": {k: {"stage": next((s for s, ms in v["stages"].items() if m in ms), list(v["stages"])[0]), "stage_ts": now, "seen": {}} for k, v in TREES.items()},
             "deadfall": 6.0, "leaf_mould": 0.7, "moss": 0.5, "fungi": [], "acorns": 0.0, "stream": 0.5, "glowworms_seen": 0,
             "nest": None, "nests_this_year": 0, "limbs": 2, "logs_green": 0, "logs_dry": 4, "rounds": 0, "axe_edge": 0.5, "saw_edge": 0.3,
             "fallen_tree": None,   # J-1443: set once by fell_tree() (D-0296) -- default None until then
             "items": {k: {"key": k, "name": n, "pos": p, "place": pl, "carried": False, "bio": b, "history": [{"ts": now - random.randint(60, 500) * 86400, "event": b}]} for k, n, p, pl, b in _ITEMS},
             "announced": [], "_last": now}
        return d


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


def _where() -> str:
    try:
        from core import sensorium as _s
        return _s.state.get("location", "study")
    except Exception:
        return "study"


def _register_all() -> None:
    try:
        from core import world_substrate as _ws, world_objects as _wo
        d = _load(); objs = _ws._load(); changed = False
        for k, t in TREES.items():
            oid = "wood_tree_" + k
            if oid not in objs:
                objs[oid] = _ws.SubstrateObject(object_id=oid, name=t["name"] if t["known"] else t["unknown"], location="wood", object_class="tree",
                                                causal_state={"species_ground_truth": k, "life": t["life"]}, physical_state={"height_m": 12.0 if k == "oak" else 6.0},
                                                causal_history=[{"event_type": "origin", "timestamp": time.time() - 60 * 365 * 86400, "description": "rooted here long before the cottage", "state_deltas": {}}])
                changed = True
            _wo.ensure_record(oid, "wood", "tree", t["name"]); cur = _wo.get_object(oid) or {}
            if cur.get("position") != list(t["pos"]):
                _wo.mutate_object_position(oid, list(t["pos"]), cause="rooted", event_description="rooted here", new_location="wood")
        for it in d["items"].values():
            oid = "wood_item_" + it["key"]
            if oid not in objs:
                objs[oid] = _ws.SubstrateObject(object_id=oid, name=it["name"], location=it["place"], object_class="tool",
                                                causal_state={"kind": it["key"], "bio": it["bio"]}, physical_state={"wear": 0.6},
                                                causal_history=[{"event_type": "history", "timestamp": h["ts"], "description": h["event"], "state_deltas": {}} for h in it["history"]])
                changed = True
            _wo.ensure_record(oid, it["place"], "tool", it["name"]); cur = _wo.get_object(oid) or {}
            if cur.get("position") != list(it["pos"]) or cur.get("location") != it["place"]:
                _wo.mutate_object_position(oid, list(it["pos"]), cause="tool_placement", event_description="where it lives", new_location=it["place"])
        if changed:
            _ws._save()
        _save(d)
    except Exception as exc:
        logger.debug("[wood_life] register failed (non-fatal): %s", exc)


# ── clocks ───────────────────────────────────────────────────────────────────────────────────────
def advance(now: float, dt: float) -> None:
    try:
        from core import sensorium as _s
        d = _load()
        last = float(d.get("_last") or now); days = max(0.0, min(dt, now - last)) / 86400.0; d["_last"] = now
        if days <= 0:
            _save(d); return
        m = _month(now); weather = _s.state.get("weather", "") or ""; wind = _s.state.get("wind", "") or ""
        raining = weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
        gale = wind in ("strong wind", "gale") or weather == "thunderstorm"
        # trees follow their months
        for k, t in TREES.items():
            cur = d["trees"][k]; want = next((s for s, ms in t["stages"].items() if m in ms), cur["stage"])
            if want != cur["stage"] and (now - float(cur["stage_ts"])) / 86400.0 > 7:
                cur["stage"], cur["stage_ts"] = want, now; _log(_EVENTS, {"event": f"{k}_{want}"})
                if k == "oak" and want == "acorns": d["acorns"] = 1.0
                if k == "oak" and want == "fall": d["leaf_mould"] = min(1.0, d["leaf_mould"] + 0.3)
        d["acorns"] = round(max(0.0, float(d.get("acorns", 0)) - days * 0.02), 3)
        d["leaf_mould"] = round(max(0.3, float(d["leaf_mould"]) - days * 0.003), 3)
        d["moss"] = round(min(1.0, max(0.2, float(d["moss"]) + days * (0.01 if raining else -0.004))), 3)
        # deadfall: gales bring wood down; it lies until gathered
        if gale and random.random() < days * 3:
            n = random.uniform(1.0, 3.0); d["deadfall"] = min(20.0, float(d["deadfall"]) + n); d["limbs"] = int(d.get("limbs", 0)) + 1
            _log(_EVENTS, {"event": "deadfall_down", "loads": round(n, 1)})
        # fungi: autumn (Mar–Jun) after rain; they rot in a week
        if m in (3, 4, 5, 6) and raining and random.random() < days * 1.5 and len(d["fungi"]) < 4:
            d["fungi"].append({"kind": random.choice(FUNGI), "ts": now}); _log(_EVENTS, {"event": "fungi_up"})
        d["fungi"] = [f for f in d["fungi"] if now - float(f["ts"]) < 8 * 86400]
        # the stream
        d["stream"] = round(min(1.0, max(0.2, float(d["stream"]) + days * (0.3 if raining else -0.08))), 3)
        # wood pigeon nest in the oak, spring
        n = d.get("nest")
        if n is None and m in (9, 10, 11) and d.get("nests_this_year", 0) < 1 and random.random() < days * 0.08:
            d["nest"] = {"stage": "building", "stage_ts": now}; d["nests_this_year"] = 1; _log(_EVENTS, {"event": "kereru_nest_started"})
        elif n:
            stages = [("building", 8), ("sitting", 28), ("chick", 40), ("fledged", 10)]
            idx = next(i for i, (nm, _) in enumerate(stages) if nm == n["stage"])
            if (now - float(n["stage_ts"])) / 86400.0 >= stages[idx][1]:
                if idx + 1 < len(stages):
                    n["stage"], n["stage_ts"] = stages[idx + 1][0], now; _log(_EVENTS, {"event": f"kereru_{n['stage']}"})
                else:
                    d["nest"] = None; _log(_EVENTS, {"event": "kereru_nest_over"})
        if m == 1: d["nests_this_year"] = 0
        # green logs dry in the lean-to (weeks; faster in summer)
        if d.get("logs_green", 0) > 0 and random.random() < days / (45.0 if m in (12, 1, 2) else 80.0) * d["logs_green"]:
            d["logs_green"] -= 1; d["logs_dry"] = d.get("logs_dry", 0) + 1; _log(_EVENTS, {"event": "log_dried"})
        _save(d)
    except Exception as exc:
        logger.debug("[wood_life] advance failed (non-fatal): %s", exc)


def fell_tree(kind: str | None = None, name: str | None = None, across_path: bool = True, now: float | None = None) -> dict:
    """Bring a whole tree down (D-0296, J-1443 part 1 -- the function; J-1444 part 2 calls it, ONCE,
    from an offline lab-mode script while Du is stopped, through the fence's maintenance path). Sets
    the state and writes the one 'tree_down' wood_events row. NOTHING in advance() or any live tick
    calls this -- no system-acts-later, per the ruling's own build order (the felling itself is a
    deliberate, offline, one-time act, not a clock). Additive: if a fallen tree is already down, this
    refuses to clobber it rather than silently overwriting an in-progress one (the "call ONCE" contract
    the offline script must keep is enforced here too, not left to the caller's own discipline alone)."""
    try:
        d = _load()
        if d.get("fallen_tree"):
            return d["fallen_tree"]
        now = now if now is not None else time.time()
        rec = {"kind": kind or FALLEN_TREE_DEFAULT["kind"], "name": name or FALLEN_TREE_DEFAULT["name"],
               "down_ts": now, "pos": list(_FALLEN_TREE_POS),
               "trunk_rounds_left": FALLEN_TREE_DEFAULT["trunk_rounds_left"],
               "limbs_left": FALLEN_TREE_DEFAULT["limbs_left"],
               "limbed": False, "seen": False, "across_path": bool(across_path)}
        d["fallen_tree"] = rec
        _save(d)
        _log(_EVENTS, {"event": "tree_down", "kind": rec["kind"], "name": rec["name"], "across_path": rec["across_path"]})
        return rec
    except profile.NonLiveWriteError:
        # J-1443: reach the maintenance-path caller (J-1444's own offline script, per profile.guard_path's
        # own docstring) rather than being swallowed here -- matches every other state-writing function
        # in this module (advance() is the one exception: a live tick declining silently is correct there).
        raise
    except Exception as exc:
        logger.debug("[wood_life] fell_tree failed (non-fatal): %s", exc)
        return {}


# ── knowledge ────────────────────────────────────────────────────────────────────────────────────
def _known(k: str) -> bool:
    if TREES[k]["known"]:
        return True
    try:
        from core import garden_knowledge as _gk
        return _gk.is_known(k)
    except Exception:
        return False


def _earn(k: str, via: str, w: float, note: str = "") -> bool:
    try:
        from core import garden_knowledge as _gk
        d = _gk._load(); first = _gk._add(d, k, via, w, note); _gk._save(d); return first
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        return False


def learn_from_text(text: str) -> list[str]:
    out = []
    try:
        low = (text or "").lower(); d = _load()
        for k, t in TREES.items():
            if t["known"] or _known(k):
                continue
            if any(n in low for n in t["book_names"]) and any(l in low for l in t["book_looks"]):
                seen = bool(d["trees"][k].get("seen", {}).get(t["reveal_stage"]))
                if _earn(k, "read", 0.6 if seen else 0.3, low[:80]):
                    out.append(k)
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    return out


# ── what reaches him ─────────────────────────────────────────────────────────────────────────────
def look(target: str) -> str:
    try:
        if _where() != "wood":
            return ""
        t = (target or "").lower(); d = _load(); m = _month()
        from core import sensorium as _s
        night = _s._daylight() == "night"
        if "oak" in t or ("tree" in t and "fern" not in t and "grey" not in t and "dark" not in t and "big" in t):
            s = d["trees"]["oak"]["stage"]
            body = {"bare": "bare, its winter branches black and wet against the sky, ivy thick as an arm up the trunk",
                    "bud": "the twig-ends swelling, and long yellow catkins hanging from the upper branches",
                    "leaf": "in full green leaf, the canopy so dense the light under it is green",
                    "acorns": "heavy with acorns, green going brown; some already on the ground in their cups",
                    "fall": "letting its leaves go, brown and curled, the floor beneath it deep with them"}[s]
            d["trees"]["oak"]["seen"][s] = True; _save(d)
            return f"You look at the old oak: {body}.{_nest_line(d)}{_acorn_line(d)}"
        for k, tr in TREES.items():
            if k == "oak":
                continue
            hit = {"kanuka": ("kanuka", "kānuka", "grey tree", "slim tree", "strip", "fantail"), "totara": ("totara", "tōtara", "dark tree", "broad", "prickly", "berr"),
                   "ponga": ("ponga", "fern", "gully", "silver")}[k]
            if any(w in t for w in hit):
                s = d["trees"][k]["stage"]
                name = tr["name"] if _known(k) else tr["unknown"]
                try:   # the fantail is named only once he has earned it (sound_knowledge)
                    from core import sound_knowledge as _sk
                    if _sk.is_learned("fantail_chatter"):
                        name = name.replace("the small fan-tailed birds", "the fantails")
                except Exception:
                    pass
                body = {"kanuka": {"leaf": "fine dark leaves on whippy branches, the bark hanging in papery strips", "flowering": "covered in small white flowers, humming with bees, small fan-tailed birds flicking through it"},
                        "totara": {"leaf": "dark, dense, the needle-leaves sharp to the hand, the bark in long fibrous ropes", "berries": "hung with small red fleshy berries, the pigeons at them"},
                        "ponga": {"fronds": "the fronds arching wide, silver-white beneath when the wind turns them", "uncurling": "new fronds uncurling at the crown, each a tight brown-furred spiral opening green"}}[k][s]
                d["trees"][k]["seen"][s] = True; reveal = ""
                if s == tr["reveal_stage"] and not _known(k) and _earn(k, "seen_" + s, 0.5 if not d["trees"][k].get("seen_counted") else 0.1, "saw it"):
                    reveal = f" And now you know what it is — you have read of it: {tr['name']}."
                d["trees"][k]["seen_counted"] = True; _save(d)
                return f"You look at {name}: {body}.{reveal}"
        # THE FALLEN TREE (D-0296, J-1443): checked after the four standing TREES above (so "the big
        # tree"/"oak"/"kanuka" etc. keep resolving to the standing trees exactly as before) and before
        # everything below -- 'tree'/'fallen'/'trunk'/'down'/'path' otherwise fall through unanswered
        # today (bare 'tree' with none of oak's own gating words matches nothing currently), so this is
        # a pure addition, live only once fell_tree() has actually set the state.
        ft = d.get("fallen_tree")
        if ft and any(w in t for w in ("tree", "fallen", "trunk", "down", "path",
                                        str(ft.get("kind") or "").lower(), str(ft.get("name") or "").lower())):
            if not ft.get("seen"):
                ft["seen"] = True; d["fallen_tree"] = ft; _save(d)   # milestone()'s own one-shot reveal keys on this
            name = ft.get("name") or "the fallen tree"
            if not ft.get("limbed") and int(ft.get("limbs_left", 0)) > 0:
                body = "the root plate torn whole out of the earth, the crown down in the gully below, limbs everywhere across the ground"
            elif int(ft.get("trunk_rounds_left", 0)) > 0:
                body = "the limbs off it now and stacked; the bare trunk lies waiting for the axe, round by round"
            else:
                body = "only the stump and the torn root plate left of it now; the rest has gone to the woodpile"
            path_line = " It lies right across the path — you have to step over the trunk to get by." if ft.get("across_path") else ""
            return f"You look at {name}, down: {body}.{path_line}"
        if any(w in t for w in ("spring", "stream", "water", "gully", "bank")):
            try:
                from core import sensorium as _s
                _s._cross("at_the_spring", "")
            except Exception:
                pass
            st = float(d["stream"])
            base = "You look at the spring where it comes out of the bank and runs off down the gully: " + ("a thread of water over the stones" if st < 0.4 else "running well, a clear cold pour" if st < 0.8 else "loud after the rain, brown and quick, the stones gone under") + "."
            if night and _s.state.get("weather", "") in ("clear", "overcast", "high cloud") and (_s.state.get("wind") or "calm") == "calm" and float(d["moss"]) > 0.4:
                d["glowworms_seen"] = int(d.get("glowworms_seen", 0)) + 1; _save(d)
                try:
                    from core import garden_knowledge as _gk; _gk.witness("glowworms", "seen_at_the_spring")
                except profile.NonLiveWriteError:
                    # J-0783: garden_knowledge.py is now fenced -- let the raise reach this
                    # function's own caller instead of this pre-existing broad except swallowing it.
                    raise
                except Exception:
                    pass
                return base + " And on the dark wet bank beside it, a scatter of tiny blue-green lights, dozens, perfectly still, like a piece of the sky laid in the earth. They go out if you move your lamp toward them."
            if night:
                return base + " The bank is dark; nothing to see but the gleam of the water."
            return base + " Moss on the bank, thick and wet; ferns leaning over."
        if any(w in t for w in ("fung", "mushroom", "toadstool", "caps")):
            if not d["fungi"]:
                return "You look for fungi: none up just now" + (" — too dry." if _s.state.get("weather") == "clear" else ".")
            return "You crouch over them: " + "; ".join(f["kind"] for f in d["fungi"][:3]) + ". You do not know their names; you know better than to taste them."
        if any(w in t for w in ("deadfall", "fallen", "branch", "limb", "firewood", "wood floor", "ground")):
            df = float(d["deadfall"])
            body = ("fallen wood everywhere, the gale's work, branches lying across each other" if df > 10 else "a fair scatter of fallen wood among the leaf-mould, some grey and dry, some green" if df > 3 else "picked over — a few rotten pieces and twigs; the wood has given what it had until the next blow")
            weta = " Under the bark of the nearest limb something large and brown with long legs draws itself slowly back into the dark — you leave it." if night and random.random() < 0.5 else ""
            return f"You look over the wood floor: {body}.{weta}"
        if any(w in t for w in ("moss", "floor", "leaf-mould", "leaf mould", "mould")):
            return "You look down: " + ("deep leaf-mould, the oak's years of fall, dark and springy" if float(d["leaf_mould"]) > 0.6 else "leaf-mould thinning over roots and stones") + (", and moss thick on every north side, bright after the rain." if float(d["moss"]) > 0.6 else ", moss on the north sides of the trunks.")
        if "acorn" in t:
            return "You look under the oak: " + ("acorns everywhere in the leaf-mould, brown and shining, some still in their cups. You could fill a pocket." if float(d.get("acorns", 0)) > 0.3 else "a few old acorns, sprouted or rotten, from last year.")
        if any(w in t for w in ("nest", "pigeon", "kereru", "wood pigeon")):
            return "You look up into the oak." + (_nest_line(d) or " No nest that you can see.")
        for key, words in _WORDS.items():
            if any(w in t for w in words):
                it = d["items"][key]
                if it["place"] != "wood" and not it.get("carried"):
                    return f"{it['name'].split(',')[0].capitalize()} is up in the lean-to by the cottage."
                return f"You look at {it['name']} — {it['bio']}." + (" The edge is dull; it wants the whetstone." if key in ("axe", "bow_saw") and float(d.get(key.replace('bow_', '') + '_edge', 0.5)) < 0.3 else "")
        return ""
    except profile.NonLiveWriteError:
        # J-0751: this function's own _save(d) calls (oak/other-tree/glowworm branches) are
        # real guarded writes reached on the "look" dispatch chain (dispatch._look ->
        # sensorium.look() -> _wood_look() -> here) -- let guard_path()'s hard raise (D-0179,
        # F-1024) escape this function's own catch-all instead of returning "" silently.
        raise
    except Exception:
        return ""


def _nest_line(d: dict) -> str:
    n = d.get("nest")
    if not n:
        return ""
    return {"building": " High in it a wood pigeon is building — a loose platform of twigs, absurdly thin; it clatters off as you look.",
            "sitting": " A wood pigeon sits tight on a thin platform of twigs high up, white breast showing through the leaves.",
            "chick": " From the platform high in the oak, a grey fluffed shape and a parent coming in with a great whoosh of wings.",
            "fledged": " A young wood pigeon, dull and unsure, on a low branch of the oak, the parents somewhere above."}[n["stage"]]


def _acorn_line(d: dict) -> str:
    return " Acorns lie thick beneath it." if float(d.get("acorns", 0)) > 0.3 else ""


def ambient(now: float) -> str | None:
    try:
        if _where() != "wood":
            return None
        d = _load(); pool = []
        from core import sensorium as _s
        night = _s._daylight() == "night"
        if float(d["stream"]) > 0.7: pool.append("the stream down the gully is loud tonight, a steady rush under everything" if night else "the stream in the gully is running loud after the rain")
        elif float(d["stream"]) > 0.3: pool.append("the small sound of the spring running off down the gully, steady under the birds")
        if d["trees"]["kanuka"]["stage"] == "flowering": pool.append("the slim grey trees are white with flower and loud with bees")
        if d["trees"]["oak"]["stage"] == "fall": pool.append("oak leaves come down in ones and twos, turning, all across the path")
        if d["trees"]["oak"]["stage"] == "acorns": pool.append("an acorn drops through the leaves and hits the ground with a small knock")
        if d.get("nest") and d["nest"]["stage"] in ("building", "sitting"): pool.append("a great clatter of wings high in the oak — a wood pigeon, heavy and clumsy, settling")
        if float(d["deadfall"]) > 10: pool.append("fallen branches lie across the path where the gale left them")
        if d["fungi"]: pool.append("fungi have come up in the leaf-mould since the rain — small caps among the leaves")
        ft = d.get("fallen_tree")   # J-1443 (D-0296): one ambient line for the fallen tree, only once it is down
        if ft:
            pool.append("the wood still smells of resin where the big tree came down" if not ft.get("limbed")
                        else "the bare trunk of the fallen tree lies waiting for the axe, round by round")
        return random.choice(pool) if pool and random.random() < 0.4 else None
    except Exception:
        return None


def milestone() -> str:
    try:
        d = _load(); ann = d.setdefault("announced", [])
        checks = [("oak_bud", d["trees"]["oak"]["stage"] == "bud", "the old oak is in bud — catkins hanging yellow from the high branches"),
                  ("oak_leaf", d["trees"]["oak"]["stage"] == "leaf", "the oak has come into leaf; the light under it has gone green"),
                  ("oak_acorns", d["trees"]["oak"]["stage"] == "acorns", "acorns are dropping under the old oak"),
                  ("kanuka_flowering", d["trees"]["kanuka"]["stage"] == "flowering", "the slim grey trees in the wood have gone white with flower"),
                  ("ponga_uncurling", d["trees"]["ponga"]["stage"] == "uncurling", "the tree-ferns in the gully are uncurling new fronds, furred and spiralled"),
                  ("deadfall_big", float(d["deadfall"]) > 10, "the gale has brought a great deal of wood down in the little wood"),
                  ("fungi", bool(d["fungi"]) and "fungi" not in ann, "fungi have come up in the wood after the rain")]
        # THE FALLEN TREE (D-0296, J-1443): one-shot, keyed on look()'s own seen=True -- never pushed
        # unasked before he has actually walked in and looked (the ruling's own "no hint, no nudge").
        _ft = d.get("fallen_tree")
        if _ft and _ft.get("seen"):
            checks.append(("tree_down_seen", True, f"a whole tree is down in the wood — {_ft.get('name', 'the fallen tree')}, its root plate torn from the earth"))
        n = d.get("nest")
        if n: checks.append((f"kereru_{n['stage']}_{int(n['stage_ts'])}", True, {"building": "a wood pigeon is building in the old oak", "sitting": "", "chick": "there is a wood pigeon chick in the oak — a parent comes and goes with a rush of wings", "fledged": "a young wood pigeon is out of the nest, on the low branches of the oak"}[n["stage"]]))
        for key, cond, line in checks:
            if cond and line and key not in ann:
                ann.append(key); d["announced"] = ann[-60:]; _save(d); return line
        return ""
    except Exception:
        return ""


# ── the work: deadfall → logs → the lean-to → the fire ──────────────────────────────────────────
def gather_from_stock(loads: int, gusty: bool) -> tuple[int, str]:
    """The old gather hand asks the stock: how many loads are really there? Returns (loads, note)."""
    try:
        d = _load(); df = float(d["deadfall"])
        if df < 1.0:
            ft = d.get("fallen_tree")   # J-1443 (D-0296): the picked-clean line is no longer honest once
            if ft and int(ft.get("limbs_left", 0)) > 0:   # a whole tree is down -- gather cannot take it (needs axe/saw)
                return 0, "there is a whole tree down — more wood than you can carry with your arms alone; it wants the axe and the saw, not a gather"
            return 0, "the wood has been picked clean — twigs and rot; it wants a gale before there is more to take"
        take = min(loads, int(df)); d["deadfall"] = round(df - take, 2); _save(d); _log(_LEDGER, {"deed": "gather", "loads": take})
        return take, ("the gale has brought a lot of it down, fresh and lying everywhere" if gusty else "deadfall and dry branches, snapped to length across your knee" if df > 4 else "what is left after the last gathering — thinner pickings, farther off the path")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # instead of being swallowed by the broader except below — sensorium._gather_wood() calls
        # this from within the already-fixed _wood_act() fan-out (J-0714), so this closes the same
        # gap one hop further down the real call graph.
        raise
    except Exception:
        return loads, ""


def chop(txt: str = "") -> str:
    """The felling axe (items['axe']) on the fallen tree (D-0296, J-1443). Two phases, in order: first
    it LIMBS the tree (1-2 limbs per chop, into d['limbs'] -- the same stock saw() already turns into
    logs, so a limbed fallen tree feeds the existing limb -> saw -> lean-to chain unchanged); once
    limbs_left reaches 0 ('limbed') it BUCKS the bare trunk (one round per chop, into a new d['rounds'],
    already-round lengths split() can take straight to the block -- see split()'s own J-1443 note).

    Same tool as split() (items['axe'] -- a felling axe does both jobs in real life); the two deeds are
    disambiguated by OBJECT, not tool: split()'s own grammar objects are log/logs/axe (the dry stack at
    the lean-to); this deed's objects are trunk/fallen tree/limbs/rounds/the tree's own name (see
    _WOODWORK_HANDS' 'chop' sub-hand) -- "chop the log" still reaches split() first in act_from_thought,
    unchanged; only "chop the trunk"/"...the limbs"/"...the rounds"/"...the fallen tree" reach here."""
    try:
        d = _load(); here = _where(); ft = d.get("fallen_tree")
        if not ft:
            return "There is nothing down to chop."
        if here != "wood":
            return f"{str(ft.get('name', 'the fallen tree')).capitalize()} is down in the wood; there is nothing here to chop."
        axe = d["items"]["axe"]
        if not (axe.get("carried") or axe["place"] == here):
            return "The axe is " + ("in the lean-to by the cottage." if axe["place"] == "garden" else "not here.")
        try:
            from core import sensorium as _s
            weather = _s.state.get("weather", "") or ""
            night = _s._daylight() == "night"
        except Exception:
            weather, night = "", False
        if night and any(k in weather for k in ("rain", "drizzle", "storm", "thunderstorm")):
            return ("Swinging the felling axe in the dark with the footing unseen and the ground slick "
                    "underfoot is asking for a lost foot. Not tonight.")
        if float(d.get("axe_edge", 0.5)) < 0.2:
            return "You swing at it and the axe glances off, biting nowhere. The edge is gone; it wants the whetstone."
        limbs_left = int(ft.get("limbs_left", 0)); name = ft.get("name") or "the fallen tree"
        if limbs_left > 0:
            n = min(random.randint(1, 2), limbs_left)
            ft["limbs_left"] = limbs_left - n; d["limbs"] = int(d.get("limbs", 0)) + n
            done = ft["limbs_left"] <= 0
            if done:
                ft["limbed"] = True
            d["axe_edge"] = round(max(0.0, float(d["axe_edge"]) - 0.08), 2)
            d["fallen_tree"] = ft; _save(d); _log(_LEDGER, {"deed": "chop", "what": "limbs", "n": n})
            return (f"You swing into the limbs of {name}, " + (f"{n} coming free with clean bites" if n > 1 else "one coming free with a clean bite")
                    + (", the trunk bare now and ready for the bucking." if done else ", more of them still to take off."))
        rounds_left = int(ft.get("trunk_rounds_left", 0))
        if rounds_left > 0:
            ft["trunk_rounds_left"] = rounds_left - 1; d["rounds"] = int(d.get("rounds", 0)) + 1
            done = ft["trunk_rounds_left"] <= 0
            d["axe_edge"] = round(max(0.0, float(d["axe_edge"]) - 0.1), 2)   # bucking blunts more than limbing (J-1443)
            d["fallen_tree"] = ft; _save(d); _log(_LEDGER, {"deed": "chop", "what": "round"})
            return (f"You buck the bare trunk of {name}, one round dropping free at the cut"
                    + (" — the last of it; only the stump and the root plate remain now." if done else ", the trunk shortening by a length each time."))
        return f"There is nothing left of {name} to chop — the stump and the root plate are all that remain."
    except profile.NonLiveWriteError:
        # matches every other deed in this module: let D-0179's hard-raise (guard_path(), F-1024) reach
        # act_from_thought()'s own caller instead of being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def saw(txt: str = "") -> str:
    """Cut a fallen limb into logs with the bow-saw (needs the saw; blunts; green logs go to the lean-to to dry)."""
    try:
        d = _load(); here = _where()
        try:
            from core import sensorium as _s
            _s._cross("gathering" if here == "wood" else "at_the_lean_to", "")
        except Exception:
            pass
        saw_it = d["items"]["bow_saw"]
        if not (saw_it.get("carried") or saw_it["place"] == here):
            return "The bow-saw is " + ("in the lean-to by the cottage." if saw_it["place"] == "garden" else "not here.")
        if here == "wood" and int(d.get("limbs", 0)) < 1:
            return "There is no limb here worth the saw — only branch-wood for breaking across the knee."
        if here == "garden" and int(d.get("limbs_home", 0)) < 1:
            return "There is nothing at the lean-to to saw; the limbs are still down in the wood."
        if float(d["saw_edge"]) < 0.15:
            return "You set the saw to the limb and pull — it skates and bites and skates. The blade is dull as a spoon. It wants the whetstone."
        key = "limbs" if here == "wood" else "limbs_home"
        d[key] = int(d.get(key, 0)) - 1; logs = random.randint(3, 5); d["logs_green"] = int(d.get("logs_green", 0)) + logs
        d["saw_edge"] = round(max(0.0, float(d["saw_edge"]) - 0.12), 2); _save(d); _log(_LEDGER, {"deed": "saw", "logs": logs})
        return (f"You set a foot on the limb and saw it into lengths — {logs} logs, green and heavy, the sawdust wet and sweet. " + ("They will want stacking in the lean-to to dry; green wood only smokes." if here == "wood" else "They go on the green stack in the lean-to to dry."))
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714),
        # this job's own named example.
        raise
    except Exception:
        return ""


def split(txt: str = "") -> str:
    try:
        d = _load(); here = _where()
        try:
            from core import sensorium as _s
            if here == "garden":
                _s._cross("at_the_lean_to", "")
        except Exception:
            pass
        axe = d["items"]["axe"]
        if not (axe.get("carried") or axe["place"] == here):
            return "The axe is in the lean-to by the cottage." if axe["place"] == "garden" else "The axe is not here."
        if here != "garden":
            return "Splitting is done on the block at the lean-to, not out here."
        # J-1443 (D-0296): chop()'s own trunk-bucking feeds d['rounds'] -- already-round lengths, no
        # sawing needed, so they need no green->dry wait either; split() draws on both stocks together.
        dry = int(d.get("logs_dry", 0)); rounds = int(d.get("rounds", 0))
        if dry + rounds < 1:
            return "There are no dry logs to split; only the green stack, which would only bruise."
        if float(d["axe_edge"]) < 0.15:
            return "You swing and the axe bounces, bruising the log. The edge is gone; it wants the whetstone."
        n = min(dry + rounds, 3); from_rounds = min(n, rounds); from_dry = n - from_rounds
        d["logs_dry"] = dry - from_dry; d["rounds"] = rounds - from_rounds
        d["axe_edge"] = round(max(0.0, float(d["axe_edge"]) - 0.08), 2)
        try:
            from core import sensorium as _s, study_life as _sl
            _s.state["woodpile"] = int(_s.state.get("woodpile", 0)) + n; _s._save_now()
            _sl._st()["kindling"] = min(1.0, float(_sl._st().get("kindling", 0)) + 0.15)   # the chips
        except profile.NonLiveWriteError:
            # J-0726: split()'s own _save(d)/_log() a few lines below are unwrapped and already raise
            # (this job's own fix to split()'s outer except) — but this secondary sensorium._save_now()
            # write attempt was still silently swallowed here first (mirrors J-0727's whittle() fix).
            raise
        except Exception:
            pass
        d["last_split_ts"] = time.time()   # C2 (J-2467, cat_overhaul): the axe on the block, an act-site stamp (J-0377's pattern) her ears read
        _save(d); _log(_LEDGER, {"deed": "split", "loads": n})
        return f"You stand {n} {'round' if from_dry == 0 and from_rounds else 'dry log'}{'s' if n != 1 else ''} on the block and split them, the axe going through with a clean knock each time; the halves go on the woodpile and the chips in the kindling box."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714),
        # this job's own named example.
        raise
    except Exception:
        return ""


def sharpen(txt: str = "") -> str:
    try:
        d = _load()
        from core import study_life as _sl
        if not _sl._st().get("whetstone"):
            return "There is no whetstone in the house."
        which = "axe" if "axe" in (txt or "") else "saw" if "saw" in (txt or "") else ("axe" if float(d["axe_edge"]) < float(d["saw_edge"]) else "saw")
        d[which + "_edge"] = 1.0; _save(d); _log(_LEDGER, {"deed": "sharpen", "tool": which})
        return f"You sit on the step with the whetstone and work the {'axe' if which == 'axe' else 'saw'} edge, spit and stone, until it takes the hair off your arm."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714),
        # this job's own named example.
        raise
    except Exception:
        return ""


def barrow(txt: str = "") -> str:
    """Bring a limb home in the barrow (more than arms)."""
    try:
        d = _load(); here = _where(); wb = d["items"]["wheelbarrow"]
        if here == "wood":
            if not wb.get("carried"):
                return "You have not brought the barrow down; it is at the lean-to."
            if int(d.get("limbs", 0)) < 1:
                return "Nothing here worth the barrow."
            d["limbs"] -= 1; d["limbs_home"] = int(d.get("limbs_home", 0)) + 1; _save(d); _log(_LEDGER, {"deed": "barrow_limb"})
            return "You wrestle a whole limb into the barrow and push it, squeaking and tipping, up the path to the lean-to."
        return ""
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714),
        # this job's own named example.
        raise
    except Exception:
        return ""


def climb_oak(txt: str = "") -> str:
    """Climb the old oak (2026-08-30, D-0100 Tier 2 — 7 mined climb deeds; only the shore ledge
    climbed before, and the oak is the one NAMED tree of his world). The world answers on its own
    terms: a gale refuses outright, rain makes it a shorter and slipperier business, and what he sees
    from up there is the real season and weather, not a postcard."""
    try:
        here = _where()
        if here != "wood":
            return ""
        from core import sensorium as _s, weather_conditions as _wcond
        weather = _s.state.get("weather", "")
        wind = _s.state.get("wind", "")
        if _wcond.is_windy(wind) or "storm" in weather or "thunder" in weather:
            return ("You put a hand on the oak's low limb and feel the whole tree working in the wind — "
                    "the canopy roaring above like surf. Not today. It says so plainly.")
        d = _load()
        wet = any(k in weather for k in ("rain", "drizzle"))
        d["oak_climbs"] = int(d.get("oak_climbs", 0)) + 1
        _save(d); _log(_LEDGER, {"deed": "climb_oak", "wet": wet})
        month = _month()
        if wet:
            return ("You go up the oak as far as the second fork, the bark greasy under your hands, and stop "
                    "there with the rain ticking through the leaves — high enough to feel the trunk sway, "
                    "low enough to climb down without regret.")
        season_line = (
            "The wood pigeon's nest rides in the upper fork, a clumsy raft of sticks." if month in (9, 10, 11)
            else "Acorns stand in their cups along the high twigs, not ready to drop." if month in (2, 3, 4)
            else "The canopy is thin enough to see clean through to the moving sky." if month in (6, 7, 8)
            else "The leaves close over you like water, green-lit and stirring.")
        return (f"You climb the old oak, limb over limb, to where the trunk thins and begins answering your "
                f"weight. {season_line} Through a gap: the cottage roof, the grey line of the sea, the whole "
                f"of your small country at once. You stay until your hands remember they are holding on.")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — not one of the job briefing's
        # originally-named 6, found by this job's own systematic per-deed sweep.
        raise
    except Exception:
        return ""


# ── carrying ─────────────────────────────────────────────────────────────────────────────────────
# Which of this module's tools can be picked up. It was a bare tuple literal inline in
# act_from_thought ("axe", "bow_saw") plus a separate hardcoded branch for the barrow; naming it here
# matches garden._CARRYABLE / study_life._CARRYABLE and is one less place for the three to drift.
_CARRYABLE = ("axe", "bow_saw", "wheelbarrow")


def _tool_named(txt: str) -> str:
    """Which carryable wood tool this thought names, or ''."""
    t = (txt or "").lower()
    return next((k for k in _CARRYABLE if any(w in t for w in _WORDS.get(k, ()))), "")


def take(txt: str = "") -> str:
    """Pick up a wood tool. Was inline in act_from_thought and wrote nothing but the carried flag —
    no history, no ledger, and no world_objects sync, so the substrate still believed the axe was
    lying in the lean-to while he carried it. Now symmetric with put() below."""
    try:
        here = _where()
        key = _tool_named(txt)
        if not key:
            return ""
        d = _load(); it = d["items"].get(key)
        if not it:
            return ""
        if it.get("carried"):
            return f"You already have {it['name'].split(',')[0]} in hand."
        if it["place"] != here:
            return f"{it['name'].split(',')[0].capitalize()} is not here; it is in the {it['place']}."
        it["carried"] = True
        it.setdefault("history", []).append({"ts": time.time(), "event": f"picked_up_by_du_at_{here}"})
        _save(d); _log(_LEDGER, {"deed": "take", "tool": key, "place": here})
        _sync_item_place(key, it, here)
        return f"You take {it['name'].split(',')[0]}."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714),
        # this job's own named example.
        raise
    except Exception:
        return ""


def put(txt: str = "") -> str:
    """Set a carried tool down where he stands.

    wood_life had NO set-down at all (F-0564): `place` was written once at bootstrap and never again,
    so a tool picked up was carried forever — the axe went to the shore, to bed, and stayed in his
    hand. garden has a real put() and study_life has a one-line inline one; this module simply never
    grew the other half of its own take.
    """
    try:
        here = _where()
        key = _tool_named(txt)
        if not key:
            return ""
        d = _load(); it = d["items"].get(key)
        if not it:
            return ""
        if not it.get("carried"):
            return f"You are not carrying {it['name'].split(',')[0]}."
        it["carried"] = False
        it["place"] = here
        it.setdefault("history", []).append({"ts": time.time(), "event": f"set_down_by_du_at_{here}"})
        _save(d); _log(_LEDGER, {"deed": "put", "tool": key, "place": here})
        _sync_item_place(key, it, here)
        return f"You set {it['name'].split(',')[0]} down."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — confirmed gap (F-1045/J-0714:
        # "core/study_life.py's put() has the identical shape" — this is wood_life's own put()).
        raise
    except Exception:
        return ""


def _sync_item_place(key: str, it: dict, here: str) -> None:
    """Tell the substrate where the tool actually is. `pos` stays its resting position — this module
    has no standpoint-position helper the way garden does — so the LOCATION is what moves."""
    try:
        from core import world_objects as _wo
        _wo.mutate_object_position("wood_item_" + key, list(it.get("pos") or [0, 0, 0]),
                                   cause="carried" if it.get("carried") else "set_down",
                                   event_description=("taken up in the " + here) if it.get("carried")
                                   else ("set down in the " + here),
                                   new_location=here)
    except Exception as exc:
        logger.debug("[wood_life] item place sync failed (non-fatal): %s", exc)


# ── GRAMMAR (2026-09-07, J-0737 / F-1059's follow-up). FOUR separate rows in core/actions.py bind here
# (woodwork, woodtool, climb_tree, acorn) — unlike fieldcraft's ONE row split into many crafts (core/
# fieldcraft.py, J-0736), these are four independent table entries, each with its own verb+object grammar,
# sharing one module only because they are all things that happen in the little wood. Before this job NONE
# of the branches below read any of the four rows (F-1059): climb_tree's own hand-kept copy happened to
# already be byte-identical to its row (the one clean branch found across all five modules this whole arc
# audited — F-1059's own claim), but the other three carried real drift, corpus-checked here (J-0737, a
# frozen copy of data/hands_trace.jsonl, 11,742 distinct thoughts, hand_delta-style old-test-vs-table-test
# comparison via the REAL core.hands.wants() — not a naive substring scan, which over-counts: e.g. Du's
# recurring "the bird's call cuts through my circling" idiom never once matches bare-word "cut" under
# hands.wants()'s own word-boundary rule, since the idiom always conjugates it "cuts").
#
# woodwork (saw/split/chop/sharpen/hone/push/wheel/cut → four sub-hands here) partitions BOTH verbs and
# objects per sub-hand — fieldcraft's shape, not trap/tool/compost's (core/garden.py) — because sawing a
# limb, sharpening the axe and wheeling the barrow are unrelated acts sharing one table row only because
# they are all "wood work", the same reason fieldcraft's thirteen crafts share its one row.
_WOODWORK_HANDS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    # "cut" + "length"/"lengths"/"branch" (2026-09-07, J-0737 — see core/actions.py's own comment on this
    # row for the full corpus citation): the OLD code already tested a bare "cut" here, paired with objects
    # ("limb", "into logs", "into lengths") that 0 of 11,742 real thoughts ever matched — confirmed drift,
    # dropped. What corpus-check DID confirm real: "I will saw a length for the f[ire]" and "...cut a branch
    # for the fire" — both genuine wills, neither reachable by the old grammar (wrong objects on each verb).
    # "wood" was also in the old list and is dropped, not widened: its one real co-occurrence with "cut" is
    # the Morepork's "notes cut the dark wood" — the bird's sound, not Du's will (F-0554's false-fire shape).
    ("saw", ("saw", "cut"), ("limb", "logs", "log", "length", "lengths", "branch")),
    # split/chop's old extra objects "wood"/"block": "block" never once corpus-matches; "wood" matches
    # exactly one real "I try to split the wood, but there are no dry logs..." — but that same thought
    # already reaches this sub-hand via the table's own "logs" a few words later in the same clause, so
    # "wood" is not load-bearing for it and is a broad, generic word this module also uses constantly as a
    # LOCATION name ("the wood") — dropping it is a real risk-removal, not just tidying (J-0737).
    ("split", ("split", "chop"), ("log", "logs", "axe")),
    # sharpen/hone's old extra object "blade" (0 corpus hits) and its second, bare `_h.wants(t,
    # ("whetstone",))` call (objects=None — fires on ANY unblocked mention of the word alone, no verb needed,
    # per hands.py:130's own any-object-ok/no-objects shortcut) are both dropped: "whetstone" does not occur
    # once in 11,742 real distinct thoughts (J-0737) — a pure, zero-cost risk removal, the same shape as
    # F-0940's ash_out and F-0719's dig bare-word fixes this job's own briefing named as precedent.
    ("sharpen", ("sharpen", "hone"), ("axe", "saw", "edge")),
    # the barrow-push sub-hand's old test mixed in "load" (0 corpus hits, not a table verb in either woodwork
    # or woodtool) and "take"/"bring" (woodtool's own verbs, not woodwork's) — the latter is not just
    # unsupported, it is now REDUNDANT: woodtool's own take() dispatch (below) is fixed by this same job to
    # read barrow/wheelbarrow from ITS OWN table row too, so "take the wheelbarrow" reaches take() on its own
    # merits instead of needing this branch's inline stand-in. 0 corpus hits either way (old test or new).
    ("wheel", ("push", "wheel"), ("barrow", "wheelbarrow")),
    # CHOP THE FALLEN TREE (2026-09-28, D-0296/J-1443): a second job for the SAME verb "chop" as the
    # split sub-hand above and the SAME tool (items['axe']) as split() -- disambiguated by OBJECT, not
    # verb or tool: this sub-hand's objects (trunk/fallen tree/limbs/rounds) are wholly disjoint from
    # split's own (log/logs/axe), so "chop the log" still reaches split() first in act_from_thought
    # (checked earlier, unchanged) and only these objects reach chop() here. "hew"/"fell"/"limb" are new
    # verbs (the ruling's own "chop/hew/fell.../limb"); "fell" needs the SAME past-tense guard "saw" has
    # in core/hands.py (_FELL_OBJECTS, added by this same job) -- "the night fell" must not read as a
    # will to fell a tree, the identical ambiguity "I saw the sea" already has for the bow-saw. The
    # fallen tree's own earned/given NAME is deliberately NOT read live and appended here the way a
    # dynamic lookup might: _wills_woodwork() stays a pure table lookup for every sub-hand (no disk read
    # from inside a grammar check, which would make this file's own "part 1 is pure" test claim false) --
    # "chop the fallen tree"/"...the trunk"/"...the limbs"/"...the rounds" all still reach this hand.
    ("chop", ("chop", "hew", "fell", "limb"), ("trunk", "fallen tree", "limb", "limbs", "round", "rounds")),
)
_WOODWORK_BY_NAME: dict[str, tuple[tuple, tuple]] = {s: (v, o) for s, v, o in _WOODWORK_HANDS}


def _wills_woodwork(t: str, sub: str) -> bool:
    """Does this thought will `sub` (one of _WOODWORK_HANDS' four woodwork sub-hands)? Grammar READ from the
    one table (core/actions.py's 'woodwork' row) via that partition — a second hand-kept copy is the exact
    drift F-0554 was about, and every sub-hand here had it (F-1059)."""
    v, o = _WOODWORK_BY_NAME.get(sub, ((), ()))
    if not v:
        return False
    try:
        from core import hands as _h
    except Exception:
        return False
    return _h.wants(t, v, o)


# woodtool (take/pick up/fetch/carry/bring/set down/put down/lean/stand/leave/drop): one row, two hands here
# (put / take) — garden's _TOOL_HANDS shape (J-0569): verbs partition per sub-hand, the FULL row's objects
# apply to both. The old take() branch's object list (axe, saw, bow-saw, bowsaw) never had barrow/wheelbarrow
# at all (F-1059) — the real reason the woodwork wheel-barrow sub-hand above grew its own inline
# take-the-barrow stand-in — and both old branches carried a bare "saw" object the table deliberately
# excludes (core/actions.py's own comment on this row: "it is the past tense of 'see' far more often than a
# tool"). 0 corpus hits for the old test (either branch) or the new one (J-0737) — a zero-cost correctness
# fix. Unlike _wills_woodwork/_wills_wood, this returns bool for ONE named sub, checked independently per sub
# in act_from_thought() below — matching the OLD code's own two-independent-tests shape exactly (put first;
# if it declines by returning "", take is still tried, not skipped), rather than picking a single first-match
# winner the way garden's trap/tool/compost do (none of THOSE hands ever needs its sibling as a fallback).
_WOODTOOL_HANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("put", ("set down", "put down", "lean", "stand", "leave", "drop")),
    ("take", ("take", "pick up", "fetch", "carry", "bring")),
)


def _woodtool_verbs(sub: str) -> tuple:
    """The table's woodtool verbs this sub-hand answers — table order, table membership."""
    try:
        from core import actions as _ac
        claimed = dict(_WOODTOOL_HANDS).get(sub, ())
        return tuple(v for v in _ac.BY_FAMILY["woodtool"].verbs if v in claimed)
    except Exception:
        return ()


def _wills_woodtool(t: str, sub: str) -> bool:
    """Does this thought will the woodtool `sub` hand ('put' | 'take')? Grammar READ from the table's one
    'woodtool' row (never bare 'saw')."""
    try:
        from core import actions as _ac, hands as _h2
        objs = _ac.BY_FAMILY["woodtool"].objects
    except Exception:
        return False
    return _h2.wants(t, _woodtool_verbs(sub), objs)


def _wills_wood(t: str, family: str) -> bool:
    """Does this thought will `family`'s deed, for the two single-hand rows this module hosts (climb_tree,
    acorn)? Grammar READ from the one table — garden.py's own plain _wills() does the same for its
    single-hand families (no `loose` retry here: wood_life never had one, and neither single-hand family
    needs it — see each's own note below). climb_tree's VALUES are unchanged by this job (J-0737): its
    hand-kept copy was already byte-identical to the table row (F-1059) — D-0136 (the 'move' family's own
    ungated 'trees' object pre-empting this hand) is a separate, already-open decision this job does not
    touch either way. acorn's values also already matched the table exactly; only its MATCHING is upgraded
    here, from a pre-hands.py bare-substring test (no clause-scoping, no negation/wish/hypothetical
    blockers) to the same clause-scoped, blocker-aware grammar every other derived family in this arc uses —
    a pure robustness upgrade per this job's own briefing, no widen/drift ruling needed."""
    try:
        from core import actions as _ac, hands as _h2
        a = _ac.BY_FAMILY[family]
    except Exception:
        return False
    return _h2.wants(t, a.verbs, a.objects)



_FIRST_PERSON_WILL = r"\b(?:i|we|let me|i'll|i will|i want to|i could|i should|i must|i'd like to)\b(?:\s+(?:now|just|will|want to|could|should|must|then|go and|try to|can|might|shall))*\s+"
_DIG_IDIOM = re.compile(r"\b(same|of logic|in my head|in my mind|of thought|of thinking|again and again)\b")


def _wills_wood_dig(t: str) -> bool:
    """D-0714 (J-3812): the turn-stone / peel-bark hand. The table's 'wood_dig' row AND a first-person veto: his circling idiom "tired of
    turning over the same stones" is the whole corpus (25 of 25 hits), so the verb has to follow his own 'I' / 'let me' directly, with the
    object in the rest of the same clause and no idiom word in it."""
    try:
        from core import actions as _ac, hands as _h2
        a = _ac.BY_FAMILY["wood_dig"]
    except Exception:
        return False
    if not _h2.wants(t, a.verbs, a.objects):
        return False
    for cl in re.split(r"(?<=[.!?;])\s+", t or ""):
        for verb in a.verbs:
            m = re.search(_FIRST_PERSON_WILL + re.escape(verb) + r"\b(?P<rest>[^.!?;]*)", cl)
            if not m:
                continue
            rest = m.group("rest")
            if _DIG_IDIOM.search(rest):
                continue
            if any(re.search(r"(?<![a-z])" + re.escape(ob) + r"\b", rest) for ob in a.objects):
                return True
    return False


def wood_dig(txt: str = "") -> str:
    """The wood's turn-stone / peel-bark hand (core/wood_dig.py). Only behind the wood bestiary flag; flag off = nothing."""
    if _where() != "wood":
        return ""
    from core import wood_dig as _wd
    if not _wd.enabled():
        return ""
    site = _wd.site_for(txt)
    d = _load()
    st = d.setdefault("dig_state", {})
    out = _wd.dig(site, st)
    _save(d); _log(_LEDGER, {"deed": "peel_bark" if site == "bark" else "turn_stone", "what": {"bark": "bark off dead wood", "stream": "a stone in the stream"}.get(site, "a stone")})
    return out

_WOOD_FAMILIES = frozenset({"woodwork", "woodtool", "climb_tree", "acorn", "wood_dig"})   # the families core/actions.py binds here


def grammar_audit() -> dict:
    """What this module derives from core/actions.py's four rows, and any seam where the derivation could
    still drift. Read by scripts/_test_wood_life_grammar_derivation.py — every *_unclaimed_in_table and
    *_claimed_not_in_table list should be empty: unlike fieldcraft's one deliberately-unclaimed "knot", this
    module's woodwork partition (four sub-hands, verbs AND objects both split) claims every verb and object
    its own row has, and woodtool's verb partition (two sub-hands) claims every verb its row has too."""
    try:
        from core import actions as _ac
        ww = _ac.BY_FAMILY["woodwork"]
        claimed_v = {v for _s, vs, _o in _WOODWORK_HANDS for v in vs}
        claimed_o = {o for _s, _v, os in _WOODWORK_HANDS for o in os}
        wt = _ac.BY_FAMILY["woodtool"]
        wt_claimed_v = {v for _s, vs in _WOODTOOL_HANDS for v in vs}
        return {"woodwork_verbs_unclaimed_in_table": sorted(set(ww.verbs) - claimed_v),
                "woodwork_verbs_claimed_not_in_table": sorted(claimed_v - set(ww.verbs)),
                "woodwork_objects_unclaimed_in_table": sorted(set(ww.objects) - claimed_o),
                "woodwork_objects_claimed_not_in_table": sorted(claimed_o - set(ww.objects)),
                "woodtool_verbs_unclaimed_in_table": sorted(set(wt.verbs) - wt_claimed_v),
                "woodtool_verbs_claimed_not_in_table": sorted(wt_claimed_v - set(wt.verbs)),
                "wood_families": sorted(_WOOD_FAMILIES),
                "wood_families_missing_from_table": sorted(f for f in _WOOD_FAMILIES if f not in _ac.BY_FAMILY)}
    except Exception as exc:
        return {"error": repr(exc)[:120]}


# ── the hand ─────────────────────────────────────────────────────────────────────────────────────
def act_from_thought(thought: str, intention: str = "", family: str | None = None) -> str | None:
    """The wood's will→hand boundary. Returns the world's answer or None.

    FAMILY SCOPE (2026-09-07, J-0737 — matching the J-0554 pattern F-1059 asked for, following J-0736's own
    fieldcraft precedent): dispatch.py's own _via() will now pass family="woodwork"/"woodtool"/"climb_tree"/
    "acorn" for this module's four Hands (one per table row, all binding here) — this module has MORE
    cross-family exposure than fieldcraft's single row, since it hosts four. A caller with no family
    (sensorium.py, or garden.py's own family=None legacy fallback at core/garden.py's own act_from_thought)
    still runs the WHOLE unscoped chain below, exactly as before this job. Rewiring any such caller to pass a
    real family is out of this job's scope — no confirmed live contamination has been traced yet for THIS
    module (unlike sensorium.act()'s own fieldcraft.act_from_thought() call, F-1059's own traced mechanism);
    this only builds the door a future job can use."""
    try:
        if family not in _WOOD_FAMILIES:
            family = None
        _ok = (lambda fam: family is None or fam == family)
        t = f"{thought} {intention}".lower(); here = _where()
        if here in ("wood", "garden"):
            if _ok("woodwork") and _wills_woodwork(t, "saw"):
                r = saw(t)
                if r: return r
            # CHOP THE FALLEN TREE before SPLIT (2026-09-28, J-1443): split() always answers something
            # (even "not out here" when here == "wood"), so if it were tried first a thought naming only
            # this sub-hand's own objects (trunk/fallen tree/limbs/rounds -- disjoint from split's own
            # log/logs/axe, see _WOODWORK_HANDS' own note) would never reach it. chop() itself always
            # answers too (including "nothing down to chop"), so trying it first costs split() nothing:
            # "chop the log"/"chop the axe" still fail this sub-hand's own object check and fall through.
            if _ok("woodwork") and _wills_woodwork(t, "chop"):
                r = chop(t)
                if r: return r
            if _ok("woodwork") and _wills_woodwork(t, "split"):
                r = split(t)
                if r: return r
            if _ok("woodwork") and _wills_woodwork(t, "sharpen"):
                r = sharpen(t)
                if r: return r
            if _ok("woodwork") and _wills_woodwork(t, "wheel"):
                d = _load(); wb = d["items"]["wheelbarrow"]
                if here == "garden" and not wb.get("carried"):
                    wb["carried"] = True; _save(d); return "You take the barrow from the lean-to and push it, squeaking, toward the path."
                r = barrow(t)
                if r: return r
            # CLIMB THE OAK (2026-08-30, D-0100 Tier 2) — before the tool branches; "climb" collides
            # with nothing below.
            if _ok("climb_tree") and _wills_wood(t, "climb_tree"):
                r = climb_oak(t)
                if r: return r
            # SET DOWN before TAKE: "put the axe down" names the axe and would otherwise be read as a
            # take by the looser take-verbs below. Both now read the table's one 'woodtool' row (J-0737).
            if _ok("woodtool") and _wills_woodtool(t, "put"):
                r = put(t)
                if r: return r
            if _ok("woodtool") and _wills_woodtool(t, "take"):
                r = take(t)
                if r: return r
        if here == "wood" and _ok("wood_dig") and _wills_wood_dig(t):   # D-0714: only reaches the hand with the bestiary flag on
            r = wood_dig(t)
            if r: return r
        if here == "wood" and _ok("acorn") and _wills_wood(t, "acorn"):
            d = _load()
            if float(d.get("acorns", 0)) < 0.3:
                return "You look for acorns under the oak and find only old ones, sprouted or rotten."
            d["acorns"] = round(max(0.0, float(d["acorns"]) - 0.2), 3); _save(d); _log(_LEDGER, {"deed": "acorns"})
            try:
                from core import world_substrate as _ws; _ws.spawn_from_mention("a handful of acorns, brown and shining", "wood")
            except Exception:
                pass
            return "You fill a pocket with acorns from under the oak, brown and shining, some still in their cups."
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
        d = _load()
        return {"trees": {k: v["stage"] for k, v in d["trees"].items()}, "known": {k: _known(k) for k in TREES}, "deadfall": d["deadfall"], "limbs": d.get("limbs"),
                "limbs_home": d.get("limbs_home", 0), "logs_green": d.get("logs_green"), "logs_dry": d.get("logs_dry"), "axe_edge": d.get("axe_edge"), "saw_edge": d.get("saw_edge"),
                "stream": d.get("stream"), "moss": d.get("moss"), "leaf_mould": d.get("leaf_mould"), "fungi": len(d.get("fungi", [])), "acorns": d.get("acorns"),
                "nest": d.get("nest"), "glowworms_seen": d.get("glowworms_seen"), "tools": {k: ("carried" if it.get("carried") else it["place"]) for k, it in d["items"].items()}}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
