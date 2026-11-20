"""
Regression: core/curiosity_queue.py's writers sit behind the D-0179 write fence (J-1820, F-2442; sibling of J-1802's meta_awareness fence).

THE GAP. enqueue() (append to data/curiosity_queue.jsonl), mark_processed() (rewrite of the same file) and transform_and_seed()'s shadow log
(data/logs/curiosity_shadow.jsonl) used __file__-relative paths with no profile.guard_path, so any non-live process reaching them wrote that tree's
REAL data/ files. THE BUILD. Each resolves guard_path before any I/O inside its own existing fail-open try; refusal is swallowed (enqueue -> None).
Live, lab-sandbox and outside-data paths are byte-identical.
  [0] resolution  [1] static AST ratchet  [2] non-live simulated data/  [3] real paths, blocking audit hook  [4] live == pre-fence reference
  [5] redirects  [6] warning visibility  [7] canary on live files

  python scripts/_test_curiosity_queue_fence.py     # exit 0 = ALL OK; run FROM the checkout it tests
TEETH: run against the pre-J-1820 module in a throwaway `git worktree add <dir> HEAD` plus this file -- must exit 1.
"""
from __future__ import annotations

import ast
import asyncio
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="j1820_cq_fence_"))
FAILS = 0
CHECKS = 0


def check(cond, label):
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_CANARY = [_LIVE_DATA / "curiosity_queue.jsonl", _LIVE_DATA / "logs" / "curiosity_shadow.jsonl"]


def _snap(p):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _CANARY}
_WATCH = sorted({str(_LIVE_DATA).lower(), str(ROOT / "data").lower()})
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod", "shutil.copyfile", "shutil.move", "shutil.rmtree"}
ATTEMPTS: list = []
_DATA_EXISTED = (ROOT / "data").exists()


def _under_watch(p):
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    hit = None
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                hit = ("open", str(path), mode)
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    hit = (event, str(a), None)
                    break
    except Exception:
        return
    if hit:
        ATTEMPTS.append(hit)
        raise PermissionError(f"J-1820 test trap: write under a real data/ blocked: {hit}")


sys.addaudithook(_audit)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows = []

    def emit(self, record):
        self.rows.append((record.name, record.levelno, record.getMessage()))


_cap = _Cap()
_lg = logging.getLogger("nascence.profile")
_lg_prop = _lg.propagate
_lg.addHandler(_cap)
_lg.propagate = False

import core                                   # noqa: E402  (BEFORE anything that could aim at another tree)
from core import profile as P                 # noqa: E402
from core import curiosity_queue as cq        # noqa: E402
import core.frontier as FR                    # noqa: E402

print("[0] module resolution + surface")
for _m in (core, P, cq):
    if ROOT not in Path(_m.__file__).resolve().parents:
        print(f"ABORT: {_m.__name__} imported from {_m.__file__}, not {ROOT}")
        sys.exit(2)
check(True, "core, core.profile, core.curiosity_queue are THIS root's")
_D = dict(Q=cq._QUEUE, S=cq._SHADOW)
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE)
check(getattr(cq, "profile", None) is P, "core.curiosity_queue.profile is core.profile")
check(_D["Q"] == ROOT / "data" / "curiosity_queue.jsonl" and _D["S"] == ROOT / "data" / "logs" / "curiosity_shadow.jsonl",
      "path constants keep names and __file__-relative defaults")
check(list(inspect.signature(cq.enqueue).parameters) == ["source", "raw_text", "meta"]
      and list(inspect.signature(cq.mark_processed).parameters) == ["item_id"], "enqueue / mark_processed signatures unchanged")

print("\n[1] static: every write-mode open() / write_text() / parent.mkdir() in core/curiosity_queue.py takes a guard_path() result")


def _is_guard(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "guard_path"
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "profile")


def _unfenced(src):
    bad = []
    for fn in ast.walk(ast.parse(src)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        guarded = {t.id for node in ast.walk(fn) if isinstance(node, ast.Assign) and _is_guard(node.value)
                   for t in node.targets if isinstance(t, ast.Name)}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Name) and f.id == "open" and node.args:
                mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
                if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and set(mode.value) & set("wax+"):
                    t = node.args[0]
                    if not (_is_guard(t) or (isinstance(t, ast.Name) and t.id in guarded)):
                        bad.append((fn.name, node.lineno, ast.unparse(t)))
            elif isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes", "mkdir"):
                if f.attr == "mkdir":
                    if not (isinstance(f.value, ast.Attribute) and f.value.attr == "parent"):
                        continue
                    base = f.value.value
                else:
                    base = f.value
                if not (_is_guard(base) or (isinstance(base, ast.Name) and base.id in guarded)):
                    bad.append((fn.name, node.lineno, ast.unparse(f.value)))
    return bad


