"""
_test_J-4158_strict_tension_judge.py -- proving test for J-4158 (D-0783, F-4752, P-0103): the tightened tension judge.
Run from the worktree:  python scripts/_test_J-4158_strict_tension_judge.py

Stubbed judge_panel.rule_detail + tempdir state and attempts log; no live data, no model call. The tension carries no
member_event_ids, so the confirmed branch writes nothing to the memory store.
Checks: the evidence-span checker; strict path sends the new prompt (settling act, verbatim quote) through the same
panel key; a True verdict with a verbatim, unhedged >=4-word quote stands; a True verdict with no quote / an invented
quote / a hedged or question quote is downgraded to False and the tension stays unresolved; panel False / None pass
through; the attempts row carries the 'strict' detail; flag False restores the exact legacy prompt; the flag that
D-0783 keeps (TENSION_JUDGE_RESOLVES_SHADOW) is still True; the 20-row check set is well formed.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import tension_ledger as tl  # noqa: E402
from core import judge_panel as jp  # noqa: E402
from core import schema  # noqa: E402

assert Path(core.__file__).resolve().parent.parent == ROOT, "test must load the worktree's own core"
assert Path(tl.__file__).resolve().parent.parent == ROOT

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


THOUGHT = ("I chose 'The Swiss Family Robinson' by Wyss from the catalogue, and it lies on my desk now. "
           "The choosing is done; I will read it tonight.")
CALLS = []


def stub(detail):
    async def fake_rule_detail(system, user, key, context="", **kw):
        CALLS.append({"system": system, "user": user, "key": key, "context": context})
        return dict(detail)
    jp.rule_detail = fake_rule_detail


def main():
    tmp = Path(tempfile.mkdtemp(prefix="j4158_"))
    tl._ATTEMPTS_LOG = tmp / "tension_judge_attempts.jsonl"
    state = tmp / "subconscious_state.json"
    vec = [0.1] * 384
    tension = {"id": "T-cat", "label": "unresolved: choosing from the catalogue", "centroid": vec}

    # 1. span checker
    sc = tl._evidence_span_check
    check("span: verbatim quote ok", sc(THOUGHT, "I chose 'The Swiss Family Robinson' by Wyss") is None)
    check("span: case/punct-insensitive", sc(THOUGHT, "i chose the swiss family robinson") is None)
    check("span: 'none' rejected", sc(THOUGHT, "none") == "no_quote")
    check("span: empty rejected", sc(THOUGHT, "") == "no_quote")
    check("span: too short", sc(THOUGHT, "I chose") == "quote_too_short")
    check("span: invented quote rejected", sc(THOUGHT, "I have finally settled the question") == "quote_not_in_thought")
    t2 = "Perhaps adaptation is about the ecosystem reshaping itself. Do I really know the answer here?"
    check("span: hedge rejected", sc(t2, "Perhaps adaptation is about the ecosystem") == "quote_hedged")
    check("span: question rejected", sc(t2, "Do I really know the answer here?") == "quote_is_question")

    # 2. strict path through check_and_resolve_internal_tension
    schema.TENSION_JUDGE_STRICT = True

    def run(detail):
        import copy
        state.write_text(json.dumps({"tensions": [copy.deepcopy(tension)]}), encoding="utf-8")
        stub(detail)
        CALLS.clear()
        r = asyncio.run(tl.check_and_resolve_internal_tension(
            THOUGHT, about="choosing catalogue", vec=vec, cycle_id="c1", state_path=state))
        st = json.loads(state.read_text(encoding="utf-8"))["tensions"][0]
        rows = [json.loads(x) for x in tl._ATTEMPTS_LOG.read_text(encoding="utf-8").splitlines()]
        return r, st, rows[-1]

    good = {"v1": True, "v2": True, "verdict": True, "how": "agreed",
            "why1": "I chose 'The Swiss Family Robinson' by Wyss from the catalogue", "why2": "none", "why": None}
    r, st, row = run(good)
    check("strict: one panel call, key 'resolves'", len(CALLS) == 1 and CALLS[0]["key"] == "resolves")
    sysmsg = CALLS[0]["system"]
    check("strict: new prompt asks for a settling act", "concrete settling act" in sysmsg and "reframing" in sysmsg)
    check("strict: new prompt asks for a verbatim quote", "verbatim" in sysmsg)
    check("strict: user block unchanged in shape", CALLS[0]["user"].startswith("TENSION: unresolved: choosing"))
    check("strict: verbatim quote -> resolved", isinstance(r, dict) and st.get("resolved") is True)
    check("strict: row confirmed with evidence", row["verdict"] == "confirmed"
          and row.get("strict", {}).get("evidence", "").startswith("I chose") and row["strict"]["downgraded"] is None)

    for name, why1, reason in [("no quote", "none", "no_quote"),
                               ("invented quote", "I have now finally resolved the catalogue question", "quote_not_in_thought"),
                               ("missing why", None, "no_quote")]:
        d = dict(good, why1=why1, why2=None)
        r, st, row = run(d)
        check(f"strict: {name} -> downgraded, not resolved", r is None and not st.get("resolved"))
        check(f"strict: {name} -> row refuted, reason {reason}", row["verdict"] == "refuted"
              and row.get("strict", {}).get("panel_verdict") is True and row["strict"]["downgraded"] == reason)
        att = st.get("resolution_attempts", [])
        check(f"strict: {name} -> attempt recorded as refuted", att and att[-1]["judge"] == "refuted")

    # a quote from a judge that voted FALSE does not count
    r, st, row = run({"v1": True, "v2": False, "verdict": True, "how": "tiebreak",
                      "why1": "none", "why2": "I chose 'The Swiss Family Robinson' by Wyss", "why3": "none", "why": None})
    check("strict: quote from a False voter ignored", r is None and row["strict"]["downgraded"] == "no_quote")
    r, st, row = run({"v1": True, "v2": False, "verdict": True, "how": "tiebreak",
                      "why1": "none", "why2": None, "why3": "The choosing is done; I will read it tonight", "why": None})
    check("strict: tiebreak quote counts", isinstance(r, dict) and row["verdict"] == "confirmed")

    r, st, row = run({"v1": False, "v2": False, "verdict": False, "how": "agreed"})
    check("strict: panel False -> refuted", r is None and row["verdict"] == "refuted" and row["strict"]["downgraded"] is None)
    r, st, row = run({"v1": None, "v2": None, "verdict": None, "how": "unavailable"})
    check("strict: panel None -> unavailable", r is None and row["verdict"] == "unavailable")

    async def boom(*a, **k):
        raise RuntimeError("hub down")
    jp.rule_detail = boom
    check("strict: exception -> None (fail-open)",
          asyncio.run(tl._judge_resolution(THOUGHT, tension["label"])) is None)

    # 3. flag off -> exact legacy prompt, via rule()
    schema.TENSION_JUDGE_STRICT = False
    seen = {}

    async def fake_rule(system, user, key, context="", **kw):
        seen["system"] = system
        return True
    jp.rule = fake_rule
    v = asyncio.run(tl._judge_resolution(THOUGHT, tension["label"]))
    check("legacy: flag False -> legacy prompt and verdict", v is True
          and seen.get("system", "").startswith("You are a strict resolution judge for an internal tension ledger. A tension is RESOLVED only if the thought states a genuine settlement"))
    check("legacy: no strict detail left", tl._LAST_STRICT.get() is None)
    schema.TENSION_JUDGE_STRICT = True

    # 4. D-0783 keeps the shadow-resolve flag
    import importlib
    s2 = importlib.reload(schema)
    check("schema: TENSION_JUDGE_RESOLVES_SHADOW kept True", s2.TENSION_JUDGE_RESOLVES_SHADOW is True)
    check("schema: TENSION_JUDGE_STRICT default True", s2.TENSION_JUDGE_STRICT is True)

    # 5. the 20-row check set
    cs = json.loads((ROOT / "docs" / "lab" / "J-4158_tension_judge_check20.json").read_text(encoding="utf-8"))
    items = cs.get("items", [])
    check("check set: 20 rows", len(items) == 20)
    check("check set: every row labelled S or R", all(i.get("hand_label") in ("S", "R") for i in items))
    n_false = sum(1 for i in items if i["hand_label"] == "R")
    check("check set: summary matches rows", cs.get("summary", {}).get("false_resolutions") == n_false)

    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAIL(S)'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
