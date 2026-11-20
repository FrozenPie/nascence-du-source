"""Regression for J-0543/F-0738 (2026-09-04) and J-0569/F-0783 (2026-09-06): core/garden.py's act_from_thought()
READS the grammar of every family it hosts from the ONE table in core/actions.py — no hand-kept copy, so the
F-0554 drift shape (a verb dropped from the table but still firing in the hand; an object the hand knows and
the gate cannot see) cannot recur silently. J-0543 derived harvest/sow/weed/water/feed_birds/trap (dig already
had it, J-0522); J-0569 derived the rest this module hosts: collect, mow, stake, net, save_seed, tool, ash_out,
water_fill, compost.
Part 1 is pure (garden._wills / the four sub-hand partitions / grammar_audit against actions.BY_FAMILY, plus a
source-text scan of garden.py for old local tuples). Part 2 exercises act_from_thought with every store it
touches redirected into a temp dir (the life_smoke isolation pattern) — the live data/ is never written.
    python scripts/_test_garden_grammar_derivation.py
"""
from __future__ import annotations
import re, sys, tempfile, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

def _stat_or_none(p: Path):
    """(mtime, size) of a path, or None if it doesn't exist -- used by part 2's live-untouched canary
    (J-0878/F-1236) so 'never existed' can be told apart from 'existed and never moved'."""
    try:
        st = p.stat()
        return (st.st_mtime, st.st_size)
    except OSError:
        return None

def _live_status(before, after):
    """Describe what happened to a live data file across part 2's run, from _stat_or_none() snapshots
    taken before and after. A bare .exists() read cannot tell 'absent' from 'present and untouched' --
    it reports the same False for both a real worktree (no data/ dir at all) and a real leak, which is
    exactly what read as a leak report in J-0832 (F-1236), for this same finally block's own old print."""
    if before is None and after is None:
        return "absent"
    if before == after:
        return "unchanged"
    return f"CHANGED ({before} -> {after})"

print("-- part 1: the derivation (pure)")
from core import actions as AC, hands as H, garden as G

audit = G.grammar_audit()
check("grammar_audit ran", "error" not in audit, str(audit))
check("every derived family is a row in core/actions.py", audit.get("derived_missing_from_table") == [], str(audit))
for fam in ("trap", "tool", "compost"):
    check(f"every {fam} verb in the table is claimed by a sub-hand", audit.get(f"{fam}_unclaimed_in_table") == [], str(audit))
    check(f"no sub-hand claims a {fam} verb the table no longer has", audit.get(f"{fam}_claimed_not_in_table") == [], str(audit))
for fam, hands_tbl in (("trap", G._TRAP_HANDS), ("tool", G._TOOL_HANDS), ("compost", G._COMPOST_HANDS)):
    _claims = [v for _, vs in hands_tbl for v in vs]
    check(f"no {fam} verb is claimed by two sub-hands", len(_claims) == len(set(_claims)), str(_claims))

# (a) every verb x object pair the TABLE accepts, the garden hand accepts — the gate can never pass a deed the
#     hand then declines on grammar
for fam in G._DERIVED_FAMILIES:
    a = AC.BY_FAMILY[fam]
    if fam == "trap":
        miss = [(v, o) for v in a.verbs for o in a.objects if G._wills_trap(f"i {v} the {o}") is None]
    elif fam == "dig":
        miss = [(v, o) for v in a.verbs for o in a.objects if not G._wills_dig(f"i {v} the {o}")]
    elif fam == "tool":
        miss = [(v, o) for v in a.verbs for o in a.objects if G._wills_tool(f"i {v} the {o}") is None]
    elif fam == "compost":
        # spread only ever answers the bare object "compost" (by design — see _wills_compost), so its half
        # of the sweep uses that object, not every row object; turn gets the full row.
        turn_v = dict(G._COMPOST_HANDS)["turn"]
        miss = [(v, "compost") for v in a.verbs if v not in turn_v and G._wills_compost(f"i {v} the compost") is None]
        miss += [(v, o) for v in a.verbs if v in turn_v for o in a.objects if G._wills_compost(f"i {v} the {o}") is None]
    else:
        miss = [(v, o) for v in a.verbs for o in a.objects if not G._wills(f"i {v} the {o}", fam, loose=False)]
    check(f"{fam}: the hand accepts every verb x object pair of its table row ({len(a.verbs)}x{len(a.objects)})", not miss, str(miss[:6]))

