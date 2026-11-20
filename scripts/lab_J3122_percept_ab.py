"""J-3122 lab (Du down): A/B/C of the Lane 2 metaphor judge. A = v1 production, B = v2 (J-2212), C = v1 sysmsg +
the tick's own percept_lines appended to the user prompt. HTTP to judge hubs only; reads lane2_shadow.jsonl via a
byte-copy; writes only under docs/lab/J-3122_data/. Reuses scripts/lab_metaphor_union.py (panel, prompts, stats).
  build | run [--arms C,A,B] [--workers 2] | score
Frame = J-3205 labelled union (221 ticks, prelabels) + stored tiebreak/split ticks + the first 48 over-500 post-boot ticks.
"""
import argparse, json, os, random, shutil, sys, time, collections
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lab_metaphor_union as U
ROOT = U.ROOT; D = os.path.join(ROOT, "docs", "lab", "J-3122_data")
FRAME = os.path.join(D, "frame.jsonl"); RUNS = os.path.join(D, "runs.jsonl"); SNAP = os.path.join(D, "shadow_snapshot.jsonl")
BOOT = time.mktime((2026, 10, 29, 18, 30, 0, 0, 0, -1))
HEAD = "THESE ARE THE WORLD'S OWN NAMES AND VALUES (never figurative):"

def user_C(passage, pl):
    return f"PASSAGE: {passage[:500]}\n\n{HEAD}\n{(pl or '')[:600]}"

