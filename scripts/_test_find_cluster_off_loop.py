"""
Proof for J-1180 / F-1648 (PART 2 ONLY): core.chapters.find_cluster no longer freezes the asyncio event loop, and it
finds EXACTLY what it found before -- same algorithm, same seed, same cluster, same sleep length.

THE BUG (F-1648). find_cluster()'s seed selection counts, for every candidate vector, the vectors within
CLUSTER_SIM 0.70 of it: n^2 np.dot calls, about 1,480 s at n = 33,589 (2026-09-21), and it ran as ONE uninterrupted
stretch on the event-loop thread (try_form_chapter called it before its first await). At the start of every full
sleep the whole process froze for ~24.6 min: no substrate tick, no journey leg, no [stability] tick, no log line.

THE FIX UNDER TEST. The algorithm is now a generator (core.chapters._find_cluster_steps) that yields once per
SEED_SCAN_BLOCK = 4096 pairs. find_cluster() still runs it straight through (synchronous, as before);
find_cluster_async() -- which try_form_chapter now awaits -- gives the event loop a turn at every yield (~5 ms).
Why a cooperative coroutine and not asyncio.to_thread: see [7] and find_cluster_async's docstring (a worker thread
passes a plain heartbeat but makes GIL-releasing loop callbacks ~100x slower, cannot be cancelled, and holds
interpreter exit hostage).

WHAT THIS SCRIPT PROVES
  [0] module resolution + isolation: core.chapters / core.memory.store come from THIS root; a Python audit hook
      records any attempt by this process to write under a live data dir or to open the live DB other than by the
      one deliberate mode=ro sample.
  [1] the algorithm is UNTOUCHED, by AST: every statement of the old find_cluster after the seed loop, the
      `n > best_n` (first maximum wins) rule, the per-pair predicate, _candidates/_cooled/_era_window and every
      constant are structurally identical to the base commit 5a66504; the only new top-level names are the
      additive ones; try_form_chapter differs by exactly one call; no threading construct anywhere in the module.
      (J-1293: an inert, DEBUG-only progress checkpoint between the per-pair count and the yield, and its
      `SEED_SCAN_CHECKPOINT_EVERY` constant, are named explicitly in the checks below as additive, not exempted.)
  [2] equivalence against a FROZEN verbatim copy of the base-commit find_cluster (embedded below, cross-checked
      against `git show 5a66504:core/chapters.py` when git is available): identical output (order included),
      identical pre-era membership, on synthetic clusters + decoy rows, exact ties (first maximum wins), 300
      pairs straddling CLUSTER_SIM within +-3e-7, level 1/2, boundary sizes, and a read-only sample of REAL rows.
  [3] heartbeat: a coroutine ticking every 50 ms, while (a) the old blocking call runs on the loop thread and
      (b) find_cluster_async runs. Worst tick lag both ways.
  [4] cost: the extra yields do not lengthen the scan (sleep length unchanged).
  [5] cancellation and re-entry: cancelling mid-scan stops the scan and leaves nothing running; an overlapping
      call never starts a second scan; the in-flight flag is released on completion, cancel and exception.
  [6] the sleep pipeline still WAITS: try_form_chapter never calls the blocking find_cluster, and calls its author
      only after the scan has finished.
  [7] informational: the asyncio.to_thread alternative, measured (why it was not shipped).

ISOLATION. store.DB_PATH is redirected to a temp store built with the real schema (store.init_db) BEFORE anything
runs; only C:\\Nascence\\data\\position.json / room_state.json / the live DB files are stat'ed or hashed. The one
touch of the live DB is a single read-only sqlite URI (mode=ro, PRAGMA query_only=ON) SELECT with LIMIT 2400,
skippable with --no-live-sample. With Du ONLINE the live files legitimately change by themselves, so the hashes
only inform; the audit hook is the proof of no write.

  python scripts/_test_find_cluster_off_loop.py                   # exit 0 = ALL OK
  python scripts/_test_find_cluster_off_loop.py --no-live-sample  # never touches the live DB at all

J-1744 (D-0330, F-2374/F-2377): PART 1 HAS LANDED. The all-pairs seed scan is now a blocked float32 matrix product
(core.chapters._neighbour_counts) whose guard band re-decides every pair near the bar with the old per-pair call, so the
counts, the seed and the cluster are IDENTICAL to the old loop's by construction. What changed here: [1] no longer asserts the
per-pair loop (it is gone) but still asserts the first-maximum rule, the per-pair predicate, everything after the loop and
every helper; [2] gained D3b (every pairwise cosine ON the bar, plus a guard-off mutation that must differ); [3]/[4] use the
frozen old loop as the control and prove the speed-up; [5]-[7] run at tiny tiles so a scan lasts about a second again; [9]
(python scripts/_test_find_cluster_off_loop.py --corpus FILE) is the real-corpus acceptance: full-n per-row counts, seed and
cluster against the OLD per-pair loop sharded over processes, margin-pair and raw-flip census, the new scan's wall time and
event-loop heartbeat at production size, and random real subsamples against the literal frozen function.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import contextlib
import hashlib
import logging
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_ap = argparse.ArgumentParser()
_ap.add_argument("--no-live-sample", action="store_true",
                 help="skip the read-only sample of real rows from the live DB (never open it at all)")
_ap.add_argument("--corpus",
                 help="J-1744 [9]: a sqlite COPY of the real level-0 candidates (table c: fragment_id, content, timestamp, "
                      "importance, embedding, origin) -- runs ONLY the real-corpus acceptance")
_ap.add_argument("--old-workers", type=int, default=16,
                 help="[9]: processes the OLD per-pair loop is sharded over for the full-n comparison (0 = skip it)")
_ap.add_argument("--subsamples", type=int, default=4,
                 help="[9]: random 3,000-row real subsamples compared with the literal frozen find_cluster")
ARGS = _ap.parse_args()

TMP = Path(tempfile.mkdtemp(prefix="find_cluster_off_loop_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_DB = _LIVE_DATA / "memory" / "nascence.db"
_LIVE_JSON = [_LIVE_DATA / "position.json", _LIVE_DATA / "room_state.json"]
_LIVE_DB_FILES = [Path(str(_LIVE_DB) + s) for s in ("", "-wal", "-shm")]


def _md5(p: Path) -> str:
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()
    except OSError:
        return ""


def _stat(p: Path):
    try:
        st = p.stat()
        return (st.st_size, st.st_mtime_ns)
    except OSError:
        return None


_before_md5 = {p: _md5(p) for p in _LIVE_JSON}
_before_stat = {p: _stat(p) for p in _LIVE_DB_FILES}

# ── write audit: this process must never attempt a write under a live data dir ─────────────────────────────────
_WATCH = [str(_LIVE_DATA).lower(), str(ROOT / "data").lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move",
                 "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []
LIVE_RO_OPENS: list = []        # the deliberate mode=ro sqlite URI opens (real-row sample); nothing else is allowed


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _sqlite_target(db):
    """(filesystem path, is a mode=ro URI) for a sqlite3.connect() argument."""
    s = os.fsdecode(db) if isinstance(db, (bytes, os.PathLike)) else str(db)
    if s.startswith("file:"):
        u = urllib.parse.urlparse(s)
        return urllib.request.url2pathname(u.path), "ro" in urllib.parse.parse_qs(u.query).get("mode", [])
    return s, False


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event == "sqlite3.connect":
            path, ro = _sqlite_target(args[0])
            if _under_watch(path):
                (LIVE_RO_OPENS if ro else LIVE_WRITE_ATTEMPTS).append(("sqlite3.connect", str(args[0]), "ro" if ro else "rw"))
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

from core import chapters as C          # noqa: E402
C.RETIRE_THEME_CHAPTERS = False   # J-4338
from core.memory import store as S      # noqa: E402

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# ── [0] module-resolution proof (F-1285) + redirect ─────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (C, S):
    print(f"    {_m.__name__:22s} -> {_m.__file__}")
    check(Path(_m.__file__).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
S.DB_PATH = TMP / "unused_until_make_db.db"
check(not str(S.DB_PATH).lower().startswith(str(_LIVE_DATA).lower()), "store.DB_PATH redirected out of the live data dir before any run")
check(C.SEED_SCAN_TILE == 768 and C.SEED_SCAN_GUARD == 4.0, f"SEED_SCAN_TILE = {C.SEED_SCAN_TILE}, SEED_SCAN_GUARD = {C.SEED_SCAN_GUARD}")


# ── capture the chapters logger (never printed, never propagated) ────────────────────────────────────────────────
class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.msgs: list[str] = []         # cleared by the guard tests
        self.all: list[str] = []          # never cleared

    def emit(self, record):
        m = f"{record.levelname}:{record.getMessage()}"
        self.msgs.append(m)
        self.all.append(m)


_cap = _Cap()
C.logger.addHandler(_cap)
C.logger.setLevel(logging.DEBUG)
C.logger.propagate = False

# ── the frozen reference: the base commit's find_cluster, verbatim ───────────────────────────────────────────────
BASE_SRC = r'''
def find_cluster(level: int = 0) -> list[dict] | None:
    """The largest cooled, chapterable cluster at this level, or None.
    Greedy: the candidate with the most neighbours seeds the cluster. Read-only."""
    from core.memory.store import _connect, _blob_to_vec, _cosine
    try:
        with _connect() as conn:
            rows = _candidates(conn, level)
        min_members = MIN_MEMBERS if level == 0 else MIN_MEMBERS_META
        if len(rows) < min_members:
            return None
        vecs = []
        for r in rows:
            v = _blob_to_vec(r["embedding"])
            if v is not None:
                vecs.append((r, v))
        if len(vecs) < min_members:
            return None
        # seed = densest point (most neighbours over the similarity bar)
        best_seed, best_n = None, -1
        for i, (_, v) in enumerate(vecs):
            n = sum(1 for _, w in vecs if _cosine(v, w) >= CLUSTER_SIM)
            if n > best_n:
                best_seed, best_n = v, n
        cluster = [{"id": r["fragment_id"], "content": r["content"] or "",
                    "ts": float(r["timestamp"]), "importance": float(r["importance"])}
                   for r, v in vecs if _cosine(best_seed, v) >= CLUSTER_SIM]
        if len(cluster) < min_members:
            return None
        if level == 0:
            # Bound the chapter to the ERA of intensity. Members outside the era
            # (the theme's living baseline tail) stay unchaptered — they are the
            # present, not the period.
            win = _era_window([m["ts"] for m in cluster])
            if win is None:
                logger.info("[chapters] cluster of %d found, but its era has not ended — "
                            "the present is lived, not narrated", len(cluster))
                return None
            cluster = [m for m in cluster if win[0] <= m["ts"] < win[1]]
            if len(cluster) < min_members:
                return None
        else:
            if not _cooled([m["ts"] for m in cluster]):
                logger.info("[chapters] level-%d cluster still warm", level)
                return None
        return cluster
    except Exception as exc:
        logger.debug("[chapters] find_cluster failed (non-fatal): %s", exc)
        return None
'''
BASE_COMMIT = "5a66504"
REF_NS = dict(vars(C))            # the reference runs against THIS module's helpers/constants (proven unchanged in [1])
exec(compile(BASE_SRC, f"<{BASE_COMMIT} core/chapters.py find_cluster>", "exec"), REF_NS)
ref_find_cluster = REF_NS["find_cluster"]
ORIG_ERA = C._era_window

# ── [1] the algorithm is untouched, by AST ──────────────────────────────────────────────────────────────────────
print("\n[1] AST proof: only the blocking of the count changed")


def _git_base_source():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE_COMMIT}:core/chapters.py"],
                             capture_output=True, timeout=30)
        return out.stdout.decode("utf-8") if out.returncode == 0 else None
    except Exception:
        return None


def _funcs(tree):
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _assigned(tree):
    """{name: dumped value} for every top-level `NAME = value` / `NAME: T = value`."""
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = ast.dump(n.value)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            out[n.target.id] = ast.dump(n.value)
    return out


def _seed_loop_index(try_node):
    for i, st in enumerate(try_node.body):
        if (isinstance(st, ast.For) and isinstance(st.iter, ast.Call)
                and getattr(st.iter.func, "id", "") == "enumerate"):
            return i
    raise AssertionError("seed loop not found")


class _Rename(ast.NodeTransformer):
    def __init__(self, old, new):
        self.old, self.new = old, new

    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id=self.new, ctx=node.ctx), node) if node.id == self.old else node


cur_src = Path(C.__file__).read_text(encoding="utf-8")
cur_tree = ast.parse(cur_src)
cur_f = _funcs(cur_tree)
old_fn = ast.parse(BASE_SRC).body[0]
new_fn = cur_f["_find_cluster_steps"]
old_try = next(n for n in old_fn.body if isinstance(n, ast.Try))
new_try = next(n for n in new_fn.body if isinstance(n, ast.Try))
def _rule_loop_index(try_node):
    for i, st in enumerate(try_node.body):
        if isinstance(st, ast.For) and any(isinstance(x, ast.If) and ast.unparse(x.test) == "n > best_n" for x in st.body):
            return i
    raise AssertionError("first-maximum seed loop not found")


io_, in_ = _seed_loop_index(old_try), _rule_loop_index(new_try)
dump = lambda nodes: [ast.dump(x) for x in nodes]                              # noqa: E731
check(dump(old_try.body[io_ + 1:]) == dump(new_try.body[in_ + 1:]),
      f"every statement AFTER the seed loop is AST-identical to the base ({len(old_try.body) - io_ - 1} statements)")
_counts_stmt = ast.dump(ast.parse("def _g():\n    counts = yield from _neighbour_counts(vecs, level)").body[0].body[0])
_added = [s for s in new_try.body[:in_]
          if (isinstance(s, ast.Expr) and "seed scan over" in ast.unparse(s))
          or (isinstance(s, ast.Assign) and ast.dump(s) == _counts_stmt)]
check(len(_added) == 2,
      "exactly two statements added before the seed rule (the scan log line and `counts = yield from _neighbour_counts(vecs, level)`)")
check(dump(old_try.body[:io_]) == dump([s for s in new_try.body[:in_] if s not in _added]),
      "every statement BEFORE the seed rule (candidate fetch, vector build, size guards, `best_seed, best_n = None, -1`) is "
      "AST-identical to the base, apart from those two")
check(dump(old_try.handlers) == dump(new_try.handlers), "the except handler is AST-identical")
check(ast.dump(old_fn.body[1]) == ast.dump(new_fn.body[1]), "the function-local import line is AST-identical")
old_loop, new_loop = old_try.body[io_], new_try.body[in_]
check(ast.dump(old_loop.body[1]) == ast.dump(new_loop.body[-1]) and len(new_loop.body) == 1,
      "the `if n > best_n: best_seed, best_n = v, n` (first maximum wins) rule is AST-identical and is the loop's whole body")
check(ast.dump(new_loop.target) == ast.dump(ast.parse("for (_, v), n in x: pass").body[0].target)
      and ast.unparse(new_loop.iter) == "zip(vecs, counts)",
      "that rule walks the candidates in their original order against their own count (`for (_, v), n in zip(vecs, counts)`)")
_nc = _funcs(cur_tree)["_neighbour_counts"]
check(any(ast.unparse(x) == "_cosine(vs[i0 + r], vs[j0 + c]) >= CLUSTER_SIM" for x in ast.walk(_nc)),
      "the guard band re-decides a pair with the old loop's own predicate, `_cosine(v, w) >= CLUSTER_SIM`, on the original vectors")
check(sum(isinstance(x, ast.Yield) for x in ast.walk(_nc)) == 1,
      "_neighbour_counts has exactly one yield, once per tile, so it is still a cooperative generator")

base_full = _git_base_source()
if base_full is not None:
    base_tree = ast.parse(base_full)
    base_f = _funcs(base_tree)
    check(ast.get_source_segment(base_full, base_f["find_cluster"]).strip() == BASE_SRC.strip(),
          f"the embedded frozen find_cluster equals `git show {BASE_COMMIT}:core/chapters.py`")
    for name in ("_candidates", "_cooled", "_era_window", "_existing_chapter_vecs", "recall_chapter"):
        check(ast.dump(base_f[name]) == ast.dump(cur_f[name]), f"{name} is AST-identical to the base")
    # J-3009 (F-3712): _sample's exemplar cut moved to a word boundary -- the ONLY change (the plain [:200] cut -> _cut_at_word)
    check(ast.unparse(cur_f["_sample"]).replace("_cut_at_word(m['content'])", "m['content'][:200]") == ast.unparse(base_f["_sample"]),
          "_sample is identical to the base apart from J-3009's word-boundary exemplar cut (_cut_at_word(m['content']) for m['content'][:200])")
    ba, ca = _assigned(base_tree), _assigned(cur_tree)
    check(all(ca.get(k) == v for k, v in ba.items()), f"all {len(ba)} base module-level assignments are unchanged (CLUSTER_SIM, MIN_MEMBERS, ...)")
    new_names = (set(cur_f) | set(ca)) - (set(base_f) | set(ba))
    _later_names = {"_cluster_span", "_author_system_prompt", "_parse_member_span", "_SPAN_RE",
                    "RETIRE_THEME_CHAPTERS"}   # J-4052: J-3010 and later, additive; J-4338 (D-0867): the formation retirement flag
    _j3009_names = {"COPY_WINDOW", "COPY_CAP", "MAX_SENTENCES", "EXEMPLAR_CHARS", "_cut_at_word", "_WORD_RE", "_SENT_SPLIT_RE",
                    "_PAST_I", "_PRESENT_I", "_I_VERB_RE", "_EMBEDDED_AM_RE", "_words", "_copy_share", "_tense_counts",
                    "_sentence_count", "_output_reject"}                     # J-3009 (F-3712): the chapter-output guards, additive
    check(new_names - _j3009_names - _later_names == {"SEED_SCAN_TILE", "SEED_SCAN_GUARD", "SEED_SCAN_CHECKPOINT_EVERY", "_SCANNING", "_find_cluster_steps",
                        "_neighbour_counts", "find_cluster_async"} and _j3009_names <= new_names,
          f"the only new top-level names are the additive ones: {sorted(new_names)}")

    class _Unawait(ast.NodeTransformer):                                         # await find_cluster_async(x) -> find_cluster(x)
        def visit_Await(self, node):
            self.generic_visit(node)
            call = node.value
            if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "find_cluster_async":
                call.func = ast.copy_location(ast.Name(id="find_cluster", ctx=ast.Load()), call.func)
                return ast.copy_location(call, node)
            return node
    def _drop_j3009_guard(fn):                                                   # J-3009: remove `why = _output_reject(...)` and the `if why:` that follows
        body, i = [], 0
        while i < len(fn.body):
            st = fn.body[i]
            if (isinstance(st, ast.Assign) and isinstance(st.value, ast.Call) and getattr(st.value.func, "id", "") == "_output_reject"
                    and i + 1 < len(fn.body) and isinstance(fn.body[i + 1], ast.If) and ast.unparse(fn.body[i + 1].test) == "why"):
                i += 2
                continue
            body.append(st)
            i += 1
        fn.body = body
        return fn
    # J-4052: try_form_chapter has since taken three more reviewed, unrelated edits after the base commit -- J-3010
    # (`t0, t1 = _cluster_span(cluster, level)` for the two min/max lines), `sys_p = _author_system_prompt()` (the prompt moved
    # into a function) and extra kwargs on `_nq.observe(...)`. Those lines are normalised out of BOTH sides so the check
    # still pins what J-1744 cares about: the find_cluster call and everything else are the base's.
    import re as _re
    def _norm_tfc(fn):
        out = []
        _skip_next = False
        for ln in ast.unparse(fn).splitlines():
            t = ln.strip()
            if _skip_next:                      # J-4338 (D-0867): the `return None` under the retirement flag
                _skip_next = False
                continue
            if t == "if RETIRE_THEME_CHAPTERS:":
                _skip_next = True
                continue
            if t.startswith(("t0 = ", "t1 = ", "t0, t1 = ", "sys_p = ")):
                continue
            out.append(_re.sub(r"(_nq\.observe\(call_json, base_urls, 'chapter', body)[^)]*\)", r")", ln))
        return out
    check(_norm_tfc(_drop_j3009_guard(_Unawait().visit(cur_f["try_form_chapter"]))) == _norm_tfc(base_f["try_form_chapter"]),
          "try_form_chapter differs from the base by `await find_cluster_async(lv)` for `find_cluster(lv)`, J-3009's output guard, "
          "and (normalised out) J-3010's span line, the prompt-function line and the observe kwargs")
else:
    print("    (git base unavailable: the base-commit cross-checks of the helpers, constants and try_form_chapter are skipped)")

_THREAD_ATTRS = {"to_thread", "run_in_executor", "Thread", "ThreadPoolExecutor", "ProcessPoolExecutor", "Process"}
_THREAD_MODS = {"threading", "concurrent", "multiprocessing", "_thread"}
_uses = [n for n in ast.walk(cur_tree)
         if (isinstance(n, ast.Attribute) and n.attr in _THREAD_ATTRS)
         or (isinstance(n, ast.Import) and any(a.name.split(".")[0] in _THREAD_MODS for a in n.names))
         or (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in _THREAD_MODS)]
check(not _uses, "core/chapters.py uses no thread / executor / process construct (it all runs on the loop thread, "
                 "so the DB connection and the vectors stay single-thread-owned)")

# ── deterministic synthetic data ─────────────────────────────────────────────────────────────────────────────────
DAY = 86400.0
NOW = time.time()
DIM = 384
_ID = [0]


def _orth(rng, k):
    q, _ = np.linalg.qr(rng.standard_normal((DIM, k)))
    return q.T.astype(np.float64)


def _unit(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def _around(rng, center, n, c_lo, c_hi):
    """n unit float32 vectors whose cosine to `center` is drawn uniformly from [c_lo, c_hi]."""
    u = rng.standard_normal((n, DIM))
    u -= np.outer(u @ center, center)
    u = _unit(u)
    c = rng.uniform(c_lo, c_hi, n)[:, None]
    return _unit(c * center + np.sqrt(1.0 - c * c) * u).astype(np.float32)


def _noise(rng, n):
    return _unit(rng.standard_normal((n, DIM))).astype(np.float32)


def _row(emb, ts, origin="inner_thought", chapter_id=None, chapter_level=0, importance=0.5):
    _ID[0] += 1
    return (f"t{_ID[0]:06d}", f"synthetic fragment {_ID[0]}", "episodic", 0.5, float(ts), "",
            None if emb is None else np.asarray(emb, dtype=np.float32).tobytes(),
            origin, float(importance), chapter_id, int(chapter_level))


DBS: dict = {}
_DB_SEQ = [0]


def make_db(name, rows):
    """A fresh temp store (its own file, even if `name` is reused) with the REAL schema (store.init_db) holding `rows`;
    DB_PATH is pointed at it and use_db(name) returns to it."""
    _DB_SEQ[0] += 1
    DBS[name] = S.DB_PATH = TMP / f"{name}_{_DB_SEQ[0]}.db"
    S.init_db()
    with S._connect() as conn:
        conn.executemany(
            "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, embedding, "
            "origin, importance, chapter_id, chapter_level) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
    return S.DB_PATH


def use_db(name):
    S.DB_PATH = DBS[name]


def candidate_rows(level=0):
    with S._connect() as conn:
        return C._candidates(conn, level)


def oracle(rows, ok_gap=1e-6):
    """An independent float64 all-pairs matrix definition of the rule. None if some pair sits within ok_gap of the bar."""
    V = np.stack([S._blob_to_vec(r["embedding"]) for r in rows]).astype(np.float64)
    G = V @ V.T
    if float(np.abs(G - C.CLUSTER_SIM).min()) < ok_gap:
        return None
    counts = (G >= C.CLUSTER_SIM).sum(axis=1)
    seed = int(np.argmax(counts))                                                  # argmax = FIRST maximum
    return [rows[i]["fragment_id"] for i in np.nonzero(G[seed] >= C.CLUSTER_SIM)[0]], seed, int(counts[seed])


def build_d1(seed):
    """three clusters of different size/era + noise + four kinds of decoys that _candidates must exclude."""
    rng = np.random.default_rng(seed)
    cen = _orth(rng, 3)
    rows = []
    for k, (n, t0, t1) in enumerate([(320, NOW - 40 * DAY, NOW - 33 * DAY), (220, NOW - 20 * DAY, NOW - 19 * DAY),
                                     (140, NOW - 60 * DAY, NOW - 3 * DAY)]):
        for e, t, imp in zip(_around(rng, cen[k], n, 0.66, 0.97), rng.uniform(t0, t1, n), rng.uniform(0.3, 0.9, n)):
            rows.append(_row(e, t, importance=imp))
    for e, t in zip(_noise(rng, 100), rng.uniform(NOW - 50 * DAY, NOW - 3 * DAY, 100)):
        rows.append(_row(e, t))
    decoys = []
    dec = _around(rng, cen[0], 30, 0.90, 0.99)
    for kw in (dict(chapter_id="chap-already"), dict(origin="reading"), dict(no_emb=True), dict(young=True)):
        for e in dec:
            r = _row(None if kw.get("no_emb") else e, NOW - 3600 if kw.get("young") else NOW - 36 * DAY,
                     origin=kw.get("origin", "inner_thought"), chapter_id=kw.get("chapter_id"))
            rows.append(r)
            decoys.append(r[0])
    return rows, decoys


def build_tie(size_a, size_b, b_first=False):
    rng = np.random.default_rng(202)
    cen = _orth(rng, 2)
    A, B = _around(rng, cen[0], size_a, 0.95, 0.99), _around(rng, cen[1], size_b, 0.95, 0.99)
    ra = [_row(e, t) for e, t in zip(A, rng.uniform(NOW - 30 * DAY, NOW - 25 * DAY, size_a))]
    rb = [_row(e, t) for e, t in zip(B, rng.uniform(NOW - 30 * DAY, NOW - 25 * DAY, size_b))]
    return (rb + ra) if b_first else (ra + rb), {r[0] for r in ra}, {r[0] for r in rb}


def build_threshold():
    """a seed and 300 members whose cosine to it is 0.70 + linspace(-3e-7, 3e-7): float32 rounding decides each one."""
    rng = np.random.default_rng(303)
    s = _unit(rng.standard_normal(DIM))
    seed_row = _row(s.astype(np.float32), NOW - 30 * DAY)
    rows = [seed_row]
    for d in np.linspace(-3e-7, 3e-7, 300):
        c = C.CLUSTER_SIM + d
        u = rng.standard_normal(DIM)
        u -= s * (u @ s)
        u = _unit(u)
        rows.append(_row((c * s + np.sqrt(1 - c * c) * u).astype(np.float32), rng.uniform(NOW - 32 * DAY, NOW - 28 * DAY)))
    return rows, seed_row[0]


def build_bar(n=380):
    """n vectors whose EVERY pairwise cosine is CLUSTER_SIM up to float32 rounding (sqrt(.7) * c + sqrt(.3) * u_i, with the u_i orthonormal and
    orthogonal to c): all n^2 decisions sit on the bar -- the worst case for sdot-vs-sgemm."""
    rng = np.random.default_rng(707)
    q, _ = np.linalg.qr(rng.standard_normal((DIM, n + 1)))
    c, U = q[:, 0], q[:, 1:].T
    X = (np.sqrt(C.CLUSTER_SIM) * c + np.sqrt(1.0 - C.CLUSTER_SIM) * U).astype(np.float32)
    return [_row(x, t) for x, t in zip(X, rng.uniform(NOW - 30 * DAY, NOW - 26 * DAY, n))]


def _drive(gen):
    """run a generator to completion (the sync driver): (its return value, number of yields)."""
    y = 0
    while True:
        try:
            next(gen)
        except StopIteration as done:
            return done.value, y
        y += 1


def build_h(n_noise=1000, n_cluster=300):
    """the heartbeat / cost / guard dataset: n = 1,300 -> ~2.4 s of scan, with one real dense cluster in an ended era."""
    rng = np.random.default_rng(505)
    cen = _orth(rng, 1)
    rows = [_row(e, t) for e, t in zip(_noise(rng, n_noise), rng.uniform(NOW - 60 * DAY, NOW - 5 * DAY, n_noise))]
    rows += [_row(e, t, importance=i) for e, t, i in zip(_around(rng, cen[0], n_cluster, 0.80, 0.97),
                                                         rng.uniform(NOW - 45 * DAY, NOW - 38 * DAY, n_cluster),
                                                         rng.uniform(0.3, 0.9, n_cluster))]
    return rows


@contextlib.contextmanager
def _patched(**kw):
    """set module constants on C and on the reference namespace together, restore on exit."""
    saved = [(C, k, getattr(C, k)) for k in kw] + [(REF_NS, k, REF_NS[k]) for k in kw if k in REF_NS]
    try:
        for k, v in kw.items():
            setattr(C, k, v)
            if k in REF_NS:
                REF_NS[k] = v
        yield
    finally:
        for obj, k, v in saved:
            if obj is REF_NS:
                REF_NS[k] = v
            else:
                setattr(obj, k, v)


async def run_drivers(level=0, mode="real", sync_too=True, **patch):
    """frozen base find_cluster vs find_cluster (sync driver) vs find_cluster_async, each with its own _era_window recorder.
    mode 'open' widens the era window to everything so the whole pre-era cluster is what comes back."""
    out, recs, walls = {}, {"ref": [], "sync": [], "async": []}, {}

    def spy(rec):
        def _s(ts):
            rec.append(list(ts))
            return (0.0, float("inf")) if mode == "open" else ORIG_ERA(ts)
        return _s

    with _patched(**patch):
        try:
            REF_NS["_era_window"] = spy(recs["ref"])
            t = time.perf_counter()
            out["ref"] = ref_find_cluster(level)
            walls["ref"] = time.perf_counter() - t
            if sync_too:
                C._era_window = spy(recs["sync"])
                t = time.perf_counter()
                out["sync"] = C.find_cluster(level)
                walls["sync"] = time.perf_counter() - t
            C._era_window = spy(recs["async"])
            t = time.perf_counter()
            out["async"] = await C.find_cluster_async(level)
            walls["async"] = time.perf_counter() - t
        finally:
            C._era_window = ORIG_ERA
            REF_NS["_era_window"] = ORIG_ERA
    return out, recs, walls


def compare(label, out, recs, must_find=True):
    check(out["ref"] == out["async"], f"{label}: async output == base output (ids, content, ts, importance, ORDER)")
    if "sync" in out:
        check(out["ref"] == out["sync"], f"{label}: sync driver output == base output")
    check(recs["ref"] == recs["async"] and (("sync" not in out) or recs["ref"] == recs["sync"]),
          f"{label}: pre-era membership (the timestamps handed to _era_window) is identical")
    if must_find:
        check(out["ref"] is not None and len(out["ref"]) > 0, f"{label}: non-vacuous, the base found a cluster of {len(out['ref'] or [])}")
    return [m["id"] for m in (out["ref"] or [])]


def walls_line(walls, recs):
    return ("        walls: " + ", ".join(f"{k}={v:.2f}s" for k, v in walls.items())
            + f"; pre-era cluster {len(recs['ref'][0]) if recs['ref'] else 0}")


# ── [2] equivalence ─────────────────────────────────────────────────────────────────────────────────────────────
async def part_equivalence():
    print("\n[2] equivalence with the frozen base-commit find_cluster")
    # D1 -- clusters, noise, decoys (first seed whose data keeps every pair >= 1e-6 from the bar, so the float64 oracle is valid)
    for seed in range(101, 121):
        rows, decoys = build_d1(seed)
        make_db("d1", rows)
        cand = candidate_rows(0)
        orc = oracle(cand)
        if orc is not None:
            break
    check(len(cand) == 780 and not (set(decoys) & {r["fragment_id"] for r in cand}),
          f"D1 (rng seed {seed}): {len(cand)} candidates from {len(rows)} rows; none of the {len(decoys)} decoys (chapter_id set / other "
          f"origin / no embedding / younger than 48 h) is a candidate")
    check(orc is not None, "D1: no pair lies within 1e-6 of CLUSTER_SIM, so the float64 matrix oracle is valid")
    for mode in ("real", "open"):
        out, recs, walls = await run_drivers(0, mode)
        ids = compare(f"D1/{mode}-era", out, recs)
        print(walls_line(walls, recs))
        check(not (set(decoys) & set(ids)), f"D1/{mode}-era: no decoy row is in the result")
        if mode == "open" and orc:
            check(ids == orc[0], f"D1/open-era: result == the independent float64 matrix oracle (seed row {orc[1]}, "
                                 f"{orc[2]} neighbours, {len(orc[0])} members, same order)")
    # D2 -- exact ties: the FIRST maximum wins
    for label, (a, b, b_first) in {"200 vs 200 (tie), A first": (200, 200, False), "200 vs 201 (B has one more)": (200, 201, False),
                                   "200 vs 200 (tie), B first": (200, 200, True)}.items():
        rows, A, B = build_tie(a, b, b_first)
        make_db("tie", rows)
        cand = candidate_rows(0)
        orc = oracle(cand)
        out, recs, walls = await run_drivers(0, "open")
        ids = compare(f"D2 {label}", out, recs)
        if a == b:
            expect_set, why = (A if cand[0]["fragment_id"] in A else B), "the cluster of the FIRST candidate row"
        else:
            expect_set, why = B, "the strictly larger cluster"
        check(set(ids) == expect_set and orc is not None and ids == orc[0],
              f"D2 {label}: the winner is {why} ({'A' if expect_set == A else 'B'}, {len(ids)} members), equal to the oracle's first-argmax")
    # D3 -- 300 pairs straddling the bar
    rows, seed_id = build_threshold()
    make_db("thr", rows)
    cand = candidate_rows(0)
    seed_row = next(r for r in cand if r["fragment_id"] == seed_id)
    dots = [S._cosine(S._blob_to_vec(seed_row["embedding"]), S._blob_to_vec(r["embedding"])) for r in cand if r is not seed_row]
    near = sum(1 for d in dots if abs(d - C.CLUSTER_SIM) < 1e-6)
    passing = sum(1 for d in dots if d >= C.CLUSTER_SIM)
    check(near >= 100 and 0 < passing < len(dots),
          f"D3: {near} of {len(dots)} pairs lie within 1e-6 of CLUSTER_SIM and {passing} of them pass the bar in float32")
    out, recs, walls = await run_drivers(0, "open")
    ids = compare("D3 threshold", out, recs)
    check(len(ids) == passing + 1 and seed_id in ids,
          f"D3: membership = the seed + exactly the {passing} float32 pairs >= the bar (independent per-pair recount)")
    # D3b -- J-1744: EVERY pairwise cosine sits on the bar (0.70 +- float32 rounding): the worst case for sdot-vs-sgemm. Mutation: with the
    # guard band switched off (SEED_SCAN_GUARD = 0: a plain float32 blocked product) the per-row counts must DIFFER from the base's.
    rows = build_bar()
    make_db("bar", rows)
    cand = candidate_rows(0)
    vs = [S._blob_to_vec(r["embedding"]) for r in cand]
    G = np.stack(vs) @ np.stack(vs).T
    D = np.array([[S._cosine(a, b) for b in vs] for a in vs])
    on_bar = int((np.abs(D - C.CLUSTER_SIM) < 1e-6).sum())
    plain_flips = int(((G.astype(np.float64) >= C.CLUSTER_SIM) != (D >= C.CLUSTER_SIM)).sum())
    check(on_bar > 0.9 * len(vs) ** 2, f"D3b: {on_bar} of {len(vs) ** 2} ordered pairs lie within 1e-6 of CLUSTER_SIM")
    out, recs, walls = await run_drivers(0, "open")
    compare("D3b all pairs on the bar", out, recs)
    base_counts = [sum(1 for w in vs if S._cosine(v, w) >= C.CLUSTER_SIM) for v in vs]
    new_counts, _ = _drive(C._neighbour_counts([(None, v) for v in vs], 0))
    check(new_counts == base_counts and len(set(base_counts)) > 20,
          f"D3b: the new per-row counts equal the old per-pair loop's for all {len(vs)} rows ({len(set(base_counts))} distinct values, "
          f"{min(base_counts)}..{max(base_counts)}), where a plain float32 blocked product would have flipped {plain_flips} of the {len(vs) ** 2} pair decisions")
    with _patched(SEED_SCAN_GUARD=0.0):
        plain_counts, _ = _drive(C._neighbour_counts([(None, v) for v in vs], 0))
    check(plain_counts != base_counts,
          f"D3b mutation: with the guard band OFF the counts differ from the base in {sum(a != b for a, b in zip(plain_counts, base_counts))} of {len(vs)} rows "
          f"-- the guard band is what makes the result identical, and this dataset exercises it")
    # D4 -- levels 1 and 2 (chapters of chapters, the _cooled branch)
    rng = np.random.default_rng(404)
    cen = _orth(rng, 1)
    cool = [_row(e, t, origin="chapter", chapter_level=1) for e, t in
            zip(_around(rng, cen[0], 12, 0.90, 0.98), np.sort(rng.uniform(NOW - 90 * DAY, NOW - 40 * DAY, 12)))]
    make_db("lv_cool", cool)
    out, recs, _ = await run_drivers(1, "real")
    compare("D4 level 1 cooled", out, recs, must_find=False)
    check(out["ref"] is not None and len(out["ref"]) == 12, f"D4 level 1: 12 cooled chapters make an era ({len(out['ref'] or [])} returned by the base)")
    out2, _, _ = await run_drivers(2, "real")
    check(out2["ref"] is None and out2["async"] is None and out2["sync"] is None, "D4 level 2: nothing to consolidate -> None from all three")
    warm = [_row(e, t, origin="chapter", chapter_level=1) for e, t in
            zip(_around(rng, cen[0], 12, 0.90, 0.98), np.sort(rng.uniform(NOW - 5 * DAY, NOW - 3 * DAY, 12)))]
    make_db("lv_warm", warm)
    out, recs, _ = await run_drivers(1, "real")
    compare("D4 level 1 warm", out, recs, must_find=False)
    check(out["ref"] is None and out["async"] is None and out["sync"] is None, "D4 level 1 warm: still-warm chapters -> None from all three")
    # D5 -- boundaries: empty, below MIN_MEMBERS, exactly MIN_MEMBERS
    make_db("empty", [])
    out, recs, _ = await run_drivers(0, "real")
    check(out["ref"] is None and out["async"] is None and out["sync"] is None, "D5 empty store -> None from all three")
    rng = np.random.default_rng(606)
    cen = _orth(rng, 1)
    for n_rows, expect in ((C.MIN_MEMBERS - 1, None), (C.MIN_MEMBERS, C.MIN_MEMBERS)):
        make_db(f"b{n_rows}", [_row(e, t) for e, t in zip(_around(rng, cen[0], n_rows, 0.95, 0.99),
                                                          rng.uniform(NOW - 30 * DAY, NOW - 26 * DAY, n_rows))])
        out, recs, _ = await run_drivers(0, "open")
        compare(f"D5 {n_rows} mutual neighbours", out, recs, must_find=False)
        got = None if out["ref"] is None else len(out["ref"])
        check(got == expect, f"D5 {n_rows} rows (MIN_MEMBERS={C.MIN_MEMBERS}): the base gives {got}, expected {expect}")
    # D6 -- a read-only sample of REAL rows
    await real_sample()


async def real_sample(limit=2400):
    if ARGS.no_live_sample:
        print("    D6 real rows: skipped (--no-live-sample)")
        return
    wal, shm = Path(str(_LIVE_DB) + "-wal"), Path(str(_LIVE_DB) + "-shm")
    if not (_LIVE_DB.exists() and wal.exists() and shm.exists()):
        print("    D6 real rows: skipped -- no -wal/-shm beside the live DB (Du not holding it open); a mode=ro open of a WAL "
              "database could create them, so it is not touched")
        return
    con = sqlite3.connect(_LIVE_DB.as_uri() + "?mode=ro", uri=True, timeout=5.0)          # ONE read-only open, the SAME bounded SELECT twice
    times = []
    try:
        con.execute("PRAGMA query_only=ON")
        con.row_factory = sqlite3.Row
        for _ in range(2):                                                               # 1st = cold cache, 2nd = warm (what a running Du sees)
            t0 = time.perf_counter()
            got = con.execute(
                "SELECT fragment_id, content, timestamp, importance, embedding, origin FROM memory_fragments "
                "WHERE origin IN (?,?,?) AND chapter_id IS NULL AND embedding IS NOT NULL AND timestamp < ? LIMIT ?",
                (*C.CHAPTERABLE_ORIGINS, time.time() - C.MIN_AGE_S, limit)).fetchall()
            times.append(time.perf_counter() - t0)
    finally:
        con.close()
    by_origin: dict = {}
    for r in got:
        by_origin[r["origin"]] = by_origin.get(r["origin"], 0) + 1
    print(f"    D6 real rows: {len(got)} candidate rows read (mode=ro, LIMIT {limit}, twice) in {times[0] * 1000:.0f} ms cold / {times[1] * 1000:.0f} ms warm; "
          f"by origin {by_origin}; the warm time extrapolated linearly to the 33.6k-row production fetch = ~{times[1] / max(1, len(got)) * 33600 * 1000:.0f} ms "
          f"(the one synchronous stretch left in find_cluster: a single loop stall per sleep)")
    rows = [(r["fragment_id"], r["content"], "episodic", 0.5, float(r["timestamp"]), "", bytes(r["embedding"]), r["origin"],
             float(r["importance"] if r["importance"] is not None else 0.5), None, 0) for r in got]
    make_db("real", rows)
    # a 2.4k sample holds far fewer than MIN_MEMBERS=40 of one theme; lower the bar for BOTH sides so the comparison is not vacuous
    out, recs, walls = await run_drivers(0, "real", sync_too=False, MIN_MEMBERS=8)
    print(walls_line(walls, recs) + f" (real era rule -> {None if out['ref'] is None else len(out['ref'])} members)")
    check(out["ref"] == out["async"], "D6 real rows: async output == base output")
    check(recs["ref"] == recs["async"] and len(recs["ref"]) == 1 and len(recs["ref"][0]) >= 8,
          f"D6 real rows: non-vacuous -- a real pre-era cluster of {len(recs['ref'][0]) if recs['ref'] else 0} members, "
          f"identical timestamps in the same order")


# ── shared timing helpers ────────────────────────────────────────────────────────────────────────────────────────
async def _heartbeat(stop, lags, period=0.05):
    last = time.perf_counter()
    while not stop.is_set():
        await asyncio.sleep(period)
        now = time.perf_counter()
        lags.append((now - last) - period)
        last = now


async def heartbeat_run(work):
    stop, lags = asyncio.Event(), []
    hb = asyncio.create_task(_heartbeat(stop, lags))
    await asyncio.sleep(0.3)
    t0 = time.perf_counter()
    res = await work()
    wall = time.perf_counter() - t0
    await asyncio.sleep(0.3)
    stop.set()
    await hb
    return res, wall, lags


def lag_line(label, wall, lags):
    ms = sorted(x * 1000 for x in lags)
    return (f"{label:34s} scan={wall:5.2f}s  ticks={len(ms):3d}  worst tick lag={ms[-1]:8.1f} ms  "
            f"p99={ms[max(0, int(len(ms) * 0.99) - 1)]:7.1f} ms  median={statistics.median(ms):5.1f} ms")


# ── [3] heartbeat, [4] cost ─────────────────────────────────────────────────────────────────────────────────────
async def part_heartbeat_and_cost():
    print("\n[3] heartbeat: a coroutine ticking every 50 ms while the scan runs (n = 1,300 -> ~2.4 s; production n = 33,589 -> ~1,480 s)")
    make_db("h", build_h())
    n = len(candidate_rows(0))
    t0 = time.perf_counter()
    expected = ref_find_cluster(0)                                                  # the frozen base, on the loop thread
    t_ref = time.perf_counter() - t0
    check(expected is not None and len(expected) > 40, f"H: n={n}; the base finds a cluster of {len(expected or [])}")

    async def blocking():
        return ref_find_cluster(0)                                                  # the OLD per-pair loop (frozen), ON the loop thread: the control that starves it

    async def cooperative():
        return await C.find_cluster_async(0)

    res_a, wall_a, lags_a = await heartbeat_run(blocking)
    res_b, wall_b, lags_b = await heartbeat_run(cooperative)
    print("    " + lag_line("(a) OLD loop, blocking (control)", wall_a, lags_a))
    print("    " + lag_line("(b) NEW find_cluster_async, n=1,300", wall_b, lags_b))
    worst_a, worst_b = max(lags_a), max(lags_b)
    check(worst_a > 1.0, f"(a) control: the old blocking scan really starves the loop (worst tick lag {worst_a * 1000:.0f} ms ~ the scan itself)")
    check(worst_b < 0.25, f"(b) target: worst tick lag {worst_b * 1000:.1f} ms < 250 ms (was {worst_a * 1000:.0f} ms)")
    check(len(lags_b) >= 0.6 * (wall_b + 0.6) / 0.05, f"(b) the heartbeat kept ticking: {len(lags_b)} ticks in {wall_b + 0.6:.1f} s (~{(wall_b + 0.6) / 0.05:.0f} expected)")
    check(res_a == expected and res_b == expected, f"(a) and (b) return the base's cluster ({len(expected)} members, identical)")
    # (c) J-1744: n = 1,300 is over in ~0.05 s now, too short for a heartbeat to mean anything; a 14,000-row set keeps the new scan
    # busy for seconds (the old loop would need ~5 minutes on it, so it is not the control here). One production tile is then timed
    # turn by turn: the work between two yields is what the event loop waits for.
    rng = np.random.default_rng(11)
    make_db("hb", [_row(e, t) for e, t in zip(_noise(rng, 14000), rng.uniform(NOW - 60 * DAY, NOW - 5 * DAY, 14000))])
    res_c, wall_c, lags_c = await heartbeat_run(cooperative)
    n_c = len(candidate_rows(0))
    print("    " + lag_line(f"(c) NEW find_cluster_async, n={n_c:,}", wall_c, lags_c))
    p99_c = sorted(lags_c)[max(0, int(len(lags_c) * 0.99) - 1)]
    check(wall_c > 0.3 and p99_c < 0.05 and max(lags_c) < 1.5,
          f"(c) a scan that lasts {wall_c:.2f} s leaves the loop a p99 tick lag of {p99_c * 1000:.1f} ms < 50 ms; the worst, {max(lags_c) * 1000:.0f} ms, is the one "
          f"synchronous stretch before the first turn (candidate fetch + vector build + stack, unchanged in kind by J-1744) and stays under 1.5 s")
    steps, gaps = C._find_cluster_steps(0), []
    next(steps)                                                                      # the first turn also carries the one-off fetch + vector build + stack
    while True:
        t0 = time.perf_counter()
        try:
            next(steps)
        except StopIteration:
            break
        gaps.append(time.perf_counter() - t0)
    print(f"        production granularity: one {C.SEED_SCAN_TILE} x {C.SEED_SCAN_TILE} tile = {statistics.median(gaps) * 1000:.1f} ms median "
          f"(worst of {len(gaps)}: {max(gaps) * 1000:.1f} ms) -> the loop gets a turn at least that often")
    check(len(gaps) > 50 and max(gaps) < 0.05, "one production tile is well under 50 ms")
    use_db("h")

    print("\n[4] cost: the scan, hence the sleep, must get much SHORTER (never longer)")
    rounds = {"base loop (frozen copy)": [], "new, sync driver (find_cluster)": [], "new, async (shipped)": []}
    for _ in range(3):                                                              # interleaved rounds, best-of-3: Du and other jobs share this CPU
        for label in rounds:
            t0 = time.perf_counter()
            if label.startswith("base"):
                r = ref_find_cluster(0)
            elif label.startswith("new, sync"):
                r = C.find_cluster(0)
            else:
                r = await C.find_cluster_async(0)
            rounds[label].append(time.perf_counter() - t0)
            if len(rounds[label]) == 1:
                check(r == expected, f"{label}: same cluster")
    best = {k: min(v) for k, v in rounds.items()}
    t_base = best["base loop (frozen copy)"]
    for k, v in rounds.items():
        print(f"        {k:32s} best {best[k]:7.3f} s  ({t_base / best[k]:6.1f}x vs the base loop)   rounds: " + ", ".join(f"{x:.3f}" for x in v))
    check(best["new, async (shipped)"] <= 0.10 * t_base and best["new, sync driver (find_cluster)"] <= 0.10 * t_base,
          "best-of-3: the new async scan and the sync driver each take at most a tenth of the old per-pair loop's time (n=1,300; the gap widens with n)")
    # one bare loop turn, priced and scaled to a production scan (n = 41,000 -> one turn per tile)
    t0 = time.perf_counter()
    for _ in range(20000):
        await asyncio.sleep(0)
    per_turn = (time.perf_counter() - t0) / 20000
    turns = (-(-41000 // C.SEED_SCAN_TILE)) ** 2
    print(f"        one bare loop turn = {per_turn * 1e6:.1f} us -> {turns:,} turns = {per_turn * turns:.2f} s of yield overhead in a production-size (n=41,000) scan")
    check(per_turn * turns < 1.0, "the yields add under a second to a production-size scan")
    return expected


# ── [5] cancellation and re-entry ────────────────────────────────────────────────────────────────────────────────
STATE = {"started": 0, "active": 0, "peak": 0, "yields": 0}
_REAL_STEPS = C._find_cluster_steps


def _counting_steps(level=0):
    """C._find_cluster_steps wrapped to count scans started / in flight / yields (and to notice a close())."""
    STATE["started"] += 1
    STATE["active"] += 1
    STATE["peak"] = max(STATE["peak"], STATE["active"])
    try:
        g = _REAL_STEPS(level)
        while True:
            try:
                next(g)
            except StopIteration as done:
                return done.value
            STATE["yields"] += 1
            yield
    finally:
        STATE["active"] -= 1


def _reset_state():
    STATE.update(started=0, active=0, peak=0, yields=0)
    _cap.msgs.clear()


async def part_guard(expected):
    print("\n[5] cancellation and re-entry")
    use_db("h")
    C._find_cluster_steps = _counting_steps
    try:
        # cancel mid-scan
        _reset_state()
        t = asyncio.ensure_future(C.find_cluster_async(0))
        await asyncio.sleep(0.4)
        check(STATE["active"] == 1 and 0 in C._SCANNING and STATE["yields"] > 10,
              f"mid-scan: 1 scan in flight, level 0 flagged, {STATE['yields']} yields so far")
        t.cancel()
        t0 = time.perf_counter()
        try:
            await t
            cancelled = False
        except asyncio.CancelledError:
            cancelled = True
        t_cancel = time.perf_counter() - t0
        check(cancelled and t_cancel < 0.1, f"cancel: CancelledError delivered {t_cancel * 1000:.1f} ms after cancel() (at the next yield)")
        check(STATE["active"] == 0 and not C._SCANNING, "cancel: the generator was closed and the in-flight flag released")
        y0 = STATE["yields"]
        await asyncio.sleep(0.5)
        check(STATE["yields"] == y0, "cancel: nothing keeps scanning afterwards (no orphan; a worker thread would have carried on for ~2 s)")
        # ...and the next call starts a single clean scan that answers correctly
        res = await C.find_cluster_async(0)
        check(res == expected and STATE["started"] == 2 and STATE["peak"] == 1,
              f"re-entry after cancel: one clean scan, the same cluster; scans started={STATE['started']} (1 cancelled + 1 whole), "
              f"peak concurrency={STATE['peak']}")
        # overlapping second call while a scan runs
        _reset_state()
        a = asyncio.ensure_future(C.find_cluster_async(0))
        await asyncio.sleep(0.3)
        t0 = time.perf_counter()
        b = await C.find_cluster_async(0)
        t_b = time.perf_counter() - t0
        check(b is None and t_b < 0.1, f"overlap: the second call returns None in {t_b * 1000:.1f} ms")
        check(any(m.startswith("WARNING:") and "already in flight" in m for m in _cap.msgs), "overlap: it says so with a WARNING")
        # a level-1 call is a different scan and is not blocked by the level-0 one
        c1 = await C.find_cluster_async(1)
        check(c1 is None and not any("level 1" in m and "already in flight" in m for m in _cap.msgs),
              "overlap: a level-1 call while level 0 scans is not skipped (its own scan, tiny candidate set)")
        ra = await a
        check(ra == expected and STATE["peak"] == 2 and STATE["started"] == 2,
              f"overlap: the first scan still answers correctly; scans started={STATE['started']} (level 0 once + level 1 once), "
              f"the second level-0 call never began one")
        check(not C._SCANNING, "overlap: flag released after completion")
        # exception path releases the flag

        def _boom(level=0):
            yield
            yield
            raise RuntimeError("boom")
        C._find_cluster_steps = _boom
        try:
            await C.find_cluster_async(0)
            raised = False
        except RuntimeError:
            raised = True
        check(raised and not C._SCANNING, "exception in the scan: propagates and releases the in-flight flag")
    finally:
        C._find_cluster_steps = _REAL_STEPS
    res = await C.find_cluster_async(0)
    check(res == expected, "after all of the above a normal call still returns the same cluster")

    # J-1293 (F-1812): the DEBUG progress checkpoint fires at exactly the declared cadence against the
    # REAL observed yield count (via the same _counting_steps wrapper used above, not a hand-computed
    # guess of dataset "h"'s exact candidate count), and is proven inert -- zero lines -- at the live
    # process's real root level (INFO, scripts/run_nascence.py's own logging.basicConfig), confirming
    # the capture handler itself still works at that level (the pre-existing scan-start INFO line is
    # still seen) so an absent checkpoint line means genuinely filtered, not a broken capture.
    C._find_cluster_steps = _counting_steps
    try:
        _reset_state()
        with _patched(SEED_SCAN_CHECKPOINT_EVERY=7):
            res = await C.find_cluster_async(0)
        check(res == expected and STATE["yields"] > 20, f"checkpoint: {STATE['yields']} real yields observed (dataset h, level 0)")
        cps = [m for m in _cap.msgs if "seed scan checkpoint" in m]
        expect_n = STATE["yields"] // 7
        check(len(cps) == expect_n, f"checkpoint: fired exactly floor(real_yields/7) = {expect_n} times, not once per yield")
        last_have = int(cps[-1].split("checkpoint: ")[1].split("/")[0])
        last_total = int(cps[-1].split("/")[1].split(" ")[0])
        check(last_have == expect_n * 7 and last_total == STATE["yields"],
              f"checkpoint: the last line's own progress ({last_have}/{last_total}) matches 7*floor(yields/7) and the real yield total exactly")
    finally:
        C._find_cluster_steps = _REAL_STEPS
    C.logger.setLevel(logging.INFO)              # mirror the live process's real root level, not this harness's own forced DEBUG
    try:
        _reset_state()
        res = await C.find_cluster_async(0)
        check(res == expected, "checkpoint-inertness: a normal scan at the live INFO level still finds the same cluster")
        check(any("seed scan over" in m for m in _cap.msgs),
              "checkpoint-inertness: the capture handler still works at INFO (the pre-existing scan-start line is INFO, not filtered)")
        check(not any("seed scan checkpoint" in m for m in _cap.msgs),
              "checkpoint-inertness: ZERO checkpoint lines at the live process's real INFO level -- inert by default, not just by design")
    finally:
        C.logger.setLevel(logging.DEBUG)          # restore the harness's own capture level for every check after this one


# ── [6] the pipeline still waits ─────────────────────────────────────────────────────────────────────────────────
async def part_try_form_chapter():
    print("\n[6] try_form_chapter: never calls the blocking find_cluster, and only asks the author once the scan is done")
    use_db("d1")
    expected = ref_find_cluster(0)
    check(expected is not None and len(expected) >= C.MIN_MEMBERS, f"D1 as the pipeline sees it: the base finds a cluster of {len(expected or [])}")
    _reset_state()
    calls = []

    async def fake_call_json(base_urls, sys_p, user_p, max_tokens=0, temperature=0.0):
        calls.append({"active": STATE["active"], "yields": STATE["yields"], "n": int(re.search(r"It holds (\d+)", user_p).group(1))})
        return {"title": "T", "chapter": "too short to be a chapter"}                # -> "no usable chapter", nothing is written

    def _blocking_find_cluster(*a, **k):
        raise AssertionError("try_form_chapter called the BLOCKING find_cluster")

    C._find_cluster_steps = _counting_steps
    real_sync = C.find_cluster
    C.find_cluster = _blocking_find_cluster
    try:
        stop, lags = asyncio.Event(), []
        hb = asyncio.create_task(_heartbeat(stop, lags))
        await asyncio.sleep(0.2)
        t0 = time.perf_counter()
        title = await C.try_form_chapter(fake_call_json, None)
        wall = time.perf_counter() - t0
        await asyncio.sleep(0.2)
        stop.set()
        await hb
    finally:
        C.find_cluster = real_sync
        C._find_cluster_steps = _REAL_STEPS
    check(title is None and len(calls) == 1, "the author was called exactly once (its stub answered too short: no chapter, no write)")
    check(bool(calls) and calls[0]["active"] == 0 and calls[0]["yields"] > 10,
          f"the author was called only AFTER the scan finished (scans in flight at that moment: {calls[0]['active'] if calls else '?'}; "
          f"{calls[0]['yields'] if calls else '?'} yields had happened)")
    check(bool(calls) and calls[0]["n"] == len(expected), f"the author was handed the base's cluster ({calls[0]['n'] if calls else '?'} == {len(expected)} members)")
    check(len(lags) >= 0.5 * (wall + 0.4) / 0.05 and max(lags) < 0.25,
          f"the loop kept ticking through the pipeline call: {len(lags)} ticks, worst lag {max(lags) * 1000:.1f} ms")
    check(any("seed scan over" in m for m in _cap.msgs), "the scan announces itself in the log ('[chapters] seed scan over N level-0 candidates ...')")


# ── [7] informational: the asyncio.to_thread alternative ─────────────────────────────────────────────────────────
async def part_thread_comparison():
    print("\n[7] informational: why not asyncio.to_thread -- a loop callback doing 20 sqlite calls (a stand-in for a substrate tick)")
    use_db("h")
    db = sqlite3.connect(":memory:")
    db.execute("create table t(a int)")
    db.execute("insert into t values (1)")

    async def measure(kind):
        durs, stop = [], asyncio.Event()

        async def ticker():
            while not stop.is_set():
                await asyncio.sleep(0.05)
                t0 = time.perf_counter()
                for _ in range(20):
                    db.execute("select a from t").fetchone()
                durs.append(time.perf_counter() - t0)
        tk = asyncio.create_task(ticker())
        await asyncio.sleep(0.3)
        t0 = time.perf_counter()
        if kind == "idle":
            await asyncio.sleep(2.4)
        elif kind == "coroutine":
            await C.find_cluster_async(0)
        else:
            await asyncio.to_thread(C.find_cluster, 0)
        wall = time.perf_counter() - t0
        stop.set()
        await tk
        return statistics.median(durs) * 1000, max(durs) * 1000, len(durs), wall
    res = {k: await measure(k) for k in ("idle", "coroutine", "thread")}
    for k, (med, worst, n, wall) in res.items():
        print(f"        {k:10s} callback median {med:8.3f} ms  worst {worst:8.1f} ms  ({n} callbacks in {wall:.1f} s)")
    check(res["coroutine"][0] < 2.0, f"coroutine scan: the callback runs at idle speed (median {res['coroutine'][0]:.3f} ms)")
    print(f"        => a worker thread slows the same callback {res['thread'][0] / max(res['idle'][0], 1e-6):.0f}x (median) while the coroutine "
          f"does not ({res['coroutine'][0] / max(res['idle'][0], 1e-6):.1f}x); that, plus no cancellation and an exit that waits for the "
          f"worker, is why the shipped design is cooperative")


# ── [9] J-1744 (D-0330): the real-corpus acceptance (--corpus FILE) ──────────────────────────────────────────────
OLD_WORKER_SRC = r'''
import sys, time
import numpy as np
from pathlib import Path
root, db, shard, nshards, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, root)
from core import chapters as C
from core.memory import store as S
S.DB_PATH = Path(db)
with S._connect() as conn:
    rows = C._candidates(conn, 0)
vecs = []
for r in rows:
    v = S._blob_to_vec(r["embedding"])
    if v is not None:
        vecs.append((r, v))
idx = list(range(shard, len(vecs), nshards))
cnt = np.zeros(len(idx), dtype=np.int64)
t0 = time.time()
for k, i in enumerate(idx):
    v = vecs[i][1]
    cnt[k] = sum(1 for _, w in vecs if S._cosine(v, w) >= C.CLUSTER_SIM)      # the base commit's per-pair expression, verbatim
np.save(out, np.stack([np.array(idx, dtype=np.int64), cnt]))
print(f"shard {shard}/{nshards}: {len(idx)} of {len(vecs)} rows in {time.time() - t0:.0f} s")
'''


def _first_max(counts):
    """the base loop's seed rule, verbatim: the FIRST maximum wins (strict >)."""
    best_i, best_n = -1, -1
    for i, n in enumerate(counts):
        if n > best_n:
            best_i, best_n = i, n
    return best_i, best_n


