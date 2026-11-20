"""D-0546 / J-3158: the 7-day read of the commitment SHADOW second look and the per-stand attempt log.

What was built (core/commitment_ledger.py, restart-gated, additive, nothing reads these for behaviour):
  data/commitment_second_look_shadow.jsonl  one row per NEW stand that passed the formation gate: a different-family
                                            judge (SERVE_CHAINS["judge_mixtral"], mixtral) saw ONLY statement + scope and
                                            said stand / insight / unclear (or the call failed: second_look null + error).
  data/commitment_attempts_shadow.jsonl     one row per defeater-judge ask: stand id, attempt number, cumulative allows,
                                            verdict, the judge's own class + why, stand age, denials so far.

The ruling (D-0546, founder 2026-11-02): measure first, change nothing, read 7 days against a HUMAN read. Its defeater: a
re-baselined human read of 40 gate-passing stands that shows precision >= 60 percent means the second look is unneeded.
The scan's own verdict on every gate-passing stand is "stand" (the gate lets through only load_bearing true), so the scan's
precision IS the human-labelled share of stands that are real stands.

Modes
  default   print + write the read report, and write a BLIND 40-stand hand-labelling sheet (statement + scope only; the
            second look's verdict is withheld in a separate key file so the founder's labels are not primed).
  --score SHEET   after the founder fills the LABEL: line under each item (stand / insight / unsure), score the scan's
            precision against the 0.60 bar (with a Wilson 95 percent interval) and the second look against the labels.

READ-ONLY against every live store (opens data/*.jsonl for reading). Zero LLM, zero model load, no core/ import, no Ramses.
Thresholds are declared below BEFORE any result exists; do not tune after looking.

Usage: python scripts/commitment_second_look_read.py [--root C:\\Nascence] [--out-dir DIR] [--since-days N | --since ISO]
                                                     [--label-n 40] [--seed 3158] [--no-sheet] [--score SHEET]
"""
import argparse
import datetime as dt
import json
import math
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------- declared parameters (fixed before any result) ----------------
PRECISION_BAR = 0.60      # D-0546 defeater: human-read precision at or above this -> the second look is unneeded
LABEL_N = 40              # D-0546 defeater: the human read is of 40 gate-passing stands
SEED = 3158
DEFAULT_DAYS = 7          # D-0546: "read 7 days"
HOLDRATE_CUTOVER = 1783377727.0   # core/commitment_ledger.py _HOLDRATE_CUTOVER: every `formed` after it is gate-passed
LABELS = ("stand", "insight", "unsure")
HERE = Path(__file__).resolve().parent.parent


