"""
Regression: core/satisfaction.py sits behind the D-0179 write fence (J-1783 / F-2406).

The gap: satisfaction._LOG / _STATE are plain module-level paths and record() never went through
profile.guard_path, unlike the ~21 other fenced modules -- so ANY process that merely imported the module and
reached record() wrote Du's REAL data/satisfaction_log.jsonl and data/satisfaction_state.json. On 2026-10-04
scripts/exploratory_ignition_test.py (its temp-redirects covered core.frontier only) did exactly that from the
shared tree: 30 frontier_born rows appended and, quieter, the on-disk state fast-forwarded by 9.5 h of decay
(record() decays every accumulator by the time since last_ts on EVERY call). It stayed hidden in job-run worktrees
only because the __file__-relative data/ there is the worktree's own empty directory.

The build: record() resolves BOTH write targets through profile.guard_path before any I/O (before even _load()),
inside its own fail-open try -- the refusal is logged and swallowed, never raised into any of its call sites.
A live process (profile.mark_live()) gets the same paths back, so Du's behaviour is byte-identical.

What this proves, ISOLATED (no model, no live data -- every write goes to a temp dir or a SIMULATED data/ root, or is
trapped before it can reach disk, and the real satisfaction files are hashed before and after):
  [1] surface     public names/signature unchanged; the module's `profile` is core.profile; guard_path on the REAL paths
  [2] the leak    (simulated data/ root) CONTROL: the pre-fix record() (verbatim copy below) rewrites both files in a
                  non-live process -- so this test can fail; the fenced record() leaves them byte-identical (size +
                  sha256), creates no file, leaves last_ts (the decay clock) alone, returns None, raises nothing
  [3] real paths  both writes TRAPPED (recorded, never executed) with _STATE/_LOG aimed at the REAL C:\\Nascence\\data
                  files: the pre-fix record() reaches both; the fenced one reaches neither -- independent of the
                  simulated root, and safe to run from ANY tree
  [4] live        (profile.LIVE = True) fenced and pre-fix record() leave byte-identical state AND log files over a
                  fixed-clock event sequence (cap, decay, unknown event, non-ASCII target); real I/O errors (state
                  parent is a file / log is a directory) stay fail-open and identical
  [5] legit       a data/_lab/<stamp>/ sandbox and a path outside data/ (the J-0870 / J-0928 style redirects) still
                  write in a non-live process; data/_lab/<file> directly stays refused
  [6] visibility  the swallowed refusal is NOT silent: one profile WARNING per path + a satisfaction debug line
  [7] reads       an unknown event touches nothing and warns about nothing; snapshot() stays a pure read
  [8] call site   the real core.frontier.note_question path of the incident (frontier's own paths redirected, satisfaction's
                  not): CONTROL leaks with the pre-fix record(); fenced, all 10 births still succeed and the files
                  are byte-identical
  [9] canary      the live satisfaction files and this tree's default paths are byte-identical to the start of the run

  python scripts/_test_satisfaction_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import inspect
import io
import json
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1783_satisfaction_fence_"))
print("isolated store dir:", TMP)

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_LOG = _LIVE_DATA / "satisfaction_log.jsonl"
_LIVE_STATE = _LIVE_DATA / "satisfaction_state.json"
_DEFAULT_LOG = ROOT / "data" / "satisfaction_log.jsonl"        # where THIS tree's module defaults point
_DEFAULT_STATE = ROOT / "data" / "satisfaction_state.json"     # (the live files themselves when run from C:\Nascence)
_WATCH = {_LIVE_LOG, _LIVE_STATE, _DEFAULT_LOG, _DEFAULT_STATE}


def _snap(p: Path):
    """(size, sha256) of a file, None if absent -- a byte-exact fingerprint, never mtime alone."""
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

from core import profile as P            # noqa: E402
from core import satisfaction as sat     # noqa: E402
from core import frontier as fr          # noqa: E402

_orig = dict(STATE=sat._STATE, LOG=sat._LOG, record=sat.record, DATA=P._DATA, CANON=P._CANONICAL_DATA,
             LIVE=P.LIVE, F=fr._F, FL=fr._F_LIGHT, time=time.time)
_real_record = sat.record

# The pre-J-1783 record(), verbatim -- the CONTROL every "unchanged" claim below is measured against.
_REFERENCE_SRC = r'''
def record(event: str, target: str = "") -> None:
    try:
        now = time.time()
        kind = "liking" if event in _LIKING_EVENTS else "wanting" if event in _WANTING_EVENTS else None
        if kind is None:
            return
        weight, domain = (_LIKING_EVENTS if kind == "liking" else _WANTING_EVENTS)[event]
        state = _load()
        _decay(state, now)
        state[kind][domain] = round(min(5.0, state[kind].get(domain, 0.0) + weight), 4)
        _STATE.write_text(json.dumps(state), encoding="utf-8")
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "event": event, "kind": kind,
                                "domain": domain, "target": target, "weight": weight},
                               ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[satisfaction] record failed (non-fatal): %s", exc)
'''
_ref_ns = dict(vars(sat))
exec(_REFERENCE_SRC, _ref_ns)
_ref_record = _ref_ns["record"]


def _aim(state: Path, log: Path) -> None:
    """Point the module (and the reference copy, which shares its helpers) at one pair of files."""
    sat._STATE = _ref_ns["_STATE"] = state
    sat._LOG = _ref_ns["_LOG"] = log


def _plant(state: Path, log: Path, last_ts: float = 1_000_000_000.0) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"liking": {"self": 1.5, "world": 0.25, "relational": 0.5, "creative": 0.0},
                                 "wanting": {"self": 2.5, "world": 4.0, "relational": 0.0, "creative": 0.75},
                                 "last_ts": last_ts}), encoding="utf-8")
    log.write_text("".join(json.dumps({"ts": last_ts + i, "event": "light_event", "kind": "liking", "domain": "self",
                                       "target": "", "weight": 0.15}) + "\n" for i in range(3)), encoding="utf-8")


def _names(d: Path):
    return sorted(x.name for x in d.iterdir())


fake = TMP / "fake_root" / "data"          # a SIMULATED data/ root -- the real one is never a write target here
fake.mkdir(parents=True)
st, lg = fake / "satisfaction_state.json", fake / "satisfaction_log.jsonl"

try:
    # ── [1] surface ───────────────────────────────────────────────────────────────────────────────────────────────
    print("\n[1] surface")
    check(getattr(sat, "profile", None) is P, "core.satisfaction.profile is core.profile (one module object, so mark_live() reaches it)")
    check(sat._STATE == ROOT / "data" / "satisfaction_state.json" and sat._LOG == ROOT / "data" / "satisfaction_log.jsonl",
          "_STATE / _LOG keep their names and defaults (scripts/satisfaction_backfill.py imports _STATE)")
    _params = inspect.signature(sat.record).parameters
    check(list(_params) == ["event", "target"] and _params["target"].default == "",
          f"record()'s signature is unchanged: {inspect.signature(sat.record)}")
    P.LIVE = False
    try:
        P.guard_path(_LIVE_STATE)
        check(False, "guard_path refuses the REAL satisfaction_state.json in a non-live process")
    except P.NonLiveWriteError:
        check(True, "guard_path refuses the REAL satisfaction_state.json in a non-live process (pure check, no I/O)")
    P.LIVE = True
    check(P.guard_path(_LIVE_LOG) == _LIVE_LOG, "...and hands the REAL satisfaction_log.jsonl back untouched once live")
    P.LIVE = False

    # ── [2] the leak, reproduced and closed (simulated data/ root) ────────────────────────────────────────────────────
    print("\n[2] non-live process, default data/ paths (simulated root)")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(st, lg)
    _plant(st, lg)
    s0, l0, names0 = _snap(st), _snap(lg), _names(fake)
    for _ in range(30):
        _ref_record("frontier_born")
    check(_snap(st) != s0 and _snap(lg) != l0 and json.loads(st.read_text())["last_ts"] != 1_000_000_000.0,
          "CONTROL: the pre-fix record() rewrites the state (decay clock fast-forwarded) AND the log in a non-live process")
    _plant(st, lg)
    s0, l0 = _snap(st), _snap(lg)
    rets = [sat.record("frontier_born") for _ in range(30)]
    check(all(r is None for r in rets), "fenced: 30 record() calls return None and raise nothing")
    check(_snap(st) == s0, "fenced: satisfaction_state.json byte-identical (size + sha256) after 30 refused calls")
    check(_snap(lg) == l0, "fenced: satisfaction_log.jsonl byte-identical (size + sha256) after 30 refused calls")
    check(json.loads(st.read_text())["last_ts"] == 1_000_000_000.0, "fenced: the on-disk decay clock (last_ts) was not advanced")
    check(_names(fake) == names0, f"fenced: no new file appeared next to them ({_names(fake)})")

    # ── [3] the REAL paths, writes trapped ──────────────────────────────────────────────────────────────────────────
    print("\n[3] REAL C:\\Nascence\\data paths with both writes trapped (recorded, never executed)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], False
    PROTECTED = {str(_LIVE_STATE).lower(), str(_LIVE_LOG).lower()}
    HITS: list = []
    _had = "write_text" in vars(Path)
    _orig_wt = Path.write_text

    def _trap_write_text(self, *a, **k):
        if str(self).lower() in PROTECTED:
            HITS.append(("write_text", str(self)))
            return 0
        return _orig_wt(self, *a, **k)

    def _trap_open(file, mode="r", *a, **k):
        if str(file).lower() in PROTECTED and any(c in mode for c in "wax+"):
            HITS.append(("open-" + mode, str(file)))
            return io.StringIO()
        return builtins.open(file, mode, *a, **k)

    _aim(_LIVE_STATE, _LIVE_LOG)
    Path.write_text = _trap_write_text
    sat.open = _ref_ns["open"] = _trap_open
    try:
        _ref_record("frontier_born")
        ref_hits = list(HITS)
        HITS.clear()
        for _ in range(30):
            sat.record("frontier_born")
        fenced_hits = list(HITS)
    finally:
        if _had:
            Path.write_text = _orig_wt
        else:
            del Path.write_text
        del sat.open
        _ref_ns.pop("open", None)
    check(len(ref_hits) == 2, f"CONTROL: the pre-fix record() reaches BOTH real writes ({[h[0] for h in ref_hits]})")
    check(not fenced_hits, f"fenced: 30 calls reach neither real write ({fenced_hits})")

    # ── [4] live behaviour identical ──────────────────────────────────────────────────────────────────────────────────
    print("\n[4] live process (profile.LIVE = True): fenced == pre-fix, byte for byte")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = True
    T = [1_800_000_000.0]
    time.time = lambda: T[0]
    HEAD = [("t4_commit", ""), ("frontier_born", ""), ("light_event", ""), ("shadow_event", ""), ("bogus_event", "x"),
            ("clean_exchange", "travis"), ("reunion", "travis"), ("study_tablet", "ünïcode – tablet ✓"),
            ("commitment_dissolved", "stand"), ("unresolved_thought", ""), ("curiosity_fired", ""),
            ("chapter_formed", ""), ("tension_discharged", ""), ("intention_formed", ""), ("commitment_held", "x")] * 5
    TAIL = [("t4_commit", "")] * 12                                  # drives liking.self into the 5.0 cap at a frozen clock
    STEPS = [0.0, 1.0, 37.5, 3600.0, 90000.0]

    def drive(rec, state_p, log_p):
        _aim(state_p, log_p)
        _plant(state_p, fake / "scratch_unused.jsonl", last_ts=1_800_000_000.0 - 7200)
        (fake / "scratch_unused.jsonl").unlink()
        log_p.unlink(missing_ok=True)
        T[0] = 1_800_000_000.0
        for i, (ev, tg) in enumerate(HEAD + TAIL):
            T[0] += STEPS[i % len(STEPS)] if i < len(HEAD) else 0.0
            rec(ev, tg)

    drive(sat.record, fake / "live_new_state.json", fake / "live_new_log.jsonl")
    drive(_ref_record, fake / "live_old_state.json", fake / "live_old_log.jsonl")
    new_s, old_s = (fake / "live_new_state.json").read_bytes(), (fake / "live_old_state.json").read_bytes()
    new_l, old_l = (fake / "live_new_log.jsonl").read_bytes(), (fake / "live_old_log.jsonl").read_bytes()
    n_known = sum(1 for e, _ in HEAD + TAIL if e in sat._LIKING_EVENTS or e in sat._WANTING_EVENTS)
    check(new_s == old_s and len(new_s) > 100, f"state file bytes identical to the pre-fix record() ({len(new_s)} B)")
    check(new_l == old_l and new_l.count(b"\n") == n_known,
          f"log file bytes identical, one row per KNOWN event and none for the unknown one ({new_l.count(chr(10).encode())} rows)")
    check(json.loads(new_s)["liking"]["self"] == 5.0, "the 5.0 cap was exercised and identical")
    check(b"\\u" not in new_l and "ünïcode – tablet ✓".encode("utf-8") in new_l, "ensure_ascii=False target survives byte-identically")
    blocker = fake / "blocker_file"
    blocker.write_text("x")
    for tag, rec in (("fenced", sat.record), ("pre-fix", _ref_record)):
        _aim(blocker / "s.json", fake / f"io1_{tag}.jsonl")
        r = rec("light_event")
        check(r is None and not (fake / f"io1_{tag}.jsonl").exists(),
              f"{tag}: state parent is a FILE -> real I/O error swallowed (None), no log row (fail-open unchanged)")
    for tag, rec in (("fenced", sat.record), ("pre-fix", _ref_record)):
        d = fake / f"logdir_{tag}"
        d.mkdir()
        _aim(fake / f"io2_{tag}_state.json", d)
        T[0] = 1_800_000_000.0
        r = rec("light_event")
        check(r is None and (fake / f"io2_{tag}_state.json").exists(), f"{tag}: log path is a DIRECTORY -> swallowed (None), state already written")
    check((fake / "io2_fenced_state.json").read_bytes() == (fake / "io2_pre-fix_state.json").read_bytes(), "...and those two state files are identical")
    time.time = _orig["time"]

    # ── [5] legitimate redirects still write ──────────────────────────────────────────────────────────────────────────
    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    lab = fake / "_lab" / "20261004_000000"
    lab.mkdir(parents=True)
    _aim(lab / "satisfaction_state.json", lab / "satisfaction_log.jsonl")
    sat.record("light_event")
    check((lab / "satisfaction_state.json").exists() and (lab / "satisfaction_log.jsonl").read_text().count("\n") == 1,
          "data/_lab/<stamp>/ (lab_env.isolate()'s sandbox) writes both files")
    _aim(fake / "_lab" / "satisfaction_state.json", fake / "_lab" / "satisfaction_log.jsonl")
    sat.record("light_event")
    check(not (fake / "_lab" / "satisfaction_state.json").exists() and not (fake / "_lab" / "satisfaction_log.jsonl").exists(),
          "data/_lab/<file> with no sandbox directory stays refused")
    _aim(TMP / "outside_state.json", TMP / "outside_log.jsonl")
    sat.record("light_event")
    check((TMP / "outside_state.json").exists() and (TMP / "outside_log.jsonl").read_text().count("\n") == 1,
          "a path outside data/ (boredom_redirect_test / _test_isolation style temp redirect) writes both files")

    # ── [6] the swallowed refusal is not silent ───────────────────────────────────────────────────────────────────────
    print("\n[6] visibility")

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.rows = []

        def emit(self, record):
            self.rows.append((record.name, record.levelno, record.getMessage()))

    cap = _Cap()
    _lg = {n: logging.getLogger(n) for n in ("nascence.profile", "nascence.satisfaction")}
    _lv = {n: l.level for n, l in _lg.items()}
    for l in _lg.values():
        l.addHandler(cap)
        l.setLevel(logging.DEBUG)
    try:
        _aim(st, lg)
        _plant(st, lg)
        P._warned.discard(str(st))
        sat.record("frontier_born")
        sat.record("frontier_born")
        warn = [r for r in cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING and "satisfaction_state.json" in r[2]]
        dbg = [r for r in cap.rows if r[0] == "nascence.satisfaction" and "record failed" in r[2] and "refused" in r[2]]
        check(len(warn) == 1, f"guard_path logs ONE warning per path naming satisfaction_state.json ({len(warn)})")
        check(len(dbg) == 2, f"record() logs a debug line carrying the refusal text on every swallowed call ({len(dbg)})")
        cap.rows.clear()

        # ── [7] reads ─────────────────────────────────────────────────────────────────────────────────────────────────
        print("\n[7] unknown event / snapshot()")
        s0, l0 = _snap(st), _snap(lg)
        P._warned.discard(str(st))
        sat.record("not_an_event")
        check(not cap.rows and _snap(st) == s0 and _snap(lg) == l0, "an unknown event touches nothing and logs nothing (no guard call)")
        snap = sat.snapshot()
        check(set(snap) == {"liking", "wanting", "gap"} and set(snap["gap"]) == set(sat.DOMAINS), "snapshot() still returns its three maps")
        check(_snap(st) == s0 and _snap(lg) == l0, "...and stays a pure read under a non-live process (files byte-identical)")
    finally:
        for n, l in _lg.items():
            l.removeHandler(cap)
            l.setLevel(_lv[n])

    # ── [8] the incident's own call path ──────────────────────────────────────────────────────────────────────────────
    print("\n[8] call site: core.frontier.note_question with ONLY frontier's paths redirected")
    QS = ["why does capillary action lift water in a narrow tube", "what makes granite form its strange surface coatings",
          "how do distant stars produce their steady light", "why do rivers meander across the flat plains",
          "what causes the ocean tides to rise and fall", "how do honeybees navigate back to the distant hive",
          "why does iron rust when left in the damp air", "how do buried seeds know which way is up",
          "why does solid ice float on top of liquid water", "what makes the evening sky turn red at sunset"]
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(st, lg)
    _plant(st, lg)
    fr._F, fr._F_LIGHT = TMP / "fr_control.json", TMP / "fr_control.light.json"
    s0, l0 = _snap(st), _snap(lg)
    sat.record = _ref_record
    try:
        born = [fr.note_question(q, "curiosity") for q in QS]
    finally:
        sat.record = _real_record
    check(all(born) and _snap(st) != s0 and _snap(lg) != l0,
          "CONTROL: 10 frontier births with the pre-fix record() leak into both satisfaction files (the F-2406 shape)")
    _plant(st, lg)
    fr._F, fr._F_LIGHT = TMP / "fr_fenced.json", TMP / "fr_fenced.light.json"
    s0, l0 = _snap(st), _snap(lg)
    born = [fr.note_question(q, "curiosity") for q in QS]
    check(all(born), "fenced: all 10 births still succeed -- the swallowed refusal never reaches frontier's flow")
    check(_snap(st) == s0 and _snap(lg) == l0, "fenced: both satisfaction files byte-identical after the 10 births")
finally:
    sat._STATE, sat._LOG, sat.record = _orig["STATE"], _orig["LOG"], _orig["record"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    fr._F, fr._F_LIGHT = _orig["F"], _orig["FL"]
    time.time = _orig["time"]
    if hasattr(sat, "open"):
        del sat.open

# ── [9] canary ──────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[9] canary")
_after = {p: _snap(p) for p in _WATCH}
check(_after == _before,
      "the live satisfaction files and this tree's default paths are byte-identical to the start of the run "
      f"(live log {_after[_LIVE_LOG][0] if _after[_LIVE_LOG] else None} B, live state {_after[_LIVE_STATE][0] if _after[_LIVE_STATE] else None} B)")
check(sat._STATE == ROOT / "data" / "satisfaction_state.json", "the module's own paths were restored")
shutil.rmtree(TMP, ignore_errors=True)
print("\n" + ("ALL OK" if not FAILS else f"{FAILS} FAILED"))
sys.exit(1 if FAILS else 0)
