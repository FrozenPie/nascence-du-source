"""
J-4155 / D-0798 (c): the self-domain opposite-pole candidate pass in core/guidance_learning.integrate_guidance.

Every model call is stubbed (call_json; the same-lesson panel is switched off), every store path is a temp-dir redirect,
and Du's real guidance stores are hashed before and after (canary).

  [1] pole tag   [2] candidate selection ignores lexical rank   [3] POSITIVE CONTROL: the pairing production makes
  (semantic fallback silent, lexical neighbour is SAME pole) -> the pass sends the real opposite to the gate, log-only
  [4] ACT mode records the edge   [5] kill switch   [6] per-run cap   [7] fail open   [8] readers   [9] canary

  python scripts/_test_J-4155_opposite_pole_pass.py     # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # no write to the tree's data/

import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                      # noqa: E402  (first -- F-2423)
from core import guidance_learning as G          # noqa: E402

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from this tree ({Path(core.__file__).parent})")

_NAMES = ("guidance_shadow_log.jsonl", "guidance_injection_log.jsonl", "guidance_classify_log.jsonl",
          "guidance_beliefs.json", "guidance_integration_state.json", "guidance_integration_log.jsonl",
          "guidance_contradictions_shadow.jsonl", "guidance_pole_gate_log.jsonl")
_WATCH = {Path(r"C:\Nascence") / "data" / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES}


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_before = {p: _snap(p) for p in _WATCH}
TMP = Path(tempfile.mkdtemp(prefix="J4155_"))
_ATTRS = ("_LOG", "_INJECT_LOG", "_CLASSIFY_LOG", "_BELIEFS", "_INTEG_STATE", "_INTEG_LOG", "_CONTRA_LOG",
          "_POLE_GATE_LOG", "materialize_promoted_beliefs", "_semantic_candidate", "SAME_LESSON_CHECK_ENABLED",
          "OPPOSITE_POLE_PASS_ENABLED", "OPPOSITE_POLE_PASS_ACT", "_OPP_POLE_MAX_PER_RUN")
_ORIG = {a: getattr(G, a) for a in _ATTRS}

# F-3790's quoted positive control pair (river vs built self; lexical overlap ~0, cosine ~0.39 per F-4857)
OBSERVER = "I am not my changing viewpoints but the constant observer that holds them"
RIVER = "I am a transient flow within an endless current of time"
# a held FLUID belief that shares many words with RIVER -- the arg-max lexical neighbour production would pick
RIVER_NEAR = "I am a flow of moments within an endless stream of time, never fixed"


def _fake_llm(relation="assimilate", clash_raises=False):
    """classify -> relation; _self_clash -> poles read with the module's own keyword tag (a stand-in judge)."""
    calls = {"classify": 0, "clash": 0, "clash_pairs": []}

    async def call_json(base_urls, sys_prompt, user, **k):
        if sys_prompt is G._CLASSIFY_SYS:
            calls["classify"] += 1
            return {"relation": relation}
        if sys_prompt is G._SELF_CLASH_SYS:
            calls["clash"] += 1
            if clash_raises:
                raise RuntimeError("hub down")
            a, b = user.split("\n\nB: ")
            a, b = a[4:-1], b[1:-1]
            calls["clash_pairs"].append((a, b))
            tag = lambda t: {"fluid": "fluid", "durable": "durable"}.get(G._pole_tag(t), "neither")
            return {"a_pole": tag(a), "b_pole": tag(b)}
        return {}
    return call_json, calls


