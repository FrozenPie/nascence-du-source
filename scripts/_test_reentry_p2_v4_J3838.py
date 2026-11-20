"""Regression test for J-3838 (D-0593): within_cycle_reentry Phase 2 v4 for commitment-formation (SHADOW ONLY): quote
stripping, one pass, control arm as its own row type, neutral system line, memory-first retrieval, no hot-lane spill.
Offline: fake revise/embed, no LLM, no hub. Writes only under lab_env.isolate(). Run from a worktree. Exit 0 = pass."""
import asyncio, pathlib, sys, types
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                    # BEFORE lab_env (F-2423)
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
from core import reentry, reentry_p2
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)
KC, KS = reentry_p2.KIND_COMMIT, reentry_p2.KIND_SCENE
d = "I resolve to write about how the uncertainty shapes the ink on my page."

check("version routing: commit v4, scene v2", reentry_p2.prompt_version(KC) == 4 and reentry_p2.prompt_version(KS) == 2)
check("strip_quotes plain/curly/nested/unbalanced",
      reentry_p2.strip_quotes('"abc def"') == "abc def" and reentry_p2.strip_quotes("“abc”") == "abc"
      and reentry_p2.strip_quotes('"\'x y\'"') == "x y" and reentry_p2.strip_quotes('"abc') == '"abc')
cp = reentry_p2.build_control_prompt(d)
check("control prompt has the draft, a length budget, and NO context/ingredient wording",
      d in cp and "about" in cp and "context" not in cp.lower() and "ingredient" not in cp.lower())
check("system line is neutral (no voice cue)", "voice" not in reentry_p2.SYSTEM_LINE.lower())

def embed(text):
    v = [0.0] * 64
    for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split():
        v[hash(w) % 64] += 1.0
    nn = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / nn for x in v]
SEEN = []
async def revise(prompt, max_tokens=999):
    SEEN.append(prompt)
    return '"I resolve to write about how the uncertainty shapes the ink, now that the ink pot cracked in the cold."'
ING = ["The ink pot cracked in the cold and the nib dried on the desk overnight.",
       "A second wholly different fragment about moss and river stones in spring rain."]
with lab_env.isolate(db="empty", also=[(reentry_p2, ["_LOG", "_STATE"]), (reentry, ["_LOG", "_STATE"])]):
    rc = asyncio.run(reentry_p2.settle_shadow_p2(d, KC, revise=revise, retrieve=lambda q: ING, embed=embed,
                                                 basin=None, level=0.9))
    check("high arousal (budget 2) is capped at ONE pass for v4", rc and rc.get("passes") == 1 and len(SEEN) == 2)
    check("settled text has the echoed quotes stripped", rc and not rc["settled"].startswith('"') and not rc["settled"].endswith('"'))
    check("ingredient pass saw the ingredient, control pass did not",
          ING[0][:30] in SEEN[0] and ING[0][:30] not in SEEN[1] and "context" not in SEEN[1].lower())
    rows = [__import__("json").loads(l) for l in open(reentry_p2._LOG, encoding="utf-8")]
    ctl = [r for r in rows if r.get("row_type") == "control"]
    check("exactly one control row, own row type, version 4, no 'passes' key",
          len(ctl) == 1 and ctl[0].get("prompt_version") == 4 and "passes" not in ctl[0] and "overall_delta" in ctl[0])
    st = reentry_p2.status()[KC]
    check("status counts 1 settle (control not counted) and reports a control block",
          st["settles"] == 1 and st.get("control", {}).get("rows") == 1)
    SEEN.clear()
    rs = asyncio.run(reentry_p2.settle_shadow_p2(d, KS, revise=revise, retrieve=lambda q: ING, embed=embed,
                                                 basin=None, level=0.9))
    check("scene-binding unchanged: v2, up to 2 passes, no control arm", rs and rs.get("prompt_version") == 2
          and rs.get("passes") == 2 and not any(r.get("row_type") == "control" and r.get("kind") == KS for r in
          [__import__("json").loads(l) for l in open(reentry_p2._LOG, encoding="utf-8")]))

# default primitives: no hot spill, memory first
import core.schema as sch
calls = []
async def fake_call_node(url, system, prompt, **kw):
    calls.append((url, system)); raise RuntimeError("down")
import core.model_client as mc
orig = mc.call_node
mc.call_node = fake_call_node
try:
    rev, ret, emb = reentry_p2._default_primitives(topic="t", kind=KC)
    try:
        asyncio.run(rev("p"))
        check("failure raises", False)
    except Exception:
        check("failure raises (settle will skip)", True)
    hot = set(sch.SERVE_CHAINS["hot"])
    check("no call reached a hot-lane URL; neutral system line used",
          calls and not any(u in hot for u, _ in calls) and all(sy == reentry_p2.SYSTEM_LINE for _, sy in calls))
finally:
    mc.call_node = orig
print("FAIL" if FAILS else "PASS", f"({len(FAILS)} failures)")
sys.exit(1 if FAILS else 0)
