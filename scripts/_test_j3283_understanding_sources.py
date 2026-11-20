"""J-3283 (D-0631 review J-3243): grounded_learning.consolidate must not distil a system-fetched Wikipedia page
into "my own understanding", and every material line must carry its source word.

Offline: an EMPTY isolated store, a fake call_json that captures the prompt text (no model is called). Also prints
the prompt input BEFORE (the HEAD~ version of the module, loaded from git) and AFTER on the same seeded material."""
import subprocess
import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
sys.path.insert(1, str(Path.home() / '.claude' / 'skills' / 'job-queue'))
import lab_env
tree = Path(__file__).resolve().parent.parent
assert tree in Path(core.__file__).resolve().parents, core.__file__

import asyncio
import tempfile
import time
from core import grounded_learning as gl

FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


def _old_module():
    """The module as committed before this job (HEAD of the parent commit), for the before/after comparison."""
    src = subprocess.run(["git", "show", "HEAD:core/grounded_learning.py"], cwd=str(tree), capture_output=True,
                         text=True, encoding="utf-8").stdout
    if "_SOURCE_WORD" in src:      # already committed: take the parent
        src = subprocess.run(["git", "show", "HEAD~1:core/grounded_learning.py"], cwd=str(tree),
                             capture_output=True, text=True, encoding="utf-8").stdout
    m = types.ModuleType("gl_before")
    m.__file__ = str(tree / "core" / "grounded_learning.py")
    exec(compile(src, "gl_before", "exec"), m.__dict__)
    return m


async def run_one(mod, tmp):
    mod._STATE = Path(tmp) / "state.json"
    mod._LOG = Path(tmp) / "log.jsonl"
    seen = {}

    async def fake_call_json(base_urls, sys_p, user_p, **kw):
        seen["user"] = user_p
        return {"understanding": "Fake understanding text that is long enough to be stored by the pass here ok."}
    out = await mod.consolidate(fake_call_json, [])
    return out, seen.get("user")


with lab_env.isolate(db="empty") as lab:
    from core.memory.store import store_fragment, _connect
    t0 = time.time() - 1000
    # six book lines, one study line, then the three kinds of research row
    for i in range(6):
        store_fragment(content=f"[From 'The Principles of Psychology' p{i}] habit is a bundle of acts number {i}.",
                       layer="episodic", origin="reading", timestamp=t0 + i)
    store_fragment(content="[Study note on: The Principles of Psychology] habit makes the path easier.",
                   layer="episodic", origin="study", timestamp=t0 + 10)
    store_fragment(content="[Looked up: 'Significance' (external shock \u2014 uninvited)] Significance refers to importance "
                           "and is also the name of a magazine.", layer="episodic", origin="research", timestamp=t0 + 11)
    store_fragment(content="[Looked up: 'Leiocephalus psammodromus' (pursuit: what is a habit)] A lizard species.",
                   layer="episodic", origin="research", timestamp=t0 + 12)
    store_fragment(content="[Looked up: 'Habit' (curiosity: habit)] Older legacy via, system fetched.",
                   layer="episodic", origin="research", timestamp=t0 + 13)
    store_fragment(content="[Looked up: 'Habituation' (asked by him: habituation)] Habituation is a decrease in response.",
                   layer="episodic", origin="research", timestamp=t0 + 14)

    import tempfile
    old = _old_module()
    with tempfile.TemporaryDirectory(prefix="J-3283_") as tmp, tempfile.TemporaryDirectory(prefix="J-3283_") as tmp2:
        out_b, user_b = asyncio.run(run_one(old, tmp))     # separate state dirs: a run advances last_ts
        out_a, user_a = asyncio.run(run_one(gl, tmp2))
    print("\n--- BEFORE (prompt input) ---\n" + str(user_b) + "\n--- AFTER (prompt input) ---\n" + str(user_a) + "\n")

    check("BEFORE leaked the shock page (baseline reproduces the bug)", user_b and "Significance refers to importance" in user_b)
    check("BEFORE leaked the pursuit page", user_b and "lizard species" in user_b)
    check("AFTER: shock page excluded", user_a and "Significance refers" not in user_a)
    check("AFTER: pursuit page excluded", user_a and "lizard species" not in user_a)
    check("AFTER: legacy 'curiosity:' via page excluded", user_a and "Older legacy via" not in user_a)
    check("AFTER: page he asked for is kept and marked", user_a and "(Wikipedia, a page I asked for) [Looked up: 'Habituation'" in user_a)
    check("AFTER: book lines carry '(book)'", user_a and user_a.count("- (book) [From 'The Principles of Psychology'") == 6)
    check("AFTER: study line carries '(my study note)'", user_a and "- (my study note) [Study note on:" in user_a)
    check("AFTER: no bare unmarked material line", user_a and all(
        ln.startswith("- (") for ln in user_a.splitlines() if ln.startswith("- ")))
    check("AFTER: topic is still the book (the _topic regex still sees the From tag)",
          gl._topic(user_a or "") == "The Principles of Psychology")
    check("AFTER: a note is still produced", bool(out_a))

    # below the minimum once the system-fetched rows are excluded: 4 books + shock/pursuit rows => no note
    with _connect() as c:
        c.execute("DELETE FROM memory_fragments")
    for i in range(4):
        store_fragment(content=f"[From 'Fragments of Science' p{i}] heat is motion {i}.", layer="episodic",
                       origin="reading", timestamp=t0 + i)
    for i in range(4):
        store_fragment(content=f"[Looked up: 'Page{i}' (external shock \u2014 uninvited)] random page {i}.",
                       layer="episodic", origin="research", timestamp=t0 + 20 + i)
    with tempfile.TemporaryDirectory(prefix="J-3283_") as tmp, tempfile.TemporaryDirectory(prefix="J-3283_") as tmp2:
        out_b2, _ = asyncio.run(run_one(old, tmp))
        out_a2, _ = asyncio.run(run_one(gl, tmp2))
    check("shock rows no longer pad the 5-fragment minimum (before: a note; after: none)", out_b2 and not out_a2)

print("\nFAILS:", FAILS)
sys.exit(1 if FAILS else 0)
