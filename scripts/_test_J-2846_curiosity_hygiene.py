"""Hermetic test for J-2846 (F-3506): Curiosity prompt hygiene.

Run from the worktree root:  python scripts/_test_J-2846_curiosity_hygiene.py
Asserts: word-boundary trim (themes 70, study snippets 220), raw prediction_error seed labels reworded at the seed
selector while the real pick / anti-relock memory keep the raw label, the stale schema + comment text is fixed.
Writes only under a temp dir; no model call; no live data touched (the module's state/log paths are pointed at the temp dir).
"""
from __future__ import annotations
import json
import random
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
from nodes import curiosity_node as cn  # noqa: E402
assert Path(cn.__file__).resolve().is_relative_to(ROOT), cn.__file__

ok_all = True


def check(name, cond):
    global ok_all
    ok_all &= bool(cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)


tmp = Path(tempfile.mkdtemp(prefix="J-2846_"))

print("[1] _trim_words")
tw = cn._trim_words
check("short text unchanged", tw("a short theme", 70) == "a short theme")
check("exactly limit unchanged", tw("x" * 70, 70) == "x" * 70)
t = "what remains of a garden when the person who kept it is gone, and who decides in the context of the unresolved"
out = tw(t, 70)
check("cut on a word boundary (no partial word)", t.startswith(out) and (t[len(out)] == " ") and len(out) <= 70)
check("the mid-word case from F-3506 no longer ends in a fragment", not out.endswith("unr") and not out.endswith("the unre"))
check("boundary exactly at limit keeps the word", tw("abc def ghi", 7) == "abc def")
check("trailing comma stripped at the cut", tw("one two, three four", 9) == "one two")
check("unbroken run is hard-cut", tw("x" * 100, 70) == "x" * 70)
cjk = "\u6e21" * 100
check("unspaced CJK hard-cut at limit", tw(cjk, 70) == "\u6e21" * 70)
check("never longer than the limit", all(len(tw("word " * 80, n)) <= n for n in (5, 33, 70, 220)))

print("[2] _seed_wording")
sw = cn._seed_wording
w = sw("prediction_error:factual_recall (felt 0.90 vs real 0.50)")
check("domain worded, underscores gone", "factual recall" in w and "_" not in w)
check("no numbers, no 'felt', no 'vs', no 'prediction_error'",
      not any(c.isdigit() for c in w) and "felt" not in w and " vs " not in w and "prediction_error" not in w)
check("no direction or advice in the wording", not any(x in w.lower() for x in ("over", "under", "should", "better", "worse", "higher", "lower")))
check("other domains / numeric forms",
      "music" in sw("prediction_error:music (felt 0.77 vs real 0.00)") and "comprehension" in sw("prediction_error:comprehension (felt 0.10 vs real 0.85)"))
for plain in ("unresolved: Sunday School loyalty", "theoretical_defence", "unresolved: \u6e21 in Japanese", ""):
    check(f"ordinary label untouched: {plain!r}", sw(plain) == plain)

print("[3] _select_seeds rewords the offered menu only; the real pick keeps the raw label")
sc = tmp / "subconscious_state.json"
RAW = "prediction_error:factual_recall (felt 0.90 vs real 0.50)"
sc.write_text(json.dumps({"tensions": [
    {"id": "t1", "label": RAW, "count": 5, "last_ts": 1.0},
    {"id": "t2", "label": "unresolved: identity", "count": 4, "last_ts": 1.0},
    {"id": "t3", "label": "unresolved: restlessness", "count": 3, "last_ts": 1.0}]}), encoding="utf-8")
cn._SUBCONSCIOUS_STATE_PATH = sc
from core import curiosity_habituation as chab  # noqa: E402
chab.observe_and_log = lambda *a, **k: None   # the shadow log writes to the live data/ path: stub it
random.seed(7)
node = cn.CuriosityNode.__new__(cn.CuriosityNode)
node._recent_seeds = []
menu = node._select_seeds(3)
check("all three offered", len(menu) == 3)
check("no raw engineering label in the offered menu", not any("prediction_error" in m or "felt" in m for m in menu))
check("worded line is in the menu", any("factual recall" in m for m in menu))
check("anti-relock memory holds the RAW label", RAW in node._recent_seeds and not any("how I expected" in s for s in node._recent_seeds))

print("[4] _build_prompt end to end (stubbed material, temp paths)")
from core import theme_dose as td  # noqa: E402
td.shadow = lambda *a, **k: {}      # the shadow row targets the live data/ path: stub it
n2 = cn.CuriosityNode()
long_snip = ("the lichen colonised the north face of the wall slowly over several decades and nobody noticed the change until "
             "a surveyor measured the stone against an old photograph taken from the lane")
n2._select_study_material = lambda k=3: [{"subject": "S", "snippet": cn._trim_words(long_snip, 220)}]
n2._select_seeds = lambda: [sw(RAW)]
for i in range(3):
    n2.add_theme("own theme number %d about the thing he wondered over in the evening by the window" % i, source="human")
p = n2._build_prompt(types.SimpleNamespace(spirit_name="Du"))
lines = [l for l in p.splitlines() if l.startswith("  - ")]
check("prompt has theme lines", len(lines) >= 3)
check("every theme line ends on a whole word of its source", all(
    any(("own theme number %d about the thing he wondered over in the evening by the window" % i).startswith(l[4:]) and
        (("own theme number %d about the thing he wondered over in the evening by the window" % i)[len(l) - 4:len(l) - 3] in (" ", ""))
        for i in range(3)) for l in lines[:3]))
check("no raw label in the built prompt", "prediction_error" not in p and "felt 0" not in p)
# a real study snippet longer than 220 is trimmed on a boundary by the selector itself
fake_store = types.ModuleType("core.memory.store")
body = " ".join(["lichen"] * 5 + ["wall%d" % i for i in range(60)])
fake_store.recent_world_material = lambda limit=9: [{"content": "[From 'A Book'] " + body}]
real_store = sys.modules.get("core.memory.store")
sys.modules["core.memory.store"] = fake_store
try:
    n3 = cn.CuriosityNode()
    got = n3._select_study_material(1)
finally:
    if real_store is not None:
        sys.modules["core.memory.store"] = real_store
    else:
        del sys.modules["core.memory.store"]
check("study snippet within 220 and whole-word", got and len(got[0]["snippet"]) <= 220 and " ".join(body.split()).startswith(got[0]["snippet"])
      and " ".join(body.split())[len(got[0]["snippet"])] == " ")

print("[5] stale text fixed")
schema_src = (ROOT / "core" / "schema.py").read_text(encoding="utf-8")
check('schema no longer says "every_120s" for curiosity', '"curiosity":     {"lane": "background", "fires": "every_120s"}' not in schema_src
      and '"fires": "on_climate_ignition"' in schema_src)
from core.schema import NODE_REGISTRY  # noqa: E402
check("NODE_REGISTRY curiosity fires value", NODE_REGISTRY["curiosity"]["fires"] == "on_climate_ignition")
node_src = (ROOT / "nodes" / "curiosity_node.py").read_text(encoding="utf-8")
check("log-path comment names the other readers", all(m in node_src for m in ("core/grounding_injection.py", "core/world_displacement.py", "core/theme_dose.py")))
check("old 'read ONLY by scripts/session_digest.py' claim gone", "read ONLY by scripts/session_digest.py \u2014" not in node_src)

print("ALL PASS" if ok_all else "FAILURES ABOVE")
sys.exit(0 if ok_all else 1)
