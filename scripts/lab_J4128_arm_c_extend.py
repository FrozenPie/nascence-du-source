"""J-4128 lab (Du down): extend J-3122 arm C to the remaining percept-bearing frame ticks and test variant C2
(C + a one-line 'any phrase equal to a listed percept name/value is literal even inside a longer phrase').
HTTP to judge hubs only. Reuses scripts/lab_J3122_percept_ab.py + lab_metaphor_union.py. Writes docs/lab/J-4128_data/.
  run [--budget-min 50] [--workers 3] [--skip-c]
"""
import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lab_metaphor_union as U
import lab_J3122_percept_ab as P
OUT = os.path.join(U.ROOT, "docs", "lab", "J-4128_data"); RUNS = os.path.join(OUT, "runs.jsonl")
C2LINE = ("NOTE: any phrase in the passage that equals one of the names or values listed above is literal, "
          "even when it appears inside a longer phrase.")

def user_C2(passage, pl):
    return f"PASSAGE: {passage[:500]}\n\n{P.HEAD}\n{(pl or '')[:600]}\n\n{C2LINE}"

def fast(sysmsg, usr):
    v1, w1, e1, _ = U.ask(U.JUDGE_1, sysmsg, usr, 600)
    if v1 is None: return {"j1": None, "j2": None, "j3": None, "verdict": None, "how": "unavailable", "why": w1}
    if v1 is False: return {"j1": False, "j2": None, "j3": None, "verdict": False, "how": "j1_false_fast", "why": w1}
    v3, w3, e3, _ = U.ask(U.TIEBREAK, sysmsg, usr, 900)
    return {"j1": True, "j2": None, "j3": v3, "verdict": v3, "how": "j1_true_gemma" if v3 is not None else "unavailable", "why": w3 or w1}

def main(a):
    os.makedirs(OUT, exist_ok=True)
    frame = {r["tick_ts"]: r for r in U._load_jsonl(P.FRAME)}
    old = U._load_jsonl(P.RUNS)
    doneC = {r["tick_ts"] for r in old if r["arm"] == "C" and r.get("how") != "unavailable"}
    cpos = [r["tick_ts"] for r in old if r["arm"] == "C" and r["verdict"]]
    mine = U._load_jsonl(RUNS) if os.path.exists(RUNS) else []
    done = {(r["arm"], r["tick_ts"]) for r in mine if r.get("how") != "unavailable"}
    jobs = [("C2", t) for t in cpos]
    if not a.skip_c:
        jobs += [("C", t) for t, r in frame.items() if r["percept_lines"] and t not in doneC]
    jobs = [j for j in jobs if j not in done]
    print(len(jobs), "runs", flush=True); t0 = time.time(); sysmsg = U.production_prompt(); n = [0]
    def work(j):
        if time.time() - t0 > a.budget_min * 60: return
        arm, t = j; r = frame[t]
        usr = user_C2(r["passage"], r["percept_lines"]) if arm == "C2" else P.user_C(r["passage"], r["percept_lines"])
        res = fast(sysmsg, usr); res.update(arm=arm, tick_ts=t)
        with U._lock:
            open(RUNS, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n"); n[0] += 1
            if n[0] % 5 == 0: print(n[0], round(time.time() - t0), "s", flush=True)
    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, jobs))
    print("done", n[0], round(time.time() - t0), flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--budget-min", type=float, default=50); ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--skip-c", action="store_true"); main(ap.parse_args())
