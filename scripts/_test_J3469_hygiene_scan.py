"""J-3469 test: scripts/hygiene_ref_scan_J3469.py classifies udms_hygiene leads from the token stream.

Builds a throwaway tree under a temp dir (no live data touched) and checks each verdict, then checks the committed
lead lists and results in docs/lab/J-3469_data/ are internally consistent. Run from the worktree:
    python scripts/_test_J3469_hygiene_scan.py
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401,E402  (import core BEFORE any lab_env, per the job-run test rule)

spec = importlib.util.spec_from_file_location("hygiene_ref_scan_J3469", ROOT / "scripts" / "hygiene_ref_scan_J3469.py")
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)

FAILS = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


with tempfile.TemporaryDirectory() as td:
    r = Path(td)
    (r / "core").mkdir()
    (r / "scripts").mkdir()
    (r / ".claude" / "worktrees" / "a").mkdir(parents=True)
    (r / "core" / "m.py").write_text(
        '"""Module doc mentions doc_only_fn() and string_key."""\n'
        "def dead_fn():\n    return 1\n"
        "def doc_only_fn():\n    # comment mentions doc_only_fn\n    return 2\n"
        "def own_fn():\n    return 3\n"
        "def real_fn():\n    return 4\n"
        "def script_fn():\n    return 5\n"
        "def test_fn():\n    return 6\n"
        "def string_fn():\n    return 7\n"
        "def alias_fn():\n    return 8\n"
        "x = own_fn()\n", encoding="utf-8")
    (r / "core" / "user.py").write_text(
        "from core import m as _alias\n"
        "def go():\n    return _alias.real_fn() + _alias.alias_fn()\n"
        'KEY = "string_fn"\n', encoding="utf-8")
    (r / "scripts" / "tool.py").write_text("from core import m\nm.script_fn()\n", encoding="utf-8")
    (r / "scripts" / "test_thing.py").write_text("from core import m\nm.test_fn()\n", encoding="utf-8")
    # a worktree copy that calls dead_fn must NOT count (.claude is skipped)
    (r / ".claude" / "worktrees" / "a" / "copy.py").write_text("import m\nm.dead_fn()\n", encoding="utf-8")
    leads = [f"core/m.py::{n}" for n in ("dead_fn", "doc_only_fn", "own_fn", "real_fn", "script_fn", "test_fn", "string_fn", "alias_fn")]
    res = hs.scan(r, leads)
    v = {k.split("::")[1]: res[k]["verdict"] for k in leads}
    check(v["dead_fn"] == "DEAD", f"dead_fn is DEAD (worktree copy ignored): {v['dead_fn']}")
    check(v["doc_only_fn"] == "DEAD", f"docstring/comment-only name is DEAD: {v['doc_only_fn']}")
    check(v["own_fn"] == "OWN_CALL", f"own_fn is OWN_CALL: {v['own_fn']}")
    check(v["real_fn"] == "REAL_CALL", f"call through a module alias attribute is REAL_CALL: {v['real_fn']}")
    check(v["alias_fn"] == "REAL_CALL", f"alias_fn is REAL_CALL: {v['alias_fn']}")
    check(v["script_fn"] == "SCRIPT_ONLY", f"script_fn is SCRIPT_ONLY: {v['script_fn']}")
    check(v["test_fn"] == "TEST_ONLY", f"test_fn is TEST_ONLY: {v['test_fn']}")
    check(v["string_fn"] == "STRING_ONLY", f"string_fn is STRING_ONLY: {v['string_fn']}")

data = ROOT / "docs" / "lab" / "J-3469_data"
leads_doc = json.loads((data / "leads.json").read_text(encoding="utf-8"))
check(len(leads_doc["zero_ref_30"]) == 30 and len(set(leads_doc["zero_ref_30"])) == 30, "leads.json carries 30 distinct zero-ref leads")
check(len(leads_doc["nonzero_33"]) == 33 and len(set(leads_doc["nonzero_33"])) == 33, "leads.json carries 33 distinct non-zero leads")
res_doc = json.loads((data / "scan_results_2026-11-07.json").read_text(encoding="utf-8"))
z = [v["verdict"] for k, v in res_doc["zero_ref_30"].items() if not k.startswith("_")]
check(z.count("DEAD") == 30, f"committed results: all 30 zero-ref leads DEAD ({z.count('DEAD')})")
n = [v["verdict"] for k, v in res_doc["nonzero_33"].items() if not k.startswith("_")]
check(n.count("REAL_CALL") == 6, f"committed results: 6 of the 33 are REAL_CALL alias false positives ({n.count('REAL_CALL')})")
# J-4052: J-3844 (D-0738) archived core/world_knowledge.py and core/induction_drill.py (leads confirmed DEAD by this very
# scan) to scripts/archive/; a lead's module counts as present if it is in its original place OR archived there.
def _lead_present(k):
    rel = k.split("::")[0]
    return (ROOT / rel).exists() or (ROOT / "scripts" / "archive" / Path(rel).name).exists()


check(all(_lead_present(k) for k in leads_doc["zero_ref_30"] + leads_doc["nonzero_33"]), "every lead's module file exists in this tree (or was archived by J-3844)")

print("\n%d failure(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
