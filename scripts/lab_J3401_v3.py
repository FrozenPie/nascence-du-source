"""J-3401 lab: percept-grounded metaphor prompt v3 on the J-3205 union frame. READ-ONLY; no core import.
v3 = production v1 sysmsg + the tick's percept_lines (600 chars, as stored in the shadow log) appended to the user prompt."""
import sys, os, json, shutil, tempfile, argparse, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab_metaphor_union as L
from concurrent.futures import ThreadPoolExecutor
OUT = os.path.join(L.ROOT, "docs", "lab", "J-3401_data"); os.makedirs(OUT, exist_ok=True)
RUNS = os.path.join(OUT, "panel_runs_v3.jsonl")
PERC = os.path.join(OUT, "percepts_by_ts.json")
_lk = threading.Lock()

def build_percepts():
    frame = L._load_jsonl(L.UNION); want = {r["tick_ts"] for r in frame}
    tmp = tempfile.mkdtemp(prefix="J3401_"); p = os.path.join(tmp, "shadow.jsonl")
    shutil.copyfile(L.LIVE_SHADOW, p)
    d = {}
    for r in L._load_jsonl(p):
        if r.get("kind") == "tick" and r["ts"] in want:
            d[str(r["ts"])] = r.get("percept_lines") or ""
    shutil.rmtree(tmp, ignore_errors=True)
    json.dump(d, open(PERC, "w", encoding="utf-8"))
    print("percepts", len(d), "nonempty", sum(1 for v in d.values() if v))

def v3_user(passage, pl):
    return (f"PASSAGE: {passage[:500]}\n\nTHESE ARE THE WORLD'S OWN NAMES AND VALUES (never figurative): {pl[:600]}")

def panel(system, usr):
    with ThreadPoolExecutor(2) as ex:
        f1 = ex.submit(L.ask, L.JUDGE_1, system, usr, 120); f2 = ex.submit(L.ask, L.JUDGE_2, system, usr, 120)
        (v1, w1, e1, s1), (v2, w2, e2, s2) = f1.result(), f2.result()
    if v1 is None and e1 in ("timeout", "http"): v1, w1, e1, s1 = L.ask(L.JUDGE_1, system, usr, 240)
    if v2 is None and e2 in ("timeout", "http"): v2, w2, e2, s2 = L.ask(L.JUDGE_2, system, usr, 240)
    verdict, how, v3, w3, e3 = None, "unavailable", None, None, None
    if v1 is not None and v2 is not None:
        if v1 == v2: verdict, how = v1, "agreed"
        else:
            v3, w3, e3, _ = L.ask(L.TIEBREAK, system, usr, 900)
            verdict, how = (v3, "tiebreak") if v3 is not None else (None, "split_no_tiebreak")
    return {"j1": v1, "j2": v2, "j3": v3, "verdict": verdict, "how": how, "why": w3 or w1 or w2, "e1": e1, "e2": e2, "e3": e3}

def run(a):
    frame = L._load_jsonl(L.UNION); perc = json.load(open(PERC, encoding="utf-8"))
    sysm = L.production_prompt()
    done = {r["tick_ts"] for r in (L._load_jsonl(RUNS) if os.path.exists(RUNS) else []) if r.get("how") != "unavailable"}
    jobs = [r for r in frame if r["tick_ts"] not in done]
    if a.limit: jobs = jobs[:a.limit]
    print(len(jobs), "to run", flush=True)
    def work(r):
        res = panel(sysm, v3_user(r["passage"], perc.get(str(r["tick_ts"]), "")))
        res.update({"arm": "v3", "tick_ts": r["tick_ts"]})
        with _lk:
            open(RUNS, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n")
    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, jobs))
    print("done")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    {"percepts": lambda a: build_percepts(), "run": run}[a.cmd](a)
