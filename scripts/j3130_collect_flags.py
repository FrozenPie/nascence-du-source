"""J-3130 step 1+2: collect the notice checker's flags (read-only on live data/lane2_shadow.jsonl) and build
the item set for the narrow said-vs-listed panel audit.  Writes only under docs/lab/J-3130_data/.
Window A = the post-10-29 18:30 NZDT boot window up to the F-3858 finding time (378 ticks, 43 flagged).
Window B = F-2730's window (10-07 20:03Z .. 10-14 21:50Z), random 60 of its flags (seed 3130).
Item = ONE checker flag with its clause widened to the full sentence of the logged notice."""
import json, re, random, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "lab" / "J-3130_data"
SHADOW = Path("C:/Nascence/data/lane2_shadow.jsonl")   # read-only


def _norm(s):
    return (s or "").replace("\u2019", "'").replace("\u2018", "'").lower()


def widen(notice, said):
    """Full sentence of `notice` containing `said` (original case); falls back to `said`."""
    n = _norm(notice)
    s = _norm(said).strip()
    i = n.find(s) if s else -1
    if i < 0 and len(s) > 12:
        i = n.find(s[:12])
    if i < 0:
        return said, False
    # sentence bounds on the normalised (same-length) text
    a = max(n.rfind(c, 0, i) for c in ".!?;")
    a = 0 if a < 0 else a + 1
    ends = [n.find(c, i + len(s)) for c in ".!?;"]
    ends = [e for e in ends if e >= 0]
    b = (min(ends) + 1) if ends else len(n)
    return notice[a:b].strip(), True


def main():
    rows = [json.loads(l) for l in SHADOW.open(encoding="utf-8") if l.strip()]
    ticks = [r for r in rows if r.get("kind") == "tick"]
    utc = dt.timezone.utc
    boot = dt.datetime(2026, 10, 29, 5, 30, tzinfo=utc).timestamp()
    cut = dt.datetime(2026, 11, 1, 19, 58, tzinfo=utc).timestamp()
    b0 = dt.datetime(2026, 10, 7, 20, 3, 9, tzinfo=utc).timestamp()
    b1 = dt.datetime(2026, 10, 14, 21, 50, 23, tzinfo=utc).timestamp()

    def flagged(t):
        return (t.get("notice_checked") or {}).get("verdict") == "contradiction"

    wa = [t for t in ticks if boot <= t["ts"] <= cut]
    wb = [t for t in ticks if b0 <= t["ts"] <= b1 and t.get("notice_checked") and t.get("notice")
          and t.get("percept_lines")]
    items = []

    def add(win, t, f):
        clause, found = widen(t["notice"], f["said"])
        items.append({"win": win, "ts": t["ts"], "kind": f["kind"], "weak": bool(f.get("weak")),
                      "said": f["said"], "listed": f["listed"], "clause": clause, "clause_found": found,
                      "notice": t["notice"], "percept_lines": t["percept_lines"],
                      "panel_judged": (t.get("notice_judged") or {}).get("verdict")})

    for t in wa:
        if flagged(t):
            for f in t["notice_checked"]["flags"]:
                add("A", t, f)
    na = len(items)
    pool = [(t, f) for t in wb if flagged(t) for f in t["notice_checked"]["flags"]]
    random.Random(3130).shuffle(pool)
    for t, f in pool[:60]:
        add("B", t, f)
    order = list(range(len(items)))
    random.Random(31300).shuffle(order)
    for rank, i in enumerate(order):
        items[i]["label_rank"] = rank
    for i, it in enumerate(items):
        it["id"] = i
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "items.json").write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    print("windowA ticks", len(wa), "flagged", sum(map(flagged, wa)), "flags", na,
          "weak", sum(1 for it in items[:na] if it["weak"]))
    print("windowB rows", len(wb), "flagged", sum(map(flagged, wb)), "flags in pool", len(pool))
    print("items", len(items), "clause_found", sum(it["clause_found"] for it in items))


if __name__ == "__main__":
    main()
