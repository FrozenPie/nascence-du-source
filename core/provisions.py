"""
Nascence — PROVISIONS: the larder the previous occupant left (2026-08-22, founder: "make sure he has a good store of
some goods — matches, soap, etc — that the previous occupant had left. All of these things need to be world objects,
with history and all that").

Every box, bar, tin and bottle is a WORLD OBJECT: a substrate entity (hidden truth + biography + his observations)
with a POSITION in the study's cupboard (shelf_east) — the same kind of thing as the driftwood and the trowel. The
study's running counts (matches, soap, candles, oil, tea, paper, ink) are VIEWS over these objects: when he strikes a
match the open box loses one; when a box is empty it is an empty box (kept; he may throw it on the fire); when the
carrier brings more, new objects with their own biography ("brought up by the carrier on …") join the shelf.

The stock as found: generous but finite — the previous occupant laid in for a winter and then left.
Zero LLM. Fail-open. Additive: study_life reads/writes through sync(); if this module fails, the counts still work.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.provisions")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "provisions.json"
_LOG = _DATA / "provisions_log.jsonl"

# kind -> (unit name, per-object quantity, study_life store key, unit of the store)
KINDS = {
    "matches": ("a box of matches", 50, "matches", "matches"),
    "soap": ("a bar of yellow soap", 1.0, "soap", "bars"),
    "candles": ("a box of six candles", 6, "candles", "candles"),
    "oil": ("a four-pint tin of lamp oil", 1.0, "oil_tin", "tins"),
    "tea": ("a tin of tea", 25, "tea_leaves", "pots"),
    "paper": ("a pad of writing paper", 40, "paper", "sheets"),
    "ink": ("a bottle of ink", 1.0, "ink", "bottles"),
    "string": ("a ball of string", 1, "string", "balls"),
    "whetstone": ("a whetstone in a leather sleeve", 1, "whetstone", ""),
    "lamp_glass": ("a spare lamp glass wrapped in newspaper", 1, "lamp_glass_spare", ""),
    "kindling": ("a bundle of kindling, tied", 0.5, "kindling", ""),
    "knife": ("a pocket knife, bone-handled, the blade worn thin", 1, "knife", ""),
    "flint": ("a flint and a steel striker in a twist of oilcloth", 1, "flint", ""),
    # PRACTICAL SCHOOL (2026-09-05, J-0626, D-0159 §4): four new kinds, added the same way as every
    # kind above — a real object, a place, a quantity, a history. "rope" is fractional (metres, like
    # tea/paper/ink); the other three are durable single-presence objects (like whetstone/knife/flint)
    # tracked as booleans in sync() below, not fractions.
    "rope": ("a 20 m coil of rope", 20, "rope_m", "metres"),
    "tinder_tin": ("a tin kept for tinder", 1, "tinder_tin", ""),
    "hand_lens": ("a hand lens in a brass ring", 1, "hand_lens", ""),
    "measuring_stick": ("a yard-long marked stick", 1, "measuring_stick", ""),
    # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504 released J-0628; plan §4): the two larder
    # objects that step names — a pocket compass (durable, boolean in sync() like the knife) and bandage
    # linen (fractional, "used up", like soap; the first-aid practicals that spend it are a later rung).
    # The fire-drill kit is NOT a provision: it is a made thing (fieldcraft.whittle()). Hand-line and
    # hook stay parked until the life engine can answer fish presence truthfully (plan §4).
    "compass": ("a pocket compass in a brass case", 1, "compass", ""),
    "bandage_linen": ("a roll of bandage linen", 1.0, "bandage_linen", "rolls"),
    # THE CAT'S FOOD (2026-09-07, D-0163/D-4, J-0719): the real resource A3's audit found missing
    # entirely ("no cat food, fish, milk, or scraps exist in data/provisions.json") — the same class
    # of conjured-meal leak the fire chain (T-0049) already closed for matches. Unlike every kind
    # above, this one is NOT part of the previous occupant's winter larder (nobody here had a cat
    # before she turned up in 06-24) — it does not appear in _bootstrap() or _seed_new_kinds() below,
    # so a fresh house genuinely starts at zero, exactly matching the audit finding, and the only way
    # any ever arrives is a real acquisition: core/supply.py's carrier line (D-4's own build order).
    # qty=4 ("feeds") per tin: scarce on purpose — one order does not cover a 14-day carrier cycle at
    # anything like her real feeding rate, so the carrier loop and the hunting fallback (D-0163's own
    # founder addendum, J-0700) both stay genuinely load-bearing rather than this becoming one more
    # infinite resource.
    "cat_food": ("a tin of fish for the cat", 4, "cat_food", "feeds"),
    # THE OTHER REAL SOURCE (2026-09-07, D-0163/D-4, J-0732/F-1055): docs/staged/cat_overhaul.md's own §B1
    # named "fish he catches" as a second real food source, alongside the carrier's tin above -- J-0719 only
    # ever built the one. Not part of _bootstrap()/_seed_new_kinds() for the same reason cat_food isn't: it
    # is not a laid-in store, it is the direct product of a real deed (core.shore_life.catch_fish(), gated on
    # the tide/weather like every other shore hand) -- a fresh house starts at zero, and the only way any ever
    # arrives is Du actually going and catching one. qty=1 ("feeds"), not cat_food's 4: a single fresh fish is
    # one meal, not a tin that lasts several -- scarcer per-catch than the carrier's own tin, on purpose, so
    # it stays a real fallback (core.cat._feed_source() tries cat_food first) rather than replacing either the
    # carrier loop or D-0163's own hunting fallback (J-0700) as the load-bearing source. Known, deliberate
    # simplification carried over from every other kind in this dict at the time this comment was first
    # written: no spoilage/expiry was modelled here (matches/candles/tea don't decay either) even though a
    # raw fish realistically would. UPDATE (2026-09-08, J-0755/F-1079): closed, but narrowly -- NOT by adding
    # a generic expiry concept here (stock()/consume()/add() below are unchanged and stay load-bearing for
    # every OTHER kind exactly as before); instead core.cat.SHORE_FISH_SPOIL_H/_shore_fish_ready() reads this
    # kind's own object `history[0]["ts"]` (the real catch time) at the one place it is actually spent, via
    # the new discard_if_stale() below -- a function nothing else in this file calls. cat_food and every
    # other kind here remain exactly as durable as they always were.
    "shore_fish": ("a fish, caught fresh at the shore", 1, "shore_fish", "feeds"),
    # REAL FOOD, THE REST OF IT (2026-10-28, cat_overhaul §B1 / §4 D-4, D-0508, J-2466): the two sources
    # §B1 named that J-0719/J-0732 never built. Same shape as cat_food/shore_fish exactly: NOT laid in by
    # the previous occupant (nobody here had a cat), so neither appears in _bootstrap()/_seed_new_kinds()
    # and a fresh house starts at zero; the only way any ever arrives is a real acquisition.
    #   milk   -- a standing carrier-catalogue line (core/supply.py GOODS; D-0276: the carrier stays the
    #             only ongoing supply). A SAUCER item: qty=4 ("saucers") per jug, a lighter meal than the
    #             tin (core.cat.MEAL_HUNGER) that mostly answers her thirst. Milk SPOILS, like shore_fish and
    #             unlike every other kind here: core.cat.MILK_SPOIL_H / _milk_ready() reads each jug's own
    #             history[0]["ts"] (the delivery) via discard_if_stale() at the one place it is spent --
    #             the same narrow pattern J-0755 chose for the fish, so stock()/consume()/add() stay
    #             exactly the shared machinery they were for every other kind.
    #   scraps -- what is left of a meal, put by for her: qty=1 ("feeds"), a small meal. NOT a carrier line
    #             (the carrier brings nothing for him to eat -- Travis's own book, §V). Credited only by a
    #             real event through core.cat.give_scraps() -> add_found(); Du has no modelled meal of his
    #             own anywhere in the repo (checked again this job: the only thing he takes is tea,
    #             core/actions.py "tea"), so as built the kind has a complete spend path and an honest
    #             credit hook with no live producer yet -- see J-2466's finding, addressed to Travis.
    "milk": ("a jug of milk, stoppered with a cork", 4, "milk", "saucers"),
    "scraps": ("a twist of paper with scraps put by for the cat", 1, "scraps", "feeds"),
}
_CUPBOARD = [4.1, 2.2, 0.2]     # study.json shelf_east — the cupboard under the east shelf
_PLURAL = {"matches": ("box of matches", "boxes of matches"), "soap": ("bar of soap", "bars of soap"), "candles": ("box of candles", "boxes of candles"),
           "oil": ("tin of lamp oil", "tins of lamp oil"), "tea": ("tin of tea", "tins of tea"), "paper": ("pad of paper", "pads of paper"),
           "ink": ("bottle of ink", "bottles of ink"), "string": ("ball of string", "balls of string"), "whetstone": ("whetstone", "whetstones"),
           "lamp_glass": ("spare lamp glass", "spare lamp glasses"), "kindling": ("bundle of kindling", "bundles of kindling"),
           "knife": ("pocket knife", "pocket knives"), "flint": ("flint and steel", "flints and steels"),
           "rope": ("coil of rope", "coils of rope"), "tinder_tin": ("tinder tin", "tinder tins"),
           "hand_lens": ("hand lens", "hand lenses"), "measuring_stick": ("measuring stick", "measuring sticks"),
           "compass": ("pocket compass", "pocket compasses"), "bandage_linen": ("roll of bandage linen", "rolls of bandage linen"),
           "cat_food": ("tin of fish for the cat", "tins of fish for the cat"),
           "shore_fish": ("fish caught at the shore", "fish caught at the shore"),
           "milk": ("jug of milk", "jugs of milk"),
           "scraps": ("twist of scraps for the cat", "twists of scraps for the cat")}
_BIOS = {
    "matches": ["bought in town, a dozen boxes at a time; the label foxed", "the previous occupant's; one corner chewed by a mouse",
                "a fresh box, the striker unworn", "half a box; someone counted them once in pencil on the lid"],
    "soap": ["cut from a long bar with a knife; the cut edge still sharp", "gone hard and cracked with age, but soap", "wrapped in a scrap of newspaper from a year ago"],
    "candles": ["tallow, a little bent from a warm day", "white, still in their paper, never opened"],
    "oil": ["the tin dented where it was dropped coming up the path", "full, the cap stiff with old oil"],
    "tea": ["a tin with a ship on the lid, the hinge loose", "the leaves gone a little dusty; they will still draw"],
    "paper": ["the top sheet yellowed, the rest white", "a pad with a list in someone else's hand on the first page — 'oil, nails, string'"],
    "ink": ["black, the label stained", "blue-black, the cork dry"],
    "string": ["sun-faded on the outside turns", "new, still in its paper band"],
    "whetstone": ["worn into a hollow by the axe that lived here before him"],
    "lamp_glass": ["never used, wrapped against the day the other breaks"],
    "kindling": ["split by someone careful, the pieces all of a length"],
    "knife": ["the previous occupant's; initials scratched into the bone, not his"],
    "flint": ["from before there were matches in the house; the steel polished by a thumb"],
    "rope": ["tarred and coiled in three loops, heavier and stiffer than the garden twine"],
    "tinder_tin": ["a flat tin, the lid a tight fit, kept for keeping tinder dry"],
    "hand_lens": ["the glass scratched at one edge but strong; it folds into a pigskin case"],
    "measuring_stick": ["a straight hazel stick, notches already cut off in feet by whoever had this room before"],
    "compass": ["a pocket compass in a brass case, the lid sprung; the needle swings and settles, pointing where it points"],
    "bandage_linen": ["a roll of clean linen torn to width for bandages, tied with a thread, never yet needed"],
    "cat_food": ["bought specially since she came — nothing here was ever laid in for a cat before her",
                 "the last tin of a run the carrier finally had in; the label a faded fish"],
    "shore_fish": ["caught off the shelf's edge on a handline and carried up to the larder, still stiff and silver",
                   "a fish off the shore, brought home the day it was caught"],
    "milk": ["a stoneware jug with a cork in its neck, the milk still cool from the carrier's crate",
             "a jug of milk wrapped in a wet cloth against the walk up; it will not keep long",
             "milk for the cat, the jug's lip chipped, the cork pushed in hard"],
    "scraps": ["the end of a meal, folded into a twist of paper and put by for her",
               "scraps kept back for the cat, the paper gone translucent where they lie"],
}


def _load() -> dict:
    try:
        return json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_ro() -> dict:
    """J-2417 (F-3117): READ-ONLY cached twin of _load() (same dict while mtime/size unchanged). SHARED result:
    never mutate it. Mutating paths (consume/add/_ensure) keep _load()."""
    try:
        from core import store_persist as _sp
        return _sp.load_json_cached(_F)
    except Exception:
        return {}


def _save(d: dict) -> bool:
    """Returns True iff `d` was actually confirmed written to disk, False iff the write raised (F-1136,
    same shape as _write_axiom's own fix, J-0763). Previously this returned None unconditionally, so
    every caller (consume(), add(), discard_if_stale(), open_kindling_bundle()) had no way to tell "the
    shelf really changed" from "the write silently failed and the old file on disk is still what's
    really there" -- and several of them reported a completion signal (a truthy kind string, a non-empty
    id list, True) to a durable-state consumer regardless of which one had actually happened. guard_path()
    itself still runs OUTSIDE this try (unchanged) so a non-live NonLiveWriteError keeps propagating
    straight to this function's own caller, exactly as before."""
    path = profile.guard_path(_F)   # J-0610: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as exc:
        logger.debug("[provisions] _save failed: %s", exc)
        return False


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-0610; raises before any I/O if non-live (D-0179, J-0704)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _bootstrap() -> dict:
    """The larder as found: laid in for a winter by whoever was here before."""
    rng = random.Random("provisions|2026-08-22")
    now = time.time()
    stock = [("matches", 6), ("soap", 4), ("candles", 2), ("oil", 2), ("tea", 2), ("paper", 2), ("ink", 2), ("string", 1), ("whetstone", 1), ("lamp_glass", 1), ("kindling", 3), ("knife", 1), ("flint", 1)]
    objs = []
    for kind, n in stock:
        unit, qty, _, _ = KINDS[kind]
        for i in range(n):
            age = rng.randint(40, 400)
            q = qty
            if kind == "matches" and i == 0: q = rng.randint(12, 30)        # the open box
            if kind == "oil" and i == 0: q = 0.55                           # the tin in use
            if kind == "soap" and i == 0: q = 0.6
            objs.append({"id": f"prov_{kind}_{rng.randrange(16**4):04x}", "kind": kind, "name": unit, "qty": q, "full_qty": qty,
                         "pos": [round(_CUPBOARD[0] + rng.uniform(-0.35, 0.35), 2), round(_CUPBOARD[1] + rng.uniform(-0.3, 0.3), 2), round(_CUPBOARD[2] + rng.uniform(0, 0.5), 2)],
                         "place": "study", "origin": "previous_occupant", "empty": False,
                         "history": [{"ts": now - age * 86400, "event": rng.choice(_BIOS[kind])}]})
    return {"objects": objs, "born": now}


