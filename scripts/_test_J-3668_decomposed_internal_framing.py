"""Proof for J-3668: decomposed_critic stimulus framing is flag-gated; default byte-identical. Hermetic (temp paths, fake model)."""
import asyncio, sys, tempfile, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa
from core import decomposed_critic as dc, schema
assert Path(dc.__file__).resolve().parent.parent == ROOT
tmp = Path(tempfile.mkdtemp(prefix="J3668_"))
dc._ALONGSIDE = tmp / "a.jsonl"; dc._SHADOW = tmp / "s.jsonl"
import core.model_client as mc
seen = []
async def fake(urls, system, user, **kw):
    seen.append(user); return {}
mc.call_node_json = fake
fails = []
def run(it, flag):
    schema.DECOMPOSED_CRITIC_INTERNAL_FRAMING_ON = flag
    seen.clear()
    rec = asyncio.run(dc.shadow_alongside("a draft here", "why?", legacy_approved=True, input_type=it))
    return seen[0], rec
def chk(n, c):
    print(("ok   " if c else "FAIL ") + n)
    if not c: fails.append(n)
u, r = run("human", False); chk("human off", u.startswith('The human said:') and r["input_type"] == "human")
u, r = run("internal", False); chk("internal off unchanged", u.startswith('The human said:') and r["input_type"] == "internal")
u, r = run("internal", True); chk("internal on reframed", u.startswith('The entity asked itself:'))
u, r = run("human", True); chk("human on unchanged", u.startswith('The human said:'))
sys.exit(1 if fails else 0)
