"""
J-3079 (F-3790) replay: run the pole gate's CURRENT _SELF_CLASH_SYS (this tree) over the 4 gate-forked near-identical pairs
and the positive control from F-3790, 2 runs each, and print fork / no-fork next to the recorded BEFORE (F-3790, old
pre-filled schema line, same model/options).

  python scripts/lab_J-3079_pole_gate_replay.py [--url http://LAN-HOST:11441/api/chat] [--model command-r7b] [--runs 2]

This calls the BACKGROUND LANE (Ramses :11441 command-r7b by default): 5 pairs x runs calls. Ramses is the founder's gaming
machine -- run it when he is not playing. Read-only: touches no Du store (pairs come from scripts/lab_J-3079_pole_gate_pairs.json).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                      # noqa: E402,F401
from core import guidance_learning as G          # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://LAN-HOST:11441/api/chat")
ap.add_argument("--model", default="command-r7b")
ap.add_argument("--runs", type=int, default=2)
a = ap.parse_args()
pairs = json.loads((ROOT / "scripts" / "lab_J-3079_pole_gate_pairs.json").read_text(encoding="utf-8"))


def call(x, y):
    payload = {"model": a.model, "messages": [{"role": "system", "content": G._SELF_CLASH_SYS},
               {"role": "user", "content": f"A: \"{x[:400]}\"\n\nB: \"{y[:400]}\""}],
               "think": False, "stream": False, "format": "json",
               "options": {"temperature": 0.1, "num_predict": 150, "num_ctx": 4096}}
    req = urllib.request.Request(a.url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        txt = json.loads(r.read())["message"]["content"]
    try:
        d = json.loads(txt)
    except Exception:
        return {"raw": txt[:80], "enum_ok": False, "clash": False}
    p, q = str(d.get("a_pole", "")).strip().lower(), str(d.get("b_pole", "")).strip().lower()
    return {"a": p, "b": q, "enum_ok": p in G._POLES and q in G._POLES, "clash": {p, q} == {"fluid", "durable"}}


for pr in pairs:
    res = [call(pr["a"], pr["b"]) for _ in range(a.runs)]
    print(f"{pr['group']:30s} before={[c for _, _, c in pr['before']]} after={[r['clash'] for r in res]} "
          f"poles={[(r.get('a'), r.get('b')) for r in res]} enum_ok={[r['enum_ok'] for r in res]}\n    {pr['a'][:60]} | {pr['b'][:60]}")