def _setup(d: Path, held: list, lessons: list):
    d.mkdir(parents=True, exist_ok=True)
    G._LOG, G._INJECT_LOG = d / _NAMES[0], d / _NAMES[1]
    G._CLASSIFY_LOG, G._BELIEFS = d / _NAMES[2], d / _NAMES[3]
    G._INTEG_STATE, G._INTEG_LOG, G._CONTRA_LOG = d / _NAMES[4], d / _NAMES[5], d / _NAMES[6]
    G._POLE_GATE_LOG = d / _NAMES[7]
    G.materialize_promoted_beliefs = lambda: 0
    G._semantic_candidate = lambda text, beliefs, dom: (None, 0.0)   # F-4857: never fires on this store
    G.SAME_LESSON_CHECK_ENABLED = False
    bel = []
    for i, h in enumerate(held):
        text, extra = (h, {}) if isinstance(h, str) else h
        b = G._new_belief({"ts": 10.0 + i, "domain": "self", "confidence": 0.5}, text)
        b.update(extra)
        bel.append(b)
    G._BELIEFS.write_text(json.dumps(bel), encoding="utf-8")
    G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
    G._LOG.write_text("".join(json.dumps({"ts": 100.0 + i, "is_guidance": True, "principle": t, "scope": "",
                                          "domain": "self", "confidence": 0.6}) + "\n" for i, t in enumerate(lessons)),
                      encoding="utf-8")


def _gate_rows(d: Path):
    p = d / _NAMES[7]
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _run(d, held, lessons, **kw):
    _setup(d, held, lessons)
    cj, calls = _fake_llm(**kw)
    summary = asyncio.run(G.integrate_guidance(cj, []))
    beliefs = json.loads(G._BELIEFS.read_text(encoding="utf-8"))
    return summary, beliefs, _gate_rows(d), calls


