"""scripts/test_sleep_single_pass_equivalence.py (J-1922 / F-2549): offline proof that the single-pass sleep sweeps
(core/like_scan.py behind book_residue.sweep, stick_test.census/snapshot and world_consolidation.sweep) produce BYTE-IDENTICAL
output to the old per-term LIKE scans, on a FULL-fidelity data/ copy inside a throwaway worktree.

Runs inside scripts/lag_harness' prelude (audit hook: no write under live C:\\Nascence, no subprocess, network blocked once
_NET['block'] is set) -- no model call can happen: only core data modules are imported (never nodes/*), and the block is PROVEN
first (an asyncio connect to a closed local port must be refused by the prelude, not by the OS).

env: LAGH_SCRATCH (dir holding the worktrees), LAGH_WT (worktree dir name under it)
usage: python test_sleep_single_pass_equivalence.py --mode old|new|off --out OUT.json --now EPOCH [--passes 1|2]
  old  the pre-J-1922 tree (HEAD of the parent commit): the per-term SQL
  new  the J-1922 tree, like_scan.SWEEPS_SINGLE_PASS = True (default); the single-pass objects are asserted to have been USED
  off  the J-1922 tree with the kill switch set False (must equal old: proves the old code path is intact)
Each pass runs stick_test.census() (full rows hashed), stick_test.snapshot, world_consolidation.sweep, book_residue.sweep in the
sleep routine's order. time.time() is frozen to --now. Outputs: raw bytes appended to each jsonl, the return values, the
census rows, and a hash of (fragment_id, chapter_id) over all of memory_fragments. Pass 2 first NULLs chapter_id of every filed
reading/study fragment (identically in every copy) so the sweep has real UPDATEs to do."""
import sys, os, time, json, asyncio, pathlib, hashlib, argparse, sqlite3

ap = argparse.ArgumentParser()
ap.add_argument("--mode", required=True, choices=["old", "new", "off"])
ap.add_argument("--out", required=True)
ap.add_argument("--now", type=float, required=True)
ap.add_argument("--passes", type=int, default=2)
args = ap.parse_args()

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402  (imports core FROM WT, asserts core/_DATA/DB_PATH are inside WT, marks live)
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
DATA = WT / "data"
from core import stick_test, world_consolidation, book_residue  # noqa: E402
from core.memory import store                                    # noqa: E402
for m in (stick_test, world_consolidation, book_residue):
    assert str(pathlib.Path(m.__file__).resolve()).lower().startswith(str(WT).lower()), m.__file__
assert str(store.DB_PATH).lower().startswith(str(WT).lower())

USED = {}
if args.mode == "old":
    assert not (WT / "core" / "like_scan.py").exists(), "old tree must not contain like_scan"
else:
    from core import like_scan
    assert str(pathlib.Path(like_scan.__file__).resolve()).lower().startswith(str(WT).lower())
    assert like_scan.SWEEPS_SINGLE_PASS is True
    if args.mode == "off":
        like_scan.SWEEPS_SINGLE_PASS = False
    # counting wrappers only (no behaviour change): prove the single-pass objects really answer, not the SQL fallback
    def _wrap(obj, name, key, none_is_fallback=True):
        orig = getattr(obj, name)
        def w(*a, **k):
            r = orig(*a, **k)
            d = USED.setdefault(key, {"calls": 0, "fallback_none": 0})
            d["calls"] += 1
            if r is None and none_is_fallback:
                d["fallback_none"] += 1
            return r
        setattr(obj, name, w)
    _wrap(book_residue._SelfRows, "top", "book_residue._SelfRows.top")
    _wrap(book_residue._ReadingGroups, "seen_for", "book_residue._ReadingGroups.seen_for")
    _wrap(book_residue._ReadingGroups, "rows_for", "book_residue._ReadingGroups.rows_for", none_is_fallback=False)
    _wrap(world_consolidation._NoteCache, "candidates", "world_consolidation._NoteCache.candidates")
    _wrap(stick_test, "_term_counts_single_pass", "stick_test._term_counts_single_pass")

