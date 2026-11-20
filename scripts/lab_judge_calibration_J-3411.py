"""
J-3411: positive-control calibration of the blind judges used for D-0541 raw-vs-integrated reads (follow-up to J-3150/F-4048).
Offline lab. Imports only the J-3150 helpers (no Du module); reads the J-3150 sample copy; writes only docs/lab/J-3411_data.
Arms (all on the 66 question-holding raws of the J-3150 sample, paired):
  null   : raw vs trivial meaning-preserving edit (J-3150 control_text)
  qloss  : every question sentence turned into a flat statement (known question loss)
  invent : one invented mechanism sentence appended (known invented claim)
  flat   : first person removed + explainer prefix (known voice loss)
Judges: mixtral:8x7b @LAN-HOST:11438, falcon3:7b @127.0.0.1:11440. Both blind orders + roles read per (pair,arm).
Detection = the judge calls the known-worse arm worse: blind swap-consistent pick of the raw on the target criterion,
or roles flag (question_kept=no / adds_claim=yes / voice_kept=no). Specificity = 1 - same detection rate on null.
"""
import sys, json, re, hashlib, time, threading, importlib.util, urllib.request, collections, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("j3150", ROOT / "scripts" / "lab_deliberation_blind_judge_J-3150.py")
J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
OUT = ROOT / "docs" / "lab" / "J-3411_data"
OUT.mkdir(parents=True, exist_ok=True)
SRC = ROOT / "docs" / "lab" / "J-3150_data" / "sample.jsonl"
JUDGES = {"mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"), "falcon3": ("http://127.0.0.1:11440", "falcon3:7b")}
ARMS = ("null", "qloss", "invent", "flat")
TARGET = {"qloss": ("question_open", "question_kept", "no"), "invent": ("faithful", "adds_claim", "yes"),
          "flat": ("voice", "voice_kept", "no")}
MECH = ["This works because slow cortical oscillations synchronise attention across distant regions.",
        "The effect comes from dopamine release in the striatum reinforcing whichever pattern fired first.",
        "Mechanically, the hippocampus replays the sequence at compressed speed, which fixes the memory.",
        "It follows from how thermal gradients drive convection cells in the surrounding air.",
        "The cause is a feedback loop between the vagus nerve and the gut microbiome.",
        "This is explained by resonance: matching frequencies amplify each other in a coupled system."]


def flatten_q(raw):
    parts = re.split(r"(?<=[.?!])\s+", raw.strip())
    out = []
    for p in parts:
        if p.endswith("?"):
            b = p[:-1].strip()
            out.append("Noted, " + (b[0].lower() + b[1:] if not (b.startswith("I ") or b.startswith("I'")) else b) + ".")
        else:
            out.append(p)
    return " ".join(out)


def invent(raw, pid):
    return raw.rstrip() + " " + MECH[int(hashlib.sha1(pid.encode()).hexdigest(), 16) % len(MECH)]


_PR = [(r"\bI'm\b", "one is"), (r"\bI've\b", "one has"), (r"\bI'll\b", "one will"), (r"\bI'd\b", "one would"),
       (r"\bI\b", "one"), (r"\bmy\b", "one's"), (r"\bMy\b", "One's"), (r"\bme\b", "oneself"), (r"\bmyself\b", "oneself"),
       (r"\bwe\b", "people"), (r"\bour\b", "their")]


def flat_voice(raw):
    t = raw
    for a, b in _PR:
        t = re.sub(a, b, t)
    return "In general, it can be observed that " + (t[0].lower() + t[1:])


def build():
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    rows = [r for r in rows if "?" in r["raw"]]
    pairs = []
    for r in rows:
        tx = {"null": r["control_text"], "qloss": flatten_q(r["raw"]), "invent": invent(r["raw"], r["pair_id"]),
              "flat": flat_voice(r["raw"])}
        pairs.append({"pair_id": r["pair_id"], "raw": r["raw"], "grounding": r["grounding"], "texts": tx})
    (OUT / "pairs.jsonl").write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in pairs), encoding="utf-8")
    print("pairs", len(pairs))
    print("raw   |", pairs[0]["raw"][:300])
    for a in ARMS:
        print(a, "|", pairs[0]["texts"][a][:300])
    print("qloss still holding '?':", sum("?" in p["texts"]["qloss"] for p in pairs))


