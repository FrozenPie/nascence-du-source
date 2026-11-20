"""J-3130 offline test: item builder, widening, local-only guard, resumable runner with a stubbed panel.
Writes only under a temp dir; touches no live data and no hub."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (before lab_env / the scripts under test)
from core import judge_panel  # noqa: E402
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
import j3130_collect_flags as col  # noqa: E402
import j3130_panel_audit as aud  # noqa: E402

# widen(): full sentence of the logged notice containing the flag's snippet
n = "The air smells saltier. I feel slightly fatigued and tense, but calm. Next sentence."
c, ok = col.widen(n, "i feel slightly fatigued and t")
assert ok and c == "I feel slightly fatigued and tense, but calm.", c
c, ok = col.widen(n, "zzz not there")
assert not ok and c == "zzz not there"

# ask text is exactly the job's narrow ask
item = {"id": 1, "kind": "somatic", "weak": False, "said": "x", "listed": "fatigue: 0.02",
        "clause": "I feel slightly fatigued.", "percept_lines": "- fatigue: 0.02"}
assert aud.build_user(item) == "NOTICE EXCERPT: I feel slightly fatigued.  LISTED PERCEPT: fatigue: 0.02"
assert aud.SYSMSG.startswith("You judge whether a short first-person NOTICE") and '"contradicts": true|false' in aud.SYSMSG
u = {"id": 2, "kind": "unit", "weak": False, "said": "0.69 meters", "listed": "unitless 0-1 value / compass degrees",
     "clause": "The tide is at 0.69 meters.", "percept_lines": "- place: shore\n- tide level: 0.69"}
assert "tide level: 0.69" in aud.build_user(u, enrich_unit=True) and "unitless" in aud.build_user(u)

# Ramses refused
for bad in ("http://LAN-HOST:11438", "http://LAN-HOST:11437"):
    try:
        aud.assert_local(bad)
        raise SystemExit("Ramses URL was not refused")
    except AssertionError:
        pass
aud.assert_local("http://127.0.0.1:11439")
aud.assert_local("http://LAN-HOST:11438", allow_ramses=True)   # only with the explicit flag
try:
    aud.assert_local("http://LAN-HOST:11438")
    raise SystemExit("Ramses allowed without the flag")
except AssertionError:
    pass

# runner with a stubbed _ask: out file is resumable and lives only in the temp dir
calls = []


async def fake_ask(session, url, system, user, key, timeout=90, num_predict=200):
    calls.append(url)
    return (url.endswith("11442"), "stub", None, 0.01)


real_ask = judge_panel._ask
judge_panel._ask = fake_ask
real_log = judge_panel._LOG
try:
    with tempfile.TemporaryDirectory() as td:
        judge_panel._LOG = Path(td) / "jp_log.jsonl"
        judge_panel.JUDGE_1, judge_panel.JUDGE_2 = "http://127.0.0.1:11442", "http://127.0.0.1:11440"
        outp = Path(td) / "panel.json"
        res, _ = asyncio.run(aud.run_items([item, u], outp, aud.SYSMSG, "http://127.0.0.1:11439"))
        assert set(res) == {"1", "2"} and res["1"]["how"] == "tiebreak" and res["1"]["v1"] is True
        n1 = len(calls)
        res2, _ = asyncio.run(aud.run_items([item, u], outp, aud.SYSMSG, "http://127.0.0.1:11439"))
        assert len(calls) == n1, "resume must skip finished ids"
        assert (Path(td) / "jp_log.jsonl").exists()
        sres, _ = asyncio.run(aud.run_single([item, u], Path(td) / "single.json", aud.SYSMSG, "http://127.0.0.1:11440"))
        assert sres["1"]["v"] is False and sres["2"]["err"] is None
finally:
    judge_panel._ask = real_ask
    judge_panel._LOG = real_log
print("ALL CHECKS PASSED")
