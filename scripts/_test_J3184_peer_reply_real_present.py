"""J-3184 (D-0571): the reply to a friend's letter reports only what is true of his day.

  [1] the _rsys reply prompt no longer says "your garden, your reading"; it says only what is true of his own
      days, and adds no line telling him what to write about.
  [2] the reply's user prompt is fed the real present: the thought that moved him and the current book
      (core.reading.current_book), best-effort; the friend's letter stays last; absent parts leave no residue.
  [3] the write-first _isys prompt and the stored-memory shape ("(my letter to X) ...", importance 0.8,
      origin peer) are untouched.
Zero LLM, zero live data (current_book is stubbed).   python scripts/_test_J3184_peer_reply_real_present.py
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

path = ROOT / "nodes" / "inner_monologue_node.py"
src = path.read_text(encoding="utf-8")
tree = ast.parse(src)

# locate the _rsys assignment by name and evaluate its constant-string concatenation (with _nm bound)
rsys_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "_rsys" for t in n.targets)]
assert len(rsys_nodes) == 1, len(rsys_nodes)
rsys = eval(compile(ast.Expression(rsys_nodes[0].value), "<rsys>", "eval"), {"_nm": "Darwin"})

# [1]
low = rsys.lower()
assert "garden" not in low and "your reading" not in low, rsys
assert "say only what is true of your own days" in rsys, rsys
assert "share your own thoughts" in rsys
assert "ask them things in return" in rsys   # J-2985 (F-3684): gender-neutral (was "ask him")
for hint in ("write about", "mention", "tell him about", "describe your", "your shore", "your hill"):
    assert hint not in low, hint
# J-2985 (F-3678) removed the named-image "retire it" sentence; scripts/_test_J-2985_reply_prompt.py owns that
print("[1] ok")

# [2] run the _rpresent block for real, as the hub does, with a stubbed current_book
seg_start = src.index('_rpresent = ""')
seg_end = src.index("_rd = await call_node_json(self.conscious_urls, _rsys,", seg_start)
block = src[seg_start:seg_end]
import textwrap  # noqa: E402

code = textwrap.dedent(" " * 24 + block.lstrip())


def run(thought, book):
    fake = types.ModuleType("core.reading")
    if book is None:
        def current_book():
            raise RuntimeError("no book")
    else:
        def current_book():
            return Path(book)
    fake.current_book = current_book
    old = sys.modules.get("core.reading")
    sys.modules["core.reading"] = fake
    import core as _c
    had = hasattr(_c, "reading")
    prev = getattr(_c, "reading", None)
    _c.reading = fake
    try:
        from core import peers as _pp
        ns = {"thought": thought, "_peers": _pp}
        exec(code, ns)
        return ns["_rpresent"]
    finally:
        if old is None:
            sys.modules.pop("core.reading", None)
        else:
            sys.modules["core.reading"] = old
        if had:
            _c.reading = prev
        else:
            try:
                del _c.reading
            except AttributeError:
                pass


p = run("The tide was out.", "/x/Some_Book_Title.txt")
assert p == 'What was on your mind just now: "The tide was out."\nThe book you are reading now: \'Some Book Title\'.\n', repr(p)
long_p = run("x" * 900, "/x/B.txt")
assert long_p.count("x") == 600  # J-3671: quote_thought limit 600
assert run("", "/x/B.txt") == "The book you are reading now: 'B'.\n"
assert run("A thought.", None) == 'What was on your mind just now: "A thought."\n'
assert run("", None) == ""
# no instruction / topic steer in the injected lines
for bad in ("write about", "mention", "tell him", "you should", "describe"):
    assert bad not in p.lower()

# the user prompt is built as present + blank line + the friend's letter, letter still last
tail = src[seg_end: seg_end + 600]
assert '(_rpresent + "\\n" if _rpresent else "")' in tail
assert '+ _nm + "\'s letter to you:\\n\\"" + _last[:_REPLY_LETTER_CAP] + "\\"\\n\\nWrite your reply now."' in tail   # J-2985
print("[2] ok")

# [3] untouched siblings
assert 'f"(my letter to {_nm}) " + _reply[:_STORED_LETTER_CAP], layer="episodic",' in src
assert "relevance=0.75, importance=0.8" in src
assert 'origin="peer", valence=_md.current_valence(), felt=_md.current_felt())' in src
assert "Share the \"\n                                 \"thing that moved you to write" in src
print("[3] ok")
print("J-3184 all ok")
