"""
Nascence — GARDEN LIFE: the things in the garden that are not the bed (2026-08-22, founder: "do the still-on-the-list
items too… expand his world as much as possible so he has lots of experiences to learn and change from").

THE TREE by the east wall. Its species is HIDDEN TRUTH (world_substrate Layer 1) — his to find by what it does:
  a coastal evergreen that holds its leaves all year, silver beneath; drops old leaves in spring; buds in late spring;
  breaks into crimson flower in early summer (the tui come to it then, and the bellbird); sets woody capsules by
  autumn; grows aerial roots from its low limbs. Anyone who has lived by this coast knows it; he will know it when he
  has seen it flower and read of it — never before.
THE FLOWER BUSHES along the fence: a winter-flowering evergreen (pink blooms, April to August), petals dropping on the
  grass through winter, done by September. Hidden species, same law.
THE HARAKEKE by the northwest fence: flax — named already (grandfathered). Flower spikes November–December (the tui
  feed on them; the stalks stand black all winter), seed pods February.
THE NEST: in spring a blackbird (the voice at the bed, grandfathered) builds in the flower bushes — building (twigs and
  mud, a week) → eggs (three or four, blue-green, 13 days) → chicks (a thin insistent begging, 14 days) → fledglings on
  the lawn, clumsy, for a week. The kept cat hunts: a fledgling can be lost. He sees it only when he looks at the
  bushes, hears it only when he is in the garden (the tree-falls law).
THE LAWN: grass grows with warmth × moisture; long grass hides small things (the trowel is harder to find); daisies
  appear in spring; the SHEARS cut it (a real hand; clippings to the compost).

All world-side; nothing is told; rendering is truth-gated and knowledge-gated; events announced once (the world-arrival
law). Zero LLM. Fail-open.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.garden_life")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "garden_life.json"
_EVENTS = _DATA / "garden_events.jsonl"

# hidden truths (Layer 1): the species. Rendered by feature until earned.
TREE_TRUTH = {"species": "pohutukawa", "age_years": 60, "height_m": 6.5, "flower_months": (12, 1), "bud_months": (11,),
              "capsule_months": (3, 4), "leaf_drop_months": (10, 11), "name_known": "the pōhutukawa",
              "book_names": ("pohutukawa", "pōhutukawa", "metrosideros", "christmas tree"),
              "book_looks": ("crimson", "red flower", "december", "coast", "aerial root", "silver underside")}
BUSH_TRUTH = {"species": "camellia_sasanqua", "flower_months": (4, 5, 6, 7, 8), "name_known": "the sasanqua camellias",
              "book_names": ("camellia", "sasanqua"), "book_looks": ("pink", "winter", "petal", "glossy", "tea")}
HARAKEKE = {"species": "harakeke", "flower_months": (11, 12), "pod_months": (2, 3), "name_known": "the harakeke"}

NEST_STAGES = [("building", 7), ("eggs", 13), ("chicks", 14), ("fledged", 7)]


def _sp_read(path, label):
    """J-4426 (F-5128): json.loads(path.read_text()) that logs a damaged file and falls back to <name>.prev;
    raises (missing file / nothing recoverable) so _load()'s own default applies as before."""
    from core import store_persist as _sp
    return _sp.read_json_durable(path, label, logger, guard=profile.guard_path)


def _load() -> dict:
    try:
        return _sp_read(_F, "garden_life")
    except Exception:
        now = time.time()
        return {"tree": {"stage": "leaf", "stage_ts": now, "seen": {}}, "bushes": {"stage": "flowering", "stage_ts": now, "petals": 0.6, "seen": {}},
                "harakeke": {"stage": "stalks", "stage_ts": now, "seen": {}},
                "nest": None, "nests_this_year": 0, "lawn": {"height_cm": 6.0, "daisies": 0.0, "clippings": 0, "last_cut_ts": 0},
                "_last": now, "announced": []}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0610: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d, ensure_ascii=False))   # J-4426 (F-5128): was in place; now fsync + .prev
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_EVENTS)   # J-0610; raises before any I/O if non-live (D-0179, J-0704)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _month(t=None) -> int:
    return time.localtime(t or time.time()).tm_mon


