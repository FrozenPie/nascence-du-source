"""J-2067: every constructed string has three pairwise-distinct vertices; ties resolve deterministically.
Pure in-memory (build_all only; writes nothing). Usage: python scripts/_test_j2067_string_vertices.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import sound_string_shadow as sss  # noqa: E402

spec = importlib.util.spec_from_file_location("dry", ROOT / "scripts" / "sound_strings_phase1_dryrun.py")
dry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dry)

strings = dry.build_all()
bad = []
for k, e in strings.items():
    s = e["string"]
    for a, b in (("onset", "peak"), ("peak", "tail"), ("onset", "tail")):
        if all(s[a][x] == s[b][x] for x in sss._AXES):
            bad.append((k, e["archetype"], a, b))
assert not bad, f"degenerate strings: {bad}"

# tie-break: a point equidistant from onset and tail prefers the bracket vertex and flags tie
e = {"string": {"onset": {x: 0.2 for x in sss._AXES}, "peak": {x: 0.9 for x in sss._AXES},
                "tail": {x: 0.2 for x in sss._AXES}}}
pt = {x: 0.2 for x in sss._AXES}
assert sss._nearest_vertex(e, pt, ("peak", "tail")) == ("tail", True)
assert sss._nearest_vertex(e, pt, ("onset", "peak")) == ("onset", True)
assert sss._nearest_vertex(e, pt, None) == ("onset", True)
assert sss._nearest_vertex(strings["kereru_wingbeats"], strings["kereru_wingbeats"]["string"]["tail"])[1] is False
print("PASS", len(strings), "strings")