# PRACTICAL SCHOOL — NEW OBJECTS REACHING AN ALREADY-RUNNING LARDER (2026-09-05, J-0626, D-0159 §4):
# _bootstrap() above only ever fires once, the first time provisions.json does not yet exist — a kind
# added to KINDS after that first boot (this session) would never reach an already-initialised save,
# the same problem core/inventory.py's sync_items() solves for study_life/wood_life/garden's keyed item
# dicts. provisions' objects are a per-kind LIST (not a {key: item} dict) so sync_items() doesn't fit
# directly; this is its list-shaped twin. Idempotent via d["seeded_kinds"] (one marker, fired once,
# ever — never re-fired even if every object of that kind is later consumed or lost) so these arrive
# exactly once, the first time _ensure() runs after the restart that ships this code: present from the
# day of the build, like everything else in the house, never spawned in response to a lesson or a deed.
_NEW_KINDS_2026_09_05 = [
    ("rope", "rope", 1, "previous_occupant", "a coil left in the corner of the cupboard, tarred, twenty metres of it"),
    ("tinder_tin", "tinder_tin", 1, "previous_occupant", "a flat tin kept for tinder, the lid a tight fit"),
    ("flint_spare", "flint", 1, "previous_occupant", "a second flint and steel, wrapped separately from the first, kept back for when it wears through"),
    ("hand_lens", "hand_lens", 1, "previous_occupant", "a small hand lens in a brass ring, folded into a pigskin case"),
    ("measuring_stick", "measuring_stick", 1, "previous_occupant", "a straight hazel stick a yard long, notches already cut off in feet"),
]


# PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504): the second batch, same mechanism, same
# once-ever markers. Present from the day of the build; never spawned in answer to a lesson.
_NEW_KINDS_2026_10_28 = [
    ("compass", "compass", 1, "previous_occupant", "a pocket compass in a brass case, found at the back of the cupboard behind the tins, the lid sprung"),
    ("bandage_linen", "bandage_linen", 1, "previous_occupant", "a roll of clean linen torn to bandage width and tied with a thread, laid in against a cut that never came"),
]
_ALL_NEW_KINDS = _NEW_KINDS_2026_09_05 + _NEW_KINDS_2026_10_28


def _seed_new_kinds(d: dict) -> bool:
    seeded = d.setdefault("seeded_kinds", [])
    changed = False
    for marker, kind, n, origin, note in _ALL_NEW_KINDS:
        if marker in seeded:
            continue
        seeded.append(marker)
        unit, qty, _, _ = KINDS[kind]
        for _i in range(n):
            oid = f"prov_{kind}_{random.randrange(16**4):04x}"
            d["objects"].append({"id": oid, "kind": kind, "name": unit, "qty": qty, "full_qty": qty,
                                 "pos": [round(_CUPBOARD[0] + random.uniform(-0.35, 0.35), 2), round(_CUPBOARD[1] + random.uniform(-0.3, 0.3), 2), round(_CUPBOARD[2] + random.uniform(0, 0.5), 2)],
                                 "place": "study", "origin": origin, "empty": False,
                                 "history": [{"ts": time.time(), "event": note}]})
        changed = True
        _log({"event": "seeded", "kind": kind, "n": n, "origin": origin, "marker": marker})
    return changed


