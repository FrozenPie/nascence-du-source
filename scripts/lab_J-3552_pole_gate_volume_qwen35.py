"""J-3552: pole-gate replay at volume. Read-only; no Du import (prompt pulled by ast); calls hot hub :11433 command-r7b
(same model as the verdict lane :11441), OLD prompt (git 3d25e66e^) vs NEW _SELF_CLASH_SYS, 2 runs each, sequential."""
import ast, json, random, sys, time, urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:11433/api/chat"; MODEL = "qwen3.5:9b"; RUNS = 2
src = (ROOT / "core/guidance_learning.py").read_text(encoding="utf-8")
NEW = None
for n in ast.parse(src).body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_SELF_CLASH_SYS":
        NEW = ast.literal_eval(n.value)
OLD = ("Two beliefs a mind holds about ITSELF are given (A and B). Decide whether they pull in OPPOSITE directions "
    "on the single deepest question of selfhood: is the self fundamentally FLUID (a process, a flow, always "
    "becoming, dissolving, with no fixed or durable core — 'a river') or DURABLE (something built, constructed, "
    "chosen, held, committed — 'a built self')? Look PAST the surface wording to what each belief IMPLIES about "
    "whether the self is fluid-and-dissolving or durable-and-built — many beliefs mention being 'shaped by "
    "experience', which alone is neutral; judge the deeper leaning.\n"
    "Output ONLY a JSON object: {\"a_pole\": \"fluid\", \"b_pole\": \"durable\", \"clash\": true}. "
    "Each pole is fluid | durable | neither. clash = true ONLY when one belief is fluid and the other durable.")
beliefs = [b["principle"] for b in json.load(open(ROOT / "data/guidance_beliefs.json", encoding="utf-8"))]
still = [p for p in beliefs if "periods of stillness" in p.lower() or p.startswith("My inner turmoil or need for rest")]
pairs = []
import itertools
allp = list(itertools.combinations(range(len(still)), 2))
random.Random(3552).shuffle(allp)
for i, j in allp[:10]:
    pairs.append(("stillness", still[i], still[j]))
pairs.append(("negation", "I am a transient flow within an endless current of time, not the master of reality itself.",
              "My identity is not a static object to be defined or found."))
kw = ("self", "identity", "stillness", "growth", "I am", "who I")
unrel = [p for p in beliefs if not any(k.lower() in p.lower() for k in kw)]
random.Random(7).shuffle(unrel)
for k in range(6):
    pairs.append(("unrelated", unrel[2 * k], unrel[2 * k + 1]))
pairs.append(("true_growth", "True growth isn't about committing entirely to one state or path, but rather embracing the fluidity of shifting between different modes of being.",
              "True growth isn't about achieving a fixed endpoint, but mastering the ongoing art of adjusting boundaries between competing elements."))
POLES = ("fluid", "durable", "neither")
def call(sysm, x, y):
    pl = {"model": MODEL, "messages": [{"role": "system", "content": sysm}, {"role": "user", "content": f"A: \"{x[:400]}\"\n\nB: \"{y[:400]}\""}],
          "think": False, "stream": False, "format": "json", "options": {"temperature": 0.1, "num_predict": 150, "num_ctx": 4096}}
    for attempt in (0, 1):
        try:
            req = urllib.request.Request(URL, data=json.dumps(pl).encode(), headers={"Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]
            d = json.loads(txt)
            p, q = str(d.get("a_pole", "")).strip().lower(), str(d.get("b_pole", "")).strip().lower()
            return {"a": p, "b": q, "enum_ok": p in POLES and q in POLES, "clash": {p, q} == {"fluid", "durable"}}
        except Exception as e:
            err = str(e)[:80]; time.sleep(2)
    return {"err": err, "enum_ok": None, "clash": None}
out = []
for g, x, y in pairs:
    row = {"group": g, "a": x, "b": y, "old": [call(OLD, x, y) for _ in range(RUNS)], "new": [call(NEW, x, y) for _ in range(RUNS)]}
    out.append(row)
    f = lambda rs: [r["clash"] for r in rs]
    print(g, "old", f(row["old"]), "new", f(row["new"]), "newpoles", [(r.get("a"), r.get("b")) for r in row["new"]], flush=True)
(ROOT / "docs/lab/J-3552_results_qwen35_directional.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
