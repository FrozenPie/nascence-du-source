"""
Regression: core/prediction_error.py sits behind the D-0179 write fence (J-1799 / F-2416).

The gap: prediction_error._STATE / _RAW / _SHADOW are plain __file__-relative module-level paths and observe() never went
through profile.guard_path, unlike the ~22 other fenced modules -- so ANY process that merely imported the module (or
core.competence, whose record_drill_accuracy() calls observe()) and reached observe() wrote Du's REAL
data/prediction_error_log.jsonl, data/prediction_error_state.json and data/logs/shadow_integrity.jsonl. On 2026-10-04 at 16:49:37
a practical-lesson replay did exactly that while Du was down (4 fieldcraft rows, 4 recurrence timestamps, 8 L1 shadow rows; the
orchestrator repaired them, F-2422). scripts/_test_practical_lesson.py imported lab_env BEFORE core and lab_env then put the SHARED
tree first on sys.path (F-2423, since fixed), so a "worktree" run executed the shared tree's unfenced module.

The build: observe() resolves all three write targets through profile.guard_path before any I/O, inside its own fail-open try
(the refusal is logged and swallowed, never raised into a caller, and the gate / DB insert behind it are never reached);
_save_state() resolves its own path outside its swallow. A live process (profile.mark_live()) gets the same paths back, so Du's
behaviour is byte-identical.

What this proves, ISOLATED (no model, no DB, no live data -- every write goes to a temp dir or a SIMULATED data/ root, or is
trapped before it can reach disk, store_shadow_event is a recording stub, and the live files are hashed before and after; it is
safe to run from ANY tree, including against the pre-fix module):
  [1] surface     public names/signatures unchanged; the module's `profile` is core.profile; guard_path refuses the 3 REAL files
  [2] the leak    (simulated data/ root) CONTROL: the pre-fix observe() (verbatim copy below) writes all three files AND reaches
                  the store_shadow_event insert in a non-live process, so this test can fail; the fenced observe() leaves all three
                  byte-identical (size + sha256), creates no file, returns None, raises nothing and never reaches the insert;
                  the private writers (_save_state, _bump) are refused too
  [3] real paths  every write TRAPPED (recorded, never executed) with the module aimed at the REAL C:\\Nascence\\data files: the
                  pre-fix observe() reaches all three, the fenced one reaches none
  [4] live        (profile.LIVE = True) fenced and pre-fix modules leave byte-identical state (indent=1), raw log and shadow log
                  over a fixed-clock sequence (gap threshold, recurrence, 14-day window, 50-entry cap, non-ASCII event text,
                  bad input, a failing DB insert) with identical return values and identical store_shadow_event calls; real I/O
                  errors (state parent is a file / raw log is a directory) stay fail-open and identical
  [5] legit       a data/_lab/<stamp>/ sandbox and a path outside data/ still write in a non-live process; data/_lab/<file> stays
                  refused; a PARTIAL redirect (one of the three still on data/) is refused wholesale, no half-write
  [6] visibility  the swallowed refusal is NOT silent: one profile WARNING per path + a debug line per refused call; bad input
                  never reaches the guard
  [7] reads       status() stays a pure read under a non-live process
  [8] call site   the incident's own path, core.competence.record_drill_accuracy -> observe(): CONTROL leaks into all three files
                  with the pre-fix observe(); fenced, the 4 calls still return their belief dicts and the files are byte-identical
  [9] canary      the live files and this tree's default paths are byte-identical to the start of the run

  python scripts/_test_prediction_error_fence.py        # exit 0 = ALL OK
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
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE every other core import, and asserted (F-2423): a test that lets ANOTHER tree's core win runs the wrong code
_core_file = Path(core.__file__).resolve()
assert ROOT in _core_file.parents, f"core resolves to {_core_file}, not inside {ROOT} -- refusing to run"

TMP = Path(tempfile.mkdtemp(prefix="j1799_prediction_error_fence_"))
print("core package:", _core_file)
print("isolated store dir:", TMP)

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE = {"state": _LIVE_DATA / "prediction_error_state.json",
         "raw": _LIVE_DATA / "prediction_error_log.jsonl",
         "shadow": _LIVE_DATA / "logs" / "shadow_integrity.jsonl"}
_DEFAULT = {k: ROOT / "data" / v.relative_to(_LIVE_DATA) for k, v in _LIVE.items()}   # where THIS tree's module defaults point
_WATCH = (set(_LIVE.values()) | set(_DEFAULT.values())
          | {_LIVE_DATA / "satisfaction_log.jsonl", _LIVE_DATA / "satisfaction_state.json"})   # the store_shadow_event hook's neighbour


def _snap(p: Path):
    """(size, sha256) of a file, None if absent -- a byte-exact fingerprint, never mtime alone."""
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


def _bytes(p: Path):
    return p.read_bytes() if p.exists() else None


_before = {p: _snap(p) for p in _WATCH}

from core import profile as P                   # noqa: E402
from core import prediction_error as pe         # noqa: E402
from core import competence as comp             # noqa: E402
import core.memory.store as store               # noqa: E402

# The pre-J-1799 module, verbatim -- the CONTROL every "unchanged" claim below is measured against.
_OLD_SRC = r'''
"""
Nascence — Prediction-Error Feed (Layer 1, the self-generated contradiction channel)
====================================================================================
The cheapest, most-grounded, externally-independent contradiction source: |predicted − measured|.
Du ALREADY computes this every lesson (essay self-prediction vs Emissary grade; math felt-confidence
vs the deterministic grade — the "0.81-felt / 0.19-real" fluency trap). It is currently spent only on
competence calibration. This module ALSO routes a large, recurring gap through the contradiction gate
so a self-generated discrepancy can (eventually) pressure identity — no external critic required.
This is the documented developmental move: monitoring transfers from external feedback to a
self-generated error signal (Holroyd & Coles ERN). Research + plan: docs/completed/contradiction_rearchitecture_plan.md.