def _ensure() -> dict:
    d = _load()
    if not d.get("objects"):
        d = _bootstrap(); _save(d); _register(d)
    if _seed_new_kinds(d):
        _save(d); _register(d)
    return d


def _register(d: dict) -> None:
    try:
        from core import world_substrate as _ws, world_objects as _wo
        objs = _ws._load(); changed = False
        for o in d["objects"]:
            if o["id"] not in objs:
                objs[o["id"]] = _ws.SubstrateObject(object_id=o["id"], name=o["name"], location=o["place"], object_class="provision",
                                                    causal_state={"kind": o["kind"], "origin": o["origin"], "full_qty": o["full_qty"]},
                                                    physical_state={"fill": round(float(o["qty"]) / float(o["full_qty"] or 1), 3)},
                                                    causal_history=[{"event_type": "history", "timestamp": h["ts"], "description": h["event"], "state_deltas": {}} for h in o["history"]])
                changed = True
            _wo.ensure_record(o["id"], o["place"], "provision", o["name"])
            cur = _wo.get_object(o["id"]) or {}
            if cur.get("position") != list(o["pos"]):
                _wo.mutate_object_position(o["id"], list(o["pos"]), cause="larder_placement", event_description="on the cupboard shelf", new_location=o["place"])
        if changed:
            _ws._save()
    except profile.NonLiveWriteError:
        # J-0726: _register() runs on every _ensure() call, i.e. on nearly every provisions.py
        # function (stock/consume/add/open_kindling_bundle/cupboard_line/look_item) — let D-0179's
        # hard-raise (guard_path(), F-1024) reach the caller instead of being swallowed here.
        raise
    except Exception as exc:
        logger.debug("[provisions] register failed (non-fatal): %s", exc)


