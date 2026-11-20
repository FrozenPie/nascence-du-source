"""J-3145 (D-0535): checks for Route 3, the contrary-target picker (core/peers.py).
  python scripts/_test_peers_contrary_J3145.py                      pure checks, zero LLM, zero writes (exit 1 on failure)
  python scripts/_test_peers_contrary_J3145.py --scan LOG.jsonl     run both matchers over every thought in a COPY of
                                                                    data/monologue_log.jsonl; print match counts + matches
  python scripts/_test_peers_contrary_J3145.py --replay LOG.jsonl [--n 40]
                                                                    N real question sentences from the log through the
                                                                    real contrary_target (hub :11439, NOT the hot lane);
                                                                    prints the pick spread. Writes only under this
                                                                    tree's data/ (isolate(db="empty"))."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core                                        # BEFORE lab_env: lab_env must not shadow this tree's core (F-2423)
assert str(Path(core.__file__).resolve()).lower().startswith(str(Path(__file__).resolve().parent.parent).lower()), core.__file__
from core import peers

EXTRACT = [  # (text, expected question or None)
    ("The rain settles. Is a river the same river twice? I let it go.", "Is a river the same river twice?"),
    ("Is the fire warm? Does a flame forget the log it came from?", "Does a flame forget the log it came from?"),
    ("The damp cold presses my chest, nothing more.", None),
    ("Why now?", None),                                   # under 4 words: not a question worth carrying
    ("A quiet urge stirs: to ask a friend how he saw nature's constant flow versus humanity's desire "
     "for fixed structures, or if he'd agree.", "how he saw nature's constant flow versus humanity's desire for fixed structures, or if he'd agree"),
    ("A quiet urge stirs: to ask Charles Darwin how he saw it.", None),     # a named friend is not the contrary route's
    ("", None),
]
WIDE = [  # (text, expected fire) -- question_to_friend_wide, flag-independent
    ("I want to write a letter to ask whether kindness needs a witness. Who would see this otherwise?", True),
    ("I want to ask my friends how they see this. Is a river the same river twice?", True),
    ("I would like to put this question to one of my friends. Is a river the same river twice?", True),   # the wide set repeats the original phrase
    ("I should write a letter to Travis to ask what he remembers. Is it the same as mine?", False),       # Travis: letters_to_travis owns it
    ("A quiet urge stirs: to ask Charles Darwin how he saw nature's constant flow, or if he'd agree.", False),  # a named friend is his own choice
    ("Do I turn inward to read, or find a way to write back to the friends who carry my questions?", False),  # a question, not a will
    ("I do not want to ask my friends about this. What is a river, really?", False),                      # negated
    ("The letter waits by the gate. What passage connects the rain to the sea?", False),                  # no intent to ask anyone
    ("Perhaps I should write that letter to ask about my appearance, letting the rain fall.", False),     # no question in the thought
]
NEUTRAL_BANNED = ("disagree", "contrary", "challenge", "distrust", "tested", "otherwise", "oppose", "push back")
FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


def pure():
    for t, e in EXTRACT:
        g = peers.extract_question(t)
        check(f"extract_question({t[:50]!r}) -> {g!r}", g == e)
    long_q = "Is " + " ".join(["wonder"] * 80) + " enough?"
    g = peers.extract_question(long_q) or ""
    check("a long question is cut at a word boundary within 300 chars", 0 < len(g) <= 300 and not g.endswith("wond"))
    for t, e in WIDE:
        check(f"wide({t[:60]!r}) -> {e}", peers.question_to_friend_wide(t) is e)
    check("flag is live (J-3371 flipped it once the system-voiced prompt line was replaced by contrary_note)", peers.PEER_CONTRARY_MATCH_WIDE == "live")
    check("live: the wide phrase fires question_to_friend", peers.question_to_friend(WIDE[0][0]) is True)
    check("live: the original phrase still fires", peers.question_to_friend("put this question to one of my friends") is True)
    peers.PEER_CONTRARY_MATCH_WIDE = "off"
    try:
        check("forced off: the wide phrase does not fire question_to_friend", peers.question_to_friend(WIDE[0][0]) is False)
    finally:
        peers.PEER_CONTRARY_MATCH_WIDE = "live"
    import random
    orders = {tuple(peers.contrary_roster(random.Random(i))) for i in range(30)}
    check("the roster is all of PERSONAS every time", all(set(o) == set(peers.PERSONAS) and len(o) == len(peers.PERSONAS) for o in orders))
    check("the roster order actually varies (%d distinct orders in 30 draws)" % len(orders), len(orders) > 10)
    check("every correspondent has a neutral line", set(peers._PEER_DESCR) == set(peers.PERSONAS))
    check("no roster line or note carries a contrary/test/hint word",
          not any(w in (v + peers.contrary_note(k)).lower() for k, v in peers._PEER_DESCR.items() for w in NEUTRAL_BANNED))
    check("contrary_note is descriptive: %r" % peers.contrary_note("lovelace"),
          peers.contrary_note("lovelace") == "(Ada Lovelace is an analyst, formal and precise.)")
    check("contrary_note('nobody') is empty", peers.contrary_note("nobody") == "")


def _thoughts(path):
    import json
    for ln in open(path, encoding="utf-8"):
        try:
            t = (json.loads(ln).get("thought") or "")
        except Exception:
            continue
        if t:
            yield t


def scan(path):
    n = old = wide = 0
    hits = []
    for t in _thoughts(path):
        n += 1
        tl = t.lower()
        if any(rx.search(t) for rx in peers._Q2FRIEND_RES):
            old += 1
        if peers.question_to_friend_wide(t):
            wide += 1
            hits.append(t)
    print(f"thoughts={n}  original-regex matches={old}  wide-matcher matches={wide}")
    for h in hits[:40]:
        print("  WIDE>", " ".join(h.split())[:300])


def replay(path, n):
    import asyncio, collections, random
    sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
    from lab_env import isolate
    qs, seen = [], set()
    for t in _thoughts(path):
        q = peers.extract_question(t)
        if q and q.endswith("?") and 40 <= len(q) <= 300 and q not in seen:
            seen.add(q)
            qs.append(q)
    random.Random(7).shuffle(qs)
    qs = qs[-n:] if len(qs) > n else qs
    picks = collections.Counter()

    async def go():
        for q in qs:
            k = await peers.contrary_target(q)
            picks[k or "NONE"] += 1
            print(f"  {k or 'NONE':11s} {q[:100]}")
    with isolate(db="empty"):
        asyncio.run(go())
    print("pick spread over", len(qs), "questions:", dict(picks.most_common()))
    print("distinct correspondents picked:", len([k for k in picks if k != "NONE"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if "--scan" in a:
        scan(a[a.index("--scan") + 1])
    elif "--replay" in a:
        replay(a[a.index("--replay") + 1], int(a[a.index("--n") + 1]) if "--n" in a else 40)
    else:
        pure()
        print(f"{'FAILED ' + str(len(FAILS)) if FAILS else 'all pass'}")
        sys.exit(1 if FAILS else 0)
