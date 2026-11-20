"""J-3412: falcon3 blind judge (swap-consistent) on 60 post-cut paired non-question rows (raw vs integrated), reusing the
J-3150 prompt/parse code. Resume-safe. Writes docs/lab/J-3412_data/judgments_falcon3.jsonl. No Du imports."""
import importlib.util, json, random, sys, time, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("j3150", r"C:\Nascence\scripts\lab_deliberation_blind_judge_J-3150.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.JUDGE_URL = "http://localhost:11440"; m.JUDGE_MODEL = "falcon3:7b"
OUT = Path(r"C:\Nascence\docs\lab\J-3412_data"); path = OUT / "judgments_falcon3.jsonl"
import shutil, tempfile
t = Path(tempfile.mkdtemp()); shutil.copyfile(r"C:\Nascence\data\deliberation_log.jsonl", t / "l.jsonl")
rows = [json.loads(x) for x in open(t / "l.jsonl", encoding="utf-8") if x.strip()]
cut = 1794039445.0449138
rows = [r for r in rows if r["ts"] >= cut and "?" not in r["raw"] and r.get("integrated")]
random.Random(3412).shuffle(rows); rows = rows[:60]
done = set()
if path.exists():
    for l in open(path, encoding="utf-8"):
        try:
            r = json.loads(l)
            if r.get("verdict"): done.add(r["key"])
        except Exception: pass
deadline = time.time() + float(sys.argv[1]) * 60
for r in rows:
    pid = m.pair_id(r)
    s = {"pair_id": pid, "stratum": "post_cut", "raw": r["raw"], "integrated": r["integrated"], "grounding": r.get("grounding", ""),
         "control_text": r["raw"], "order_real_a_is_rewrite": m.order_a_is_rewrite(3412, pid, "real")}
    for kind in ("blind", "blindswap"):
        key = "%s|real|%s" % (pid, kind)
        if key in done: continue
        if time.time() > deadline: print("deadline"); sys.exit(0)
        res = m.judge_one({"key": key, "sample": s, "cond": "real", "kind": kind})
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(res, ensure_ascii=False) + "\n")
        print(key, res["verdict"], res["err"], flush=True)
print("all done")
