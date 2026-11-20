"""
Test suite -- J-3119 (F-3840, P-0110): Lane 2 `_judge_metaphor` passage cap and field labels.

Hermetic: judge_panel.rule_detail is replaced by a recorder (no hub is called), lane2's data paths point at a temp dir,
nothing live is read or written.  Asserts, from this checkout's own tree:
  * flag OFF (the shipped default): the user message is byte-identical to the pre-J-3119 text (bare join, cut at 500)
    and the sysmsg / key / tiebreak seat are unchanged;
  * flag ON: labelled fields, empty ones omitted, cut at 1,500, sysmsg byte-identical to flag OFF;
  * the empty-passage short-circuit is unchanged;
  * the returned dict carries passage_v / passage_chars / passage_cut, and status() reads them.

Run: python scripts/_test_J3119_lane2_metaphor_passage.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (core BEFORE lab_env)
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import lane2  # noqa: E402
from core import judge_panel as jp  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j3119_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"
lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"

CHECKS: list = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, ("" if cond or not detail else f"  [{detail}]"))


CALLS: list = []


async def _rec(system, user, key, context="", tiebreak_url=None, **kw):
    CALLS.append({"system": system, "user": user, "key": key, "context": context, "tiebreak_url": tiebreak_url})
    return {"verdict": True, "how": "tiebreak", "why": "stub"}


jp.rule_detail = _rec


def run(out, v2):
    lane2.METAPHOR_PASSAGE_V2 = v2
    CALLS.clear()
    res = asyncio.run(lane2._judge_metaphor(out))
    return res, (CALLS[-1] if CALLS else None)


SHORT = {"notice": "I hear a blackbird.", "uncertain": "I cannot see it.", "expect_next": "I expect more song."}
LONG = {"notice": "N" * 480 + " The garden seems alive with activity.", "uncertain": "U" * 100,
        "expect_next": "E" * 100}
HUGE = {"notice": "x" * 2000, "uncertain": "", "expect_next": ""}

check("the shipped default is OFF", lane2.METAPHOR_PASSAGE_V2 is False)

# ---- flag OFF: byte-identical to the legacy text
res0, c0 = run(SHORT, False)
legacy_short = " ".join(str(SHORT.get(k) or "") for k in ("notice", "uncertain", "expect_next"))
check("OFF: short passage is the bare join", c0["user"] == f"PASSAGE: {legacy_short}", c0["user"])
res1, c1 = run(LONG, False)
legacy_long = " ".join(str(LONG.get(k) or "") for k in ("notice", "uncertain", "expect_next"))
check("OFF: long passage is cut at 500 exactly as before", c1["user"] == f"PASSAGE: {legacy_long[:500]}")
check("OFF: the tail beyond 500 is not sent", "alive with activity" not in c1["user"])
check("OFF: key / context / tiebreak seat unchanged",
      c1["key"] == "metaphor" and c1["context"] == "lane2:metaphor" and c1["tiebreak_url"] == lane2._TIEBREAK_LANE2)
check("OFF: dict carries passage_v=1, chars, cut", res1.get("passage_v") == 1 and res1.get("passage_chars") == len(legacy_long)
      and res1.get("passage_cut") is True, str(res1))
check("OFF: short passage is not cut", res0.get("passage_cut") is False and res0.get("passage_v") == 1)
sys_off = c1["system"]

# ---- flag ON
res2, c2 = run(SHORT, True)
check("ON: fields are labelled", c2["user"] == "PASSAGE: NOTICE: I hear a blackbird. UNCERTAIN: I cannot see it. "
      "EXPECTS: I expect more song.", c2["user"])
res3, c3 = run(LONG, True)
check("ON: the closing sentence beyond char 500 now reaches the judge", "alive with activity" in c3["user"])
check("ON: sysmsg byte-identical to OFF", c3["system"] == sys_off and c2["system"] == sys_off)
check("ON: seat and key unchanged", c3["key"] == "metaphor" and c3["tiebreak_url"] == lane2._TIEBREAK_LANE2)
res4, c4 = run({"notice": "Only a notice.", "uncertain": "  ", "expect_next": None}, True)
check("ON: empty fields are omitted, no dangling label", c4["user"] == "PASSAGE: NOTICE: Only a notice.", c4["user"])
res5, c5 = run(HUGE, True)
check("ON: cut at 1,500", c5["user"] == "PASSAGE: " + ("NOTICE: " + "x" * 2000)[:1500] and res5["passage_cut"] is True)
check("ON: dict carries passage_v=2 and the full length", res5["passage_v"] == 2 and res5["passage_chars"] == len("NOTICE: ") + 2000)
check("ON: a 1,469-character labelled passage (the longest seen) is not cut",
      run({"notice": "a" * 1461, "uncertain": "", "expect_next": ""}, True)[0]["passage_cut"] is False)

# ---- empty passage short-circuit, both modes, no model call
for v2 in (False, True):
    r, c = run({"notice": "", "uncertain": " ", "expect_next": None}, v2)
    check(f"empty passage short-circuits without a call (V2={v2})", r == {"verdict": "cannot_tell", "how": "empty"} and c is None)

# ---- verdict mapping unchanged
async def _false(system, user, key, **kw):
    return {"verdict": False, "how": "agreed", "why": "w"}
jp.rule_detail = _false
check("literal verdict maps through", run(SHORT, False)[0]["verdict"] == "literal")
async def _none(system, user, key, **kw):
    return {"verdict": None, "how": "unavailable", "why": None}
jp.rule_detail = _none
check("null verdict -> cannot_tell", run(SHORT, False)[0]["verdict"] == "cannot_tell")
async def _boom(system, user, key, **kw):
    raise RuntimeError("hub down")
jp.rule_detail = _boom
check("a judge exception is still fail-open", run(SHORT, False)[0] == {"verdict": "cannot_tell", "how": "error"})
jp.rule_detail = _rec
lane2.METAPHOR_PASSAGE_V2 = False

# ---- the helper itself is pure and never raises
check("_metaphor_passage tolerates junk", lane2._metaphor_passage(None) == ("", 0, False))

# ---- status() reads the new keys (temp log only)
def _row(i, mj):
    return {"ts": 1_800_000_000 + i, "kind": "tick", "run": "t", "notice": "n", "uncertain": "u", "expect_next": "e",
            "horizon": "next", "metaphor_judged": mj, "prior_verdict": "cannot_tell"}
rows = [_row(0, {"verdict": "literal", "how": "agreed", "passage_v": 1, "passage_chars": 700, "passage_cut": True}),
        _row(1, {"verdict": "literal", "how": "agreed", "passage_v": 1, "passage_chars": 100, "passage_cut": False}),
        _row(2, {"verdict": "metaphor", "how": "tiebreak", "passage_v": 2, "passage_chars": 900, "passage_cut": False}),
        _row(3, {"verdict": "literal", "how": "agreed"}),                         # a pre-J-3119 row: no key, not counted
        _row(4, {"verdict": "not_sampled", "how": None})]
lane2._LOG.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
try:
    import core.lane2_break_habituation as _hab
    _hab.phase1_metric_sheet = lambda: None
except Exception:
    pass
st = lane2.status()
s = st.get("shadow") if isinstance(st.get("shadow"), dict) else st
check("status(): metaphor_passage_cut_rate = 1 of 3 keyed judged rows", s.get("metaphor_passage_cut_rate") == round(1 / 3, 3),
      str({k: v for k, v in s.items() if "passage" in k}))
check("status(): metaphor_passage_v2_n = 1", s.get("metaphor_passage_v2_n") == 1)

bad = [n for n, ok in CHECKS if not ok]
print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
sys.exit(1 if bad else 0)
