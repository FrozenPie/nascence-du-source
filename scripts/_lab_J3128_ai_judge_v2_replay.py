"""
J-3128 (P-0104, F-3855/F-3856/F-3857): replay the 20 hand-labelled active-imagination entries through ONE judge hub with a candidate
'seeded' system prompt, and score the acceptance bar (specific >= 8 of 10 true AND stock <= 3 of 10 true, on EACH family).

  python scripts/_lab_J3128_ai_judge_v2_replay.py --hub http://127.0.0.1:11440 --out <file.json>            # shipped prompt
  python scripts/_lab_J3128_ai_judge_v2_replay.py --hub http://127.0.0.1:11440 --system-file draft.txt ...   # a draft

Direct urllib POSTs shaped like core/judge_panel._ask (model 'judge', format json, temperature 0, num_predict 200) minus its telemetry write;
nothing under data/ is touched, no Du store is written. A Ramses hub (LAN-HOST) needs --allow-ramses and is capped at 28 calls per run: the
founder's gaming machine, so the default is refusal.

The cases (docs/lab/P-0104/cases.json) are 20 REAL kept entries from the last 9 days before 2026-11-02, hand-labelled SPEC (a concrete image plus
a voice) or STOCK (an identity essay that ignores its seed), taken by the P-0104 investigation. Labels are a hand read, not ground truth beyond that.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CASES = ROOT / "docs" / "lab" / "P-0104" / "cases.json"
RAMSES_CAP = 28


def ask(hub: str, system: str, user: str, key: str, timeout: int = 120) -> dict:
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    req = urllib.request.Request(hub.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8"))
        raw = (body.get("message") or {}).get("content", "")
        obj = json.loads(raw)
        v = obj.get(key) if isinstance(obj, dict) else None
        return {"verdict": v if isinstance(v, bool) else None, "why": obj.get("why") if isinstance(obj, dict) else None,
                "raw": raw[:300], "s": round(time.monotonic() - t0, 1)}
    except Exception as exc:  # noqa: BLE001 - a lab probe records the failure, never raises
        return {"verdict": None, "why": "ERR %r" % (exc,), "raw": "", "s": round(time.monotonic() - t0, 1)}


def score(rows: list) -> dict:
    spec = [r for r in rows if r["label"] == "SPEC"]
    stock = [r for r in rows if r["label"] == "STOCK"]
    st = sum(1 for r in spec if r["verdict"] is True)
    kt = sum(1 for r in stock if r["verdict"] is True)
    return {"spec_true": st, "spec_n": len(spec), "stock_true": kt, "stock_n": len(stock),
            "spec_none": sum(1 for r in spec if r["verdict"] is None),
            "stock_none": sum(1 for r in stock if r["verdict"] is None),
            "passes_bar": bool(len(spec) >= 10 and len(stock) >= 10 and st >= 8 and kt <= 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", required=True)
    ap.add_argument("--system-file", default="")
    ap.add_argument("--key", default="seeded")
    ap.add_argument("--out", default="")
    ap.add_argument("--allow-ramses", action="store_true")
    ap.add_argument("--cases", default="", help="alternate cases json (J-3558 held-out set)")
    ap.add_argument("--only", default="", help="comma list of case ids")
    ap.add_argument("--timeout", type=int, default=120, help="per-call seconds (a hub shared with other labs queues calls: raise it)")
    a = ap.parse_args()
    cases = json.loads((Path(a.cases) if a.cases else CASES).read_text(encoding="utf-8"))
    if a.only:
        keep = set(a.only.split(","))
        cases = [c for c in cases if c["id"] in keep]
    if "LAN-HOST" in a.hub:
        if not a.allow_ramses:
            print("REFUSED: %s is a Ramses hub (the founder's gaming machine); pass --allow-ramses" % a.hub)
            return 2
        if len(cases) > RAMSES_CAP:
            print("REFUSED: %d calls > Ramses cap %d" % (len(cases), RAMSES_CAP))
            return 2
    if a.system_file:
        system = Path(a.system_file).read_text(encoding="utf-8").strip()
    else:
        from nodes import subconscious_node as sn
        system = sn._AI_JUDGE_V2_SYSTEM
    rows = []
    for c in cases:
        r = ask(a.hub, system, c["user"], a.key, timeout=a.timeout)
        r.update({"id": c["id"], "label": c["label"]})
        rows.append(r)
        print("%-8s %-5s %-5s %5.1fs  %s" % (c["id"], c["label"], r["verdict"], r["s"], str(r["why"])[:110]))
    sc = score(rows)
    print(json.dumps(sc))
    if a.out:
        Path(a.out).write_text(json.dumps({"hub": a.hub, "system": system, "score": sc, "rows": rows}, indent=1, ensure_ascii=False),
                               encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