PHASE 0 = OBSERVE-FIRST. This logs what WOULD feed the tension_ledger; it writes NOTHING to the ledger
and changes no behaviour. Phase 1 flips `FEED_LEDGER` on after the shadow log is reviewed.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

FEED_LEDGER = True             # Phase 1 (2026-06-16): would_pressure signals now WRITE a prediction_error
                               # shadow event → the existing clustering folds it into a tension whose chronic
                               # mass T4 reads. Reversible kill-switch: set False to return to observe-only.
GAP_THRESHOLD = 0.40           # |predicted − measured| at/above which a gap is a candidate contradiction
REC_WINDOW_S = 14 * 86400      # recurrence window: large gaps in the same domain within 14 days

_STATE = Path(__file__).parent.parent / "data" / "prediction_error_state.json"
_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "shadow_integrity.jsonl"
_RAW = Path(__file__).parent.parent / "data" / "prediction_error_log.jsonl"

# How core each domain's skill is to the self-concept (the gate's importance term). Skills are
# moderately important — honest enough to pressure when they recur, not so core a single bad drill moves him.
_IMPORTANCE = {"mathematics": 0.35, "comprehension": 0.45}


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps(d, indent=1), encoding="utf-8")
    except Exception:
        pass


def _recurrence(domain: str, now: float) -> int:
    """How many large gaps in this domain fall inside the recurrence window (incl. this one)."""
    st = _load_state()
    hits = [t for t in st.get(domain, []) if now - t <= REC_WINDOW_S]
    return len(hits)


def _bump(domain: str, now: float) -> None:
    st = _load_state()
    hits = [t for t in st.get(domain, []) if now - t <= REC_WINDOW_S]
    hits.append(now)
    st[domain] = hits[-50:]
    _save_state(st)


