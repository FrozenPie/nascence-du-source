"""
J-3260 / D-0651 -- put the shore's stream mouth on the map. Founder ruling (2026-11-02, plan shore_upgrade): the stream mouth is a braid
reaching the waterline around x 14 to 16 on the 30 x 20 m frame (origin SW, +x east, +y north out to sea), east of driftwood_tangle (6,4) and
the shell drift, west of rock_pools (20,9).

data/ is git-ignored, so the geometry change cannot travel in a commit: this script is how it gets made. ADDITIVE ONLY: it adds one
feature, `stream_mouth`, to data/world_geometry/shore.json and touches nothing else (no anchor, no standpoint, no sightline), so
spatial.render's clauses -- which name features one by one (waterline, rock_pools, the `anchors` list) -- are unchanged.
core/life_shore.py ZONES['stream_mouth'] (a disc, r 2.0, anchored on this feature) needs it, so run this BEFORE the restart that carries
that line.

  python scripts/apply_shore_stream_mouth_j3260.py            # dry run: says what it would do
  python scripts/apply_shore_stream_mouth_j3260.py --write    # backs shore.json up beside itself, then adds the feature (idempotent)
  python scripts/apply_shore_stream_mouth_j3260.py --geo PATH # another shore.json (tests)

Pos (15.0, 7.0, 0.0): x in the ruled 14-16 band; y just landward of the highest the tide reaches (waterline tide_y 8.5..14.5), where the
braid crosses the shingle to meet the moving edge. (core/life_traces.py already files the shore's stream_mouth tracks at (14, 6).)
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEO = ROOT / "data" / "world_geometry" / "shore.json"

FEATURE = {
    "pos": [15.0, 7.0, 0.0],
    "note": "where a braid of the stream crosses the shingle to meet the sea - fresh water running out over the stones, the tide taking "
            "or leaving it as the waterline moves (D-0651, 2026-11-02)",
}


def apply(geo: Path, write: bool) -> str:
    with open(geo, encoding="utf-8", newline="") as fh:                # newline="": keep the file's own CRLF visible
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    d = json.loads(raw)
    feats = d.get("features")
    if not isinstance(feats, dict) or "waterline" not in feats:
        raise SystemExit(f"{geo}: no features/waterline -- not the shore geometry, refusing")
    if "stream_mouth" in feats:
        return f"already present ({feats['stream_mouth'].get('pos')}): nothing to do"
    feats["stream_mouth"] = FEATURE
    # the file is json.dumps(indent=2, ensure_ascii=False) with this newline and (here) no trailing newline: keep that exactly
    out = json.dumps(d, indent=2, ensure_ascii=False).replace("\n", nl)
    if raw.endswith(nl):
        out += nl
    if not write:
        return f"dry run: would add features.stream_mouth at {FEATURE['pos']} to {geo}"
    bak = geo.with_name(f"{geo.name}.bak_J-3260_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(geo, bak)
    tmp = geo.with_name(geo.name + ".J-3260.tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    json.loads(tmp.read_text(encoding="utf-8"))                      # the new file must parse before it replaces the old
    tmp.replace(geo)
    return f"added features.stream_mouth at {FEATURE['pos']}; backup {bak.name}"


if __name__ == "__main__":
    args = sys.argv[1:]
    geo = Path(args[args.index("--geo") + 1]) if "--geo" in args else DEFAULT_GEO
    print(apply(geo, "--write" in args))
