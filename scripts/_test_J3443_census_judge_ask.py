"""J-3443 (F-4071): the prompt-site census sees prompts sent through judge_panel._ask from another module, and
prompt_registry.py censuses the tree it is run from (cwd / --root) instead of always C:/Nascence.
Run from the worktree: python scripts/_test_J3443_census_judge_ask.py   (writes only under a temp dir; the
registry ledger is only READ by `check`, never written)."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CENSUS = HERE / "scripts" / "prompt_site_census.py"
TOOL = Path.home() / ".claude" / "skills" / "prompt-registry" / "prompt_registry.py"
fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


tmp = Path(tempfile.mkdtemp(prefix="J3443_"))
try:
    (tmp / "scripts").mkdir()
    (tmp / "core").mkdir()
    (tmp / "nodes").mkdir()
    shutil.copy(CENSUS, tmp / "scripts" / "prompt_site_census.py")
    (tmp / "core" / "judge_panel.py").write_text("async def _ask(session, url, system, user, key, **kw):\n    return None\n", encoding="utf-8")
    (tmp / "core" / "viaattr.py").write_text(
        "SYS = 'be a judge'\n"
        "async def f(s):\n"
        "    from core import judge_panel as _jp\n"
        "    return await _jp._ask(s, _jp.JUDGE_1, SYS, 'u', 'supported', num_predict=7)\n", encoding="utf-8")
    (tmp / "core" / "viafull.py").write_text(
        "import core.judge_panel\n"
        "SYS2 = 'x'\n"
        "async def g(s):\n"
        "    return await core.judge_panel._ask(s, 'url', SYS2, 'u', 'k')\n", encoding="utf-8")
    (tmp / "core" / "viafrom.py").write_text(
        "from core.judge_panel import _ask as _a, rule\n"
        "SYS3 = 'x'\n"
        "async def h(s):\n"
        "    await _a(s, 'url', SYS3, 'u', 'k')\n"
        "    return await rule(SYS3, 'u', 'k')\n", encoding="utf-8")
    (tmp / "core" / "localask.py").write_text(      # a LOCAL _ask with no judge_panel import: not a judge site
        "async def _ask(s, system, user, key):\n    return None\n"
        "async def k(s):\n    return await _ask(s, 'sys', 'u', 'k')\n", encoding="utf-8")

    spec = importlib.util.spec_from_file_location("census_tmp", tmp / "scripts" / "prompt_site_census.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sites, _ = m.census()
    by = {}
    for s in sites:
        by.setdefault(s["module"], []).append(s)
    check([s["via"] for s in by.get("core.viaattr", [])] == ["judge_panel._ask"], "_jp._ask(...) is a judge site")
    check(by["core.viaattr"][0]["system"] == "SYS" and by["core.viaattr"][0]["tok"] == "7",
          "_ask system arg is positional arg 2 (SYS), num_predict read")
    check(len(by.get("core.viafull", [])) == 1, "core.judge_panel._ask(...) via `import core.judge_panel` is a judge site")
    vf = by.get("core.viafrom", [])
    check(sorted(s["via"] for s in vf) == ["judge_panel._ask", "judge_panel.rule"],
          "from core.judge_panel import _ask as _a, rule: both seen under their canonical names")
    check(all(s["system"] == "SYS3" for s in vf), "rule() system is arg 0, _ask() system is arg 2: both read SYS3")
    check("core.localask" not in by, "a module's own _ask with no judge_panel import is NOT a judge site")
    check("core.judge_panel" not in by, "judge_panel's own internal _ask is not a site (it is the plumbing)")

    # registry tool: --root and cwd detection (read-only `census` / `check`)
    r = subprocess.run([sys.executable, str(TOOL), "census", "--root", str(tmp)], capture_output=True, text=True, encoding="utf-8")
    check(r.returncode == 0 and "judge_panel" not in r.stderr and str(tmp) in r.stdout and "core.viaattr:f" in r.stdout,
          "prompt_registry census --root <tmp> reads the tmp tree")
    r = subprocess.run([sys.executable, str(TOOL), "census"], capture_output=True, text=True, encoding="utf-8", cwd=str(tmp / "core"))
    check(r.returncode == 0 and "via cwd" in r.stdout and "core.viaattr:f" in r.stdout,
          "prompt_registry census run from a subdir of a tree picks that tree (cwd)")
    r = subprocess.run([sys.executable, str(TOOL), "check"], capture_output=True, text=True, encoding="utf-8", cwd=str(tmp))
    check(r.returncode == 1 and "NEW    core.viaattr:f" in r.stdout, "check from the tree reports its unregistered judge site (exit 1)")
    r = subprocess.run([sys.executable, str(TOOL), "census"], capture_output=True, text=True, encoding="utf-8", cwd=str(tmp.parent))
    check(r.returncode == 0 and "via default" in r.stdout, "outside any tree the default (C:/Nascence) is unchanged")

    # the real worktree: the J-3238 faithfulness judge is now seen
    spec = importlib.util.spec_from_file_location("census_real", CENSUS)
    mr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr)
    keys = {s["key"] for s in mr.census()[0]}
    check("core.refinery:_judge_faithfulness" in keys, "this tree: refinery._judge_faithfulness (J-3238) is now in the census")
    check("core.ground_grade:_ask" in keys, "this tree: ground_grade._ask wrapper is now in the census")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("FAILED: %d" % len(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
