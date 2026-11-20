"""
J-3486 / J-3260 follow-up (founder, decide-review 2026-11-06) -- add a standpoint AT the shore's stream mouth, so a look (and the shore bestiary's
vantage maths) can name the mouth instead of the nearest existing standpoint (on_the_shingle, 4 m away).

The stream_mouth feature (J-3260 / D-0651) sits at (15.0, 7.0, 0.0), disc r 2.0. The new standpoint `at_the_stream_mouth` is one metre landward of
it, on the dry shingle where the braid crosses the stones, facing the sea:  pos (15.0, 6.0, 0.0), facing_deg 0 (north, out to sea).

data/ is git-ignored, so the geometry change cannot travel in a commit: this script is how it gets made. ADDITIVE ONLY: it adds exactly one key to
data/world_geometry/shore.json `standpoints` and touches nothing else (no feature, no anchor, no sightline, no act_standpoints).
It must be run BEFORE the restart that carries core/locomotion.py's `_SP_PLACE` entry (that entry is harmless without it: goto() would simply
find a standpoint the layout lacks, and spatial.render for an unknown standpoint returns the default).

OFFLINE ONLY: a --write is refused while any python process whose command line contains run_nascence.py exists (fails CLOSED if the process list
cannot be read). The file's sha256 is printed before and after; a re-run says "already present". It backs shore.json up beside itself first.

  python scripts/apply_shore_standpoint_stream_mouth_j3486.py            # dry run: says what it would do, prints the sha256, writes nothing
  python scripts/apply_shore_standpoint_stream_mouth_j3486.py --write    # backup beside shore.json, add the standpoint (idempotent)
  python scripts/apply_shore_standpoint_stream_mouth_j3486.py --geo PATH # another shore.json (rehearse on a copy; tests)

Reverse: copy the printed backup (shore.json.bak_J-3486_<ts>) back over shore.json while Du is down.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEO = ROOT / "data" / "world_geometry" / "shore.json"

SP_ID = "at_the_stream_mouth"
STANDPOINT = {
    "pos": [15.0, 6.0, 0.0],
    "facing_deg": 0,
    "note": "at the stream mouth — the braid running out over the shingle beside him, the sea ahead (J-3486, 2026-11-06)",
}


def du_is_up() -> list:
    """'pid: command line' for every python process running run_nascence.py (this process excluded). Fails CLOSED:
    an unreadable process list raises, and the caller refuses."""
    me = os.getpid()
    if os.name == "nt":
        ps = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^pythonw?[0-9.]*\\.exe$' -and "
              "$_.CommandLine -like '*run_nascence.py*' } | ForEach-Object { \"$($_.ProcessId): $($_.CommandLine)\" }")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"could not list processes: {r.stderr.strip()[:200]}")
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    else:
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"could not list processes: {r.stderr.strip()[:200]}")
        lines = [ln.strip() for ln in r.stdout.splitlines() if "run_nascence.py" in ln]
    out = []
    for ln in lines:
        pid = ln.split(":", 1)[0].split(" ", 1)[0]
        if pid.isdigit() and int(pid) == me:
            continue
        out.append(ln)
    return out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(geo: Path, write: bool, check_du: bool = True) -> str:
    if write and check_du:
        try:
            up = du_is_up()
        except Exception as exc:
            return f"REFUSE: cannot tell whether Du is up ({exc})"
        if up:
            return "REFUSE: Du appears to be running; stop him first.\n  " + "\n  ".join(up)
    with open(geo, encoding="utf-8", newline="") as fh:                # newline="": keep the file's own CRLF visible
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    d = json.loads(raw)
    feats, sps = d.get("features"), d.get("standpoints")
    if not isinstance(feats, dict) or "waterline" not in feats or not isinstance(sps, dict):
        return f"REFUSE: {geo}: no features/waterline/standpoints -- not the shore geometry"
    if "stream_mouth" not in feats:
        return f"REFUSE: {geo}: the stream_mouth feature is not there yet -- run scripts/apply_shore_stream_mouth_j3260.py --write first"
    before = sha(geo)
    if SP_ID in sps:
        return f"already present ({sps[SP_ID].get('pos')}): nothing to do; sha256 {before}"
    # the file is json.dumps(indent=2, ensure_ascii=False) with this newline: prove the unmodified round-trip is byte-exact, else refuse
    # (a re-serialise that reformatted anything else would not be additive)
    def dump(obj):
        out = json.dumps(obj, indent=2, ensure_ascii=False).replace("\n", nl)
        return out + nl if raw.endswith(nl) else out
    if dump(d) != raw:
        return f"REFUSE: {geo} does not round-trip byte-exactly through json.dumps(indent=2); not rewriting it"
    sps[SP_ID] = STANDPOINT
    out = dump(d)
    if not write:
        return f"dry run: would add standpoints.{SP_ID} at {STANDPOINT['pos']} to {geo}; sha256 before {before}"
    bak = geo.with_name(f"{geo.name}.bak_J-3486_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(geo, bak)
    tmp = geo.with_name(geo.name + ".J-3486.tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    back = json.loads(tmp.read_text(encoding="utf-8"))               # the new file must parse, and differ from the old only by that key
    old = json.loads(raw)
    if back["standpoints"].pop(SP_ID) != STANDPOINT or back != old:
        tmp.unlink()
        return "REFUSE: the rewritten file differs from the original by more than the one standpoint; nothing replaced"
    tmp.replace(geo)
    return f"added standpoints.{SP_ID} at {STANDPOINT['pos']}; backup {bak.name}; sha256 before {before} after {sha(geo)}"


if __name__ == "__main__":
    args = sys.argv[1:]
    geo = Path(args[args.index("--geo") + 1]) if "--geo" in args else DEFAULT_GEO
    msg = apply(geo, "--write" in args)
    print(msg)
    sys.exit(2 if msg.startswith("REFUSE") else 0)