# (b) the sub-hand partitions route each table verb to the sub-hand that claims it
for sub, verbs in G._TRAP_HANDS:
    wrong = [v for v in verbs if G._wills_trap(f"i {v} the trap") != sub]
    check(f"trap: {sorted(verbs)} route to the '{sub}' hand", not wrong, str(wrong))
check("trap: a non-trap thought routes nowhere", G._wills_trap("i set the book down and check the fire") is None)
check("trap: 'the pull of that rusted trap' routes nowhere (J-0554 noun rule holds through the derivation)",
      G._wills_trap("feeling the pull of that rusted trap and the quiet restlessness beneath") is None)

for sub, verbs in G._TOOL_HANDS:
    wrong = [v for v in verbs if G._wills_tool(f"i {v} the trowel") != sub]
    check(f"tool: {sorted(verbs)} route to the '{sub}' hand", not wrong, str(wrong))
check("tool: a non-tool thought routes nowhere", G._wills_tool("i sit by the fire and think of nothing") is None)
check("tool: 'i leave the abstract river logic behind' routes nowhere ('leave' is not a claimed verb — the drift this closed)",
      G._wills_tool("i leave the abstract river logic behind, feeling the gritty dust on my hands") is None)

for sub, verbs in G._COMPOST_HANDS:
    obj = "compost" if sub == "spread" else "heap"
    wrong = [v for v in verbs if G._wills_compost(f"i {v} the {obj}") != sub]
    check(f"compost: {sorted(verbs)} route to the '{sub}' hand", not wrong, str(wrong))
check("compost: a non-compost thought routes nowhere", G._wills_compost("i sit by the fire and think of nothing") is None)
check("compost: 'fork in the compost heap' routes to turn, not spread (the heap exclusion)",
      G._wills_compost("i fork in the compost heap by the wall") == "turn")
check("compost: 'fork in the compost' (no heap nearby) routes to spread",
      G._wills_compost("i fork in the compost and barrow it to the bed") == "spread")

check("water_fill (wood): 'fill the barrel from the spring' routes to 'barrel'",
      G._wills_water_fill_wood("i will fill the barrel from the spring") == "barrel")
check("water_fill (wood): 'fill the pail at the spring' routes to 'pail'",
      G._wills_water_fill_wood("i will fill the pail at the spring") == "pail")
check("water_fill (wood): a non-water thought routes nowhere",
      G._wills_water_fill_wood("i sit under the oak and think of nothing") is None)

# (c) the objects/verbs only the gate could now see reach the hand, and the objects/verbs only the hand knew
#     are in the table
check("water: the table's 'sunflowers' reaches the hand", G._wills("i water the sunflowers", "water"))
check("sow: the table's 'soil' reaches the hand", G._wills("i plant a few seeds in the soil", "sow"))
check("sow: the tin's species live in the table ('sow the radish')", G._wills("i will sow the radish now", "sow"))
check("harvest: the crops the hand cuts live in the table ('pick some lettuce')", G._wills("i pick some lettuce for tonight", "harvest"))
for fam, obj in (("harvest", "chives"), ("harvest", "silverbeet"), ("harvest", "lettuce"), ("harvest", "radish"), ("sow", "packet"),
                 ("sow", "calendula"), ("sow", "tomatoes")):
    check(f"{fam}: '{obj}' is in the table row", obj in AC.BY_FAMILY[fam].objects)
check("harvest: the hand's old 'leaves' is gone (its one corpus hit was 'damp earth and cut leaves')", "leaves" not in AC.BY_FAMILY["harvest"].objects)
check("weed: the hand's old 'them'/'out' are not in the table", not {"them", "out"} & set(AC.BY_FAMILY["weed"].objects))
check("water: the hand's old 'soak'/'douse' verbs and 'them'/'it' objects are not in the table",
      not ({"soak", "douse"} & set(AC.BY_FAMILY["water"].verbs)) and not ({"them", "it"} & set(AC.BY_FAMILY["water"].objects)))