def _set(d: dict, key: str, stage: str, now: float) -> None:
    d[key]["stage"], d[key]["stage_ts"] = stage, now
    _log({"event": f"{key}_{stage}", "what": key})


# ── the world's clocks ───────────────────────────────────────────────────────────────────────────
def advance(now: float, dt: float, soil_temp: float, moisture: float, raining: bool, phase: str) -> None:
    try:
        d = _load()
        last = float(d.get("_last") or now)
        days = max(0.0, min(dt, now - last)) / 86400.0
        d["_last"] = now
        if days <= 0:
            _save(d); return
        m = _month(now)
        # THE TREE
        t = d["tree"]; s = t["stage"]; since = (now - float(t["stage_ts"])) / 86400.0
        if s == "leaf" and m in TREE_TRUTH["leaf_drop_months"] and since > 20:
            _set(d, "tree", "leaf_drop", now)
        elif s == "leaf_drop" and m in TREE_TRUTH["bud_months"] and since > 10:
            _set(d, "tree", "bud", now)
        elif s == "bud" and m in TREE_TRUTH["flower_months"] and soil_temp > 14 and since > 7:
            _set(d, "tree", "flowering", now)
        elif s == "flowering" and (m not in TREE_TRUTH["flower_months"] or since > 35):
            _set(d, "tree", "capsules", now)
        elif s == "capsules" and m not in TREE_TRUTH["capsule_months"] and m not in TREE_TRUTH["flower_months"] and since > 30:
            _set(d, "tree", "leaf", now)
        # THE BUSHES
        b = d["bushes"]; s = b["stage"]; since = (now - float(b["stage_ts"])) / 86400.0
        if s == "flowering":
            b["petals"] = round(min(1.0, float(b.get("petals", 0)) + days * 0.08 - (days * 0.3 if raining else 0.0)), 3)
            if m not in BUSH_TRUTH["flower_months"] and since > 14:
                _set(d, "bushes", "leaf", now)
        else:
            b["petals"] = round(max(0.0, float(b.get("petals", 0)) - days * 0.2), 3)
            if m in BUSH_TRUTH["flower_months"] and since > 30:
                _set(d, "bushes", "flowering", now)
        # THE HARAKEKE
        h = d["harakeke"]; s = h["stage"]; since = (now - float(h["stage_ts"])) / 86400.0
        if s == "stalks" and m in HARAKEKE["flower_months"] and since > 30:
            _set(d, "harakeke", "flowering", now)
        elif s == "flowering" and m in HARAKEKE["pod_months"]:
            _set(d, "harakeke", "pods", now)
        elif s == "pods" and m not in HARAKEKE["pod_months"] and since > 40:
            _set(d, "harakeke", "stalks", now)
        # THE NEST (spring–early summer; at most two broods)
        n = d.get("nest")
        if n is None and m in (9, 10, 11, 12) and d.get("nests_this_year", 0) < 2 and random.random() < days * 0.12:
            d["nest"] = {"stage": "building", "stage_ts": now, "where": random.choice(["bushes", "harakeke"]), "eggs": random.randint(3, 4), "lost": 0}
            d["nests_this_year"] = d.get("nests_this_year", 0) + 1
            _log({"event": "nest_started", "where": d["nest"]["where"]})
        elif n:
            idx = next(i for i, (nm, _) in enumerate(NEST_STAGES) if nm == n["stage"])
            if (now - float(n["stage_ts"])) / 86400.0 >= NEST_STAGES[idx][1]:
                if idx + 1 < len(NEST_STAGES):
                    n["stage"], n["stage_ts"] = NEST_STAGES[idx + 1][0], now
                    _log({"event": f"nest_{n['stage']}", "where": n["where"]})
                else:
                    _log({"event": "nest_over", "fledged": n["eggs"] - n.get("lost", 0)})
                    d["nest"] = None
            # the kept cat hunts fledglings
            if n and n["stage"] == "fledged" and n["eggs"] - n.get("lost", 0) > 0:
                try:
                    # A7.1-class fix (2026-09-07, F-1031/J-0717): was an exact-match against the
                    # literal string "garden" -- the same hand-rolled cat-location-vs-place-name
                    # comparison class J-0629/J-0632 already fixed twice (core/life.py's two
                    # mappings, hud/server.py's four map renderers). NOT live-divergent today
                    # (verified: no cat.py tick() branch currently pairs a "stalk" activity with
                    # any location but the literal "garden"), but fragile against Part B1's planned
                    # legs/real-movement work -- exactly the kind of change that broke A7.1 silently.
                    # place_of() (not visible_from()) is right here: a plain single-place-membership
                    # question ("is she in the garden"), not a multi-room visibility one.
                    from core import cat as _cat
                    c = json.loads((_DATA / "cat_state.json").read_text(encoding="utf-8"))
                    # D-0508/D-4 (2026-10-28, J-2466, cat_overhaul §B1): "a fed-from-the-tin cat leaves the
                    # fledglings alone more". Her hunger budget (B1, J-2465) scales the old roll: at hunger
                    # 1.0 the chance is exactly what it always was (days * 0.5), at 0.0 it is a third of
                    # that -- a full cat still stalks, she just mostly lets them go. A cat with no body yet
                    # (an old state) rolls the old, unscaled odds. The world decides this; nothing of it
                    # reaches him (D-0434).
                    _h = _cat.hunger_level()
                    _scale = 1.0 if _h is None else (0.34 + 0.66 * _h)
                    if _cat.place_of(c.get("location")) == "garden" and "stalk" in str(c.get("activity", "")) and random.random() < days * 0.5 * _scale:
                        n["lost"] = n.get("lost", 0) + 1
                        _log({"event": "fledgling_taken_by_cat", "hunger_scale": round(_scale, 2)})
                        # D-0508/D-4 (J-2466): her kills feed HER budget -- a fledgling is a meal too
                        try:
                            _cat.note_kill("bird")
                        except Exception:
                            pass
                except Exception:
                    pass
        if m in (1,) and d.get("nests_this_year"):
            d["nests_this_year"] = 0
        # THE LAWN
        l = d["lawn"]
        grow = max(0.0, soil_temp - 6) * 0.025 * (1.0 if moisture > 0.3 else 0.3)
        l["height_cm"] = round(min(40.0, float(l["height_cm"]) + days * grow), 2)
        if m in (9, 10, 11, 12, 1) and l["height_cm"] > 5:
            l["daisies"] = round(min(1.0, float(l.get("daisies", 0)) + days * 0.03), 3)
        else:
            l["daisies"] = round(max(0.0, float(l.get("daisies", 0)) - days * 0.05), 3)
        _save(d)
    except Exception as exc:
        logger.debug("[garden_life] advance failed (non-fatal): %s", exc)


