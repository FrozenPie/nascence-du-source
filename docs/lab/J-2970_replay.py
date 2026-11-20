"""J-2970 replay: run the control battery through the three panel hubs, read-only, no core import.
Payload is byte-equivalent to core.judge_panel._ask: model 'judge', stream False, format json, temp 0.0, num_predict 200,
system = _JUDGE_C_SYS / _JUDGE_B_SYS extracted unchanged from core/follow_line.py by AST (nothing under core/ imported,
so no telemetry / judge_panel_log / DB path can be touched). User text = the exact f-string of follow_line._judge.
Hubs: mixtral :11438 and granite :11437 on Ramses LAN-HOST, falcon3 :11440 local. Resumable; one thread per hub,
requests sequential within a hub. Variant 'q' rewrites the leading 'CLAIM:' to 'QUESTION:' on question-form items."""
import ast, json, sys, time, threading, urllib.request, urllib.error
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Nascence")
OUT = ROOT / "docs" / "lab" / "J-2970_calls.jsonl"
HUBS = {"mixtral": "http://LAN-HOST:11438", "falcon3": "http://127.0.0.1:11445", "granite": "http://LAN-HOST:11437"}


def sysprompts():
    tree = ast.parse((ROOT / "core" / "follow_line.py").read_text(encoding="utf-8"))
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("_JUDGE_C_SYS", "_JUDGE_B_SYS"):
            out[n.targets[0].id] = ast.literal_eval(n.value)
    return out


def user_c(d, label="CLAIM"):
    return (f"{label}: {d['claim']}\n\nGROUNDS:\n" +
            "\n".join(f"[{i}] ({o}) {t}" for i, (o, t) in enumerate(d["grounds"], 1)) +
            f"\n\nOBJECTION: {d['objection']}" + (f"\nSCOPE: {d['scope']}" if d.get("scope") else ""))


def user_b(d, label="CLAIM"):
    return f"{label}: {d['claim']}\n\nCONSEQUENCES:\n" + "\n".join(f"[{i}] {c}" for i, c in enumerate(d["cons"], 1))


def ask(url, system, user, key, timeout=300):
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get(key), bool):
            return v[key], None, round(time.monotonic() - t0, 2)
        return None, "parse", round(time.monotonic() - t0, 2)
    except Exception as e:
        return None, type(e).__name__, round(time.monotonic() - t0, 2)


def main():
    SP = sysprompts()
    bat = json.loads((ROOT / "docs" / "lab" / "J-2970_battery.json").read_text(encoding="utf-8"))
    jobs = []   # (item_id, key, system, user, variant)
    for d in bat["cuts"]:
        jobs.append((d["id"], "cuts", SP["_JUDGE_C_SYS"], user_c(d), "base"))
        if d["claim"].rstrip().endswith("?"):
            jobs.append((d["id"], "cuts", SP["_JUDGE_C_SYS"], user_c(d, "QUESTION"), "q"))
    for d in bat["follows"]:
        jobs.append((d["id"], "follows", SP["_JUDGE_B_SYS"], user_b(d), "base"))
        if d["claim"].rstrip().endswith("?"):
            jobs.append((d["id"], "follows", SP["_JUDGE_B_SYS"], user_b(d, "QUESTION"), "q"))
    # priority order so a partial run is still balanced: base calls first, round-robin across classes (hand-written first),
    # label-variant ('q') calls last
    cls_of = {d["id"]: d["cls"] for d in bat["cuts"] + bat["follows"]}
    seen_n = {}
    rank = {}
    for j in jobs:
        if j[4] == "base":
            k = cls_of[j[0]]
            seen_n[k] = seen_n.get(k, 0) + 1
            rank[(j[0], j[4])] = seen_n[k]
    pri = {"hand_counterexample": 0, "hand_vacuous": 0, "hand_checkable": 0, "substantive_real": 1, "concession": 1, "restatement": 1,
           "boilerplate": 1, "non_sequitur": 1, "hedge": 1, "non_addressing": 2}
    jobs.sort(key=lambda j: (j[4] != "base", rank.get((j[0], j[4]), 0), pri.get(cls_of[j[0]], 1)))
    done = set()
    if OUT.exists():
        for l in OUT.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("verdict") is not None:
                    done.add((r["hub"], r["id"], r["variant"]))
    lock = threading.Lock()
    print("jobs per hub", len(jobs), "already done", len(done), flush=True)

    def worker(hub):
        for (iid, key, system, user, var) in jobs:
            if (hub, iid, var) in done:
                continue
            for attempt in (1, 2):
                v, err, secs = ask(HUBS[hub], system, user, key)
                if v is not None or attempt == 2:
                    break
                time.sleep(10)
            with lock:
                with open(OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(dict(hub=hub, id=iid, key=key, variant=var, verdict=v, err=err, secs=secs, attempt=attempt)) + "\n")

    ts = [threading.Thread(target=worker, args=(h,)) for h in HUBS]
    [t.start() for t in ts]
    [t.join() for t in ts]
    print("finished", flush=True)


if __name__ == "__main__":
    main()

