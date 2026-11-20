"""J-2912 (F-3596 / F-3597 / F-3598, P-0044): replay the pre-J-2912 and the J-2912 follow_line generative prompts on the SAME
inputs and print the defect rates side by side.

Inputs: the last N distinct grounded would_return rows of follow_line_shadow.jsonl (read-only; cargo.grounds carries origin,
age and the first 120 chars of each ground). Both arms run the REAL stop code (_stop_why, _stop_consequences, _stop_against)
with fl.PROMPT_V2 and the prompt aliases switched, so parsing, clipping and labelling are exercised too.

  python scripts/_replay_J-2912_prompts.py --n 20 --url http://127.0.0.1:11433 --out <dir>

The production lane is command-r7b on Ramses :11441 (RAMSES IS THE FOUNDER'S GAMING MACHINE: not called by default). The default
URL is the local hot lane (qwen3.5:9b, ollama-native). Run with --url http://LAN-HOST:11441 later, when Ramses is free, to
reproduce on the production model. Writes ONLY the --out directory (a temp dir by default); the telemetry/guard paths are
isolated with lab_env. Live data is never written.
"""
from __future__ import annotations
import argparse, asyncio, json, re, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import follow_line as fl
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

LIVE_LOG = Path(r"C:\Nascence\data\logs\follow_line_shadow.jsonl")
_FIRST = re.compile(r"\b(I|my|me|I'm|I've)\b")
_THIRD_OPEN = re.compile(r"^\W*(The|These|This)\b")
_BOILER = re.compile(r"too broad|vague|oversimplif|lacks specificity|too abstract", re.I)
_CONCEDE = re.compile(r"is supported by|supported by the (grounds|study)|consistent with", re.I)
_W = re.compile(r"[a-z]{4,}")


def _words(t):
    return set(_W.findall((t or "").lower()))


def load_inputs(n, seed):
    import random
    rows, seen = [], set()
    for line in LIVE_LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        g = (r.get("cargo") or {}).get("grounds") or []
        if r.get("kind") == "would_return" and g and r.get("q") and r["q"] not in seen:
            seen.add(r["q"])
            rows.append({"q": r["q"], "grounds": [{"origin": x.get("origin", ""), "age": x.get("age", ""),
                                                   "text": x.get("text", "")} for x in g]})
    random.Random(seed).shuffle(rows)
    return rows[:n]


def set_arm(v2):
    fl.PROMPT_V2 = v2
    fl._WHY_SYS = fl._WHY_SYS_V2 if v2 else fl._WHY_SYS_V1
    fl._CONS_SYS = fl._CONS_SYS_V2 if v2 else fl._CONS_SYS_V1
    fl._AGAINST_SYS = fl._AGAINST_SYS_V2 if v2 else fl._AGAINST_SYS_V1


async def run_one(it):
    rec = {"q": it["q"], "n_grounds": len(it["grounds"])}
    for name, fn in (("why", lambda: fl._stop_why(it["q"], it["grounds"])),
                     ("against", lambda: fl._stop_against(it["q"], it["grounds"]))):
        try:
            rec[name] = await fn()
        except Exception as exc:
            rec[name] = {"text": "", "err": str(exc)[:100]}
    try:
        rec["cons"] = await fl._stop_consequences(it["q"], it["grounds"], rec.get("why") or {})
    except Exception as exc:
        rec["cons"] = []
        rec["cons_err"] = str(exc)[:100]
    return rec


async def run_both(inputs, url, arms=("old", "new")):
    """Old and new arm INTERLEAVED per input (so a busy lane hits both alike); progress printed per input."""
    fl.LINE_URLS = [url]
    res = {"old": [], "new": []}
    for i, it in enumerate(inputs, 1):
        for label, v2 in (("old", False), ("new", True)):
            if label not in arms:
                continue
            set_arm(v2)
            t0 = time.time()
            rec = await run_one(it)
            errs = [k for k in ("why", "against") if rec[k].get("err")] + (["cons"] if rec.get("cons_err") else [])
            res[label].append(rec)
            print(f"[{i}/{len(inputs)}] {label} {time.time() - t0:.0f}s errs={errs}", flush=True)
    return res


def metrics(recs):
    n = len(recs)
    why = [r["why"].get("text", "") for r in recs]
    wn = [t for t in why if t]
    cons = [(r["q"], r.get("why", {}).get("text", ""), c) for r in recs for c in r.get("cons", [])]
    ag = [r["against"] for r in recs]
    an = [a for a in ag if a.get("text")]
    m = {"n": n,
         "stop_errors": sum(bool(r["why"].get("err")) + bool(r["against"].get("err")) + bool(r.get("cons_err")) for r in recs),
         "why_first_person": sum(bool(_FIRST.search(t)) for t in wn), "why_n": len(wn),
         "why_third_open": sum(bool(_THIRD_OPEN.match(t)) for t in wn),
         "why_suggest": sum("suggest" in t.lower() for t in wn),
         "why_ge395": sum(len(t) >= 395 for t in wn),
         "why_cites_all": sum(1 for r in recs if r["why"].get("cites") and len(r["why"]["cites"]) == r["n_grounds"] and r["n_grounds"] >= 2),
         "why_with_2plus_grounds": sum(1 for r in recs if r["n_grounds"] >= 2),
         "cons_n": len(cons),
         "cons_restate_q": sum(1 for q, _w, c in cons if _words(q) and len(_words(q) & _words(c.get("text", ""))) / len(_words(q)) >= 0.6),
         "cons_in_why": sum(1 for q, w, c in cons if w and _words(c.get("text", "")) and len(_words(c.get("text", "")) & _words(w)) / len(_words(c.get("text", ""))) >= 0.7),
         "cons_slot_why": sum(1 for _q, _w, c in cons if c.get("slot") == "why"),
         "cons_slot_distinct": len({c.get("slot") for _q, _w, c in cons}),
         "against_nonempty": len(an), "against_empty": n - len(an),
         "against_boiler": sum(bool(_BOILER.search(a["text"])) for a in an),
         "against_uncited": sum(1 for a in an if not a.get("cites")),
         "against_concede": sum(bool(_CONCEDE.search(a["text"])) for a in an),
         "against_the_claim": sum(a["text"].lower().startswith("the claim") for a in an)}
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=44)
    ap.add_argument("--url", default="http://127.0.0.1:11433")
    ap.add_argument("--out", default="")
    ap.add_argument("--arms", default="old,new", help="old,new (default) or new: iterate on the J-2912 prompts only")
    a = ap.parse_args()
    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="J-2912_replay_"))
    out.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs(a.n, a.seed)
    print(f"inputs {len(inputs)} url {a.url} out {out}")
    res = {}
    with isolate(also=[(fl, ["SHADOW_LOG"])], db="empty"):
        res = asyncio.run(run_both(inputs, a.url, tuple(a.arms.split(","))))
        for label in ("old", "new"):
            if res[label]:
                (out / f"{label}.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in res[label]), encoding="utf-8")
    mo, mn = metrics(res["old"]), metrics(res["new"])
    print(f"{'metric':28s} {'old':>6s} {'new':>6s}")
    for k in mo:
        print(f"{k:28s} {mo[k]:>6} {mn[k]:>6}")
    (out / "metrics.json").write_text(json.dumps({"old": mo, "new": mn}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