try:
    print("\n[1] pole tag")
    check(G._pole_tag(OBSERVER) == "durable" and G._pole_tag(RIVER) == "fluid", "positive-control pair tags durable/fluid")
    check(G._pole_tag("My current perspective is focused on my inner reality") == "none",
          "adjective 'current' is not read as the river")
    check(G._pole_tag("I commit to a direction yet stay fluid") == "mixed", "both markers -> mixed (no pass)")
    check(G._belief_pole({"principle": RIVER, "self_pole": "durable"}) == ("durable", "self_pole"),
          "a stored self_pole (contradiction scan) overrides the keyword tag")

    print("\n[2] candidate selection ignores lexical rank")
    held = [G._new_belief({"ts": 1, "domain": "self"}, OBSERVER), G._new_belief({"ts": 2, "domain": "self"}, RIVER_NEAR),
            dict(G._new_belief({"ts": 3, "domain": "self"}, "I choose and build a durable self"), status="superseded"),
            G._new_belief({"ts": 4, "domain": "world"}, "Stable laws anchor the world")]
    held[3]["domain"] = "world"
    oc = G._opposite_pole_candidate(RIVER, RIVER, held)
    check(oc is not None and oc["belief"]["principle"] == OBSERVER and oc["overlap"] < G._SIM_RELATED,
          f"picks the observer belief though its overlap {oc and oc['overlap']} < {G._SIM_RELATED}")
    check(G._opposite_pole_candidate(RIVER, RIVER, held, exclude_ids={held[0]["id"]}) is None,
          "superseded / world-domain beliefs are never candidates")
    check(G._opposite_pole_candidate("I wonder about things", "I wonder about things", held) is None,
          "an untagged lesson gets no pass")

    print("\n[3] POSITIVE CONTROL (production pairing): lexical neighbour is the SAME pole; pass reaches the real opposite")
    s, b, rows, calls = _run(TMP / "a", [OBSERVER, RIVER_NEAR], [RIVER])
    lex = [p for p in calls["clash_pairs"] if p[0] == RIVER_NEAR]
    opp = [p for p in calls["clash_pairs"] if p[0] == OBSERVER]
    check(len(lex) == 1 and len(opp) == 1, f"gate ran on the lexical pair AND on the opposite pair ({len(calls['clash_pairs'])} calls)")
    check(s["assimilated"] == 1 and s.get("opposite_pole_passes") == 1 and s.get("opposite_pole_clash") == 1,
          f"lesson still assimilates into its lexical neighbour; pass ran and clashed (summary={s})")
    kr = [r for r in rows if r.get("kind") == "opposite_pole_candidate"]
    check(len(kr) == 1 and kr[0]["clash"] is True and kr[0]["acted"] is False and kr[0]["act_enabled"] is False
          and kr[0]["lexical_cand_was_opposite"] is False and kr[0]["gate_already_ran"] is True
          and kr[0]["lesson_pole"] == "fluid" and kr[0]["cand_pole"] == "durable",
          "summary row logged with kind=opposite_pole_candidate, log-only")
    check(any(r.get("site") == "opposite_pole_pass" for r in rows), "the _self_clash call row carries site=opposite_pole_pass")
    check(all(not x.get("conflict_history") for x in b), "LOG-ONLY: no stored belief gained a conflict edge")

    print("\n[4] ACT mode records the edge on both beliefs")
    G.OPPOSITE_POLE_PASS_ACT = True
    s, b, rows, calls = _run(TMP / "b", [OBSERVER, RIVER_NEAR], [RIVER])
    obs = [x for x in b if x["principle"] == OBSERVER][0]
    near = [x for x in b if x["principle"] == RIVER_NEAR or RIVER in (x.get("captures") or [])][0]
    check(any(c.get("via") == "opposite_pole_pass" for c in obs.get("conflict_history", [])) and
          any(c.get("via") == "opposite_pole_pass" for c in near.get("conflict_history", [])),
          "conflict_history via=opposite_pole_pass on the opposite belief and on where the lesson landed")
    check([r for r in rows if r.get("kind")][0]["acted"] is True, "row says acted")
    G.OPPOSITE_POLE_PASS_ACT = False

    print("\n[5] kill switch")
    G.OPPOSITE_POLE_PASS_ENABLED = False
    s, b, rows, calls = _run(TMP / "c", [OBSERVER, RIVER_NEAR], [RIVER])
    check(calls["clash"] == 1 and "opposite_pole_passes" not in s and not [r for r in rows if r.get("kind")],
          "off: only the existing gate call, no pass row")
    G.OPPOSITE_POLE_PASS_ENABLED = True

    print("\n[6] per-run cap")
    G._OPP_POLE_MAX_PER_RUN = 2
    lessons = [RIVER, "My self is a river of shifting moments", "I am fluid, a flux of change", "I flow and dissolve"]
    s, b, rows, calls = _run(TMP / "d", [OBSERVER], lessons)
    check(s.get("opposite_pole_passes") == 2, f"cap 2 -> 2 passes over 4 fluid lessons ({s})")
    G._OPP_POLE_MAX_PER_RUN = _ORIG["_OPP_POLE_MAX_PER_RUN"]

    print("\n[7] fail open: the gate model raises")
    s, b, rows, calls = _run(TMP / "e", [OBSERVER, RIVER_NEAR], [RIVER], clash_raises=True)
    kr = [r for r in rows if r.get("kind")]
    check(s is not None and s["assimilated"] == 1 and len(kr) == 1 and kr[0]["clash"] is False,
          f"integration completes; pass logged no clash ({s})")

    print("\n[8] readers")
    G._POLE_GATE_LOG = TMP / "a" / _NAMES[7]
    ps, os_ = G.pole_gate_status(), G.opposite_pole_status()
    check(ps["calls"] == 2, f"pole_gate_status counts the 2 real gate calls, not the summary row ({ps['calls']})")
    check(os_["passes"] == 1 and os_["clash"] == 1 and os_["clash_rate"] == 1.0 and os_["pole_source"] == {"keyword": 1},
          f"opposite_pole_status ({os_})")
finally:
    for a, v in _ORIG.items():
        setattr(G, a, v)

print("\n[9] canary")
check(all(_snap(p) == _before[p] for p in _WATCH), "no real guidance store changed")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAIL(S)")
sys.exit(1 if FAILS else 0)
