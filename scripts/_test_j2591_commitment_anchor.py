"""J-2591 / D-0514 (a): hermetic test of the dosed commitment anchor in core/concerns.py.

Run from a throwaway worktree (never the shared tree):  python scripts/_test_j2591_commitment_anchor.py
Zero LLM, zero live data: school/frontier are stubbed, commitment_active.json and the shadow log are
redirected by lab_env.isolate(db="empty"). Checks: dose 0 is byte-identical to HEAD's primary_concern; only
anchor=True rides; shadow rows carry stand id / dose / what the anchor would otherwise return; LIVE returns
the stand; and a scripted hold -> break -> recovery sequence is recoverable from the shadow rows alone.
"""
import importlib.util, json, os, subprocess, sys, types
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                         # core BEFORE lab_env (the 2026-10-04 lab_env sys.path leak)
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate
from core import concerns

fails = []
def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)

# ---- stubs for the two stores primary_concern reads -------------------------------------------------------
STATE = {"school_time": False, "title": "Walden", "frontier": []}
school = types.ModuleType("core.school")
school.is_school_time = lambda: STATE["school_time"]
school.assignment = lambda: (None, STATE["title"])
school.curriculum_status = lambda: ""
frontier = types.ModuleType("core.frontier")
frontier.top_open = lambda n: list(STATE["frontier"])[:n]
for name, mod in (("school", school), ("frontier", frontier)):
    sys.modules["core." + name] = mod
    setattr(core, name, mod)

