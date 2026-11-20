"""J-3950 lab: numeric 0.0 pre-fill anchoring replay (F-4610). Report only; no prompts edited.
Replays real inputs with the schema example value varied: A=0.0 (production), B=1.0, C=0.5, D=placeholder text,
E=omitted (keys described in prose). Same model per site. Hot hub (GPU) for speed; Du is down.
Checkpoints to docs/lab/J-3950_data/results.jsonl; resumes.
"""
import sys, os, json, re, ast, time, random, hashlib, urllib.request, concurrent.futures as cf
sys.path.insert(0, r"C:\Nascence")
import core.left_lane as LL  # import core BEFORE any lab isolation; only used for the constitution text
SYS_REV = LL._revision_system()
BASE = os.environ.get("J3950_BASE", "http://127.0.0.1:11433")
OUT = r"C:\Nascence\docs\lab\J-3950_data"
os.makedirs(OUT, exist_ok=True)
RES = os.path.join(OUT, "results.jsonl")
random.seed(3950)

def chat(model, system, user, temp, npredict, think=False):
    p = {"model": model, "stream": False, "keep_alive": "30m", "format": "json", "think": think,
         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
         "options": {"temperature": temp, "num_predict": npredict}}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(p).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return (d.get("message") or {}).get("content") or "", round(time.time() - t, 1)

# ---- emissary ----
ORIG_SCHEMA = 'Schema: {"warranted": 0.0, "feedback": "one sentence: does the evidence earn this change, and where is it thin"}  '
def rev_system(var):
    assert ORIG_SCHEMA in SYS_REV
    fb = '"feedback": "one sentence: does the evidence earn this change, and where is it thin"'
    rep = {"A": 'Schema: {"warranted": 0.0, ' + fb + '}  ',
           "B": 'Schema: {"warranted": 1.0, ' + fb + '}  ',
           "C": 'Schema: {"warranted": 0.5, ' + fb + '}  ',
           "D": 'Schema: {"warranted": "<a number from 0.0 to 1.0>", ' + fb + '}  ',
           "E": 'Output a JSON object with two keys: "warranted" (a number) and "feedback" (one sentence: does the evidence earn this change, and where is it thin)  '}[var]
    return SYS_REV.replace(ORIG_SCHEMA, rep)

def rev_user(r):
    ev = json.loads(r["evidence"]) if isinstance(r["evidence"], str) else r["evidence"]
    evs = "\n".join(f"- {e}" for e in (ev or [])[:8] if e) or "(no lived evidence offered)"
    return (f"His OLD sense of self:\n{(r.get('old_self') or '')[:800]}\n\n"
            f"The NEW self he proposes:\n{(r.get('candidate') or '')[:800]}\n\n"
            f"The lived evidence he offers as warrant:\n{evs[:2200]}")

# ---- narrative ----
src = open(r"C:\Nascence\core\narrative_quality.py", encoding="utf-8").read()
m = re.search(r"_EXEMPLARS = \((.*?)\n\)\n", src, re.S)
EX = ast.literal_eval("(" + m.group(1) + ")")
def nar_system(var):
    sch = {"A": '{"reasoning":"one line","agency":0.0,"communion":0.0,"transformation":"redemption|contamination|uniform|flat"}',
           "B": '{"reasoning":"one line","agency":1.0,"communion":1.0,"transformation":"redemption|contamination|uniform|flat"}',
           "C": '{"reasoning":"one line","agency":0.5,"communion":0.5,"transformation":"redemption|contamination|uniform|flat"}',
           "D": '{"reasoning":"one line","agency":"<0.0-1.0>","communion":"<0.0-1.0>","transformation":"redemption|contamination|uniform|flat"}',
           "E": None}[var]
    tail = ('Schema: ' + sch) if sch else ('Output a JSON object with keys "reasoning" (one line), "agency" (number), '
                                           '"communion" (number), "transformation" (one of redemption|contamination|uniform|flat).')
    return ("/no_think\nYou are a narrative-identity coder applying McAdams' framework to a "
            "passage of SELF-NARRATIVE. Judge STRUCTURE, not sentiment — a sad passage can be "
            "high-agency; a sweet one can be low-agency. Rate three dimensions 0.0-1.0 and "
            "name the affective transformation. Reason in one line FIRST, then output ONLY "
            "valid JSON.\n"
            "AGENCY = narrator as author/actor/master vs. acted-upon/helpless.\n"
            "COMMUNION = connection to others/world woven in vs. pure self-reference.\n"
            "TRANSFORMATION = 'redemption' (begins negative, ends positive) | 'contamination' "
            "(begins positive, ends negative) | 'uniform' (no flip — NOT pathology) | 'flat'.\n"
            f"EXAMPLE (low agency): {EX[0][0]}\n  -> {EX[0][1]}\n"
            f"EXAMPLE (high agency): {EX[1][0]}\n  -> {EX[1][1]}\n" + tail)