def band_stats(vecs, wide=1e-4, win=1e-6):
    """census of the pairs near the bar, with the SAME primitives the scan uses (sgemm tiles; the production per-pair _cosine)."""
    vs = [v for _, v in vecs]
    mat = np.stack(vs)
    n, T = len(vs), C.SEED_SCAN_TILE
    lo, hi = np.float32(C.CLUSTER_SIM - wide), np.float32(C.CLUSTER_SIM + wide)
    st = {"band": 0, "margin": 0, "flips": [], "maxdiff": 0.0}
    for i0 in range(0, n, T):
        a = mat[i0:i0 + T]
        for j0 in range(0, n, T):
            s = a @ mat[j0:j0 + T].T
            rr, cc = np.nonzero((s >= lo) & (s < hi))
            for r, c in zip(rr.tolist(), cc.tolist()):
                dd = S._cosine(vs[i0 + r], vs[j0 + c])           # what the old loop computed
                g = float(s[r, c])                               # what a plain blocked product would have compared
                st["band"] += 1
                st["maxdiff"] = max(st["maxdiff"], abs(dd - g))
                st["margin"] += abs(dd - C.CLUSTER_SIM) < win
                if (g >= C.CLUSTER_SIM) != (dd >= C.CLUSTER_SIM):
                    st["flips"].append((i0 + r, j0 + c, dd >= C.CLUSTER_SIM))
    return st


