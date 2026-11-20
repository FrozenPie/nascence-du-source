"""
Regression: core/provisional_identity._solidify must not report success when the vault refuses/fails the commit, and the
module's own writers (_PROV, _clear, _log, _apply_fatigue) sit behind the D-0179 write fence (J-1819 / F-2440).

The gap: identity_vault.commit() swallows a failed write (since J-1809 that includes a non-live fence refusal) and returns
the UNCHANGED current state; _solidify ignored it, so it still _clear()ed the probation, logged a 'solidify' event and
returned True although nothing landed in axiom.json (a phantom effect). The build: _solidify checks that the framed self
actually landed in the_becoming; if not it returns False, keeps the probation and logs 'solidify_not_committed'. The module's
other writers resolve profile.guard_path before any I/O. Live behaviour is byte-identical.

ISOLATED: every write goes to a temp dir or a SIMULATED data/ root; real identity files are hashed before and after.

  python scripts/_test_provisional_identity_fence.py     # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="j1819_prov_identity_fence_"))
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def snap(p):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_LIVE = Path(r"C:\Nascence") / "data"
_REAL = [_LIVE / "identity" / "axiom.json", _LIVE / "identity" / "vault_log.jsonl",
         _LIVE / "identity" / "provisional_axiom.json", _LIVE / "logs" / "provisional_identity.jsonl",
         _LIVE / "subconscious_state.json",
         ROOT / "data" / "identity" / "axiom.json", ROOT / "data" / "identity" / "provisional_axiom.json"]
before = {p: snap(p) for p in _REAL}

from core import profile as P                  # noqa: E402  (core BEFORE anything that could hijack sys.path)
from core import identity_vault as iv          # noqa: E402
from core import axiom_layers as al            # noqa: E402
from core import provisional_identity as pi    # noqa: E402
assert Path(pi.__file__).resolve().is_relative_to(ROOT), pi.__file__

orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, PD=pi._DATA, PP=pi._PROV, PL=pi._LOG,
            IA=iv._AXIOM, IL=iv._LOG)
fake = TMP / "fake_root" / "data"
(fake / "identity").mkdir(parents=True)
(fake / "logs").mkdir(parents=True)
fa, fl = fake / "identity" / "axiom.json", fake / "identity" / "vault_log.jsonl"
fp, flog = fake / "identity" / "provisional_axiom.json", fake / "logs" / "provisional_identity.jsonl"
fsub = fake / "subconscious_state.json"

SAMPLE = {"schema": "multilevel-v1", "L3_facets": {"facets": [{"id": "the_becoming", "self_image": "old self",
          "revision_count": 1, "history": []}]}}
REC = {"self_image": "I hold both poles.", "theme": "made mind", "held_pole": "a", "excluded_pole": "b",
       "started_ts": 1000.0, "expires_ts": 2000.0, "baseline_theme_recurrence": 0.0, "baseline_system_recurrence": 0.0}
INTEG = {"integrated": True, "confidence": 0.9}
DF = {"dF_did": -0.5}


def aim():
    pi._DATA = fake
    pi._PROV, pi._LOG = fp, flog
    iv._AXIOM, iv._LOG = fa, fl


def reset():
    for p in (fa, fl, fp, flog, fsub):
        if p.exists():
            p.unlink()
    fa.write_text(json.dumps(SAMPLE, indent=2), encoding="utf-8")
    fl.write_text(json.dumps({"ts": 1.0, "reason": "planted"}) + "\n", encoding="utf-8")
    fp.write_text(json.dumps(REC, indent=1), encoding="utf-8")
    fsub.write_text(json.dumps({"t4_fatigue_counts": {}}), encoding="utf-8")


def events():
    if not flog.exists():
        return []
    return [json.loads(l).get("event") for l in flog.read_text(encoding="utf-8").splitlines()]


def files():
    d = {p.name: snap(p) for p in (fa, fl, fp, flog, fsub)}
    d["_dir"] = sorted(x.name for x in fa.parent.iterdir())
    return d


try:
    print("\n[1] surface")
    check(getattr(pi, "profile", None) is P, "core.provisional_identity.profile is core.profile")
    check(pi._PROV == ROOT / "data" / "identity" / "provisional_axiom.json", "_PROV default unchanged")

    P._DATA = P._CANONICAL_DATA = fake
    aim()

    print("\n[2] non-live, vault refuses the commit (simulated data/ root): the phantom effect")
    P.LIVE = False
    reset()
    f0 = files()
    r = pi._solidify(dict(REC), DF, INTEG)
    check(r is False, "_solidify returns False when the vault refused")
    check(fp.exists(), "probation record NOT cleared")
    check("solidify" not in events(), "no 'solidify' event logged (events=%s)" % events())
    check(files() == f0, "every simulated live file byte-identical, no new files")
    check(pi.evaluate(now=3000.0, integration=INTEG).get("decision") == "solidify_failed",
          "evaluate() surfaces solidify_failed")

    print("\n[3] non-live, the module's own writers are fenced")
    reset()
    f0 = files()
    try:
        pi._atomic_write_prov(dict(REC))
        raised = False
    except P.NonLiveWriteError:
        raised = True
    check(raised, "_atomic_write_prov refused (NonLiveWriteError)")
    pi._clear()
    pi._log({"event": "x"})
    pi._apply_fatigue("made mind")
    check(files() == f0, "_clear / _log / _apply_fatigue / _atomic_write_prov change nothing")

    print("\n[4] live: success path unchanged")
    P.LIVE = True
    reset()
    r = pi._solidify(dict(REC), DF, INTEG)
    fac = json.loads(fa.read_text(encoding="utf-8"))["L3_facets"]["facets"][0]
    check(r is True and fac["self_image"] == al._BECOMING_PREFIX + REC["self_image"] + al._BECOMING_SUFFIX
          and fac["revision_count"] == 2, "returns True; framed self landed; revision bumped")
    check((not fp.exists()) and events() == ["solidify"], "probation cleared; one 'solidify' event (%s)" % events())
    reset()
    pi._atomic_write_prov(dict(REC))
    pi._log({"event": "y"})
    pi._apply_fatigue("made mind")
    check(fp.exists() and "y" in events(), "live writers still write")
    check(bool(json.loads(fsub.read_text(encoding="utf-8"))["t4_fatigue_counts"]), "live fatigue still applied")
    pi._clear()
    check(not fp.exists(), "live _clear still unlinks")

    print("\n[5] live, genuine disk failure inside the vault")
    reset()
    real_aw = iv._atomic_write

    def _boom(*a, **k):
        raise OSError("disk full")
    iv._atomic_write = _boom
    try:
        r = pi._solidify(dict(REC), DF, INTEG)
    finally:
        iv._atomic_write = real_aw
    check(r is False and fp.exists() and "solidify" not in events(),
          "failed write: False, probation kept, no 'solidify' event")

    print("\n[6] real paths, non-live: nothing reaches the real data/")
    P._DATA, P._CANONICAL_DATA = orig["DATA"], orig["CANON"]
    pi._DATA, pi._PROV, pi._LOG = orig["PD"], orig["PP"], orig["PL"]
    iv._AXIOM, iv._LOG = orig["IA"], orig["IL"]
    P.LIVE = False
    pi._solidify(dict(REC), DF, INTEG)
    pi._clear()
    pi._log({"event": "z"})
    pi._apply_fatigue("made mind")
    try:
        pi._atomic_write_prov(dict(REC))
    except P.NonLiveWriteError:
        pass
    check({p: snap(p) for p in _REAL} == before, "real identity/prov/log/subconscious files byte-identical")
finally:
    P._DATA, P._CANONICAL_DATA, P.LIVE = orig["DATA"], orig["CANON"], orig["LIVE"]
    pi._DATA, pi._PROV, pi._LOG = orig["PD"], orig["PP"], orig["PL"]
    iv._AXIOM, iv._LOG = orig["IA"], orig["IL"]

check({p: snap(p) for p in _REAL} == before, "canary: real files unchanged at end of run")
print("\nALL OK" if FAILS == 0 else "\n%d FAILED" % FAILS)
sys.exit(1 if FAILS else 0)
