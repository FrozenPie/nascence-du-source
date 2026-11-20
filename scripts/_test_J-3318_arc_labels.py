"""J-3318 test: the digest labels the frozen June arc and prints the live L4 arc count + last write
date; /arc prints the legacy note; app.js relabels Arc: -> Status: only for probation events.
Writes only under a temp dir; touches no live data."""
import sys, json, io, time, tempfile, contextlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: F401  (before lab_env)
import session_digest as sd

with tempfile.TemporaryDirectory() as td:
    d = Path(td); (d / "identity").mkdir()
    ts = time.mktime((2026, 6, 18, 12, 0, 0, 0, 0, -1))
    axiom = {"emergent_self_legacy": {"chosen_name": "X", "revision_count": 3, "self_narrative_arc": [{}] * 12,
                                       "history": [], "self_concept": "c"},
             "L4_narrative": {"arc_recent": ["a", "b"]}}
    (d / "identity" / "axiom.json").write_text(json.dumps(axiom), encoding="utf-8")
    rows = [{"ts": ts, "reason": "T4 self-authoring"},
            {"ts": ts + 9e6, "reason": "T4 probationary self SOLIDIFIED (x)"}]
    (d / "identity" / "vault_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    sd.DATA = d
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            sd.developmental_arc([], [])
        except Exception as e:  # later sections may need more data; the identity lines print first
            pass
    out = buf.getvalue()
    assert "12 arc chapters (legacy, frozen 2026-06-13)" in out, out
    assert "live arc (L4_narrative.arc_recent): 2 entries" in out, out
    assert "last arc write 2026-06-18" in out, out
    # no vault row -> honest message
    assert "no 'T4 self-authoring' vault write found" in sd._live_arc_line(axiom, [])
    assert "0 entries" in sd._live_arc_line({}, [])

assert "legacy June arc, frozen 2026-06-13" in (ROOT / "scripts" / "run_nascence.py").read_text(encoding="utf-8")
js = (ROOT / "hud" / "static" / "app.js").read_text(encoding="utf-8")
assert 'th.event ? "Status:" : "Arc:"' in js
print("J-3318 OK")
