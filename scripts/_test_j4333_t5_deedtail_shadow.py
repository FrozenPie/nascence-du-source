"""J-4333: T5 Phase 1 deed-bound grade shadow. Temp-path stores only; no live data touched."""
import json, os, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["NASCENCE_T5_DEEDTAIL_SHADOW"] = "1"
import core.procedures as P

tmp = Path(tempfile.mkdtemp())
P._F = tmp / "procedures.json"; P._LOG = tmp / "plog.jsonl"
P._T5_DEEDTAIL_LOG = tmp / "shadow.jsonl"; P._HANDS_TRACE = tmp / "hands.jsonl"
ok = fail = 0
def chk(n, c):
    global ok, fail
    print(("  [PASS] " if c else "  [FAIL] ") + n); ok += c; fail += (not c)

t0 = 1_800_000_000.0; D = 86400
cl = [{"ts": t0, "q": "goodnight"}, {"ts": t0 + D + 5, "q": "off to bed"}, {"ts": t0 + 2 * D + 9, "q": "night"}]
rows = [{"ts": t0 + 60, "hands": [{"hand": "fire", "answer": "the fire banks down", "ts": t0 + 60}]},
        {"ts": t0 + D + 100, "hands": [{"hand": "fire", "answer": "the log slips and will not hold", "ts": t0 + D + 100}]},
        {"ts": t0 + 2 * D + 20, "hands": [{"hand": "look", "answer": "x", "ts": t0 + 2 * D + 20}]}]
P._HANDS_TRACE.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

g = P.deed_bound_grade(cl, P._t5_load_deeds(P._HANDS_TRACE, t0, t0 + 3 * D))
chk("2 deed members, look excluded", g["deed_members"] == 2)
chk("one ok one refused", g["deed_ok"] == 1 and g["deed_refused"] == 1)
chk("qualifies (3 members, 48h, 3 convs, 2 deeds)", g["qualifies"] is True)
g2 = P.deed_bound_grade(cl, [])
chk("no deeds -> not qualifying", g2["qualifies"] is False and g2["deed_members"] == 0)

before = None
p = P.compiled("goodnight kind", "bank the fire", cl)
chk("compiled still returns the ledger row", bool(p) and p["rung"] in P.RUNGS)
lines = P._T5_DEEDTAIL_LOG.read_text(encoding="utf-8").splitlines()
chk("one shadow row written", len(lines) == 1)
r = json.loads(lines[0])
chk("row carries key, rung_live, grade", r["key"].startswith("talk:") and r["rung_live"] == p["rung"] and r["qualifies"])
chk("ledger evidence unchanged by shadow (3 members, all ok)", len(p["evidence"]) == 3 and p["successes"] == 3)

P.T5_DEEDTAIL_SHADOW = False
P.compiled("goodnight kind", "bank the fire", cl)
chk("flag off -> no new row", len(P._T5_DEEDTAIL_LOG.read_text(encoding="utf-8").splitlines()) == 1)
P.T5_DEEDTAIL_SHADOW = True
P._HANDS_TRACE = tmp / "missing.jsonl"
P._t5_deedtail_shadow("k", "t", cl, "occurred")
chk("missing trace is fail-open", True)
print(f"=== {ok}/{ok+fail} passed ===")
sys.exit(1 if fail else 0)
