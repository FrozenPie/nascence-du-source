"""J-2888 prep: build per-arm system + user prompts for the 100 sample rows, inside lab_env.isolate (live DB never touched)."""
import sys, json, os, hashlib
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Nascence")
from core import left_lane, emissary as _emissary, source_sight as _ss      # core BEFORE lab_env
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate
D = r"C:\Nascence\docs\lab\J-2888_data"
live_db = r"C:\Nascence\data\memory\nascence.db"
before = (os.path.getsize(live_db), os.path.getmtime(live_db))
rows = [json.loads(l) for l in open(D + r"\sample.jsonl", encoding="utf-8")]

STEM = left_lane._GROUND_TASK_NO_NULL[: -len(left_lane._GROUND_SCHEMA)]   # task text with no schema line
assert left_lane._GROUND_TASK.startswith(STEM)
LIVE_TASK = left_lane._GROUND_TASK
C_SCHEMA = ("Schema: {\"grounding\": \"2-3 sentences of concrete real-world mechanism behind the literal referent of the thought\"}, "
            "or, when the thought has no physical referent, {\"grounding\": null, \"reason\": \"no physical referent\"}.\n"
            "Never write the words 'symbolizes', 'represents' or 'alludes' (or symbol, metaphor, evokes): say what the thing physically is and does, not what it means.")
D_SCHEMA = ("Schema: {\"grounding\": \"2-3 sentences of concrete real-world mechanism behind the literal referent of the thought\"}, "
            "or {\"grounding\": null, \"reason\": \"no physical referent\"}.\n"
            "Give the mechanism ONLY when the thought itself names a concrete physical thing (an object, a material, an animal, a sound, a place feature, a weather or light condition); "
            "for a thought about a feeling, an idea, a person's act, a book, or a self-image with no physical thing named, answer null. "
            "Name no object, place, person, number or file that the thought does not itself contain; if the mechanism is uncertain, say less, not more.\n"
            "Never write the words 'symbolizes', 'represents' or 'alludes' (or symbol, metaphor, evokes): say what the thing physically is and does, not what it means.")
systems = {}
cons = None
with isolate(also=[]) as lab_dir:
    cons = _emissary.constitution()
    ctx = _emissary.master_context(include_thought=False)
    ctx_old_full = _emissary.master_context(include_thought=True)
    hints_narrow, hints_broad = [], []
    for r in rows:
        t = r["raw"]
        hn = _ss.see_code_narrow(t, k=1) if _ss.is_self_mechanism_narrow(t) else []
        hb = _ss.see_code(t, k=1) if _ss.is_self_mechanism(t) else []
        hints_narrow.append(hn[0] if hn else None); hints_broad.append(hb[0] if hb else None)
print("lab_dir", lab_dir)
systems["A"] = cons + "\n\n" + LIVE_TASK
systems["A0"] = systems["A"]; systems["B"] = systems["A"]
systems["C"] = cons + "\n\n" + STEM + C_SCHEMA
systems["D"] = cons + "\n\n" + STEM + D_SCHEMA

def hint(h):
    return (f"\n\nTHE REAL MECHANISM (you can see the code — ground in what is actually there, not an imagined one):\n  {h['file']}: {h['line']}") if h else ""
def build(ctx_, code, thought):
    return f"{ctx_}{code}\n\nThe thought to ground:\n  \"{thought[:1700]}\"" if (ctx_ or code) else thought[:2000]
# A0 context: previous-thought line first, dream/concern as in the live ctx (approximation, documented)
def ctx_with_prev(prev):
    line = f"his latest thought: \"{' '.join(prev.split())[:160]}\"" if prev else ""
    head = "THE ONE YOU SERVE, right now (ground for him, in his moment):\n  "
    body = ctx[len(head):] if ctx.startswith(head) else ctx
    return head + (line + "\n  " if line else "") + body if ctx else ctx
prompts = {}
for k, r in enumerate(rows):
    t = r["raw"]
    prompts[k] = {
        "A0": build(ctx_with_prev(r["prev_raw"]), hint(hints_broad[k]), t),
        "A": build(ctx, hint(hints_narrow[k]), t),
        "B": build(ctx, "", t),
        "C": build(ctx, "", t),
        "D": build(ctx, "", t),
    }
json.dump({"systems": systems, "prompts": prompts, "ctx": ctx,
           "hints_narrow": sum(1 for h in hints_narrow if h), "hints_broad": sum(1 for h in hints_broad if h)},
          open(D + r"\inputs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
after = (os.path.getsize(live_db), os.path.getmtime(live_db))
print("ctx:", ctx[:400]); print("hints narrow/broad", sum(1 for h in hints_narrow if h), sum(1 for h in hints_broad if h))
print("live db unchanged:", before == after, before, after)
