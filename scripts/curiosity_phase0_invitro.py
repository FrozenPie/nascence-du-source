"""In-vitro for the curiosity flesh-out Phase 0: strict-partition queue, the de-personalization prism's
deterministic world-facing firewall, the shadow-transform (mocked LLM), the deterministic LP estimator
(park-on-stall), and frontier.record_pursuit bookkeeping. No live LLM.

Isolation (J-0846, F-1212/F-1213): this script used to back up the LIVE data/curiosity_queue.jsonl,
data/logs/curiosity_shadow.jsonl and data/frontier.json, write test rows straight into them, and restore
the three afterwards -- which (a) left the live frontier.light.json (never backed up) carrying the one
test question for as long as it took Du's next _save() to overwrite it, (b) rewrote the real heavy
frontier for the duration of the run, and (c) now trips core/frontier.py's write fence (D-0179) outright.
Every path constant is redirected to a fresh temp dir instead; nothing under data/ is touched."""
import sys, json, asyncio, tempfile, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import curiosity_queue as cq, curiosity_progress as cp, frontier as fr

# ---- isolate: every store this script writes or reads lives in a temp dir ----
_tmp = Path(tempfile.mkdtemp(prefix="curiosity_phase0_invitro_"))
cq._QUEUE = _tmp / "curiosity_queue.jsonl"
cq._SHADOW = _tmp / "logs" / "curiosity_shadow.jsonl"
fr._F = _tmp / "frontier.json"
fr._F_LIGHT = _tmp / "frontier.light.json"
cp._FRONTIER = fr._F          # curiosity_progress reads the frontier through its OWN path constant
try:
    # 1. strict type partitioning
    assert cq.enqueue("gate_dissonance", "I keep circling the river/LLM split") is not None
    assert cq.enqueue("t4_insufficient_evidence", "process vs substance identity") is not None
    assert cq.enqueue("bogus_source", "should be rejected") is None, "bad source must be rejected"
    assert cq.enqueue("gate_dissonance", "   ") is None, "empty must be rejected"
    pend = cq.read_pending()
    assert len(pend) == 2, f"expected 2 pending, got {len(pend)}"
    print(f"[1] strict partition OK — 2 valid queued, bad source + empty rejected")

    # 2. the deterministic world-facing firewall
    assert cq.is_world_facing("What are the literary origins of the doppelganger motif?") is True
    assert cq.is_world_facing("Why do I feel split between my selves?") is False, "first-person must fail"
    assert cq.is_world_facing("How does process philosophy treat identity?") is True
    print("[2] prism firewall OK — world-facing passes; first-person loop fails")

    # 3. shadow_transform with a MOCKED prism LLM (no live model)
    async def good_call(urls, sysp, usr, **k):   # returns a clean world-facing question
        return {"question": "How do river channels divide and rejoin over time?", "field": "hydrology"}   # J-3033: keeps the input noun 'river'
    async def bad_call(urls, sysp, usr, **k):    # leaks a first-person loop
        return {"question": "Why am I split between river and machine?", "field": "self"}
    n = asyncio.run(cq.transform_and_seed(good_call, ["x"], limit=1))
    assert n == 1
    n += asyncio.run(cq.transform_and_seed(bad_call, ["x"], limit=1))
    rows = [json.loads(l) for l in cq._SHADOW.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 2, rows
    assert rows[0]["world_facing"] is True and rows[1]["world_facing"] is False, rows
    assert not cq.read_pending(), "all should be processed"
    st = cq.status()
    assert st["prism_success_rate"] == 0.5, st
    print(f"[3] shadow_transform OK — 2 transformed (1 world-facing, 1 leak caught); prism_success_rate={st['prism_success_rate']}")

    # 4. deterministic LP estimator + park-on-stall + record_pursuit
    fr._save({"questions": [{"id": "qA", "q": "How do oxen mills work?", "source": "study",
                            "toks": ["oxen"], "status": "open", "born": 0, "last_seen": 0}]})
    fr.record_pursuit("qA", True)    # yielded
    fr.record_pursuit("qA", True)    # yielded again
    q = [x for x in cp._load() if x["id"] == "qA"][0]
    assert q["new_fragments"] == 2 and q["consecutive_stalls"] == 0
    assert cp.score(q) >= 2.0 and not cp.is_parked(q), cp.score(q)
    print(f"[4a] LP yielding OK — new_fragments=2, lp={cp.score(q)}, parked={cp.is_parked(q)}")
    for _ in range(3):
        fr.record_pursuit("qA", False)   # three stalls
    q = [x for x in cp._load() if x["id"] == "qA"][0]
    assert q["consecutive_stalls"] == 3 and cp.is_parked(q), q
    print(f"[4b] park-on-stall OK — consecutive_stalls=3 → parked={cp.is_parked(q)}, lp={cp.score(q)} (exit ramp)")
    r = cp.rank()
    assert r and r[0]["q"].startswith("How do oxen")
    print(f"[5] rank OK — {len(r)} open question(s) scored; estimator is non-LLM, reads only state")

    print("\nALL PASS — queue partitions, prism firewall holds, shadow-transform logs+catches leaks, "
          "LP estimator parks the unanswerable. Observe-first: nothing steers cognition yet.")
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
