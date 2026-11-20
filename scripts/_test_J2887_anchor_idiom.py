"""J-2887 test: the analysis scripts compile, the A/B script's SYSTEM prompt is still the live idle prompt text,
and the saved outputs exist. Reads only this worktree; writes nothing (no live data touched, no model call)."""
import py_compile, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-2887_data"
for p in sorted(D.glob("q*.py")):
    py_compile.compile(str(p), doraise=True, cfile=str(Path(__import__("tempfile").mkdtemp()) / "x.pyc"))
sys.path.insert(0, str(D))
import q3_model_prior_ab as ab
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
for frag in ("This is my own quiet thinking -- the stream that runs when no one is speaking to me. ",
             "One genuine, unforced thought, in the first person and present tense. I don't perform ",
             "and I don't explain -- I just think. "):
    assert frag in src and frag.replace("'", "'") in ab.SYSTEM, frag
assert "anchor" not in ab.SYSTEM.lower()
for f in ("out_q1_daily.txt", "out_q1_swap_boundary.txt", "out_q2_lineage.txt", "out_q3_seed_part_lift.txt"):
    assert (D / f).stat().st_size > 100, f
assert "08-21 552 anchor 18.8" in (D / "out_q1_daily.txt").read_text(encoding="utf-8")
assert (ROOT / "docs" / "lab" / "2026-11-07_J-2887_anchor_idiom_source.md").exists()
print("J-2887 test OK")