FILES = {"stick_test_log": "stick_test_log.jsonl", "world_consolidation_log": "world_consolidation_log.jsonl",
         "book_residue": "book_residue.jsonl"}
_real_time = time.time
time.time = lambda: args.now            # frozen: identical ts and windows in every run


def sizes():
    return {k: ((DATA / v).stat().st_size if (DATA / v).exists() else 0) for k, v in FILES.items()}


def appended(before):
    out = {}
    for k, v in FILES.items():
        p = DATA / v
        b = b""
        if p.exists() and p.stat().st_size > before[k]:
            with open(p, "rb") as f:
                f.seek(before[k]); b = f.read()
        out[k] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    return out


def chapter_hash():
    c = sqlite3.connect(str(store.DB_PATH), timeout=60)
    h = hashlib.sha256(); n = nn = 0
    for fid, ch in c.execute("SELECT fragment_id, chapter_id FROM memory_fragments ORDER BY fragment_id"):
        h.update(f"{fid}\x00{ch}\n".encode()); n += 1; nn += ch is None
    c.close()
    return {"rows": n, "null_chapter": nn, "sha256": h.hexdigest()}


def refile_prep():
    c = sqlite3.connect(str(store.DB_PATH), timeout=60)
    cur = c.execute("UPDATE memory_fragments SET chapter_id=NULL WHERE origin IN ('reading','study') AND chapter_id IS NOT NULL")
    c.commit(); n = cur.rowcount; c.close()
    return n


def jsonable(x):
    try:
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return repr(x)


async def prove_no_network():
    P._NET["block"] = True       # the harness sets this AFTER the loop exists
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", 9), 5)
    except PermissionError as e:
        return {"blocked_by_prelude": True, "err": str(e)[:100]}
    except Exception as e:
        return {"blocked_by_prelude": False, "err": repr(e)[:100]}
    return {"blocked_by_prelude": False, "err": "connected?!"}


def one_pass(label):
    res = {"label": label}
    before = sizes(); res["pre_chapter"] = chapter_hash()
    timings = {}; rets = {}
    steps = [("stick_test.census", stick_test.census), ("stick_test.snapshot", stick_test.snapshot),
             ("world_consolidation.sweep", world_consolidation.sweep), ("book_residue.sweep", book_residue.sweep)]
    for name, fn in steps:
        t0 = time.perf_counter()
        r = fn()
        t1 = time.perf_counter()
        timings[name] = round(t1 - t0, 2)
        if name == "stick_test.census":
            blob = json.dumps(r, sort_keys=True, default=str).encode()
            rets[name] = {"rows": len(r.get("rows", [])), "summary": jsonable(r.get("summary")), "sha256": hashlib.sha256(blob).hexdigest()}
        else:
            rets[name] = jsonable(r)
        print(f"[{label}] {name}: {t1 - t0:.1f}s", flush=True)
    res["timings_s"] = timings; res["returns"] = rets
    res["appended"] = appended(before); res["post_chapter"] = chapter_hash()
    return res


async def main():
    out = {"mode": args.mode, "wt": str(WT), "now": args.now, "core_file": core.__file__}
    out["network_block_proof"] = await prove_no_network()
    print("network block proof:", out["network_block_proof"], flush=True)
    assert out["network_block_proof"]["blocked_by_prelude"], "prelude network block NOT proven; refusing to run"
    out["subprocess_attempts"] = P._SUBP
    out["passes"] = []
    out["passes"].append(one_pass("pass1_as_is"))
    if args.passes >= 2:
        out["refile_nulled"] = refile_prep()
        out["passes"].append(one_pass("pass2_refile"))
    out["single_pass_used"] = USED
    out["subprocess_attempts_after"] = P._SUBP
    json.dump(out, open(args.out, "w"), indent=1)
    print("wrote", args.out)

asyncio.run(main())
