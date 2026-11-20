"""J-3255 test (D-0644, F-3539): search_by_subjects rank="distinct" vs the original download order.

Offline.  Reads ONLY (a) the static SPGC catalogue CSV and (b) a COPY of data/librarian_log.jsonl that you pass in.
It never opens C:\\Nascence\\data, never calls a model: the log already holds the headings each ask produced
(`subjects`), so the replay re-runs only the mechanical step (headings -> rows) under both rankings.  The reading
shelf is forced empty (the worktree has none), so both arms see the same "everything is fresh" state; the logged
canon share of the same 100 asks (live shelf, original ranking) is printed as the baseline.

Usage:  python scripts/test_librarian_distinct_rank_J3255.py LOGCOPY.jsonl [--n 100]
"""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core  # noqa: E402,F401  (BEFORE any other repo import; asserted to be the worktree copy below)

assert str(Path(core.__file__).resolve()).lower().startswith(r"c:\wt\wt_wb_memlev"), core.__file__

from core import library_hand as lib   # noqa: E402
from core import reading_history as rh  # noqa: E402

# The 14 canon books named in F-3539 (lowercase substring of the shown title).
CANON = ["the prince", "siddhartha", "beyond good and evil", "tractatus", "meditations", "the iliad", "ulysses",
         "alice's adventures", "pens", "orthodoxy", "pride and prejudice", "war and peace",
         "anne of green gables", "my secret life"]
TOP4 = ["the prince", "beyond good and evil", "siddhartha", "tractatus"]


def is_canon(t: str) -> bool:
    t = t.lower()
    return any(c in t for c in CANON)


def share(titles_by_ask):
    tot = sum(len(t) for t in titles_by_ask)
    return sum(is_canon(x) for t in titles_by_ask for x in t) / tot if tot else 0.0


def top4(titles_by_ask):
    c = Counter()
    for t in titles_by_ask:
        for x in t:
            for k in TOP4:
                if k in x.lower():
                    c[k] += 1
    return {k: c[k] for k in TOP4}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.log, encoding="utf-8") if l.strip()]
    asks = [r for r in rows if r.get("subjects")][-a.n:]
    print(f"replaying {len(asks)} asks (log has {len(rows)} rows)")

    cat = list(lib._rows())            # one CSV scan for the whole replay
    lib._rows = lambda: iter(cat)
    rh.shelf_keys = lambda *a_, **k_: set()
    rh.is_known = lambda *a_, **k_: False

    # --- unit checks on a tiny synthetic catalogue -------------------------------------------------
    syn = [dict(title="Broad Popular", language="['en']", subjects="Philosophy", downloads="9000", author="a"),
           dict(title="Specific Two", language="['en']", subjects="Ethics; Stoicism", downloads="10", author="b"),
           dict(title="Specific Three", language="['en']", subjects="Ethics; Stoicism; Philosophy", downloads="5", author="c"),
           dict(title="Other", language="['en']", subjects="Cooking", downloads="99999", author="d")]
    keep, lib._rows = lib._rows, (lambda: iter(syn))
    old = [r["title"] for r in lib.search_by_subjects(["philosophy", "ethics", "stoicism"], 8)]
    new = [r["title"] for r in lib.search_by_subjects(["philosophy", "ethics", "stoicism"], 8, "distinct")]
    dup = [r["title"] for r in lib.search_by_subjects(["Philosophy", "philosophy ", "ethics"], 8, "distinct")]
    lib._rows = keep
    assert old[0] == "Broad Popular", old                       # original order unchanged for other callers
    assert new == ["Specific Three", "Specific Two", "Broad Popular"], new
    assert dup[0] == "Specific Three", dup                       # duplicated headings count once
    assert "Other" not in new
    assert lib.search_by_subjects([], 8, "distinct") == []
    print("unit checks OK: default order unchanged, distinct puts 3-heading > 2-heading > 1-heading, dupes count once")

    # --- replay ------------------------------------------------------------------------------------
    res = {}
    for mode in ("downloads", "distinct"):
        shown, zero = [], 0
        for i, r in enumerate(asks):
            random.seed(i)
            hit = lib.search_by_subjects(r["subjects"], 8, mode)
            zero += not hit
            shown.append([h["title"][:60] for h in hit])
        res[mode] = (shown, zero)
    logged = [r.get("titles") or [] for r in asks]
    print(f"\n{'':22}{'canon share':>12}{'zero-hit asks':>15}   top-4 appearances (Prince / BGE / Siddhartha / Tractatus)")
    print(f"{'logged (live shelf)':22}{share(logged):>12.3f}{sum(not r.get('n_hits') for r in asks):>15}   "
          f"{list(top4(logged).values())}")
    for mode, (shown, zero) in res.items():
        print(f"{'replay ' + mode:22}{share(shown):>12.3f}{zero:>15}   {list(top4(shown).values())}")
    d, n = res["downloads"][0], res["distinct"][0]
    print(f"\nasks whose shown set changed: {sum(1 for x, y in zip(d, n) if x != y)} of {len(asks)}")
    assert res["distinct"][1] == res["downloads"][1], "ranking must not change which asks get zero hits"
    assert share(n) <= share(d) + 1e-9, "distinct ranking should not raise canon share"
    print("PASS")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