check("trap: the hand's old 'close' verb is not a trap verb", "close" not in AC.BY_FAMILY["trap"].verbs)
check("net: 'take off'/'lift' (the un-net branch net() already implements) are table verbs",
      {"take off", "lift"} <= set(AC.BY_FAMILY["net"].verbs))
check("net: the widened verbs reach the hand ('i lift the netting off the bed')", G._wills("i lift the netting off the bed", "net"))
check("net: 'untangle'/'secure' (Du's own netting words, J-1772/D-0344) are table verbs and reach the hand -- and nothing else joined the row",
      {"untangle", "secure"} <= set(AC.BY_FAMILY["net"].verbs) and G._wills("i untangle that bird netting", "net") and G._wills("i secure the bed with the netting", "net")
      and tuple(AC.BY_FAMILY["net"].verbs) == ("net", "cover", "stretch", "take off", "lift", "untangle", "secure"), str(AC.BY_FAMILY["net"].verbs))
check("tool: 'shears' (a real _CARRYABLE item the table could not see) is a table object", "shears" in AC.BY_FAMILY["tool"].objects)
check("tool: the widened object reaches the hand ('i take the shears')", G._wills_tool("i take the shears") == "take")

# (d) the drifted copies' false fires are closed (Du's own corpus idioms; F-0738/F-0783, J-0543/J-0569)
check("weed: 'the fire pulls me out of my head' is no weeding will", not G._wills("the fire pulls me out of my head and back to the room", "weed"))
check("water: 'the tide ... stone and water' is no watering will", not G._wills("the tide works at the stone and water finds every crack", "water"))
check("water: 'soak it' is no watering will", not G._wills("i let the light soak it all in", "water"))
check("harvest: 'damp earth and cut leaves' is no harvest will", not G._wills("the air smells of damp earth and cut leaves", "harvest"))
check("harvest: a real cut still reads ('i cut a sprig of rosemary')", G._wills("i cut a sprig of rosemary", "harvest"))
check("weed: a real pull still reads ('i pull the chickweed out of the bed')", G._wills("i pull the chickweed out of the bed", "weed"))
check("loose retry kept for the hands that had it: 'i go to the bed. i cut some rosemary for the rack.'",
      G._wills("i go to the bed. i cut some rosemary for the rack.", "harvest"))
check("feed_birds stays strict: 'i feed the fire. the birds call.' is no feeding will", not G._wills("i feed the fire. the birds call.", "feed_birds", loose=False))
check("feed_birds: 'i scatter a pinch for the birds' reads", G._wills("i scatter a pinch for the birds", "feed_birds", loose=False))
check("an unknown family fails closed", not G._wills("i harvest the herbs", "no_such_family"))

check("stake: the hand's old 'them'/'stakes' are not in the table (zero corpus hits either way; 'stakes' already belongs to 'tool')",
      not ({"them", "stakes"} & set(AC.BY_FAMILY["stake"].objects)))
check("stake: a real stake will still reads ('i stake the tomatoes with twine')", G._wills("i stake the tomatoes with twine", "stake"))
check("net: the hand's old bare 'net' object is gone", "net" not in AC.BY_FAMILY["net"].objects)
check("net: 'the orange net tangled in wrack' is no netting will (16/16 of its old corpus hits were this beach idiom)",
      not G._wills("i watch the orange net tangled in wrack, then turn to the book of rhymes", "net"))
check("net: a real cover still reads ('i stretch the netting over the seedlings')", G._wills("i stretch the netting over the seedlings", "net"))
check("save_seed: the hand's copy was already identical to the table ('i save the seed heads')", G._wills("i save the seed heads from the bed", "save_seed"))
check("mow: the hand's copy was already identical to the table ('i mow the lawn')", G._wills("i mow the lawn", "mow", loose=False))
check("collect: the hand's old bare 'the box at the gate' (no verb) is gone — its one corpus hit was noticing, not a will",
      not G._wills("the box at the gate is full, heavy with letters from darwin and others waiting", "collect", loose=False))
