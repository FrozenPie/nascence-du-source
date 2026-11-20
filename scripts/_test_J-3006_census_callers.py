"""J-3006 (F-3704): the prompt-site census resolves import aliases when it looks for the callers of a key.

  [1] synthetic tree (temp dir): every binding form resolves -- `from core import left_lane as _ll4` (module alias),
      function-local alias, `import core.left_lane as z`, `from core.left_lane import f as g`, a plain
      `import core.left_lane` full dotted chain, a relative import, a callback reference, self.m() and a
      same-module call; a name that merely shares the function's name on another module does NOT count; a
      function's own recursion is dropped.
  [2] the same tree with aliases=False (a plain-grep reader) finds none of the aliased forms: this is the miss that
      made P-0091 look DEAD.
  [3] the real pre-J-3108 files (git show 63c9e924~1): `_ll4.grade_self_revision(...)` in
      nodes/subconscious_node.py resolves for core.left_lane:grade_self_revision at line 2128 (it was 2045 when the
      finding was written, the file has moved since); without alias resolution it is 0. Skipped, loudly, if git or
      that commit is unavailable.
  [4] this tree: core.left_lane:grade_self_revision_traced resolves to nodes/subconscious_node.py via _ll4; the census
      key list is unchanged by the caller code (same keys with and without calling callers()).
Reads source only; writes only under a temp dir; touches no live data, calls no model.
   python scripts/_test_J-3006_census_callers.py
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

spec = importlib.util.spec_from_file_location("_census_j3006", ROOT / "scripts" / "prompt_site_census.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
assert cm.ROOT == ROOT, cm.ROOT


def write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---- [1] / [2] synthetic tree --------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    t = Path(td)
    write(t, "core/__init__.py", "")
    write(t, "nodes/__init__.py", "")
    write(t, "core/left_lane.py", '''
async def grade(a):
    return await grade(a - 1) if a else None          # recursion: must be dropped

class Lane:
    def judge(self, x):
        return self.helper(x)                          # self.method, same module
    def helper(self, x):
        return x

def local_user():
    return grade(1)                                    # same-module bare name
''')
    write(t, "core/other.py", "def grade(a):\n    return a\n")      # same function name, different module
    write(t, "nodes/a_modalias.py", '''
async def run():
    from core import left_lane as _ll4
    return await _ll4.grade(1)
''')
    write(t, "nodes/b_importas.py", '''
import core.left_lane as z
async def run():
    return await z.grade(1)
''')
    write(t, "nodes/c_funcalias.py", '''
from core.left_lane import grade as g
async def run():
    return await g(1)
''')
    write(t, "nodes/d_dotted.py", '''
import core.left_lane
async def run():
    return await core.left_lane.grade(1)
''')
    write(t, "core/e_relative.py", '''
from . import left_lane as ll
from .left_lane import grade as gg
async def run():
    return (await ll.grade(1), await gg(2))
''')
    write(t, "nodes/f_callback.py", '''
import asyncio
from core import left_lane as ll
async def run():
    return await asyncio.to_thread(ll.grade, 1)        # passed, not called
''')
    write(t, "nodes/g_unrelated.py", '''
from core import other as ll
async def run():
    return ll.grade(1)                                 # core.other.grade, NOT core.left_lane.grade
''')
    write(t, "nodes/h_method.py", '''
from core import left_lane
def run(lane):
    return left_lane.Lane().judge(1)                   # instance of another module's class: weak name match only
''')

    keys = ["core.left_lane:grade", "core.left_lane:Lane.judge", "core.left_lane:Lane.helper"]
    full = cm.callers(keys, root=t, aliases=True)
    plain = cm.callers(keys, root=t, aliases=False)

    g = {(r["module"], r["how"], r["via_alias"]) for r in full["core.left_lane:grade"]}
    expect = {
        ("nodes.a_modalias", "module-attr", True),
        ("nodes.b_importas", "module-attr", True),
        ("nodes.c_funcalias", "imported-name", True),
        ("nodes.d_dotted", "module-attr", False),
        ("core.e_relative", "module-attr", True),
        ("core.e_relative", "imported-name", True),
        ("nodes.f_callback", "ref", True),
        ("core.left_lane", "same-module", False),
    }
    assert g == expect, (g ^ expect)
    mods = {r["module"] for r in full["core.left_lane:grade"]}
    assert "nodes.g_unrelated" not in mods and "core.other" not in mods, mods
    # recursion inside grade() itself is dropped; local_user() (a different function) is kept
    assert all(r["fn"] != "grade" for r in full["core.left_lane:grade"]), full["core.left_lane:grade"]
    assert any(r["fn"] == "local_user" for r in full["core.left_lane:grade"])
    # methods: self.helper from judge resolves strongly; left_lane.Lane().judge(...) is a weak name match only
    h = full["core.left_lane:Lane.helper"]
    assert [r["fn"] for r in h] == ["Lane.judge"] and h[0]["how"] == "method" and not h[0]["weak"], h
    j = full["core.left_lane:Lane.judge"]
    assert j and all(r["weak"] for r in j), j
    print("[1] ok  grade callers:", sorted(f"{m}:{h}" for m, h, _ in g))

    p = {(r["module"], r["how"]) for r in plain["core.left_lane:grade"]}
    assert p == {("nodes.d_dotted", "module-attr"), ("core.left_lane", "same-module")}, p
    print("[2] ok  without alias resolution only", sorted(p), "survive (the plain-grep view)")

# ---- [3] real files from before J-3108 ------------------------------------------------------------------------
def git_show(rev: str, path: str):
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True, timeout=60)
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


old_sub = git_show("63c9e924~1", "nodes/subconscious_node.py")
old_ll = git_show("63c9e924~1", "core/left_lane.py")
if old_sub is None or old_ll is None:
    print("[3] SKIPPED (git or commit 63c9e924 not available in this clone) -- the finding's line is not re-proved")
else:
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        write(t, "core/__init__.py", "")
        write(t, "nodes/__init__.py", "")
        write(t, "core/left_lane.py", old_ll)
        write(t, "nodes/subconscious_node.py", old_sub)
        key = "core.left_lane:grade_self_revision"
        full = cm.callers([key], root=t, aliases=True)[key]
        plain = cm.callers([key], root=t, aliases=False)[key]
        hit = [r for r in full if r["module"] == "nodes.subconscious_node"]
        assert len(hit) == 1 and hit[0]["line"] == 2128 and hit[0]["via_alias"] and hit[0]["how"] == "module-attr", full
        assert hit[0]["text"] == "_ll4.grade_self_revision", hit[0]
        assert plain == [], plain
        print(f"[3] ok  pre-J-3108 nodes/subconscious_node.py:{hit[0]['line']} "
              f"({hit[0]['fn']}) resolved via alias _ll4; plain view: {len(plain)} callers")

# ---- [4] this tree --------------------------------------------------------------------------------------------
sites_before, _ = cm.census()
k = "core.left_lane:grade_self_revision_traced"
rows = cm.callers([k])[k]
sub = [r for r in rows if r["module"] == "nodes.subconscious_node"]
assert sub and sub[0]["via_alias"] and sub[0]["text"] == "_ll4.grade_self_revision_traced", rows
assert not cm.callers([k], aliases=False)[k] or all(r["module"] == "core.left_lane" for r in cm.callers([k], aliases=False)[k])
sites_after, _ = cm.census()
assert [s["key"] for s in sites_before] == [s["key"] for s in sites_after]
print(f"[4] ok  this tree: {k} <- nodes/subconscious_node.py:{sub[0]['line']} via alias; census keys unchanged "
      f"({len(sites_after)} sites)")
print("ALL OK")
