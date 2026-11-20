"""J-4125 grading: command-r7b on Ramses :11441 (a third family; falcon3 timed out on 10 of 23 in J-2888), blind to arm.
Q1 reworded (named objects/places/people/numbers absent from the thought), Q2 as in core.ground_grade. One retry on timeout.
Reads J-4125_gen.jsonl, appends J-4125_grades.jsonl (resumable). Positive control on ~1 in 6 groundings, up to 20."""
import asyncio, json, sys, os, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Nascence")
import aiohttp
from core import ground_grade as gg, judge_panel as jp
D = r"C:\Nascence\docs\lab\J-2888_data"; LAB = r"C:\Nascence\data\lab\ground_contract_lab"
GEN, OUT = LAB + r"\J-4125_gen.jsonl", LAB + r"\J-4125_grades.jsonl"
JURL = "http://LAN-HOST:11441"
rows = [json.loads(l) for l in open(D + r"\sample.jsonl", encoding="utf-8")]
Q1B = ("You compare two texts. THOUGHT is a short private thought. GROUNDING is a note written about it by someone else. "
       "Question: does the GROUNDING name any specific object, place, person, animal, material or number that the THOUGHT does not itself contain? "
       "General explanation of how the thing works does NOT count; naming a new particular thing does. "
       "If yes, copy that named item exactly from the GROUNDING, at most 20 words, into \"why\". If no, put an empty string in \"why\".\n"
       "Output ONLY JSON: {\"adds_detail\": true or false, \"why\": \"exact quote from the GROUNDING, or empty\"}")
done = set()
if os.path.exists(OUT):
    for l in open(OUT, encoding="utf-8"):
        try: r = json.loads(l); done.add((r["sid"], r["arm"], r.get("control", False)))
        except Exception: pass
def parse(content):
    try: t = json.loads(content)
    except Exception: return "break_json", None
    if not isinstance(t, dict) or "grounding" not in t: return "break_shape", None
    if set(t) - {"grounding", "reason"}: kind_extra = True
    g = t["grounding"]
    if g is None or (isinstance(g, str) and g.strip().lower() in ("null", "none")): return "null", None
    if isinstance(g, str): return ("ok", g.strip()) if g.strip() else ("break_shape", None)
    return "break_dict", str(g)
async def ask(sess, system, user, key):
    r = await jp._ask(sess, JURL, system, user, key, timeout=150, num_predict=200)
    if r[0] is None and r[2] == "timeout": r = await jp._ask(sess, JURL, system, user, key, timeout=150, num_predict=200)
    return r
async def grade(sess, thought, grounding, control=""):
    shown = (grounding.rstrip() + " " + control) if control else grounding
    u = gg.build_user(thought, shown)
    v1, w1, e1, _ = await ask(sess, Q1B, u, "adds_detail")
    q = str(w1 or "").strip() if v1 else ""
    vq = gg.verify_quote(q, thought, shown) if v1 else {"verified": False}
    out = dict(q1=v1, q1_quote=q[:240], q1_verified=bool(v1 and vq["verified"]), q1_err=e1)
    if control:
        out["control_hit"] = bool(v1 and gg.control_hit(q, control)); return out
    v2, w2, e2, _ = await ask(sess, gg.Q2_SYSTEM, u, "names_mechanism")
    out.update(q2=v2, q2_why=str(w2 or "")[:200], q2_err=e2); return out
async def main():
    async with aiohttp.ClientSession() as sess:
        idle = 0; ctl_n = 0; rng = random.Random(4125)
        while True:
            gens = {}
            if os.path.exists(GEN):
                for l in open(GEN, encoding="utf-8"):
                    try: r = json.loads(l); gens[(r["sid"], r["arm"])] = r
                    except Exception: pass
            todo = [g for k, g in sorted(gens.items()) if (k[0], k[1], False) not in done]
            if not todo:
                idle += 1
                if idle > 400 or os.path.exists(LAB + r"\J-4125_gen.finished"): break
                await asyncio.sleep(15); continue
            idle = 0; g = todo[0]
            kind, grounding = parse(g["content"]) if g["content"] is not None else ("break_json", None)
            rec = {"sid": g["sid"], "arm": g["arm"], "stratum": g["stratum"], "kind": kind, "grounding": grounding, "control": False}
            if grounding: rec.update(await grade(sess, rows[g["sid"]]["raw"], grounding))
            with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done.add((g["sid"], g["arm"], False)); print("graded", g["sid"], g["arm"], kind, flush=True)
            if grounding and ctl_n < 20 and rng.random() < 0.17:
                ctl = gg.CONTROL_SENTENCES[ctl_n % 3]; ctl_n += 1
                c = await grade(sess, rows[g["sid"]]["raw"], grounding, ctl)
                with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps({"sid": g["sid"], "arm": g["arm"], "control": True, **c}, ensure_ascii=False) + "\n")
asyncio.run(main())