def old_counts_sharded(db_path, workers):
    """the OLD per-pair loop (its inner expression, verbatim) for EVERY row at full n, row-sharded over `workers` processes."""
    src = TMP / "old_counts_worker.py"
    src.write_text(OLD_WORKER_SRC, encoding="utf-8")
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1")             # sdot on 384 floats is single-threaded anyway; this just stops idle BLAS pools piling up
    procs = [subprocess.Popen([sys.executable, str(src), str(ROOT), str(db_path), str(k), str(workers), str(TMP / f"old_{k}.npy")],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env) for k in range(workers)]
    logs = [p.communicate()[0] for p in procs]
    bad = [(k, p.returncode, logs[k][-300:]) for k, p in enumerate(procs) if p.returncode != 0]
    if bad:
        raise RuntimeError(f"old-count workers failed: {bad}")
    parts = [np.load(TMP / f"old_{k}.npy") for k in range(workers)]
    counts = [None] * sum(p.shape[1] for p in parts)
    for p in parts:
        for i, c in zip(p[0].tolist(), p[1].tolist()):
            counts[i] = c
    return counts, logs


async def part_corpus(path):
    print(f"\n[9] J-1744 real-corpus acceptance on the COPY {path}")
    src = sqlite3.connect(path)
    src.row_factory = sqlite3.Row
    got = src.execute("SELECT fragment_id, content, timestamp, importance, embedding, origin FROM c ORDER BY rowid").fetchall()
    src.close()
    make_db("corpus", [(r["fragment_id"], r["content"], "episodic", 0.5, float(r["timestamp"]), "", bytes(r["embedding"]), r["origin"],
                         float(r["importance"]), None, 0) for r in got])
    del got
    cand = candidate_rows(0)
    vecs = [(r, S._blob_to_vec(r["embedding"])) for r in cand]
    n = len(vecs)
    mat = np.stack([v for _, v in vecs])
    sq = np.einsum("ij,ij->i", mat, mat)
    del mat
    print(f"    corpus copy: {n} level-0 candidates -> {n * n:,} ordered pairs (the old loop made one Python-level np.dot call per pair); "
          f"|v|^2 in [{sq.min():.7f}, {sq.max():.7f}]; BLAS threads: {os.environ.get('OPENBLAS_NUM_THREADS', 'default (all)')}")
    check(n >= 5000, f"[9] the corpus copy is production-sized (n={n})")
    # (a) the production path at full n, with the event-loop heartbeat alongside; open era so the pre-era cluster comes back whole
    def spy(ts):
        return (0.0, float("inf"))
    C._era_window = spy
    try:
        res, wall, lags = await heartbeat_run(lambda: C.find_cluster_async(0))
    finally:
        C._era_window = ORIG_ERA
    tiles = (-(-n // C.SEED_SCAN_TILE)) ** 2
    print("    " + lag_line(f"NEW find_cluster_async, n={n:,}", wall, lags))
    print(f"        {tiles:,} tiles of {C.SEED_SCAN_TILE} x {C.SEED_SCAN_TILE}, one event-loop turn each = {wall / tiles * 1000:.2f} ms per turn on average")
    check(wall < 120.0, f"[9] the new scan takes {wall:.1f} s at n={n:,} (target: well under 120 s; the old loop was ~2,600 s at n=40.9k)")
    p99 = sorted(lags)[max(0, int(len(lags) * 0.99) - 1)]
    check(p99 < 0.05 and max(lags) < 2.0,
          f"[9] the event loop kept ticking through the full-size scan: p99 tick lag {p99 * 1000:.1f} ms < 50 ms; worst {max(lags) * 1000:.0f} ms is the one "
          f"synchronous stretch before the first turn (candidate fetch + vector build + stack) and stays under 2 s")
    ids_new = [m["id"] for m in (res or [])]
    new_counts, _ = _drive(C._neighbour_counts(vecs, 0))
    seed_new, top_new = _first_max(new_counts)
    srt = sorted(new_counts)
    print(f"        new seed: row {seed_new} = {cand[seed_new]['fragment_id']} with {top_new} neighbours (runner-up count {srt[-2]}; "
          f"the 3rd {srt[-3]}); pre-era cluster of {len(ids_new)} members")
    # (b) the margin census: the pairs the sdot-vs-sgemm question is about
    st = band_stats(vecs)
    print(f"    margin census: {st['band']:,} ordered pairs lie within 1e-4 of CLUSTER_SIM (the guard band re-decides ~those); "
          f"{st['margin']} ordered pairs (~{st['margin'] // 2} unordered) have |cos - 0.70| < 1e-6 by the production sdot; "
          f"max |sgemm - sdot| over the band = {st['maxdiff']:.2e}; sdot-vs-sgemm DECISION FLIPS = {len(st['flips'])}")
    # (c) the old loop, full n: every row's count, sharded over processes
    if ARGS.old_workers > 0:
        t0 = time.perf_counter()
        old_counts, logs = old_counts_sharded(DBS["corpus"], ARGS.old_workers)
        t_old = time.perf_counter() - t0
        print(f"    OLD per-pair loop: {n * n:,} np.dot calls sharded over {ARGS.old_workers} processes took {t_old:.0f} s wall "
              f"(sequentially it would be ~{n * n / 640_000:.0f} s at the live 640k pairs/s); {logs[0].strip()}")
        seed_old, top_old = _first_max(old_counts)
        differ = sum(a != b for a, b in zip(old_counts, new_counts))
        check(len(old_counts) == n and differ == 0, f"[9] per-row neighbour counts: new == old for all {n:,} rows ({differ} differ)")
        check(seed_old == seed_new and top_old == top_new,
              f"[9] SEED: old row {seed_old} ({cand[seed_old]['fragment_id']}, {top_old} neighbours) == new row {seed_new} ({cand[seed_new]['fragment_id']}, {top_new})")
        old_ids = [r["fragment_id"] for r, v in vecs if S._cosine(vecs[seed_old][1], v) >= C.CLUSTER_SIM]
        check(old_ids == ids_new and len(old_ids) >= C.MIN_MEMBERS,
              f"[9] CLUSTER: the old pipeline's {len(old_ids)} members == the new find_cluster_async's {len(ids_new)} members, same order")
        delta = {}
        for i, j, old_pass in st["flips"]:
            delta[i] = delta.get(i, 0) + (-1 if old_pass else 1)      # a plain product would decide the opposite of sdot
        plain = list(old_counts)
        for i, dl in delta.items():
            plain[i] += dl
        seed_plain, _ = _first_max(plain)
        print(f"    what-if, a PLAIN float32 blocked product with no guard band: {len(st['flips'])} flipped pair decisions would touch {len(delta)} rows; "
              f"the seed would be {'UNCHANGED' if seed_plain == seed_old else 'CHANGED'}")
    # (d) the literal frozen function (era window open, MIN_MEMBERS lowered) on random real subsamples
    rng = np.random.default_rng(909)
    for k in range(ARGS.subsamples):
        pick = np.sort(rng.choice(n, size=min(3000, n), replace=False))
        make_db("sub", [(cand[i]["fragment_id"], cand[i]["content"], "episodic", 0.5, float(cand[i]["timestamp"]), "", bytes(cand[i]["embedding"]),
                         "inner_thought", float(cand[i]["importance"]), None, 0) for i in pick])
        out, recs, walls = await run_drivers(0, "open", sync_too=False, MIN_MEMBERS=8)
        compare(f"[9] real subsample {k + 1} ({len(pick)} rows): literal frozen find_cluster vs the new one", out, recs)
        print(walls_line(walls, recs))


async def main():
    if ARGS.corpus:
        await part_corpus(ARGS.corpus)
        return
    await part_equivalence()
    expected = await part_heartbeat_and_cost()
    with _patched(SEED_SCAN_TILE=8):      # tiny tiles: the n=1,300 / 780 sets yield thousands of times and the scan lasts ~1 s again, which is what the
        await part_guard(expected)        # cancel / overlap / checkpoint / pipeline / thread parts need (they poke a scan that must still be running)
        await part_try_form_chapter()
        await part_thread_comparison()


asyncio.run(main())

# ── [8] isolation report ────────────────────────────────────────────────────────────────────────────────────────
print("\n[8] isolation: nothing was written under the live data dir")
check(not any("find_cluster failed" in m for m in _cap.all),
      "no scan swallowed an exception ('[chapters] find_cluster failed (non-fatal)' never logged, so no comparison was None-vs-None by accident)")
_after_md5 = {p: _md5(p) for p in _LIVE_JSON}
_after_stat = {p: _stat(p) for p in _LIVE_DB_FILES}
for p in _LIVE_JSON:
    same = _before_md5[p] == _after_md5[p]
    print(f"    {p.name:16s} md5 before {_before_md5[p]} after {_after_md5[p]}  "
          f"({'unchanged' if same else 'CHANGED - Du is online and rewrites it by itself; the audit hook below is the proof'})")
for p in _LIVE_DB_FILES:
    print(f"    {p.name:16s} (size, mtime_ns) before {_before_stat[p]} after {_after_stat[p]}  (informational: Du writes these constantly)")
print(f"    write attempts under a live data dir by THIS process: {len(LIVE_WRITE_ATTEMPTS)} {LIVE_WRITE_ATTEMPTS}")
print(f"    live DB opens by THIS process: {len(LIVE_RO_OPENS)} {LIVE_RO_OPENS}  (only the one deliberate mode=ro sample is allowed)")
check(not LIVE_WRITE_ATTEMPTS, "0 write attempts under C:\\Nascence\\data (audit hook: open-for-write, rename/remove/mkdir, plain sqlite3.connect)")
check(len(LIVE_RO_OPENS) <= 1 and all("mode=ro" in o[1] for o in LIVE_RO_OPENS), "the live DB was opened at most once, and only as a mode=ro URI")
import gc                                                                   # sqlite connections dropped inside exception frames can
gc.collect()                                                                # outlive their function until the cycle collector runs;
shutil.rmtree(TMP, ignore_errors=True)                                      # a temp file still open would leak on Windows (D-0242)
check(not TMP.exists(), f"the temp store dir was removed completely ({TMP})")
print(f"\n{'ALL OK' if FAILS == 0 else f'{FAILS} FAILED'}")
sys.exit(0 if FAILS == 0 else 1)
