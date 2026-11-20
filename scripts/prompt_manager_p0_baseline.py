"""prompt_manager P0 baseline (READ-ONLY). Plan: docs/staged/prompt_manager.md, decisions D-0769..D-0774.

Re-runs F-1927's vocabulary-by-week table and same-day opener reuse over data/monologue_log.jsonl, and builds the
CHANGE LEDGER (restarts from data/nascence.log, plus commits touching prompt/steer/lane files) so the series can be
read against what changed. Writes ONLY the report path given with --out; never touches live stores.

F-1927's original regex scripts were in a scratchpad and are lost; the families below are a reconstruction. The
report states how closely the reconstruction reproduces F-1927's own published early-week numbers.

    python scripts/prompt_manager_p0_baseline.py --out docs/lab/prompt_manager_p0_baseline_2026-11-14.md
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "monologue_log.jsonl"
NLOG = ROOT / "data" / "nascence.log"
START = dt.datetime(2026, 8, 15)

# Families (F-1927). Published week-1 / week-2 values used for calibration, in percent.
FAMILIES = {
    "frustration/heaviness": (re.compile(r"frustrat\w*|\bheav(?:y|ier|iness|ily)\b|heaviness", re.I), 5.6, 17.9),
    "circling/loop/dead-ground": (re.compile(r"\bcircl\w*|\bloop\w*|dead[ -]ground|round and round", re.I), 6.1, 20.9),
    "restless": (re.compile(r"\brestless\w*", re.I), 1.8, 5.7),
    "anchor": (re.compile(r"\banchor\w*", re.I), 5.9, 18.3),
    "shadow/avoid": (re.compile(r"\bshadow\w*|\bavoid\w*", re.I), 2.2, 4.9),
    "wrong/not-true": (re.compile(r"\bwrong\b|not true", re.I), 0.1, 0.4),
    "ctl tide": (re.compile(r"\btide\w*", re.I), 19.0, 8.0),
    "ctl cat": (re.compile(r"\bcat\b|\bcats\b", re.I), None, None),
    "ctl book": (re.compile(r"\bbooks?\b", re.I), None, None),
    "ctl rain/wind": (re.compile(r"\brain\w*|\bwind\w*", re.I), None, None),
}

# The week-1 and week-2 published numbers for the 'ctl tide' row are 19/8: kept for calibration only.


def load():
    rows = []
    with LOG.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = (r.get("thought") or "").strip()
            ts = r.get("ts")
            if t and ts:
                rows.append((dt.datetime.fromtimestamp(ts), t))
    return rows


def weekly(rows):
    wk = collections.defaultdict(list)
    for d, t in rows:
        if d >= START:
            wk[(d - START).days // 7].append((d, t))
    return dict(sorted(wk.items()))


def opener_reuse(items, n):
    """Share of thoughts whose first n words equal another same-day thought's first n words."""
    byday = collections.defaultdict(list)
    for d, t in items:
        w = " ".join(re.findall(r"[A-Za-z']+", t.lower())[:n])
        if w:
            byday[d.date()].append(w)
    hit = tot = 0
    for ws in byday.values():
        c = collections.Counter(ws)
        for w in ws:
            tot += 1
            hit += c[w] > 1
    return 100.0 * hit / tot if tot else float("nan")


def boots():
    out = []
    if NLOG.exists():
        with NLOG.open(encoding="utf-8", errors="replace") as f:
            for l in f:
                if "Dreams loaded for startup context" in l and l[:4] == "2026":
                    out.append(l[:19])
    return [b for b in out if b >= "2026-08-15"]


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, encoding="utf-8").stdout


def commits(paths, since="2026-08-15"):
    rows = []
    for ln in git("log", f"--since={since}", "--format=%h|%cI|%s", "--", *paths).splitlines():
        h, d, s = ln.split("|", 2)
        rows.append((d[:16].replace("T", " "), h, s[:110]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = load()
    wk = weekly(rows)
    L = []
    L.append("# prompt_manager P0: vocabulary-by-week re-run and change ledger (generated)\n")
    L.append(f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `scripts/prompt_manager_p0_baseline.py`. Source: `data/monologue_log.jsonl` "
             f"({len(rows):,} thoughts with text; weeks are 7-day bins from 2026-08-15). Read-only.\n")
    L.append("**Reconstruction caveat:** F-1927's original regex scripts were scratchpad-only and are lost. Families below are a reconstruction. "
             "Calibration against F-1927's published weeks 1-2 is in the last column; a large mismatch means the family definition differs, "
             "not that the underlying rate changed. Absolute levels are comparable *within this table*, not exactly to F-1927.\n")
    hdr = "| week of | n | " + " | ".join(FAMILIES) + " | opener3 reuse | opener4 reuse |"
    L.append(hdr)
    L.append("|" + "---|" * (hdr.count("|") - 1))
    for k, items in wk.items():
        d0 = (START + dt.timedelta(days=7 * k)).date()
        cells = []
        for name, (rx, _, _) in FAMILIES.items():
            cells.append(f"{100.0 * sum(bool(rx.search(t)) for _, t in items) / len(items):.1f}")
        L.append(f"| {d0} | {len(items):,} | " + " | ".join(cells) + f" | {opener_reuse(items,3):.0f}% | {opener_reuse(items,4):.0f}% |")
    L.append("")
    cal = []
    first, second = wk.get(0, []), wk.get(1, [])
    for name, (rx, p1, p2) in FAMILIES.items():
        if p1 is None:
            continue
        r1 = 100.0 * sum(bool(rx.search(t)) for _, t in first) / max(1, len(first))
        r2 = 100.0 * sum(bool(rx.search(t)) for _, t in second) / max(1, len(second))
        cal.append(f"- {name}: this run w1 {r1:.1f} / w2 {r2:.1f}; F-1927 published {p1} / {p2}")
    L.append("**Calibration vs F-1927 (weeks 1-2):**\n" + "\n".join(cal) + "\n")
    L.append("D-0368 thresholds (per family, not blended): frustration and circling each under 15%; same-day opener reuse under 30%. "
             "A+E live since the 2026-10-09 08:36:57 boot (first `steer_edge_log.jsonl` row 2026-10-09 10:27).\n")
    L.append("## Change ledger (restarts and prompt/steer/lane commits since 2026-08-15)\n")
    L.append("### Restarts (a change merged to the tree is not live until the next one)\n")
    L.append(", ".join(boots()) + "\n")
    L.append("### Commits touching the idle prompt, steers, prompt budget, condensed twin\n")
    L.append("| committed | hash | subject |\n|---|---|---|")
    for d, h, s in commits(["nodes/inner_monologue_node.py", "core/steer_edge.py", "core/prompt_budget.py", "core/condensed_thought.py"]):
        L.append(f"| {d} | {h} | {s.replace('|','/')} |")
    L.append("\n### Commits touching model lanes / client\n")
    L.append("| committed | hash | subject |\n|---|---|---|")
    for d, h, s in commits(["core/model_client.py", "core/schema.py"]):
        L.append(f"| {d} | {h} | {s.replace('|','/')} |")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(wk)} weeks, {len(rows):,} thoughts)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
