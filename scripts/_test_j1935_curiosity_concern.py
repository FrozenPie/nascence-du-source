"""J-1935 / F-2560: idle_allocator curiosity backlog read (CURIOSITY_USE_BACKLOG, default False) and concern two-level
percentile bypass (CONCERN_BYPASS_PERCENTILE). Shadow-only. Compares against the pre-change module (git show <old-rev>).
All state/log paths temp, network blocked, core imported BEFORE anything else; run from a throwaway worktree.
Usage: python scripts/_test_j1935_curiosity_concern.py [--old-rev c5da3bd] [--shadow-log P] [--state P] [--ticks 4000]"""
import sys, os, json, random, tempfile, subprocess, importlib.util, argparse, shutil, glob
from collections import Counter
from pathlib import Path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core                                                         # core BEFORE anything else (live-store safety)
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), core.__file__
assert os.path.normcase(ROOT) != os.path.normcase(r"C:\Nascence"), "run from a throwaway worktree"
import socket
def _no_net(*a, **k): raise OSError("J-1935 test: network blocked")
socket.socket.connect = _no_net; socket.socket.connect_ex = _no_net
from core import idle_allocator as new
from core import curiosity_progress as cp
from core import concerns
assert os.path.abspath(new.__file__).lower().startswith(ROOT.lower())