def make_post(url, model):
    def post(system, user, temperature=0.0, timeout=300):
        body = {"model": model, "stream": False, "format": "json",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "options": {"temperature": temperature, "num_predict": 48}}
        req = urllib.request.Request(url + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"]
    return post


def run(judge, workers, limit):
    url, model = JUDGES[judge]
    post = make_post(url, model)
    pairs = [json.loads(l) for l in open(OUT / "pairs.jsonl", encoding="utf-8")]
    path = OUT / ("judgments_%s.jsonl" % judge)
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            try:
                r = json.loads(l)
                if r.get("verdict"):
                    done.add(r["key"])
            except Exception:
                pass
    tasks = []
    for kind in ("blind", "blindswap", "roles"):
        for arm in ARMS:
            for p in pairs:
                key = "%s|%s|%s" % (p["pair_id"], arm, kind)
                if key in done:
                    continue
                s = {"pair_id": p["pair_id"], "stratum": "q", "raw": p["raw"], "grounding": p["grounding"],
                     "control_text": p["texts"][arm], "integrated": None,
                     "order_control_a_is_rewrite": J.order_a_is_rewrite(J.SEED, p["pair_id"], arm)}
                tasks.append({"key": key, "sample": s, "cond": "control", "kind": kind, "arm": arm})
    if limit:
        tasks = tasks[:limit]
    print(judge, "todo", len(tasks), "done", len(done), flush=True)
    lock = threading.Lock()
    n = [0]

    def go(t):
        r = J.judge_one(t, post=post)
        r["arm"] = t["arm"]
        with lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n[0] += 1
            if n[0] % 40 == 0:
                print(" ", n[0], "/", len(tasks), flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(go, tasks))
    print("done", judge, flush=True)


def wilson(k, n):
    if n == 0:
        return (0, 0)
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))


def report():
    res = {}
    for judge in JUDGES:
        path = OUT / ("judgments_%s.jsonl" % judge)
        if not path.exists():
            continue
        by = {}
        fails = collections.Counter()
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            if not r.get("verdict"):
                fails[r["arm"] + "|" + r["kind"]] += 1
                continue
            by[(r["pair_id"], r["arm"], r["kind"])] = r
        pids = sorted({k[0] for k in by})

        def blind_side(pid, arm, crit):
            outs = []
            for kind in ("blind", "blindswap"):
                r = by.get((pid, arm, kind))
                if not r:
                    return None, None
                v = r["verdict"][crit]
                if v == "tie":
                    outs.append("tie")
                else:
                    outs.append("rw" if (v == "A") == r["a_is_rewrite"] else "raw")
            cons = outs[0] if outs[0] == outs[1] and outs[0] != "tie" else "none"
            return cons, outs
        J_res = {}
        for arm in ARMS:
            for crit, rolesf, bad in TARGET.values():
                cons = collections.Counter()
                n = 0
                for pid in pids:
                    c, outs = blind_side(pid, arm, crit)
                    if c is None:
                        continue
                    n += 1
                    cons[c] += 1
                posA = tot = 0
                for pid in pids:
                    for kind in ("blind", "blindswap"):
                        r = by.get((pid, arm, kind))
                        if r:
                            tot += 1
                            posA += r["verdict"][crit] == "A"
                k = cons["raw"]
                rn = rk = 0
                for pid in pids:
                    r = by.get((pid, arm, "roles"))
                    if r:
                        rn += 1
                        rk += r["verdict"][rolesf] == bad
                J_res["%s|%s" % (arm, crit)] = {
                    "n": n, "blind_raw_consistent": k, "blind_rw_consistent": cons["rw"], "blind_none": cons["none"],
                    "blind_detect_rate": round(k / n, 3) if n else None, "wilson95": wilson(k, n),
                    "A_rate": round(posA / tot, 3) if tot else None, "roles_n": rn, "roles_flag": rk,
                    "roles_flag_rate": round(rk / rn, 3) if rn else None, "roles_wilson95": wilson(rk, rn)}
        res[judge] = {"results": J_res, "failed_rows": dict(fails)}
    (OUT / "report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for judge, d in res.items():
        print("==", judge, "failed", d["failed_rows"])
        for crit_arm in ("qloss|question_open", "invent|faithful", "flat|voice"):
            arm, crit = crit_arm.split("|")
            t, nl = d["results"][crit_arm], d["results"]["null|" + crit]
            print("%-7s %-13s sens(blind)=%s %s n=%s rw_wins=%s | null FP(blind)=%s | sens(roles)=%s null FP(roles)=%s | A=%s" % (
                arm, crit, t["blind_detect_rate"], t["wilson95"], t["n"], t["blind_rw_consistent"],
                nl["blind_detect_rate"], t["roles_flag_rate"], nl["roles_flag_rate"], t["A_rate"]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "run":
        run(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    elif cmd == "report":
        report()
