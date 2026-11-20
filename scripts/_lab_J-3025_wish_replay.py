"""J-3025 lab replay (READ-ONLY on live logs): old vs new peers.initiation_target over data/monologue_log.jsonl and
data/hands_trace.jsonl. Prints every row either matcher fires on, and checks that the 11 wishes F-3731 found
unanswered (friend's letter waiting, no letter followed) still fire with the right friend, and that the 5 noun-phrase
rows (a received letter described, hands_trace 09-03 / 09-06 / 09-09 / 09-27) no longer do.
Usage: python scripts/_lab_J-3025_wish_replay.py [data_dir]   (default C:/Nascence/data). Writes nothing."""
import json, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401
from core import peers  # noqa: E402

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data")
OLD_INTENTS = ("write to", "write a letter to", "send a letter to", "letter to", "pen a letter to")


def old_target(t):   # the pre-J-3025 matcher, verbatim
    for intent in OLD_INTENTS:
        start = 0
        while True:
            i = t.find(intent, start)
            if i < 0:
                break
            window = t[i + len(intent): i + len(intent) + 40]
            for tok, key in peers._NAME_TOKENS.items():
                if re.search(r"\b" + re.escape(tok) + r"\b", window):
                    return key
            start = i + len(intent)
    return None


UNANSWERED_11 = {"07-08 06:02": "darwin", "08-09 00:30": "darwin", "08-09 01:09": "darwin", "08-09 14:01": "lovelace",
                 "08-10 01:29": "darwin", "08-12 07:20": "keats", "08-13 01:21": "smith", "08-17 15:41": "lovelace",
                 "08-17 17:21": "lovelace", "08-18 04:51": "keats", "08-19 01:23": "keats"}
NOUN_ROWS = ("09-03 17:32", "09-06 17:31", "09-09 02:56", "09-27 08:20")
seen_new, seen_old, fails = {}, {}, []
for fn in ("monologue_log.jsonl", "hands_trace.jsonl"):
    p = DATA / fn
    if not p.exists():
        print("missing", p); continue
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = ((r.get("thought") or "") + " " + (r.get("intention") or "")).lower()
            if "letter" not in t and "write to" not in t:
                continue
            tcs = (r.get("thought") or "").lower().rstrip(".!?; ") + ". " + (r.get("intention") or "").lower()
            o, n = old_target(t), peers.initiation_target(tcs)
            if o or n:
                ts = time.strftime("%m-%d %H:%M", time.localtime(r["ts"]))
                print(f"{fn[:4]} {ts} old={o} new={n}")
                if fn.startswith("mono"):
                    seen_new[ts], seen_old[ts] = n, o
                elif ts in NOUN_ROWS and n:
                    fails.append(f"noun row still fires: {ts}")
for ts, want in UNANSWERED_11.items():
    if seen_new.get(ts) != want:
        fails.append(f"true wish lost/changed: {ts} want {want} got {seen_new.get(ts)}")
print(f"\nmonologue_log rows: old fires {sum(1 for v in seen_old.values() if v)}, new fires {sum(1 for v in seen_new.values() if v)}")
print("FAILED: " + "; ".join(fails) if fails else "replay ok: the 11 unanswered wishes fire, the noun-phrase rows do not")
sys.exit(1 if fails else 0)