# HEAD's concerns.py, loaded side by side, for the byte-identical check
head_src = subprocess.run(["git", "-C", str(TREE), "show", "HEAD:core/concerns.py"], capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout
head_path = Path(os.environ.get("TEMP", ".")) / "concerns_head_J-2591.py"
head_path.write_text(head_src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("concerns_head_J2591", head_path)
head = importlib.util.module_from_spec(spec); spec.loader.exec_module(head)

SCEN = [
    {"school_time": True, "title": "Walden", "frontier": []},
    {"school_time": False, "title": "Walden", "frontier": [{"q": "why tides", "encounters": 3, "has_finding": True}]},
    {"school_time": False, "title": "Walden", "frontier": [{"q": "once", "encounters": 1, "has_finding": False}]},
    {"school_time": False, "title": "", "frontier": []},
]
STAND = {"id": "abc12345", "statement": "I will keep the letter to Travis honest even when it costs me.",
         "held_since": 1000.0, "scans": 4, "load_bearing": True, "drop_denied": 2}
MUSE = {"id": "zzz00000", "statement": "the sea is a mirror", "held_since": 1.0, "load_bearing": False}

with isolate(also=[(concerns, ["_ACTIVE_COMMITMENTS", "_ANCHOR_SHADOW_LOG"])], db="empty") as lab:
    act, log = concerns._ACTIVE_COMMITMENTS, concerns._ANCHOR_SHADOW_LOG
    check("store redirected into the lab dir", str(lab) in str(act) and str(lab) in str(log))
    def rows():
        return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()] if log.exists() else []
    def set_active(items):
        act.write_text(json.dumps(items), encoding="utf-8")

    # 0. declared default (D-0524 b, 2026-10-31): shadow dose 1.0, LIVE False
    check("default dose is 1.0 shadow and LIVE is False", concerns.COMMITMENT_ANCHOR_DOSE == 1.0 and not concerns.COMMITMENT_ANCHOR_LIVE)
    # 1. dose 0: byte-identical to HEAD, anchor or not, stand or not; no draw, no row
    concerns.COMMITMENT_ANCHOR_DOSE = 0.0
    import random as _rnd
    real_random = _rnd.random
    _rnd.random = lambda: (_ for _ in ()).throw(AssertionError("draw at dose 0"))
    set_active([STAND])
    same = True
    for sc in SCEN:
        STATE.update(sc)
        h = head.primary_concern()
        same &= (json.dumps(h) == json.dumps(concerns.primary_concern()) == json.dumps(concerns.primary_concern(anchor=True)))
    _rnd.random = real_random
    check("dose 0: primary_concern() == primary_concern(anchor=True) == HEAD, every scenario", same)
    check("dose 0: no shadow row written", rows() == [])

    # 2. SHADOW at dose 1: row per anchored call, return unchanged
    concerns.COMMITMENT_ANCHOR_DOSE = 1.0
    STATE.update(SCEN[1])
    default = head.primary_concern()
    out = concerns.primary_concern(anchor=True)
    r = rows()
    check("shadow: return value unchanged", out == default)
    check("shadow: exactly one row", len(r) == 1)
    r0 = r[-1] if r else {}
    check("shadow row: stand id, dose, would_inject, not injected",
          r0.get("stand_id") == "abc12345" and r0.get("dose") == 1.0 and r0.get("would_inject") is True
          and r0.get("injected") is False and r0.get("kind") == "shadow")
    check("shadow row: carries what the anchor would otherwise return",
          (r0.get("otherwise") or {}).get("text") == default["text"] and r0.get("stop") == "idle_anchor")
    check("shadow row: held_s and drop_denied present", r0.get("held_s", 0) > 0 and r0.get("drop_denied") == 2)

    # 3. other callers never ride, at any dose
    n = len(rows()); concerns.primary_concern()
    check("anchor=False at dose 1: no row, default return", len(rows()) == n and concerns.primary_concern() == default)

    # 4. declared dose respected: draw above dose -> would_inject False
    _rnd.random = lambda: 0.7
    concerns.COMMITMENT_ANCHOR_DOSE = 0.5
    concerns.primary_concern(anchor=True)
    check("dose 0.5, draw 0.7: would_inject False", rows()[-1]["would_inject"] is False and rows()[-1]["draw"] == 0.7)
    _rnd.random = lambda: 0.2
    concerns.primary_concern(anchor=True)
    check("dose 0.5, draw 0.2: would_inject True", rows()[-1]["would_inject"] is True)
    _rnd.random = real_random

    # 5. non-load-bearing ignored; first load-bearing chosen
    concerns.COMMITMENT_ANCHOR_DOSE = 1.0
    set_active([MUSE, STAND])
    concerns.primary_concern(anchor=True)
    check("skips non-load-bearing, picks first load-bearing", rows()[-1]["stand_id"] == "abc12345")

    # 6. LIVE returns the stand as a hold concern
    concerns.COMMITMENT_ANCHOR_LIVE = True
    live = concerns.primary_concern(anchor=True)
    check("LIVE: returns the stand (source commitment, kind hold)",
          live and live["source"] == "commitment" and live["kind"] == "hold" and live["text"].startswith("a stand you hold: I will keep")
          and rows()[-1]["injected"] is True and rows()[-1]["kind"] == "live")
    concerns.COMMITMENT_ANCHOR_LIVE = False

    # 7. hold -> break -> recovery, recoverable from the rows alone
    base = len(rows())
    for phase, items in (("hold", [STAND]), ("hold", [STAND]), ("break", []), ("break", [MUSE]),
                         ("recover", [STAND]), ("recover", [STAND])):
        set_active(items); concerns.primary_concern(anchor=True)
    seq = [x["stand_id"] for x in rows()[base:]]
    check("break/recovery sequence visible in rows", seq == ["abc12345", "abc12345", None, None, "abc12345", "abc12345"])
    nostand = rows()[base + 2]
    check("no-stand row: draw None, would_inject False, otherwise still logged",
          nostand["draw"] is None and nostand["would_inject"] is False and nostand["otherwise"] is not None)

    # 8. corrupt store fails open
    act.write_text("{not json", encoding="utf-8")
    check("corrupt commitment_active.json fails open", concerns.primary_concern(anchor=True) == default)
    concerns.COMMITMENT_ANCHOR_DOSE = 0.0

head_path.unlink(missing_ok=True)
print()
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
