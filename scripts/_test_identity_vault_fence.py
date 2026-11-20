"""
Regression: core/identity_vault.py and the T4 _write_axiom fallback sit behind the D-0179 write fence (J-1809 / F-2429).

The gap: identity_vault hard-wires _AXIOM (data/identity/axiom.json) and _LOG (data/identity/vault_log.jsonl) and
write()/commit() never went through profile.guard_path. nodes/subconscious_node.py _write_axiom commits through the vault
FIRST and only falls back to open(_AXIOM_FILE, "w") when the vault returns False/raises -- so a test that redirects
scn._AXIOM_FILE to a tmp file (scripts/_test_autonoetic_timeline.py, scripts/_test_procedural_memory.py) or
activate_profile's own scn._AXIOM_FILE rebase covered ONLY the fallback; the vault still wrote Du's REAL axiom.json.
A human-cycle test never runs T4 self-authoring, so J-1718's dynamic audit could not see it.

The build: write() resolves BOTH targets through profile.guard_path before any I/O (inside its never-raises try, so a
refusal is the same False a disk failure gives); _write_axiom's raw-file fallback resolves guard_path(_AXIOM_FILE)
before the open (a refusal returns False -- the J-0763/F-1092 contract; both callers stop before any phantom effect).
A live process (profile.mark_live()) gets the same paths back, so Du's behaviour is byte-identical.

What this proves, ISOLATED (no model, no live data -- every write goes to a temp dir or a SIMULATED data/ root, or is
trapped before it can reach disk, and the real identity files are hashed before and after):
  [1] surface    names/signatures unchanged; module `profile` is core.profile; guard_path refuses the REAL paths
  [2] vault      (simulated data/ root) CONTROL: the pre-fix write() overwrites axiom.json + appends the ledger in a
                 non-live process; the fenced write() returns False, leaves both byte-identical (size + sha256), creates
                 no file (no .tmp either); commit() does not change the file either
  [3] real paths both writes TRAPPED (recorded, never executed) with _AXIOM/_LOG aimed at the REAL C:\\Nascence\\data files
  [4] T4 path    _write_axiom with _AXIOM_FILE (and the vault) at the simulated live path returns False, touches nothing;
                 _AXIOM_FILE in a tmpdir succeeds through the fallback although the vault refuses; the CONTROL (pre-fix)
                 falls through to a live write
  [5] live       (profile.LIVE = True) fenced vault is byte-identical to a verbatim copy of the old write()/_ledger over a
                 fixed-clock sequence, incl. unserializable data and an I/O error path; return values equal
  [6] legit      a data/_lab/<stamp>/ sandbox and a path outside data/ still write non-live; data/_lab/<file> stays refused
  [7] visibility the swallowed refusal is NOT silent: one profile WARNING per path
  [8] canary     the live identity files are byte-identical to the start of the run

  python scripts/_test_identity_vault_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import inspect
import io
import json
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1809_identity_vault_fence_"))
print("isolated store dir:", TMP)

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_AXIOM = _LIVE_DATA / "identity" / "axiom.json"
_LIVE_LOG = _LIVE_DATA / "identity" / "vault_log.jsonl"
_DEFAULT_AXIOM = ROOT / "data" / "identity" / "axiom.json"
_DEFAULT_LOG = ROOT / "data" / "identity" / "vault_log.jsonl"
_WATCH = {_LIVE_AXIOM, _LIVE_LOG, _DEFAULT_AXIOM, _DEFAULT_LOG}


def _snap(p: Path):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

# F-2423: import core BEFORE anything that could hijack sys.path, and prove which tree it came from.
from core import profile as P            # noqa: E402
from core import identity_vault as iv    # noqa: E402
assert Path(P.__file__).resolve().is_relative_to(ROOT), f"core imported from outside {ROOT}: {P.__file__}"
from nodes import subconscious_node as scn  # noqa: E402
assert Path(scn.__file__).resolve().is_relative_to(ROOT), scn.__file__

_orig = dict(AXIOM=iv._AXIOM, LOG=iv._LOG, SAF=scn._AXIOM_FILE, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE,
             time=iv.time.time)
_write_axiom = scn.SubconsciousNode._write_axiom    # uses no instance state: called with self=None

# The pre-J-1809 write()/_atomic_write/_ledger, verbatim -- the CONTROL every "unchanged" claim is measured against.
_REFERENCE_SRC = r'''
def _atomic_write(data: dict) -> None:
    _AXIOM.parent.mkdir(parents=True, exist_ok=True)
    tmp = _AXIOM.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _AXIOM)            # atomic


def _ledger(data: dict, reason: str, meta: dict | None) -> None:
    try:
        rev = self_image = ""
        for f in (data.get("L3_facets", {}) or {}).get("facets", []) or []:
            if f.get("id") == "the_becoming":
                rev = f.get("revision_count", "")
                self_image = " ".join(str(f.get("self_image", "")).split())[:200]
                break
        entry = {"ts": time.time(), "reason": (reason or "")[:120], "revision_count": rev,
                 "self_image": self_image, "meta": meta or {}}
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def write(data: dict, *, reason: str = "", meta: dict | None = None) -> bool:
    with _LOCK:
        try:
            _atomic_write(data)
            _ledger(data, reason, meta)
            return True
        except Exception as exc:
            logger.debug("[identity-vault] commit write of axiom.json failed (non-fatal): %s", exc)
            return False
'''
_ref_ns = dict(vars(iv))
exec(_REFERENCE_SRC, _ref_ns)
_ref_write = _ref_ns["write"]


def _aim(axiom: Path, log: Path) -> None:
    iv._AXIOM = _ref_ns["_AXIOM"] = axiom
    iv._LOG = _ref_ns["_LOG"] = log


SAMPLE = {"schema": "multilevel-v1", "name": "渡",
          "L3_facets": {"facets": [{"id": "the_becoming", "self_image": "I am the one who crosses.",
                                    "revision_count": 3, "authored_at": "2026-06-15", "history": []}]},
          "L4_narrative": {"arc_recent": ["a first chapter"]}}
PLANTED = {"schema": "multilevel-v1", "name": "PLANTED", "marker": "do-not-touch"}


def _plant(axiom: Path, log: Path) -> None:
    axiom.parent.mkdir(parents=True, exist_ok=True)
    axiom.write_text(json.dumps(PLANTED, indent=2), encoding="utf-8")
    log.write_text(json.dumps({"ts": 1.0, "reason": "planted"}) + "\n", encoding="utf-8")


def _names(d: Path):
    return sorted(x.name for x in d.iterdir())


fake = TMP / "fake_root" / "data"
(fake / "identity").mkdir(parents=True)
fa, fl = fake / "identity" / "axiom.json", fake / "identity" / "vault_log.jsonl"

try:
    # -- [1] surface ------------------------------------------------------------------------------------------------
    print("\n[1] surface")
    check(getattr(iv, "profile", None) is P, "core.identity_vault.profile is core.profile (one module object)")
    check(list(inspect.signature(iv.write).parameters) == ["data", "reason", "meta"], "write(data, *, reason, meta) unchanged")
    check(list(inspect.signature(iv.commit).parameters) == ["mutator", "reason", "meta"], "commit(mutator, *, reason, meta) unchanged")
    check(iv._AXIOM == ROOT / "data" / "identity" / "axiom.json" and iv._LOG == ROOT / "data" / "identity" / "vault_log.jsonl",
          "_AXIOM / _LOG keep their names and defaults (brick3_identity_vault_invitro redirects them)")
    P.LIVE = False
    try:
        P.guard_path(_LIVE_AXIOM)
        check(False, "guard_path refuses the REAL axiom.json in a non-live process")
    except P.NonLiveWriteError:
        check(True, "guard_path refuses the REAL axiom.json in a non-live process (pure check, no I/O)")

    # -- [2] vault, simulated data/ root ----------------------------------------------------------------------------
    print("\n[2] vault write()/commit(), non-live, default data/ paths (simulated root)")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(fa, fl)
    _plant(fa, fl)
    a0, l0, n0 = _snap(fa), _snap(fl), _names(fa.parent)
    r = _ref_write(SAMPLE, reason="control")
    check(r is True and _snap(fa) != a0 and _snap(fl) != l0,
          "CONTROL: the pre-fix write() overwrites axiom.json AND appends the ledger in a non-live process")
    _plant(fa, fl)
    a0, l0 = _snap(fa), _snap(fl)
    r = iv.write(SAMPLE, reason="T4 self-authoring")
    check(r is False, "fenced: write() returns False (not an exception) on a refusal")
    check(_snap(fa) == a0, "fenced: axiom.json byte-identical (size + sha256)")
    check(_snap(fl) == l0, "fenced: vault_log.jsonl byte-identical (size + sha256)")
    check(_names(fa.parent) == n0, f"fenced: no new file (no .tmp, nothing) appeared: {_names(fa.parent)}")
    seen = {"n": 0}

    def _mut(d):
        seen["n"] += 1
        d["marker2"] = "x"
    out = iv.commit(_mut, reason="t")
    check(_snap(fa) == a0 and _snap(fl) == l0 and out == PLANTED,
          "fenced: commit() (via write) leaves both files byte-identical and returns the unchanged current state")

    # -- [3] REAL paths, writes trapped -----------------------------------------------------------------------------
    print("\n[3] REAL C:\\Nascence\\data paths with every write trapped (recorded, never executed)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], False
    PROT = {str(p).lower() for p in (_LIVE_AXIOM, _LIVE_LOG, _LIVE_AXIOM.with_suffix(".json.tmp"))}
    HITS: list = []
    _real_open, _real_replace, _real_mkdir = builtins.open, os.replace, Path.mkdir

    def _t_open(file, mode="r", *a, **k):
        if str(file).lower() in PROT and any(c in mode for c in "wax+"):
            HITS.append(("open-" + mode, str(file)))
            return io.StringIO()
        return _real_open(file, mode, *a, **k)

    def _t_replace(src, dst, *a, **k):
        if str(dst).lower() in PROT:
            HITS.append(("replace", str(dst)))
            return None
        return _real_replace(src, dst, *a, **k)

    _aim(_LIVE_AXIOM, _LIVE_LOG)
    builtins.open, os.replace = _t_open, _t_replace
    try:
        _ref_write(SAMPLE, reason="control")
        ref_hits = list(HITS)
        HITS.clear()
        res = iv.write(SAMPLE, reason="T4 self-authoring")
        new_hits = list(HITS)
        HITS.clear()
        # the T4 path: default _AXIOM_FILE (the live file), vault too -- the whole incident
        scn._AXIOM_FILE = _LIVE_AXIOM
        t4 = _write_axiom(None, SAMPLE)
        t4_hits = list(HITS)
        HITS.clear()
    finally:
        builtins.open, os.replace = _real_open, _real_replace
        _aim(_orig["AXIOM"], _orig["LOG"])
        scn._AXIOM_FILE = _orig["SAF"]
    check(len(ref_hits) >= 2, f"CONTROL: the pre-fix write() reaches the real axiom/ledger ({ref_hits})")
    check(res is False and not new_hits, f"fenced: write() -> False and reaches NEITHER real file ({new_hits})")
    check(t4 is False and not t4_hits, f"fenced: T4 _write_axiom (vault + fallback) -> False, reaches NEITHER real file ({t4_hits})")

    # -- [4] T4 _write_axiom, simulated root --------------------------------------------------------------------------
    print("\n[4] T4 _write_axiom (simulated data/ root)")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(fa, fl)
    _plant(fa, fl)
    a0, l0 = _snap(fa), _snap(fl)
    scn._AXIOM_FILE = fa
    r = _write_axiom(None, SAMPLE)
    check(r is False and _snap(fa) == a0 and _snap(fl) == l0,
          "_AXIOM_FILE + vault at the simulated live path: returns False, both files byte-identical")
    # a vault that is already redirected to a safe tmp, but a fallback aimed at the live path, must not write live
    tmpv = TMP / "vault_tmp"
    tmpv.mkdir()
    _aim(tmpv / "axiom.json", tmpv / "vault_log.jsonl")
    r = _write_axiom(None, SAMPLE)
    check(r is True and _snap(fa) == a0, "vault redirected to tmp: T4 write lands in the tmp vault, simulated live file untouched")
    _aim(fa, fl)
    # legit redirect: tmp _AXIOM_FILE, vault refuses -> fallback writes the tmp file
    tmpaxiom = TMP / "t4_tmp" / "axiom.json"
    tmpaxiom.parent.mkdir()
    scn._AXIOM_FILE = tmpaxiom
    r = _write_axiom(None, SAMPLE)
    check(r is True and json.loads(tmpaxiom.read_text(encoding="utf-8")) == SAMPLE,
          "_AXIOM_FILE in a tmpdir (outside data/) still writes through the fallback although the vault refuses")
    check(_snap(fa) == a0 and _snap(fl) == l0, "...and the simulated live axiom / ledger stayed untouched")
    # CONTROL: pre-fix fallback would write the live path. Emulate it with the old fallback body.
    scn._AXIOM_FILE = fa
    with open(scn._AXIOM_FILE, "w", encoding="utf-8") as f:
        json.dump(SAMPLE, f, indent=2, ensure_ascii=False)
    check(_snap(fa) != a0, "CONTROL: the old fallback body (raw open of _AXIOM_FILE) does overwrite the live path")

    # -- [5] LIVE byte-identity ---------------------------------------------------------------------------------------
    print("\n[5] live process: fenced vault == verbatim pre-fix write()/_ledger")
    P.LIVE = True
    clock = {"t": 1_700_000_000.0}

    def _tick():
        clock["t"] += 1.5
        return clock["t"]
    iv.time.time = _tick

    def _run(fn, d: Path):
        d.mkdir(parents=True, exist_ok=True)
        _aim(d / "axiom.json", d / "vault_log.jsonl")
        clock["t"] = 1_700_000_000.0
        rets = []
        rets.append(fn(SAMPLE, reason="r1", meta={"k": 1}))
        s2 = json.loads(json.dumps(SAMPLE))
        s2["L3_facets"]["facets"][0]["revision_count"] = 4
        s2["L3_facets"]["facets"][0]["self_image"] = "  multi\n line  " + "x" * 300 + " 渡"
        rets.append(fn(s2, reason="r" * 200, meta=None))
        rets.append(fn({"bad": object()}, reason="unserializable"))          # json.dump raises -> False
        (d / "axiom.json.tmp").unlink(missing_ok=True)
        rets.append(fn({"schema": "legacy", "emergent_self": {}}, reason="legacy"))
        return rets, (d / "axiom.json").read_bytes(), (d / "vault_log.jsonl").read_bytes()

    ref = _run(_ref_write, TMP / "live_ref")
    new = _run(iv.write, TMP / "live_new")
    check(ref[0] == new[0] == [True, True, False, True], f"return values identical: {ref[0]} vs {new[0]}")
    check(ref[1] == new[1], f"axiom.json bytes identical ({len(ref[1])} bytes)")
    check(ref[2] == new[2] and ref[2].count(b"\n") == 3, f"vault_log.jsonl bytes identical ({ref[2].count(bytes([10]))} rows, fixed clock)")
    # I/O error path: the axiom's parent is a FILE -> mkdir raises -> False in both
    for nm, fn in (("ref", _ref_write), ("new", iv.write)):
        blocker = TMP / f"blocker_{nm}"
        blocker.write_text("x", encoding="utf-8")
        _aim(blocker / "axiom.json", blocker / "vault_log.jsonl")
        check(fn(SAMPLE, reason="io") is False, f"I/O error path ({nm}) returns False, raises nothing")
    iv.time.time = _orig["time"]
    # commit() round-trip in live mode
    _aim(TMP / "live_c" / "axiom.json", TMP / "live_c" / "vault_log.jsonl")
    iv.write(SAMPLE, reason="seed")
    got = iv.commit(lambda d: d.__setitem__("added", 1), reason="c")
    check(got.get("added") == 1 and json.loads((TMP / "live_c" / "axiom.json").read_text(encoding="utf-8")).get("added") == 1,
          "live commit() read-modify-write still lands")

    # -- [6] legitimate redirects -----------------------------------------------------------------------------------
    print("\n[6] non-live: legitimate redirects still write")
    P.LIVE = False
    P._DATA = P._CANONICAL_DATA = fake
    lab = fake / "_lab" / "20261004_000000" / "identity"
    lab.mkdir(parents=True)
    _aim(lab / "axiom.json", lab / "vault_log.jsonl")
    check(iv.write(SAMPLE, reason="lab") is True and (lab / "axiom.json").exists(), "data/_lab/<stamp>/ sandbox writes")
    out_d = TMP / "outside"
    _aim(out_d / "axiom.json", out_d / "vault_log.jsonl")
    check(iv.write(SAMPLE, reason="out") is True and (out_d / "axiom.json").exists(), "a path outside data/ writes (brick3-style tmp redirect)")
    _aim(fake / "_lab" / "axiom.json", fake / "_lab" / "vault_log.jsonl")
    check(iv.write(SAMPLE, reason="bad") is False and not (fake / "_lab" / "axiom.json").exists(), "data/_lab/<file> directly stays refused")

    # -- [7] visibility -----------------------------------------------------------------------------------------------
    print("\n[7] the swallowed refusal is not silent")
    recs: list = []

    class _H(logging.Handler):
        def emit(self, r):
            recs.append(r)
    h = _H()
    plog = logging.getLogger(P.logger.name)
    plog.addHandler(h)
    try:
        P._warned.clear()
        _aim(fa, fl)
        iv.write(SAMPLE)
        iv.write(SAMPLE)
    finally:
        plog.removeHandler(h)
    warns = [r for r in recs if r.levelno == logging.WARNING]
    check(len(warns) == 1 and "refused" in warns[0].getMessage(), f"exactly one profile WARNING for the repeated refusal ({len(warns)})")
finally:
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    _aim(_orig["AXIOM"], _orig["LOG"])
    scn._AXIOM_FILE = _orig["SAF"]
    iv.time.time = _orig["time"]
    builtins.open, os.replace = _real_open, _real_replace

# -- [8] canary -------------------------------------------------------------------------------------------------------
print("\n[8] canary")
check(all(_snap(p) == _before[p] for p in _WATCH), "the live identity files (and this tree's defaults) are byte-identical to the start of the run")
shutil.rmtree(TMP, ignore_errors=True)
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
