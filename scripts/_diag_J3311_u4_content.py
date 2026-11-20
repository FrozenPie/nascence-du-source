"""J-3311 POST-HOC diagnostic (not preregistered): how many U4 positives survive if the shared 4-gram must contain
at least 2 tokens of 5+ letters (content-ish) and no bare apostrophe token. Read-only. Writes docs/lab/J-3311_data/u4_content_diag.json."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_J3311_used_label as A

units = A.read_jsonl(A.OUT / "labels.jsonl")
fin = A.load_voice_finals()
db = A.open_db()
fr = A.fetch_fragments(db, {u["fragment_id"] for u in units})
db.close()

def ok(g):
    return all(t.strip("'") for t in g) and sum(1 for t in g if len(t.strip("'")) >= 5) >= 2

by = {}
tot_pos = tot_strict = 0
for u in units:
    if not u["u4"]:
        continue
    sh = A.grams4(fr[u["fragment_id"]][0]) & A.grams4(fin[u["cycle_id"]])
    strict = any(ok(g) for g in sh)
    d = by.setdefault(u["origin"], [0, 0])
    d[0] += 1
    d[1] += strict
    tot_pos += 1
    tot_strict += strict
res = {"u4_positives": tot_pos, "u4_strict_positives": tot_strict, "strict_rate_over_all_units": round(tot_strict / len(units), 4),
       "by_origin_pos_strict": {k: v for k, v in sorted(by.items(), key=lambda kv: -kv[1][0])[:10]}}
(A.OUT / "u4_content_diag.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