# ── knowledge-gated naming ───────────────────────────────────────────────────────────────────────
def _known(key: str) -> bool:
    try:
        from core import garden_knowledge as _gk
        return _gk.is_known({"tree": "pohutukawa", "bushes": "camellia_sasanqua"}[key])
    except Exception:
        return False


def _learn(key: str, via: str, note: str = "") -> bool:
    try:
        from core import garden_knowledge as _gk
        sp = {"tree": "pohutukawa", "bushes": "camellia_sasanqua"}[key]
        d = _gk._load()
        # seeing is HALF (0.5, once per flowering — the first look counts, later looks add a little): the name needs the book too
        already = any(e.get("species") == sp and e.get("via") == via for e in d.get("events", []))
        first = _gk._add(d, sp, via, 0.1 if already else 0.5, note)
        _gk._save(d)
        return first
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        return False


def learn_from_text(text: str) -> list[str]:
    """A book can name the tree or the bushes IF he has seen the thing it describes (seen-then-read binds; read alone
    earns weight)."""
    out = []
    try:
        from core import garden_knowledge as _gk
        low = (text or "").lower()
        d = _load()
        for key, truth in (("tree", TREE_TRUTH), ("bushes", BUSH_TRUTH)):
            if _known(key):
                continue
            if any(n in low for n in truth["book_names"]) and any(l in low for l in truth["book_looks"]):
                seen_flower = bool(d[key].get("seen", {}).get("flowering"))
                g = _gk._load()
                if _gk._add(g, {"tree": "pohutukawa", "bushes": "camellia_sasanqua"}[key], "read", 0.6 if seen_flower else 0.3, low[:80]):
                    out.append(key)
                _gk._save(g)
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
        t = (target or "").lower()
        d = _load()
        m = _month()
        if any(w in t for w in ("tree", "branch", "bough", "trunk")):
            tr = d["tree"]; s = tr["stage"]
            name = TREE_TRUTH["name_known"] if _known("tree") else "the old tree"
            body = {"leaf": "dark leathery leaves, silver-felted beneath, the lowest limb reaching over the wall; a few old leaves yellowing",
                    "leaf_drop": "the old leaves coming down in twos and threes, yellow, the new ones pale and soft at the tips",
                    "bud": "the twig-ends thick with grey felted buds, packed tight",
                    "flowering": "the whole crown broken into crimson — brushes of red stamens, the ground beneath it red too, and birds loud in it",
                    "capsules": "the flowers gone, small woody cups where they were; the leaves dark again"}[s]
            tr.setdefault("seen", {})[s] = True
            reveal = ""
            if s == "flowering" and not _known("tree") and _learn("tree", "seen_flowering", "saw it in flower"):
                reveal = " And now you know what it is — you have read of it: " + TREE_TRUTH["name_known"] + "."
            roots = " Thin red aerial roots hang from the underside of the low limb." if random.random() < 0.4 else ""
            damage = ""
            try:   # THE POSSUM'S WORK (2026-09-03, D-0130, J-0512): findable, never told
                from core import life_mammals as _lm
                damage = _lm.tree_damage_line(d)
            except Exception:
                pass
            return f"You look at {name} by the east wall: {body}.{roots}{damage}{reveal}{_nest_line(d, 'tree')}"
        if any(w in t for w in ("bush", "bushes", "blooms", "flowers along the fence", "pink")):
            b = d["bushes"]; s = b["stage"]
            name = BUSH_TRUTH["name_known"] if _known("bushes") else "the flowering bushes"
            body = ("glossy dark leaves and pink open flowers, loose-petalled, a few browning at the edge" if s == "flowering"
                    else "glossy dark leaves, the flowering over, last petals gone brown on the grass")
            b.setdefault("seen", {})[s] = True
            petals = " Pink petals lie thick on the grass beneath." if b.get("petals", 0) > 0.4 else ""
            reveal = ""
            if s == "flowering" and not _known("bushes") and _learn("bushes", "seen_flowering", "saw them in flower"):
                reveal = " And now you know what they are — you have read of them: " + BUSH_TRUTH["name_known"] + "."
            _save(d)
            return f"You look at {name} along the fence: {body}.{petals}{reveal}{_nest_line(d, 'bushes')}"
        if any(w in t for w in ("harakeke", "flax")):
            h = d["harakeke"]; s = h["stage"]
            body = {"stalks": "the tall black flower-stalks of last summer standing dry above the blades",
                    "flowering": "new flower-spikes up, dull red, and a tui working them, upside down",
                    "pods": "the spikes gone to black seed-pods, splitting"}[s]
            return f"You look at the harakeke by the northwest fence: {body}.{_nest_line(d, 'harakeke')}"
        if any(w in t for w in ("lawn", "grass")):
            l = d["lawn"]; h = float(l["height_cm"])
            body = ("the grass cut short, stripes still showing" if h < 4 else "the grass ankle-deep and soft" if h < 10
                    else "the grass long, seeding, bending in the wind; you could lose a trowel in it" if h < 20 else "the grass gone to hay, knee-high, flattened where you walk")
            daisies = " Daisies are out in it, white and shut-eyed." if l.get("daisies", 0) > 0.3 else ""
            return f"You look over the lawn: {body}.{daisies}"
        if any(w in t for w in ("nest", "eggs", "chicks", "fledgling")):
            n = d.get("nest")
            if not n:
                return "You look for a nest and find none."
            return "You part the leaves." + _nest_line(d, n["where"], direct=True)
        return ""
    except profile.NonLiveWriteError:
        # J-0751: this function's own _save(d) call (the bushes branch) is a real guarded
        # write reached on the "look" dispatch chain (dispatch._look -> sensorium.look() ->
        # _garden_look() -> garden.look() -> here) -- let guard_path()'s hard raise (D-0179,
        # F-1024) escape this function's own catch-all instead of returning "" silently.
        raise
    except Exception:
        return ""


