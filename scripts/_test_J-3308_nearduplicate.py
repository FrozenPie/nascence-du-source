"""J-3308: test the replay script's pure parts and its report stage on a synthetic pair set under a temp dir.
Touches no live data and calls no model."""
import importlib.util
import json
import random
import string
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (import core BEFORE any lab_env, per the job-run test rule)

spec = importlib.util.spec_from_file_location("lab_j3308", ROOT / "scripts" / "lab_J-3308_nearduplicate_replay.py")
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
assert Path(L.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"


def test_tiers():
    t = L.tiers("Why is the sea salty?", "why is the SEA salty", None)
    assert t["t1"] and t["ref_dup"], t
    t = L.tiers("Why is the sea salty?", "What makes seawater taste of salt?", 0.88)
    assert (not t["t1"]) and t["t3"] and t["ref_dup"], t
    t = L.tiers("the river carries memory", "a loaf of bread rises slowly", 0.2)
    assert not t["ref_dup"], t
    assert L.shingles("") == set() and L.jac(set(), set()) == 0.0
    assert abs(L.cos([1, 0], [1, 0]) - 1.0) < 1e-9 and L.cos(None, [1]) is None


def test_wilson():
    lo, hi = L.wilson(3, 30)
    assert 0.03 < lo < 0.1 < hi < 0.27, (lo, hi)
    assert L.wilson(0, 0) == (None, None)


def test_rules_import_sites_own_code():
    rules = L.site_rules()
    # the sites' own constants/functions are used, so a drift in them is seen here
    assert rules["delib"]("a b c d e", "a b c d e", None)
    assert not rules["delib"]("the sea is salty today friend", "bread rises in a warm kitchen oven", None)
    assert rules["frontier_lex"]("Why do granite coatings form on stone?", "Why do granite coatings form on stones?", None)
    assert not rules["frontier_lex"]("Why is the sea salty", "How do birds navigate home", None)
    assert rules["frontier"]("alpha delta words", "gamma sigma tokens", 0.9)          # live semantic leg
    assert not rules["frontier_lex"]("alpha delta words", "gamma sigma tokens", 0.9)
    assert rules["commit"]("x", "y", 0.5)                                  # cosine >= 0.45
    assert not rules["commit"]("alpha beta gamma delta", "epsilon zeta eta theta", 0.1)


def test_frontier_and_wager_tokenizers_identical():
    from core import frontier, wager_curiosity
    rnd = random.Random(7)
    alpha = string.ascii_letters + "'  -.,?!012渡"
    for _ in range(3000):
        s = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 60)))
        assert frontier._toks(s) == wager_curiosity._toks(s), s


def test_report_on_synthetic():
    out = Path(tempfile.mkdtemp(prefix="j3308_test_"))
    pairs, sample, labels = [], [], []
    for i in range(40):
        src = "F" if i < 20 else "D"
        site = i % 2 == 0
        row = {"pid": f"P{i:04d}", "src": src, "kind": "x", "a": "a", "b": "b", "cos": 0.5, "t1": False, "t2": False,
               "t3": site, "j3": 0.1, "ref_dup": site, "rules": {n: site for n in ("frontier", "frontier_lex", "wager", "lane2", "delib", "guid", "commit", "moment")},
               "site_dup": site, "stratum": L.STRATA[0] if site else L.STRATA[4], "pool_n": 10, "alloc_n": 5}
        pairs.append(row)
        sample.append({"pid": row["pid"], "src": src, "stratum": row["stratum"], "swap": False, "a": "a", "b": "b",
                       "pool_n": 10, "judged_n": 5})
        labels.append({"pid": row["pid"], "model": "gemma4:12b", "same": site})
        labels.append({"pid": row["pid"], "model": "falcon3:7b", "same": site})
    for name, rows in (("pairs.jsonl", pairs), ("judge_pairs.jsonl", sample), ("judge_labels.jsonl", labels)):
        with open(out / name, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    import argparse
    L.cmd_report(argparse.Namespace(out=str(out)))
    s = json.load(open(out / "summary.json", encoding="utf-8"))
    assert s["per_source"]["F"]["site_agree_weighted"] == 1.0, s["per_source"]["F"]
    assert s["decision"].startswith("STOP"), s["decision"]
    assert L.panel_label({"gemma4:12b": True, "falcon3:7b": False, "yi:34b-v1.5": False}) == (False, "yi_tiebreak")
    assert L.panel_label({"gemma4:12b": True, "falcon3:7b": None}) == (True, "single_judge")


if __name__ == "__main__":
    test_tiers()
    test_wilson()
    test_rules_import_sites_own_code()
    test_frontier_and_wager_tokenizers_identical()
    test_report_on_synthetic()
    print("J-3308 tests OK")
