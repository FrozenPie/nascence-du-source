"""J-3493 (F-4104): Follow Line GROUNDS lines carry no store label and are cut on a boundary. Pure functions only.
Run: python scripts/_test_J-3493_grounds_text.py"""
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl
ok = True
def check(n, c):
    global ok
    ok = ok and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
body = "The heron stands in the shallows and waits for the water to settle before it moves at all, which is its whole method. " * 4
for lab in ("[gist \u00b7 semantic] ", "[From 'A Book [vol 2]'] ", "Q: what is it?\nA: "):
    stored = fl._grounds_cut(lab + body)
    check(f"source cut keeps label {lab[:10]!r} intact", stored.startswith(lab.strip()[:6]))
    check("source cut is on a boundary (sentence end or '...')", stored.endswith((".", "!", "?", "...")))
    cargo = {"grounds": [{"origin": "reading", "age": "a month ago", "text": stored}], "grounds_outcome": "found"}
    t = fl.render({"q": "why wait?"}, cargo, {"a": "yes"})
    line = [x for x in t.split(" In ") if x.startswith("reading")][0] if " In " in t else t
    check("rendered ground has no label", "[gist" not in t and "[From" not in t and "Q:" not in t and "\nA:" not in t)
    check("cargo grounds untouched by render", cargo["grounds"][0]["text"] == stored)
short = fl._grounds_cut("[gist \u00b7 semantic] A short fact.")
check("short text passes whole", short == "[gist \u00b7 semantic] A short fact.")
check("unbalanced label ground is skipped, no crash", "[From" not in fl.render({"q": "x"}, {"grounds": [{"origin": "reading", "age": "", "text": "[From 'abc"}], "grounds_outcome": "found"}, {"a": "yes"}))
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