def observe(domain: str, predicted: float, measured: float, event: str = "") -> dict | None:
    """Record one (predicted, measured) lesson outcome. Always logs the raw observation. If the gap is
    large, build a prediction-error signal, run it through the contradiction gate, and log the verdict
    (Phase 0) — or feed the chronic-mass accumulator (Phase 1, when FEED_LEDGER). Best-effort; returns
    the gate verdict or None. Never raises into the caller (a lesson must never fail on this)."""
    try:
        predicted = float(predicted); measured = float(measured)
        gap = abs(predicted - measured)
        now = time.time()
        rec = {"ts": now, "domain": domain, "predicted": round(predicted, 3),
               "measured": round(measured, 3), "gap": round(gap, 3), "large": gap >= GAP_THRESHOLD}
        _RAW.parent.mkdir(parents=True, exist_ok=True)
        with open(_RAW, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if gap < GAP_THRESHOLD:
            return None

        _bump(domain, now)
        signal = {
            "kind": "prediction_error",
            "concrete_ref": True,                       # bound to a real, dated lesson event
            "recurrence_count": _recurrence(domain, now),
            "resolution_axis": "re-study / practice",   # a real path to close the gap (behaviour change)
            "importance": _IMPORTANCE.get(domain, 0.35),
            "text": event or f"I predicted {predicted:.2f} on {domain} but measured {measured:.2f}",
            "domain": domain,
        }
        from core import contradiction_gate as _gate
        verdict = _gate.evaluate(signal)

        _SHADOW.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": now, "layer": "L1", "source": "prediction_error",
                                 "signal": signal, "verdict": verdict, "fed": False}, ensure_ascii=False) + "\n")

        if FEED_LEDGER and verdict.get("would_pressure"):
            try:
                # Phase 1: write a CONTRADICTION shadow event. The Subconscious clusters recurring
                # prediction-errors into a tension; the chronic-mass accumulator bumps it on recurrence.
                # ⚠ 2026-06-30: the old claim "the T4 gate reads that mass" is FALSE — T4's live commit is the
                # solidify judge; the cn/chronic-mass gate is the dormant ENABLED=False fallback. So this feed does
                # NOT drive T4 commit. It may still shape candidate SELECTION / acute pressure — unverified; the
                # whole chronic→T4 value is under re-examination (docs/staged/contradiction_rearchitecture_plan.md).
                # Rides the same store_shadow_event pipe as critic_rejection — no new tension code, no gate change.
                from core.memory import store as _ms
                _ms.store_shadow_event(
                    cycle_id="lesson",
                    raw_input=f"self-prediction on {domain}",
                    rejected_draft=signal["text"],
                    corrections=[f"prediction_error:{domain} (felt {predicted:.2f} vs real {measured:.2f})"],
                    source="prediction_error",
                )
                with open(_SHADOW, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": now, "layer": "L1", "source": "prediction_error",
                                         "fed": True, "domain": domain}, ensure_ascii=False) + "\n")
            except Exception:
                pass
        return verdict
    except Exception:
        return None


def status() -> dict:
    """Summary for the du_pulse gauge: large-gap recurrence per domain + would-pressure count."""
    try:
        st = _load_state()
        now = time.time()
        per = {d: len([t for t in ts if now - t <= REC_WINDOW_S]) for d, ts in st.items()}
        wp = fed = 0
        if _SHADOW.exists():
            for line in _SHADOW.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                    if r.get("source") != "prediction_error":
                        continue
                    if r.get("verdict", {}).get("would_pressure"):
                        wp += 1
                    if r.get("fed"):
                        fed += 1
                except Exception:
                    pass
        return {"recurrence_by_domain": per, "would_pressure_total": wp, "fed_total": fed,
                "feeding": FEED_LEDGER}
    except Exception:
        return {}
