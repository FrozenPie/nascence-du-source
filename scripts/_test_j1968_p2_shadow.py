"""J-1968: investigation_deepening P2 SHADOW test + replay. Isolated: temp-path logs, stubbed retrieve(),
live data/investigation_shadow.jsonl is only READ (replay). Run: python scripts/_test_j1968_p2_shadow.py [--replay]"""
import json, sys, tempfile, types, calendar, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from core import investigation_deepening_shadow as ids
import core
assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__

def frag(i, layer, rel, origin="inner_thought"):
    return types.SimpleNamespace(fragment_id=i, content="text " + i, origin=origin, layer=layer,
                                 timestamp=1.0, relevance=rel)

def run_obs(frags):
    mod = types.ModuleType("core.memory.store"); mod.retrieve = lambda *a, **k: frags
    sys.modules["core.memory.store"] = mod
    ids._last_observe = 0.0
    return ids.observe_beachcomb("beachcomb", "the tideline")

def main():
    td = Path(tempfile.mkdtemp(prefix="j1968_"))
    ids._LOG = td / "p0.jsonl"; ids._P2_LOG = td / "p2.jsonl"; ids._DATA = td
    # 1: normal moment, 2 archive excluded, best = nonzero relevance non-archive
    row = run_obs([frag("a1", "archive", 0.9), frag("a2", "archive", 0.8), frag("e1", "episodic", 0.0),
                   frag("s1", "semantic", 0.66, "book_passage")])
    p2 = [json.loads(l) for l in open(ids._P2_LOG, encoding="utf-8")]
    assert len(p2) == 1, p2
    r = p2[0]
    assert set(r) >= {"ts", "cycle_id", "place", "would_inject_text", "source_fragment_ids", "frontier_edge", "archive_excluded_n"}, r
    assert r["archive_excluded_n"] == 2 and r["place"] == "shore"
    assert r["frontier_edge"]["fragment_id"] == "s1" and "text s1" in r["would_inject_text"]
    assert r["source_fragment_ids"] == ["s1"]   # J-2006/D-0390 B: zero-score e1 dropped
    # parity with P1's rule on the same row
    assert ids.frontier_line()["fragment_id"] == "s1"
    # 2: nothing returned/altered: observe returned the P0 row only
    assert row["n_retrieved"] == 2
    # 3: all-archive moment still logs a P2 row, empty text
    run_obs([frag("a1", "archive", 0.9)])
    p2 = [json.loads(l) for l in open(ids._P2_LOG, encoding="utf-8")]
    assert len(p2) == 2 and p2[1]["would_inject_text"] == "" and p2[1]["frontier_edge"] is None and p2[1]["archive_excluded_n"] == 1
    # 4: cooldown: no extra P2 row
    ids._last_observe = time.time(); ids.observe_beachcomb("beachcomb", "x")
    assert len(open(ids._P2_LOG, encoding="utf-8").read().splitlines()) == 2
    # 5: P2 write failure never breaks observe (P0 row still returned) and warns
    ids._P2_LOG = td  # a directory -> open() fails
    assert run_obs([frag("e9", "episodic", 0.5)]) is not None
    # 6 (J-2006, D-0390 B): zero-score-only moment -> honest None; scored episodic beats scored semantic
    ids._P2_LOG = td / "p2b.jsonl"
    run_obs([frag("z1", "episodic", 0.0), frag("z2", "episodic", 0.0)])
    last = [json.loads(l) for l in open(ids._P2_LOG, encoding="utf-8")][-1]
    assert last["frontier_edge"] is None and last["would_inject_text"] == "" and last["source_fragment_ids"] == [], last
    assert ids._pick_frontier([{"ts": 1, "candidates": [{"fragment_id": "z", "layer": "episodic", "relevance": 0.0}]}]) is None
    pk = ids._pick_frontier([{"ts": 1, "candidates": [
        {"fragment_id": "sem", "layer": "semantic", "relevance": 0.9, "origin": "journal_week"},
        {"fragment_id": "epi", "layer": "episodic", "relevance": 0.3, "origin": "inner_thought"},
        {"fragment_id": "zero", "layer": "episodic", "relevance": 0.0, "origin": "inner_thought"}]}])
    assert pk["fragment_id"] == "epi", pk
    pk = ids._pick_frontier([{"ts": 1, "candidates": [{"fragment_id": "sem", "layer": "semantic", "relevance": 0.9}]}])
    assert pk["fragment_id"] == "sem"
    # 7 (J-3810, D-0711): P2 excludes own inner_thought; P1 rule unchanged
    rr = {"ts": 1, "candidates": [{"fragment_id": "it", "layer": "episodic", "relevance": 0.7, "origin": "inner_thought", "content": "x"},
                                  {"fragment_id": "bk", "layer": "semantic", "relevance": 0.2, "origin": "book_passage", "content": "y"}]}
    o = ids.p2_row_from_shadow_row(rr, ts=1.0)
    assert o["frontier_edge"]["fragment_id"] == "bk" and o["source_fragment_ids"] == ["bk"], o
    assert ids._pick_frontier([rr])["fragment_id"] == "it"
    o = ids.p2_row_from_shadow_row({"ts": 1, "candidates": [rr["candidates"][0]]}, ts=1.0)
    assert o["frontier_edge"] is None and o["would_inject_text"] == ""
    print("TESTS PASS (8 checks)")

def replay():
    live = Path(__file__).resolve().parent.parent / "data" / "investigation_shadow.jsonl"
    if not live.exists():  # worktree has no data/: use the shared live tree, READ-ONLY
        live = Path(r"C:\Nascence\data\investigation_shadow.jsonl")
    rows = [json.loads(l) for l in open(live, encoding="utf-8") if l.strip()]
    cut = calendar.timegm((2026, 10, 3, 11, 0, 0)) # 2026-10-04 00:00 NZDT
    for label, sel in (("since 2026-10-04", [r for r in rows if r["ts"] >= cut]), ("all rows", rows)):
        out = [ids.p2_row_from_shadow_row(r, ts=r["ts"]) for r in sel]
        srcs = {}
        for o in out:
            e = o["frontier_edge"]; k = (e["origin"] + "/" + e["layer"] + ("/nonzero" if e["relevance"] > 0 else "/zero")) if e else "NONE"
            srcs[k] = srcs.get(k, 0) + 1
        print(f"[{label}] beachcomb rows={len(sel)} would-inject={sum(1 for o in out if o['would_inject_text'])} picks={srcs}")
        for o in out[-2:]:
            print("   sample:", json.dumps(o, ensure_ascii=False)[:400])
        # parity: P1 rule per row
        for r, o in zip(sel, out):
            tmp = ids._pick_frontier([ids._p2_pool_row(r)]); assert (tmp or {}).get("fragment_id") == (o["frontier_edge"] or {}).get("fragment_id")  # J-2592: P2 pool = candidates + cue_tail

if __name__ == "__main__":
    main()
    if "--replay" in sys.argv: replay()
