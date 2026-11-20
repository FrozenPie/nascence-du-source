"""J-3410: read-only per-key, per-judge verdict skew from data/judge_panel_log.jsonl (F-4044 sweep).

For every panel key: n rulings, each judge's true-rate (v1 mixtral :11438, v2 falcon3 :11440, v3 tiebreak),
how often v1 and v2 agree, and the ordering signature of the prompt that key ships. Reads the live log
read-only (opened 'r'), writes only to --out (default docs/lab/J-3410_data/judge_skew.json).
Usage: python scripts/lab_j3410_judge_skew.py [--log PATH] [--since TS] [--out PATH]
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = Path("C:/Nascence/data/judge_panel_log.jsonl")


def measure(rows):
    by = defaultdict(lambda: {"n": 0, "v1": [0, 0], "v2": [0, 0], "v3": defaultdict(lambda: [0, 0]),
                              "both": 0, "agree": 0, "agree_true": 0, "agree_false": 0,
                              "v1T_v2F": 0, "v1F_v2T": 0, "hubs": defaultdict(int), "verdict": [0, 0], "how": defaultdict(int)})
    for r in rows:
        k = r.get("key")
        if not k:
            continue
        ctx = str(r.get("context") or "")
        # split keys that two stations share ("resolved": dream vs pursuit-close; "genuine": self-interrogation vs
        # active imagination) by the context prefix the caller logs
        k = "%s@%s" % (k, ctx.split(":")[0] or "-")
        b = by[k]
        b["n"] += 1
        b["hubs"]["%s/%s/%s" % (r.get("hub1"), r.get("hub2"), r.get("hub3"))] += 1
        b["how"][str(r.get("how"))] += 1
        v1, v2, v3 = r.get("v1"), r.get("v2"), r.get("v3")
        if isinstance(v1, bool):
            b["v1"][0] += 1; b["v1"][1] += int(v1)
        if isinstance(v2, bool):
            b["v2"][0] += 1; b["v2"][1] += int(v2)
        if isinstance(v1, bool) and isinstance(v2, bool):
            b["both"] += 1
            if v1 == v2:
                b["agree"] += 1
                b["agree_true" if v1 else "agree_false"] += 1
            elif v1:
                b["v1T_v2F"] += 1
            else:
                b["v1F_v2T"] += 1
        vv = r.get("verdict")
        if isinstance(vv, bool):
            b["verdict"][0] += 1; b["verdict"][1] += int(vv)
    return by


def summarise(by):
    out = {}
    for k, b in sorted(by.items(), key=lambda kv: -kv[1]["n"]):
        def rate(p):
            return round(p[1] / p[0], 3) if p[0] else None
        out[k] = {"n": b["n"], "v1_n": b["v1"][0], "v1_true": rate(b["v1"]), "v2_n": b["v2"][0], "v2_true": rate(b["v2"]),
                  "both_n": b["both"], "agree_rate": round(b["agree"] / b["both"], 3) if b["both"] else None,
                  "split_v1T_v2F": b["v1T_v2F"], "split_v1F_v2T": b["v1F_v2T"],
                  "verdict_n": b["verdict"][0], "verdict_true": rate(b["verdict"]),
                  "hubs": dict(b["hubs"]), "how": dict(b["how"])}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--since", type=float, default=0.0)
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3410_data" / "judge_skew.json"))
    a = ap.parse_args(argv)
    rows = []
    with open(a.log, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ts", 0) >= a.since:
                rows.append(r)
    res = summarise(measure(rows))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"log": a.log, "since": a.since, "rows": len(rows), "keys": res}, indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("rows", len(rows))
    for k, v in res.items():
        print("%-14s n=%5d v1T=%s v2T=%s agree=%s splits(v1T/v2F=%d, v1F/v2T=%d) verdictT=%s" % (
            k, v["n"], v["v1_true"], v["v2_true"], v["agree_rate"], v["split_v1T_v2F"], v["split_v1F_v2T"], v["verdict_true"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
