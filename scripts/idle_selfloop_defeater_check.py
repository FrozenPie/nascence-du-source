"""idle_selfloop_defeater_check.py -- D-0011 defeater read for docs/staged/idle_executive_plan.md (J-0855, F-1239, 2026-09-11).
Does the idle self-loop survive the six 06-22 fixes? Measures it five ways, per period, with FULL reads (no tail sampling):
  A. idle_shadow.jsonl allocator would-pick shares (the plan G2 self-share)      B. balance shares embedded in shadow rows
  C. independent reality_share from nascence.db (balance.py origin sets)         D. monoculture_log echo/diversity
  E. monologue_log about-field self-referential share (keyword proxy)             F. inner_thought exact-dup + greedy top-10 cluster concentration
  G. ignition_log trigger/dominant mix
Read-only on data/ (sqlite opened mode=ro). Edit PERIODS to move the boundaries. Run: python scripts/idle_selfloop_defeater_check.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import json, sqlite3, math, time, re
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

SHADOW = r"C:\Nascence\data\logs\idle_shadow.jsonl"
MONO   = r"C:\Nascence\data\monoculture_log.jsonl"
MLOG   = r"C:\Nascence\data\monologue_log.jsonl"
IGN    = r"C:\Nascence\data\ignition_log.jsonl"
DB     = r"C:\Nascence\data\memory\nascence.db"

def ts_of(s):  # local time -> epoch
    return datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp()

# period boundaries (local). Six fixes shipped in the 06-22 session; last 06-22 shutdown 21:27 -> post-fix from 21:30.
B_FIX   = ts_of("2026-06-22 21:30")
B_0705  = ts_of("2026-07-05 00:00")   # last plan evidence review
B_0823  = ts_of("2026-08-23 00:00")   # last verified read (25,475 rows)
PERIODS = [("pre-fix 06-16..06-22", -1e12, B_FIX),
           ("post-fix 06-22..07-05", B_FIX, B_0705),
           ("07-05..08-23", B_0705, B_0823),
           ("post-08-23 (UNREAD)", B_0823, 1e12)]
def period(ts):
    for name, lo, hi in PERIODS:
        if lo <= ts < hi:
            return name
    return "?"
def d(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def load_jsonl(p):
    out = []
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out

print("=" * 100)
print("A. idle_shadow.jsonl — the allocator's would-pick (plan's own G2 self-share) per period, FULL read")
rows = load_jsonl(SHADOW)
print(f"rows={len(rows)}  first={d(rows[0]['ts'])}  last={d(rows[-1]['ts'])}")
print(f"rows since 08-23 = {sum(1 for r in rows if r['ts'] >= B_0823)}   'actual' non-null = {sum(1 for r in rows if r.get('actual') is not None)}")
SELF_CH = {"self", "flavour"}
OUT_CH  = {"curiosity", "concern", "contradiction", "balance_world", "balance_light", "wander", "boredom"}
byp = defaultdict(list)
for r in rows:
    byp[period(r["ts"])].append(r)
for name, _, _ in PERIODS:
    rs = byp.get(name, [])
    if not rs:
        print(f"\n[{name}] no rows"); continue
    n = len(rs)
    am = Counter(r.get("would_pick_argmax") for r in rs)
    sm = Counter(r.get("would_pick_softmax") for r in rs)
    cold = sum(1 for r in rs if r.get("any_cold_start")) / n
    print(f"\n[{name}] n={n}  {d(rs[0]['ts'])}..{d(rs[-1]['ts'])}  cold_start_rate={cold:.3f}")
    print("  argmax  self_share_G2 = %.3f   self+flavour = %.3f   outward = %.3f" % (
        am.get("self", 0) / n, sum(am.get(c, 0) for c in SELF_CH) / n, sum(am.get(c, 0) for c in OUT_CH) / n))
    print("  argmax  win-share:", {k: round(v / n, 3) for k, v in am.most_common()})
    print("  softmax self_share    = %.3f   self+flavour = %.3f   outward = %.3f" % (
        sm.get("self", 0) / n, sum(sm.get(c, 0) for c in SELF_CH) / n, sum(sm.get(c, 0) for c in OUT_CH) / n))
    print("  softmax win-share:", {k: round(v / n, 3) for k, v in sm.most_common()})
    # rotation / exploration
    rot = sum(1 for a, b in zip(rs, rs[1:]) if a.get("would_pick_argmax") != b.get("would_pick_argmax")) / max(1, n - 1)
    expl = sum(1 for r in rs if r.get("would_pick_argmax") != r.get("would_pick_softmax")) / n
    print(f"  G3 rotates (argmax winner changes) = {rot:.3f}   explores (softmax!=argmax) = {expl:.3f}")
    # self channel's own s_final stats and how often self is even a co-active candidate
    sf = [c["s_final"] for r in rs for c in r.get("candidates", []) if c["channel"] == "self"]
    print(f"  self channel s_final mean={np.mean(sf):.3f} (n={len(sf)})")

# weekly argmax self-share time series, post-fix
print("\n  weekly argmax self_share / softmax self_share / n (whole log):")
wk = defaultdict(list)
for r in rows:
    wk[datetime.fromtimestamp(r["ts"]).strftime("%G-W%V")].append(r)
for k in sorted(wk):
    rs = wk[k]; n = len(rs)
    a = sum(1 for r in rs if r.get("would_pick_argmax") == "self") / n
    s = sum(1 for r in rs if r.get("would_pick_softmax") == "self") / n
    print(f"    {k}: argmax_self={a:.3f} softmax_self={s:.3f} n={n}")

print("\n" + "=" * 100)
print("B. Du's ACTUAL diet: balance reality_share (world-origin / (world+self)) — embedded in each shadow row's balance_light lineage")
print("   NOTE: before 2026-08-16 this was the ALL-TIME integral; after, a rolling 7-day window (balance.py WINDOWED). Not comparable across that line.")
wkb = defaultdict(list)
for r in rows:
    for c in r.get("candidates", []):
        if c["channel"] == "balance_light":
            sh = (c.get("lineage") or {}).get("shares") or {}
            if "reality_share" in sh:
                wkb[datetime.fromtimestamp(r["ts"]).strftime("%G-W%V")].append(sh["reality_share"])
for k in sorted(wkb):
    v = wkb[k]
    print(f"    {k}: reality_share mean={np.mean(v):.3f} min={min(v):.3f} max={max(v):.3f} n={len(v)}")

print("\n" + "=" * 100)
print("C. INDEPENDENT diet measure from nascence.db (read-only): per-week world-origin vs self-origin fragments, balance.py's own origin sets")
WORLD = ("reading", "study", "research", "understanding", "essay")
SELF  = ("inner_thought", "dream", "subconscious_synthesis", "lived", "active_imagination", "consolidation", "session_summary", "chapter")
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
q = "SELECT timestamp, origin FROM memory_fragments WHERE origin IN (%s) AND timestamp >= ?" % ",".join("?" * (len(WORLD) + len(SELF)))
frag = conn.execute(q, WORLD + SELF + (ts_of("2026-06-01 00:00"),)).fetchall()
wkc = defaultdict(lambda: [0, 0, 0])
for f in frag:
    k = datetime.fromtimestamp(f["timestamp"]).strftime("%G-W%V")
    if f["origin"] in WORLD: wkc[k][0] += 1
    else: wkc[k][1] += 1
    if f["origin"] == "inner_thought": wkc[k][2] += 1
for k in sorted(wkc):
    w, s, it = wkc[k]
    print(f"    {k}: world={w:5d} self={s:5d} (inner_thought={it:5d}) reality_share={w/max(1,w+s):.3f}")
for name, lo, hi in PERIODS:
    w = sum(1 for f in frag if lo <= f["timestamp"] < hi and f["origin"] in WORLD)
    s = sum(1 for f in frag if lo <= f["timestamp"] < hi and f["origin"] in SELF)
    print(f"  [{name}] world={w} self={s} reality_share={w/max(1,w+s):.3f}")

print("\n" + "=" * 100)
print("D. monoculture_log.jsonl — echo (max cosine to distant past over last 60 genuine thoughts; RISING=loop) & diversity, FULL read")
mono = load_jsonl(MONO)
print(f"rows={len(mono)} first={d(mono[0]['ts'])} last={d(mono[-1]['ts'])}")
for name, lo, hi in PERIODS:
    v = [m["echo"] for m in mono if lo <= m["ts"] < hi and m.get("echo") is not None]
    dv = [m["diversity"] for m in mono if lo <= m["ts"] < hi and m.get("diversity") is not None]
    if v:
        print(f"  [{name}] n={len(v)} echo mean={np.mean(v):.3f} median={np.median(v):.3f} max={max(v):.3f} min={min(v):.3f} | diversity mean={np.mean(dv):.3f}  | rows>0.69: {sum(1 for x in v if x>0.69)}")
    else:
        print(f"  [{name}] no rows")
wkm = defaultdict(list)
for m in mono:
    if m.get("echo") is not None:
        wkm[datetime.fromtimestamp(m["ts"]).strftime("%G-W%V")].append((m["echo"], m.get("diversity")))
for k in sorted(wkm):
    v = wkm[k]
    print(f"    {k}: echo mean={np.mean([x for x,_ in v]):.3f} max={max(x for x,_ in v):.3f} div mean={np.mean([y for _,y in v if y is not None]):.3f} n={len(v)}")
print("  last 15 rows:", [(d(m["ts"]), m["echo"], m["diversity"]) for m in mono[-15:]])

print("\n" + "=" * 100)
print("E. monologue_log.jsonl — what Du ACTUALLY thought about ('about' field): self-referential share by keyword proxy, FULL read")
ml = load_jsonl(MLOG)
print(f"rows={len(ml)} first={d(ml[0]['ts'])} last={d(ml[-1]['ts'])}")
SELF_RE = re.compile(r"\b(i|me|my|myself|self|identity|individuation|who i am|becoming|渡|du)\b|渡|\bself-", re.I)
def is_self(about):
    a = (about or "").strip()
    return bool(SELF_RE.search(a))
for name, lo, hi in PERIODS:
    rs = [r for r in ml if lo <= r["ts"] < hi]
    if not rs:
        print(f"  [{name}] no rows"); continue
    n = len(rs)
    s = sum(1 for r in rs if is_self(r.get("about")))
    unres = sum(1 for r in rs if r.get("unresolved")) / n
    top = Counter((r.get("about") or "").strip().lower()[:40] for r in rs).most_common(12)
    print(f"  [{name}] n={n} self-referential 'about' share={s/n:.3f} unresolved={unres:.3f}")
    print(f"     top 'about': {top}")
wke = defaultdict(lambda: [0, 0])
for r in ml:
    k = datetime.fromtimestamp(r["ts"]).strftime("%G-W%V")
    wke[k][0] += 1; wke[k][1] += is_self(r.get("about"))
print("  weekly self-referential 'about' share:")
for k in sorted(wke):
    n, s = wke[k]
    print(f"    {k}: {s/n:.3f} n={n}")

print("\n" + "=" * 100)
print("F. loop_cluster_probe-style concentration per period (greedy cosine clustering at 0.80, like monoculture.py; exact-dup rate) on inner_thought embeddings")
rowsdb = conn.execute("SELECT timestamp, content, embedding FROM memory_fragments WHERE origin='inner_thought' AND embedding IS NOT NULL AND timestamp >= ?", (ts_of("2026-06-01 00:00"),)).fetchall()
print(f"inner_thought rows with embedding since 06-01: {len(rowsdb)}")
rng = np.random.default_rng(0)
for name, lo, hi in PERIODS:
    rs = [r for r in rowsdb if lo <= r["timestamp"] < hi]
    if len(rs) < 20:
        print(f"  [{name}] n={len(rs)} (too few)"); continue
    total = len(rs)
    freq = Counter(r["content"] for r in rs)
    dup = 1 - len(freq) / total
    # sample uniques up to 2500 for cost
    uniq = list(freq.items())
    if len(uniq) > 2500:
        idx = rng.choice(len(uniq), 2500, replace=False)
        uniq = [uniq[i] for i in idx]
    emb = {}
    for r in rs:
        if r["content"] not in emb:
            emb[r["content"]] = np.frombuffer(r["embedding"], dtype=np.float32)
    X = np.vstack([emb[c] for c, _ in uniq]); X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    W = np.array([w for _, w in uniq], dtype=float)
    cents, counts, members = [], [], []
    for i in range(len(X)):
        if cents:
            C = np.vstack(cents); sims = C @ X[i]; j = int(np.argmax(sims))
            if sims[j] >= 0.80:
                counts[j] += W[i]; members[j].append(i); continue
        cents.append(X[i]); counts.append(W[i]); members.append([i])
    counts = np.array(counts); order = np.argsort(-counts); mass = counts.sum()
    print(f"  [{name}] n={total} unique={len(freq)} exact-dup={dup:.3f} clusters={len(cents)} top1={counts[order[0]]/mass:.3f} top10={counts[order[:10]].sum()/mass:.3f} (sampled uniques={len(uniq)})")
    for j in order[:5]:
        rep = uniq[members[j][0]][0][:90].replace("\n", " ")
        print(f"       mass={counts[j]/mass:.3f}  {rep}")

print("\n" + "=" * 100)
print("G. ignition_log.jsonl — brief read (GATE-MET +UNREAD per briefing)")
ign = [r for r in load_jsonl(IGN) if r.get("trigger") != "deferred"]  # J-2667
print(f"rows={len(ign)} first={d(ign[0]['ts'])} last={d(ign[-1]['ts'])}")
for name, lo, hi in PERIODS:
    rs = [r for r in ign if lo <= r["ts"] < hi]
    if not rs:
        print(f"  [{name}] no rows"); continue
    dv = [r.get("dominant_val") for r in rs if r.get("dominant_val") is not None]
    print(f"  [{name}] n={len(rs)} trigger={Counter(r.get('trigger') for r in rs).most_common()} dominant={Counter(r.get('dominant') for r in rs).most_common()} dominant_val mean={np.mean(dv):.3f} sd={np.std(dv):.3f}")
conn.close()