ap = argparse.ArgumentParser()
ap.add_argument("--old-rev", default="c5da3bd")
ap.add_argument("--shadow-log", default=r"C:\Nascence\data\logs\idle_shadow.jsonl")
ap.add_argument("--state", default=r"C:\Nascence\data\idle_allocator_state.json")
ap.add_argument("--ticks", type=int, default=4000)
args = ap.parse_args()
TMP = tempfile.mkdtemp(prefix="j1935_")
src = subprocess.run(["git", "-C", ROOT, "show", f"{args.old_rev}:core/idle_allocator.py"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
assert "CURIOSITY_USE_BACKLOG" not in src and "BALANCE_USE_SHARES" in src
op = os.path.join(TMP, "idle_allocator_old_j1935.py"); open(op, "w", encoding="utf-8").write(src)
spec = importlib.util.spec_from_file_location("idle_allocator_old_j1935", op)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)

FAILS = []
def check(name, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + name + ((" -- " + str(extra)) if extra else ""), flush=True)
    if not ok: FAILS.append(name)
def point(mod, tag):
    d = os.path.join(TMP, tag); os.makedirs(os.path.join(d, "logs"), exist_ok=True)
    mod._DATA = Path(d); mod._STATE = mod._DATA / "idle_allocator_state.json"; mod._LOG = mod._DATA / "logs" / "idle_shadow.jsonl"
    assert os.path.abspath(str(mod._STATE)).lower().startswith(TMP.lower()); return d

class FakeRank:
    def __init__(self, rows): self.rows = rows
    def __enter__(self): self.s = cp.rank; cp.rank = lambda: [dict(r) for r in self.rows]; return self
    def __exit__(self, *a): cp.rank = self.s
class FakeConcern:
    def __init__(self, c): self.c = c
    def __enter__(self): self.s = concerns.primary_concern; concerns.primary_concern = lambda: dict(self.c); return self
    def __exit__(self, *a): concerns.primary_concern = self.s
def qrow(lp, finding, parked=False, q="question about x"):
    return {"q": q, "lp": lp, "parked": parked, "stalls": 3 if parked else 0, "finding": finding, "source": "t"}
ROWS = [qrow(2.0, True, q="alpha beta gamma delta"), qrow(2.0, True), qrow(0.0, False), qrow(0.0, False), qrow(-3.0, False, parked=True), qrow(2.0, True, parked=True)]

print("== [A] curiosity channel")
check("A0 defaults: backlog switch False (variance too low), concern bypass True", new.CURIOSITY_USE_BACKLOG is False and new.CONCERN_BYPASS_PERCENTILE is True)
with FakeRank(ROWS):
    base_new, base_old = new._ch_curiosity(), old._ch_curiosity()
check("A1 switch False == old module exactly", base_new == base_old and base_new[0] == 1.0, base_new[0])
new.CURIOSITY_USE_BACKLOG = True
try:
    with FakeRank(ROWS):
        r = new._ch_curiosity()
    check("A2 switch True: raw = closeable/active = 2/4 (parked excluded)", abs(r[0] - 0.5) < 1e-12 and r[4]["n_closeable"] == 2 and r[4]["n_active"] == 4, r[0])
    check("A3 binding key = top-ranked question slug (unchanged); fraction+counts in lineage; still semantic",
          r[1] == base_old[1] == "alpha_beta_gamma_delta" and r[2] == "semantic" and r[4]["backlog_fraction"] == 0.5 and r[4]["lp"] == 2.0, r[1:4])
    with FakeRank([qrow(0.0, False)] * 3):
        z = new._ch_curiosity()
    check("A4 no closeable question -> raw 0.0", z[0] == 0.0)
    with FakeRank([qrow(2.0, True)] * 3):
        o = new._ch_curiosity()
    check("A5 all closeable -> raw 1.0", o[0] == 1.0)
    with FakeRank([qrow(0.0, False, parked=True)]):
        check("A6 only parked questions -> None (unchanged)", new._ch_curiosity() is None)
    with FakeRank([]):
        check("A7 no questions -> None", new._ch_curiosity() is None)
    with FakeRank([qrow(1.0, False)] + [qrow(0.0, False)] * 3):
        l1 = new._ch_curiosity()
    check("A8 raw always in [0,1]", all(0.0 <= x[0] <= 1.0 for x in (r, z, o, l1)))
finally:
    new.CURIOSITY_USE_BACKLOG = False
check("A9 curiosity stays in GRADED_CHANNELS", "curiosity" in new.GRADED_CHANNELS)

print("== [B] concern channel + bypass")
check("B1 concern left GRADED, is in TWO_LEVEL_BY_DESIGN, disjoint from the others",
      "concern" not in new.GRADED_CHANNELS and new.TWO_LEVEL_BY_DESIGN == ("concern",) and not (set(new.TWO_LEVEL_BY_DESIGN) & (set(new.GRADED_CHANNELS) | set(new.CONSTANT_BY_DESIGN)))
      and set(new.GRADED_CHANNELS) == set(old.GRADED_CHANNELS) - {"concern"} and new.CONSTANT_BY_DESIGN == old.CONSTANT_BY_DESIGN)
for kind in ("pursuit", "project"):
    with FakeConcern({"kind": kind, "text": "some concern text here", "source": "s"}):
        check(f"B2 _ch_concern raw unchanged ({kind})", new._ch_concern() == old._ch_concern())

def one_tick(mod, hist_concern, concern_raw, bypass=None):
    point(mod, "B_" + str(random.random()))
    open(mod._STATE, "w", encoding="utf-8").write(json.dumps({"history": {"concern": hist_concern}, "streak": {}}))
    saved = dict(mod._CHANNELS)
    mod._CHANNELS = {"concern": lambda ctx: (concern_raw, "k", "semantic", "j", {})}
    if bypass is not None: mod.CONCERN_BYPASS_PERCENTILE = bypass
    try:
        random.seed(1); rec = mod.shadow_tick({})
    finally:
        mod._CHANNELS = saved
        if bypass is not None: mod.CONCERN_BYPASS_PERCENTILE = True
    return rec["candidates"][0]
H = [0.55] * 500
c55, c45 = one_tick(new, H, 0.55), one_tick(new, H, 0.45)
check("B3 bypass: 0.55 -> p_norm 1.0, 0.45 -> 0.8182 even against 500/500 pursuit history (old: 0.0)",
      c55["p_norm"] == 1.0 and abs(c45["p_norm"] - 0.45 / 0.55) < 1e-3 and one_tick(old, H, 0.45)["p_norm"] == 0.0, (c55["p_norm"], c45["p_norm"]))
check("B4 bypass: preference ratio s_final(0.55)/s_final(0.45) == declared 1.222", abs(c55["s_final"] / c45["s_final"] - 0.55 / 0.45) < 0.01, (c55["s_final"], c45["s_final"]))
cold = one_tick(new, [0.55] * 5, 0.45)
check("B5 bypass also applies cold (declared level, not the flat 0.5 prior)", abs(cold["p_norm"] - 0.8182) < 1e-3 and cold["cold_start"] is True)
off55, off45 = one_tick(new, H, 0.55, bypass=False), one_tick(new, H, 0.45, bypass=False)
o55, o45 = one_tick(old, H, 0.55), one_tick(old, H, 0.45)
check("B6 CONCERN_BYPASS_PERCENTILE=False == old module record exactly", off55 == o55 and off45 == o45, (off55["p_norm"], off45["p_norm"]))
mixed = [0.55] * 300 + [0.45] * 200
check("B7 bypass independent of history content", one_tick(new, mixed, 0.45)["p_norm"] == c45["p_norm"])

print("== [C] history versioning")
def only_cur(tag, state_obj, switch):
    point(new, tag)
    if state_obj is not None: open(new._STATE, "w", encoding="utf-8").write(state_obj if isinstance(state_obj, str) else json.dumps(state_obj))
    saved = dict(new._CHANNELS); new._CHANNELS = {"curiosity": saved["curiosity"], "self": saved["self"]}
    new.CURIOSITY_USE_BACKLOG = switch
    try:
        with FakeRank(ROWS): random.seed(1); rec = new.shadow_tick({})
    finally:
        new._CHANNELS = saved; new.CURIOSITY_USE_BACKLOG = False
    return rec, json.loads(open(new._STATE, encoding="utf-8").read())
def mk(**e):
    s = {"history": {"curiosity": [1.0] * 500, "concern": [0.55] * 500, "self": [0.55] * 500}, "streak": {"curiosity": 2}}; s.update(e); return s
rec, st = only_cur("C1", mk(), True)
cc = [c for c in rec["candidates"] if c["channel"] == "curiosity"][0]
check("C1 switch True: curiosity history dropped to 1 row, stamped 2, cold 0.5; other channels untouched",
      st["curiosity_schema"] == 2 and len(st["history"]["curiosity"]) == 1 and cc["cold_start"] and cc["p_norm"] == 0.5
      and st["history"]["concern"] == [0.55] * 500, st.get("curiosity_schema"))
_, st = only_cur("C2", mk(curiosity_schema=2), True)
check("C2 already schema 2: no drop", len(st["history"]["curiosity"]) == 500)
_, st = only_cur("C3", mk(), False)
check("C3 switch False: no drop, no stamp", len(st["history"]["curiosity"]) == 500 and "curiosity_schema" not in st)
_, st = only_cur("C4", "{ not json", True)
check("C4 corrupt state fails open and stamps", st["curiosity_schema"] == 2)
check("C5 no .tmp left", not os.path.exists(str(new._STATE.with_suffix(".tmp"))))

print("== [D] full replay over logged shadow rows")
def tail(path, n):
    sz = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, sz - n * 6000)); data = f.read()
    rows = []
    for ln in data.split(b"\n")[1:]:
        try: rows.append(json.loads(ln.decode("utf-8")))
        except Exception: pass
    return rows[-n:]
