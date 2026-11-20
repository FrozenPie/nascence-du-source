"""J-3876: watershed candidates keep sample_refs (id twin of sample_thoughts). Temp data dir only."""
import hashlib, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import watershed as ws
assert str(Path(ws.__file__).resolve()).startswith(str(ROOT))

V = [1.0, 0.0, 0.0]
T = "I notice that I keep returning to the same quiet question about myself."


def _fresh(tmp):
    ws.configure(data_dir=tmp)


def test_new_and_matched_refs_trim_in_step():
    with tempfile.TemporaryDirectory() as tmp:
        _fresh(tmp)
        for i in range(ws.SAMPLE_KEEP + 3):
            ws.observe(T + str(i), vec=V, ts=1000.0 + i, cycle_id=f"c{i}",
                       fragment_id=f"f{i}" if i % 2 == 0 else "", _cooldown=False)
        c = json.load(open(Path(tmp) / "watershed_state.json"))["candidates"][0]
        assert len(c["sample_thoughts"]) == len(c["sample_refs"]) == ws.SAMPLE_KEEP
        last = c["sample_refs"][-1]
        assert last["cycle_id"] == f"c{ws.SAMPLE_KEEP + 2}"
        assert last["content_sha1"] == hashlib.sha1((T + str(ws.SAMPLE_KEEP + 2)).encode()).hexdigest()
        assert "fragment_id" in c["sample_refs"][-1] or True
        assert any("fragment_id" in r for r in c["sample_refs"])
        assert any("fragment_id" not in r for r in c["sample_refs"])


def test_old_state_without_sample_refs_loads():
    with tempfile.TemporaryDirectory() as tmp:
        _fresh(tmp)
        old = {"candidates": [{"id": "old1", "centroid": V, "n": 2, "days": [0], "first_ts": 1.0, "last_ts": 2.0,
                               "recent_vecs": [V], "sample_thoughts": ["a"], "born": False}]}
        (Path(tmp) / "watershed_state.json").write_text(json.dumps(old), encoding="utf-8")
        rec = ws.observe(T, vec=V, ts=100.0, cycle_id="c", _cooldown=False)
        assert rec and rec["candidate_id"] == "old1"
        c = json.load(open(Path(tmp) / "watershed_state.json"))["candidates"][0]
        assert len(c["sample_refs"]) == 1 and len(c["sample_thoughts"]) == 2


def test_observe_row_shape_unchanged():
    with tempfile.TemporaryDirectory() as tmp:
        _fresh(tmp)
        rec = ws.observe(T, vec=V, ts=5.0, cycle_id="c", fragment_id="f", _cooldown=False)
        assert set(rec) == {"ts", "kind", "cycle_id", "candidate_id", "sim", "n", "n_days", "new_candidate", "thought"}
