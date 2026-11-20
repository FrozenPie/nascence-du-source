"""
Proof for J-3162 / D-0550: the T4 legacy single-pass author is gradeable -- its lived `material` fragments reach the
decoupled judge and the weak filter as evidence. No network, nothing under the live data dir written.

  [1] _t4_legacy_evidence: formats '[origin] text', 200-char cut, newline flattening, cap 8, skips empty/garbage rows,
      never raises, [] for empty/None.
  [2] source checks: the judge-shadow block and the probation weak-filter both swap in the legacy evidence only when
      `not distinct and T4_LEGACY_EVIDENCE`; the admission bar line (WARRANTED_ADMIT_MIN, _grounded) is unchanged;
      the flag constant exists and is True; the chain path (`distinct`) still reads chain['evidence'].
  [3] with the evidence, grade_self_revision's user message no longer contains '(no lived evidence offered)'
      (stubbed aiohttp captures the payload); with [] it still does.
  [4] SUB-QUESTION (J-3054): top_contradiction has no rest filter. With one tension whose label is RESTING,
      _t4_distinct_tensions returns [] (so T4 takes the legacy path) while top_contradiction still returns that rested
      label -- i.e. during a rest the legacy prompt WOULD re-introduce the rested question. Asserted as observed
      behaviour (documents the gap; fixing it is a separate job).

  python scripts/_test_J-3162_legacy_gradeable.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import asyncio, re, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
from core import left_lane as ll, tension_ledger as tl  # noqa: E402
from nodes import subconscious_node as sn  # noqa: E402

assert Path(sn.__file__).resolve().parent.parent == ROOT, sn.__file__
fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# [1]
f = sn.SubconsciousNode._t4_legacy_evidence
mat = [{"content": "a\nb" + "x" * 300, "origin": "dream"}, {"content": "", "origin": "dream"}, {"content": "hello", "origin": None},
       None, {"origin": "x"}] + [{"content": f"m{i}", "origin": "session_summary"} for i in range(12)]
ev = f(mat)
check("[1] cap 8", len(ev) == 8)
check("[1] origin prefix + newline flattened + 200 cut", ev[0].startswith("[dream] a b") and len(ev[0]) == len("[dream] ") + 200)
check("[1] None origin -> lived, empty skipped", ev[1] == "[lived] hello")
check("[1] empty/None -> []", f([]) == [] and f(None) == [])
check("[1] SubconsciousNode flag True", sn.T4_LEGACY_EVIDENCE is True)

# [2]
src = Path(sn.__file__).read_text(encoding="utf-8")
check("[2] judge block swaps in legacy evidence",
      "if not distinct and T4_LEGACY_EVIDENCE:   # J-3162 / D-0550: the legacy path is gradeable\n"
      "                _sevlist = self._t4_legacy_evidence(material)" in src)
check("[2] weak filter swaps in legacy evidence",
      "_evl = self._t4_legacy_evidence(material)" in src and "_evl, _held, _excl)" in src)
check("[2] chain path unchanged", 'chain.get("evidence", "") if (distinct and isinstance(chain, dict)) else ""' in src)
check("[2] admission bar unchanged",
      "_admit = ((_grounded and float(_judge) >= _pi.WARRANTED_ADMIT_MIN)" in src)

# [3]
captured = {}


class _Resp:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": '{"warranted": 0.7, "feedback": "x"}'}}


class _Sess:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None):
        captured["user"] = json["messages"][1]["content"]
        return _Resp()


class _Lat:
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


ll.aiohttp.ClientSession = lambda *a, **k: _Sess()
ll._note_call = lambda payload: None
ll._tel_lat.raw_http_latency = lambda *a, **k: _Lat()
res, meta = asyncio.run(ll.grade_self_revision_traced("old", "new", ev))
check("[3] judge ok with evidence", res and res["warranted"] == 0.7 and meta["judge_status"] == "ok")
check("[3] evidence shown, placeholder absent", "(no lived evidence offered)" not in captured["user"] and "[dream] a b" in captured["user"])
asyncio.run(ll.grade_self_revision_traced("old", "new", []))
check("[3] empty evidence still prints the placeholder", "(no lived evidence offered)" in captured["user"])

# [4]
import core.memory.store as store  # noqa: E402
LABEL = "I keep claiming certainty about recall that my own record contradicts"
tensions = [{"member_event_ids": ["e1"], "label": LABEL}]
now = time.time()
store.get_event_sources = lambda ids: {i: ("critic_rejection", now - 3600) for i in ids}
store.get_event_corrections = lambda ids: {}
node = object.__new__(sn.SubconsciousNode)
toks = sorted({w for w in LABEL.lower().split() if len(w) >= 4})
node._state = {"t4_rests": [{"toks": toks, "until": now + 86400}]}
distinct = node._t4_distinct_tensions(tensions)
top = tl.top_contradiction(tensions)
check("[4] resting question -> docket empty (legacy path taken)", distinct == [])
check("[4] top_contradiction still returns the rested question (no rest filter) -> legacy prompt re-introduces it",
      bool(top) and top["label"].lower().split()[:3] == LABEL.lower().split()[:3])

print("\nALL OK" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
