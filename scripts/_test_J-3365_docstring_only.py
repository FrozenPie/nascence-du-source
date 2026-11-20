"""J-3365 check: the two commits for D-0654 stale-hub wording changed only comments / the module docstring.

Compares the AST (module docstring stripped) of core/judge_panel.py and core/peers.py at the parent of the
J-3365 commits against HEAD-side blobs. Read-only: uses `git show`, writes nothing.
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the job rules)

COMMIT = {"core/judge_panel.py": "4adcd867", "core/peers.py": "ba23a453"}   # the two J-3365 commits


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")


def stripped(src):
    tree = ast.parse(src)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        tree.body = tree.body[1:]
    return ast.dump(tree)


fails = 0
for path, needle in (("core/judge_panel.py", "NO LONGER TRUE"), ("core/peers.py", "CORRECTED 2026-11-05, J-3365")):
    # J-4052 re-pin: compare the J-3365 commit against its own parent (HEAD drifts as later commits touch these files).
    c = COMMIT[path]
    old, new = show(c + "^", path), show(c, path)
    same = stripped(old) == stripped(new)
    has = needle in new
    print(path, "code-identical:", same, "| new wording present:", has)
    fails += (not same) + (not has)
print("PASS" if not fails else "FAIL")
sys.exit(1 if fails else 0)