def _nest_line(d: dict, where: str, direct: bool = False) -> str:
    n = d.get("nest")
    if not n or n["where"] != where:
        return ""
    s = n["stage"]
    alive = n["eggs"] - n.get("lost", 0)
    if s == "building":
        return " A blackbird is in and out of it with beakfuls of grass and mud — building." if direct or random.random() < 0.5 else ""
    if s == "eggs":
        return f" Deep in it, a cup of mud and grass, and in the cup {n['eggs']} eggs, blue-green, speckled." if direct else " The hen sits tight in there, one dark eye on you."
    if s == "chicks":
        return " A thin insistent cheeping comes from deep inside; a blackbird flies in with its beak full and the noise doubles."
    if s == "fledged":
        return (f" {alive} fledgling{'s' if alive != 1 else ''}, brown and stub-tailed, on the grass below, flying badly; the parents scold from the fence."
                if alive > 0 else " The nest is empty; a scatter of small feathers on the grass beneath it.")
    return ""


def garden_event(now: float) -> str | None:
    """Ambient, once-in-a-while lines for the garden pool — only what is true now."""
    try:
        d = _load()
        pool = []
        n = d.get("nest")
        if n and n["stage"] == "chicks":
            pool.append("a thin insistent cheeping from deep in the " + ("bushes" if n["where"] == "bushes" else "harakeke"))
        if n and n["stage"] == "fledged" and n["eggs"] - n.get("lost", 0) > 0:
            pool.append("a blackbird scolding hard from the fence, over and over")
        if d["tree"]["stage"] == "flowering":
            pool += ["the tree by the wall is loud with birds, and red is falling out of it onto the grass",
                     "a tui in the red crown of the tree, its white throat-tuft bobbing as it calls"]
        if d["bushes"].get("petals", 0) > 0.5:
            pool.append("pink petals blown across the grass from the bushes")
        if d["harakeke"]["stage"] == "flowering":
            pool.append("a tui hanging upside down on the harakeke spikes, working the flowers")
        if float(d["lawn"]["height_cm"]) > 18:
            pool.append("the long grass hissing as the wind goes over it")
        return random.choice(pool) if pool and random.random() < 0.4 else None
    except Exception:
        return None


