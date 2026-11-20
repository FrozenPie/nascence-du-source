"""J-2212 lab (2026-10-16, Du down): does a prompt-only change remove the F-2877 false-positive
family from the Lane 2 metaphor judge's tiebreak seat (gemma4:12b, judge hub :11439)?

LAB ONLY. Makes HTTP calls to an already-running judge hub and nothing else: it imports no core
module, executes no Nascence code, and writes only to the --out path you give it (never data/).
The production prompt (arm "v1") is read out of core/lane2.py's `_judge_metaphor` by AST parse, so the
"before" arm is byte-identical to what production sends; arm "v2" is the candidate below. No
production file is changed by this script or by J-2212.

Dataset: J-2177's 155-row set (128 replay splits labelled clear/arguable/fp/None per F-2877 + F-2724,
16 reconstructed D-0311 fixture rows, 11 JUDGE_1-missed positives). Row text is the exact first 500
chars the judge saw.

Usage:
  python scripts/lab_J2212_metaphor_prompt.py run   --data DS.json --out RES.jsonl [--arms v1,v2]
                                                    [--base http://127.0.0.1:11439] [--model gemma4:12b]
  python scripts/lab_J2212_metaphor_prompt.py score --data DS.json --out RES.jsonl [--extra LABELS.json]
"""
import argparse
import ast
import json
import math
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LANE2 = os.path.join(HERE, "..", "core", "lane2.py")


def production_prompt() -> str:
    """The exact sysmsg string literal assigned inside `_judge_metaphor` (AST, no import)."""
    src = open(LANE2, encoding="utf-8-sig").read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_judge_metaphor":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Assign) and len(sub.targets) == 1
                        and getattr(sub.targets[0], "id", None) == "sysmsg"):
                    return ast.literal_eval(sub.value)
    raise RuntimeError("sysmsg not found in _judge_metaphor")


# Candidate prompt (J-2212). Changes vs v1, all aimed at the F-2877 false-positive family, where the
# judge named a category from the prompt ('symbolic', 'self-narrative', 'mood-painting', 'paradox')
# and pinned it on a phrase that is only a sensor reading restated:
#  1. SELF-NARRATIVE narrowed to identity/life-story talk; the body and its state values are excluded.
#  2. New exemption: the writer restates its sensor fields by NAME + VALUE, which can read as an
#     oxymoron ('daylight' band whose value is 'night', 'warmth' band whose value is 'cool') but is a
#     literal report.
#  3. New exemption: real sound/call names, fire, embers, and plain sensation words.
#  4. A positive test: say true only if a quoted phrase characterises the scene's mood, liveliness,
#     meaning or the speaker's identity; odd, garbled or contradictory wording alone is not figurative.
V2 = (
    "You judge whether a short first-person passage uses figurative language rather than plain "
    "literal description of what is currently perceived. The writer is a system that reports its "
    "senses, so its sentences often restate a sensor field by its name together with its current "
    "value. TWO registers count as figurative: (1) METAPHOR, SYMBOLISM or SELF-NARRATIVE in the "
    "river/crossing/becoming/journey/soul/tapestry style -- self-narrative means talk of who the "
    "speaker is, what its life means, or what it is becoming, NOT mention of its body or body state; "
    "(2) AMBIENT-MOOD language that paints the scene's atmosphere, liveliness or meaning, or "
    "personifies it, instead of reporting a percept -- e.g. a place 'alive with' something, sounds "
    "that are 'a symphony' or 'rich with life', the scene 'serene'/'peaceful'/'tranquil'/'cozy'/"
    "'somber'/'vibrant', 'a sense of isolation'. Do NOT flag any of these, they are literal: "
    "(a) a sensor field named together with its value, even when the pair sounds odd or "
    "contradictory -- the 'daylight' field can have the value night or dusk, the 'warmth' field can "
    "be cool or cold, the 'light' field can be dark or dim, so 'the daylight is night', 'dark "
    "daylight', 'a cool warmth', 'the warmth is cold', 'the light band', 'the warmth band' are plain "
    "reports; (b) body-state words and values: 'the body', 'a warm body', 'the body's drive', "
    "'somatic energy', 'somatic tension', fatigue, tension, energy, vitality; (c) the name of a real "
    "sound or call, including bird-call names such as song, trill, chatter, scold, cry, call, bray, "
    "and sounds such as surf booms, waves on shingle, a fire burning or crackling, embers, rain; "
    "(d) a literal comparison of what a real sound or sight resembles ('a sound like a cat "
    "purring'); (e) an ordinary colour/temperature word for a real light source or material ('a warm "
    "glow from the fire', 'a golden sunset'); (f) a real phenomenon with an evocative common name "
    "('dawn chorus'); (g) awkward, garbled or ungrammatical wording -- strangeness alone is not "
    "figurative. Answer true ONLY if you can quote a phrase that characterises the scene's mood, "
    "liveliness or meaning, or the speaker's identity, beyond any percept or field value. Output ONLY "
    "JSON: {\"metaphor\": true|false, \"why\": \"<the quoted phrase, or a short reason>\"}"
)


