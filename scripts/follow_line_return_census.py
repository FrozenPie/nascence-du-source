"""
Follow Line return census (J-2911; the read side of F-3593 / F-3594 / F-3595). READ-ONLY over a follow_line_shadow.jsonl.

Counts, over the would_return rows (optionally only those at/after --since, a unix ts, e.g. the restart time):
  grounded_a_no_holds_little  rows with grounds + judged.a == no whose text says "Your past holds little"  (F-3593; want 0 after J-2911)
  not_settled_label           rows that say "What you found did not settle it."                              (the J-2911 label)
  at_cap                      rows with len(text) >= 1200                                                  (F-3594: 84/175 before)
  no_closing_question         rows whose text does not end with the closing question                        (F-3594: 84/175 before)
  touch_dirty                 rows whose "It touches:" tail carries '[', "Q: ", "time(s)" or "Travis said"   (F-3595: 105/137 before)
Run:  python scripts/follow_line_return_census.py [--log PATH] [--since TS]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CLOSE = "Does it hold, or only part of it?"
CAP = 1200


def census(log: Path, since: float = 0.0) -> dict:
    out = {"rows": 0, "grounded_a_no_holds_little": 0, "not_settled_label": 0, "at_cap": 0, "no_closing_question": 0,
           "with_touch": 0, "touch_dirty": 0}
    if not log.exists():
        return out
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("kind") != "would_return" or float(r.get("ts", 0) or 0) < since:
            continue
        t = r.get("return_text") or ""
        out["rows"] += 1
        grounds = (r.get("cargo") or {}).get("grounds") or []
        if grounds and (r.get("judged") or {}).get("a") == "no" and "Your past holds little" in t:
            out["grounded_a_no_holds_little"] += 1
        if "What you found did not settle it." in t:
            out["not_settled_label"] += 1
        if len(t) >= CAP:
            out["at_cap"] += 1
        if not t.endswith(CLOSE):
            out["no_closing_question"] += 1
        if "It touches:" in t:
            out["with_touch"] += 1
            tail = t.split("It touches:", 1)[1]
            if "[" in tail or "Q: " in tail or "time(s)" in tail or "Travis said" in tail:
                out["touch_dirty"] += 1
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "logs" / "follow_line_shadow.jsonl"))
    ap.add_argument("--since", type=float, default=0.0)
    a = ap.parse_args()
    print(json.dumps(census(Path(a.log), a.since), indent=2))