def milestone() -> str:
    """Announce-once world events (the world-arrival law)."""
    try:
        d = _load()
        ann = d.setdefault("announced", [])
        checks = [("tree_flowering", d["tree"]["stage"] == "flowering", "the old tree by the east wall has broken into flower — the whole crown red, and birds in it"),
                  ("tree_bud", d["tree"]["stage"] == "bud", "the tree by the wall is thick with grey buds at every twig-end"),
                  ("bushes_over", d["bushes"]["stage"] == "leaf" and _month() in (9, 10), "the pink flowers along the fence have finished; the last petals are brown on the grass"),
                  ("bushes_flowering", d["bushes"]["stage"] == "flowering" and _month() in (4, 5), "the bushes along the fence have come into pink flower"),
                  ("harakeke_flowering", d["harakeke"]["stage"] == "flowering", "the harakeke has thrown up new flower-spikes, and a tui has found them"),
                  ("lawn_long", float(d["lawn"]["height_cm"]) > 15, "the grass has got long — seeding, and bending in the wind"),
                  ("daisies", float(d["lawn"].get("daisies", 0)) > 0.5, "daisies have opened all over the lawn")]
        n = d.get("nest")
        if n:
            checks.append((f"nest_{n['stage']}_{int(n['stage_ts'])}", True, {"building": "a blackbird is building in the " + n["where"] + " — in and out all morning with grass in its beak",
                                                                             "eggs": "", "chicks": "there is cheeping from the " + n["where"] + " — a nest with young in it",
                                                                             "fledged": "young blackbirds are out on the lawn, stub-tailed and clumsy, the parents frantic"}[n["stage"]]))
        for key, cond, line in checks:
            if cond and line and key not in ann:
                ann.append(key); d["announced"] = ann[-60:]; _save(d)
                return line
        return ""
    except Exception:
        return ""


