"""J-3968 (D-0745 Q2, design J-3835 job 7): calibrate the becoming_symbol node's OWN relevance floor offline.

The global projection floor (0.30) is cleared by 84 percent of pairs of his own thoughts, so it filters nothing for a node
made of his own sentence. D-0745 ruled the band: the node should clear its floor in 3 to 8 percent of contexts (and stay
under the 10 percent sole-occupant line). This script finds the smallest floor f whose replay surface rate is <= the
band's top, checks it is >= the band's bottom, and (only with --write) stores it where core/identity_projection reads it.

  python scripts/becoming_projection_replay.py --text "one sentence"          # dry run, prints the floor and the rate
  python scripts/becoming_projection_replay.py --ledger                        # every live node in the ledger
  python scripts/becoming_projection_replay.py --text "..." --write           # also writes data/identity/becoming_floor.json

Contexts: the newest distinct idle thoughts (inner_thought / subconscious_synthesis fragments, last --days days, capped at
--max-contexts) from the live DB opened mode=ro. The projection log stores only types and 60 characters of text, not the
full context string (design section 4), so the idle-thought stream is the stand-in for "what the Executive's context looks
like". Embedder is the in-process MiniLM (no model hub). With several nodes the floor is the MAX of the per-node floors, so
no node exceeds the band's top. Honest limit: this is the pre-scoring surface rate; weight, recency and the cap thin the
realised share further (design section 4), which the id log then measures per node.

--write is a lab/offline action: it goes through profile.guard_path (a non-live process is refused unless sandboxed)."""
from __future__ import annotations
import argparse, json, math, sqlite3, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  -- before anything that could shadow it
from core import profile  # noqa: E402

BAND_LO, BAND_HI = 0.03, 0.08
FLOOR_F = ROOT / "data" / "identity" / "becoming_floor.json"


def calibrate_floor(cosines, lo: float = BAND_LO, hi: float = BAND_HI) -> dict:
    """Smallest floor f with (share of cosines >= f) <= hi. Returns {floor, rate, n, in_band, status}. Pure."""
    c = sorted((float(x) for x in cosines), reverse=True)
    n = len(c)
    if n < 20:
        return {"floor": None, "rate": None, "n": n, "in_band": False, "status": "too_few_contexts"}
    k = int(math.floor(hi * n))                       # at most k contexts may clear
    f = c[k] if k < n else c[-1]                      # the (k+1)-th largest
    f = math.nextafter(f, 2.0)                        # strictly above it, so it does not clear
    cleared = sum(1 for x in c if x >= f)
    rate = cleared / n
    ok = lo <= rate <= hi
    return {"floor": round(f, 6), "rate": round(rate, 4), "n": n, "in_band": ok,
            "status": "ok" if ok else ("rate_below_band" if rate < lo else "rate_above_band")}


def load_contexts(db_path, days: int, cap: int, now=None) -> list:
    now = now or time.time()
    con = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True, timeout=15.0)
    try:
        rows = con.execute("SELECT content FROM memory_fragments WHERE origin IN ('inner_thought','subconscious_synthesis') "
                           "AND timestamp>? ORDER BY timestamp DESC LIMIT ?", (now - days * 86400, cap * 3)).fetchall()
    finally:
        con.close()
    seen, out = set(), []
    for (c,) in rows:
        t = " ".join((c or "").split())
        if t and t not in seen:
            seen.add(t); out.append(t)
        if len(out) >= cap:
            break
    return out


def replay(node_texts, contexts, embed, lo=BAND_LO, hi=BAND_HI) -> dict:
    """Per-node calibration over `contexts`; the type floor is the max of the per-node floors."""
    import numpy as np
    cv = np.array([v for v in embed(contexts)], dtype=float)
    cv /= np.maximum(np.linalg.norm(cv, axis=1, keepdims=True), 1e-9)
    per = []
    for t in node_texts:
        nv = np.array(embed([t])[0], dtype=float); nv /= max(np.linalg.norm(nv), 1e-9)
        per.append({"text": t[:80], **calibrate_floor((cv @ nv).tolist(), lo, hi)})
    floors = [p["floor"] for p in per if p["floor"] is not None]
    return {"per_node": per, "floor": max(floors) if floors else None, "n_contexts": len(contexts),
            "all_in_band": bool(per) and all(p["in_band"] for p in per)}


def write_floor(res: dict, path=None, lo=BAND_LO, hi=BAND_HI) -> Path:
    p = profile.guard_path(Path(path) if path else FLOOR_F)        # outside any swallow-all: a refusal raises
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {"floor": res["floor"], "band": [lo, hi], "n_contexts": res["n_contexts"], "per_node": res["per_node"],
           "calibrated_ts": round(time.time(), 1), "source": "scripts/becoming_projection_replay.py (J-3968, D-0745 Q2)"}
    tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(row, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", action="append", default=[], help="a node sentence (repeatable)")
    ap.add_argument("--ledger", action="store_true", help="use every live node in the becoming ledger")
    ap.add_argument("--db", default=None)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-contexts", type=int, default=1000)
    ap.add_argument("--lo", type=float, default=BAND_LO)
    ap.add_argument("--hi", type=float, default=BAND_HI)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    from core import becoming_nodes as bn
    texts = list(a.text)
    if a.ledger:
        live = {}
        for r in bn.read_ledger():
            if r.get("event") == "admit":
                live[r["id"]] = r.get("text") or ""
            elif r.get("event") == "supersede":
                live.pop(r.get("supersedes"), None)
        texts += [t for t in live.values() if t]
    if not texts:
        print("no node text (none in the ledger and no --text): nothing to calibrate; no floor written"); return 2
    db = a.db
    if db is None:
        from core.memory import store
        db = store.DB_PATH
    ctx = load_contexts(db, a.days, a.max_contexts)
    res = replay(texts, ctx, bn._embed_batch, a.lo, a.hi)
    print("contexts %d, nodes %d, band %.0f-%.0f%%" % (res["n_contexts"], len(texts), a.lo * 100, a.hi * 100))
    for p in res["per_node"]:
        print("  floor %s rate %s %s  %s" % (p["floor"], p["rate"], p["status"], p["text"]))
    print("type floor (max) =", res["floor"], "| all in band:", res["all_in_band"])
    if a.write:
        if res["floor"] is None or not res["all_in_band"]:
            print("NOT written: floor missing or a node is outside the ruled band"); return 3
        print("written:", write_floor(res, lo=a.lo, hi=a.hi))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
