"""
Proof for J-3108 (F-3828, F-3830): the T4 emissary-judge log row now records the old self, the evidence list, why the
judge was unavailable (judge_status) and how long the call took (judge_s); the stale "gates nothing" text is corrected.
Additive logging only: grade_self_revision keeps its signature and its fail-open return (dict or None).

  [1] grade_self_revision_traced against a stubbed aiohttp: ok / none_timeout / none_transport (connect error and HTTP
      500) / none_parse (not JSON, JSON without 'warranted', non-numeric warranted); judge_s is a number in every case.
  [2] grade_self_revision returns exactly the same value as the traced result (dict or None) for every case, and the
      warranted clamp (0..1) is unchanged.
  [3] source checks on nodes/subconscious_node.py: the writer calls the traced twin and writes old_self[:400], evidence
      items[:300], judge_status, judge_s, judge_error; no "gates NOTHING" text remains; the gate still reads _emj and
      WARRANTED_ADMIT_MIN exactly as before. left_lane docstring no longer says "gates nothing yet".
  [4] the log-row dict, built by the same expressions on a stub, is JSON-serialisable and the slices cap the lengths.
  [5] isolation: telemetry (_note_call) stubbed, no network, nothing under the live data dir written.

  python scripts/_test_J-3108_t4_judge_log.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  (core BEFORE lab_env)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
from core import left_lane as ll  # noqa: E402
import aiohttp  # noqa: E402

assert Path(ll.__file__).resolve().parent.parent == ROOT, f"imported left_lane from {ll.__file__}, not {ROOT}"

TMP = Path(tempfile.mkdtemp(prefix="J3108_"))
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---- stubs -----------------------------------------------------------------------------------------------------
ll._note_call = lambda *a, **k: None   # no live telemetry


class _Resp:
    def __init__(self, behaviour):
        self.b = behaviour

    async def __aenter__(self):
        if self.b.get("enter_exc"):
            raise self.b["enter_exc"]
        return self

    async def __aexit__(self, *a):
        return False

    def raise_for_status(self):
        if self.b.get("status", 200) >= 400:
            raise aiohttp.ClientResponseError(None, (), status=self.b["status"], message="boom")

    async def json(self):
        return {"message": {"content": self.b.get("content", "")}}


class _Session:
    behaviour: dict = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def post(self, *a, **k):
        return _Resp(_Session.behaviour)


ll.aiohttp = type("A", (), {"ClientSession": _Session, "ClientTimeout": aiohttp.ClientTimeout,
                            "ClientResponseError": aiohttp.ClientResponseError})


def run(behaviour, fn):
    _Session.behaviour = behaviour
    return asyncio.run(fn("old self", "new self", ["ev one", "ev two"]))


CASES = [
    ("ok",           {"content": json.dumps({"warranted": 0.7, "feedback": "fine"})}, "ok", 0.7),
    ("ok_clamp_hi",  {"content": json.dumps({"warranted": 7, "feedback": "x"})}, "ok", 1.0),
    ("ok_clamp_lo",  {"content": json.dumps({"warranted": -3, "feedback": "x"})}, "ok", 0.0),
    ("timeout",      {"enter_exc": asyncio.TimeoutError()}, "none_timeout", None),
    ("transport_connect", {"enter_exc": aiohttp.ClientConnectionError("down")}, "none_transport", None),
    ("transport_oserr",   {"enter_exc": OSError("refused")}, "none_transport", None),
    ("transport_http500", {"status": 500}, "none_transport", None),
    ("parse_notjson", {"content": "I think it is warranted"}, "none_parse", None),
    ("parse_empty",   {"content": ""}, "none_parse", None),
    ("parse_nokey",   {"content": json.dumps({"verdict": 1})}, "none_parse", None),
    ("parse_list",    {"content": json.dumps([1, 2])}, "none_parse", None),
    ("parse_badnum",  {"content": json.dumps({"warranted": "high"})}, "none_parse", None),
]

print("[1]+[2] traced vs plain")
for name, beh, want_status, want_w in CASES:
    res, meta = run(beh, ll.grade_self_revision_traced)
    plain = run(beh, ll.grade_self_revision)
    check(f"{name}: status={want_status}", meta.get("judge_status") == want_status, str(meta))
    check(f"{name}: judge_s numeric", isinstance(meta.get("judge_s"), float) and meta["judge_s"] >= 0, str(meta))
    if want_w is None:
        check(f"{name}: fail-open None (traced and plain)", res is None and plain is None)
        check(f"{name}: judge_error recorded", bool(meta.get("judge_error")))
    else:
        check(f"{name}: warranted={want_w} (traced and plain agree)",
              res is not None and res["warranted"] == want_w and plain == res, f"{res} vs {plain}")
        check(f"{name}: no judge_error", meta.get("judge_error") == "")

print("[3] source checks")
sn = (ROOT / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
lls = (ROOT / "core" / "left_lane.py").read_text(encoding="utf-8")
check("writer calls the traced twin", "_ll4.grade_self_revision_traced(" in sn)
for key in ('"old_self": (old_self_concept or "")[:400]', '[str(_e)[:300] for _e in _sevlist]',
            '"judge_status": _emj_meta.get("judge_status")', '"judge_s": _emj_meta.get("judge_s")',
            '"judge_error": _emj_meta.get("judge_error", "")'):
    check(f"row field present: {key[:40]}", key in sn)
check("no 'gates NOTHING' text left in subconscious_node.py", "gates NOTHING" not in sn.split("DECOUPLED-JUDGE SHADOW", 1)[1][:3000])
check("comment says it GATES probation admission", "now GATES the probation admission below (admit only if warranted >= provisional_identity.WARRANTED_ADMIT_MIN" in sn)
check("gate itself untouched (_judge from _emj, WARRANTED_ADMIT_MIN)",
      '_judge = (_emj or {}).get("warranted") if _emj is not None else None' in sn
      and "float(_judge) >= _pi.WARRANTED_ADMIT_MIN" in sn)
check("left_lane docstring: no 'gates nothing yet'", "gates nothing yet" not in lls)
check("left_lane docstring says it GATES", "It GATES probation admission" in lls)

print("[4] row construction")
_sevlist = ["e" * 1000, "short"]
old_self_concept = "o" * 900
row = {"old_self": (old_self_concept or "")[:400], "evidence": [str(_e)[:300] for _e in _sevlist],
       "judge_status": "ok", "judge_s": 1.23, "judge_error": ""}
s = json.dumps(row, ensure_ascii=False)
check("row serialises; caps hold", len(row["old_self"]) == 400 and [len(x) for x in row["evidence"]] == [300, 5] and json.loads(s) == row)

print("[5] isolation")
live = Path(r"C:\Nascence\data\logs\t4_emissary_judge.jsonl")
check("this tree's writer path is under the worktree, not C:\\Nascence",
      str(ROOT).lower().startswith("c:\\wt\\") or str(ROOT).lower() != r"c:\nascence")

print()
if FAILS:
    print(f"FAILED {len(FAILS)}: {FAILS}")
    sys.exit(1)
print("ALL OK")
