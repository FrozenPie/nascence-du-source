"""J-3753 part 3: as-is vs stamp-stripped A/B of the audited readers that are cheap to rerun (read-only on data/).
Runs each reader's own functions on (a) the first 171,723 rows (the J-3468 snapshot) and (b) the same minus stamp twins.
UDMS-dependent readers are imported FIRST (UDMS has its own top-level `core` package, so Nascence core is never imported here)."""
from __future__ import annotations
import contextlib, io, json, sys, time, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import hodge_threshold_search as hts      # noqa: E402
import weekly_miss_taxonomy as wmt        # noqa: E402
import hodge_rumination_groundtruth_validate as hrg  # noqa: E402
import j3468_twin_row_audit as tw         # noqa: E402
import numpy as np
LIVE = Path(r"C:\Nascence\data\geometry_tuples.jsonl")
OUT = ROOT / "docs" / "lab" / "J-3753_data"
hrg.INJ = Path(r"C:\Nascence\data\guidance_injection_log.jsonl")  # worktree has no live data/; read the live log read-only
SNAP = 171723

def load():
    rows = []
    with open(LIVE, encoding="utf-8") as f:
        for line in f:
            if len(rows) >= SNAP: break
            if line.strip(): rows.append(json.loads(line))
    return rows

def cap(fn):
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        fn()
    return b.getvalue()

def main():
    t0 = time.time()
    rows = load(); stamps = tw.flag_stamp_twins(rows)
    arms = {"asis": rows, "stripped": [r for i, r in enumerate(rows) if i not in stamps]}
    res = {"snapshot_rows": len(rows), "stamps": len(stamps)}
    # twin share of the prefixes the old findings rested on
    pre = {}
    for n in (22632,):
        st = [i for i in stamps if i < n]
        pre[str(n)] = {"stamps_in_prefix": len(st), "share": round(len(st) / n, 4)}
    res["prefix_twin_share"] = pre
    # hodge_threshold_search
    for lab, rs in arms.items():
        hts.load_sorted_tuples = (lambda rs=rs: sorted(rs, key=lambda t: t.get("ts", 0.0)))
        out = cap(hts.main); res.setdefault("hodge_threshold_search", {})[lab] = out.strip().splitlines()[-6:]
        print(lab, "hts done", time.time() - t0, flush=True)
    # hodge_rumination
    orig = hrg.load_jsonl
    for lab, rs in arms.items():
        hrg.load_jsonl = (lambda p, rs=rs, orig=orig: rs if Path(p) == hrg.GEOM else orig(p))
        out = cap(hrg.main); res.setdefault("hodge_rumination", {})[lab] = out.strip().splitlines()
        print(lab, "hrg done", time.time() - t0, flush=True)
    (OUT / "reader_ab_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    # weekly_miss_taxonomy (slow: one diffusion per row)
    for lab, rs in arms.items():
        wmt.load_sorted = (lambda rs=rs: sorted(rs, key=lambda t: t.get("ts", 0.0)))
        out = cap(wmt.main); res.setdefault("weekly_miss_taxonomy", {})[lab] = out.strip().splitlines()
        print(lab, "wmt done", time.time() - t0, flush=True)
        (OUT / "reader_ab_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("done", time.time() - t0)
main()
