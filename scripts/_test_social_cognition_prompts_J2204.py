"""J-2204 test: the v3 social-cognition prompts (tightened after the F-2903 hand-label check) carry the clauses that
fixed refs_earlier / attributes over-calling, PROMPT_V was bumped so v2 rows are ignored, and nothing touches data/.
No hub calls. Exit 0 = pass."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import social_cognition_shadow as S

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

def fp():
    d = ROOT / "data"
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()} if d.exists() else {}

before = fp()
check("PROMPT_V bumped past 3 (v3 rows ignored by the default; J-3112 made it 5)", S.PROMPT_V >= 3)
check("refs_earlier requires phrase absent from the current message",
      "NOT in the current" in S._SYS["refs_earlier"] and "false" in S._SYS["refs_earlier"])
check("attributes excludes speech verbs ('you speak of')", "'you speak of...'" in S._SYS["attributes"]
      and "feels, fears, wants" in S._SYS["attributes"])
check("attrib_supported and tracks_intent prompts unchanged in key", S._KEY["attrib_supported"] == "supported"
      and S._KEY["tracks_intent"] == "tracks")
check("all prompts still end with the JSON contract", all("Output ONLY JSON" in v for v in S._SYS.values()))
after = fp()
leak = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
check(f"no data/ top-level leak {sorted(leak)}", not leak)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