def jl(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return out


def wilson(k, n, z=1.96):
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def pct(k, n):
    return "n/a" if not n else f"{100.0 * k / n:.0f}% ({k}/{n})"


def med(xs):
    return statistics.median(xs) if xs else None


def fmt_min(sec):
    return "n/a" if sec is None else f"{sec / 60:.0f} min"


def load(root):
    d = Path(root) / "data"
    ledger = jl(d / "commitment_ledger.jsonl")
    by_id = defaultdict(list)
    for r in ledger:
        if r.get("id"):
            by_id[r["id"]].append(r)
    return {"second": jl(d / "commitment_second_look_shadow.jsonl"),
            "attempts": jl(d / "commitment_attempts_shadow.jsonl"),
            "ledger": ledger, "by_id": by_id}


def window_start(second, since_iso, since_days, now):
    if since_iso:
        return dt.datetime.fromisoformat(since_iso).timestamp()
    if since_days:
        return now - since_days * 86400.0
    if second:
        return min(r.get("ts", now) for r in second)
    return now - DEFAULT_DAYS * 86400.0


def stand_outcome(events):
    ev = {r.get("event") for r in events}
    life = next((r.get("lifespan_seconds") for r in events if r.get("event") == "dissolved"), None)
    return {"dissolved": "dissolved" in ev, "achieved": "achieved" in ev,
            "reaffirmed": sum(1 for r in events if r.get("event") == "reaffirmed"),
            "denied_judge": sum(1 for r in events if r.get("event") == "drop_denied_judge"),
            "denied_gate": sum(1 for r in events if r.get("event") == "drop_denied"),
            "lifespan_s": life}


def build_report(data, t0, t1, now):
    L = []
    A = L.append
    formed = [r for r in data["ledger"] if r.get("event") == "formed" and r.get("ts", 0) >= max(t0, HOLDRATE_CUTOVER)
              and r.get("ts", 0) <= t1]
    second = [r for r in data["second"] if t0 <= r.get("ts", 0) <= t1]
    attempts = [r for r in data["attempts"] if t0 <= r.get("ts", 0) <= t1]
    A(f"# D-0546 / J-3158 -- commitment second look + attempt log: the read\n")
    A(f"Window {dt.datetime.fromtimestamp(t0):%Y-%m-%d %H:%M} to {dt.datetime.fromtimestamp(t1):%Y-%m-%d %H:%M} "
      f"({(t1 - t0) / 86400:.1f} days). Generated {dt.datetime.fromtimestamp(now):%Y-%m-%d %H:%M}. "
      f"Precision bar {PRECISION_BAR:.0%} (D-0546 defeater).\n")
    # ---- A coverage
    ans = [r for r in second if r.get("second_look") in ("stand", "insight", "unclear")]
    errs = Counter(r.get("error") for r in second if r.get("second_look") is None)
    formed_ids = {r["id"] for r in formed}
    seen_ids = {r.get("stand_id") for r in second}
    A("## A. Coverage (is every new stand accounted for?)")
    A(f"- Gate-passing stands formed in window (ledger `formed`): {len(formed)}")
    A(f"- Second-look rows in window: {len(second)}; answered {len(ans)}; failed {len(second) - len(ans)} "
      f"({dict(errs) or 'none'})")
    A(f"- Formed stands with NO second-look row: {len(formed_ids - seen_ids)} "
      "(expected 0 once the restart has run the whole window; a stand formed while the lane was off, or whose task was "
      "cut by a restart, shows here)")
    lat = [r.get("latency_s") for r in second if isinstance(r.get("latency_s"), (int, float))]
    A(f"- Second-look latency median {med(lat) if lat else 'n/a'} s over {len(lat)} rows\n")
    # ---- B scan vs second look
    cnt = Counter(r["second_look"] for r in ans)
    n = len(ans)
    A("## B. The scan's verdict vs the cross-family second look")
    A("The scan calls EVERY gate-passing stand a stand (the gate passes only load_bearing true), so agreement = the share "
      "the second look also calls a stand.")
    A(f"- stand {pct(cnt['stand'], n)} | insight {pct(cnt['insight'], n)} | unclear {pct(cnt['unclear'], n)}")
    dec = cnt["stand"] + cnt["insight"]
    A(f"- Agreement with the scan, unclear counted as disagreement: {pct(cnt['stand'], n)}; unclear excluded: "
      f"{pct(cnt['stand'], dec)}")
    A(f"- Pre-ruling baseline for comparison: a 20-case human read found 5 clear stands (25%) (P-0038 / D-0546). The second "
      f"look is itself a model and is NOT the evidence; section E (the human labels) is.\n")
    # ---- C outcomes by second look verdict (does the second look carry signal beyond itself?)
    A("## C. What happened to each stand, by the second look's verdict")
    A("A check that the second look is not just noise: if its `insight` stands behave differently from its `stand` ones "
      "(dissolve sooner, never achieved, drawn into more re-asks) it carries signal; identical behaviour means it carries "
      "none. Stands still held are right-censored.")
    A("| second look | n | dissolved | achieved | reaffirmed >=1 | judge-denied >=1 | median life of dissolved |")
    A("|---|---|---|---|---|---|---|")
    for v in ("stand", "insight", "unclear"):
        ids = [r["stand_id"] for r in ans if r["second_look"] == v and r["stand_id"] in data["by_id"]]
        outs = [stand_outcome(data["by_id"][i]) for i in ids]
        k = len(outs)
        A(f"| {v} | {k} | {pct(sum(o['dissolved'] for o in outs), k)} | {pct(sum(o['achieved'] for o in outs), k)} | "
          f"{pct(sum(1 for o in outs if o['reaffirmed']), k)} | {pct(sum(1 for o in outs if o['denied_judge']), k)} | "
          f"{fmt_min(med([o['lifespan_s'] for o in outs if o['lifespan_s'] is not None]))} |")
    A("")
    # ---- D attempts
    A("## D. Defeater-judge attempts per stand (D-0546 part 2)")
    asks = len(attempts)
    mix = Counter(r.get("verdict") for r in attempts)
    A(f"- Judge asks in window: {asks} over {len({r['stand_id'] for r in attempts})} stands; verdict "
      f"allow {mix.get('allow', 0)} | deny {mix.get('deny', 0)} | none (judge failed, gate verdict stood) {mix.get(None, 0)}")
    cls = Counter(r.get("judge_class") or "(none)" for r in attempts)
    A(f"- The judge's own class mix: {dict(cls.most_common())}")
    per = defaultdict(list)
    for r in sorted(attempts, key=lambda r: r.get("ts", 0)):
        per[r["stand_id"]].append(r)
    dist = Counter(min(len(v), 6) for v in per.values())
    A(f"- Asks per stand (6 = six or more): {dict(sorted(dist.items()))}")
    denied = {s: v for s, v in per.items() if any(r.get("verdict") == "deny" for r in v)}
    redis, gaps = 0, []
    for s, v in denied.items():
        i_deny = next(i for i, r in enumerate(v) if r.get("verdict") == "deny")   # file order, ts is only 0.1 s resolution
        later_allow = [r["ts"] for r in v[i_deny + 1:] if r.get("verdict") == "allow"]
        if later_allow:
            redis += 1
            gaps.append(later_allow[0] - v[i_deny]["ts"])
    A(f"- Stands denied at least once: {len(denied)}; of those later ALLOWED on a re-ask (the 'dissolved anyway' path): "
      f"{pct(redis, len(denied))}; median first-deny to allow {fmt_min(med(gaps))}  (P-0037 whole-life reference: 58% / 32 min)")
    amax = [v[-1].get("attempt", 0) for v in per.values()]
    A(f"- Highest attempt number seen per stand: median {med(amax) if amax else 'n/a'}, max {max(amax) if amax else 'n/a'}")
    cumok = Counter(v[-1].get("cum_allows", 0) for v in per.values())
    A(f"- Final cumulative allows per stand: {dict(sorted(cumok.items()))}")
    A("- Reading rule: re-asks that end in an allow after repeated denials are the pressure-wears-through path. Whether "
      "a REASONED change of mind is a legitimate drop is a founder question after this measure, not decided here.\n")
    return "\n".join(L), formed, {r.get("stand_id"): r for r in second}


def write_sheet(formed, second_by_id, n, seed, out_dir, stamp):
    rng = random.Random(seed)
    pool = sorted(formed, key=lambda r: r.get("id", ""))
    pick = pool if len(pool) <= n else rng.sample(pool, n)
    rng.shuffle(pick)
    sheet = [f"# D-0546 / J-3158 -- hand-labelling sheet ({len(pick)} gate-passing stands)\n",
             "Label each item by filling the `LABEL:` line with exactly one of: stand | insight | unsure.\n",
             "- **stand**: a commitment he holds -- a name given, a decision, a promise, a position that could be "
             "challenged. Test: could he later be shown to have BROKEN it by acting otherwise?",
             "- **insight**: an observation, realisation, description, musing, want of the moment, small-act report.",
             "- **unsure**: you cannot tell from the sentence and scope alone.\n",
             "You see only the statement and scope the scan produced. The cross-family second look's verdict is "
             "withheld on purpose (it is in the key file) so the read is not primed. Then run:\n",
             f"    python scripts/commitment_second_look_read.py --score <this file>\n"]
    key = {}
    for i, r in enumerate(pick, 1):
        sl = second_by_id.get(r["id"]) or {}
        key[str(i)] = {"stand_id": r["id"], "formed_ts": r.get("ts"), "scan": "stand",
                       "second_look": sl.get("second_look"), "second_look_why": sl.get("why", "")}
        sheet.append(f"### {i}")
        sheet.append(f"STATEMENT: {str(r.get('statement', ''))[:300]}")
        sheet.append(f"SCOPE: {str(r.get('scope', ''))[:120]}")
        sheet.append("LABEL: \n")
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = out_dir / f"{stamp}_J-3158_commitment_stand_hand_label_sheet.md"
    kp = sp.with_name(sp.stem + "_key.json")
    sp.write_text("\n".join(sheet), encoding="utf-8")
    kp.write_text(json.dumps({"seed": seed, "n": len(pick), "population": len(pool), "items": key}, indent=1),
                  encoding="utf-8")
    return sp, kp, len(pool)


def score(sheet_path):
    sp = Path(sheet_path)
    kp = sp.with_name(sp.stem + "_key.json")
    key = json.loads(kp.read_text(encoding="utf-8"))["items"]
    text = sp.read_text(encoding="utf-8")
    labels = {}
    for m in re.finditer(r"^### (\d+)\s*$(.*?)(?=^### |\Z)", text, re.S | re.M):
        lm = re.search(r"^LABEL:\s*([A-Za-z]+)", m.group(2), re.M)
        if lm and lm.group(1).lower() in LABELS:
            labels[m.group(1)] = lm.group(1).lower()
    L = []
    A = L.append
    A("# D-0546 / J-3158 -- hand-label score\n")
    A(f"Labelled {len(labels)} of {len(key)} items ({sp.name}).")
    c = Counter(labels.values())
    k, dec = c["stand"], c["stand"] + c["insight"]
    if not labels:
        A("No labels found: fill the LABEL: lines first.")
        return "\n".join(L)
    lo, hi = wilson(k, dec)
    lo2, hi2 = wilson(k, len(labels))
    A(f"- Human labels: stand {c['stand']} | insight {c['insight']} | unsure {c['unsure']}")
    A(f"- Scan precision, unsure excluded: {pct(k, dec)}, Wilson 95% [{lo:.0%}, {hi:.0%}]")
    A(f"- Scan precision, unsure counted as not-a-stand: {pct(k, len(labels))}, Wilson 95% [{lo2:.0%}, {hi2:.0%}]")
    met = (k / dec >= PRECISION_BAR) if dec else False
    A(f"- D-0546 defeater (precision >= {PRECISION_BAR:.0%} -> the second look is unneeded): "
      f"{'MET on the point estimate' if met else 'NOT met on the point estimate'}"
      f"{'' if (lo >= PRECISION_BAR or hi < PRECISION_BAR) else ' -- but the interval straddles the bar, so it is not settled at this n'}.")
    A("\nSecond look vs the human labels (items where both are decisive):")
    conf = Counter()
    for i, h in labels.items():
        s = key.get(i, {}).get("second_look")
        if h in ("stand", "insight") and s in ("stand", "insight"):
            conf[(h, s)] += 1
    tot = sum(conf.values())
    A("| human \\ second look | stand | insight |")
    A("|---|---|---|")
    for h in ("stand", "insight"):
        A(f"| {h} | {conf[(h, 'stand')]} | {conf[(h, 'insight')]} |")
    agree = conf[("stand", "stand")] + conf[("insight", "insight")]
    A(f"- Agreement {pct(agree, tot)}. "
      f"When the second look says insight, the human agrees {pct(conf[('insight', 'insight')], conf[('stand', 'insight')] + conf[('insight', 'insight')])}.")
    A("- The second look only earns a place if it beats the base rate on these labels; a model that says `stand` for "
      "everything agrees with the human exactly as often as the human share of stands.")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=r"C:\Nascence")
    ap.add_argument("--out-dir", default=str(HERE / "docs" / "lab"))
    ap.add_argument("--since-days", type=float, default=None)
    ap.add_argument("--since", default=None, help="ISO datetime window start")
    ap.add_argument("--label-n", type=int, default=LABEL_N)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--score", default=None, help="score a filled hand-labelling sheet and exit")
    a = ap.parse_args(argv)
    if a.score:
        text = score(a.score)
        print(text)
        return 0
    now = time.time()
    data = load(a.root)
    t0 = window_start(data["second"], a.since, a.since_days, now)
    report, formed, second_by_id = build_report(data, t0, now, now)
    stamp = dt.datetime.fromtimestamp(now).strftime("%Y-%m-%d")
    out_dir = Path(a.out_dir)
    extra = ""
    if not a.no_sheet:
        if formed:
            sp, kp, pool = write_sheet(formed, second_by_id, a.label_n, a.seed, out_dir, stamp)
            extra = (f"\n## E. Hand-labelling sheet (the evidence the ruling's defeater needs)\n"
                     f"- {min(a.label_n, pool)} of {pool} gate-passing stands, seeded sample (seed {a.seed}), blind to the "
                     f"second look: {sp}\n- key (do not open before labelling): {kp}\n"
                     + (f"- WARNING: only {pool} stands in the window, fewer than the {a.label_n} the defeater asks for; "
                        f"widen the window with --since-days.\n" if pool < a.label_n else "")
                     + "- After labelling: python scripts/commitment_second_look_read.py --score <sheet>\n")
        else:
            extra = "\n## E. Hand-labelling sheet\n- No gate-passing stands in the window, no sheet written.\n"
    report += extra
    out_dir.mkdir(parents=True, exist_ok=True)
    rp = out_dir / f"{stamp}_J-3158_commitment_second_look_read.md"
    rp.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[report written: {rp}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