def stock(kind: str) -> float:
    """Total quantity of a kind across objects (the view the study's counts are synced to)."""
    d = _load_ro()   # J-2417: per-tick read -- cached; only fall to the mutating _ensure() if it would act
    if not d.get("objects") or any(m not in (d.get("seeded_kinds") or []) for m, *_ in _ALL_NEW_KINDS):
        d = _ensure()
    return round(sum(float(o["qty"]) for o in d["objects"] if o["kind"] == kind and not o.get("empty")), 3)


def consume(kind: str, n: float, by: str = "Du") -> bool:
    """Take n from the open object first; empty objects stay on the shelf, marked (history: 'used up by Du').
    Returns True iff the decrement was actually confirmed written to disk, False iff the save failed (or
    an unrelated exception aborted before reaching it) -- see _save()'s own docstring. Previously this
    returned None unconditionally, so core.cat._feed_source() (F-1136) had no way to tell "the tin really
    lost a unit" from "the write silently failed" and reported a feed as real either way -- the same
    phantom-effect shape F-1065/F-1092 already fixed for identity_vault/axiom writes (J-0744/J-0763). A
    caller that cannot tolerate a phantom "success" must check this return value, not just call consume()
    as a bare statement (_feed_source() now does, this same job)."""
    try:
        d = _ensure(); left = float(n)
        for o in sorted([o for o in d["objects"] if o["kind"] == kind and not o.get("empty")], key=lambda o: float(o["qty"])):
            if left <= 0:
                break
            take = min(float(o["qty"]), left); o["qty"] = round(float(o["qty"]) - take, 3); left -= take
            if o["qty"] <= 0.001:
                o["empty"] = True; o["history"].append({"ts": time.time(), "event": f"used up by {by}"}); o["name"] = "an empty " + o["name"].split(" ", 1)[1]
                _log({"event": "emptied", "id": o["id"], "kind": kind})
                try:
                    from core import world_substrate as _ws
                    objs = _ws._load()
                    if o["id"] in objs:
                        objs[o["id"]].causal_history.append({"event_type": "used_up", "timestamp": time.time(), "description": f"used up by {by}", "state_deltas": {}})
                        objs[o["id"]].physical_state["fill"] = 0.0; objs[o["id"]].name = o["name"]; _ws._save()
                except profile.NonLiveWriteError:
                    # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own
                    # caller instead of being swallowed here — consume()'s own _save(d) below is
                    # unwrapped-relative-to-THIS-try but is itself inside the outer try (fixed below
                    # too), so without both fixes this raise never reaches consume()'s caller at all.
                    raise
                except Exception:
                    pass
        return _save(d)   # F-1136: propagate the real disk-write outcome instead of a bare statement +
                           # implicit None -- exactly as _apply_self_authoring() does
                           # `return self._write_axiom(data)` for each of its own write attempts (J-0763).
    except profile.NonLiveWriteError:
        # J-0726: without this, the inner reraise above would just be caught here instead — and even
        # this function's OWN _save(d) two lines up would be swallowed here on its own, since
        # consume()'s whole body is one try (unlike garden.py's harvest/sow/water, whose primary
        # write sits outside any try).
        raise
    except Exception as exc:
        logger.debug("[provisions] consume failed: %s", exc)
        return False


