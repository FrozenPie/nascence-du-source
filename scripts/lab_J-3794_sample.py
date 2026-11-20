"""J-3794 pre-registered sampler. Read-only on data/logs/follow_line_shadow.jsonl. Seed 3794."""
import json, random, datetime, sys
CUT = datetime.datetime(2026, 11, 8, 10, 51).timestamp()
SRC = "data/logs/follow_line_shadow.jsonl"
OUT = "docs/lab/J-3794_data/sample.jsonl"
FREEZE_TS = 1794650551.212 + 1  # rows with ts <= this are eligible (frozen at the last row seen when pre-registering)
rows = []
for l in open(SRC, encoding="utf-8"):
    if '"settled"' not in l: continue
    try: r = json.loads(l)
    except Exception: continue
    if r.get("kind") == "settled" and r["ts"] <= FREEZE_TS and (r.get("thought") or "").strip() and (r.get("q") or "").strip():
        rows.append(r)
rng = random.Random(3794)
out = []
for v in ("yes", "partly", "no", "unsaid"):
    post = sorted([r for r in rows if r["verdict"] == v and r["ts"] >= CUT], key=lambda r: r["ts"])
    pre = sorted([r for r in rows if r["verdict"] == v and r["ts"] < CUT], key=lambda r: r["ts"])
    npost = min(20, len(post)); npre = min(10, len(pre))
    pick = rng.sample(post, npost) + rng.sample(pre, npre)
    if len(pick) < 30:  # top up from post
        rest = [r for r in post if r not in pick]
        pick += rng.sample(rest, min(30 - len(pick), len(rest)))
    out += pick
rng.shuffle(out)
with open(OUT, "w", encoding="utf-8") as f:
    for i, r in enumerate(out):
        f.write(json.dumps({"sid": i, **{k: r.get(k) for k in ("ts","q_id","q","thought","verdict","resolved","closure_how","source")}}) + "\n")
import collections
print(len(out), collections.Counter(r["verdict"] for r in out), sum(r["ts"] >= CUT for r in out))
