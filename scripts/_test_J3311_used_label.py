"""_test_J3311_used_label.py -- proving test for scripts/analyze_J3311_used_label.py (J-3311).
Run from the worktree: python scripts/_test_J3311_used_label.py
Synthetic data in a tempdir, stub embedder (hashed bag of words), stub judge call. No live data, no model, no hub.
"""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ["J3311_DATA"] = str(Path(tempfile.gettempdir()) / "j3311_unused_placeholder")
import analyze_J3311_used_label as A  # noqa: E402

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


check("script lives in this tree", Path(A.__file__).resolve().parent.parent == ROOT)
check("default OUT is under this tree", str(A.OUT).startswith(str(ROOT)))


def fake_embed(texts):
    out = []
    for t in texts:
        v = np.zeros(384, np.float32)
        for w in A.words(t):
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            v[h % 384] += 1.0
        out.append(v)
    return np.vstack(out)


# unit helpers
check("grams4 four words", A.grams4("a b c d e") == {("a", "b", "c", "d"), ("b", "c", "d", "e")})
check("sentences drops short", A.sentences("Hi there. This is a longer sentence here.") == ["This is a longer sentence here."])
check("wilson bounds", A.wilson(5, 50)[0] < 0.1 < A.wilson(5, 50)[1])
check("auc perfect", A.auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0)
check("auc ties half", abs(A.auc([1, 1, 1, 1], [0, 1, 0, 1]) - 0.5) < 1e-9)
check("auc one class None", A.auc([1, 2], [1, 1]) is None)

with tempfile.TemporaryDirectory() as td:
    data = Path(td) / "data"
    (data / "training").mkdir(parents=True)
    (data / "memory").mkdir()
    out = Path(td) / "out"
    db = sqlite3.connect(data / "memory" / "nascence.db")
    db.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, embedding BLOB)")
    texts = {
        "f_used": "The lighthouse keeper watched the grey water for three long nights without sleeping.",
        "f_semantic": "A keeper of the lighthouse stared at gray water, awake for three nights running.",
        "f_other": "Quarterly spreadsheets require careful reconciliation of every ledger column before filing.",
        "f_other2": "Mountain goats climb steep granite ledges during the early autumn migration season.",
        "f_other3": "Baking sourdough needs a patient starter fed daily with flour and warm water.",
        "f_other4": "Tidal harmonics predict the height of the sea at every harbour along this coast.",
    }
    for fid, t in texts.items():
        db.execute("INSERT INTO memory_fragments VALUES (?,?,?,?)", (fid, t, "lived", b"x"))
    for i in range(30):  # unserved pool for null B
        db.execute("INSERT INTO memory_fragments VALUES (?,?,?,?)",
                   (f"p{i}", f"Unserved filler memory number {i} about unrelated gardens and fences and weather.", "lived", b"x"))
    db.commit()
    db.close()
    served, voice, perc = [], [], []
    for c in range(8):
        cid = f"c{c}"
        frs = [{"fragment_id": k, "origin": "lived", "layer": "episodic", "abstraction_level": 0, "relevance": 0.5}
               for k in texts]
        served.append({"ts": 1.0 + c, "cycle_id": cid, "input_type": "internal" if c % 2 else "human", "fragments": frs})
        final = ("The lighthouse keeper watched the grey water for three long nights without sleeping. "
                 f"Meanwhile something else entirely number {c} happens in the harbour town tonight.")
        voice.append({"cycle_id": cid, "output": {"final": final}})
        perc.append({"cycle_id": cid, "raw_input": "tell me about the lighthouse", "output": {"summary": "asks about lighthouse"}})
    served.append({"ts": 99.0, "cycle_id": "no_voice", "input_type": "internal", "fragments": []})
    for name, rows in (("recall_served_log.jsonl", served), ("training/voice.jsonl", voice), ("training/perception.jsonl", perc)):
        (data / name).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    emb = A.Embedder(fake_embed)
    units, meta = A.build_labels(emb=emb, data=data, out_dir=out, verbose=False)
    check("one row dropped for no voice", meta["dropped_rows_no_voice"] == 1)
    check("48 units", len(units) == 48)
    uu = {u["fragment_id"]: u for u in units if u["cycle_id"] == "c0"}
    check("verbatim fragment is u4 and ue", uu["f_used"]["u4"] and uu["f_used"]["ue"])
    check("unrelated fragment not u4, not ue", not uu["f_other"]["u4"] and not uu["f_other"]["ue"])
    check("semantic paraphrase: not u4", not uu["f_semantic"]["u4"])
    check("thresholds ordered", meta["null_a_thresholds"]["p95"] <= meta["null_a_thresholds"]["p99"] <= meta["null_a_thresholds"]["p999"])
    check("null B ran", meta["null_b_n"] > 0)
    # judge (stub): score 9 for the lighthouse fragments, else 1
    def stub(system, user):
        return "9" if "lighthouse" in user.split("REMEMBERED FRAGMENT:")[1].lower() else "1"
    n = A.run_judge("http://unused", "x", 30, call=stub, data=data, out_dir=out, tag="stub")
    check("judge stopped at max-units", n == 30)
    n2 = A.run_judge("http://unused", "x", 30, call=stub, data=data, out_dir=out, tag="stub")
    check("judge resume adds nothing", n2 == 30 and len((out / "judge_scores_stub.jsonl").read_text().splitlines()) == 30)
    A.run_judge("http://unused", "x", 48, call=stub, data=data, out_dir=out, tag="stub")
    def bstub(system, user, n_pred):
        import re as _re
        n = int(_re.search(r"fragments 1 to (\d+)", user).group(1))
        lines = [l for l in user.split(chr(10)) if l.startswith("[")]
        assert len(lines) == n
        return " ".join("9" if "lighthouse" in l.lower() else "1" for l in lines)
    nb = A.run_judge_batch("http://unused", "x", 5, call=bstub, data=data, out_dir=out, tag="bstub")
    check("batch judge scored 5 cycles", nb == 5 and len((out / "judge_scores_bstub.jsonl").read_text().splitlines()) == 30)
    A.run_judge_batch("http://unused", "x", 8, call=bstub, data=data, out_dir=out, tag="bstub")
    rep = A.build_report(out_dir=out)
    check("batch judge AUC", rep["judge"]["bstub"]["auc_ue"]["auc"] > 0.8 and rep["judge"]["bstub"]["errors"] == 0)
    check("report has overall", rep["overall"]["u4"]["n"] == 48)
    print(rep["judge"]["stub"]); check("judge AUC computed", rep["judge"]["stub"]["auc_ue"]["auc"] is not None and rep["judge"]["stub"]["auc_ue"]["auc"] > 0.8)
    check("ceiling present", "pilot_origin_mix_shift_per_cycle_at_2.25_slots" in rep["ceiling_ue"])
    check("results.json written under temp out", (out / "results.json").exists())
    check("live OUT untouched by the test", not (A.OUT / "judge_scores_stub.jsonl").exists())

print("ALL PASS" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
