"""J-3412 (D-0541 defeater part 2): deterministic read of the post-cut control arm. Read-only on Du's stores (copies to temp).
Imports no Du module. Output: docs/lab/J-3412_data/deterministic.json"""
import json, re, shutil, tempfile, hashlib, datetime as d, statistics as st, collections, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Nascence\data"); OUT = Path(r"C:\Nascence\docs\lab\J-3412_data")
tmp = Path(tempfile.mkdtemp(prefix="J-3412_"))
def ld(n):
    if not (D / n).exists():
        return []
    shutil.copyfile(D / n, tmp / n)
    return [json.loads(l) for l in open(tmp / n, encoding="utf-8") if l.strip()]
ctrl = ld("deliberation_control_log.jsonl"); log = ld("deliberation_log.jsonl")
null = ld("deliberation_null_log.jsonl"); guard = ld("deliberation_guard_log.jsonl"); qskip = ld("deliberation_question_skip_log.jsonl")
q = lambda s: "?" in s or "\uff1f" in s
cut = min(r["ts"] for r in ctrl)
day = lambda r: d.date.fromtimestamp(r["ts"]).isoformat()
post = [r for r in log if r["ts"] >= cut]
pre = [r for r in log if cut - 30 * 86400 <= r["ts"] < cut]
W = lambda w: set(re.findall(r"[a-z']{4,}", w.lower()))
FP = re.compile(r"\b(i|my|me|i'm|i've|myself)\b", re.I)
HEDGE = re.compile(r"\b(maybe|perhaps|seems?|wonder|might|unsure|not sure|if)\b", re.I)
def pair_metrics(rows):
    n = len(rows)
    lr = [len(r["integrated"]) / max(1, len(r["raw"])) for r in rows]
    new = []
    for r in rows:
        base = W(r["raw"]) | W(r.get("grounding", ""))
        iw = W(r["integrated"]); new.append(len(iw - base) / max(1, len(iw)))
    return {"n": n, "len_ratio_mean": round(st.mean(lr), 3), "new_word_share_mean": round(st.mean(new), 3),
            "fp_per_100w_raw": round(100 * sum(len(FP.findall(r["raw"])) for r in rows) / max(1, sum(len(r["raw"].split()) for r in rows)), 2),
            "fp_per_100w_integ": round(100 * sum(len(FP.findall(r["integrated"])) for r in rows) / max(1, sum(len(r["integrated"].split()) for r in rows)), 2),
            "hedge_per_100w_raw": round(100 * sum(len(HEDGE.findall(r["raw"])) for r in rows) / max(1, sum(len(r["raw"].split()) for r in rows)), 2),
            "hedge_per_100w_integ": round(100 * sum(len(HEDGE.findall(r["integrated"])) for r in rows) / max(1, sum(len(r["integrated"].split()) for r in rows)), 2),
            "raw_q_pct": round(100 * sum(q(r["raw"]) for r in rows) / n, 2), "integ_q_pct": round(100 * sum(q(r["integrated"]) for r in rows) / n, 2),
            "lost_q_of_q_raws": [sum(q(r["raw"]) and not q(r["integrated"]) for r in rows), sum(q(r["raw"]) for r in rows)]}
# stored-thought accounting post-cut (every eligible thought lands in exactly one bucket)
P = lambda rows: [r for r in rows if r["ts"] >= cut]
bk = {"skipped_by_draw(control)": P(ctrl), "deliberated_rewritten": post, "null_passthrough": P(null), "guard_kept_raw": P(guard), "question_skipped_upfront": P(qskip)}
tot = sum(len(v) for v in bk.values())
buckets = {k: {"n": len(v), "share_pct": round(100 * len(v) / tot, 2), "raw_q_pct": round(100 * sum(q(r["raw"]) for r in v) / max(1, len(v)), 2)} for k, v in bk.items()}
stored_q = sum(q(r["raw"]) for k, v in bk.items() if k != "deliberated_rewritten" for r in v) + sum(q(r["integrated"]) for r in post)
raw_q = sum(q(r["raw"]) for v in bk.values() for r in v)
# the control bucket overlaps in time with qskip/guard? note whether control raws are disjoint from other buckets by hash
import hashlib as H
h = lambda s: H.sha1(s.encode("utf-8")).hexdigest()[:16]
ctrl_h = {r["thought_hash"] for r in P(ctrl)}
overlap = {k: sum(h(r["raw"]) in ctrl_h for r in v) for k, v in bk.items() if k != "skipped_by_draw(control)"}
# per day
byday = collections.defaultdict(lambda: collections.Counter())
for k, v in bk.items():
    for r in v: byday[day(r)][k] += 1
perday = {k: dict(v) | {"deliberated_share_pct": round(100 * v["deliberated_rewritten"] / sum(v.values()), 1)} for k, v in sorted(byday.items())}
nonq = lambda rows: [r for r in rows if not q(r["raw"])]
elig_nonq = sum(len(nonq(v)) for v in bk.values())
res = {"cut_ts": cut, "cut_date": d.datetime.fromtimestamp(cut).isoformat(), "last_ts": max(r["ts"] for r in ctrl),
       "control_rows": len(ctrl), "control_unique_hash": len(ctrl_h), "post_cut_deliberated_rows": len(post),
       "sha1_control_copy": hashlib.sha1((tmp / "deliberation_control_log.jsonl").read_bytes()).hexdigest(),
       "buckets": buckets, "eligible_total": tot, "buckets_overlap_with_control_hash": overlap,
       "rewrite_share_of_all_eligible_pct": round(100 * len(post) / tot, 2),
       "rewrite_share_of_nonq_eligible_pct": round(100 * len(nonq(post)) / elig_nonq, 2),
       "stored_q_pct": round(100 * stored_q / tot, 2), "raw_q_pct_all_eligible": round(100 * raw_q / tot, 2),
       "q_retention_pct_stored_vs_raw": round(100 * stored_q / raw_q, 2),
       "pre_cut_30d_pair_metrics": pair_metrics(pre), "post_cut_pair_metrics": pair_metrics(post),
       "post_cut_nonq_pair_metrics": pair_metrics(nonq(post)),
       "control_vs_integrated_same_days": {
           "control_raw": {"n": len(P(ctrl)), "mean_len": round(st.mean(len(r["raw"]) for r in P(ctrl)), 1), "q_pct": round(100 * sum(q(r["raw"]) for r in P(ctrl)) / len(P(ctrl)), 2),
                           "fp_per_100w": round(100 * sum(len(FP.findall(r["raw"])) for r in P(ctrl)) / sum(len(r["raw"].split()) for r in P(ctrl)), 2),
                           "hedge_per_100w": round(100 * sum(len(HEDGE.findall(r["raw"])) for r in P(ctrl)) / sum(len(r["raw"].split()) for r in P(ctrl)), 2)},
           "control_raw_nonq": {"n": len(nonq(P(ctrl))), "mean_len": round(st.mean(len(r["raw"]) for r in nonq(P(ctrl))), 1)},
           "integrated": {"n": len(post), "mean_len": round(st.mean(len(r["integrated"]) for r in post), 1)}},
       "per_day": perday}
(OUT / "deterministic.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps({k: v for k, v in res.items() if k != "per_day"}, indent=1))