check("collect: a real fetch still reads ('i will fetch the box from the gate')", G._wills("i will fetch the box from the gate", "collect", loose=False))
check("water_fill: the old test matched ZERO of 9,791 corpus thoughts; a real fill now reads",
      G._wills("i will fill the bucket from the barrel", "water_fill", loose=False))
check("ash_out: 'the rain washes...the garden' is no ash-tipping will (48/49 of its old corpus hits were this circling-thought idiom)",
      not G._wills("the rain washes away plato's forms, yet i feel a pull toward the garden", "ash_out", loose=False))
check("ash_out: a real tip still reads ('i tip the ash bucket out on the bed')", G._wills("i tip the ash bucket out on the bed", "ash_out", loose=False))
check("tool: 'i leave the abstract river logic behind' is no tool will (299/302 of its old corpus hits were this 'leave' idiom)",
      G._wills_tool("i leave the abstract river logic behind, feeling the gritty dust on my hands") is None)
check("tool: a real take still reads ('i take the trowel with me')", G._wills_tool("i take the trowel with me") == "take")
check("compost: the hand's old 'put' verb is gone (zero corpus support either way; every other compost verb matched the table)",
      "put" not in AC.BY_FAMILY["compost"].verbs)
check("compost: real corpus mentions are all ambient, never a will ('the blackbird cuts across the lawn...against the compost heap's rot')",
      not G._wills("the blackbird cuts across the lawn, its flight a clean line against the compost heap's rot", "compost"))

# (e) the source itself: no hand-kept copy of a derived family's grammar left in garden.py
src = (ROOT / "core" / "garden.py").read_text(encoding="utf-8")
body = src[src.index("def act_from_thought("):]
for name in ("_harvest_v", "_sow_v", "_weed_v", "_water_v", "_harvest_o", "_sow_o", "_weed_o", "_water_o",
             "_stake_v", "_stake_o", "_net_v", "_net_o", "_saveseed_v", "_saveseed_o"):
    check(f"garden.py act_from_thought no longer defines {name}", name not in body)
check("garden.py carries no literal feed_birds verb tuple", '("feed", "scatter"' not in src)
check("garden.py act_from_thought carries no literal trap object tuple (the item word-map _WORDS is not grammar)", '("trap", "possum trap")' not in body)
check("garden.py carries each trap verb tuple exactly once (in _TRAP_HANDS)",
      src.count('("check", "look in"') == 1 and src.count('("set", "bait"') == 1 and src.count('("spring", "disarm"') == 1)
# exact multi-item literal joins from the old code (not just the bare phrase, which this file's own prose
# comments now also quote for readability — "the box at the gate is full..." — without being the old test)
check("garden.py act_from_thought carries no literal collect phrase list", '"collect the box", "fetch the box"' not in body)
check("garden.py act_from_thought carries no literal water_fill phrase list", '"fill the pail", "fetch water"' not in body)
check("garden.py act_from_thought carries no literal ash_out substring test", '"tip", "spread", "on the bed", "garden"' not in body)
check("garden.py act_from_thought carries no literal tool take/put phrase lists",
      '"pick up", "take the", "fetch the"' not in body and '"leave the", "set the"' not in body)
check("garden.py carries the tool verb tuples exactly once each (in _TOOL_HANDS)",
      src.count('("pick up", "take", "fetch", "carry", "bring", "grab")') == 1 and src.count('("set down", "put down")') == 1)
check("garden.py carries the compost verb tuples exactly once each (in _COMPOST_HANDS)",
      src.count('("spread", "barrow", "fork in", "dig in")') == 1 and src.count('("turn", "fork", "turn over", "fork over")') == 1)

