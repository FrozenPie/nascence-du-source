"""closure_producer Phase 2: calibrate the closure gate (core/closure_gate.py) before it may block anything.

Samples N question + finding pairs from a COPY of the frontier file, asks the gate's judge about each (the real
decoupled panel, core.judge_panel), and writes the pairs and verdicts for hand grading.

  python scripts/closure_gate_calibrate.py --frontier <copy of frontier.json> --out <dir> [--n 60]
         [--line-log <copy of follow_line_shadow.jsonl>] [--seed 7] [--dry] [--grades <grades.json>]

Three strata, n/3 each (shortfalls filled from the others):
  line_yes   questions he settled `yes` on (resolved_how == line); the finding is the return he was shown, read
             from the Follow Line log's would_return row (the frontier row itself rarely keeps it)
  memory     entries whose attached finding is an expired Follow Line return ("what you found in your own memory")
  research   entries whose attached finding came from curiosity research (a titled extract; the nearest thing to
             a lookup finding that exists before any lookup has run)

Outputs in --out: pairs.jsonl (id, stratum, q, title, finding), verdicts.jsonl (id, verdict, how, why, v1, v2,
secs), grading_sheet.md (pairs WITHOUT verdicts, for blind grading), summary.json (verdict distribution, pegged).
With --grades (a JSON object {pair id: "yes"|"no"|"partly"}) it also reports agreement and the confusion table
and the recommendation: enforce only if agreement >= 75% and no single verdict holds >= 90%.

It refuses a --frontier under a live data/ directory, never writes outside --out, starts no server, and sends the
judge logs of this run to --out (never the checkout's data/).
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MEMORY_TITLE = "what you found in your own memory"
VERDICTS = ("yes", "no", "partly", "unavailable")


def _is_live_data(p: Path) -> bool:
    parts = [x.lower() for x in p.resolve().parts]
    return "data" in parts and "nascence" in parts and "_lab" not in parts and "temp" not in parts


def _line_returns(path: Path | None, want: set) -> dict:
    out: dict = {}
    if not path or not path.exists():
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"would_return"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == "would_return" and r.get("q_id") in want and r.get("return_text"):
                out[r["q_id"]] = r["return_text"]          # the latest return for that id wins
    return out


def sample(frontier: Path, line_log: Path | None, n: int, seed: int) -> list[dict]:
    qs = json.loads(frontier.read_text(encoding="utf-8")).get("questions", [])
    rng = random.Random(seed)
    line_yes = [q for q in qs if q.get("resolved_how") == "line" and q.get("q")]
    rets = _line_returns(line_log, {q["id"] for q in line_yes})
    strata = {
        "line_yes": [dict(id=q["id"], q=q["q"], title=MEMORY_TITLE, finding=rets[q["id"]]) for q in line_yes if q["id"] in rets],
        "memory": [dict(id=q["id"], q=q["q"], title=q.get("finding_title") or "", finding=q["finding"])
                   for q in qs if q.get("finding") and q.get("q") and q.get("finding_title") == MEMORY_TITLE
                   and q.get("resolved_how") != "line"],
        "research": [dict(id=q["id"], q=q["q"], title=q.get("finding_title") or "", finding=q["finding"])
                     for q in qs if q.get("finding") and q.get("q") and q.get("finding_title") != MEMORY_TITLE],
    }
    for rows in strata.values():
        rows.sort(key=lambda r: r["id"])
        rng.shuffle(rows)
    per = n // 3
    picked, left = [], []
    for name, rows in strata.items():
        for r in rows[:per]:
            picked.append(dict(r, stratum=name))
        left += [dict(r, stratum=name) for r in rows[per:]]
    rng.shuffle(left)
    seen = {p["id"] for p in picked}
    for r in left:
        if len(picked) >= n:
            break
        if r["id"] not in seen:
            picked.append(r)
            seen.add(r["id"])
    print(f"strata available: " + ", ".join(f"{k} {len(v)}" for k, v in strata.items()) + f"; sampled {len(picked)}")
    return picked


async def run_judge(pairs: list[dict], out: Path) -> list[dict]:
    from core import closure_gate, judge_panel, telemetry
    judge_panel._LOG = out / "judge_panel_log.jsonl"
    judge_panel._INPUTS_LOG = out / "judge_inputs_log.jsonl"
    for name in ("_CALLS", "_LAT", "_JSONFAIL", "_STATIONS"):
        if hasattr(telemetry, name):
            setattr(telemetry, name, out / ("telemetry" + name.lower() + ".jsonl"))
    rows = []
    with open(out / "verdicts.jsonl", "a", encoding="utf-8") as f:
        for i, p in enumerate(pairs, 1):
            d = await closure_gate.judge(p["q"], p["finding"], p["title"], context=f"closure_gate:calibrate:{p['id'][:8]}")
            row = {"id": p["id"], "stratum": p["stratum"], "verdict": d["verdict"], "how": d["how"], "why": d["why"],
                   "v1": d["v1"], "v2": d["v2"], "secs": d["secs"]}
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i}/{len(pairs)}] {p['stratum']:<9} {d['verdict']:<11} {d['how']:<18} {d['secs']}s", flush=True)
    return rows


def summarise(rows: list[dict]) -> dict:
    dist = collections.Counter(r["verdict"] for r in rows)
    judged = [r for r in rows if r["verdict"] != "unavailable"]
    top = max((dist[v] for v in ("yes", "no", "partly")), default=0)
    return {"n": len(rows), "judged": len(judged), "distribution": dict(dist),
            "by_stratum": {s: dict(collections.Counter(r["verdict"] for r in rows if r["stratum"] == s))
                           for s in sorted({r["stratum"] for r in rows})},
            "pegged": bool(judged) and top / len(judged) >= 0.90,
            "top_share": round(top / len(judged), 3) if judged else None}


def compare(rows: list[dict], grades: dict) -> dict:
    conf: dict = collections.defaultdict(int)
    n = agree = 0
    for r in rows:
        g = grades.get(r["id"])
        if g not in ("yes", "no", "partly") or r["verdict"] == "unavailable":
            continue
        n += 1
        agree += int(g == r["verdict"])
        conf[f"hand_{g}/judge_{r['verdict']}"] += 1
    hy = sum(v for k, v in conf.items() if k.startswith("hand_yes/"))
    jy = sum(v for k, v in conf.items() if k.endswith("/judge_yes"))
    tp = conf.get("hand_yes/judge_yes", 0)
    return {"graded_and_judged": n, "agreement": round(agree / n, 3) if n else None, "confusion": dict(conf),
            "judge_yes_precision": round(tp / jy, 3) if jy else None,
            "judge_yes_recall": round(tp / hy, 3) if hy else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontier", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--line-log", default="")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--dry", action="store_true", help="sample and write the pairs only; ask no judge")
    ap.add_argument("--grades", default="", help="JSON {pair id: yes|no|partly}; compare with verdicts.jsonl in --out")
    a = ap.parse_args(argv)
    fr, out = Path(a.frontier), Path(a.out)
    if _is_live_data(fr) or _is_live_data(out):
        print("refused: --frontier and --out must not be under a live data/ directory; copy the file first")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    if a.grades:
        rows = [json.loads(x) for x in (out / "verdicts.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        s = summarise(rows)
        c = compare(rows, json.loads(Path(a.grades).read_text(encoding="utf-8")))
        ok = c["agreement"] is not None and c["agreement"] >= 0.75 and not s["pegged"]
        res = {"summary": s, "against_hand_grades": c, "recommend": "enforce" if ok else "shadow"}
        (out / "calibration.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(json.dumps(res, indent=1))
        return 0
    pairs = sample(fr, Path(a.line_log) if a.line_log else None, a.n, a.seed)
    with open(out / "pairs.jsonl", "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(out / "grading_sheet.md", "w", encoding="utf-8") as f:
        for i, p in enumerate(pairs, 1):
            f.write(f"## {i}. {p['id']} ({p['stratum']})\n\nQUESTION: {p['q']}\n\nMATERIAL ({p['title']}):\n{p['finding']}\n\n")
    if a.dry:
        print(f"dry run: {len(pairs)} pairs written to {out}")
        return 0
    t0 = time.time()
    if (out / "verdicts.jsonl").exists():
        (out / "verdicts.jsonl").unlink()
    rows = asyncio.run(run_judge(pairs, out))
    s = summarise(rows)
    s["secs"] = round(time.time() - t0)
    (out / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    print(json.dumps(s, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
