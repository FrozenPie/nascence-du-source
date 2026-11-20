"""
Test suite -- J-3127 / F-3854 / P-0111: Lane 2 `_coherence_check` asks the panel for a one-clause "why" so a verdict can
be audited, returns it as `why` beside verdict and how, and `status()` reports `coherence_why_coverage`.  Nothing else in
the sysmsg changes, the key stays "coherent", the tiebreak seat and the call frequency are untouched.

Hermetic: the panel (`core.judge_panel.rule_detail`) is a recording stub, no socket is opened, lane2's `_LOG` is a temp
file, and the live shadow log is stat-checked before and after.  The live replay of 20 stored pairs (does asking for a
why move the coherent/incoherent mix) needs the panel hubs and is NOT run here: see scripts/lane2_coherence_why_replay_J3127.py.

Run: python scripts/_test_J-3127_coherence_why.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import lane2  # noqa: E402
from core import judge_panel as _jp  # noqa: E402

_ORIG_LOG = lane2._LOG
_before = (_ORIG_LOG.stat().st_size, _ORIG_LOG.stat().st_mtime_ns) if _ORIG_LOG.exists() else None
FAILS: list = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


SEEN: list = []
REPLY: dict = {}


async def _stub(system, user, key, context="", num_predict=0, tiebreak_url=None, **kw):
    SEEN.append({"system": system, "user": user, "key": key, "context": context, "tiebreak_url": tiebreak_url,
                 "num_predict": num_predict})
    return dict(REPLY)


_jp.rule_detail = _stub


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


STORE = {"factual": [{"ts": 1, "notice": "I hear waves on shingle.", "place": "shore", "standpoint": "at_the_path_foot"}]}
PERC = {"world": {"place": "shore"}, "standpoint": "at_the_path_foot"}


def call(reply):
    REPLY.clear()
    REPLY.update(reply)
    SEEN.clear()
    return run(lane2._coherence_check({"notice": "I hear a kingfisher."}, STORE, PERC))


# A. the ask
r = call({"verdict": True, "how": "agreed", "why": "same shore, gradual detail"})
s = SEEN[-1]
check("A1 key unchanged 'coherent', context and tiebreak seat unchanged",
      s["key"] == "coherent" and s["context"] == "lane2:coherence" and s["tiebreak_url"] == lane2._TIEBREAK_LANE2)
check("A2 sysmsg ends with the why-bearing JSON instruction",
      s["system"].endswith('Output ONLY JSON: {"coherent": true|false, "why": "<one short clause>"}'), s["system"][-90:])
check("A3 num_predict not passed (the shared 200 default stays)", not s["num_predict"])

base = subprocess.run(["git", "-C", str(ROOT), "show", "223c95c6:core/lane2.py"], capture_output=True, check=True).stdout
base_src = base.decode("utf-8-sig").replace("\r\n", "\n")
i = base_src.index('sysmsg = ("You judge whether a NEW observation is PLAUSIBLE')
j = base_src.index('usr = f"RECENT RECORD', i)
ns = {}
exec("_x = " + base_src[i:j].split("=", 1)[1].strip(), ns)
old_sys = ns["_x"]
tail = 'Output ONLY JSON: {"coherent": true|false}'
check("A4 every word before the final instruction is byte-identical to master 223c95c6",
      old_sys.endswith(tail) and s["system"][: -len('Output ONLY JSON: {"coherent": true|false, "why": "<one short clause>"}')]
      == old_sys[: -len(tail)])

# B. the return
check("B1 verdict, how and why returned", r.get("verdict") == "coherent" and r.get("how") == "agreed"
      and r.get("why") == "same shore, gradual detail", str(r))
r = call({"verdict": False, "how": "tiebreak", "why": "fire reversed"})
check("B2 incoherent + why", r["verdict"] == "incoherent" and r["why"] == "fire reversed", str(r))
r = call({"verdict": True, "how": "agreed"})
check("B3 model gave no why -> why None (key present), shape otherwise unchanged",
      r.get("why") is None and "why" in r and r["verdict"] == "coherent" and r.get("hist_v") == 2, str(r))
r = call({"verdict": None, "how": "unavailable", "why": None})
check("B4 unavailable -> cannot_tell, why None", r["verdict"] == "cannot_tell" and r["why"] is None, str(r))
check("B5 early exits keep their old shape (no model call)",
      run(lane2._coherence_check({"notice": ""}, STORE, PERC)) == {"verdict": "cannot_tell", "how": "empty"}
      and run(lane2._coherence_check({"notice": "x"}, {"factual": []}, PERC)) == {"verdict": "cannot_tell", "how": "no-history"})

# C. the resolved why really comes from judge_panel.rule_detail (the real one, with a stubbed _ask)
src = (ROOT / "core" / "judge_panel.py").read_text(encoding="utf-8")
# J-4052 re-pin: rule_detail is now a thin wrapper (J-3761) around _rule_detail_impl
check("C1 judge_panel.rule_detail returns a resolved 'why' key", '"why"' in src[src.index("async def _rule_detail_impl"):src.index("async def _rule_detail_impl") + 9000])

# D. tick() logs the coherence dict verbatim, so why reaches the shadow log
lsrc = (ROOT / "core" / "lane2.py").read_text(encoding="utf-8")
check("D1 tick row stores the whole coherence dict", re.search(r'"coherence": coherence,', lsrc) is not None)
check("D2 call frequency untouched: coherence still awaited every tick (no sampling flag added)",
      "coherence = await _coherence_check(out, store, percepts)" in lsrc and "_COHERENCE_SAMPLE" not in lsrc)

# E. status() reader
def row(i, coh):
    return {"kind": "tick", "ts": 1000 + i, "notice": f"n{i}", "expect_next": f"e{i}", "coherence": coh,
            "grounding": {"grounded_share": 1.0}}


rows = ([row(i, {"verdict": "coherent", "how": "agreed", "why": "fine"}) for i in range(8)]
        + [row(10, {"verdict": "incoherent", "how": "tiebreak", "why": "reversed"})]
        + [row(11, {"verdict": "coherent", "how": "agreed", "why": None})]
        + [row(12, {"verdict": "cannot_tell", "how": "unavailable", "why": None})]    # not judged -> excluded
        + [row(20 + i, {"verdict": "coherent", "how": "agreed"}) for i in range(5)])   # OLD rows: no key -> excluded
tmp = Path(tempfile.mkdtemp(prefix="J-3127_"))
lane2._LOG = tmp / "lane2_shadow.jsonl"
lane2._LOG.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
try:
    st = lane2.status()
    lane2._LOG.write_text("\n".join(json.dumps(x) for x in rows[-5:]) + "\n", encoding="utf-8")
    st_old = lane2.status()
finally:
    lane2._LOG = _ORIG_LOG
cov = st.get("coherence_why_coverage")
check("E1 coverage counts only judged rows that carry the why key (9 of 10)",
      cov == {"rate": 0.9, "with_why": 9, "judged": 10}, str(cov))
check("E2 rows from before J-3127 only -> rate None, not 0",
      (st_old.get("coherence_why_coverage") or {}).get("rate") is None
      and st_old["coherence_why_coverage"]["judged"] == 0, str(st_old.get("coherence_why_coverage")))
check("E3 pooled incoherence_rate unchanged by the new key (1 incoherent of 15 judged)", st.get("incoherence_rate") == round(1 / 15, 3), str(st.get("incoherence_rate")))

after = (_ORIG_LOG.stat().st_size, _ORIG_LOG.stat().st_mtime_ns) if _ORIG_LOG.exists() else None
check("Z1 live shadow log untouched", _before == after)
print()
print(f"{'ALL PASS' if not FAILS else 'FAILED: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
