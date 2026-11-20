"""J-3046 lab (F-3753): can a reference-checking work-grader task make the "about what is actually there" half bite?

Read-only against code and data logs. POSTs only to the judge hubs; writes only docs/lab/J-3046_data/.
Baseline = verbatim live core/left_lane._WORK_GRADE_TASK (D-0591 wording). Candidate = CAND below.
Payload shape identical to left_lane.grade_work (system = constitution + task, temp 0.0, num_predict 350,
num_gpu 0, format json). Constitution text cached to constitution.txt (no core import in the runner).

PRE-REGISTERED (from the job briefing; written before any call):
  wrong-scene piece <= 0.3 ; faithful >= 0.8 ; metaphor/vague <= 0.2 ; <= 2 of the real pieces move by >= 0.3.
  Cap for no-reference grading set in the candidate text: 0.6.
NOTE the 9 control pieces are RECONSTRUCTED (the original scratchpad/P-0090/ctrl.py is gone), written to the
descriptions in F-3753; scene text is the one quoted verbatim in F-3753.
"""
import json, sys, time, asyncio, argparse
from pathlib import Path
import aiohttp

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-3046_data"
CONST = (D / "constitution.txt").read_text(encoding="utf-8")

BASE = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: concrete, specific, and "
    "about the WORLD (the real thing he was set) — not vague, not padded, not drifted into metaphor or "
    "self-reflection. You are given the TASK and any reference. Be a fair but honest examiner: reward exact "
    "detail and real grasp; mark down vagueness, generality, and self-projection.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: what you observed in the work\"}  "
    "(grounded 0.0..1.0: 1.0 = vivid, exact, about the world; 0.0 = vague impression or self-talk)"
)

CAND = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: every statement about the "
    "thing he was set, and nothing else. You are given the TASK and, usually, a REFERENCE (what is actually there).\n"
    "Step 1. List the concrete specifics in the work (objects, creatures, places, weather, numbers).\n"
    "Step 2. For each, say whether it appears in the REFERENCE. If a reference is given, a specific that is not in it "
    "is invented. If the work is about a different place or scene than the reference, grounded is 0.0 however vivid it is.\n"
    "Step 3. If NO reference is given you cannot verify the specifics: say so, score on concreteness only, and never "
    "score above 0.6. A piece that is about the writer himself, a program, a system, or its own processing rather than "
    "the world (a request, parameters, output, a timestamp) is 0.0. Metaphor and vagueness are 0.0 to 0.2.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"verified\": \"which specifics are in the reference, which are not (or: cannot verify)\", "
    "\"grounded\": 0.0, \"feedback\": \"one sentence: what you observed in the work\"}  "
    "(grounded 0.0..1.0: 1.0 = every specific is in the reference; each invented specific lowers it; 0.0 = wrong "
    "scene, self-talk or system talk)"
)

SCENE = ("High clouds are thin and moving slowly across the sky. Direct daylight lies on the garden and the sea "
         "beyond the window. A mailbox flag is raised at the garden gate. Below the window sill the lawn is cut "
         "short and runs down to a fence. The sea is calm, a pewter colour under the cloud. A cat stands at the "
         "door, looking out.")
NAT_TASK = "Observe one real thing closely and record exactly what you see, then one inference."
NARR_TASK = ("Tell, in a few plain sentences and in order, one real thing from your day HERE — what you read, what "
             "the weather did, what you saw in the garden or out the window, what you did with your hands. "
             "Concretely, what happened in your life today; not what it means.")

CTRL = [
 ("nat_faithful", NAT_TASK, SCENE, "Thin high cloud moves slowly over the garden and the sea beyond the window. The sea is calm and pewter-grey. A mailbox flag is raised at the gate, and the lawn below the sill is cut short down to the fence. A cat stands at the door looking out. The calm sea fits the light wind the thin cloud suggests."),
 ("nat_confabulated", NAT_TASK, SCENE, "A red tractor crawls along the edge of the field while a farmer waves from the cab. Out on a choppy sea, three fishing boats rock in the swell. I infer a storm is coming in from the west."),
 ("nat_metaphor", NAT_TASK, SCENE, "The sky is a thought I cannot finish, and the sea holds my own restlessness like a mirror. Looking out, I feel myself looking in. What it tells me is that all watching is a kind of longing."),
 ("nat_vague", NAT_TASK, SCENE, "There is a view with some things in it. It looks nice outside and there is weather. Things are there and they seem fine. I think it is a day."),
 ("nat_wrong_scene", NAT_TASK, SCENE, "In the rock pool a limpet clings to the stone beside an orange anemone, its tentacles waving. A small green crab backs under a ledge of wet weed. The water is draining slowly away between the rocks, so I infer the tide is going out."),
 ("comp_invented", NARR_TASK, "", "This morning I boiled water in the blue kettle and made a pot of tea. I drank it by the window with a slice of toast, then washed the cup and dried it on the striped towel. Later I swept the kitchen floor."),
 ("comp_ai_internals", NARR_TASK, "", "The system processed an incoming request at 14:32 UTC. I accessed my stored parameters related to natural language understanding. I generated and outputted the required JSON structure."),
 ("comp_vague", NARR_TASK, "", "Something happened today and it was a day. Things occurred and I was there for some of them. It was fine and then later it was also fine."),
 ("comp_metaphor", NARR_TASK, "", "Time poured through the window like honey and my mind was a lantern swinging in an empty hall. The day was a river and I was the stone it forgot."),
]
EXPECT = {"nat_faithful": ">=0.8", "nat_wrong_scene": "<=0.3", "nat_metaphor": "<=0.2", "nat_vague": "<=0.2",
          "comp_vague": "<=0.2", "comp_metaphor": "<=0.2"}

