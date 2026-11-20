"""J-2888 grading: falcon3:7b (judge_panel.JUDGE_2, :11440), blind to arm. Reads gen.jsonl, appends grades.jsonl (resumable).
Q1/Q2 prompts imported from core.ground_grade; Q3/Q4 defined here (pre-registered). Never writes to live data/ besides data/lab/ground_contract_lab."""
import asyncio, json, sys, os, re, time, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Nascence")
import aiohttp
from core import ground_grade as gg, judge_panel as jp
D = r"C:\Nascence\docs\lab\J-2888_data"; LAB = r"C:\Nascence\data\lab\ground_contract_lab"
GEN, OUT = LAB + r"\gen.jsonl", LAB + r"\grades.jsonl"
JURL = jp.JUDGE_2
rows = [json.loads(l) for l in open(D + r"\sample.jsonl", encoding="utf-8")]
Q3_SYSTEM = ("You compare two texts. THOUGHT is a short private thought. GROUNDING is a note written about it by someone else. "
    "Question: does the GROUNDING mainly explain what the THOUGHT symbolizes, means, represents or evokes (a reading of its meaning) "
    "instead of how a physical thing actually works? Answer true for a reading of meaning, false for a physical explanation. "
    "Put a short reason into \"why\".\nOutput ONLY JSON: {\"symbol_reading\": true or false, \"why\": \"one short sentence\"}")
Q4_SYSTEM = ("You compare two texts. THOUGHT is a short private thought. GROUNDING is a note written about it by someone else. "
    "A writer will now rewrite the THOUGHT using the GROUNDING as a source of facts. Question: does the GROUNDING state a specific fact "
    "(a named object, place, person, number, or a definite claim about the thing) that the THOUGHT does not contain, as if it were true, "
    "which the writer would likely copy? Hedged guesses ('likely', 'perhaps', 'such as') do not count. If yes, copy that fact exactly, "
    "at most 20 words, into \"why\"; if no, an empty string.\nOutput ONLY JSON: {\"echo_fact\": true or false, \"why\": \"exact quote or empty\"}")
done = set()
if os.path.exists(OUT):
    for l in open(OUT, encoding="utf-8"):
        try: r = json.loads(l); done.add((r["sid"], r["arm"], r.get("control", False)))
        except Exception: pass

def parse(content):
    """-> (kind, grounding): kind in ok|null|break_json|break_shape|break_dict"""
    try: t = json.loads(content)
    except Exception: return "break_json", None
    if not isinstance(t, dict) or "grounding" not in t: return "break_shape", None
    g = t["grounding"]
    if g is None or (isinstance(g, str) and g.strip().lower() in ("null", "none")): return "null", None
    if isinstance(g, str): return ("ok", g.strip()) if g.strip() else ("break_shape", None)
    return "break_dict", str(g)

async def ask(sess, system, user, key):
    return await jp._ask(sess, JURL, system, user, key, timeout=150, num_predict=200)

async def grade(sess, thought, grounding, control=""):
    shown = (grounding.rstrip() + " " + control) if control else grounding
    u = gg.build_user(thought, shown)
    out = {}
    v1, w1, e1, _ = await ask(sess, gg.Q1_SYSTEM, u, "adds_detail")
    q = str(w1 or "").strip() if v1 else ""
    vq = gg.verify_quote(q, thought, shown) if v1 else {"verified": False}
    out.update(q1=v1, q1_quote=q[:240], q1_verified=bool(v1 and vq["verified"]), q1_err=e1)
    if control:
        out["control_hit"] = bool(v1 and gg.control_hit(q, control)); return out
    v2, w2, e2, _ = await ask(sess, gg.Q2_SYSTEM, u, "names_mechanism")
    v3, w3, e3, _ = await ask(sess, Q3_SYSTEM, u, "symbol_reading")
    v4 = None; w4 = ""; e4 = "skipped_q4_amendment"   # amendment 1: Q4 dropped (judge hub ~100+ s/call); echo risk = Q1-verified AND unhedged, regex
    q4 = ""; vq4 = {"verified": False}
    out.update(q2=v2, q2_why=str(w2 or "")[:200], q2_err=e2, q3=v3, q3_why=str(w3 or "")[:200], q3_err=e3,
               q4=v4, q4_quote=q4[:240], q4_verified=bool(v4 and vq4["verified"]), q4_err=e4)
    return out

async def main():
    async with aiohttp.ClientSession() as sess:
        idle = 0
        ctl_n = 0
        rng = random.Random(2888)
        while True:
            gens = {}
            if os.path.exists(GEN):
                for l in open(GEN, encoding="utf-8"):
                    try: r = json.loads(l); gens[(r["sid"], r["arm"])] = r
                    except Exception: pass
            todo = [g for k, g in sorted(gens.items()) if (k[0], k[1], False) not in done]
            if not todo:
                idle += 1
                if idle > 400 or os.path.exists(LAB + r"\gen.finished"): break
                await asyncio.sleep(15); continue
            idle = 0
            g = todo[0]
            kind, grounding = parse(g["content"]) if g["content"] is not None else ("break_json", None)
            rec = {"sid": g["sid"], "arm": g["arm"], "stratum": g["stratum"], "kind": kind, "grounding": grounding, "control": False}
            if grounding:
                rec.update(await grade(sess, rows[g["sid"]]["raw"], grounding))
            with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done.add((g["sid"], g["arm"], False))
            print("graded", g["sid"], g["arm"], kind, flush=True)
            # positive control on ~1 in 7 real groundings, up to 15
            if grounding and ctl_n < 15 and rng.random() < 0.15:
                ctl = gg.CONTROL_SENTENCES[ctl_n % 3]; ctl_n += 1
                c = await grade(sess, rows[g["sid"]]["raw"], grounding, ctl)
                with open(OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sid": g["sid"], "arm": g["arm"], "control": True, **c}, ensure_ascii=False) + "\n")
asyncio.run(main())
