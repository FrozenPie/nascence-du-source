"""J-2669 test: the mineness re-audit scripts run on a SYNTHETIC log in a temp dir and recover a planted
composition effect. Touches no live data. Run from the worktree: python scripts/_test_J-2669_mineness_audit.py"""
import sys, json, random, subprocess, tempfile, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
try:
    import lab_env  # noqa: F401
except Exception:
    pass

def synth(path):
    random.seed(1)
    t0 = datetime.datetime(2026, 7, 4, tzinfo=datetime.timezone.utc).timestamp()
    rows = []
    # July: spontaneous err ~0.40, world err ~0.46 (gap +0.06). Sept: spontaneous 0.34, world 0.37, percept 0.34
    def add(ts, kind, auth, mu):
        e = max(0.05, min(0.95, random.gauss(mu, 0.08)))
        rows.append({"ts": ts, "seed_kind": kind, "ownership": "in_stream", "authorship": auth, "error": round(e, 4),
                     "recent_sim": round(1 - e, 4), "basin_sim": round(0.5 * (1 - e), 4), "felt_mine": e < 0.45,
                     "thought": "synthetic thought number %d about the sea" % len(rows)})
    for i in range(1200):
        ts = t0 + i * 60
        k = "world" if i % 5 == 0 else "spontaneous"
        add(ts, k, "OTHER" if k == "world" else "SELF", 0.46 if k == "world" else 0.40)
    t1 = datetime.datetime(2026, 9, 10, tzinfo=datetime.timezone.utc).timestamp()
    for i in range(3000):
        ts = t1 + i * 60
        r = i % 10
        if r < 3: add(ts, "spontaneous", "SELF", 0.34)
        elif r < 8: add(ts, "percept", "OTHER", 0.34)
        elif r < 9: add(ts, "world", "OTHER", 0.375)
        else: add(ts, "frontier", "OTHER", 0.36)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r) + "\n")

with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "mineness_shadow.jsonl"; synth(p)
    outs = {}
    for name in ("_analyze_J2669_mineness.py", "_analyze_J2669_b.py", "_analyze_J2669_c.py"):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / name), str(p)], capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, (name, r.stderr[-800:])
        outs[name] = r.stdout
    a = outs["_analyze_J2669_mineness.py"]
    # July headline separation ~ +0.06, September headline is diluted by percept (planted ~ +0.01 or less)
    jul = [l for l in a.splitlines() if l.startswith("2026-07") and "OTHERshare" in l][0]
    sep_jul = float(jul.split("sep=")[1]); assert 0.04 < sep_jul < 0.08, jul
    sep_line = [l for l in a.splitlines() if l.startswith("2026-09") and "OTHERshare" in l][0]
    sep_sep = float(sep_line.split("sep=")[1]); assert sep_sep < 0.03, sep_line
    b = outs["_analyze_J2669_b.py"]
    assert "world-only" in b and "kind-equal" in b
    row = [l for l in b.splitlines() if l.startswith("2026-09 actual")][0]
    world_only = float(row.split("world-only")[1].split()[0]); assert world_only > sep_sep + 0.01, row
    c = outs["_analyze_J2669_c.py"]
    assert "AUC" in c and "time-shift" in c
print("J-2669 mineness audit test: OK (planted composition effect recovered: Jul %.4f, Sep headline %.4f, Sep world-only %.4f)"
      % (sep_jul, sep_sep, world_only))
