"""J-3300 test: the T4 docstring/comment edit changed no executable code.

Compares each edited file at the J-3300 parent commit (ba23a453) against the working tree, with docstrings stripped
from the AST, and asserts the docstring-stripped trees are identical. Also asserts the stale claims are gone and the
corrected statements are present. Reads only; writes nothing; touches no live data.
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# J-4052 re-pin: the test used to compare the J-3300 parent against the WORKING TREE, which went stale the moment a later
# commit changed code in these files. It now compares each file's J-3300 commit against ITS OWN parent (the edit itself).
COMMITS = {"core/provisional_identity.py": "381bda18", "core/axiom_layers.py": "2498a9f9", "nodes/subconscious_node.py": "d2cb23d7"}
FILES = tuple(COMMITS)


def strip(src: str) -> str:
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
                    and isinstance(b[0].value.value, str):
                n.body = b[1:] or [ast.Pass()]
    return ast.dump(tree)


fails = []
for rel in FILES:
    old = subprocess.run(["git", "show", f"{COMMITS[rel]}^:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    new = subprocess.run(["git", "show", f"{COMMITS[rel]}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    if strip(old) != strip(new):
        fails.append(f"{rel}: executable AST changed")
    compile(new, rel, "exec")

pi = (ROOT / "core/provisional_identity.py").read_text(encoding="utf-8")
al = (ROOT / "core/axiom_layers.py").read_text(encoding="utf-8")
sn = (ROOT / "nodes/subconscious_node.py").read_text(encoding="utf-8")
for label, text, bad in (
    ("pi stale prior claim", pi, "it is held as a real prior (the contradiction-detector appraises NEW"),
    ("al stale propagation claim", al, "This is the one change that makes the\n    probationary loop a real state-transition test"),
    ("sn stale line ref", sn, "RETURNS at line ~1582"),
):
    if bad in text:
        fails.append(f"stale text still present: {label}")
for label, text, good in (
    ("pi prediction test", pi, "PREDICTION"),
    ("pi no discharge", pi, "_discharge_contradiction"),
    ("al not served", al, "THAT IS NOT WHAT THE LIVE CODE DOES"),
    ("sn dormant-only note", sn, "reachable ONLY from this dormant block"),
):
    if good not in text:
        fails.append(f"expected text missing: {label}")

print("FAIL" if fails else "PASS", fails)
sys.exit(1 if fails else 0)
