"""J-1198: compare the walk-back replay (units file, or the final jsonl) with J-1086's 2026-09-18 baseline (F-1504).

Read-only: no hub calls, no repo imports. Prints a markdown section; with --append-report it replaces/appends the
"## Comparison with the J-1086 baseline" section of docs/lab/train_split_merge_step2_replay_2026-09-22_walkback.md.

  python scripts/lab_j1198_compare_baseline.py [--units PATH] [--append-report]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT.parent
ap = argparse.ArgumentParser()
ap.add_argument("--units", default=str(SCRATCH / "lab_j1198_units.jsonl"))
ap.add_argument("--append-report", action="store_true")
ARGS = ap.parse_args()

BASE = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-18_scopestatus.jsonl"
REPORT = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback.md"
HEAD = "## Comparison with the J-1086 baseline (F-1504, fallback in both calls)"


def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


old = load(BASE)
new_rows = load(ARGS.units)
new = [r["record"] if "record" in r else r for r in new_rows]
new = [r for r in new if r.get("disprove_status") != "INFRA_EXCLUDED"]


def shares(rs):
    c = Counter(r["disprove_status"] for r in rs)
    n = len(rs) or 1
    return c, {k: round(v / n, 3) for k, v in c.items()}


def second_stats(rs):
    reached = [r for r in rs if r.get("disprove_scope_how") is not None]
    tb = [r for r in reached if r["disprove_scope_how"] == "tiebreak"]
    return len(reached), len(tb)


def first_tb(rs):
    return sum(1 for r in rs if r.get("disprove_how") == "tiebreak")


lines = [HEAD, ""]
co, so = shares(old)
cn, sn = shares(new)
lines += [f"- J-1086 (n={len(old)}): {dict(co)} -> shares {so}",
          f"- J-1198 (n={len(new)}): {dict(cn)} -> shares {sn}", ""]
for w in ("A", "B"):
    o = [r for r in old if r["window"].startswith(w)]
    n = [r for r in new if r["window"].startswith(w)]
    lines.append(f"- window {w}: J-1086 {dict(Counter(r['disprove_status'] for r in o))} | J-1198 {dict(Counter(r['disprove_status'] for r in n))}")
ro, to = second_stats(old)
rn, tn = second_stats(new)
lines += ["", f"- second (scope_only) call reached: J-1086 {ro}/{len(old)}, tiebreak-decided {to} ({100.0 * to / ro:.1f}% of those reached); "
              f"J-1198 {rn}/{len(new)}, tiebreak-decided {tn} ({(100.0 * tn / rn) if rn else 0:.1f}% of those reached)",
          f"- first-call TIEBREAK (-> UNDETERMINED, unchanged fallback): J-1086 {first_tb(old)}/{len(old)}, J-1198 {first_tb(new)}/{len(new)}", ""]

# how much of the distribution rests on the second call's TIEBREAK vote: re-derive the shares of THIS run's own
# records under three rules for those events (no new hub calls): the walk-back as run; J-0986's fallback (second-call
# tiebreak -> UNDETERMINED); and the opposite constant vote (every second-call tiebreak -> True = held_within_scope).
tb_ev = [r for r in new if r.get("disprove_scope_how") == "tiebreak"]
if tb_ev:
    def _shares_under(rule):
        c = Counter()
        for r in new:
            s = r["disprove_status"]
            if r.get("disprove_scope_how") == "tiebreak":
                s = rule(s)
            c[s] += 1
        n_ = len(new) or 1
        return {k: round(v / n_, 3) for k, v in sorted(c.items())}
    as_run = _shares_under(lambda s: s)
    j0986 = _shares_under(lambda s: "UNDETERMINED")
    all_true = _shares_under(lambda s: "held_within_scope")
    lines += [f"- {len(tb_ev)} of {len(new)} replayed events ({100.0 * len(tb_ev) / len(new):.1f}%) have a status decided by a second-call TIEBREAK vote "
              f"(True: {sum(1 for r in tb_ev if r['disprove_status'] == 'held_within_scope')}, False: "
              f"{sum(1 for r in tb_ev if r['disprove_status'] == 'objected')}). The same records re-derived under three rules for those events:",
              f"    - walk-back as run: {as_run}",
              f"    - J-0986's fallback (second-call tiebreak -> UNDETERMINED): {j0986}",
              f"    - opposite constant vote (every second-call tiebreak -> True = held_within_scope): {all_true} "
              f"(D-0181's held_within_scope > 70% bar would {'FAIL' if all_true.get('held_within_scope', 0) > 0.7 else 'pass'} there)", ""]

# window A: byte-identical claims -> event-level transitions old status -> new status
oldA = {r["claim"]: r for r in old if r["window"].startswith("A")}
trans = Counter()
same_support = 0
n_pair = 0
for r in new:
    if not r["window"].startswith("A"):
        continue
    o = oldA.get(r["claim"])
    if o is None:
        continue
    n_pair += 1
    trans[(o["disprove_status"], r["disprove_status"])] += 1
    same_support += int(o["support"] == r["support"])
if n_pair:
    lines += [f"- window A, byte-identical claims ({n_pair} paired; prove's support text is identical in {same_support} of them, "
              "so the two runs are NOT paired on the support): old status -> new status:"]
    for (a, b), c in sorted(trans.items(), key=lambda kv: -kv[1]):
        lines.append(f"    - {a} -> {b}: {c}")
    lines.append("")
out = "\n".join(lines)
print(out)
if ARGS.append_report and REPORT.exists():
    text = REPORT.read_text(encoding="utf-8")
    cut = text.find("\n\n" + HEAD)
    if cut >= 0:
        # replace only this section (it ends at the next '## ' heading or EOF)
        tail_i = text.find("\n## ", cut + 4 + len(HEAD))
        tail = text[tail_i:] if tail_i >= 0 else ""
        text = text[:cut] + tail
    p3 = text.find("\n\n## Part 3 — read against")
    if p3 >= 0:                       # keep Part 3 last: lab_j1198_part3_tiebreak_reads.py replaces from its heading to EOF
        text = text[:p3].rstrip("\n") + "\n\n" + out + "\n" + text[p3:]
    else:
        text = text.rstrip("\n") + "\n\n" + out + "\n"
    REPORT.write_text(text, encoding="utf-8")
    print(f"[compare] wrote section into {REPORT}")
