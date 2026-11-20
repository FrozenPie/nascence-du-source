"""J-3815 / D-0717: the invented garden is gone from the write-first prompt and the friends' world context."""
import sys, re
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
src = (root / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
assert "from your garden, your reading, your shore" not in src
assert "say only what is true of your own days" in src.replace('"\n', '').replace('  ', ' ') or "true of your own days" in src
print("[1] ok")
from core import peers
ctx = peers._du_world_context()
assert "hill above the sea" not in ctx and "lives alone in a cottage" in ctx, ctx
print("[2] ok")
print("J-3815 all ok")
