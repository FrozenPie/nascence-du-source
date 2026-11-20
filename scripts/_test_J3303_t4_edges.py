"""Hermetic test for scripts/analysis_J3303_t4_edges.py: synthetic live tree in a temp dir, no live data."""
import hashlib, json, sqlite3, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: F401,E402  (core before lab_env, per the job rules)
assert Path(core.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
import analysis_J3303_t4_edges as A  # noqa: E402


def sha(t):
    return hashlib.sha1(t.encode()).hexdigest()[:12]


def build(tmp: Path):
    (tmp / "data/memory").mkdir(parents=True)
    (tmp / "data/logs").mkdir(parents=True)
    t0 = time.time() - 5 * 86400
    db = sqlite3.connect(tmp / "data/memory/nascence.db")
    db.execute("CREATE TABLE light_events (event_id TEXT PRIMARY KEY, timestamp REAL, cycle_id TEXT, raw_input TEXT,"
               " integrated_content TEXT, emotion_primary TEXT, embedding BLOB, source TEXT DEFAULT 'x')")
    db.execute("CREATE TABLE memory_edges (edge_id INTEGER PRIMARY KEY, src_kind TEXT, src_id TEXT, dst_kind TEXT,"
               " dst_id TEXT, edge_type TEXT, weight REAL, provenance TEXT, created REAL,"
               " UNIQUE(src_kind,src_id,dst_kind,dst_id,edge_type))")
    # 12 events; e2/e3 are the SAME sentence under two sources (the real corpus duplicates thoughts)
    for i in range(12):
        txt = "same sentence" if i in (2, 3) else f"sentence {i}"
        db.execute("INSERT INTO light_events VALUES (?,?,?,?,?,?,?,?)",
                   (f"e{i}", t0 + i * 600, "c", "(idle thought about: x)", txt, None, None, "integration" if i != 3 else "play"))
    full = "prediction_error:comprehension (felt 0.00 vs real 0.50)"
    cut = "a long unresolved label that the chain log cuts at forty chars and more"
    h1, h2 = sha(full), sha(cut)
    log = []
    ts = t0 + 7200
    rows = [(h1, "e0", .5), (h1, "e1", .4), (h1, "e2", .3), (h1, "e3", .3)]
    for k, (h, e, w) in enumerate(rows):
        db.execute("INSERT INTO memory_edges (src_kind,src_id,dst_kind,dst_id,edge_type,weight,provenance,created)"
                   " VALUES ('tension',?,'light_event',?,'t4_crossing_evidence',?,'has_movement=False',?)", (h, e, w, ts + k * 0.01))
    lt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts + 3))
    log.append(f"{lt},100 [x] [subconscious] T4 considered 3 fragment(s) — no change: weighed the crossings — no genuine movement, still circling (tension: {full!r})")
    ts2 = ts + 3600
    for k, e in enumerate(["e5", "e6"]):
        db.execute("INSERT INTO memory_edges (src_kind,src_id,dst_kind,dst_id,edge_type,weight,provenance,created)"
                   " VALUES ('tension',?,'light_event',?,'t4_crossing_evidence',.5,'has_movement=True',?)", (h2, e, ts2 + k * 0.01))
    lt2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts2 + 20))
    log.append(f"{lt2},100 [x] [subconscious] T4 CHAIN — tension={cut[:40]!r} → evidence ✓ → delta='d' → authored")
    db.commit()
    db.close()
    (tmp / "data/nascence.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    (tmp / "data/logs/provisional_identity.jsonl").write_text(
        json.dumps({"ts": ts2 + 60, "event": "open", "theme": "some other theme", "self_image": "I am x"}) + "\n", encoding="utf-8")
    (tmp / "data/logs/t4_emissary_judge.jsonl").write_text(
        json.dumps({"ts": ts2 + 30, "emissary_warranted": 0.7}) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    build(tmp)
    out = tmp / "out"
    sys.argv = ["x", "--live", str(tmp), "--out", str(out)]
    assert A.main() == 0
    s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert s["edges"] == 6 and s["tensions_hashes"] == 2, s["edges"]
    assert s["hash_resolution"]["exact"] == 1 and s["hash_resolution"]["aligned"] == 1, s["hash_resolution"]
    assert s["hash_resolution"]["unresolved"] == 0
    assert s["provenance_counts"] == {"has_movement=False": 4, "has_movement=True": 2}
    # e2 and e3 are one sentence: 6 rows, 5 distinct sentences
    assert s["duplication"]["distinct_sentences"] == 5, s["duplication"]
    assert s["reach"]["dst_resolve"] == {"present": 6}
    assert s["reach"]["share_rank_le_300_pct"] == 100.0
    assert s["estate_link_test"]["probation_opens"] == 1
    assert s["estate_link_test"]["opens_whose_own_hearing_wrote_rows"] == 1
    assert s["probation_since_edges"]["judged_ge_0_6"] == 1
    assert (out / "per_family.json").exists() and (out / "per_hash.json").exists()
print("OK _test_J3303_t4_edges")
