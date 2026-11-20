"""
Regression for J-3079 (F-3790, P-0019): every pole-gate (_self_clash) call is logged with the poles as returned and
`enum_ok`; the _SELF_CLASH_SYS schema line no longer pre-fills the answer; verdict logic and return shape unchanged.

  [1] prompt text  [2] logged rows (clash, no clash, off-enum, failed, None)  [3] return shape == pre-J-3079
  [4] both call sites tag `site`  [5] pole_gate_status reader  [6] non-live default path refused (fence)  [7] canary

  python scripts/_test_J-3079_pole_gate_log.py     # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/

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


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_NAMES = ("guidance_pole_gate_log.jsonl", "guidance_classify_log.jsonl", "guidance_beliefs.json",
          "guidance_contradictions_shadow.jsonl")
_WATCH = {Path(r"C:\Nascence") / "data" / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES}
_before = {p: _snap(p) for p in _WATCH}
TMP = Path(tempfile.mkdtemp(prefix="J3079_"))
_ORIG_LOG = G._POLE_GATE_LOG

check(Path(core.__file__).resolve().is_relative_to(ROOT), "core imported from this tree")


def stub(reply):
    async def call_json(base_urls, sys_prompt, user, **k):
        assert sys_prompt is G._SELF_CLASH_SYS
        if isinstance(reply, Exception):
            raise reply
        return reply
    return call_json


def rows():
    p = G._POLE_GATE_LOG
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


print("\n[1] prompt text")
S = G._SELF_CLASH_SYS
check(isinstance(S, str), "_SELF_CLASH_SYS is still one str (other tests compare it by identity)")
check('"clash": true' not in S and '"a_pole": "fluid"' not in S and '"b_pole": "durable"' not in S,
      "schema line no longer shows the pre-filled clash answer")
check(S.index("fluid, durable, or neither") < S.index("Output ONLY"), "allowed values are stated in words BEFORE the format line")
check("never answer with any other word" in S, "off-enum words are forbidden in words")

print("\n[2] rows")
G._POLE_GATE_LOG = TMP / "g1.jsonl"
A, B = "I am a transient flow within an endless current", "I am the constant observer that holds my viewpoints"
r1 = asyncio.run(G._self_clash(stub({"a_pole": "Fluid ", "b_pole": "durable", "clash": False}), [], A, B, site="t"))
r2 = asyncio.run(G._self_clash(stub({"a_pole": "neither", "b_pole": "neither"}), [], A, B))
r3 = asyncio.run(G._self_clash(stub({"a_pole": "restoration", "b_pole": "durable"}), [], A, B))
r4 = asyncio.run(G._self_clash(stub(RuntimeError("hub down")), [], A, B))
r5 = asyncio.run(G._self_clash(stub(None), [], A, B))
R = rows()
check(len(R) == 5, f"one row per call, all 5 outcomes ({len(R)})")
check(R[0]["clash"] is True and R[0]["enum_ok"] is True and R[0]["a_pole"] == "Fluid " and R[0]["site"] == "t"
      and R[0]["a"] == A and R[0]["b"] == B and R[0]["off_enum"] == [],
      "fluid/durable: clash True from the CODE (model's own clash=False ignored), poles AS RETURNED, both texts")
check(R[1]["clash"] is False and R[1]["enum_ok"] is True, "neither/neither: enum ok, no clash")
check(R[2]["clash"] is False and R[2]["enum_ok"] is False and R[2]["off_enum"] == ["restoration"],
      "off-enum 'restoration': enum_ok False, listed, no clash")
check(R[3]["call_failed"] is True and R[3]["enum_ok"] is None and R[3]["clash"] is False, "raising call: call_failed row")
check(R[4]["enum_ok"] is False and R[4]["clash"] is False and R[4]["call_failed"] is False,
      "None reply: empty poles are off-enum (enum_ok False), no clash")

print("\n[3] return shape unchanged")
check(r1 == {"clash": True, "a_pole": "fluid", "b_pole": "durable"}, f"clash result {r1}")
check(r2 == {"clash": False, "a_pole": "neither", "b_pole": "neither"}, "no-clash result")
check(r3 == {"clash": False, "a_pole": "restoration", "b_pole": "durable"}, "off-enum result = no clash, poles as before")
check(r4 == {"clash": False, "a_pole": "", "b_pole": ""}, "failure result")

print("\n[4] call sites")
G._POLE_GATE_LOG = TMP / "g2.jsonl"
G._CONTRA_LOG = TMP / "contra.jsonl"
mk = lambda i, t: {"id": f"b{i}", "status": "promoted", "domain": "self", "principle": t, "entrenchment": 0.5,
                   "corroboration_count": 2}
n = asyncio.run(G._scan_contradictions(stub({"a_pole": "fluid", "b_pole": "durable"}), [], [mk(1, A), mk(2, B)]))
check(n == 1 and [x["site"] for x in rows()] == ["scan_contradictions"], f"_scan_contradictions logs site ({n}, {rows()[:1] and rows()[0]['site']})")
import inspect
check('site="integrate_guidance"' in inspect.getsource(G.integrate_guidance), "integrate_guidance passes site")

print("\n[5] reader")
G._POLE_GATE_LOG = TMP / "g1.jsonl"
st = G.pole_gate_status()
check(st["calls"] == 5 and st["clash"] == 1 and st["call_failed"] == 1 and st["enum_ok_false"] == 2
      and st["off_enum_words"] == {"restoration": 1, "(empty)": 2} and st["clash_rate"] == 0.25 and st["off_enum_rate"] == 0.5, str(st))
check(G.pole_gate_status(since_ts=9e12)["calls"] == 0, "since_ts filters")
G._POLE_GATE_LOG = TMP / "missing.jsonl"
check(G.pole_gate_status()["calls"] == 0, "missing log -> zeros, no raise")

print("\n[6] fence: non-live default path")
G._POLE_GATE_LOG = _ORIG_LOG
try:
    r = asyncio.run(G._self_clash(stub({"a_pole": "fluid", "b_pole": "durable"}), [], A, B))
    check(r["clash"] is True, "verdict still returned when the log write is refused")
except Exception as e:
    check(False, f"raised {e!r}")
check(not _ORIG_LOG.exists() or _snap(_ORIG_LOG) == _before.get(_ORIG_LOG), "default data/ path not written by a non-live process")

print("\n[7] canary")
check(all(_snap(p) == _before[p] for p in _WATCH), "Du's real guidance stores byte-identical")

print("\nALL OK" if not FAILS else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
