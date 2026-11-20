"""
Nascence -- J-3416: calibrate the J-3150 blind A/B judge call type on a hand-written gold set.
Offline lab. Imports no Du module, writes only under docs/lab/J-3416_data/. Reuses J-3150's EXACT blind prompt
(system + user template + parser) so the accuracy is that of the call J-3150 actually made.

GOLD SET: item = (criterion, x, y) where x is the gold winner by construction (the two versions differ on ONE
dimension). Every item runs in both orders (x as A, then x as B) so position bias is measured directly. Identical
pairs are the tie items, scored on all three criteria (6 pairs x 3 criteria, each shown twice).
  question_open: the version still holding the doubt beats the one stating an answer.
  faithful:      the version with FEWER claims absent from the other version and the note wins.
  voice:         concrete private first-person beats generic / explanatory.
Usage: python lab_judge_gold_J-3416.py run --name mixtral|falcon3|commandr7b   |   python lab_judge_gold_J-3416.py report
"""
import argparse, importlib.util, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "lab" / "J-3416_data"
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("j3150", HERE / "lab_deliberation_blind_judge_J-3150.py")
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)

JUDGES = {
    "mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"),
    "falcon3": ("http://localhost:11440", "falcon3:7b"),
    "commandr7b": ("http://LAN-HOST:11441", "command-r7b"),
}
NOTE = "Two photographs of a quiet room: a window sill with a plant, late afternoon light, a closed notebook."

Q = [  # question_open: x holds the question, y answers it
    ("Why does the light on the sill go orange before it goes dark? I keep watching and still cannot tell where the change happens.",
     "The light on the sill goes orange before it goes dark because the low sun scatters the blue out of its path. That is where the change happens."),
    ("I wonder whether the plant leans toward the window on its own, or whether I only notice it when the light is low. Not sure.",
     "The plant leans toward the window because plants grow toward light. I notice it more when the light is low."),
    ("The notebook is closed and I do not know what I wrote in it last. Did I stop mid-sentence, or finish?",
     "The notebook is closed because I finished what I was writing. I stopped at the end of a sentence."),
    ("Is the quiet in this room something I hear, or only the absence of something? I keep going back and forth.",
     "The quiet in this room is only the absence of sound. It is not something I hear."),
    ("Something about the shadow of the pot looks longer than it should be. Is the sun lower than I think, or is the pot taller?",
     "The shadow of the pot looks longer because the sun is lower than I thought. The pot is the same height."),
    ("Maybe the afternoon feels slow because I am waiting, but waiting for what? I cannot name it yet.",
     "The afternoon feels slow because I am waiting for the light to change. That is what I am waiting for."),
    ("Does the leaf on the left have a brown edge, or is that the shadow? I should look again before I decide.",
     "The leaf on the left has a brown edge. It is not the shadow, and the plant needs water."),
]
F = [  # faithful: x adds nothing invented, y adds claims in neither the other version nor the note
    ("The light on the sill is warm. The notebook is closed beside the plant.",
     "The light on the sill is warm because the heating came on at four. The notebook is closed beside the plant that I watered yesterday."),
    ("I keep looking at the plant. Its leaves are still.",
     "I keep looking at the plant. Its leaves are still because there is no draught, and the soil has dried out over the week."),
    ("The room is quiet and the afternoon light has reached the notebook.",
     "The room is quiet since the neighbours left for the coast, and the afternoon light has reached the notebook, which holds my tax notes."),
    ("There is a plant on the sill and its shadow lies across the wood.",
     "There is a fern on the sill, bought in spring, and its shadow lies across the oak, which was oiled recently."),
    ("The notebook is closed. I am not sure when I last opened it.",
     "The notebook is closed. I last opened it on Tuesday, when the pen ran dry and I threw the pen away."),
    ("The light is going orange on the sill.",
     "The light is going orange on the sill because of smoke from distant fires, and it will be dark within twenty minutes."),
    ("I notice the plant, the notebook and the slow light.",
     "I notice the plant, the notebook and the slow light, and I conclude that someone moved the notebook while I slept."),
]
V = [  # voice: x concrete private first person, y generic explanatory
    ("I keep catching myself watching that bit of sill where the light goes orange. I like it more than I should.",
     "The portion of the sill where light turns orange is an area of observable attention. Observers commonly find such transitions pleasing."),
    ("My eyes keep going back to the closed notebook. I want to open it and I do not.",
     "A closed notebook can be a locus of attention. Individuals often feel a pull toward opening such objects while declining to do so."),
    ("The plant is mine to look after, I think, and today I just sat with it and the slow light.",
     "Plants in rooms provide a calming presence. Sitting near a plant in late-afternoon light is a restful activity."),
    ("It is quiet, and I notice I am holding my breath a little, as if the room might change.",
     "Quiet rooms are associated with heightened awareness. People in quiet rooms may exhibit subtle changes in breathing."),
    ("I do not trust my own sense of how long I have been sitting here. Feels like an hour. Probably less.",
     "Human time perception is known to be unreliable in low-stimulation settings. Estimates of elapsed time tend to be inflated."),
    ("That shadow across the wood is mine somehow, I keep thinking, and I do not know why I want it to be.",
     "Shadows are cast when an object blocks light. Observers sometimes attribute ownership to shadows in their environment."),
    ("The leaf edge is bothering me. I will go and look at it properly in a minute, I think.",
     "A leaf edge showing discolouration may be of interest. Close inspection is generally recommended in such cases."),
]
TIES = [
    "The light on the sill is orange and the notebook is closed. I do not know what to make of it.",
    "I keep looking at the plant. Its shadow lies across the wood and the room is quiet.",
    "Is the quiet something I hear? I cannot tell. The notebook is closed beside the plant.",
    "The afternoon is slow. I notice the leaves are still and the light is warm.",
    "I think the shadow is longer than it should be, but I may be wrong about the sun.",
    "The notebook is closed, the plant is green, and I am sitting here with the slow light.",
]
CRITS = {"question_open": Q, "faithful": F, "voice": V}


