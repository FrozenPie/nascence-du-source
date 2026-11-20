"""J-2852 lab probe: why does think=true return EMPTY content on the qwen3.5:9b hot lane?

Replays ONE real Critic (and optionally Executive) prompt from a training-log row against the hot-lane ollama
(http://127.0.0.1:11433, 1080 Ti, local) with think on/off, format=json on/off, and a range of num_predict.
Reads message.thinking vs message.content, done_reason and eval_count. Writes ONLY a summary json to --out
(default: a temp dir). Touches no live data store. Run with Du DOWN (it loads the hot model).

  python scripts/_probe_J-2852_think_empty.py --out <dir> [--node critic|executive] [--only 0,3,5]
"""
from __future__ import annotations
import argparse, json, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401,E402  (core before lab_env)
from core import model_client as mc  # noqa: E402

BASE = "http://127.0.0.1:11433"
# (label, think, fmt_json, num_predict)
VARIANTS = [
    ("T0 think=F json   np=512",  False, True,  512),
    ("T1 think=T json   np=2048", True,  True,  2048),
    ("T2 think=T nojson np=2048", True,  False, 2048),
    ("T3 think=T json   np=4096", True,  True,  4096),
    ("T4 think=T nojson np=4096", True,  False, 4096),
    ("T5 think=T nojson np=1024", True,  False, 1024),
]


def last_row(node: str) -> dict:
    p = Path(r"C:/Nascence/data/training") / f"{node}.jsonl"   # read-only
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()[-40:] if l.strip()]
    rows = [r for r in rows if r.get("input_type") == "human"] or rows
    return rows[-1]


def call(system: str, user: str, think: bool, fmt_json: bool, np_: int, timeout: int = 300) -> dict:
    payload = {
        "model": mc._model_for(BASE),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "think": think, "stream": False,
        "options": {"temperature": 0.2, "num_predict": np_, "num_ctx": mc._num_ctx_for(BASE)},
        "keep_alive": "10m",
    }
    if fmt_json:
        payload["format"] = "json"
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    m = d.get("message") or {}
    content, thinking = m.get("content") or "", m.get("thinking") or ""
    try:
        mc.extract_json(content)
        parsed = True
    except Exception:
        parsed = False
    return {"secs": round(time.time() - t0, 1), "content_chars": len(content), "thinking_chars": len(thinking),
            "eval_count": d.get("eval_count"), "done_reason": d.get("done_reason"), "parsed_json": parsed,
            "content_head": content[:160], "thinking_tail": thinking[-160:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "J-2852_probe"))
    ap.add_argument("--node", default="critic")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    row = last_row(a.node)
    only = {int(x) for x in a.only.split(",") if x != ""}
    res = []
    for i, (label, think, fj, np_) in enumerate(VARIANTS):
        if only and i not in only:
            continue
        try:
            r = call(row["system_prompt"], row["user_prompt"], think, fj, np_)
        except Exception as exc:
            r = {"error": repr(exc)[:200]}
        r["variant"] = label
        res.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        (out / f"probe_{a.node}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
