"""Regression test for F-2423 (2026-10-04): importing lab_env must never shadow a caller's OWN `core` package.

Before the fix, ~/.claude/skills/job-queue/lab_env.py ran sys.path.insert(0, "C:\\Nascence") on import, so a test launched
from a job-run worktree that imported lab_env before core loaded the SHARED tree's core -- exercising master's code and
writing Du's LIVE __file__-relative data/ files through every module isolate(also=[...]) does not redirect (the second
2026-10-04 live-store leak). The fix appends instead of inserting at position 0.

Each scenario runs in a fresh interpreter (sys.path / sys.modules state is the whole point). Read-only: find_spec never
executes the package, lab_env.isolate() is never called, the fake tree lives in a temp dir that is removed afterwards.
Exit code 0 = all checks pass."""
import pathlib, shutil, subprocess, sys, tempfile

HOME_SKILL = str(pathlib.Path.home() / ".claude" / "skills" / "job-queue")
SHARED = pathlib.Path(r"C:\Nascence")
FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


def run(code, cwd):
    p = subprocess.run([sys.executable, "-c", code], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, [ln for ln in p.stdout.splitlines() if ln.strip()], p.stderr


tmp = pathlib.Path(tempfile.mkdtemp(prefix="fake_worktree_"))
try:
    (tmp / "core").mkdir()
    (tmp / "core" / "__init__.py").write_text("", encoding="utf-8")

    print("[1] a caller whose own tree is first on sys.path keeps its own core after importing lab_env")
    code = (
        "import importlib.util, pathlib, sys\n"
        f"sys.path.insert(0, {str(tmp)!r}); sys.path.insert(1, {HOME_SKILL!r})\n"
        "before = pathlib.Path(importlib.util.find_spec('core').origin).resolve()\n"
        "import lab_env\n"
        "after = pathlib.Path(importlib.util.find_spec('core').origin).resolve()\n"
        "print(before); print(after); print(sys.path[0])\n"
    )
    rc, out, err = run(code, str(tmp))
    check("interpreter ran cleanly (%s)" % (err.strip()[:80] or "no stderr"), rc == 0 and len(out) == 3)
    if len(out) == 3:
        check("core resolved to the caller's tree before importing lab_env", pathlib.Path(out[0]).parent.parent == tmp.resolve())
        check("core STILL resolves to the caller's tree after importing lab_env (F-2423)", pathlib.Path(out[1]).parent.parent == tmp.resolve())
        check("sys.path[0] is not the shared tree after the import", pathlib.Path(out[2]).resolve() != SHARED.resolve())

    print("[2] a caller outside any Nascence tree can still import core through lab_env's appended path")
    code = (
        "import importlib.util, pathlib, sys\n"
        f"sys.path.insert(0, {HOME_SKILL!r})\n"
        "import lab_env\n"
        "print(pathlib.Path(importlib.util.find_spec('core').origin).resolve())\n"
        "print(sys.path[-1])\n"
    )
    rc, out, err = run(code, tempfile.gettempdir())
    check("interpreter ran cleanly (%s)" % (err.strip()[:80] or "no stderr"), rc == 0 and len(out) == 2)
    if len(out) == 2:
        check("core resolves to the shared tree (the original reason for the path entry)", pathlib.Path(out[0]).parent.parent == SHARED.resolve())
        check("the shared tree was appended at the END of sys.path", pathlib.Path(out[1]).resolve() == SHARED.resolve())

    print("[3] a caller that already has the shared tree on sys.path is unchanged (no duplicate entry)")
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(SHARED)!r}); sys.path.insert(1, {HOME_SKILL!r})\n"
        "n0 = sys.path.count(" + repr(str(SHARED)) + ")\n"
        "import lab_env\n"
        "print(n0); print(sys.path.count(" + repr(str(SHARED)) + "))\n"
    )
    rc, out, err = run(code, str(SHARED))
    check("interpreter ran cleanly (%s)" % (err.strip()[:80] or "no stderr"), rc == 0 and len(out) == 2)
    if len(out) == 2:
        check("sys.path entry count for the shared tree is unchanged by the import", out[0] == out[1] == "1")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nALL OK" if not FAILS else "\n%d FAILED: %s" % (len(FAILS), FAILS))
sys.exit(0 if not FAILS else 1)
