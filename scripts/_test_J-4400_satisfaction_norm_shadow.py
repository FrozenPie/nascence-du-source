"""J-4400 (D-0871): shadow windowed satisfaction gap. Temp-store only; real data/ hashed before/after.
  python scripts/_test_J-4400_satisfaction_norm_shadow.py   # exit 0 = ALL OK"""
import hashlib, json, os, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import satisfaction as S, profile

REAL = [S._LOG, S._STATE, S._NORM_SHADOW]
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
before = [h(p) for p in REAL]
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: sys.exit(1)

tmp = Path(tempfile.mkdtemp())
log = tmp / "log.jsonl"; now = 1_000_000.0
rows = [{"ts": now - 60, "event": "light_event", "kind": "liking", "domain": "self", "weight": 0.15}] * 100
rows += [{"ts": now - 60, "event": "shadow_event", "kind": "wanting", "domain": "self", "weight": 0.2}] * 3
rows += [{"ts": now - 7 * 3600, "event": "frontier_born", "kind": "wanting", "domain": "world", "weight": 0.18}]
log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
w = S.windowed_snapshot(now=now, log_path=log)
ok(w["self"]["liking_w"] == 1.0 and w["self"]["n_l"] == 1, "flood of one type capped at 1.0")
ok(abs(w["self"]["wanting_w"] - 0.6) < 1e-6 and abs(w["self"]["gap"] + 0.4) < 1e-6, "gap = wanting - liking")
ok(w["world"]["gap"] is None and w["creative"]["gap"] is None, "out-of-window / empty domain is None, not 0")
ok(S.hours_above("self", -0.5, hours=2, now=now, log_path=log) == 1, "hours_above persistence")

S._NORM_SHADOW = tmp / "shadow.jsonl"; S._norm_last_tick = 0.0
os.environ.pop("NASCENCE_SATISFACTION_NORM_SHADOW", None)
ok(S.norm_shadow_tick(now) is False and not S._NORM_SHADOW.exists(), "default OFF writes nothing")
os.environ["NASCENCE_SATISFACTION_NORM_SHADOW"] = "1"
profile.LIVE = True
S._LOG = log
ok(S.norm_shadow_tick(now) is True, "flag on writes")
got = [json.loads(l) for l in S._NORM_SHADOW.read_text().splitlines()]
ok(len(got) == 4 and {"ts","domain","liking_w","wanting_w","gap","n_l","n_w","old_gap"} <= set(got[0]), "4 domain rows, full schema")
ok(S.norm_shadow_tick(now + 60) is False, "throttled within the hour")
profile.LIVE = False; S._norm_last_tick = 0.0; S._NORM_SHADOW = Path(__file__).resolve().parent.parent / "data" / "satisfaction_norm_shadow.jsonl"
ok(S.norm_shadow_tick(now + 7200) is False and not S._NORM_SHADOW.exists(), "non-live process refused by fence, fail-open")
ok([h(p) for p in REAL] == before, "real data files untouched")
print("ALL OK")
