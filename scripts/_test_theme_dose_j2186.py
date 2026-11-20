"""Hermetic test for J-2322 (measurement_to_action arm 5 shadow build; design J-2186, F-3012).

Run from the worktree root:  python scripts/_test_theme_dose_j2186.py
- imports core FIRST and asserts core.__file__ is in this tree (lab_env sys.path hijack, feedback_jobrun_live_store_leaks)
- window() cases; _build_prompt with the flag None renders themes_text byte-identical to the pre-change code;
  shadow row lands only in the isolated lab path; sha256 canary on data/curiosity_log.jsonl + data/frontier.json.
"""
from __future__ import annotations
import hashlib
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
sys.path.insert(1, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env  # noqa: E402

from core import theme_dose as td, profile  # noqa: E402
from nodes import curiosity_node as cn  # noqa: E402

ok_all = True


def check(name, cond):
    global ok_all
    ok_all &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


CANARIES = [ROOT / "data" / "curiosity_log.jsonl", ROOT / "data" / "frontier.json"]
_LIVE = Path(r"C:\Nascence\data")
if _LIVE.resolve() != (ROOT / "data").resolve():   # running from a worktree: also guard the live tree
    CANARIES += [_LIVE / "curiosity_log.jsonl", _LIVE / "frontier.json",
                 _LIVE / "logs" / "curiosity_theme_dose_shadow.jsonl"]
before = {str(p): sha(p) for p in CANARIES}

print("[1] window()")
T = [f"t{i}" for i in range(14)]
S = ["internal" if i % 2 == 0 else "human" for i in range(14)]
check("None == themes[-10:]", td.window(T, S, None) == T[-10:])
check("None, fewer than n", td.window(T[:3], S[:3], None) == T[:3])
check("None, empty", td.window([], [], None) == [])
w1 = td.window(T, S, 1)
check("dose 1: all non-self kept, only newest self", w1 == ["t1", "t3", "t5", "t7", "t9", "t11", "t12", "t13"])
w0 = td.window(T, S, 0)
check("dose 0: no self lines", w0 == ["t1", "t3", "t5", "t7", "t9", "t11", "t13"])
mixed = ["a", "b", "c", "d", "e"]
msrc = ["internal", "internal", "timer", "internal", "human"]
check("mixed order preserved (dose 1)", td.window(mixed, msrc, 1) == ["c", "d", "e"])
check("dose 2", td.window(mixed, msrc, 2) == ["b", "c", "d", "e"])
check("untagged theme never dosed", td.window(["x", "y"], [], 0) == ["x", "y"])
allself = [f"s{i}" for i in range(20)]
check("all self, dose 1 -> newest only", td.window(allself, ["internal"] * 20, 1) == ["s19"])
check("n respected", len(td.window(T, ["human"] * 14, 1)) == 10)

print("[2] _build_prompt with flag None is byte-identical to the pre-change themes_text")
_FLAG_LIVE = td.SELF_THEME_DOSE   # D-0485: the shipped default is now 1; section 2 tests the None (revert) path
td.SELF_THEME_DOSE = None


def old_themes_text(themes):   # pre-J-2322 expression; J-2846 swapped the [:70] slice for the word-boundary trim
    return ("\n".join(f"  - {cn._trim_words(t, 70)}" for t in themes[-10:]) if themes else "  (no recent themes yet)")


with lab_env.isolate(also=[(td, ["_LOG"])], db="empty") as lab:
    log = td._LOG
    check("shadow path redirected into lab dir", Path(log).resolve().is_relative_to(Path(lab).resolve()))
    node = cn.CuriosityNode()
    node._select_study_material = lambda k=3: []   # hermetic: no store read
    node._select_seeds = lambda: ["seed one"]
    state = types.SimpleNamespace(spirit_name="Du")
    themes = [f"theme number {i} " + "x" * (60 + i) for i in range(14)]
    srcs = ["internal", "internal", "human", "internal", "timer", "internal", "internal",
            "internal", "human", "internal", "internal", "internal", "internal", "internal"]
    for t, s in zip(themes, srcs):
        node.add_theme(t, source=s)
    check("provenance list parallel", node._recent_theme_src == srcs)
    p = node._build_prompt(state)
    expect = f"Recent themes:\n{old_themes_text(node._recent_themes)}\n"
    check("themes block byte-identical (flag None)", expect in p)
    node2 = cn.CuriosityNode(); node2._select_study_material = lambda k=3: []; node2._select_seeds = lambda: []
    p2 = node2._build_prompt(state)
    check("empty window byte-identical", f"Recent themes:\n{old_themes_text([])}\n" in p2)
    node3 = cn.CuriosityNode(); node3._select_study_material = lambda k=3: []; node3._select_seeds = lambda: []
    node3._recent_themes = ["direct mutation, untagged"]   # what curiosity_twig_test does
    check("direct _recent_themes mutation still renders", "  - direct mutation, untagged" in node3._build_prompt(state))
    for i in range(35):
        node3.add_theme(f"z{i}")
    check("trim keeps lists aligned at 30", len(node3._recent_themes) == 30 == len(node3._recent_theme_src))
    node._last_curiosity_id = "abc123"
    node._build_prompt(state)
    rows = [json.loads(l) for l in Path(log).read_text(encoding="utf-8").splitlines() if l.strip()]
    check("one shadow row per build (4 builds)", len(rows) == 4)
    r = rows[0]
    print("     row0:", json.dumps({k: r[k] for k in ("flag", "n_live", "n_self_live", "n_self_would", "dose", "line", "stop")}))
    check("row keys", set(r) == {"ts", "stop", "line", "dose", "flag", "n_live", "n_self_live", "n_self_would",
                                 "live_window", "would_window", "seeds", "study_subjects", "curiosity_id"})
    check("flag None, live = last 10", r["flag"] is None and r["live_window"] == [t[:70] for t in themes[-10:]])
    check("n_self_live = 8 of last 10", r["n_self_live"] == 8)
    check("would = dose-1 window", r["would_window"] == [t[:70] for t in td.window(themes, srcs, 1)])
    check("n_self_would = 1", r["n_self_would"] == 1)
    check("seeds logged", r["seeds"] == ["seed one"])
    check("curiosity_id = previous row id", rows[-1]["curiosity_id"] == "abc123" and r["curiosity_id"] is None)

td.SELF_THEME_DOSE = _FLAG_LIVE
print("[3] non-live write to the real data/ path is refused, and _build_prompt swallows it")
real = ROOT / "data" / "logs" / "curiosity_theme_dose_shadow.jsonl"
real_before = sha(real)
check("theme_dose._LOG restored to real path", Path(td._LOG).resolve() == real.resolve())
try:
    td.shadow(["a"], ["internal"], ["a"], ["a"])
    check("shadow() raised NonLiveWriteError", False)
except profile.NonLiveWriteError:
    check("shadow() raised NonLiveWriteError", True)
n4 = cn.CuriosityNode(); n4._select_study_material = lambda k=3: []; n4._select_seeds = lambda: []
n4.add_theme("q", source="internal")
check("_build_prompt fail-open in non-live process", "  - q" in n4._build_prompt(types.SimpleNamespace(spirit_name="Du")))
check("real shadow path untouched", sha(real) == real_before)

after = {str(p): sha(p) for p in CANARIES}
for p in CANARIES:
    check(f"canary unchanged: {p.name}", before[str(p)] == after[str(p)])

print("ALL PASS" if ok_all else "FAILURES ABOVE")
sys.exit(0 if ok_all else 1)
