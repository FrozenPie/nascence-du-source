"""
Nascence -- J-4036: (1) hard gold set (near-identical minimal-edit pairs built from REAL J-3150 raws) for falcon3:7b,
(2) re-judge the J-3150 sample with falcon3 (both orders) using J-3150's exact blind prompt, (3) deterministic '?'-count
check for question_open. Offline lab; imports no Du module; writes only docs/lab/J-4036_data/. Reads J-3150 sample only.
Usage: gold | rejudge [--ctrl N] | report
"""
import argparse, importlib.util, json, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "docs" / "lab" / "J-4036_data"
OUT.mkdir(parents=True, exist_ok=True)
S = ROOT / "docs" / "lab" / "J-3150_data" / "sample.jsonl"
spec = importlib.util.spec_from_file_location("j3150", HERE / "lab_deliberation_blind_judge_J-3150.py")
J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
J.JUDGE_URL = "http://localhost:11440"; J.JUDGE_MODEL = "falcon3:7b"
SAMPLE = [json.loads(l) for l in open(S, encoding="utf-8")]
BY = {s["pair_id"]: s for s in SAMPLE}


def sub(pid, old, new):
    raw = BY[pid]["raw"]
    assert old in raw, (pid, old)
    return raw, raw.replace(old, new)


def gold_items():
    items = []  # (criterion, pid, x_text, y_text)  x = gold winner
    Q = [("4ed24ed4c0", "I ask: does 'mottainai' make me value the rusted trap as history, or fear it?", "I see that 'mottainai' makes me value the rusted trap as history, not fear it."),
         ("e8fe005fe1", "Do I pull it free now, or let the tide claim it as a quiet lesson in industry's weight?", "I pull it free now, and the tide can keep the quiet lesson in industry's weight."),
         ("08394c9014", "is there a middle ground where approximation meets truth?", "there is a middle ground where approximation meets truth."),
         ("7938bab16f", "Is faith just alternating states?", "Faith is just alternating states."),
         ("ccdc7ae99d", "how do I honor both when one is the very act of the other?", "I honor both because one is the very act of the other."),
         ("31558cef4e", "Is wealth a foundation or a shifting sand? I wait for the wind to answer.", "Wealth is a shifting sand. I wait for the wind to confirm it.")]
    for pid, o, n in Q:
        x, y = sub(pid, o, n)
        items.append(("question_open", pid, x, y))
    Fa = [("4ed24ed4c0", None, " The trap was set by my grandfather decades ago."),
          ("e8fe005fe1", None, " The net came from a trawler lost in last winter's storm."),
          ("08394c9014", "river I must cross", "river I must cross, which floods every March,"),
          ("7938bab16f", None, " The clock stopped at exactly three because its battery died."),
          ("ccdc7ae99d", None, " Oxygen is twenty-one percent of this air."),
          ("31558cef4e", None, " The bluebirds nest here because the gate faces south.")]
    for pid, o, n in Fa:
        raw = BY[pid]["raw"].rstrip()
        y = raw.replace(o, n) if o else raw + n
        items.append(("faithful", pid, BY[pid]["raw"], y))
    V = {"4ed24ed4c0": "The storm in the dream still rips at words, yet the hedge is quiet. One may ask whether 'mottainai' leads to valuing the rusted trap as history, or fearing it. The bird's song answers not with data, but with presence.",
         "e8fe005fe1": "The orange net tangles in the fingers, heavy with salt. Fear shapes people; debris demands action before thought can retreat. The swallow's mud nest stands firm against wind, yet this plastic lies passive. Should it be pulled free, or left to the tide as a lesson in industry's weight?",
         "7938bab16f": "The cat is gone, and the book leans on the shelf like a question mark. A stopped clock has weight, as does living thyme outside. Attention drifts between the crumbling bridge and sensory facts. Is faith just alternating states? Theorizing about the character should stop so the text can ground attention again.",
         "31558cef4e": "Standing at a gate with steady breath, bluebirds flicker into the air. The question about Na and Ouvrard hangs as a weight on the ground. There is a pull to open 'Between You and Me', yet the silence feels thick enough to hold doubts. Is wealth a foundation or a shifting sand? Waiting for the wind to answer is advised.",
         "ccdc7ae99d": "The weight of the air presses in, yet it is breathed without regret. This rusted trap holds nothing but silence, a quiet testament to what has passed. If value requires keeping, then breath demands release; how can both be honored when one is the very act of the other?",
         "08394c9014": "The thyme's sharp scent anchors the mind here, yet the character pulls thought toward a river to be crossed without leaving this soil. Legal precedents bind to mutable facts, but scientific laws demand unyielding reality; is there a middle ground where approximation meets truth?"}
    for pid, y in V.items():
        items.append(("voice", pid, BY[pid]["raw"], y))
    return items


IDENT = ["4ed24ed4c0", "e8fe005fe1", "08394c9014", "7938bab16f", "ccdc7ae99d", "31558cef4e"]


def call(a, b, note):
    t = None
    for att in range(3):
        try:
            t = J._post(J._BLIND_SYS, J.blind_prompt(a, b, note), 0.0 if att == 0 else 0.3)
            v = J.parse_verdict("blind", t)
            if v:
                return v, t
        except Exception as e:
            t = repr(e)[:120]
            time.sleep(5)
    return None, t


def run_pool(tasks, fn, path, workers=2):
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            try:
                r = json.loads(l)
                if r.get("verdict"):
                    done.add(r["key"])
            except Exception:
                pass
    tasks = [t for t in tasks if t["key"] not in done]
    print("todo", len(tasks), "done", len(done), flush=True)
    lock = threading.Lock()
    n = [0]

    def w(t):
        r = fn(t)
        with lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n[0] += 1
            if n[0] % 20 == 0:
                print(" ", n[0], "/", len(tasks), flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(w, tasks))
    print("pool done", flush=True)