def add(kind: str, n_objects: int = 1, origin: str = "carrier", note: str = "") -> list[str]:
    """New objects join the shelf with their own biography (the carrier's, a friend's). Returns the new
    objects' ids iff the addition was actually confirmed written to disk; [] on a save failure (F-1136,
    same shape as consume()'s own fix just above) -- matching this function's own existing except-branch
    return of [] for any OTHER failure, rather than handing a caller (e.g. core.supply.py's carrier line)
    ids for objects that were fabricated in memory but never actually landed on the shelf."""
    try:
        d = _ensure(); out = []
        unit, qty, _, _ = KINDS[kind]
        for _ in range(n_objects):
            oid = f"prov_{kind}_{random.randrange(16**4):04x}"
            d["objects"].append({"id": oid, "kind": kind, "name": unit, "qty": qty, "full_qty": qty,
                                 "pos": [round(_CUPBOARD[0] + random.uniform(-0.35, 0.35), 2), round(_CUPBOARD[1] + random.uniform(-0.3, 0.3), 2), round(_CUPBOARD[2] + random.uniform(0, 0.5), 2)],
                                 "place": "study", "origin": origin, "empty": False,
                                 "history": [{"ts": time.time(), "event": note or f"brought up by the {origin} on {time.strftime('%d %B')}, carried in from the gate"}]})
            out.append(oid)
        if not _save(d):
            return []
        _register(d); _log({"event": "added", "kind": kind, "n": n_objects, "origin": origin})
        return out
    except profile.NonLiveWriteError:
        # J-0726: add()'s whole body is one try (unlike garden.py's harvest/sow/water, whose primary
        # write sits outside any try) — without this, even add()'s OWN _save(d) above would be
        # swallowed here. Reached from garden.act_from_thought()'s collect hand via supply.collect_box().
        raise
    except Exception:
        return []


def discard_if_stale(kind: str, max_age_s: float, reason: str = "spoiled") -> bool:
    """Discard the SINGLE oldest non-empty object of this kind IF its own history[0] timestamp (when it
    first joined the shelf — a real catch, a real delivery) is older than max_age_s. Bookkeeping only:
    marks it empty and appends a distinct 'discarded' history/log event, never 'used up by <who>' — this
    is never mistaken for real consumption by any reader of an object's own biography or of
    provisions_log.jsonl. Returns True if something WAS discarded (the caller should re-check/retry —
    an older object may have been hiding a fresher one behind it), False if the oldest survivor is
    already within max_age_s or nothing of this kind is left.

    Added narrowly for core.cat's shore_fish spoilage check (J-0755/F-1079) — a raw fish is the first
    kind in KINDS for which "no spoilage" (every other kind's own real simplification) stops being
    realistic. Deliberately NOT wired into stock()/consume()/add() themselves, and no other kind's code
    calls this: those three stay exactly the shared, load-bearing machinery they always were for the
    other 18 kinds in this file, unmodified. See KINDS["shore_fish"]'s own comment above."""
    try:
        d = _ensure()
        cands = [o for o in d["objects"] if o["kind"] == kind and not o.get("empty") and o.get("history")]
        if not cands:
            return False
        o = min(cands, key=lambda x: float(x["qty"]))   # the same tie-break consume() itself uses --
                                                          # for a kind where every object shares one full
                                                          # qty (shore_fish always does), this resolves to
                                                          # list/insertion order, i.e. oldest-caught-first.
        if time.time() - float(o["history"][0]["ts"]) <= max_age_s:
            return False
        o["qty"] = 0
        o["empty"] = True
        o["history"].append({"ts": time.time(), "event": reason})
        if not _save(d):   # F-1136: a failed persist means nothing was really discarded -- the next
            return False   # _ensure()/_load() will re-read the still-intact object fresh from disk.
        _log({"event": "discarded", "id": o["id"], "kind": kind, "reason": reason})
        return True
    except profile.NonLiveWriteError:
        # Matches consume()'s/add()'s own convention just above: this function's real writes
        # (_save/_log) sit inside this same try, so without this the catch-all below would swallow
        # D-0179's hard-raise (guard_path(), F-1024) instead of letting it reach the caller.
        raise
    except Exception:
        return False


