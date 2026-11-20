"""J-3415: how often does each Du node actually use the null outcome its output schema allows?

READ-ONLY on the live data directory (opens every file for reading, never writes there).
Writes one JSON report under docs/lab/J-3415_data/ in this worktree.

Usage:  python scripts/lab_J-3415_null_rate_census.py [DATA_DIR] [OUT_JSON]
Default DATA_DIR C:/Nascence/data ; default OUT docs/lab/J-3415_data/null_rates.json (next to this tree).

Each row of the report: prompt id, what the null form is, n rows, null count, null rate, split by
input_type where the log has it, and the window (all rows, and rows since SINCE_TS = 2026-09-25, the
current regime after the 09-25 boot). A node whose schema admits a null but whose null rate is under
a few percent is a node where the closing ask, not the schema, decides the answer (the P-0043 shape).
"""
import json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs" / "lab" / "J-3415_data" / "null_rates.json"
SINCE_TS = time.mktime((2026, 9, 25, 0, 0, 0, 0, 0, -1))

def rows(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def _out(r):
    o = r.get("output")
    return o if isinstance(o, dict) else {}

# node name -> (prompt id, null-form description, predicate(output) -> True when the null was used, denominator guard)
NODES = {
    "episodic_buffer": ("P-0006", "dissonance == [] (no friction between streams)",
                        lambda o: isinstance(o.get("dissonance"), list) and len(o["dissonance"]) == 0,
                        lambda o: "dissonance" in o),
    "recall": ("P-0005", "tensions == [] (no evidenced contradiction)",
               lambda o: isinstance(o.get("tensions"), list) and len(o["tensions"]) == 0,
               lambda o: "tensions" in o),
    "consolidation": ("P-0012", "wisdom_extracted null/empty (nothing notable)",
                      lambda o: not (str(o.get("wisdom_extracted") or "").strip()) or str(o.get("wisdom_extracted")).strip().lower() in ("null", "none"),
                      lambda o: "wisdom_extracted" in o),
    "critic": ("P-0008", "approved true (no violation found); null-use = approve",
               lambda o: o.get("approved") is True,
               lambda o: "approved" in o),
    "curiosity": ("P-0011", "questions == [] (nothing to ask)",
                  lambda o: isinstance(o.get("questions"), list) and len(o["questions"]) == 0,
                  lambda o: "questions" in o),
    "executive": ("P-0009", "response_type silence/decline or should_respond false",
                  lambda o: o.get("should_respond") is False or o.get("response_type") in ("silence",),
                  lambda o: "response_type" in o or "should_respond" in o),
}

report = {"data_dir": str(DATA), "since_ts": SINCE_TS, "nodes": {}, "other": {}}
for node, (pid, desc, is_null, ok) in NODES.items():
    p = DATA / "training" / f"{node}.jsonl"
    if not p.exists():
        report["nodes"][node] = {"prompt": pid, "error": "missing"}
        continue
    tot = Counter(); nul = Counter()
    for r in rows(p):
        o = _out(r)
        if not o or not ok(o):
            continue
        ts = r.get("ts") or 0
        it = r.get("input_type") or "?"
        for win in ("all", "since_0925") if ts >= SINCE_TS else ("all",):
            tot[(win, "any")] += 1; tot[(win, it)] += 1
            if is_null(o):
                nul[(win, "any")] += 1; nul[(win, it)] += 1
    entry = {"prompt": pid, "null_form": desc, "windows": {}}
    for (win, it), n in sorted(tot.items()):
        entry["windows"].setdefault(win, {})[it] = {"n": n, "null": nul[(win, it)], "rate": round(nul[(win, it)] / n, 4)}
    report["nodes"][node] = entry

# self-interrogation (P-0042 generator, P-0105 judge): genuine rate and a lexical confirm-vs-doubt marker rate
conf = re.compile(r"\b(it holds|holds up|holds true|holds exactly|stands|survives|I (do )?trust (it|this)|I can trust|is sound|remains true|still true|keep it as it is|no need to revise|unchanged)\b", re.I)
doubt = re.compile(r"\b(clinging|excuse|convenient|comfortable|flatter|avoid|must ask|ask (myself|if)|am I|bias|too (neat|easy|tidy)|performing|might be|perhaps|suspicious|I wonder whether|or am I|safer|defensive|retreat)\b", re.I)
p = DATA / "self_interrogation_shadow.jsonl"
if p.exists():
    c = Counter()
    for r in rows(p):
        if r.get("kind") != "interrogate":
            continue
        t = r.get("reflection") or ""
        c["n"] += 1; c["judge_genuine"] += bool(r.get("genuine"))
        a, b = bool(conf.search(t)), bool(doubt.search(t))
        c[f"conf={a},doubt={b}"] += 1
    report["other"]["self_interrogation"] = dict(c)

# self-implication (P-0036): fires / A rate (the well-behaved null user)
p = DATA / "self_implication_shadow.jsonl"
if p.exists():
    c = Counter()
    for r in rows(p):
        if "fires" in r:
            c["n"] += 1; c["fires"] += bool(r.get("fires")); c["A"] += bool(r.get("A"))
    report["other"]["self_implication_thought_scan"] = dict(c)

# refinery shadow (P-0051): insight always produced, even at low fidelity
p = DATA / "refinery_shadow.jsonl"
if p.exists():
    c = Counter(); lowfid = 0
    for r in rows(p):
        c["n"] += 1; c["empty_insight"] += not (r.get("insight") or "").strip()
        c["accepted"] += bool(r.get("accepted"))
        f = r.get("fidelity")
        if isinstance(f, (int, float)) and f < 0.5:
            lowfid += 1
    c["fidelity_under_0.5"] = lowfid
    report["other"]["refinery_shadow"] = dict(c)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT)
for n, e in report["nodes"].items():
    w = e.get("windows", {})
    for win in ("all", "since_0925"):
        a = w.get(win, {}).get("any")
        if a:
            print(f"{e['prompt']} {n:16s} {win:10s} n={a['n']:6d} null={a['null']:6d} rate={a['rate']:.3f}  [{e['null_form']}]")
print(json.dumps(report["other"], indent=1))
