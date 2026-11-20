"""Hermetic test for J-3286 / D-0662: origin 'research' (a looked-up page) maps to SourceType.EXTERNAL_REFERENCE
(grounded, strength 3, below MEMORY_RECALL and above PARAMETRIC_LIBRARY) and a world picture whose strongest ground is
such a page cannot grade past THINK unless a tier-1/3/4 witness lifts it. No DB, no files: pure functions and fake states.
`import core` comes first and its path is asserted to be this worktree.
Run: python scripts/_test_external_reference_J3286.py   (exit 0 = all pass)"""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                              # noqa: E402
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import source_model as sm                      # noqa: E402
from core.source_model import SourceType as S, Verification as V   # noqa: E402
from core.epistemic_state import ProvenanceLedger as L, ModelProvenance as MP   # noqa: E402

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

print("[1] the taxonomy")
check("research -> EXTERNAL_REFERENCE", sm.source_of_origin("research") is S.EXTERNAL_REFERENCE)
check("case/space tolerant", sm.source_of_origin(" Research ") is S.EXTERNAL_REFERENCE)
check("reading/study untouched (still the MEMORY_RECALL default)",
      sm.source_of_origin("reading") is S.MEMORY_RECALL and sm.source_of_origin("study") is S.MEMORY_RECALL)
check("lived/parametric_library untouched",
      sm.source_of_origin("lived") is S.MEMORY_RECALL and sm.source_of_origin("parametric_library") is S.PARAMETRIC_LIBRARY)
check("strength 3, between memory (4) and the Scholar (2)",
      sm.strength(S.EXTERNAL_REFERENCE) == 3 and sm.strength(S.MEMORY_RECALL) > 3 > sm.strength(S.PARAMETRIC_LIBRARY))
check("grounded, not injected", sm.is_grounded(S.EXTERNAL_REFERENCE) and not sm.is_injected(S.EXTERNAL_REFERENCE))
check("memory beats a page; a page beats the Scholar",
      sm.strongest([S.EXTERNAL_REFERENCE, S.MEMORY_RECALL]) is S.MEMORY_RECALL
      and sm.strongest([S.PARAMETRIC_LIBRARY, S.EXTERNAL_REFERENCE]) is S.EXTERNAL_REFERENCE)
# (HUMAN_INSTRUCTION has no strength entry and never did: strength() returns 0 for it. Not this job's change.)
check("the new member has an explicit strength and grounded entry", S.EXTERNAL_REFERENCE in sm._SOURCE_STRENGTH and S.EXTERNAL_REFERENCE in sm.GROUNDED_SOURCES)

print("[2] the cap in _grade")
def world(dom, n=3, contra=0):
    return MP("world", True, True, n, contra, dom)
def grade(dom, ver=V.NONE, n=3):
    w = world(dom, n)
    return L._grade(w, ver, [w], 0.5)
check("memory_recall, 3 sources, no contradiction -> KNOW (unchanged)", grade("memory_recall") == "KNOW")
check("external_reference, same picture -> THINK (page alone cannot KNOW)", grade("external_reference") == "THINK")
check("parametric_library cap unchanged", grade("parametric_library") == "THINK")
check("external_reference + tier-1/3 witness lifts the cap", grade("external_reference", V.EXTERNAL_WITNESS) == "KNOW")
check("external_reference + user confirmation lifts the cap", grade("external_reference", V.USER_CONFIRMED) == "KNOW")
check("a weaker picture is not raised by the cap (1 source, 2 contradictions -> SUSPECT)",
      L._grade(MP("world", True, True, 1, 2, "external_reference"), V.NONE,
               [MP("world", True, True, 1, 2, "external_reference")], 0.5) == "SUSPECT")

print("[3] end to end through _world / _compute with fake fragments")
def frag(origin): return SimpleNamespace(origin=origin)
def state(origins):
    return SimpleNamespace(memory_fragments=[frag(o) for o in origins], recall=None, episodic_scene=None,
                           conversation_history=None, executive=None, reflection=None, attention_vector=None,
                           recurring_subconscious_patterns=None, social_note=None, active_goal_note=None)
w = L._world(state(["research", "research", "research"]))
check("three pages alone: dominant external_reference, 3 sources", w.dominant_source == "external_reference" and w.source_count == 3)
a = L()._compute(state(["research", "research", "research"]))
check("three pages alone grade THINK, not KNOW", a is not None and a.grade == "THINK")
w2 = L._world(state(["research", "lived", "research"]))
check("a page next to lived memory: memory still the dominant ground", w2.dominant_source == "memory_recall")
a2 = L()._compute(state(["research", "lived", "consolidation"]))
check("page + remembered experience still reaches KNOW", a2 is not None and a2.grade == "KNOW")

print("FAILED: %d" % len(FAILS) if FAILS else "all pass")
sys.exit(1 if FAILS else 0)