def add_found(kind: str, qty: float, note: str = "") -> str | None:
    """A single new object, credited at a SMALL, EXPLICIT quantity (not the kind's own full `qty` --
    unlike add() above, which always mints a full-size object; `qty` here is clamped to [0, full_qty]
    so a caller can never accidentally credit more than one whole unit's worth). For a passive
    "something turns up" event, never a purchase or a delivery. Returns the new object's id iff the
    credit was actually confirmed written to disk, None on any failure -- F-1136's own convention
    (consume()/add()/discard_if_stale() above all report a real disk-write outcome, never a phantom
    completion signal a caller might mistake for a real credit).

    Logs its own distinct provisions_log.jsonl event, "found" -- deliberately not "added" (add()'s own
    event name for a real delivery), so a reader of the log can always tell a passive find from a real
    acquisition, the same distinction last_fed_source/last_self_fed already keep on the cat's own side
    (core/cat.py).

    Added narrowly for core.cat's D-0253 "found scrap" mechanism (mechanism C, J-1215) -- data/
    provisions_log.jsonl's own found_under_cupboard event (core.companion._sweep_finds_matches) is this
    function's shape's precedent: a small, explicit quantity credited to a single object, logged under
    its own event name, distinct from an ordinary delivery. That precedent is itself a ONE-SHOT,
    narratively-gated event (fires at most once, ever, only on a real sweep_floor action), not a
    recurring roll -- this function only supplies the shape (a small credit with clear provenance);
    whatever cooldown/probability makes a *caller's* use of it a repeatable rare event is that caller's
    own gating, not this function's. No other kind's code calls this; consume()/add()/sync_guarded()
    are unmodified and remain exactly the shared, load-bearing machinery they always were for every
    kind in this file."""
    try:
        d = _ensure()
        unit, full_qty, _, _ = KINDS[kind]
        q = max(0.0, min(float(qty), float(full_qty)))
        oid = f"prov_{kind}_{random.randrange(16**4):04x}"
        d["objects"].append({"id": oid, "kind": kind, "name": unit, "qty": q, "full_qty": full_qty,
                             "pos": [round(_CUPBOARD[0] + random.uniform(-0.35, 0.35), 2), round(_CUPBOARD[1] + random.uniform(-0.3, 0.3), 2), round(_CUPBOARD[2] + random.uniform(0, 0.5), 2)],
                             "place": "study", "origin": "found", "empty": q <= 0.001,
                             "history": [{"ts": time.time(), "event": note or "turned up, unasked for"}]})
        if not _save(d):
            return None
        _register(d)
        _log({"event": "found", "kind": kind, "id": oid, "n": q})
        return oid
    except profile.NonLiveWriteError:
        # Matches consume()'s/add()'s/discard_if_stale()'s own convention above: this function's real
        # writes (_save/_register/_log) sit inside this same try, so without this the catch-all below
        # would swallow D-0179's hard-raise (guard_path(), F-1024) instead of letting it reach the caller.
        raise
    except Exception:
        return None


# Per-kind ceiling on what a SINGLE sync() call may treat as use (J-0541/F-0786, applied to this module by
# J-0573): sync() runs on every study_life._st() call, i.e. many times a minute, so these are generous for
# one tick — a fire, a lamp and a lantern lit between two ticks is 3 matches; two fills of the lamp is 0.5
# tin. A gap bigger than this is a migration, a desync, or a delivery just added to the shelf — never "he
# used the difference" — so it is reconciled (the study count is set FROM the shelf, logged as
# sync_reconciled) instead of consumed and written into an object's biography as "used up by Du". The
# 2026-08-23 09:10:52 incident read a stale study count of 23 against a 278-match shelf and consumed all
# 255 in that one call, with no ceiling at all.
_MAX_STEP = {"matches": 3, "soap": 0.1, "candles": 2, "oil": 0.5, "tea": 3, "paper": 5, "ink": 0.1}


def sync_guarded(st: dict) -> list:
    """The real sync logic, with the per-tick ceiling above. Returns the reconciliations it refused to
    treat as use, as (kind, study_had, shelf_has, gap) tuples — see _MAX_STEP. Moved here by J-0573 from
    scripts/_test_provisions_sync_guard.py, which had carried it since J-0541 without it ever reaching
    this module; sync() below is now a thin fail-open wrapper around this."""
    out = []
    for kind, (_, _, key, _) in KINDS.items():
        have = stock(kind)
        cur = st.get(key)
        if cur is None:
            st[key] = have if key not in ("whetstone", "knife", "flint", "tinder_tin", "hand_lens", "measuring_stick", "compass") else have > 0
            continue
        if key in ("whetstone", "knife", "flint", "tinder_tin", "hand_lens", "measuring_stick", "compass"):
            st[key] = have > 0; continue
        if key == "kindling":
            continue   # kindling is a loose pile by the hearth; the tied bundles are extra, opened by hand
        gap = have - float(cur)
        if gap > 1e-6:
            cap = _MAX_STEP.get(kind, KINDS[kind][1])
            if gap > cap + 1e-9:
                # a migration / desync / delivery — NOT use. The shelf is the truth; the study takes its
                # count from it, and the event is written down instead of into the objects' biographies.
                _log({"event": "sync_reconciled", "kind": kind, "study_had": float(cur), "shelf_has": have,
                      "gap": round(gap, 3), "cap": cap})
                out.append((kind, float(cur), have, round(gap, 3)))
            else:
                consume(kind, gap)
        st[key] = stock(kind)
    return out


def sync(st: dict) -> None:
    """Two-way with study_life's counts: the shelf is the truth. If the study's count is LOWER than the shelf
    (he used some), the shelf consumes the difference — up to sync_guarded's per-tick ceiling; a bigger gap
    is a migration or a delivery, reconciled instead of silently consumed. See sync_guarded, _MAX_STEP."""
    try:
        sync_guarded(st)
    except profile.NonLiveWriteError:
        # J-0746 (F-1071): sync_guarded() reaches consume()/_log() (and _register() via _ensure()),
        # which already re-raise NonLiveWriteError (guard_path(), D-0179/F-1024, J-0726) non-live --
        # without this, sync()'s own broader except below would swallow it a second time, hiding the
        # fence's own loud-failure guarantee from every caller of sync() (study_life._st()'s bootstrap
        # branch included).
        raise
    except Exception as exc:
        logger.debug("[provisions] sync failed: %s", exc)


