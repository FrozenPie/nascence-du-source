"""J-2604 (D-0515, F-3327): hermetic test of core/evidence_recall.py's corrected R2 instrument.

Covers: gather() writes a `source` field (default route2; follow_line's grounds stop passes follow_line);
r2_signature() classifies rows by source (pre-boot rows without the field = route2, post-boot rows named in
Follow Line's shadow log = follow_line_inferred, else unknown), keeps every legacy field, counts only own-act
Route 2 trains as grounded, excludes every asked train from the ungrounded pool, runs the J-2587 matched-pairs
port (prior length k, alive at k, window, TF-IDF topic, 1:1 greedy) and codes the verdict on earned length.

Every store is a temp path; no model, no judge, no live data/ write. Run from a worktree:
    python scripts/r2_signature_test.py
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE lab_env (feedback_jobrun_live_store_leaks)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402
from core import evidence_recall as ev  # noqa: E402
from core import follow_line as fl  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def build_stores(tmp: Path, n_own: int):
    boot = ev.R2_SOURCE_AMBIGUOUS_SINCE
    t0 = boot - 5 * 86400
    ev_rows, lens, states, flog = [], [], [], []

    def train(tid, ts, length, topic, ask_after_step=None, src=None, ask_ts=None, q=None, fl_named=False):
        for s in range(1, length + 1):
            states.append({"ts": ts + s, "train_id": tid, "step": s, "thought": f"{topic} step {s} thinking"})
        lens.append({"ts": ts + length + 1, "kind": "thought", "train_id": tid, "length": length,
                     "reason": "thread-end"})
        if ask_after_step is not None:
            row = {"ts": ask_ts if ask_ts is not None else ts + ask_after_step + 0.5,
                   "question": q or f"what bears on {topic}?", "n_candidates": 0, "judged": [],
                   "outcome": "empty", "n_returned": 0, "secs": 0.1, "train_id": tid}
            if src:
                row["source"] = src
            ev_rows.append(row)
            if fl_named:
                flog.append({"ts": row["ts"], "kind": "would_return", "train_id": tid, "q": row["question"]})

    for i in range(n_own):                          # own Route 2 asks, pre-boot, no source field: earned
        topic = f"alpha{i}word beta{i}word"
        train(f"g{i}", t0 + i * 600, 6, topic, ask_after_step=1)
        train(f"u{i}", t0 + i * 600 + 30, 2, topic)      # same topic, alive at k=1, not earned
    train("gk3", t0 + 99999, 4, "gammaword deltaword", ask_after_step=3)   # k=3: no ungrounded alive at 3
    train("ugk", t0 + 99999 + 30, 2, "gammaword deltaword")
    pb = boot + 3600                                # post-boot asks
    for i in range(5):
        train(f"fi{i}", pb + i * 600, 7, f"flinf{i} topic", ask_after_step=1, fl_named=True)
    for i in range(3):
        train(f"un{i}", pb + 9000 + i * 600, 7, f"unk{i} topic", ask_after_step=1)
    for i in range(2):
        train(f"fe{i}", pb + 20000 + i * 600, 7, f"flexp{i} topic", ask_after_step=1, src="follow_line")
    train("re0", pb + 30000, 6, "rexp topic", ask_after_step=1, src="route2")
    ev_rows.append({"ts": t0, "question": "no train id ask", "outcome": "empty", "train_id": None})
    paths = {"_LOG": tmp / "evidence_log.jsonl", "_TRAIN_LOG": tmp / "train_length_log.jsonl",
             "_TRAIN_STATE_LOG": tmp / "train_state_log.jsonl", "_FOLLOW_LINE_LOG": tmp / "fl.jsonl"}
    write_jsonl(paths["_LOG"], ev_rows)
    write_jsonl(paths["_TRAIN_LOG"], lens)
    write_jsonl(paths["_TRAIN_STATE_LOG"], states)
    write_jsonl(paths["_FOLLOW_LINE_LOG"], flog)
    return paths


def main():
    with isolate(db="empty"), tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        orig = {k: getattr(ev, k) for k in ("_LOG", "_TRAIN_LOG", "_TRAIN_STATE_LOG", "_FOLLOW_LINE_LOG", "_candidates")}
        from core import memory_edges, memory_service
        orig_lcr, orig_su = memory_edges.log_co_recall, memory_service.stash_usage
        try:
            # ---- gather() writes source; no candidates, no judge, side-logs stubbed ----
            ev._LOG = tmp / "gather_log.jsonl"
            ev._candidates = lambda q, k=ev.K_CANDIDATES: []
            memory_edges.log_co_recall = lambda *a, **k: None
            memory_service.stash_usage = lambda *a, **k: None
            asyncio.run(ev.gather("does the garden remember the frost?", train_id="t1"))
            asyncio.run(ev.gather("does the garden remember the frost?", train_id="t2", source="follow_line"))
            rows = [json.loads(l) for l in open(ev._LOG, encoding="utf-8")]
            check("gather default source=route2", rows[0].get("source") == "route2", rows[0])
            check("gather source=follow_line", rows[1].get("source") == "follow_line", rows[1])
            check("gather keeps train_id", rows[0].get("train_id") == "t1")
            seen = {}
            orig_gather = ev.gather

            async def fake_gather(q, train_id=None, source="route2", dedupe=False):
                seen.update(q=q, train_id=train_id, source=source)
                return {"episodes": [], "outcome": "empty"}
            ev.gather = fake_gather
            try:
                asyncio.run(fl._stop_grounds("why does the cat sleep?", "t9"))
            finally:
                ev.gather = orig_gather
            check("follow_line grounds stop passes source=follow_line", seen.get("source") == "follow_line", seen)

            # ---- r2_signature on a synthetic store ----
            paths = build_stores(tmp / "big", n_own=22)
            for k, v in paths.items():
                setattr(ev, k, v)
            r = ev.r2_signature()
            for key in ("n_asks", "n_asks_with_train_id", "grounded_trains", "ungrounded_trains", "note",
                        "verdict", "min_n"):
                check(f"legacy field kept: {key}", key in r)
            check("legacy grounded counts every source (22+1+5+3+2+1=34)", r["grounded_trains"]["n"] == 34,
                  r["grounded_trains"])
            check("legacy productive kept as secondary", "productive_close_rate" in r["grounded_trains"])
            src = r["asks_by_source"]
            check("pre-boot rows -> route2_inferred (22+1+1 no-train-id)", src.get("route2_inferred") == 24, src)
            check("post-boot rows named by Follow Line log -> follow_line_inferred", src.get("follow_line_inferred") == 5, src)
            check("post-boot unnamed rows -> unknown", src.get("unknown") == 3, src)
            check("explicit sources honoured", src.get("follow_line") == 2 and src.get("route2") == 1, src)
            check("own grounded = route2 trains only (22+1+1)", r["own_grounded_trains"]["n"] == 24, r["own_grounded_trains"])
            check("other-source trains in neither pool", r["n_trains_asked_only_by_other_source"] == 10)
            check("own ungrounded excludes every asked train", r["own_ungrounded_trains"]["n"] == 23,
                  r["own_ungrounded_trains"])
            m = r["matched_pairs"]
            check("k=3 grounded not matched to a train dead before step 3 (24 grounded, 23 pairs, 1 unmatched)",
                  m.get("n_grounded_with_steps") == 24 and m.get("n_pairs") == 23 and m.get("n_unmatched") == 1, m)
            check("prior-length k recorded (k=1 x23 matched)", m.get("k_distribution") == {"1": 23}, m.get("k_distribution"))
            check("topic match pairs gi with ui", m.get("topic_sim_mean", 0) > 0.3, m.get("topic_sim_mean"))
            check("earned primary: grounded 1.0 vs matched 0.0",
                  m.get("earned_rate_grounded") == 1.0 and m.get("earned_rate_matched") == 0.0, m)
            check("verdict on earned length = grounded_develops_more", r["verdict"] == "grounded_develops_more", r["verdict"])
            check("verdict_metric earned_rate", r.get("verdict_metric") == "earned_rate")
            check("all-sources parity read present", r["matched_pairs_all_sources"].get("n_pairs", 0) >= 22)

            small = build_stores(tmp / "small", n_own=5)
            for k, v in small.items():
                setattr(ev, k, v)
            r2 = ev.r2_signature()
            check("below R2_MIN_N pairs -> insufficient_data", r2["verdict"] == "insufficient_data", r2["verdict"])
            r3 = ev.r2_signature(matched=False)
            check("matched=False skips the pair read", r3["matched_pairs"] == {"skipped": True})

            # ---- stats helpers agree with scipy values quoted in F-3327 ----
            check("sign p(15,4)=0.0192 (F-3327 pre-boot)", ev._sign_p(15, 4) == 0.0192, ev._sign_p(15, 4))
            check("sign p(3,4)=1.0", ev._sign_p(3, 4) == 1.0)
            check("sign p(0,0)=None", ev._sign_p(0, 0) is None)
        finally:
            for k, v in orig.items():
                setattr(ev, k, v)
            memory_edges.log_co_recall, memory_service.stash_usage = orig_lcr, orig_su
    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAIL'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