def build(a):
    os.makedirs(D, exist_ok=True)
    if not os.path.exists(SNAP): shutil.copyfile(U.LIVE_SHADOW, SNAP)
    ticks = [r for r in U._load_jsonl(SNAP) if r.get("kind") == "tick"]
    byts = {r["ts"]: r for r in ticks}
    frame = {}
    for f in U._load_jsonl(U.UNION):
        t = byts.get(f["tick_ts"])
        frame[f["tick_ts"]] = {"tick_ts": f["tick_ts"], "passage": f["passage"], "src": ["j3205"], "stored": f.get("stored_v1"),
                               "percept_lines": (t or {}).get("percept_lines")}
    def add(t, src):
        p = U.passage_of(t)
        if not p.strip(): return
        e = frame.setdefault(t["ts"], {"tick_ts": t["ts"], "passage": p, "src": [], "stored": None, "percept_lines": t.get("percept_lines")})
        if src not in e["src"]: e["src"].append(src)
        mj = t.get("metaphor_judged") or {}
        if e["stored"] is None and mj.get("verdict") in ("metaphor", "literal"):
            e["stored"] = {"verdict": mj["verdict"], "how": mj.get("how")}
    for t in ticks:
        mj = t.get("metaphor_judged") or {}
        if mj.get("how") in ("tiebreak", "split_no_tiebreak"): add(t, "split")
    over = sorted([t for t in ticks if t["ts"] >= BOOT and len(U.passage_of({**t}) ) and
                   len(" ".join(str(t.get(k) or "") for k in U.FIELDS)) > 500], key=lambda r: r["ts"])[:48]
    for t in over: add(t, "over500")
    rows = sorted(frame.values(), key=lambda r: r["tick_ts"])
    with open(FRAME, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = collections.Counter(s for r in rows for s in r["src"])
    print(len(rows), dict(c), "with percept_lines:", sum(1 for r in rows if r["percept_lines"]))

def panelC(sysmsg, passage, pl):
    # same as U.panel but user prompt carries percepts
    usr = user_C(passage, pl)
    with ThreadPoolExecutor(2) as ex:
        f1 = ex.submit(U.ask, U.JUDGE_1, sysmsg, usr, 120); f2 = ex.submit(U.ask, U.JUDGE_2, sysmsg, usr, 120)
        (v1, w1, e1, s1), (v2, w2, e2, s2) = f1.result(), f2.result()
    if v1 is None and e1 in ("timeout", "http"): v1, w1, e1, s1 = U.ask(U.JUDGE_1, sysmsg, usr, 240)
    if v2 is None and e2 in ("timeout", "http"): v2, w2, e2, s2 = U.ask(U.JUDGE_2, sysmsg, usr, 240)
    verdict, how, v3, w3, e3 = None, "unavailable", None, None, None
    if v1 is not None and v2 is not None:
        if v1 == v2: verdict, how = v1, "agreed"
        else:
            v3, w3, e3, _ = U.ask(U.TIEBREAK, sysmsg, usr, 900)
            verdict, how = (v3, "tiebreak") if v3 is not None else (None, "split_no_tiebreak")
    return {"j1": v1, "j2": v2, "j3": v3, "verdict": verdict, "how": how, "why": w3 or w1 or w2, "e1": e1, "e2": e2, "e3": e3}

def panelC_fast(sysmsg, passage, pl):
    """Hubs were saturated (falcon3 timed out at 200 s+ every call). falcon3 voted True on 0 of 1,442 answered ticks
    (J-2094/F-3844), so the panel's metaphor verdict == JUDGE_1 True AND gemma tiebreak True. Ask JUDGE_1 first, gemma
    only if JUDGE_1 says True. j2 is recorded as None (not asked)."""
    usr = user_C(passage, pl)
    v1, w1, e1, _ = U.ask(U.JUDGE_1, sysmsg, usr, 600)
    if v1 is None: return {"j1": None, "j2": None, "j3": None, "verdict": None, "how": "unavailable", "why": w1}
    if v1 is False: return {"j1": False, "j2": None, "j3": None, "verdict": False, "how": "j1_false_fast", "why": w1}
    v3, w3, e3, _ = U.ask(U.TIEBREAK, sysmsg, usr, 900)
    return {"j1": True, "j2": None, "j3": v3, "verdict": v3, "how": "j1_true_gemma" if v3 is not None else "unavailable", "why": w3 or w1}

def run(a):
    pri = set(json.load(open(os.path.join(D, "priority_ts.json")))) if a.priority else None
    frame = U._load_jsonl(FRAME)
    if pri: frame = [r for r in frame if r["tick_ts"] in pri]; v1p = U.production_prompt(); v2p = U.v2_prompt()
    done = set()
    if os.path.exists(RUNS):
        done = {(r["arm"], r["tick_ts"]) for r in U._load_jsonl(RUNS) if r.get("how") != "unavailable"}
    # reuse J-3205 panel runs for A (v1) and B (v2) on frame ticks they covered
    old = {}
    if os.path.exists(U.RUNS):
        for r in U._load_jsonl(U.RUNS):
            if r["arm"] in ("v1", "v2") and r.get("how") != "unavailable": old[({"v1": "A", "v2": "B"}[r["arm"]], r["tick_ts"])] = r
    jobs = []
    for arm in a.arms.split(","):
        for r in frame:
            k = (arm, r["tick_ts"])
            if k in done or k in old: continue
            if arm == "A" and r["stored"] and r["stored"]["verdict"] in ("metaphor", "literal"): continue
            if arm == "C" and not r["percept_lines"]: continue
            jobs.append((arm, r))
    print(len(jobs), "runs", flush=True); t0 = time.time(); n = [0]; lk = U._lock
    def work(j):
        arm, r = j
        res = (panelC_fast if a.fast else panelC)(v1p, r["passage"], r["percept_lines"]) if arm == "C" else U.panel(v1p if arm == "A" else v2p, r["passage"])
        res = {k: res[k] for k in ("j1", "j2", "j3", "verdict", "how", "why")}; res.update(arm=arm, tick_ts=r["tick_ts"])
        with lk:
            open(RUNS, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n"); n[0] += 1
            if n[0] % 10 == 0: print(n[0], round(time.time() - t0), "s", flush=True)
    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, jobs))
    print("done", n[0], round(time.time() - t0), flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); s = ap.add_subparsers(dest="c")
    s.add_parser("build"); r = s.add_parser("run"); r.add_argument("--arms", default="C,A,B"); r.add_argument("--workers", type=int, default=2); r.add_argument("--priority", action="store_true"); r.add_argument("--fast", action="store_true")
    a = ap.parse_args(); {"build": build, "run": run}[a.c](a)
