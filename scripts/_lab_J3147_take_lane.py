"""J-3147 / D-0539 lab: measure the Emissary take on a candidate hub and replay real inputs.

Posts the CURRENT take prompt (core.left_lane._take_system + _clean_take) to one hub, one request at a time,
and writes per-sample latency, the raw model output and the cleaned take. Read-only against live data: the replay
inputs are a JSON file you pass in ({"human":[{cycle_id,raw_input,old_take}], "internal":[...]}), extracted from
data/training/reflection.jsonl; nothing is written under data/. Run from the worktree.

  python scripts/_lab_J3147_take_lane.py --url http://127.0.0.1:11440 --model falcon3:7b \
      --inputs <replay.json> --out <results.json> --human 8 --internal 7 [--seed 7]

Does not touch Ramses unless you point --url there (do not, without a reason: it is the founder's gaming machine).
"""
import argparse
import json
import random
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core import left_lane as LL  # noqa: E402  (core BEFORE anything else, per the lab rules)


def post(url: str, payload: dict, timeout: int) -> tuple[dict | None, float, str]:
    t0 = time.monotonic()
    req = urllib.request.Request(f"{url}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data, time.monotonic() - t0, ""
    except Exception as exc:  # noqa: BLE001
        return None, time.monotonic() - t0, repr(exc)[:120]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--human", type=int, default=8)
    ap.add_argument("--internal", type=int, default=7)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--max-tokens", type=int, default=LL.TAKE_MAX_TOKENS)
    ap.add_argument("--warm", action="store_true", help="one throwaway call first so the model is resident")
    ap.add_argument("--v1", action="store_true", help="baseline: the pre-D-0539 constitution prompt and no cleaning")
    a = ap.parse_args()
    if a.v1:
        LL.TAKE_V2 = False
        # the baseline needs the REAL constitution; a worktree has no data/ (gitignored) so read it from the live tree, read-only
        from core import emissary
        live = Path(r"C:/Nascence/data/identity/emissary_axiom.json")
        if live.exists():
            emissary._AXIOM_PATH = live
            emissary._cache = None

    src = json.loads(Path(a.inputs).read_text(encoding="utf-8"))
    rnd = random.Random(a.seed)
    items = []
    for it, n in (("human", a.human), ("internal", a.internal)):
        pool = list(src.get(it, []))
        rnd.shuffle(pool)
        items += [(it, r) for r in pool[:n]] if n >= 0 else []
    if a.human == 0 and a.internal == 0:
        return
    if a.warm:
        post(a.url, {"model": a.model, "stream": False, "messages": [{"role": "user", "content": "ok"}],
                     "options": {"num_predict": 2}}, a.timeout)

    out = []
    for it, r in items:
        raw = r["raw_input"]
        payload = {"model": a.model, "stream": False,
                   "messages": [{"role": "system", "content": LL._take_system(it)},
                                {"role": "user", "content": raw[:3000]}],
                   "options": {"temperature": 0.0, "num_predict": a.max_tokens}, "format": "json"}
        data, secs, err = post(a.url, payload, a.timeout)
        rec = {"input_type": it, "cycle_id": r.get("cycle_id"), "raw_input": raw[:300], "seconds": round(secs, 2),
               "error": err, "raw_take": None, "cleaned": None, "reasons": None, "old_take": r.get("old_take")}
        if data is not None:
            txt = (data.get("message") or {}).get("content") or ""
            rec["raw_take"] = txt
            try:
                t = json.loads(txt)
                if isinstance(t, dict) and t.get("literal_ask"):
                    c, why = (LL._clean_take(t, raw, it) if not a.v1 else (t, []))
                    rec["cleaned"], rec["reasons"] = c, why
            except Exception:  # noqa: BLE001
                rec["reasons"] = ["unparseable"]
        out.append(rec)
        print(f"[{it:8s}] {secs:6.1f}s  {'ERR ' + err if err else ''} "
              f"{(rec['cleaned'] or {}).get('literal_ask', rec['reasons'])}", flush=True)
    secs = sorted(x["seconds"] for x in out if not x["error"])
    summ = {"url": a.url, "model": a.model, "n": len(out), "errors": sum(1 for x in out if x["error"]),
            "p50": statistics.median(secs) if secs else None,
            "p90": secs[min(len(secs) - 1, int(0.9 * len(secs)))] if secs else None,
            "kept": sum(1 for x in out if x["cleaned"]),
            "filtered": sum(1 for x in out if x["raw_take"] and not x["cleaned"])}
    Path(a.out).write_text(json.dumps({"summary": summ, "samples": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ))


if __name__ == "__main__":
    main()
