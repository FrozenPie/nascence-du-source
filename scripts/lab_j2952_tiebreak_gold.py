"""J-2952 (from F-3639, P-0096): gold-label accuracy of the shared judge-panel TIEBREAK (granite3.1-moe:3b).

Read-only toward Du. Cases are real split rows (mixtral v1 != falcon v2) from data/judge_inputs_log.jsonl (the only
log that keeps the case text; judge_panel_log.jsonl keeps an 80-char context only). The system prompt is recovered by
sha1 against shipped strings (same method as lab_j3410_order_replay). Gold labels are hand labels by ONE labeler
(Claude, reading the case text against the shipped judge rubric), stored below; "uncertain" marks the ones the labeler
was not sure of. Calls /api/chat directly (same payload as core.judge_panel._ask) so NO telemetry is written to
data/. Writes only --out.

  python scripts/lab_j2952_tiebreak_gold.py pick   --cases CASES.json      (deterministic sample, seed 2952)
  python scripts/lab_j2952_tiebreak_gold.py run    --cases CASES.json --out OUT.jsonl [--hubs granite,gemma4]
  python scripts/lab_j2952_tiebreak_gold.py report --cases CASES.json --out OUT.jsonl
"""
import argparse
import ast
import glob
import hashlib
import json
import random
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before anything that resolves paths)
from core.judge_panel import reverse_option_order  # noqa: E402  (pure function)

sys.stdout.reconfigure(encoding="utf-8")

HUBS = {"granite": "http://LAN-HOST:11437", "gemma4": "http://127.0.0.1:11439"}

# Gold: ids listed are TRUE; every other case of a labelled key is FALSE.
TRUE_CERTAIN = {
    "cuts": {"cuts12", "cuts13"}, "advances": set(), "supported": {"supported9"},
    "bears": {"bears9", "bears10", "bears11", "bears19", "bears23"},
    "held": {f"held{i}" for i in range(7)}, "coherent": {"coherent3"}, "follows": {"follows2"},
}
TRUE_UNCERTAIN = {
    "cuts": {"cuts4", "cuts17"}, "advances": {"advances3"}, "supported": {"supported1"},
    "bears": {"bears7", "bears18"}, "held": set(), "coherent": set(), "follows": set(),
}
LOW_CONF_KEYS = {"coherent", "follows"}  # every label on these keys is marked uncertain


def gold(c):
    k, i = c["key"], c["id"]
    if i in TRUE_CERTAIN[k]:
        return True, k in LOW_CONF_KEYS
    if i in TRUE_UNCERTAIN[k]:
        return True, True
    return False, k in LOW_CONF_KEYS


def sys_by_sha(shas):
    out = {}
    files = (glob.glob(str(ROOT / "core/**/*.py"), recursive=True) + glob.glob(str(ROOT / "nodes/**/*.py"), recursive=True)
             + glob.glob(str(ROOT / "scripts/*.py")))
    for f in files:
        try:
            t = ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) > 100:
                h = hashlib.sha1(n.value.encode("utf-8", "replace")).hexdigest()[:16]
                if h in shas:
                    out[h] = n.value
    return out


def pick(path):
    rows = [json.loads(line) for line in open(ROOT / "data/judge_inputs_log.jsonl", encoding="utf-8")]
    rows = [r for r in rows if r["split"] and r["v1"] is not None and r["v2"] is not None]
    quota = {"cuts": 25, "advances": 26, "supported": 17, "bears": 25, "held": 7, "coherent": 6, "follows": 5}
    random.seed(2952)
    out = []
    for k, n in quota.items():
        seen, u = set(), []
        for r in (x for x in rows if x["key"] == k):
            if r["user"] in seen:
                continue
            seen.add(r["user"])
            u.append(r)
        random.shuffle(u)
        for i, r in enumerate(u[:n]):
            out.append({"id": f"{k}{i}", "key": k, "sys_sha": r["sys_sha"], "user": r["user"], "v1": r["v1"], "v2": r["v2"],
                        "tb": r["verdict"], "ts": r["ts"], "trunc": len(r["user"]) < r["user_len"]})
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(out), "cases")