_bad = _unfenced(Path(cq.__file__).read_text(encoding="utf-8"))
check(not _bad, f"no unfenced write/mkdir site in core/curiosity_queue.py {_bad}")
check(_unfenced("def w(p):\n    with open(p, 'a') as f:\n        f.write('x')\n") != []
      and _unfenced("def w():\n    _S.write_text('x')\n") != []
      and _unfenced("def w(p):\n    q = profile.guard_path(p)\n    q.parent.mkdir()\n    open(q, 'a')\n    open(p)\n") == [],
      "the ratchet has teeth (flags bare writes, passes guard_path-bound ones and plain reads)")

# pre-fence reference: shipped functions with guard_path(X) undone textually
_SITE = re.compile(r"profile\.guard_path\((\w+)\)")
_ref_ns = dict(vars(cq))
_sites = {}
for _name in ("enqueue", "mark_processed", "transform_and_seed"):
    _src, _sites[_name] = _SITE.subn(r"\1", inspect.getsource(getattr(cq, _name)))
    exec(compile(_src, f"<pre-J-1820 {_name}>", "exec"), _ref_ns)
check(_sites == {"enqueue": 1, "mark_processed": 1, "transform_and_seed": 1}, f"exactly one guard_path site per fenced function {_sites}")


def _new(n):
    return getattr(cq, n)


def _ref(n):
    return _ref_ns[n]


fake = TMP / "fake_root" / "data"
fake.mkdir(parents=True)


def _paths(d):
    return dict(q=d / "curiosity_queue.jsonl", s=d / "logs" / "curiosity_shadow.jsonl")


def _plant(p):
    p["q"].parent.mkdir(parents=True, exist_ok=True)
    p["q"].write_text(json.dumps({"id": "planted01", "ts": 1.0, "source": "gate_dissonance", "raw_text": "old knot",
                                  "status": "pending", "meta": {}}) + "\n", encoding="utf-8")
    p["s"].parent.mkdir(parents=True, exist_ok=True)
    p["s"].write_text('{"planted": 1}\n', encoding="utf-8")


def _aim(p):
    for attr, v in (("_QUEUE", p["q"]), ("_SHADOW", p["s"])):
        setattr(cq, attr, v)
        _ref_ns[attr] = v


async def _call_json(urls, sysp, usr, max_tokens=0, temperature=0):
    return {"question": "How does comparative literature treat the doppelganger motif?", "field": "literature"}


# frontier is a separate fenced writer; neutralise it so only this module's writers are measured
_fr_orig = FR.note_question
FR.note_question = lambda q, src: True


def _sequence(get):
    r = {}
    r["enq"] = get("enqueue")("t4_insufficient_evidence", "a recurring knot \u00fcn\u00ef \u2713", {"k": 1})
    r["enq_bad"] = get("enqueue")("not_a_source", "x")
    get("mark_processed")("planted01")
    r["n"] = asyncio.run(get("transform_and_seed")(_call_json, [], 4))
    return r


def _SIM():
    P._DATA = fake
    P._CANONICAL_DATA = fake


def _REAL():
    P._DATA = _orig["DATA"]
    P._CANONICAL_DATA = _orig["CANON"]


def _fp(p):
    return {k: _snap(p[k]) for k in p}


def _by(p):
    return {k: (p[k].read_bytes() if p[k].exists() else None) for k in p}


def _norm(b):   # ids are random uuid and ts are wall-clock; compare structure
    out = []
    for line in (b or b"").decode("utf-8").splitlines():
        d = json.loads(line)
        if d.get("id") != "planted01":
            d.pop("id", None)
        d.pop("ts", None)
        out.append(d)
    return out