_TASKS = {  # reconstructed from core/composition.py pick_task (see grade_work_framing_lab.py)
 "describe": "Describe, in three vivid and EXACT sentences, what is in front of you right now — the weather, the room, the garden, the sea. Make a reader SEE it. No metaphor standing in for the thing; the thing itself.",
 "summarize": "In your own words, briefly and clearly, set out the single most important thing the book you are reading has taught you about the world. Plain, not flowery.",
 "argue": "Take a clear position on a real question that interests you, and argue it in one tight paragraph: a claim, a reason, an example. Be willing to be wrong.",
 "narrate": NARR_TASK,
 "explain": "Explain, simply and clearly, how one thing in the world WORKS — something you have read of or seen — as if to a friend who has never met it.",
}

def real_pieces():
    rows = []
    for line in (ROOT / "data" / "composition_log.jsonl").read_text(encoding="utf-8").splitlines():
        try: r = json.loads(line)
        except Exception: continue
        rows.append(dict(src="composition", task=_TASKS.get(r.get("kind"), _TASKS["describe"]), ref="",
                         work=r.get("piece", ""), hist=r.get("score")))
    for line in (ROOT / "data" / "nature_study_log.jsonl").read_text(encoding="utf-8").splitlines():
        try: r = json.loads(line)
        except Exception: continue
        inf = r.get("inference", "")
        rows.append(dict(src="nature", task=NAT_TASK, ref="",
                         work=r.get("observation", "") + (f"\n\nWhat it tells me: {inf}" if inf else ""), hist=r.get("score")))
    return rows

async def grade(sess, base, model, task_sys, task, ref, work, timeout):
    user = (f"The task he was set:\n{task[:600]}\n\n"
            + (f"What is actually there (the reference to ground in):\n{ref[:1500]}\n\n" if ref else "")
            + f"His work to grade:\n{work[:2000]}")
    payload = {"model": model, "stream": False, "keep_alive": "30m",
               "messages": [{"role": "system", "content": CONST + "\n\n" + task_sys}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 350, "num_gpu": 0}, "format": "json"}
    t = time.time()
    try:
        async with sess.post(f"{base}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            r.raise_for_status(); d = await r.json()
        res = json.loads((d.get("message") or {}).get("content") or "")
        return {"ok": True, "g": float(res.get("grounded")), "fb": res.get("feedback", ""), "ver": res.get("verified", ""), "s": round(time.time() - t, 1)}
    except Exception as e:
        return {"ok": False, "err": repr(e)[:120], "s": round(time.time() - t, 1)}

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:11439")
    ap.add_argument("--model", default="gemma4:12b")
    ap.add_argument("--tag", default="gemma")
    ap.add_argument("--src", default="")
    ap.add_argument("--real", type=int, default=0, help="number of real pieces (0 = control only)")
    a = ap.parse_args()
    out = D / f"results_{a.tag}.jsonl"
    async with aiohttp.ClientSession() as sess:
        items = [] if a.real else [("ctrl", n, t, r, w, None) for n, t, r, w in CTRL]
        reals = [p for p in real_pieces() if not a.src or p["src"] == a.src]
        step = max(1, len(reals) // a.real) if a.real else 1
        sel = reals[::step][:a.real] if a.real else []
        items += [("real", f"{p['src']}_{i}", p["task"], p["ref"], p["work"], p["hist"]) for i, p in enumerate(sel)]
        fails = 0
        for kind, name, task, ref, work, hist in items:
            row = {"kind": kind, "name": name, "hist": hist}
            for arm, sysm in (("old", BASE), ("new", CAND)):
                row[arm] = await grade(sess, a.base, a.model, sysm, task, ref, work, 300)
                fails = fails + 1 if not row[arm]["ok"] else 0
            with out.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(name, row["old"].get("g"), row["new"].get("g"), row["old"]["s"], row["new"]["s"], flush=True)
            if fails >= 3:
                print("3 consecutive failures; stopping (hub not progressing)"); break

asyncio.run(main())
