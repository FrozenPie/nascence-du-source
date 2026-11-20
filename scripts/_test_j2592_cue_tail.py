"""J-2592 (D-0518, F-3265): P2 shore-beachcomb shadow now sees the cue-scored episodic hits that retrieve()
returns PAST observe_beachcomb()'s RETRIEVE_LIMIT cap (the recency guarantee's 5 zero-score fillers used to
fill the cap). Isolated: temp-path logs, stubbed retrieve(); no store, no model.
Run: python scripts/_test_j2592_cue_tail.py [--replay]   (--replay only READS the live data/investigation_shadow.jsonl)"""
import json, sys, tempfile, types, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
import core
from core import investigation_deepening_shadow as ids
assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__

def frag(i, layer, rel, origin="inner_thought"):
    return types.SimpleNamespace(fragment_id=i, content="text " + i, origin=origin, layer=layer,
                                 timestamp=1.0, relevance=rel)

def run_obs(frags):
    mod = types.ModuleType("core.memory.store"); mod.retrieve = lambda *a, **k: frags
    sys.modules["core.memory.store"] = mod
    ids._last_observe = 0.0
    return ids.observe_beachcomb("beachcomb", "the tideline")

# retrieve()'s real return order (store.py: archive top-1, then the 5 recency-guarantee episodic at 0.0, then
# the rest of archive, semantic tier, cue-scored episodic tier) -- the shape 116/116 live P0 rows show.
LIVE_SHAPE = ([frag("a1", "archive", 0.8)] + [frag(f"r{i}", "episodic", 0.0) for i in range(5)] +
              [frag("a2", "archive", 0.7), frag("jw", "semantic", 0.66, "journal_week"),
               frag("s2", "semantic", 0.41, "consolidation"), frag("s3", "semantic", 0.0, "consolidation"),
               frag("e1", "episodic", 0.52), frag("e2", "episodic", 0.47), frag("e3", "episodic", 0.0)])

def main():
    td = Path(tempfile.mkdtemp(prefix="j2592_"))
    ids._LOG = td / "p0.jsonl"; ids._P2_LOG = td / "p2.jsonl"; ids._DATA = td
    ids.P2_USE_CUE_TAIL = True
    ids.P2_EXCLUDE_ORIGINS = frozenset()   # J-3810: this test is about the cue_tail pool, not origin narrowing
    row = run_obs(LIVE_SHAPE)
    # 1: P0 `candidates` unchanged (cap still keeps 5 fillers + jw) -> P0 metric and P1 pool untouched
    assert [c["fragment_id"] for c in row["candidates"]] == ["r0", "r1", "r2", "r3", "r4", "jw"], row["candidates"]
    assert row["n_retrieved"] == 6
    # 2: cue_tail = only the relevance>0 hits past the cap, in retrieve order
    assert [c["fragment_id"] for c in row["cue_tail"]] == ["s2", "e1", "e2"], row["cue_tail"]
    # 3: P2 picks Du's own cue-scored episodic material (highest relevance episodic)
    p2 = [json.loads(l) for l in open(ids._P2_LOG, encoding="utf-8")][-1]
    assert p2["frontier_edge"]["fragment_id"] == "e1" and p2["frontier_edge"]["layer"] == "episodic", p2
    assert p2["frontier_edge"]["relevance"] > 0 and "text e1" in p2["would_inject_text"]
    assert p2["cue_tail_n"] == 3
    # 4: D-0518 defeater guard: J-2126 static journal_week never enters P2's pool; zero-scores never do
    assert "jw" not in p2["source_fragment_ids"] and not any(f.startswith("r") for f in p2["source_fragment_ids"])
    assert p2["source_fragment_ids"] == ["s2", "e1", "e2"], p2["source_fragment_ids"]
    # 5: P1 (live journal frontier_line) unchanged: reads `candidates` only -> jw dropped -> None, as before
    assert ids.frontier_line() is None
    # 6: kill switch: P2_USE_CUE_TAIL False reproduces pre-J-2592 P2 (empty would-inject on the same row)
    ids.P2_USE_CUE_TAIL = False
    old = ids.p2_row_from_shadow_row(row, ts=row["ts"])
    assert old["frontier_edge"] is None and old["would_inject_text"] == "" and old["cue_tail_n"] == 0
    ids.P2_USE_CUE_TAIL = True
    # 7: pre-J-2592 rows (no cue_tail key) replay exactly as before
    legacy = {k: v for k, v in row.items() if k != "cue_tail"}
    assert ids._p2_pool_row(legacy) is legacy and ids.p2_row_from_shadow_row(legacy)["frontier_edge"] is None
    # 8: semantic-only tail still selectable (episodic preferred when both); dedupe vs candidates
    r2 = {"ts": 1, "candidates": [{"fragment_id": "x", "layer": "semantic", "relevance": 0.3, "origin": "consolidation"}],
          "cue_tail": [{"fragment_id": "x", "layer": "semantic", "relevance": 0.3, "origin": "consolidation"}]}
    assert len(ids._p2_pool_row(r2)["candidates"]) == 1
    # 9: tail capped; an all-zero tail logs nothing
    row9 = run_obs([frag(f"r{i}", "episodic", 0.0) for i in range(6)] + [frag(f"t{i}", "episodic", 0.1) for i in range(20)])
    assert len(row9["cue_tail"]) == ids.CUE_TAIL_LIMIT
    row10 = run_obs([frag(f"r{i}", "episodic", 0.0) for i in range(9)])
    assert row10["cue_tail"] == []
    # 10: P2 write failure still never breaks observe
    ids._P2_LOG = td
    assert run_obs(LIVE_SHAPE) is not None
    print("J-2592 TESTS PASS (10 checks)")

def replay():
    live = Path(r"C:\Nascence\data\investigation_shadow.jsonl")
    rows = [json.loads(l) for l in open(live, encoding="utf-8") if l.strip()]
    have = sum(1 for r in rows if "cue_tail" in r)
    out = [ids.p2_row_from_shadow_row(r, ts=r["ts"]) for r in rows]
    print(f"[replay READ-ONLY] P0 rows={len(rows)} rows_with_cue_tail={have} "
          f"would-inject={sum(1 for o in out if o['would_inject_text'])} "
          f"episodic_picks={sum(1 for o in out if (o['frontier_edge'] or {}).get('layer') == 'episodic')}")

if __name__ == "__main__":
    main()
    if "--replay" in sys.argv: replay()