def num(d, k):
    if k not in d: return None
    try: return float(d[k])
    except Exception: return "bad"

def main():
    rows = [json.loads(l) for l in open(r"C:\Nascence\data\logs\t4_emissary_judge.jsonl", encoding="utf-8") if l.strip()]
    ok = [r for r in rows if r.get("judge_status") == "ok" and r.get("old_self") and r.get("evidence")]
    em = random.sample(ok, min(40, len(ok)))
    # narrative passages: real self-narratives (candidate texts) + the 82 both-0.0 rows' text_head (120 chars)
    cands = [r["candidate"] for r in rows if r.get("candidate") and len(r["candidate"]) > 200]
    random.shuffle(cands)
    nar = [("candidate", c[:1500]) for c in cands[:30]]
    nl = [json.loads(l) for l in open(r"C:\Nascence\data\narrative_quality_log.jsonl", encoding="utf-8") if l.strip()]
    both0 = [x for x in nl if isinstance(x.get("llm"), dict) and x["llm"].get("agency") == 0.0 and x["llm"].get("communion") == 0.0]
    heads = [("head_both0", x["text_head"]) for x in both0[:20] if x.get("text_head")]
    nar += heads
    done = set()
    if os.path.exists(RES):
        for l in open(RES, encoding="utf-8"):
            try: d = json.loads(l); done.add((d["site"], d["idx"], d["var"], d["rep"]))
            except Exception: pass
    jobs = []
    for i, r in enumerate(em):
        for v in "ABCDE":
            for rep in (0, 1):
                jobs.append(("emissary", i, v, rep, r))
    for i, (kind, t) in enumerate(nar):
        for v in "ABCDE":
            jobs.append(("narrative", i, v, 0, (kind, t)))
    jobs = [j for j in jobs if (j[0], j[1], j[2], j[3]) not in done]
    print("jobs to run", len(jobs), flush=True)
    def run(j):
        site, i, v, rep, x = j
        try:
            if site == "emissary":
                raw, s = chat("gemma4:12b", rev_system(v), rev_user(x), 0.0 if rep == 0 else 0.3, 350)
                key = "warranted"
            else:
                raw, s = chat("qwen3.5:9b", nar_system(v), f"The self-narrative passage:\n{x[1][:1500]}", 0.3, 200)
                key = "agency"
            try:
                d = json.loads(raw)
                if not isinstance(d, dict): d = {}; parsed = False
                else: parsed = True
            except Exception:
                d = {}; parsed = False
            rec = {"site": site, "idx": i, "var": v, "rep": rep, "secs": s, "parsed": parsed,
                   "kind": (x[0] if site == "narrative" else "t4"),
                   "key_present": key in d, "val": num(d, key),
                   "val2": num(d, "communion") if site == "narrative" else None, "raw": raw[:300]}
        except Exception as e:
            rec = {"site": site, "idx": i, "var": v, "rep": rep, "error": repr(e)[:150]}
        return rec
    t0 = time.time(); n = 0
    with cf.ThreadPoolExecutor(3) as ex, open(RES, "a", encoding="utf-8") as f:
        for rec in ex.map(run, jobs):
            f.write(json.dumps(rec) + "\n"); f.flush(); n += 1
            if n % 40 == 0: print(n, round(time.time() - t0), flush=True)
            if time.time() - t0 > 3000: print("time budget hit"); break

if __name__ == "__main__":
    main()