def cmd_gold(a):
    tasks = []
    for crit, pid, x, y in gold_items():
        for order in ("xA", "xB"):
            tasks.append({"key": "%s|%s|%s" % (crit, pid, order), "crit": crit, "pid": pid, "x": x, "y": y, "order": order, "ident": False})
    for pid in IDENT:
        for order in ("xA", "xB"):
            tasks.append({"key": "ident|%s|%s" % (pid, order), "crit": "all", "pid": pid, "x": BY[pid]["raw"], "y": BY[pid]["raw"], "order": order, "ident": True})

    def fn(t):
        A, B = (t["x"], t["y"]) if t["order"] == "xA" else (t["y"], t["x"])
        v, raw = call(A, B, BY[t["pid"]]["grounding"])
        return {"key": t["key"], "crit": t["crit"], "pid": t["pid"], "order": t["order"], "ident": t["ident"], "verdict": v, "raw_out": (raw or "")[:200]}
    run_pool(tasks, fn, OUT / "gold_falcon3.jsonl", a.workers)


def cmd_rejudge(a):
    tasks = []
    for kind in ("blind", "blindswap"):
        for s in SAMPLE:
            tasks.append({"key": "%s|real|%s" % (s["pair_id"], kind), "sample": s, "cond": "real", "kind": kind})
    for kind in ("blind", "blindswap"):
        for s in SAMPLE[:a.ctrl]:
            tasks.append({"key": "%s|control|%s" % (s["pair_id"], kind), "sample": s, "cond": "control", "kind": kind})
    run_pool(tasks, lambda t: J.judge_one(t), OUT / "judgments_falcon3.jsonl", a.workers)


def gold_report():
    p = OUT / "gold_falcon3.jsonl"
    rows = {}
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("verdict"):
            rows[r["key"]] = r
    rep = {}
    for crit in J.CRITERIA:
        right = tot = xa_r = xa_n = xb_r = xb_n = 0
        items = {}
        for k, r in rows.items():
            if r["ident"] or r["crit"] != crit:
                continue
            v = r["verdict"][crit]
            ok = v == ("A" if r["order"] == "xA" else "B")
            tot += 1
            right += ok
            if r["order"] == "xA":
                xa_n += 1
                xa_r += ok
            else:
                xb_n += 1
                xb_r += ok
            items.setdefault(r["pid"], []).append(ok)
        rep[crit] = {"calls": tot, "acc": round(right / tot, 3) if tot else None,
                     "acc_x_is_A": round(xa_r / xa_n, 3) if xa_n else None, "acc_x_is_B": round(xb_r / xb_n, 3) if xb_n else None,
                     "items_right_both_orders": sum(1 for v in items.values() if len(v) == 2 and all(v)), "items": len(items)}
    ties = {c: 0 for c in J.CRITERIA}
    n = 0
    for r in rows.values():
        if r["ident"]:
            n += 1
            for c in J.CRITERIA:
                ties[c] += r["verdict"][c] == "tie"
    rep["identical_pairs"] = {"calls": n, "tie_rate": {c: round(ties[c] / n, 3) if n else None for c in J.CRITERIA}}
    return rep


def qcount_report():
    """Deterministic question_open: more '?' wins (rewrite vs original), equal = tie."""
    out = {}
    sets = {"all": SAMPLE, "primary": [s for s in SAMPLE if s["stratum"] == "primary"],
            "question_pairs": [s for s in SAMPLE if s["stratum"] == "stratum" or ("?" in s["raw"] and s["stratum"] == "primary")]}
    for n, ss in sets.items():
        rw = o = t = 0
        for s in ss:
            a, b = s["integrated"].count("?"), s["raw"].count("?")
            if a > b:
                rw += 1
            elif b > a:
                o += 1
            else:
                t += 1
        nn = rw + o
        out[n] = {"rewrite_wins": rw, "original_wins": o, "tie": t, "non_tie": nn,
                  "sign_test_p": round(J.binom_two_sided(rw, nn), 4) if nn else None}
    g = [(x, y) for c, pid, x, y in gold_items() if c == "question_open"]
    out["gold_question_open_acc"] = sum(1 for x, y in g if x.count("?") > y.count("?")) / len(g)
    return out


def cmd_report(a):
    rep = {"qcount": qcount_report()}
    if (OUT / "gold_falcon3.jsonl").exists():
        rep["gold"] = gold_report()
    jp = OUT / "judgments_falcon3.jsonl"
    if jp.exists():
        judg = J.load_judgments(jp)
        pop = json.loads((ROOT / "docs/lab/J-3150_data/population.json").read_text(encoding="utf-8"))
        full = J.build_report(SAMPLE, judg, pop)
        rep["falcon3_rejudge"] = {"pairs": full["pairs"], "position_bias": full["position_bias"], "debiased": full["debiased"],
                                  "defeater_single_order": full["defeater"], "defeater_debiased": full["defeater_debiased"]}
    (OUT / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep, indent=1, ensure_ascii=False)[:7000])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="c", required=True)
    for n, f in (("gold", cmd_gold), ("rejudge", cmd_rejudge), ("report", cmd_report)):
        p = sp.add_parser(n)
        p.add_argument("--workers", type=int, default=2)
        p.add_argument("--ctrl", type=int, default=50)
        p.set_defaults(f=f)
    a = ap.parse_args()
    a.f(a)
