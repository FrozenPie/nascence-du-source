"""J-3440 (F-4070, plan object_epistemic_loop): deontic / intention frames are not hypotheses.

Hermetic: core is imported BEFORE lab_env and asserted to resolve inside this tree; world_substrate's store paths are
redirected to a temp dir; zero LLM, zero network.  Live data/ is hashed before and after.
python scripts/_test_J-3440_deontic.py      Exit 0 = pass.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import object_hypothesis as oh
from core import actions as act
from core import world_substrate as ws
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

FAIL = []
LIVE = Path(r"C:\Nascence\data")


def check(cond, name, info=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{info}]" if (info and not cond) else ""))
    if not cond:
        FAIL.append(name)


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


CANARY = [LIVE / "world_substrate.json", LIVE / "monologue_log.jsonl", LIVE / "hands_trace.jsonl"]
before = [_h(p) for p in CANARY]


def flags(extract_on=True, guard_on=True):
    os.environ["NASCENCE_DEONTIC_EXTRACT_GATE"] = "1" if extract_on else "0"
    os.environ["NASCENCE_DEONTIC_TEST_GUARD"] = "1" if guard_on else "0"


fam = act.families()

with isolate() as _lab:
    # -- 1. the frame -----------------------------------------------------------------------
    pos = ["maybe i should just let the dandelion float away for now",
           "perhaps i should leave it be, letting the seeds rest",
           "i think i'll heft it", "i want to scrape the rust", "let me smell the wood", "let's float the stone",
           "maybe i could water the thyme", "just let the seeds drift", "i'm going to check the trap",
           "should i water it", "what if i left it dry", "we should look again", "i need to weigh it",
           "i’ll try the stone", "i have to see"]
    neg = ["this driftwood might be beech", "i think it is rotten", "the stone is probably pumice",
           "i want to know if this stone is pumice", "i want to understand why it floats",
           "i can tell it's rusted", "i could be wrong about the stone", "it could be iron", "maybe the thyme is dying",
           "the barrel will leak", "that will be the frost", "he lets it float", "i was going to water it"]
    check(all(oh.deontic_frame_start(t) is not None for t in pos),
          "every intention clause opens a frame", str([t for t in pos if oh.deontic_frame_start(t) is None]))
    check(all(oh.deontic_frame_start(t) is None for t in neg),
          "no claim / inquiry clause is read as a frame", str([t for t in neg if oh.deontic_frame_start(t) is not None]))
    _t = "i think it is rotten, so i should water it"
    check(oh.deontic_frame_start(_t) == _t.index("i should"), "frame start index is exact")
    check(oh.deontic_frame_start("") is None and oh.deontic_frame_start(None) is None, "empty -> None")

    # -- 2. extract -------------------------------------------------------------------------
    D = ("plant", "a dandelion")
    flags(True, True)
    check(oh.extract("Maybe I should just let the dandelion float away for now", *D) is None,
          "F-4070 live case 1 (dandelion float away) -> not a hypothesis")
    check(oh.extract("The dandelion has gone to seed. Perhaps I should leave it be, letting the seeds rest.", *D) is None,
          "F-4070 live case 2 (leave it be, letting the seeds rest; anchor in the neighbour clause) -> not a hypothesis")
    TR = ("garden_item", "a spring-jawed possum trap, rusted, its plate set with a twist of wire for bait")
    check(oh.extract("Perhaps I should leave the trap be, it is rusted", *TR) is None,
          "intention that carries a claim word after the frame -> not a hypothesis")
    check(oh.extract("I think the dandelion is dying, so I should water it", *D) is not None,
          "a real claim BEFORE the frame is still recorded")
    check(oh.extract("Maybe the thyme is dying", "plant", "the thyme") is not None, "plain hypothesis unchanged")
    check(oh.extract("I want to know if this stone is pumice, perhaps it is", "stone", "a smooth grey beach stone")
          is not None, "an inquiry is not a frame; the claim clause stays")
    # an intention clause beside a real claim clause: the claim clause alone is returned
    r = oh.extract("Maybe the dandelion is wilting. Perhaps I should let it be.", *D)
    check(r is not None and "wilting" in r[0] and "should" not in r[0], f"claim clause kept, intention clause dropped: {r}")
    flags(False, True)
    check(oh.extract("Maybe I should just let the dandelion float away for now", *D) is not None,
          "kill switch NASCENCE_DEONTIC_EXTRACT_GATE=0 restores the previous extractor")
    # byte-for-byte on frame-free text across the flag
    samples = ["This pale stone might be pumice", "I think this driftwood might actually be beech, not fir, given the grain",
               "Maybe the thyme is dying from the frost", "The rain barrel is low on its side, and I suspect it leaks",
               "Maybe that rusted trap is iron", "Perhaps the twine is full", "mottainai, maybe the stone is heavy"]
    objs = [("stone", "a smooth grey beach stone"), ("driftwood", "driftwood log"), ("plant", "the thyme"),
            ("garden_item", "the rain barrel at the cottage corner"), TR, ("garden_item", "a ball of garden twine")]
    same = True
    for t in samples:
        for c, n in objs:
            flags(True, True); a = oh.extract(t, c, n)
            flags(False, False); b = oh.extract(t, c, n)
            same &= (a == b)
    check(same, "frame-free text: extract identical with the gate on and off")

    # -- 3. intervention_test guard ---------------------------------------------------------
    flags(True, False)
    off = oh.intervention_test("Maybe I should just let the dandelion float away for now", *D, "garden", families=fam)
    flags(True, True)
    on = oh.intervention_test("Maybe I should just let the dandelion float away for now", *D, "garden", families=fam)
    check(len(off) >= 1 and on == [], "guard: F-4070 float-away intention derives a deed with the guard off, none with it on",
          f"off={off} on={on}")
    flags(True, False)
    off2 = oh.intervention_test("Perhaps I should leave the trap be, it is rusted", *TR, "garden", families=fam)
    flags(True, True)
    on2 = oh.intervention_test("Perhaps I should leave the trap be, it is rusted", *TR, "garden", families=fam)
    check(len(off2) >= 1 and on2 == [], "guard: rusted-trap intention derives scrape with the guard off, none with it on",
          f"off={off2} on={on2}")
    flags(True, True)
    keep = oh.intervention_test("I think the pale stone is pumice, so I should heft it", "stone", "a pale stone", "shore",
                                families=fam)
    check(len(keep) >= 1 and {c["cue"] for c in keep} & {"pumice", "stone"},
          f"a claim before the frame still derives its test: {[(c['verb'], c['cue']) for c in keep]}")
    same = True
    for t in ["This pale stone might be pumice", "Maybe the thyme is dying from the frost", "Maybe that rusted trap is iron",
              "I think this driftwood might be beech and it is waterlogged and rotten"]:
        for c, n in [("stone", "a smooth grey beach stone"), ("plant", "the thyme"), TR, ("driftwood", "driftwood log")]:
            flags(True, True); a = oh.intervention_test(t, c, n, "garden", families=fam)
            flags(True, False); b = oh.intervention_test(t, c, n, "garden", families=fam)
            same &= (a == b)
    check(same, "frame-free claims: intervention_test identical with the guard on and off")

    # -- 4. end to end through the live writer in _route_act --------------------------------
    tmp = Path(tempfile.mkdtemp(prefix="j3440_"))
    ws._SUBSTRATE_F = tmp / "world_substrate.json"
    ws._LAST_LOOKED_F = tmp / "last_looked.json"
    ws._SUBSTRATE_LOG = tmp / "events.jsonl"

    def fresh(oid="dand_t", name="a dandelion", cls="plant", loc="garden"):
        s = {oid: {"object_id": oid, "name": name, "location": loc, "object_class": cls,
                   "observations": [{"observation_id": f"obs_{oid}_{i}", "timestamp": 1.0 + i, "action": "look",
                                     "features": {"colour": "yellow"}} for i in range(5)], "inferences": []}}
        ws._SUBSTRATE_F.write_text(json.dumps(s), encoding="utf-8")
        ws._cache = {}
        ws._cache_ts = 0.0
        ws._LAST_LOOKED_F.write_text(json.dumps({"object_id": oid, "ts": time.time() - 60}), encoding="utf-8")

    from nodes import inner_monologue_node as imn
    node = imn.InnerMonologueNode.__new__(imn.InnerMonologueNode)

    def route(thought):
        asyncio.run(node._route_act(None, "none", "", thought, "", set()))
        ws._cache = {}
        ws._cache_ts = 0.0
        return ws.get_object("dand_t").inferences

    os.environ.pop("NASCENCE_STRICT_INFERENCE_GATE", None)
    os.environ["NASCENCE_INTERVENTION_TEST"] = "1"
    flags(True, True)
    fresh()
    inf = route("Maybe I should just let the dandelion float away for now.")
    check(len(inf) == 0, f"live writer: the intention records no inference ({len(inf)})")
    fresh()
    inf = route("The dandelion head has gone to seed. Maybe the dandelion is dying.")
    check(len(inf) == 1, "live writer: a real claim is still recorded")
    flags(False, True)
    fresh()
    inf = route("Maybe I should just let the dandelion float away for now.")
    check(len(inf) == 1 and not inf[0].get('intervention_test'),
          f"extract gate killed, guard on: stored (legacy) but carries NO derived deed ({inf[0].get('intervention_test') if inf else None})")
    flags(False, False)
    fresh()
    inf = route("Maybe I should just let the dandelion float away for now.")
    check(len(inf) == 1 and bool(inf[0].get('intervention_test')), "both killed: the previous behaviour, byte for byte")
    flags(True, True)

    # -- 5. no live-data write ----------------------------------------------------------------
    after = [_h(p) for p in CANARY]
    check(before == after, "live data files unchanged (hash)")

print()
print("RESULT", "FAIL " + str(FAIL) if FAIL else "PASS")
sys.exit(1 if FAIL else 0)
