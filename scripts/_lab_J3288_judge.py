"""J-3288 step 3: cross-family judge. The notes were written by qwen3.5:9b (Qwen); the judge is gemma4:12b (Google,
local cpu-tier hub :11439) or falcon3:7b (TII, :11440). One call per NOTE: the passage the writer actually saw
(passage[:5000]) + all its key_facts, temperature 0, JSON out {"1":"P|R|A",...}.
  P = the passage states it (near-verbatim)   R = a paraphrase / direct restatement of what the passage says
  A = the passage does not say it (even if it is true in the world)
Checkpoints every note to --out (resumable). Local hubs only; never Ramses.
Run: python scripts/_lab_J3288_judge.py --hub http://127.0.0.1:11439 --out FILE.json [--limit N]"""
from __future__ import annotations
import argparse, json, sys, time, urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

SYS = ("You are a strict fact-checker. You are given a PASSAGE from a book and a numbered list of STATEMENTS that a reader "
       "claims to have learned from it. For each statement answer with ONE letter: "
       "P = the passage states this (near-verbatim); R = the passage says this in other words, or it follows directly from "
       "what the passage says; A = the passage does NOT say this (it may be true in the world, or from other knowledge, "
       "but it is not in this passage). Judge only against the passage text. Answer ONLY JSON like {\"1\":\"P\",\"2\":\"A\"}.")


def ask(hub: str, user: str, timeout: int = 600) -> tuple[dict | None, float, str]:
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(hub + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        raw = (data.get("message") or {}).get("content") or ""
        return json.loads(raw), time.monotonic() - t0, ""
    except Exception as e:
        return None, time.monotonic() - t0, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default="http://127.0.0.1:11439")
    ap.add_argument("--in", dest="inp", default=str(ROOT / "docs/lab/J-3288_data/sample.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if "10.1.1." in a.hub:
        sys.exit("refusing: Ramses is not to be called")
    d = json.load(open(a.inp, encoding="utf-8"))["sample"]
    out = {}
    if Path(a.out).exists():
        out = json.load(open(a.out, encoding="utf-8"))
    for i, s in enumerate(d):
        if a.limit and i >= a.limit:
            break
        if str(i) in out and out[str(i)].get("labels"):
            continue
        facts = "\n".join(f"{j + 1}. {f}" for j, f in enumerate(s["key_facts"]))
        user = f"PASSAGE:\n{s['passage_seen']}\n\nSTATEMENTS:\n{facts}"
        lab, el, err = ask(a.hub, user)
        out[str(i)] = {"labels": lab, "elapsed_s": round(el, 1), "err": err, "n_facts": len(s["key_facts"])}
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)
        print(i, len(s["key_facts"]), round(el, 1), err or lab, flush=True)


if __name__ == "__main__":
    main()