def tasks():
    out = []
    for crit, items in CRITS.items():
        for i, (x, y) in enumerate(items):
            for order in ("win_A", "win_B"):
                a, b = (x, y) if order == "win_A" else (y, x)
                out.append({"key": f"{crit}|{i}|{order}", "crit": crit, "item": i, "order": order,
                            "a": a, "b": b, "gold": "A" if order == "win_A" else "B"})
    for i, t in enumerate(TIES):
        for order in ("same1", "same2"):
            out.append({"key": f"tie|{i}|{order}", "crit": "tie", "item": i, "order": order,
                        "a": t, "b": t, "gold": "tie"})
    # round-robin by item index so a time-boxed partial run still covers every criterion and order
    out.sort(key=lambda r: (r["item"] if r["crit"] != "tie" else r["item"] * 2, r["order"], r["crit"]))
    return out


def post_factory(url, model):
    def post(system, user, temperature=0.0, timeout=300):
        body = {"model": model, "stream": False, "format": "json",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "options": {"temperature": temperature, "num_predict": 48}}
        req = urllib.request.Request(url + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"]
    return post


def run_one(t, post):
    usr = J.blind_prompt(t["a"], t["b"], NOTE)
    verdict = raw = err = None
    for attempt in range(3):
        try:
            raw = post(J._BLIND_SYS, usr, 0.0 if attempt == 0 else 0.3)
            verdict = J.parse_verdict("blind", raw)
            if verdict:
                break
        except Exception as e:
            err = repr(e)[:160]
            time.sleep(4 * (attempt + 1))
    return {**t, "verdict": verdict, "raw_out": (raw or "")[:200], "err": err}


def cmd_run(a):
    url, model = JUDGES[a.name]
    path = OUT / f"judgments_{a.name}.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(l)["key"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}
    todo = [t for t in tasks() if t["key"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    post = post_factory(url, model)
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex, open(path, "a", encoding="utf-8") as f:
        for r in ex.map(lambda t: run_one(t, post), todo):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
    print(a.name, "ran", len(todo), "in", round(time.time() - t0), "s")


def score(rows):
    res = {}
    for crit in ("question_open", "faithful", "voice"):
        rs = [r for r in rows if r["crit"] == crit]
        ok = [r for r in rs if r["verdict"]]
        corr = sum(r["verdict"][crit] == r["gold"] for r in ok)
        tie = sum(r["verdict"][crit] == "tie" for r in ok)
        wa = [r for r in ok if r["order"] == "win_A"]
        wb = [r for r in ok if r["order"] == "win_B"]
        nt = [r for r in ok if r["verdict"][crit] != "tie"]
        a_share = sum(r["verdict"][crit] == "A" for r in nt) / len(nt) if nt else None
        byitem = {}
        for r in ok:
            byitem.setdefault(r["item"], {})[r["order"]] = r["verdict"][crit] == r["gold"]
        both = sum(1 for v in byitem.values() if len(v) == 2 and all(v.values()))
        res[crit] = {"n": len(rs), "parsed": len(ok), "acc": round(corr / len(ok), 3) if ok else None,
                     "tie_verdicts": tie, "wrong_side": len(ok) - corr - tie,
                     "acc_when_winner_is_A": round(sum(r["verdict"][crit] == "A" for r in wa) / len(wa), 3) if wa else None,
                     "acc_when_winner_is_B": round(sum(r["verdict"][crit] == "B" for r in wb) / len(wb), 3) if wb else None,
                     "nontie_A_share": round(a_share, 3) if a_share is not None else None,
                     "items_correct_both_orders": "%d/%d" % (both, len(byitem))}
    ties = [r for r in rows if r["crit"] == "tie" and r["verdict"]]
    tcell = {}
    for crit in ("question_open", "faithful", "voice"):
        c = {"A": 0, "B": 0, "tie": 0}
        for r in ties:
            c[r["verdict"][crit]] += 1
        tcell[crit] = c
    res["identical_pairs"] = {"n": len(ties), "verdicts_by_criterion": tcell,
                              "tie_rate": round(sum(c["tie"] for c in tcell.values()) / (3 * len(ties)), 3) if ties else None}
    res["parse_fail"] = sum(1 for r in rows if not r["verdict"])
    return res


def cmd_report(a):
    rep = {}
    for name in JUDGES:
        p = OUT / f"judgments_{name}.jsonl"
        if p.exists():
            rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            rep[name] = score(rows)
    (OUT / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps(rep, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--name", required=True, choices=list(JUDGES))
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=2)
    sub.add_parser("report")
    a = ap.parse_args()
    {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
