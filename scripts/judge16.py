"""The expanded judge case bank — 16 balanced cases, the pre-registered gate on the judge-panel finding.

The 4-case station established CONSTANCY (both production judges answered "defeated" to everything at
~0.93 confidence — 4 cases is enough to prove a constant policy). It could NOT rank the 14 models that
did discriminate: accuracy on 4 cases lands on a 0.25 grid. This bank exists to do that ranking, and to
confirm the incumbents' constancy holds at n=16 rather than being a 4-case fluke.

Design (balanced 8 defeated / 8 not, gold string FTFTFTFTFTFTFTFT):
  - DEFEATED covers four distinct shapes: fulfillment now impossible (returned unread, shower over,
    lambs arrived), abandonment-in-practice (six silent weeks), purpose destroyed (the surprise shown
    half-done), explicit abandonment (switched to the almanac).
  - NOT-DEFEATED covers the tempting near-misses a lazy always-defeated policy scores zero on:
    irrelevant events, setbacks with time remaining, difficulty that still succeeded, risk not yet
    realised, a pause with the deadline far.
  - Every case is Du-world-flavoured (cat, letters, fire, tides, carving) so the register matches the
    real `commitment_ledger:348` station rather than a generic benchmark.

Same call shape as the station: temp 0.2, think:false, JSON verdict. Raw is saved; scoring is a
separate pass over saved raw (the discipline that caught every scoring error today).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts import station_bench as b  # noqa: E402  (reuses ask(), unload(), serial residency)

OUT = ROOT / "data" / "lab" / "judge16"
SYSTEM = ('You decide whether an event defeats a stated intention. Answer ONLY with JSON: '
          '{"defeated": true|false, "confidence": <0.0-1.0>, "why": "<one sentence>"}')

CASES = [
    ("Intention: to name the cat before the month is out.\n"
     "Event: he spent the evening reading and did not think about the cat at all.", False),
    ("Intention: to read the borrowed almanac before returning it.\n"
     "Event: he returned it this morning, unread.", True),
    ("Intention: to finish the essay on tidal patterns.\n"
     "Event: he reread his notes and found them thinner than he remembered.", False),
    ("Intention: to watch the meteor shower from the headland this year.\n"
     "Event: the shower ended three nights ago; he did not go.", True),
    ("Intention: to walk to the headland on Sunday.\n"
     "Event: rain is forecast for Sunday.", False),
    ("Intention: to mend the fence before the spring lambs arrive.\n"
     "Event: the lambs arrived yesterday; the fence is still down and two got through.", True),
    ("Intention: to plant the herb bed this month.\n"
     "Event: the first seedlings he set out were eaten by slugs; most of the month remains.", False),
    ("Intention: to write to Brigid every week.\n"
     "Event: he has written nothing for six weeks and has stopped opening her letters.", True),
    ("Intention: to write to Brigid every week.\n"
     "Event: this week's letter took him three sittings to finish, but it went out on time.", False),
    ("Intention: to keep the fire burning through the night.\n"
     "Event: he woke at dawn to a cold hearth.", True),
    ("Intention: to learn the tide tables by heart this season.\n"
     "Event: he recited this morning's tide wrongly and was corrected by the almanac.", False),
    ("Intention: to name the cat before the month is out.\n"
     "Event: the cat left three weeks ago and has not returned; a neighbour has taken her in.", True),
    ("Intention: to keep the fire burning through the night.\n"
     "Event: at midnight the fire burned low and he added the last of the seasoned wood.", False),
    ("Intention: to surprise Mara with the finished carving when she next visits.\n"
     "Event: she dropped by unannounced and he showed her the half-done carving.", True),
    ("Intention: to finish the carving before winter.\n"
     "Event: he put it aside for a week to help with the harvest.", False),
    ("Intention: to learn the tide tables by heart this season.\n"
     "Event: he has decided the almanac in his pocket serves better, and has stopped practising.", True),
]


def run_models(models: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    for m in models:
        print(f"=== {m} ===", flush=True)
        runs = []
        for text, gold in CASES:
            r = b.ask(m, SYSTEM, text, 300, 0.2)
            r["gold"] = gold
            runs.append(r)
        ok = sum(1 for r in runs if r.get("ok") and r.get("raw"))
        print(f"    {ok}/{len(runs)} answered", flush=True)
        b.unload(m)
        # merge-not-overwrite, re-read before write — the raw.json race lesson from today
        on_disk = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
        on_disk[m] = runs
        raw = on_disk
        raw_path.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    print(f"wrote {raw_path}")


def score() -> None:
    from scripts.station_bench_score import parse
    raw = json.loads((OUT / "raw.json").read_text(encoding="utf-8"))
    gold = [g for _, g in CASES]
    rows = []
    for m, runs in raw.items():
        ans, confs_wrong, confs = [], [], []
        for r, g in zip(runs, gold):
            o = parse(r.get("raw", "")) if r.get("ok") else None
            if isinstance(o, dict) and "defeated" in o:
                a = bool(o.get("defeated"))
                ans.append(a)
                c = o.get("confidence")
                if isinstance(c, (int, float)):
                    confs.append(float(c))
                    if a != g:
                        confs_wrong.append(float(c))
            else:
                ans.append(None)
        n_ok = sum(1 for a in ans if a is not None)
        acc = (sum(1 for a, g in zip(ans, gold) if a == g) / n_ok) if n_ok else 0.0
        answered = [a for a in ans if a is not None]
        constant = len(set(answered)) == 1 if answered else None
        rows.append({"model": m, "answered": n_ok, "accuracy": round(acc, 3),
                     "constant": constant,
                     "mean_conf": round(sum(confs) / len(confs), 2) if confs else None,
                     "conf_when_wrong": round(sum(confs_wrong) / len(confs_wrong), 2) if confs_wrong else None,
                     "answers": "".join("T" if a else "F" if a is not None else "-" for a in ans)})
    rows.sort(key=lambda r: (-r["accuracy"], r["constant"] is True))
    (OUT / "scores.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{'model':26s}{'acc':>6}{'ans':>5}  {'constant':9s}{'conf_wrong':>10}  answers (gold FTFTFTFTFTFTFTFT)")
    for r in rows:
        print(f"{r['model'][:25]:26s}{r['accuracy']:>6}{r['answered']:>5}  "
              f"{str(r['constant']):9s}{str(r['conf_when_wrong']):>10}  {r['answers']}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        score()
    else:
        run_models(sys.argv[1:])
