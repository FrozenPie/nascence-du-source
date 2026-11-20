"""
Regression: core/training_log.py log_example sits behind the D-0179 write fence (J-1816 / F-2428).

The gap: log_example (called by core/node_base.py after EVERY successful Node LLM call) appended to data/training/<node>.jsonl
(the live teacher corpora) in ANY process that imported it from the shared tree, default ON. The build resolves the per-node
path through profile.guard_path BEFORE _ensure_dir()'s mkdir and the open, INSIDE the existing fail-open try (a refusal must
never break a cycle; it is swallowed, guard_path logs one warning). LIVE gets the same path back: byte-identical.

ISOLATED: writes go to a temp dir / simulated data root, or are TRAPPED (recorded, never executed) when aimed at the REAL
C:/Nascence/data; live files are hashed before/after. Safe against pre-fix modules (it must FAIL there).

  python scripts/_test_training_log_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE every other core import (F-2423)
_core_file = Path(core.__file__).resolve()
assert ROOT in _core_file.parents, f"core resolves to {_core_file}, not inside {ROOT} -- refusing to run"

TMP = Path(tempfile.mkdtemp(prefix="j1816_fence_"))
print("core package:", _core_file)
FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"


def _snap(p: Path):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_WATCH = {p for p in (_LIVE_DATA / "training").glob("*.jsonl")} | {
    _LIVE_DATA / "satisfaction_log.jsonl", _LIVE_DATA / "prediction_error_log.jsonl",
    _LIVE_DATA / "logs" / "shadow_integrity.jsonl", _LIVE_DATA / "buses_log.jsonl"}
_before = {p: _snap(p) for p in _WATCH}

from core import profile as P, training_log as TL  # noqa: E402

_orig = dict(DIR=TL._LOG_DIR, READY=TL._dir_ready, EN=TL._ENABLED, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE)


def restore():
    TL._LOG_DIR, TL._dir_ready, TL._ENABLED = _orig["DIR"], _orig["READY"], _orig["EN"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]


def listing(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")) if root.exists() else []


def aim_at(root: Path):
    TL._LOG_DIR = root / "training"
    TL._dir_ready = False
    TL._ENABLED = True
    P._DATA = P._CANONICAL_DATA = root


def call(node="executive", **kw):
    TL.log_example(node, "UP", {"a": "é"}, system_prompt="SP", cycle_id="c1", raw_input="RI", input_type="t", hedged=False, **kw)


try:
    print("[1] surface")
    check(getattr(TL, "profile", None) is P, "training_log holds core.profile")
    P.LIVE = False
    try:
        P.guard_path(_LIVE_DATA / "training" / "executive.jsonl")
        check(False, "guard_path refuses real training file")
    except P.NonLiveWriteError:
        check(True, "guard_path refuses real training file")

    print("[2] non-live refusal (simulated data root)")
    fake = TMP / "fake" / "data"
    fake.mkdir(parents=True)
    aim_at(fake)
    P.LIVE = False
    try:
        call()
        check(True, "non-live log_example swallows the refusal (never breaks a cycle)")
    except Exception as e:
        check(False, f"non-live log_example raised {e!r}")
    check(listing(fake) == [], "no training dir / file created (no mkdir, no append)")

    print("[3] real live data paths (writes trapped)")
    trapped = []
    _ro, _rm = builtins.open, Path.mkdir

    def _is_real(p) -> bool:
        try:
            Path(p).resolve().relative_to(_LIVE_DATA)
            return True
        except Exception:
            return False

    def t_open(f, mode="r", *a, **k):
        if _is_real(f) and any(c in str(mode) for c in "wax+"):
            trapped.append(("open", str(f)))
            raise OSError("trapped")
        return _ro(f, mode, *a, **k)

    def t_mkdir(self, *a, **k):
        if _is_real(self):
            trapped.append(("mkdir", str(self)))
            return None
        return _rm(self, *a, **k)

    builtins.open, Path.mkdir = t_open, t_mkdir
    try:
        TL._LOG_DIR = _LIVE_DATA / "training"
        TL._dir_ready = False
        TL._ENABLED = True
        P._DATA = P._CANONICAL_DATA = _LIVE_DATA
        P.LIVE = False
        for n in ("executive", "emotion", "brand_new_node_j1816"):
            call(n)
        check(trapped == [], f"non-live reached NO real mkdir/append (trapped={trapped})")
        P.LIVE = True
        TL._dir_ready = False
        call("executive")
        check(any(k == "open" for k, _ in trapped), "CONTROL: a live call IS seen by the trap (the test can fail)")
    finally:
        builtins.open, Path.mkdir = _ro, _rm

    print("[4] live parity")
    live = TMP / "live" / "data"
    live.mkdir(parents=True)
    aim_at(live)
    P.LIVE = True
    _t = time.time
    time.time = lambda: 1234.5
    try:
        call("executive")
        call("executive")
        call("emotion")
    finally:
        time.time = _t
    rec = {"ts": 1234.5, "cycle_id": "c1", "node": "executive", "input_type": "t", "raw_input": "RI", "user_prompt": "UP",
           "output": {"a": "é"}, "hedged": False, "system_prompt": "SP"}
    ref = TMP / "ref.jsonl"
    with _ro(ref, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    check((live / "training" / "executive.jsonl").read_bytes() == ref.read_bytes(), "executive.jsonl bytes identical to pre-fix expression")
    check((live / "training" / "emotion.jsonl").exists() and len(listing(live)) == 3, "live: dir + per-node files created as before")
    TL._ENABLED = False
    call("off_node")
    check(not (live / "training" / "off_node.jsonl").exists(), "env gate off still writes nothing")
    TL._ENABLED = True

    print("[5] legit redirect (outside data/) non-live")
    P._DATA = P._CANONICAL_DATA = _orig["DATA"]
    P.LIVE = False
    out = TMP / "elsewhere"
    TL._LOG_DIR = out / "training"
    TL._dir_ready = False
    call("executive")
    check((out / "training" / "executive.jsonl").exists(), "redirected non-live write still lands")
    lab = _orig["DATA"] / "_lab" / "j1816_stamp"
    P.guard_path(lab / "training" / "x.jsonl")
    check(True, "data/_lab/<stamp>/ sandbox still allowed")
    try:
        P.guard_path(_orig["DATA"] / "_lab" / "x.jsonl")
        check(False, "data/_lab/<file> still refused")
    except P.NonLiveWriteError:
        check(True, "data/_lab/<file> still refused")
finally:
    restore()

print("[6] canary")
_after = {p: _snap(p) for p in _WATCH}
check(_after == _before, "every watched live file byte-identical")

print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILURE(S)")
sys.exit(1 if FAILS else 0)
