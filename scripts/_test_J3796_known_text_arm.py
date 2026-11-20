"""J-3796 test: flag-gated known_text shown/withheld arm. Stub known_text, temp log, no live data, no model calls."""
import hashlib, json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (core before lab_env)
from core import procedures as P

LINE = "\n\nThings you have done before and that held (your own hands, your own record): door, fire, tea."
state = {"line": LINE}
P.known_text = lambda location="": state["line"]
with tempfile.TemporaryDirectory() as td:
    log = Path(td) / "known_text_arm.jsonl"
    P._KT_ARM_LOG = log
    P.profile.guard_path = lambda p: p
    os.environ.pop("NASCENCE_KNOWN_TEXT_ARM", None)
    # flag off: identity, no write
    for i in range(20):
        assert P.known_text_gated("study", f"cyc{i}") == LINE
    assert not log.exists()
    os.environ["NASCENCE_KNOWN_TEXT_ARM"] = "1"
    n = 1000; shown = 0
    for i in range(n):
        cid = f"{i:08x}-0000-4000-8000-{i:012x}"
        out = P.known_text_gated("study", cid)
        exp = "shown" if int(hashlib.sha1(("kt-arm:" + cid).encode()).hexdigest(), 16) % 2 else "withheld"
        assert out == (LINE if exp == "shown" else ""), cid
        assert P.known_text_gated("study", cid) == out   # determinism
        shown += out == LINE
    assert abs(shown / n - 0.5) <= 0.05, shown
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2 * n
    r = rows[0]
    assert set(r) == {"ts", "cycle", "arm", "would_name", "where"} and r["would_name"] == ["door", "fire", "tea"] and len(r["cycle"]) <= 24
    # not eligible (empty line): no write, returns ""
    before = log.stat().st_size; state["line"] = ""
    assert P.known_text_gated("study", "zzz") == "" and log.stat().st_size == before
    # log failure is fail-open and the coin still decides
    state["line"] = LINE
    P._KT_ARM_LOG = Path(td) / "a_file"; (Path(td) / "a_file").write_text("x"); P._KT_ARM_LOG = Path(td) / "a_file" / "sub.jsonl"
    cid = "q1"; assert P.known_text_gated("study", cid) in (LINE, "")
print("OK J-3796 known_text arm")
