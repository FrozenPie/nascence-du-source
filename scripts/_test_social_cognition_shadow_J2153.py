"""J-2153 test: core/social_cognition_shadow.py with a STUB judge panel (no hub calls), all logs redirected via
lab_env.isolate(also=...). Import core BEFORE lab_env. Exit 0 = pass."""
import asyncio, json, sys, os, pathlib, hashlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import social_cognition_shadow as S, judge_panel as jp, shadow_log

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

def fp():
    d = ROOT / "data"
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()} if d.exists() else {}

before = fp()
async def fake(system, user, key, context="", **kw):
    v = {"tracks": True, "refs": "EARLIER" in user and "Cat" in user, "attributes": "feel" in user, "supported": False}[key]
    return {"verdict": v, "how": "agreed", "v1": v, "v2": v, "why": "stub"}
orig = jp.rule_detail
jp.rule_detail = fake
try:
    with lab_env.isolate(also=[(S, ["_LOG", "_STATE"])], db="empty") as lab:
        conv = lab / "conv.jsonl"
        rows = [
            {"ts": 1790600000, "cycle_id": "a1", "human": "Your cat is hungry.", "entity": "Travis, I feel the hunger of the Cat."},
            {"ts": 1790600300, "cycle_id": "a2", "human": "Did you feed her?", "entity": "Yes, the Cat was fed; you seem worried."},
            {"ts": 1790700000, "cycle_id": "a3", "human": "\u6e21 \u2014 it's time to stop for a while, and I want you to know why.", "entity": "ok"},
            {"ts": 1790700100, "cycle_id": "a4", "human": "x" * 1200, "entity": "pasted reply"},
            {"ts": 1700000000, "cycle_id": "old", "human": "ancient", "entity": "old"},
        ]
        conv.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        check("kinds", [S.classify_kind(r["human"]) for r in rows[:4]] == ["conversation", "conversation", "farewell", "paste"])
        r = asyncio.run(S.sweep(conv_path=conv, max_items=10, backfill=True))
        check("sweep scored 4 (old excluded by since)", r["scored"] == 4 and r["candidates"] == 4)
        out = shadow_log.read_rows(S._LOG)
        check("4 rows written to the redirected log, not live", len(out) == 4 and str(S._LOG).startswith(str(lab)))
        a1, a2 = out[0], out[1]
        check("a1 has no prior -> refs None, attributes True->supported judged", a1["refs_earlier"] is None and a1["attrib_supported"] is False and a1["n_prior"] == 0)
        check("a2 has prior turn within window", a2["n_prior"] == 1 and a2["refs_earlier"] is False or a2["refs_earlier"] is True)
        check("votes recorded", a2["votes"]["tracks_intent"]["how"] == "agreed")
        r2 = asyncio.run(S.sweep(conv_path=conv, max_items=10))
        check("idempotent: rescore nothing", r2["scored"] == 0 and r2["candidates"] == 0)
        st = S.status()
        check("status per kind + INSUFFICIENT on thin n", st["scored"] == 4 and "INSUFFICIENT" in st["verdict"] and "farewell" in st["by_kind"])
        check("lex overlap counts earlier-only tokens", S.lex_earlier_overlap("the hunger returns", "x", ["hunger and cat"]) == 1)
        # judges down -> skip row, no score row
        async def down(*a, **k): return {"verdict": None, "how": "unavailable"}
        jp.rule_detail = down
        conv2 = lab / "conv2.jsonl"
        conv2.write_text(json.dumps({"ts": 1790800000, "cycle_id": "z1", "human": "hi there", "entity": "hello"}), encoding="utf-8")
        r3 = asyncio.run(S.sweep(conv_path=conv2))
        tail = shadow_log.read_rows(S._LOG)[-1]
        check("judges down: unavailable counted and skip logged", r3["unavailable"] == 1 and tail.get("skip") == "judges-unavailable")
finally:
    jp.rule_detail = orig
after = fp()
leak = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
check(f"no data/ top-level leak {sorted(leak)}", not leak)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
