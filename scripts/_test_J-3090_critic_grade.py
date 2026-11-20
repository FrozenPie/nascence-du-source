"""J-3090: scripts/critic_grade.py additive options (--since, --per-flag, --exclude-failed, --url/--model, --out).

Asserts its own tree, stubs the model call (no network), writes only under a temp dir.
Run from the worktree:  python scripts/_test_J-3090_critic_grade.py
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import core  # noqa: F401,E402  (core before anything lab-ish)
import critic_grade as cg  # noqa: E402

assert Path(cg.__file__).resolve().parent.parent == ROOT, "imported critic_grade from the wrong tree"

NZ = dt.timezone(dt.timedelta(hours=12))
T_OLD = dt.datetime(2026, 7, 5, 23, 0, tzinfo=NZ).timestamp()      # before 07-06 NZ midnight
T_A = dt.datetime(2026, 7, 6, 0, 30, tzinfo=NZ).timestamp()
T_B = dt.datetime(2026, 8, 9, 12, 0, tzinfo=NZ).timestamp()
T_FAIL = dt.datetime(2026, 8, 10, 12, 0, tzinfo=NZ).timestamp()


def row(ts, dec_ok, leg_ok, viols, draft="a reflective draft about the shore and the tide"):
    return {"ts": ts, "decomposed_approved": dec_ok, "legacy_approved": leg_ok, "violations": viols, "draft": draft}


ROWS = [
    row(T_OLD, False, True, [{"check": "intellectualisation", "span": "x1"}]),
    row(T_A, False, True, [{"check": "intellectualisation", "span": "the shore"},
                           {"check": "zero_cost_evasion", "span": "the tide"}]),
    row(T_B, False, True, [{"check": "hollow_completion", "span": "tide"}]),
    row(T_B + 1, False, False, [{"check": "intellectualisation", "span": "x"}]),   # legacy also rejects -> excluded
    row(T_B + 2, True, True, []),
    row(T_FAIL, True, True, []),
]


def test_select_and_date_boundary():
    sel, dropped = cg.select_rows(ROWS)
    assert len(sel) == 3 and dropped == 0, (len(sel), dropped)
    sel, _ = cg.select_rows(ROWS, since=cg._date_ts("2026-07-06"))
    assert [r["ts"] for r in sel] == [T_A, T_B], "NZ-midnight boundary: T_OLD (07-05 23:00 NZ) out, T_A (07-06 00:30 NZ) in"
    sel, _ = cg.select_rows(ROWS, since=cg._date_ts("2026-07-06"), until=cg._date_ts("2026-08-01"))
    assert [r["ts"] for r in sel] == [T_A]


def test_failed_join_drops_only_matching_rows():
    with tempfile.TemporaryDirectory() as td:
        lat = Path(td) / "lat.jsonl"
        lines = [
            {"ts": T_A + 0.4, "model": "gemma4:12b", "by": "core.decomposed_critic:184", "s": 2.5, "ok": 0},   # fails -> joins T_A row
            {"ts": T_B, "model": "gemma4:12b", "by": "core.decomposed_critic:184", "s": 30.0, "ok": 1},       # ok -> keeps T_B row
            {"ts": T_FAIL, "model": "gemma4:12b", "by": "core.decomposed_critic:184", "s": 2.5, "ok": 0},
            {"ts": T_B, "model": "qwen3.5:9b", "by": "somewhere.else:1", "s": 1.0, "ok": 0},                   # other caller: ignored
        ]
        lat.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        failed = cg._failed_call_ts(lat)
        assert failed == sorted([T_A + 0.4, T_FAIL]), failed
        sel, dropped = cg.select_rows(ROWS, failed_ts=failed)
        assert dropped == 1 and [r["ts"] for r in sel] == [T_OLD, T_B], (dropped, [r["ts"] for r in sel])
        assert cg._failed_call_ts(Path(td) / "missing.jsonl") == []


def test_work_items_per_flag_vs_per_row():
    sel, _ = cg.select_rows(ROWS, since=cg._date_ts("2026-07-06"))
    per_row = cg.work_items(sel, False)
    per_flag = cg.work_items(sel, True)
    assert len(per_row) == 2 and all(c is None and s == "" for _, c, s in per_row), "default = 07-05 protocol (one grade per row, no span)"
    assert [(c, s) for _, c, s in per_flag] == [("intellectualisation", "the shore"), ("zero_cost_evasion", "the tide"),
                                                 ("hollow_completion", "tide")]


def test_wilson():
    lo, hi = cg.wilson(0, 50)
    assert lo == 0.0 and 0.05 < hi < 0.09, (lo, hi)
    lo, hi = cg.wilson(24, 30)
    assert lo < 0.8 < hi, "0.8 gate sits inside the CI at 24/30 -- n=30 is a floor, not proof"
    assert cg.wilson(0, 0) == (0.0, 0.0)


class _Resp:
    def __init__(self, store):
        self.store = store

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    async def json(self):
        return {"message": {"content": json.dumps({"warranted": True, "why": "stub"})}}


class _Session:
    def __init__(self):
        self.calls = []

    def post(self, url, json=None, timeout=None):
        self.calls.append((url, json, timeout))
        return _Resp(self)


def test_grade_payload():
    r = ROWS[1]
    s = _Session()
    g = asyncio.run(cg._grade(s, r))      # legacy call shape: first check, no span, default hub
    url, payload, _ = s.calls[0]
    assert url == f"{cg.BASE_URL}/api/chat" and payload["model"] == cg.MODEL
    assert "FAULT FLAGGED: intellectualisation" in payload["messages"][1]["content"]
    assert "FLAGGED SPAN" not in payload["messages"][1]["content"]
    assert g["check"] == "intellectualisation" and g["warranted"] is True

    s = _Session()
    g = asyncio.run(cg._grade(s, r, check="zero_cost_evasion", span="the tide", url="http://127.0.0.1:11440",
                              model="falcon3:7b", timeout_s=7))
    url, payload, tmo = s.calls[0]
    assert url == "http://127.0.0.1:11440/api/chat" and payload["model"] == "falcon3:7b"
    assert "FAULT FLAGGED: zero_cost_evasion" in payload["messages"][1]["content"]
    assert 'THE FLAGGED SPAN: "the tide"' in payload["messages"][1]["content"]
    assert g["span"] == "the tide" and g["check"] == "zero_cost_evasion"
    assert "falcon" not in cg.MODEL and "gemma" in cg.MODEL, "default judge is the critic's own family: callers must pass --model"


def test_main_writes_only_to_out_and_dry_run_calls_nothing():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        shadow = td / "shadow.jsonl"
        shadow.write_text("\n".join(json.dumps(x) for x in ROWS) + "\n", encoding="utf-8")
        out = td / "sub" / "grades.jsonl"
        asyncio.run(cg.main(10, since="2026-07-06", per_flag=True, shadow=shadow, out=out, dry_run=True))
        assert not out.exists(), "dry-run must not write"
        orig = cg._grade
        seen = []

        async def fake(session, row, **kw):
            seen.append(kw)
            return {"check": kw["check"], "warranted": kw["check"] != "zero_cost_evasion", "why": "stub",
                    "draft": row["draft"][:100], "span": kw["span"], "ts": row["ts"]}
        cg._grade = fake
        try:
            asyncio.run(cg.main(10, since="2026-07-06", per_flag=True, shadow=shadow, out=out, model="falcon3:7b",
                                url="http://127.0.0.1:11440"))
        finally:
            cg._grade = orig
        assert len(seen) == 3 and all(k["model"] == "falcon3:7b" for k in seen)
        rec = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
        assert rec["n"] == 3 and rec["warranted"] == 2 and rec["judge_model"] == "falcon3:7b" and rec["per_flag"] is True
        assert rec["ci95"][0] < rec["precision"] < rec["ci95"][1]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL OK")