try:
    print("\n[2] non-live process, simulated data/ root")
    _SIM()
    P.LIVE = False
    ctl, new = _paths(fake / "nl_ctl"), _paths(fake / "nl_new")
    _plant(ctl)
    _aim(ctl)
    r_ctl = _sequence(_ref)
    check(r_ctl["enq"] is not None and ctl["q"].read_text(encoding="utf-8").count("\n") == 2 and ctl["s"].read_text(encoding="utf-8").count("\n") > 1,
          "CONTROL: pre-fence reference writes the queue and the shadow log in a non-live process")
    _plant(new)
    f0 = _fp(new)
    names0 = sorted(x.name for x in (fake / "nl_new").iterdir())
    _aim(new)
    r_new = _sequence(_new)
    check(_fp(new) == f0, "fenced: queue and shadow log byte-identical (size+sha256) after enqueue, mark_processed and transform_and_seed")
    check(sorted(x.name for x in (fake / "nl_new").iterdir()) == names0, "fenced: no new file appeared")
    check(r_new["enq"] is None and r_new["enq_bad"] is None, "fenced enqueue returns None (refusal swallowed), raises nothing")
    try:
        check(_new("mark_processed")("planted01") is None and _fp(new) == f0, "fenced mark_processed returns None and touches nothing")
    except Exception as exc:
        check(False, f"mark_processed raised {exc!r}")

    print("\n[3] module's own REAL default paths, non-live, blocking audit hook armed")
    _REAL()
    P.LIVE = False
    ATTEMPTS.clear()
    _aim(dict(q=_D["Q"], s=_D["S"]))
    _sequence(_new)
    check(not ATTEMPTS, f"fenced: ZERO write attempts under any real data/ {ATTEMPTS}")
    check((ROOT / "data").exists() == _DATA_EXISTED, "fenced: no data/ directory created under this root")
    ATTEMPTS.clear()
    _sequence(_ref)
    names = {Path(a[1]).name for a in ATTEMPTS}
    check("curiosity_queue.jsonl" in names or "data" in names or "logs" in names,
          f"CONTROL: pre-fence reference attempts REAL data/ writes (blocked): {sorted(names)}")
    ATTEMPTS.clear()

    print("\n[4] live process: fenced == pre-fence reference")
    _SIM()
    P.LIVE = True
    ln, lo = _paths(fake / "live_new"), _paths(fake / "live_old")
    rets = {}
    for p_, g_, tag in ((ln, _new, "new"), (lo, _ref, "old")):
        _plant(p_)
        _aim(p_)
        rets[tag] = _sequence(g_)
    bn, bo = _by(ln), _by(lo)
    check(_norm(bn["q"]) == _norm(bo["q"]) and len(_norm(bn["q"])) == 2, "queue contents identical to pre-fence reference (modulo uuid/ts)")
    check(_norm(bn["s"]) == _norm(bo["s"]) and len(_norm(bn["s"])) > 1, "shadow log contents identical to pre-fence reference (modulo ts)")
    check("\u00fcn\u00ef \u2713".encode("utf-8") in bn["q"], "ensure_ascii=False content survives")
    check(rets["new"]["n"] == rets["old"]["n"] and (rets["new"]["enq"] is None) == (rets["old"]["enq"] is None), "return values identical")
    check(all(json.loads(l)["status"] == "processed" for l in ln["q"].read_text(encoding="utf-8").splitlines() if "planted01" in l),
          "mark_processed really flipped the planted row")

    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    for tag, p_ in (("data/_lab/<stamp>/ sandbox", _paths(fake / "_lab" / "20261004_000000")), ("outside data/", _paths(TMP / "outside"))):
        _plant(p_)
        _aim(p_)
        _sequence(_new)
        check(_norm(p_["q"].read_bytes()) == _norm(bo["q"]), f"{tag}: writes identically to the live run")
    direct = _paths(fake / "_lab")
    _aim(direct)
    _sequence(_new)
    check(not direct["q"].exists(), "data/_lab/<file> with no sandbox dir stays refused")

    print("\n[6] the swallowed refusal is not silent")
    vis = _paths(fake / "vis")
    _plant(vis)
    _aim(vis)
    P._warned.discard(str(vis["q"]))
    _cap.rows.clear()
    for i in range(3):
        cq.enqueue("gate_dissonance", f"distinct tension {i}")
    warn = [r for r in _cap.rows if r[1] == logging.WARNING and "curiosity_queue.jsonl" in r[2]]
    check(len(warn) == 1, f"ONE guard_path warning naming curiosity_queue.jsonl across 3 refused enqueues ({len(warn)})")
finally:
    cq._QUEUE, cq._SHADOW = _D["Q"], _D["S"]
    FR.note_question = _fr_orig
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    _lg.removeHandler(_cap)
    _lg.propagate = _lg_prop

print("\n[7] canary")
_after = {p: _snap(p) for p in _CANARY}
check(_after == _before, "live curiosity queue / shadow log byte-identical to the start of the run")
check((ROOT / "data").exists() == _DATA_EXISTED, "this root's data/ directory is as it was")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} -- {CHECKS} checks")
sys.exit(1 if FAILS else 0)