print("-- part 2: act_from_thought routes through the derivation (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="garden_grammar_"))
# J-0878 (F-1236): found alongside fieldcraft's own copy of the same bug -- this bare live.exists() read
# "untouched: False" whenever ROOT/data/garden.json simply doesn't exist (every run inside a git worktree,
# which has no data/ dir at all) and "untouched: True" whenever it happens to exist regardless of whether
# THIS run touched it. Snapshot before part 2 runs, compare for real after.
_LIVE = ROOT / "data" / "garden.json"
_LIVE_BEFORE = _stat_or_none(_LIVE)
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    # J-0743 (2026-09-08, F-1063's wider sweep): every (module, attrs) pair below was re-verified
    # directly against the real module source this pass. core.garden_life was missing its own
    # "_EVENTS" (shared filename with core.garden's, per core/profile.py's own comment, but a
    # DIFFERENT Python attribute -- garden's own redirect never covered it); core.supply was missing
    # "_LOG"; core.fieldcraft was missing "_LEDGER" -- all three are real guard_path()-protected
    # write targets (core/garden_life.py:72, core/supply.py:64, core/fieldcraft.py:72) this script's
    # own exercised act_from_thought() calls can plausibly reach, caught only by that separate,
    # later-built fence until now, not by this script's own isolation claim. core.locomotion's "_F"
    # was dead (the module has never had one; its real store is "_POS_F", never listed at all --
    # the same wrong-name bug F-1063 already found and fixed in scripts/_test_letterbox_reach.py and
    # scripts/life_smoke.py). core.garden_soil/core.life_traces/core.inventory carry NO redirectable
    # path of their own at all (all three operate on core.garden's/core.life's own state, already
    # covered above) -- their entries were always dead no-ops; dropped rather than left to mislead
    # the next copy. core.hands' own "_F" was likewise dead (real store is "_TRACE" alone).
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")), ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                       ("core.life", ("_F", "_LEDGER", "_EVENTS", "_FLAGS_F")), ("core.study_life", ("_LEDGER", "_EVENTS")),  # J-0743: _FLAGS_F read-only, see life_smoke.py's own comment
                       ("core.provisions", ("_F", "_LOG")), ("core.locomotion", ("_POS_F",)), ("core.hands", ("_TRACE",)),
                       # J-0783: core.garden_knowledge is now guard_path()-protected too (was never
                       # fenced before) -- this script's own act_from_thought() sweep reaches
                       # _stage_phrase()/_wname()/display_name() (garden.py's look()/bed_summary()/
                       # weed()), unredirected until now; scripts/life_smoke.py already carried this
                       # entry, this script never did.
                       ("core.garden_knowledge", ("_F",)),
                       # J-0920: core.smell._F (smell_field.json) is guard_path()-fenced since J-0917
                       # (2026-09-12, module #20) but was never added here -- confirmed empirically
                       # (scratchpad/audit_J-0920_stage_gating.py): harvest()'s own _sm.brush(species)
                       # cross-link (garden.py, wrapped in a bare `except Exception: pass`) raises
                       # NonLiveWriteError and is silently swallowed on every harvest() call this part
                       # 2 makes, the same never-updated-after-fencing shape J-0743/J-0783 already
                       # fixed for other modules here. No live leak either way (the fence's whole job
                       # is to refuse an unredirected write, which it did) -- redirecting restores real
                       # test fidelity for that cross-link instead of relying on the swallow.
                       ("core.smell", ("_F",)),
                       # J-0920: core.keepsakes._F (data/keepsakes.json) was never redirected here at
                       # all -- invisible until now because save_seed()'s own real try/except body
                       # (the keepsakes.keep() call) had zero-plant coverage before this same job's fix
                       # a few lines below (F-1284). keepsakes.py is guard_path()-fenced (J-0877) and
                       # save_seed()'s own J-0895 fix explicitly re-raises NonLiveWriteError rather
                       # than swallowing it, so the very first real save_seed() call this script ever
                       # made hard-raised straight through part 2's own try/except -- confirmed by
                       # direct run, not guessed (the exact refusal: "non-live process attempted to
                       # write to data/keepsakes.json -- refused (D-0179)"). No live leak either way
                       # (the fence refused the write, exactly as designed); redirected here the same
                       # way scripts/life_smoke.py already does at its own KP._F line.
                       ("core.keepsakes", ("_F",))):
        try:
            m = __import__(mod, fromlist=["x"])
            for a in attrs:
                if hasattr(m, a):
                    setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                else:
                    # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with
                    # zero warning. Loud now, on purpose.
                    print("   (redirect skipped:", mod, a, "-- no such attribute, stale/typo'd isolation-list entry? )")
        except Exception as exc:
            print("   (redirect skipped:", mod, exc, ")")
    # J-0743: core.wandering / core.activity_memory -- the same two modules F-1063 found un-
    # redirectable in scripts/_test_letterbox_reach.py (neither defines a per-module path attribute
    # at all). This script's part-2 sweep drives act_from_thought() through water/sow/harvest/weed/
    # feed_birds/trap/mow/stake/net/save_seed/tool/collect/ash_out/water_fill/compost -- MANY real
    # "deed" cross-links into core/garden.py's own _log() (garden.py:267-270), per the same mechanism
    # life_smoke.py's own empirical reach-probe confirmed 9 real activity_memory.record() calls for
    # over a much narrower slice of these same families. Neutralized here by function monkeypatch,
    # the only option either module allows.
    from core import wandering as _WDR
    from core import activity_memory as _AM
    _WDR.perceive = lambda *a, **k: None
    _AM.record = lambda *a, **k: None
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "garden",
                    "garden": S._fresh_garden()})
    if hasattr(G, "_st"):
        try: G._st = None
        except Exception: pass
    # J-0920 (F-1284's own follow-up audit, 2026-09-14): this fixture never lets real time pass, so
    # several deeds below were only ever answered by their own early decline/report return, not the
    # real state-mutating body -- confirmed empirically, not guessed (ledger-append before/after each
    # call, scratchpad/audit_J-0920_stage_gating.py, outer Claude Code scratchpad): 5 of the 17 calls
    # below never reached a real write before this fix. save_seed's own gap was already known
    # (F-1284; J-0895's own dedicated verify_J-0895.py probe closes it there, not here); collect/
    # ash_out/water_fill's are the same shape, newly found by this job. Rig one real, reachable
    # precondition directly into each store's own cached state before the loop runs -- the identical
    # technique verify_J-0895.py already used (a real seeding-stage plant injected into garden's own
    # cached state) -- rather than waiting on a tick loop that would need days of simulated time to
    # grow one on its own. check_trap's own first-look decline (below, "i check the trap under the
    # tree") is deliberately left as-is: it is a legitimate no-catch report, not a broken precondition
    # -- the very next two calls in this same loop (set, then spring) do reach real bodies against the
    # SAME cached trap state; only the "a possum/hedgehog was actually caught" branch has no coverage
    # here, a genuinely separate, larger gap (it depends on core.life's own night_pass simulation) --
    # see this job's own spawned follow-up rather than rigged here.
    import copy as _copy
    _gst = G._load()
    _seed_src = next(p for p in _gst["plants"].values() if p["species"] == "broad_beans")
    _seed_plant = _copy.deepcopy(_seed_src)
    _seed_plant.update({"id": "garden_plant_peas_j0920", "species": "peas", "slot": 7,
                         "pos": G._BED_SLOTS[7], "stage": "seeding"})
    _gst["plants"][_seed_plant["id"]] = _seed_plant                         # save_seed: a real seeding-stage candidate
    from core import supply as _sup
    # core.supply._load() carries NO module-level cache (a plain read-file-or-default, unlike
    # core.garden._load()/core.study_life._st()'s own `global _state` pattern) -- confirmed by direct
    # read of its source. Mutating the dict it returns without writing it back is silently lost the
    # next time anything calls _load() again (collect_box() does, internally) -- caught empirically by
    # this job's own re-verification probe, which is exactly why this explicit _save() is here and not
    # left implicit like the other three precondition rigs below.
    _sup_box = _sup._load(); _sup_box["box"] = {"ts": time.time(), "items": ["seed"], "spoiled": False}
    _sup._save(_sup_box)                                                    # collect: a real box at the gate
    from core import study_life as _sl
    _sl._st()["ash_bucket_full"] = True                                    # ash_out: a real bucket of ash to tip
    _sl._st()["items"]["water_pail"]["carried"] = True                     # water_fill: the pail actually out with him
    # sow: found FLAKY by this job's own re-verification pass (re-run 4x: 1/4 reached the real body,
    # 3/4 declined "soil is cold" -- _bootstrap()'s default soil_temp=6.0 sits right at most species'
    # own t_germ-2 floor, and sow()'s own packet choice is genuinely unseeded `random.choice`, unlike
    # _bootstrap()'s own seeded rng that built the packet SET). Make it deterministic instead of
    # leaving a coin-flip: add a real, explicitly-labelled radish packet -- radish is both the species
    # the thought text itself already names (so sow()'s own `named` branch picks it over the random
    # one) and has the widest sow window in the table (Aug-Apr, core/garden.py:77), so this holds
    # across the whole year, not just today's real calendar date. soil_temp bumped to 14.0 (radish's
    # own t_germ is 8, but a generous margin costs nothing and matches the value scripts/life_smoke.py's
    # own sow() test already uses). _month() pinned to September for the same reason life_smoke.py's
    # own sow test pins it (its docstring: "September: cabbage's season") -- belt-and-braces alongside
    # the wide sow window, restored after the loop whether it raises or not.
    _gst.setdefault("packets", []).append({"species": "radish", "labelled": True, "count": 20, "year": 2026})
    _gst["soil_temp"] = 14.0
    _real_month = G._month
    G._month = lambda t=None: 9
    try:
        # positives: a family-scoped call must be ANSWERED by its own hand (a decline line is still an answer; None is not)
        for fam, t in (("water", "i water the sunflowers"), ("sow", "i sow the radish in the bed"), ("harvest", "i pick some lettuce"),
                       ("weed", "i pull the weeds from the bed"), ("feed_birds", "i scatter seed for the birds"),
                       ("trap", "i check the trap under the tree"), ("trap", "i set the trap under the tree"), ("trap", "i spring the trap"),
                       ("mow", "i mow the lawn"), ("stake", "i stake the tomatoes with the bundle and twine"),
                       ("net", "i stretch the netting over the seedlings"), ("save_seed", "i save the seed heads from the bed"),
                       ("tool", "i take the trowel with me"), ("collect", "i will fetch the box from the gate"),
                       ("ash_out", "i tip the ash bucket out on the bed"), ("water_fill", "i will fill the bucket from the barrel"),
                       ("compost", "i turn the compost heap by the wall")):
            ans = G.act_from_thought(t, "", family=fam)
            check(f"family='{fam}' answers {t!r}", bool(ans), repr(ans))
    finally:
        G._month = _real_month
    # the three trap hands are distinct answers
    a_chk = G.act_from_thought("i check the trap under the tree", "", family="trap")
    a_set = G.act_from_thought("i bait the trap under the tree", "", family="trap")
    check("trap: check and set are different hands", a_chk != a_set, f"{a_chk!r} == {a_set!r}")
    # tool: take then put the SAME item are different hands (put needs it carried first)
    a_take = G.act_from_thought("i take the trowel with me", "", family="tool")
    a_put = G.act_from_thought("i set the trowel down here", "", family="tool")
    check("tool: take and put-down give distinct answers once carried", bool(a_take) and bool(a_put) and a_take != a_put,
          f"{a_take!r} / {a_put!r}")
    # negatives: the drifted copies' false fires return NOTHING from the hand
    for fam, t in (("weed", "the fire pulls me out of my head and back to the room"),
                   ("water", "the tide works at the stone and water finds every crack"),
                   ("harvest", "the air smells of damp earth and cut leaves"),
                   ("trap", "a spring-jawed possum trap rusts far off"),
                   ("feed_birds", "i feed the fire. the birds call."),
                   ("net", "i watch the orange net tangled in wrack, then turn to the book of rhymes"),
                   ("ash_out", "the rain washes away plato's forms, yet i feel a pull toward the garden"),
                   ("collect", "the box at the gate is full, heavy with letters from darwin and others waiting"),
                   ("tool", "i leave the abstract river logic behind, feeling the gritty dust on my hands")):
        ans = G.act_from_thought(t, "", family=fam)
        check(f"family='{fam}' does not answer {t!r}", ans is None, repr(ans))
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    print(f"   isolated dir {TMP}; live garden.json: {_live_status(_LIVE_BEFORE, _stat_or_none(_LIVE))}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