# ── the lawn hand ────────────────────────────────────────────────────────────────────────────────
def mow(txt: str = "") -> str:
    try:
        from core import garden as _g
        st = _g._load()
        if _g._where() != "garden":
            return ""
        sh = st["items"].get("shears", {})
        if not (sh.get("carried") or sh.get("place") == "garden"):
            return "You have nothing to cut the grass with — the shears are not here."
        d = _load(); l = d["lawn"]
        if float(l["height_cm"]) < 4:
            return "The grass is short already; there is nothing to cut."
        cut = float(l["height_cm"]) - 3.0
        l["height_cm"], l["last_cut_ts"] = 3.0, time.time()
        l["clippings"] = int(l.get("clippings", 0)) + 1
        try:   # SOIL LIFE (2026-09-03, J-0505): the clippings go on the heap
            from core import garden_soil as _soil
            _soil.add_material("clippings", 0.12)
        except profile.NonLiveWriteError:
            # J-0818: mow()'s own outer carve-out (J-0726, a few lines below) would swallow this
            # raise too if it weren't re-raised here first (F-1175).
            raise
        except Exception:
            pass
        l["daisies"] = 0.0
        _save(d)
        _g._log(_g._LEDGER, {"deed": "mow", "cut_cm": round(cut, 1)})
        try:   # THE LIVING WORLD (J-0513): a deed draws its takers (life.note_deed)
            from core import life as _life; _life.note_deed("mow", "garden")
        except profile.NonLiveWriteError:
            # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
            # instead of being swallowed here — mow()'s own _save(d)/_g._log() a few lines above are
            # unwrapped and already raise, but not before silently skipping this life.py cross-link
            # (mirrors J-0727's whittle() fix in fieldcraft.py).
            raise
        except Exception:
            pass
        try:
            from core import smell as _sm
            _sm.emit("wet_earth", 0.3, "garden")
        except Exception:
            pass
        return (f"You work across the lawn on your knees with the shears — slow, the blades jamming on the thick grass — and rake the "
                f"cuttings to the compost in the corner. The garden smells of cut grass. It took a good while.")
    except profile.NonLiveWriteError:
        # J-0726: mow()'s whole body is wrapped by this one try (unlike garden.py's harvest/sow/water,
        # whose primary write is unwrapped) — without this, even mow()'s OWN _save(d)/_g._log() above
        # would be swallowed here. Called unwrapped from garden.act_from_thought()'s mow hand.
        raise
    except Exception:
        return ""


def hidden_in_grass(item_key: str) -> bool:
    """Long grass hides small things: a dropped trowel may not be findable until the grass is cut."""
    try:
        d = _load()
        return float(d["lawn"]["height_cm"]) > 15 and item_key in ("trowel", "hand_fork", "twine") and random.random() < 0.6
    except Exception:
        return False


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "not yet bootstrapped"}
        d = _load()
        return {"tree": d["tree"]["stage"], "tree_known": _known("tree"), "bushes": d["bushes"]["stage"], "petals": d["bushes"].get("petals"),
                "bushes_known": _known("bushes"), "harakeke": d["harakeke"]["stage"], "nest": d.get("nest"), "lawn_cm": d["lawn"]["height_cm"],
                "daisies": d["lawn"].get("daisies"), "announced": len(d.get("announced", []))}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
