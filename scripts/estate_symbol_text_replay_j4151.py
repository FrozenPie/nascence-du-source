"""J-4151 (D-0778): lab measurement of the estate symbol-node text change, READ-ONLY on live data.

Reads the live estate file (data/identity_estate.json) and symbol_tablets (sqlite opened immutable, read-only),
builds two estates in memory -- symbol nodes with the OLD placeholder text and with the NEW
"<symbol> — now: <newest tablet>" text (core.identity_estate._symbol_node_text) -- and replays the projection
selection (core.identity_projection.project with commit=False, so rotation memory never advances) over a sample of
recent projection contexts from data/identity_projection_shadow.jsonl. Reports symbol share of slots under each
text and how picks change. D-0778 defeater: symbol share moving more than a few points of slots.

Nothing under data/ is written. The estate copy the projection reads is a temp file; output goes to --out.
Run: python scripts/estate_symbol_text_replay_j4151.py --out <scratch json> [--n 300] [--data C:/Nascence/data]
"""
import argparse, json, random, sqlite3, sys, tempfile
from collections import Counter
from pathlib import Path
WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
import core                                                            # tree under test
assert str(Path(core.__file__).resolve()).startswith(str(WT)), core.__file__
from core import identity_estate as ie
from core import identity_projection as ip


def newest_tablets(db: Path) -> dict:
    uri = "file:" + db.resolve().as_posix() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True); conn.row_factory = sqlite3.Row
    best = {}
    for r in conn.execute("SELECT symbol, tablet, created FROM symbol_tablets ORDER BY rowid"):
        nid = f"symb_{str(r['symbol'])[:20]}"
        if nid not in best or r["created"] >= best[nid][0]:
            best[nid] = (r["created"], r["symbol"], r["tablet"])
    conn.close()
    return best


def contexts(shadow: Path, n: int, seed: int = 4151) -> list:
    rows = []
    with shadow.open(encoding="utf-8") as f:
        for line in f:
            try:
                c = json.loads(line).get("context")
            except Exception:
                continue
            if c and c.strip():
                rows.append(c)
    recent = rows[-max(n * 4, n):]
    random.Random(seed).shuffle(recent)
    return recent[:n]


def replay(estate: dict, ctxs: list, tmpdir: Path, tag: str) -> list:
    f = tmpdir / f"estate_{tag}.json"
    f.write_text(json.dumps(estate, ensure_ascii=False), encoding="utf-8")
    ip._ESTATE_F = f
    ip._cache.update({"sig": None, "nodes": None, "embs": None})
    ip._recency.clear()
    out = []
    for c in ctxs:
        out.append(ip.project(c, commit=False)["nodes"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(WT.parent / "data") if (WT.parent / "data").exists() else "C:/Nascence/data")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    data = Path(a.data)
    out = Path(a.out).resolve()
    assert not str(out).lower().startswith(str(data.resolve()).lower()), "never write under data/"
    est = json.loads((data / "identity_estate.json").read_text(encoding="utf-8"))
    best = newest_tablets(data / "memory" / "nascence.db")
    ctxs = contexts(data / "identity_projection_shadow.jsonl", a.n)
    ip._floor = lambda: "I am one self."            # the floor is constant across both arms; skip the live read
    old, new, changed = json.loads(json.dumps(est)), json.loads(json.dumps(est)), 0
    for arm, flag in ((old, False), (new, True)):
        ie.SYMBOL_NODE_NEWEST_TABLET = flag
        for nd in arm["nodes"]:
            if nd.get("source") == "symbol_evolution" and nd.get("id") in best:
                _, sym, tab = best[nd["id"]]
                nd["text"] = ie._symbol_node_text(sym, tab)
                changed += flag
    ie.SYMBOL_NODE_NEWEST_TABLET = True
    tmpdir = Path(tempfile.mkdtemp(prefix="j4151_replay_"))
    po, pn = replay(old, ctxs, tmpdir, "old"), replay(new, ctxs, tmpdir, "new")
    def share(picks):
        slots = sum(len(p) for p in picks)
        sym = sum(1 for p in picks for x in p if x["type"] == "symbol")
        tsym = sum(1 for p in picks for x in p if x["type"] == "symbol" and str(x["id"]) not in ("symb_river", "symb_du"))
        return {"slots": slots, "symbol_slots": sym, "symbol_share_pct": round(100.0 * sym / max(1, slots), 2),
                "tablet_symbol_slots": tsym, "tablet_symbol_share_pct": round(100.0 * tsym / max(1, slots), 2),
                "contexts_with_symbol_pct": round(100.0 * sum(any(x["type"] == "symbol" for x in p) for p in picks)
                                                  / max(1, len(picks)), 2)}
    so, sn = share(po), share(pn)
    same = sum(1 for x, y in zip(po, pn) if [n["id"] for n in x] == [n["id"] for n in y])
    jac = [len({n["id"] for n in x} & {n["id"] for n in y}) / max(1, len({n["id"] for n in x} | {n["id"] for n in y}))
           for x, y in zip(po, pn)]
    top_new = Counter(n["id"] for p in pn for n in p if n["type"] == "symbol").most_common(8)
    top_old = Counter(n["id"] for p in po for n in p if n["type"] == "symbol").most_common(8)
    rep = {"contexts": len(ctxs), "symbol_nodes_retexted": changed, "old": so, "new": sn,
           "symbol_share_delta_pts": round(sn["symbol_share_pct"] - so["symbol_share_pct"], 2),
           "identical_pick_lists_pct": round(100.0 * same / max(1, len(ctxs)), 2),
           "mean_jaccard_old_vs_new": round(sum(jac) / max(1, len(jac)), 3),
           "top_symbol_ids_old": top_old, "top_symbol_ids_new": top_new,
           "sample_new_texts": [nd["text"][:200] for nd in new["nodes"]
                                if nd.get("source") == "symbol_evolution"][:5]}
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("contexts", "symbol_nodes_retexted", "old", "new", "symbol_share_delta_pts",
                                          "identical_pick_lists_pct", "mean_jaccard_old_vs_new")}, indent=1))


if __name__ == "__main__":
    main()
