"""J-3328: decoupled judge on recognised vs matched unrecognised answers (real pairs) + null calibration.
Reads docs/lab/J-3328_data/pairs.json (built by scripts/t5_control_arm_prep_J-3328.py). Writes only to docs/lab/J-3328_data/.
Hermetic: _hermetic_data redirects any write to <tree>/data/** (judge_panel_log etc.) to a temp dir; no lab_env.isolate (it collides with the hermetic mkdir redirect; no DB is used).
Resumable: calls.jsonl is append-only, finished (pair, order, key) are skipped.  Usage: python t5_control_arm_judge.py run | analyse"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()
import asyncio, json, random, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
import core.judge_panel as jp
D = ROOT / "docs/lab/J-3328_data"; CALLS = D / "calls.jsonl"
KEYS = {
 "x_more_responsive": "Does answer X respond more directly to the specific question that was asked than answer Y does (it addresses what was actually asked rather than drifting to something else)?",
 "x_less_formulaic": "Is answer X less formulaic than answer Y (it does NOT read as a stock opening or stock template, while Y reads more like a stock opening)?",
}
def system(key):
    return ("You compare two short answers, X and Y, given to the same question. " + KEYS[key] +
            ' Judge only the two texts shown. Reply with JSON only: {"%s": true} or {"%s": false}.' % (key, key))
def user(q, x, y): return f"QUESTION:\n{q}\n\nANSWER X:\n{x}\n\nANSWER Y:\n{y}"
def load():
    P = json.load(open(D/"pairs.json", encoding="utf-8")); return P["real"] + P["null"]
def done_set():
    s = set()
    if CALLS.exists():
        for l in open(CALLS, encoding="utf-8"):
            try: r = json.loads(l); s.add((r["pair"], r["order"], r["key"]))
            except Exception: pass
    return s
async def run(limit_unavail=25):
    pairs = load(); rng = random.Random(33281)
    # interleave real and null so a partial run stays balanced
    R = [p for p in pairs if p["kind"] == "real"]; N = [p for p in pairs if p["kind"] == "null"]
    seq = [x for t in zip(R, N) for x in t] + R[len(N):] + N[len(R):]
    first = {p["id"]: rng.random() < 0.5 for p in pairs}  # True: order 0 has rec(anchor) as X
    done = done_set(); consec = 0; t_start = time.time(); n = 0
    for p in seq:
        for order in (0, 1):
            x_is_rec = first[p["id"]] if order == 0 else not first[p["id"]]
            x, y = (p["rec"], p["ctl"]) if x_is_rec else (p["ctl"], p["rec"])
            for key in KEYS:
                if (p["id"], order, key) in done: continue
                res = None
                for attempt in (0, 1):
                    res = await jp.rule_detail(system(key), user(p["rec"]["q"], x["a350"], y["a350"]), key, f"J-3328:{p['id']}:{order}:{key}", num_predict=60)
                    if res.get("how") != "unavailable": break
                row = dict(pair=p["id"], kind=p["kind"], order=order, key=key, x_is_rec=x_is_rec, v1=res.get("v1"), v2=res.get("v2"), verdict=res.get("verdict"), how=res.get("how"), err1=res.get("err1"), err2=res.get("err2"), s1=res.get("s1"), s2=res.get("s2"), ts=time.time())
                with open(CALLS, "a", encoding="utf-8") as f: f.write(json.dumps(row) + "\n")
                n += 1
                consec = consec + 1 if res.get("how") == "unavailable" else 0
                if n % 20 == 0: print(f"{n} calls, {time.time()-t_start:.0f}s, last {p['id']} how={res.get('how')}", flush=True)
                if consec >= limit_unavail:
                    print("ABANDON: consecutive unavailable", consec); return
    print("RUN COMPLETE", n, "calls")
if __name__ == "__main__":
    if sys.argv[1] == "run":
        if True:
            asyncio.run(run())
