"""
Hermetic test for J-2907 (F-3564, P-0044): the Follow Line return says how long ago he asked, not 'just now'.

No LLM, no embedder, no live data. Runs inside lab_env.isolate with every touched store redirected to the lab dir; the
return is built from hand-made typed cargo (no stops run). Checks:
  [1] _ago_phrase thresholds (just now < 5 min, a while ago < 1 h, some hours ago < 24 h, yesterday, N days ago)
  [2] _origin_phrase: asked ages with `now`, keeps ", about X"; no timestamp -> 'asked earlier' (never 'just now');
      claim / consequence / study / dream phrases unchanged and carry no time claim
  [3] render(now=...) ages only the first sentence; the closing question is intact; no instruction to act
  [4] take_delivery re-renders at DELIVERY: a return rendered 'just now' and met 5 h later says 'some hours ago'
  [5] _expire attaches the aged text as the entry's finding (the fallback path)
Run:  python scripts/_test_J-2907_asked_age.py   (from the tree under test)
"""
from __future__ import annotations
import sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl
from core import frontier as fr
from core import coupling_rides as cr
from core import evidence_recall as ev
from core import satisfaction as sat
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate, _hash_file

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = Path(r"C:\Nascence\data")
CANARY = [LIVE / "frontier.json", LIVE / "logs" / "follow_line_shadow.jsonl", LIVE / "coupling_rides.jsonl"]
before = [_hash_file(p) for p in CANARY]
ALSO = [(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG"]), (cr, ["_LOG"]), (ev, ["_LOG"]), (sat, ["_LOG", "_STATE"])]
H = 3600.0

with isolate(also=ALSO, db="empty") as lab_dir:
    print(f"lab dir: {lab_dir}")
    fr.FRONTIER_SEMANTIC_MERGE = None
    cr._DATA = lab_dir

    print("[1] _ago_phrase")
    check("0 s and 299 s -> just now", fl._ago_phrase(0) == "just now" and fl._ago_phrase(299) == "just now")
    check("300 s .. 3599 s -> a while ago", fl._ago_phrase(300) == "a while ago" and fl._ago_phrase(3599) == "a while ago")
    check("1 h .. 23.9 h -> some hours ago (the measured median 4.9 h lands here)",
          fl._ago_phrase(H) == "some hours ago" and fl._ago_phrase(4.9 * H) == "some hours ago" and fl._ago_phrase(23.9 * H) == "some hours ago")
    check("1 d -> yesterday; 3 d -> 3 days ago; negative/None age clamps to just now",
          fl._ago_phrase(86400) == "yesterday" and fl._ago_phrase(3 * 86400) == "3 days ago"
          and fl._ago_phrase(-50) == "just now" and fl._ago_phrase(None) == "just now")

    print("[2] _origin_phrase")
    t0 = 1_000_000.0
    ent = {"source": "asked", "about": "Portuguese integration", "asked_by": {"ts": t0}, "born": t0}
    check("asked 10 s ago keeps 'just now' and the about clause", fl._origin_phrase(ent, t0 + 10) == "asked just now, about Portuguese integration")
    check("asked 5 h ago -> 'some hours ago', about kept", fl._origin_phrase(ent, t0 + 5 * H) == "asked some hours ago, about Portuguese integration")
    check("no about -> no trailing clause", fl._origin_phrase({"source": "asked", "asked_by": {"ts": t0}}, t0 + 30 * 60) == "asked a while ago")
    check("asked_by.ts missing -> falls back to born", fl._origin_phrase({"source": "asked", "born": t0}, t0 + 2 * H) == "asked some hours ago")
    check("no timestamp at all -> 'asked earlier', never 'just now'",
          fl._origin_phrase({"source": "asked", "about": "x"}, t0) == "asked earlier, about x" and "just now" not in fl._origin_phrase({"source": "asked"}, t0))
    check("claim / study / dream / consequence / intention phrases unchanged, no time claim",
          fl._origin_phrase({"source": "claim", "asked_by": {"book_title": "B"}}, t0) == "held after reading 'B'"
          and fl._origin_phrase({"source": "study", "asked_by": {"book_title": "B"}}, t0) == "wondered while reading 'B'"
          and fl._origin_phrase({"source": "dream"}, t0) == "wondered in a dream"
          and fl._origin_phrase({"source": "consequence"}, t0) == "found would have to follow from something you hold"
          and fl._origin_phrase({"source": "intention"}, t0) == "meant to find out")
    check("default now = the clock: an entry asked a moment ago says just now",
          fl._origin_phrase({"source": "asked", "asked_by": {"ts": time.time() - 3}}) == "asked just now")

    print("[3] render(now=...)")
    cargo = {"grounds": [{"origin": "reading", "age": "a month ago", "text": "Albuquerque ordered soldiers to marry local women."}],
             "grounds_outcome": "found", "why": {}, "consequences": [], "connections": {}, "against": {}, "own_test": {}, "status": "undetermined"}
    judged = {"a": "yes", "b": "no", "c": "no"}
    ent2 = {"id": "q_t", "q": "how did the Portuguese blend cultures?", "source": "asked", "kind": "question", "slot": "how",
            "about": "Goa", "asked_by": {"ts": t0}, "born": t0}
    r_now, r_late = fl.render(ent2, cargo, judged, now=t0 + 5), fl.render(ent2, cargo, judged, now=t0 + 5 * H)
    check("fresh render says just now", r_now.startswith('Something you asked just now, about Goa: "how did'))
    check("5 h later says some hours ago", r_late.startswith('Something you asked some hours ago, about Goa: "how did') and "just now" not in r_late)
    check("only the first sentence differs; the closing question is intact",
          r_now.split(": ", 1)[1] == r_late.split(": ", 1)[1] and r_late.endswith(fl.RETURN_CLOSING))
    check("no instruction to act", "you could" not in r_late.lower() and "you should" not in r_late.lower())
    check("render() with no now argument still works (back-compat)", fl.render(ent2, cargo, judged).startswith("Something you asked"))

    print("[4] take_delivery re-renders at delivery")
    fl.FOLLOW_LINE = "live"
    fl._PENDING.clear(); fl._DELIVERED.clear(); fr._save({"questions": []})
    e = fr.note_question_ex("how did the Portuguese truly blend cultures, and what scars or gifts remained?", "asked", slot="how",
                            about="Goa", asked_by={"train_id": "t_x", "ts": time.time() - 5 * H}, allow_self=True)
    ent_live = fr.get(e["id"])
    stale = fl.render(ent_live, cargo, judged, now=time.time() - 5 * H + 20)        # rendered when the line finished, 20 s after asking
    check("the stale text said 'just now'", "asked just now" in stale)
    fl._place_pending(e["id"], stale, ent_live, cargo, judged)
    check("placed", fl.pending_count() == 1)
    d = fl.take_delivery()
    check("delivered text says 'some hours ago', not 'just now'", d is not None and "asked some hours ago, about Goa" in d["text"] and "just now" not in d["text"])
    check("delivered text still ends with the closing question", d["text"].endswith(fl.RETURN_CLOSING))
    check("the kept delivered record carries the aged text", fl._DELIVERED[e["id"]]["text"] == d["text"])

    print("[5] _expire attaches the aged text")
    e2 = fr.note_question_ex("what did the Portuguese leave behind in Goa that still stands?", "asked", slot="what",
                             about="Goa", asked_by={"train_id": "t_y", "ts": time.time() - 3 * H}, allow_self=True)
    ent2l = fr.get(e2["id"])
    fl._place_pending(e2["id"], fl.render(ent2l, cargo, judged, now=time.time() - 3 * H + 5), ent2l, cargo, judged)
    fl._expire(e2["id"], "ttl")
    got = fr.get(e2["id"])
    blob = str(got)
    check("expired finding carries 'some hours ago', no 'just now'", "asked some hours ago" in blob and "asked just now" not in blob)

after = [_hash_file(p) for p in CANARY]
check("live stores untouched", before == after)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