rows = tail(args.shadow_log, args.ticks)
state_text = open(args.state, "r", encoding="utf-8").read()
rs = json.loads(state_text)
check("D0 inputs: rows + real state (curiosity all 1.0; concern history present)", len(rows) >= 1000 and set(rs["history"]["curiosity"]) == {1.0},
      (len(rows), {k: sorted(set(v))[:3] for k, v in rs["history"].items() if k in ("curiosity", "concern")}))
fr = []
for f in sorted(glob.glob(r"C:\Nascence\data\backups\*\frontier.json")):
    qs = (json.load(open(f, encoding="utf-8")) or {}).get("questions", [])
    op_ = [q for q in qs if q.get("status") == "open" and int(q.get("consecutive_stalls", 0) or 0) < 3]
    if op_: fr.append((len(op_), sum(1 for q in op_ if q.get("finding"))))
fracs = [b / a for a, b in fr]
print("   frontier backup fractions (SYNTHETIC replay series, interpolated across the replay window):", [round(x, 3) for x in fracs])
def synth_rows(i):
    t = i / max(1, len(rows) - 1) * (len(fr) - 1); a = int(t); b = min(a + 1, len(fr) - 1); w = t - a
    frac = fracs[a] * (1 - w) + fracs[b] * w
    n = 365; k = max(1, round(frac * n))
    return [qrow(2.0, True, q="top question")] + [qrow(2.0, True)] * (k - 1) + [qrow(0.0, False)] * (n - k)

def replay(mod, tag, backlog=False, bypass=True):
    point(mod, tag); open(mod._STATE, "w", encoding="utf-8").write(state_text)
    saved = dict(mod._CHANNELS); out = []
    if hasattr(mod, "CURIOSITY_USE_BACKLOG"): mod.CURIOSITY_USE_BACKLOG = backlog
    if hasattr(mod, "CONCERN_BYPASS_PERCENTILE"): mod.CONCERN_BYPASS_PERCENTILE = bypass
    try:
        for i, row in enumerate(rows):
            by = {c["channel"]: c for c in row["candidates"]}
            ch = {}
            for name in saved:
                if name in by:
                    c = by[name]
                    ch[name] = (lambda _c: (lambda ctx: (_c["raw"], _c["binding_key"], _c["key_kind"], _c["justification"], {})))(c)
                else: ch[name] = lambda ctx: None
            real_cur = backlog and "curiosity" in by
            if real_cur: ch["curiosity"] = saved["curiosity"]          # the REAL new channel code over a synthetic frontier
            mod._CHANNELS = ch
            if real_cur:
                with FakeRank(synth_rows(i)): random.seed(i); out.append(mod.shadow_tick({}))
            else:
                random.seed(i); out.append(mod.shadow_tick({}))
    finally:
        mod._CHANNELS = saved
        if hasattr(mod, "CURIOSITY_USE_BACKLOG"): mod.CURIOSITY_USE_BACKLOG = False
        if hasattr(mod, "CONCERN_BYPASS_PERCENTILE"): mod.CONCERN_BYPASS_PERCENTILE = True
    return out