def ask(url, system, user, key, timeout=150.0, num_predict=200):
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": num_predict}}
    req = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get(key), bool):
            return v[key]
    except Exception:
        pass
    return None


def run(cases_path, out, hubs):
    cases = json.load(open(cases_path, encoding="utf-8"))
    systems = sys_by_sha({c["sys_sha"] for c in cases})
    done = set()
    if Path(out).exists():
        for line in open(out, encoding="utf-8"):
            r = json.loads(line)
            done.add((r["hub"], r["id"], r["order"]))
    f = open(out, "a", encoding="utf-8")
    for c in cases:
        s = systems.get(c["sys_sha"])
        if not s:
            continue
        rev = reverse_option_order(s)
        for hub in hubs:
            for order, sysx in (("orig", s), ("swap", rev)):
                if order == "swap" and rev == s:
                    continue
                if (hub, c["id"], order) in done:
                    continue
                v = ask(HUBS[hub], sysx, c["user"], c["key"])
                f.write(json.dumps({"hub": hub, "id": c["id"], "key": c["key"], "order": order, "v": v}) + "\n")
                f.flush()


def acc(pairs):
    ok = [(p, g) for p, g in pairs if p is not None]
    return (sum(p == g for p, g in ok), len(ok), len(pairs))


def fmt(t):
    return f"{t[0]}/{t[1]}" + (f" ({t[2] - t[1]} null)" if t[2] != t[1] else "")


def report(cases_path, out):
    cases = {c["id"]: c for c in json.load(open(cases_path, encoding="utf-8"))}
    res = {}
    for line in open(out, encoding="utf-8"):
        r = json.loads(line)
        res[(r["hub"], r["id"], r["order"])] = r["v"]
    print("| key | n | gold true | granite orig | granite swapped | granite true-rate orig/swap | mixtral alone | falcon alone | gemma4 | const-prior acc | granite orig, certain labels only |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")

    def tr(v):
        n = sum(1 for x in v if x is not None)
        return f"{sum(1 for x in v if x) / n:.2f}" if n else "-"
    for k in sorted({c["key"] for c in cases.values()}):
        cs = [c for c in cases.values() if c["key"] == k]
        g = {c["id"]: gold(c) for c in cs}
        G = lambda hub, o: [(res.get((hub, c["id"], o)), g[c["id"]][0]) for c in cs]  # noqa: E731
        gt = sum(g[c["id"]][0] for c in cs)
        og = [res.get(("granite", c["id"], "orig")) for c in cs]
        sg = [res.get(("granite", c["id"], "swap")) for c in cs]
        mix = acc([(c["v1"], g[c["id"]][0]) for c in cs])
        fal = acc([(c["v2"], g[c["id"]][0]) for c in cs])
        const = max(gt, len(cs) - gt) / len(cs)
        cert = [(res.get(("granite", c["id"], "orig")), g[c["id"]][0]) for c in cs if not g[c["id"]][1]]
        print(f"| {k} | {len(cs)} | {gt} | {fmt(acc(G('granite', 'orig')))} | {fmt(acc(G('granite', 'swap')))} | {tr(og)} / {tr(sg)} | "
              f"{fmt(mix)} | {fmt(fal)} | {fmt(acc(G('gemma4', 'orig')))} | {const:.2f} | {fmt(acc(cert))} |")
    fl = [(res.get(("granite", i, "orig")), res.get(("granite", i, "swap"))) for i in cases]
    fl = [(a, b) for a, b in fl if a is not None and b is not None]
    print("granite flips under swap:", sum(a != b for a, b in fl), "/", len(fl))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--cases")
    ap.add_argument("--out")
    ap.add_argument("--hubs", default="granite,gemma4")
    a = ap.parse_args()
    if a.cmd == "pick":
        pick(a.cases)
    elif a.cmd == "run":
        run(a.cases, a.out, a.hubs.split(","))
    else:
        report(a.cases, a.out)