'''
ref = types.ModuleType("pe_pre_j1799")
ref.__file__ = str(ROOT / "core" / "prediction_error.py")
exec(compile(_OLD_SRC, "<pre-J-1799 core/prediction_error.py>", "exec", dont_inherit=True), ref.__dict__)

_orig = dict(STATE=pe._STATE, SHADOW=pe._SHADOW, RAW=pe._RAW, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE,
             observe=pe.observe, time=pe.time, store_fn=store.store_shadow_event, beliefs=comp._BELIEFS_FILE)
CALLS: list = []          # every store_shadow_event call (the DB insert behind the gate) -- a recording stub, never a real insert


def _stub_shadow(**k):
    CALLS.append(("ok", k))
    return "fake-id"


def _stub_raising(**k):
    CALLS.append(("raising", k))
    raise RuntimeError("db down")


store.store_shadow_event = _stub_shadow
T = [1_800_000_000.0]
_fake_time = types.SimpleNamespace(time=lambda: T[0])   # swapped in as the MODULES' `time` only -- logging etc. keep the real clock


def _aim(state: Path, shadow: Path, raw: Path) -> None:
    """Point the module (and the reference copy) at one trio of files."""
    for m in (pe, ref):
        m._STATE, m._SHADOW, m._RAW = state, shadow, raw


def _plant(state: Path, shadow: Path, raw: Path) -> None:
    for p in (state, shadow, raw):
        p.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"fieldcraft": [1_788_820_212.9, 1_788_820_231.9], "mathematics": [1_790_716_310.2]}, indent=1),
                     encoding="utf-8")
    shadow.write_text("".join(json.dumps({"ts": 1_791_046_033.0 + i, "layer": "L2", "source": "meta_awareness"}) + "\n" for i in range(3)),
                      encoding="utf-8")
    raw.write_text("".join(json.dumps({"ts": 1_790_716_310.0 + i, "domain": "mathematics", "predicted": 0.8, "measured": 0.2,
                                       "gap": 0.6, "large": True}) + "\n" for i in range(3)), encoding="utf-8")


def _tree(d: Path):
    return sorted(str(x.relative_to(d)) for x in d.rglob("*"))


fake = TMP / "fake_root" / "data"          # a SIMULATED data/ root -- the real one is never a write target here
(fake / "logs").mkdir(parents=True)
st, sh, rw = fake / "prediction_error_state.json", fake / "logs" / "shadow_integrity.jsonl", fake / "prediction_error_log.jsonl"

try:
    # ── [1] surface ───────────────────────────────────────────────────────────────────────────────────────────────
    print("\n[1] surface")
    check(getattr(pe, "profile", None) is P, "core.prediction_error.profile is core.profile (one module object, so mark_live() reaches it)")
    check(pe._STATE == ROOT / "data" / "prediction_error_state.json" and pe._RAW == ROOT / "data" / "prediction_error_log.jsonl"
          and pe._SHADOW == ROOT / "data" / "logs" / "shadow_integrity.jsonl",
          "_STATE / _RAW / _SHADOW keep their names and defaults (scripts/*_invitro.py and du_pulse read them)")
    _p = inspect.signature(pe.observe).parameters
    check(list(_p) == ["domain", "predicted", "measured", "event"] and _p["event"].default == "",
          f"observe()'s signature is unchanged: {inspect.signature(pe.observe)}")
    check(pe.FEED_LEDGER is True and pe.GAP_THRESHOLD == 0.40 and pe.REC_WINDOW_S == 14 * 86400,
          "FEED_LEDGER / GAP_THRESHOLD / REC_WINDOW_S unchanged (True / 0.40 / 14 days)")
    P.LIVE = False
    refused = []
    for name, path in _LIVE.items():
        try:
            P.guard_path(path)
        except P.NonLiveWriteError:
            refused.append(name)
    check(refused == ["state", "raw", "shadow"], f"guard_path refuses all 3 REAL prediction_error files in a non-live process ({refused})")
    P.LIVE = True
    check(all(P.guard_path(p) == p for p in _LIVE.values()), "...and hands them back untouched once live")
    P.LIVE = False

    # ── [2] the leak, reproduced and closed (simulated data/ root) ────────────────────────────────────────────────
    print("\n[2] non-live process, default data/ paths (simulated root)")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(st, sh, rw)
    _plant(st, sh, rw)
    s0, h0, r0, names0 = _snap(st), _snap(sh), _snap(rw), _tree(fake)
    CALLS.clear()
    for _ in range(2):
        ref.observe("mathematics", 0.81, 0.19)
    check(_snap(st) != s0 and _snap(sh) != h0 and _snap(rw) != r0,
          "CONTROL: the pre-fix observe() rewrites the state AND appends to the raw log AND the shadow_integrity log in a non-live process")
    check(len(CALLS) >= 1 and all(c[0] == "ok" for c in CALLS),
          f"CONTROL: ...and reaches the store_shadow_event DB insert ({len(CALLS)} call(s): a recurring large gap would_pressure)")
    _plant(st, sh, rw)
    s0, h0, r0 = _snap(st), _snap(sh), _snap(rw)
    CALLS.clear()
    rets = [pe.observe("mathematics", 0.81, 0.19) for _ in range(30)] + [pe.observe("mathematics", 0.80, 0.78),
                                                                         pe.observe("fieldcraft", 0.5, 0.0, event="x")]
    check(all(r is None for r in rets), "fenced: 32 observe() calls (large gaps, a small gap, an event) return None and raise nothing")
    check(_snap(st) == s0, "fenced: prediction_error_state.json byte-identical (size + sha256) after the refused calls")
    check(_snap(rw) == r0, "fenced: prediction_error_log.jsonl byte-identical (size + sha256) after the refused calls")
    check(_snap(sh) == h0, "fenced: logs/shadow_integrity.jsonl byte-identical (size + sha256) after the refused calls")
    check(_tree(fake) == names0, f"fenced: no new file appeared next to them ({_tree(fake)})")
    check(not CALLS, "fenced: the would_pressure path never reached store_shadow_event (no DB insert from a refused call)")
    for fn, args in ((pe._save_state, ({"x": [1.0]},)), (pe._bump, ("mathematics", 1.0))):
        try:
            fn(*args)
            ok = False
        except P.NonLiveWriteError:
            ok = True
        check(ok and _snap(st) == s0, f"fenced: the private writer {fn.__name__}() is refused too and leaves the state file byte-identical")

    # ── [3] the REAL paths, writes trapped ──────────────────────────────────────────────────────────────────────────
    print("\n[3] REAL C:\\Nascence\\data paths with every write trapped (recorded, never executed)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], False
    PROTECTED = {str(p).lower() for p in _LIVE.values()}
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

    _aim(_LIVE["state"], _LIVE["shadow"], _LIVE["raw"])
    Path.write_text = _trap_write_text
    pe.open = ref.open = _trap_open
    CALLS.clear()
    try:
        ref.observe("fieldcraft", 0.5, 0.0, event="control")
        ref_hits = list(HITS)
        HITS.clear()
        fenced_rets = [pe.observe("fieldcraft", 0.5, 0.0, event="fenced") for _ in range(30)]
        fenced_hits = list(HITS)
    finally:
        if _had:
            Path.write_text = _orig_wt
        else:
            del Path.write_text
        del pe.open
        del ref.open
    _names_hit = {Path(h[1]).name for h in ref_hits}
    check({"prediction_error_state.json", "prediction_error_log.jsonl", "shadow_integrity.jsonl"} <= _names_hit,
          f"CONTROL: the pre-fix observe() reaches ALL THREE real writes ({sorted(_names_hit)}; {len(ref_hits)} attempts)")
    check(all(r is None for r in fenced_rets) and not fenced_hits,
          f"fenced: 30 calls reach none of them ({len(fenced_hits)} attempts{'; first: ' + str(fenced_hits[:3]) if fenced_hits else ''})")

    # ── [4] live behaviour identical ──────────────────────────────────────────────────────────────────────────────────
    print("\n[4] live process (profile.LIVE = True): fenced == pre-fix, byte for byte")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = True
    pe.time = ref.time = _fake_time
    SEQ = [("mathematics", 0.80, 0.78, ""),                      # small gap: raw row only
           ("mathematics", 0.81, 0.19, ""),                      # large, recurrence 1: state + L1 signal row, no feed
           ("mathematics", 0.80, 0.20, "On mathematics: I felt 0.80 \u2014 \u00fcn\u00efcode \u2713 \u2013 but measured 0.20"),   # recurrence 2: feed + fed row
           ("comprehension", 0.9, 0.3, ""),                      # importance 0.45
           ("fieldcraft", 0.5, 0.0, ""),                         # unknown domain: default importance 0.35
           ("fieldcraft", 0.5, 0.0, ""),
           ("fieldcraft", 0.5, 1.0, "gap 0.5 up"),
           ("mathematics", "not-a-number", 0.5, ""),             # bad input: None, nothing written
           ("mathematics", 0.40, 0.0, ""),                       # gap exactly 0.40
           ("mathematics", 0.60, 0.20, "")]                      # gap 0.39999999999999997: a small gap by float luck
    DT = [0.0, 1.0, 37.5, 3600.0, 90000.0]

    def scenario(mod, tag):
        sp, shp, rp = fake / f"{tag}_state.json", fake / "logs" / f"{tag}_shadow.jsonl", fake / f"{tag}_raw.jsonl"
        for p in (sp, shp, rp):
            p.unlink(missing_ok=True)
        _aim(sp, shp, rp)
        CALLS.clear()
        out = []
        T[0] = 1_800_000_000.0
        for i, (dom, pr, me, ev) in enumerate(SEQ):                       # A: the mixed sequence
            T[0] += DT[i % len(DT)]
            out.append(mod.observe(dom, pr, me, event=ev))
        T[0] += 15 * 86400                                                # B: the 14-day recurrence window
        out.append(mod.observe("mathematics", 0.81, 0.19))
        T[0] += 1.0
        out.append(mod.observe("mathematics", 0.80, 0.20))
        mid = json.loads(sp.read_text(encoding="utf-8"))
        for _ in range(55):                                               # C: the 50-entry cap
            T[0] += 1.0
            out.append(mod.observe("cap_domain", 0.9, 0.1))
        store.store_shadow_event = _stub_raising                          # D: a failing DB insert stays swallowed
        try:
            for _ in range(2):
                T[0] += 1.0
                out.append(mod.observe("mathematics", 0.8, 0.2))
        finally:
            store.store_shadow_event = _stub_shadow
        return {"rets": out, "calls": list(CALLS), "state": _bytes(sp), "shadow": _bytes(shp), "raw": _bytes(rp), "mid": mid}

    new, old = scenario(pe, "live_new"), scenario(ref, "live_old")
    check(new["state"] == old["state"] and len(new["state"]) > 100, f"state file bytes identical to the pre-fix module ({len(new['state'])} B)")
    check(new["raw"] == old["raw"] and new["raw"].count(b"\n") == len(SEQ) - 1 + 2 + 55 + 2,
          f"raw log bytes identical, one row per numeric call and none for the bad input ({new['raw'].count(chr(10).encode())} rows)")
    check(new["shadow"] == old["shadow"] and b'"fed": true' in new["shadow"] and b'"fed": false' in new["shadow"],
          f"shadow_integrity bytes identical, with both signal and fed rows ({new['shadow'].count(chr(10).encode())} rows)")
    check(new["rets"] == old["rets"] and any(isinstance(r, dict) and r["would_pressure"] for r in new["rets"]),
          "every return value identical (verdict dicts / None), incl. a would_pressure verdict")
    check(new["calls"] == old["calls"] and any(c[0] == "raising" for c in new["calls"]) and any(c[0] == "ok" for c in new["calls"]),
          f"the store_shadow_event calls are identical ({len(new['calls'])} incl. the failing ones)")
    check(new["shadow"].count(b'"fed": true') == sum(1 for c in new["calls"] if c[0] == "ok"),
          "a failing DB insert wrote no fed row (the inner fail-open try is unchanged)")
    check(len(json.loads(new["state"])["cap_domain"]) == 50, "the 50-entry cap was exercised and identical")
    check(len(new["mid"]["mathematics"]) == 2 and new["mid"] == old["mid"], "the 14-day recurrence window was exercised and identical (old hits dropped)")
    check(b"\\u" not in new["shadow"] and "\u00fcn\u00efcode".encode("utf-8") in new["shadow"], "ensure_ascii=False event text survives byte-identically")
    blocker = fake / "blocker_file"
    blocker.write_text("x")
    io1 = {}
    for tag, mod in (("fenced", pe), ("pre-fix", ref)):
        _aim(blocker / "s.json", fake / "logs" / f"io1_{tag}_shadow.jsonl", fake / f"io1_{tag}_raw.jsonl")
        T[0] = 1_800_000_000.0
        r = mod.observe("mathematics", 0.81, 0.19)
        io1[tag] = (r, _bytes(fake / "logs" / f"io1_{tag}_shadow.jsonl"), _bytes(fake / f"io1_{tag}_raw.jsonl"))
        check(isinstance(r, dict) and io1[tag][1] and io1[tag][2],
              f"{tag}: state parent is a FILE -> _save_state's real I/O error swallowed, verdict still returned, both logs written (fail-open unchanged)")
    check(io1["fenced"] == io1["pre-fix"], "...and those results are identical")
    for tag, mod in (("fenced", pe), ("pre-fix", ref)):
        d = fake / f"rawdir_{tag}"
        d.mkdir()
        _aim(fake / f"io2_{tag}_state.json", fake / "logs" / f"io2_{tag}_shadow.jsonl", d)
        r = mod.observe("mathematics", 0.81, 0.19)
        check(r is None and not (fake / f"io2_{tag}_state.json").exists(), f"{tag}: raw log path is a DIRECTORY -> swallowed (None), nothing else written")
    pe.time = ref.time = _orig["time"]

    # ── [5] legitimate redirects still write ──────────────────────────────────────────────────────────────────────────
    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    lab = fake / "_lab" / "20261004_000000"
    (lab / "logs").mkdir(parents=True)
    _aim(lab / "prediction_error_state.json", lab / "logs" / "shadow_integrity.jsonl", lab / "prediction_error_log.jsonl")
    pe.observe("mathematics", 0.9, 0.1)
    check(all(p.exists() for p in (pe._STATE, pe._SHADOW, pe._RAW)), "data/_lab/<stamp>/ (lab_env.isolate()'s sandbox) writes all three files")
    _aim(fake / "_lab" / "prediction_error_state.json", fake / "_lab" / "shadow_integrity.jsonl", fake / "_lab" / "prediction_error_log.jsonl")
    pe.observe("mathematics", 0.9, 0.1)
    check(not any(p.exists() for p in (pe._STATE, pe._SHADOW, pe._RAW)), "data/_lab/<file> with no sandbox directory stays refused")
    _aim(TMP / "outside_state.json", TMP / "outside_shadow.jsonl", TMP / "outside_raw.jsonl")
    pe.observe("mathematics", 0.9, 0.1)
    check(all(p.exists() for p in (pe._STATE, pe._SHADOW, pe._RAW)), "a path outside data/ (the *_invitro.py / boredom_redirect style temp redirect) writes all three files")
    _aim(st, sh, TMP / "partial_raw.jsonl")        # only the raw log redirected; state and shadow_integrity still on data/
    _plant(st, sh, TMP / "partial_raw.jsonl")
    s0, h0, r0 = _snap(st), _snap(sh), _snap(TMP / "partial_raw.jsonl")
    check(pe.observe("mathematics", 0.9, 0.1) is None and (_snap(st), _snap(sh), _snap(TMP / "partial_raw.jsonl")) == (s0, h0, r0),
          "a PARTIAL redirect (raw log outside data/, state + shadow still on data/) is refused wholesale: no half-write, not even to the redirected file")

    # ── [6] the swallowed refusal is not silent ───────────────────────────────────────────────────────────────────────
    print("\n[6] visibility")

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.rows = []

        def emit(self, record):
            self.rows.append((record.name, record.levelno, record.getMessage()))

    cap = _Cap()
    _lg = {n: logging.getLogger(n) for n in ("nascence.profile", "nascence.prediction_error")}
    _lv = {n: l.level for n, l in _lg.items()}
    for l in _lg.values():
        l.addHandler(cap)
        l.setLevel(logging.DEBUG)
    try:
        _aim(st, sh, rw)
        _plant(st, sh, rw)
        P._warned.discard(str(rw))
        pe.observe("mathematics", 0.9, 0.1)
        pe.observe("mathematics", 0.9, 0.1)
        warn = [r for r in cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING and "prediction_error_log.jsonl" in r[2]]
        dbg = [r for r in cap.rows if r[0] == "nascence.prediction_error" and "refused" in r[2] and "prediction_error_log.jsonl" in r[2]]
        check(len(warn) == 1, f"guard_path logs ONE warning per path naming prediction_error_log.jsonl ({len(warn)})")
        check(len(dbg) == 2, f"observe() logs a debug line carrying the refusal text on every swallowed call ({len(dbg)})")
        cap.rows.clear()
        s0 = _snap(st)
        P._warned.discard(str(rw))
        check(pe.observe("mathematics", "not-a-number", 0.5) is None and not cap.rows and _snap(st) == s0,
              "bad input returns None before the guard: nothing logged, nothing touched")

        # ── [7] reads ─────────────────────────────────────────────────────────────────────────────────────────────────
        print("\n[7] status()")
        import time as _real_time
        _now = _real_time.time()
        st.write_text(json.dumps({"fieldcraft": [_now - 100, _now - 200, _now - 99 * 86400], "mathematics": [_now - 5]}, indent=1), encoding="utf-8")
        sh.write_text(json.dumps({"layer": "L1", "source": "prediction_error", "verdict": {"would_pressure": True}, "fed": False}) + "\n"
                      + json.dumps({"layer": "L1", "source": "prediction_error", "fed": True, "domain": "mathematics"}) + "\n"
                      + json.dumps({"layer": "L2", "source": "meta_awareness", "verdict": {"would_pressure": True}}) + "\n", encoding="utf-8")
        s0, h0 = _snap(st), _snap(sh)
        s = pe.status()
        check(s == {"recurrence_by_domain": {"fieldcraft": 2, "mathematics": 1}, "would_pressure_total": 1, "fed_total": 1, "feeding": True},
              f"status() still returns the same summary from a non-live process ({s})")
        check(_snap(st) == s0 and _snap(sh) == h0, "...and stays a pure read under a non-live process (files byte-identical)")
    finally:
        for n, l in _lg.items():
            l.removeHandler(cap)
            l.setLevel(_lv[n])

    # ── [8] the incident's own call path ──────────────────────────────────────────────────────────────────────────────
    print("\n[8] call site: core.competence.record_drill_accuracy('fieldcraft', ...) with ONLY competence's beliefs file redirected")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(st, sh, rw)
    _plant(st, sh, rw)
    s0, h0, r0 = _snap(st), _snap(sh), _snap(rw)
    CALLS.clear()
    comp._BELIEFS_FILE = TMP / "beliefs_control.json"
    pe.observe = ref.observe
    try:
        for _ in range(4):
            comp.record_drill_accuracy("fieldcraft", 0.0)
    finally:
        pe.observe = _orig["observe"]
    check(_snap(st) != s0 and _snap(sh) != h0 and _snap(rw) != r0 and CALLS,
          "CONTROL: 4 drills with the pre-fix observe() leak into all three files and reach the DB insert (the F-2416 shape)")
    _plant(st, sh, rw)
    s0, h0, r0 = _snap(st), _snap(sh), _snap(rw)
    CALLS.clear()
    comp._BELIEFS_FILE = TMP / "beliefs_fenced.json"
    beliefs = [comp.record_drill_accuracy("fieldcraft", 0.0) for _ in range(4)]
    check(all(isinstance(b, dict) and b["accuracy_count"] == i + 1 for i, b in enumerate(beliefs)),
          "fenced: all 4 drills still return their belief dicts -- the swallowed refusal never reaches competence's flow")
    check((_snap(st), _snap(sh), _snap(rw)) == (s0, h0, r0) and not CALLS,
          "fenced: all three files byte-identical after the 4 drills, and no DB insert was attempted")
finally:
    pe._STATE, pe._SHADOW, pe._RAW = _orig["STATE"], _orig["SHADOW"], _orig["RAW"]
    pe.observe, pe.time = _orig["observe"], _orig["time"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    store.store_shadow_event = _orig["store_fn"]
    comp._BELIEFS_FILE = _orig["beliefs"]
    for _m in (pe, ref):
        if "open" in vars(_m):
            del _m.open

# ── [9] canary ──────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[9] canary")
_after = {p: _snap(p) for p in _WATCH}
check(_after == _before,
      "the live files and this tree's default paths are byte-identical to the start of the run "
      f"(live raw log {_after[_LIVE['raw']][0] if _after[_LIVE['raw']] else None} B, live state {_after[_LIVE['state']][0] if _after[_LIVE['state']] else None} B, "
      f"live shadow_integrity {_after[_LIVE['shadow']][0] if _after[_LIVE['shadow']] else None} B)")
check(pe._STATE == ROOT / "data" / "prediction_error_state.json" and store.store_shadow_event is _orig["store_fn"],
      "the module's own paths and the DB-insert function were restored")
shutil.rmtree(TMP, ignore_errors=True)
print("\n" + ("ALL OK" if not FAILS else f"{FAILS} FAILED"))
sys.exit(1 if FAILS else 0)