R_old = replay(old, "D_old")
R_off = replay(new, "D_off", backlog=False, bypass=False)
R_new = replay(new, "D_new", backlog=False, bypass=True)
R_bk = replay(new, "D_bk", backlog=True, bypass=True)
check("D1 all ticks recorded", all(R_old) and all(R_off) and all(R_new) and all(R_bk) and len(R_old) == len(rows))
def strip(rs_): return [{k: v for k, v in r.items() if k != "ts"} for r in rs_]
check("D2 both switches off == OLD module record-for-record (incl. winner-streak feedback)", strip(R_old) == strip(R_off))
def wins(rs_):
    c = Counter(r["would_pick_argmax"] for r in rs_); n = sum(c.values()); return {k: round(v / n, 4) for k, v in c.most_common()}
print("   win-share OLD                      :", wins(R_old))
print("   win-share NEW concern bypass only  :", wins(R_new))
print("   win-share NEW bypass + curiosity bk:", wins(R_bk))
def col(rs_, ch, f): return [c[f] for r in rs_ for c in r["candidates"] if c["channel"] == ch]
def stat(x):
    m = sum(x) / len(x); return {"n": len(x), "min": round(min(x), 4), "max": round(max(x), 4), "mean": round(m, 4), "var": round(sum((v - m) ** 2 for v in x) / len(x), 5), "distinct": len(set(x))}
for lab, rs_ in (("OLD", R_old), ("NEW bypass", R_new), ("NEW bypass+bk", R_bk)):
    print(f"   concern   {lab:14s} raw {stat(col(rs_,'concern','raw'))}\n   concern   {lab:14s} p_norm {stat(col(rs_,'concern','p_norm'))}")
    print(f"   curiosity {lab:14s} raw {stat(col(rs_,'curiosity','raw'))}\n   curiosity {lab:14s} p_norm {stat(col(rs_,'curiosity','p_norm'))}")
check("D3 concern p_norm under bypass is exactly {1.0, 0.8182}", set(col(R_new, "concern", "p_norm")) <= {1.0, round(0.45 / 0.55, 4)}, sorted(set(col(R_new, "concern", "p_norm"))))
check("D4 curiosity raw/p_norm UNCHANGED by the concern bypass alone", col(R_old, "curiosity", "raw") == col(R_new, "curiosity", "raw") and col(R_old, "curiosity", "p_norm") == col(R_new, "curiosity", "p_norm"))
cur_cands = [c for r in R_bk for c in r["candidates"] if c["channel"] == "curiosity"]
warm = [c["p_norm"] for c in cur_cands if not c["cold_start"]]
check("D5 curiosity backlog replay: raw varies (>5 distinct) and p_norm leaves 1.0 once warm", len(set(col(R_bk, "curiosity", "raw"))) > 5 and bool(warm) and min(warm) < 1.0, (len(set(col(R_bk, "curiosity", "raw"))), min(warm) if warm else None))
others = ("contradiction", "balance_world", "balance_light", "boredom", "self", "wander", "flavour")
bad = [(ch, f) for ch in others for f in ("raw", "p_norm") if col(R_new, ch, f) != col(R_old, ch, f) or col(R_bk, ch, f) != col(R_old, ch, f)]
check("E1 no other channel's raw or p_norm changes (OLD vs NEW vs NEW+backlog)", not bad, bad)
check("E2 concern raw identical in all", col(R_old, "concern", "raw") == col(R_new, "concern", "raw") == col(R_bk, "concern", "raw"))
check("E3 only temp paths written (live state/log only READ)", all(os.path.abspath(str(p)).lower().startswith(TMP.lower()) for p in (old._STATE, old._LOG, new._STATE, new._LOG)))
shutil.rmtree(TMP, ignore_errors=True)
print("\nRESULT:", "ALL PASS" if not FAILS else f"{len(FAILS)} FAIL: {FAILS}")
sys.exit(1 if FAILS else 0)