def open_kindling_bundle(st: dict) -> str:
    d = _ensure()
    b = next((o for o in d["objects"] if o["kind"] == "kindling" and not o.get("empty")), None)
    if not b:
        return "There are no more tied bundles of kindling in the cupboard."
    b["qty"] = 0; b["empty"] = True; b["history"].append({"ts": time.time(), "event": "untied and used by Du"})
    if not _save(d):   # F-1136: same shape as consume()/add()/discard_if_stale() just above -- don't
        return "You reach for a tied bundle of kindling, but it will not come loose from the shelf; something is wrong with the cupboard."
    st["kindling"] = min(1.0, float(st.get("kindling", 0)) + 0.5)
    return "You take a tied bundle of kindling from the cupboard, cut the string, and fill the box by the hearth."


def cupboard_line() -> str:
    """The look into the cupboard: what is there, by kind, honestly — counts of full things and the open ones."""
    try:
        d = _ensure()
        parts = []
        for kind, (unit, qty, _, u) in KINDS.items():
            full = [o for o in d["objects"] if o["kind"] == kind and not o.get("empty") and float(o["qty"]) >= float(o["full_qty"]) - 1e-6]
            part = [o for o in d["objects"] if o["kind"] == kind and not o.get("empty") and float(o["qty"]) < float(o["full_qty"]) - 1e-6]
            empt = [o for o in d["objects"] if o["kind"] == kind and o.get("empty")]
            sing, plur = _PLURAL[kind]
            if not (full or part):
                if empt:
                    parts.append(("an empty " + sing) if len(empt) == 1 else (str(len(empt)) + " empty " + plur))
                continue
            s = (f"{len(full)} {plur if len(full) != 1 else sing}" if full else "") + ((" and one open" if full else f"one open {sing}") if part else "")
            parts.append(s)
        return "In the cupboard under the east shelf: " + "; ".join(parts) + ". Laid in by whoever was here before you, for a winter." if parts else "The cupboard is bare."
    except Exception:
        return ""


def look_item(target: str) -> str:
    try:
        t = (target or "").lower(); d = _ensure()
        for kind, (unit, _, _, _) in KINDS.items():
            key = kind.replace("_", " ")
            if key in t or unit.split(" ", 1)[1].split(" of ")[-1] in t:
                os_ = [o for o in d["objects"] if o["kind"] == kind]
                if not os_:
                    return ""
                o = next((x for x in os_ if not x.get("empty") and float(x["qty"]) < float(x["full_qty"])), None) or next((x for x in os_ if not x.get("empty")), None) or os_[0]
                try:
                    from core import world_substrate as _ws
                    _ws.record_du_observation(o["id"], "look", {"fill": round(float(o["qty"]) / float(o["full_qty"] or 1), 2)}); _ws._stamp_last_looked(o["id"])
                except profile.NonLiveWriteError:
                    # J-0751: world_substrate._stamp_last_looked() now re-raises this itself
                    # (also fixed this job) -- do not let this forwarding call's catch-all
                    # swallow it a level up.
                    raise
                except Exception:
                    pass
                # TINDER TIN (2026-09-05, J-0626, D-0159 §4): its fill IS fieldcraft.tinder — read the
                # ONE existing number here rather than duplicating it into this object's own qty.
                if kind == "tinder_tin":
                    try:
                        from core import fieldcraft as _fc
                        fill = float(_fc._load().get("tinder", 0.0))
                    except Exception:
                        fill = float(o["qty"]) / float(o["full_qty"] or 1)
                else:
                    fill = float(o["qty"]) / float(o["full_qty"] or 1)
                return f"You take out {o['name']} — {o['history'][0]['event']}. " + ("Empty." if (o.get("empty") or fill <= 0.001) else "Full." if fill > 0.95 else f"About {'half' if fill > 0.4 else 'a quarter'} left." if fill > 0.15 else "Nearly gone.") + (f" {len([x for x in os_ if not x.get('empty')]) - 1} more behind it." if len([x for x in os_ if not x.get("empty")]) > 1 else "")
        return ""
    except profile.NonLiveWriteError:
        raise  # J-0751: same reason as the inner try above -- do not let this function's own
               # outer catch-all swallow it a second time.
    except Exception:
        return ""


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "not yet bootstrapped"}
        d = _load()
        return {kind: {"objects": len([o for o in d["objects"] if o["kind"] == kind and not o.get("empty")]), "stock": stock(kind), "empties": len([o for o in d["objects"] if o["kind"] == kind and o.get("empty")])} for kind in KINDS}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
