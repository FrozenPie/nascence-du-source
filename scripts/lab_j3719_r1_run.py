"""J-3719: R1 live-gate order-control replay. Reuses scripts/lab_j3410_order_replay.py (reverse_order, ask, run, report).
Local hubs only (falcon3 :11440, gemma4 :11439). Mixtral (Ramses) arm: --hubs mixtral is NOT wired (recorded not run)."""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lab_j3719_r1_cases as rc   # imports core first
import lab_j3410_order_replay as rp
from core import self_interrogation

def extra_cases(n=100, seed=3719):
    rnd = random.Random(seed); out = []
    rows = [json.loads(l) for l in (ROOT/"data"/"self_interrogation_shadow.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    k = [r for r in rows if r.get("kind") == "interrogate" and r.get("reflection") and r.get("genuine") is not None]
    f = [r for r in k if r["genuine"] is False]; t = [r for r in k if r["genuine"] is True]
    rnd.shuffle(t); pick = f + t[: n - len(f)]
    for r in pick:
        u = f"ORIGINAL THOUGHT: \"{r['thought'][:400]}\"\n\nREFLECTION: \"{r['reflection'][:400]}\""
        out.append({"station": "P-0105 genuine", "case": "si@%s" % r["ts"], "key": "genuine", "system": self_interrogation._GRADE_SYSTEM,
                    "user": u, "label": None, "label_raw": "producer_log"})
    sysm = rc.systems()["P-0103 resolves"][1]
    rows = [json.loads(l) for l in (ROOT/"data"/"tension_judge_attempts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rnd.shuffle(rows)
    for r in rows[:n]:
        u = f"TENSION: {r['label'][:200]}\n\nTHOUGHT: {r['thought'][:600]}\n\nDoes the thought resolve the tension?"
        out.append({"station": "P-0103 resolves", "case": "ta@%s" % r["ts"], "key": "resolves", "system": sysm,
                    "user": u, "label": None, "label_raw": "producer_log"})
    return out

def all_cases(cap=100):
    cs, _, _ = rc.build(cap)
    cs += extra_cases(cap)
    return rp.interleave(cs)

if __name__ == "__main__":
    cmd = sys.argv[1]
    out = Path(sys.argv[2]); hubs = sys.argv[3].split(",") if len(sys.argv) > 3 else ["falcon3", "gemma4"]
    cs = all_cases()
    from collections import Counter
    print(Counter(c["station"] for c in cs), "unchanged-on-reverse:", sum(rp.reverse_order(c["system"]) == c["system"] for c in cs))
    if cmd == "run":
        print("asked", rp.run(out, hubs, cs))
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
    rep = rp.report(rows)
    out.with_name(out.stem + "_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for k, v in rep.items(): print(k, json.dumps(v))