def call(base, model, sysmsg, passage, timeout=900):
    p = {"model": model, "stream": False, "format": "json",
         "messages": [{"role": "system", "content": sysmsg},
                      {"role": "user", "content": "PASSAGE: " + passage[:500]}],
         "options": {"temperature": 0.0, "num_predict": 200}}
    if base.rstrip("/").endswith(":11433"):
        p["think"] = False  # hot ollama hub: same setting J-2177 used for its :11433 control arm
    t = time.time()
    req = urllib.request.Request(base + "/api/chat", json.dumps(p).encode(),
                                 {"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8-sig"))
    return d["message"]["content"], round(time.time() - t, 1)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def cmd_run(a):
    data = json.load(open(a.data, encoding="utf-8"))
    arms = {"v1": production_prompt(), "v2": V2}
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out, encoding="utf-8"):
            try:
                r = json.loads(line)
                if r.get("verdict") is not None or "err" not in r:
                    done.add((r["arm"], r["set"], r["id"]))
            except Exception:
                pass
    with open(a.out, "a", encoding="utf-8") as f:
        for arm in a.arms.split(","):
            for r in data:
                k = (arm, r["set"], r["id"])
                if k in done:
                    continue
                rec = {"arm": arm, "model": a.model, "base": a.base, "set": r["set"], "id": r["id"]}
                try:
                    c, s = call(a.base, a.model, arms[arm], r["text"])
                    try:
                        v = json.loads(c)
                        rec["verdict"] = v.get("metaphor") if isinstance(v.get("metaphor"), bool) else None
                        rec["why"] = v.get("why")
                    except Exception:
                        rec["verdict"] = None
                    rec["raw"] = c[:300]
                    rec["secs"] = s
                except Exception as e:
                    rec["verdict"] = None
                    rec["err"] = repr(e)[:200]
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
    print("DONE", flush=True)


def cmd_score(a):
    data = json.load(open(a.data, encoding="utf-8"))
    lab = {(r["set"], r["id"]): r for r in data}
    extra = json.load(open(a.extra, encoding="utf-8")) if a.extra else {}
    res = {}
    for line in open(a.out, encoding="utf-8"):
        r = json.loads(line)
        res[(r["arm"], r["set"], r["id"])] = r
    arms = sorted({k[0] for k in res})
    for arm in arms:
        print(f"===== ARM {arm} =====")
        # splits
        sp = [(lab[("split", i)], res[(arm, "split", i)]) for (ar, s, i) in res if ar == arm and s == "split"]
        flagged = [(r, x) for r, x in sp if x.get("verdict") is True]
        nulls = sum(1 for _, x in sp if x.get("verdict") is None)

        def lbl(r):
            return r["label"] or extra.get(r["id"])  # unlabelled rows: hand-read labels from --extra
        clear = sum(1 for r, _ in flagged if lbl(r) == "clear")
        argu = sum(1 for r, _ in flagged if lbl(r) == "arguable")
        unl = [r["id"] for r, _ in flagged if lbl(r) is None]
        n = len(flagged)
        pos_c = sum(1 for r, _ in sp if lbl(r) == "clear")
        pos_i = sum(1 for r, _ in sp if lbl(r) in ("clear", "arguable"))
        print(f"splits n={len(sp)} null={nulls} metaphor={n}  clear={clear} arguable={argu} "
              f"fp/literal={n - clear - argu} (unlabelled flagged: {unl})")
        if n:
            print(f"  strict precision {clear}/{n} = {100 * clear / n:.1f}% Wilson {wilson(clear, n)}")
            print(f"  inclusive precision {clear + argu}/{n} = {100 * (clear + argu) / n:.1f}% "
                  f"Wilson {wilson(clear + argu, n)}")
        print(f"  strict recall {clear}/{pos_c}   inclusive recall {clear + argu}/{pos_i}")
        fps = [(r["id"], x.get("why")) for r, x in flagged if lbl(r) not in ("clear", "arguable")]
        for i, w in fps:
            print(f"    FP {i}: {w}")
        # fixture
        fx = [(lab[("fixture", i)], res[(arm, "fixture", i)]) for (ar, s, i) in res if ar == arm and s == "fixture"]
        tp = sum(1 for r, x in fx if r["label"] == 1 and x.get("verdict") is True)
        fn = sum(1 for r, x in fx if r["label"] == 1 and x.get("verdict") is not True)
        fp = sum(1 for r, x in fx if r["label"] == 0 and x.get("verdict") is True)
        tn = sum(1 for r, x in fx if r["label"] == 0 and x.get("verdict") is not True)
        print(f"fixture (15 scored) TP/FP/TN/FN = {tp}/{fp}/{tn}/{fn}")
        am = [(lab[("agreed_missed", i)], res[(arm, "agreed_missed", i)]) for (ar, s, i) in res
              if ar == arm and s == "agreed_missed"]
        print(f"JUDGE_1-missed positives caught solo: {sum(1 for _, x in am if x.get('verdict') is True)}/{len(am)}")
        secs = [x["secs"] for _, x in sp if "secs" in x]
        if secs:
            print(f"latency mean {sum(secs) / len(secs):.1f}s max {max(secs)}s over {len(secs)} split calls")
    if set(arms) >= {"v1", "v2"}:
        ids = [k[2] for k in res if k[0] == "v1" and k[1] == "split"]
        flips = [(i, res[("v1", "split", i)].get("verdict"), res[("v2", "split", i)].get("verdict"),
                  lab[("split", i)]["label"]) for i in ids
                 if res.get(("v2", "split", i)) and
                 res[("v1", "split", i)].get("verdict") != res[("v2", "split", i)].get("verdict")]
        print(f"===== v1->v2 split flips: {len(flips)} =====")
        for f in flips:
            print("   ", f)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score", "show-prompts"])
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--extra")
    ap.add_argument("--arms", default="v1,v2")
    ap.add_argument("--base", default="http://127.0.0.1:11439")
    ap.add_argument("--model", default="gemma4:12b")
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a)
    elif a.cmd == "score":
        cmd_score(a)
    else:
        print("V1:\n" + production_prompt() + "\n\nV2:\n" + V2)


if __name__ == "__main__":
    main()
