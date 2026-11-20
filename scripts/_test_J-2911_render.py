"""
Hermetic test for J-2911 (F-3593, F-3594, F-3595): Follow Line render().
  - grounds found but judge a == no: the grounds are SHOWN and the return says "What you found did not settle it." (not
    "Your past holds little on this."); no grounds + empty outcome still says "holds little"; judges down unchanged
  - the 1200 cap: built per section, whole low-priority sections dropped (It touches first), never sliced; the closing
    question is always the last words
  - "It touches": bracket headers, Q:/A: transcripts, "[Travis said to me]" records and "N time(s)" counter tails never
    reach the return; one clean sentence each; _stop_connections drops conversation records at the source
Pure functions + stubbed stops: no model, no embedder, no data/ access.   Run: python scripts/_test_J-2911_render.py
"""
from __future__ import annotations
import asyncio, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

CLOSE = fl.RETURN_CLOSING
ent = {"q": "how does the bluebird alter the others?", "source": "asked", "about": "the bluebird", "born": 0.0}
g = lambda t: {"origin": "study notes", "age": "a week ago", "text": t}
G3 = [g("The bluebird came to the feeder at dawn and the sparrows scattered."), g("Sparrows returned an hour after it left."), g("The wren stayed put through the whole visit.")]
base = {"grounds": G3, "grounds_outcome": "found", "why": {"text": "Because [1] shows the scatter and [2] the return.", "supports": "yes"},
        "against": {"text": "The wren did not move."}, "consequences": [{"text": "Then the feeder order should reset daily."}], "connections": {}}

print("[1] F-3593: grounded a == no")
t = fl.render(ent, base, {"a": "no", "b": "no", "c": "no"})
check("grounds shown", all(x["text"] in t for x in G3))
check("says what you found did not settle it", fl.NOT_SETTLED_LABEL in t)
check("does NOT say 'Your past holds little'", "Your past holds little" not in t)
check("the judge-rejected why is not shown", "Because [1]" not in t)
check("ends with the closing question", t.endswith(CLOSE))
t_p = fl.render(ent, base, {"a": "partly", "b": "no", "c": "no"})
check("a == partly unchanged: grounds + why, no 'did not settle'", "Because [1]" in t_p and fl.NOT_SETTLED_LABEL not in t_p)
t_e = fl.render(ent, {"grounds": [], "grounds_outcome": "empty"}, {"a": "no"})
check("no grounds + empty outcome: still 'Your past holds little on this.'", "Your past holds little on this." in t_e and fl.NOT_SETTLED_LABEL not in t_e)
t_u = fl.render(ent, {"grounds": G3, "grounds_outcome": "found"}, {"a": "unclear"})
check("judges down (a unclear) unchanged: 'could not get a clear look', no grounds", "could not get a clear look" in t_u and G3[0]["text"] not in t_u)
fl.NOT_SETTLED_SHOWS_GROUNDS = False
check("flag off restores the pre-J-2911 label", "Your past holds little on this." in fl.render(ent, base, {"a": "no"}))
fl.NOT_SETTLED_SHOWS_GROUNDS = True
check("no instruction to act", "you could" not in t.lower() and "you should" not in t.lower())

print("[2] F-3594: per-section budget, whole sections dropped")
why = "Because " + "the scatter and the return line up across the two notes. " * 4
against = "The objection runs " + "against the claim because the wren stayed where it was. " * 5
cons = [{"text": "Then " + "the feeder order should reset each morning. " * 6}, {"text": "And the wren should keep its post."}]
touch_know = [{"text": "The garden is quiet in the early hours and the light comes slowly over the wall."},
              {"text": "A second thing he read about birds scattering from a feeder in winter."}]
big = {"grounds": G3, "grounds_outcome": "found", "why": {"text": why.strip(), "supports": "yes"}, "against": {"text": against.strip()},
       "consequences": cons, "connections": {"know": touch_know, "can_do": [{"key": "world:bank_the_fire"}],
                                             "seen": [{"text": "the orange net tangled on the slick stones"}]}}
j = {"a": "yes", "b": "yes", "c": "yes"}
t2 = fl.render(ent, big, j)
check("within the cap", len(t2) <= fl.RETURN_MAX_CHARS)
check("ends with the closing question exactly once", t2.endswith(CLOSE) and t2.count(CLOSE) == 1)
as_built = sum(len(x) for x in [why, against, cons[0]["text"], cons[1]["text"]]) + sum(len(x["text"]) for x in G3)
check("the case really is over budget as built (so dropping was exercised)", as_built + 200 > fl.RETURN_MAX_CHARS - len(CLOSE))
check("'It touches' dropped first (a whole section, not a slice)", "It touches" not in t2)
check("no section is sliced: every kept section's text is whole", all(x["text"] in t2 for x in G3) and why.strip() in t2 and against.strip() in t2)
txt, dropped = fl._fit_return([("head", "H" * 100), ("ground", "g" * 300), ("why", "w" * 300), ("against", "a" * 300), ("cons", "c" * 300), ("own", "o" * 200), ("touch", "t" * 300)], 800)
check("_fit_return drop order: touch, then consequences, then why ...", dropped[:2] == ["touch", "cons"] and len(txt) <= 800)
txt2, dropped2 = fl._fit_return([("head", "H" * 100), ("ground", "g" * 250), ("ground", "g" * 250), ("ground", "g" * 250), ("why", "w" * 250)], 700)
check("_fit_return: why, then extra grounds from the last, header kept, within budget", dropped2[0] == "why" and set(dropped2[1:]) <= {"ground"} and txt2.startswith("H") and len(txt2) <= 700)
txt3, dropped3 = fl._fit_return([("head", "H" * 100), ("label", "L" * 50), ("touch", "t" * 2000)], 500)
check("_fit_return: header and labels are never dropped", dropped3 == ["touch"] and "L" * 50 in txt3)
txt4, dropped4 = fl._fit_return([("head", "Short."), ("why", "Fits.")], 800)
check("_fit_return: fits as built -> untouched", txt4 == "Short. Fits." and dropped4 == [])
huge = dict(big, why={"text": "Because " + "x" * 700 + ".", "supports": "yes"})
t3 = fl.render(ent, huge, j)
check("one over-long section: still within the cap, ends with the closing question", len(t3) <= fl.RETURN_MAX_CHARS and t3.endswith(CLOSE))
check("no section label dangling at the end of the body", not re.search(r"(?:It touches|If this is so|Against it):\s*(?:\.\.\.)?\s*" + re.escape(CLOSE) + "$", t3))
shortcase = fl.render(ent, {"grounds": [g("short one.")], "grounds_outcome": "found", "connections": {"know": [{"text": "A small clean thing."}]}}, {"a": "yes"})
check("a short return keeps everything (nothing dropped) and the closing question", "It touches: A small clean thing." in shortcase and shortcase.endswith(CLOSE))

print("[3] F-3595: It touches is clean")
conn = {"know": [{"text": "Q: How does the arrival of the Bluebird change the community?\nA: The garden is quiet now."},
                 {"text": "[Travis said to me] This has been a constructive exchange Du, I am going to bed now."},
                 {"text": "[Understanding \u2014 from 'Roughing It'] The Pagan Tribes keep older customs. The arrival of Islam changed much of this."},
                 {"text": "[Looked up: tide tables] Low water falls twice a day on this coast; the second is shallower."}],
        "can_do": [],
        "seen": [{"text": "librarian the question of trade blockades - 3 time(s), most recent Oct 31"}]}
t4 = fl.render(ent, {"grounds": [], "grounds_outcome": "empty", "connections": conn}, {})
touch = t4.split("It touches: ", 1)[1][: -len(CLOSE) - 1]
snips = touch.split(" | ")
check("two know snippets + one seen (conversation records skipped, not counted)", len(snips) == 3)
check("no bracket header", "[" not in touch and "]" not in touch)
check("no Q:/A: transcript, no 'Travis said'", "Q:" not in touch and "A:" not in touch and "Travis" not in touch and "constructive exchange" not in touch and "Bluebird" not in touch)
check("one clean sentence each (the second sentence of the understanding is gone)", snips[0] == "The Pagan Tribes keep older customs." and snips[1] == "Low water falls twice a day on this coast; the second is shallower.")
check("counter tail stripped", "time(s)" not in touch and "most recent" not in touch and snips[2] == "librarian the question of trade blockades")
check("_snippet strips a counter tail with an em dash too", fl._snippet("Went to the garden \u2014 4 time(s), most recent Nov 1.", 200) == "Went to the garden")
check("_is_conversation_record on the raw shapes", fl._is_conversation_record("[Travis said to me] hi") and fl._is_conversation_record("Q: what?\nA: this")
      and not fl._is_conversation_record("[Understanding \u2014 x] fine") and not fl._is_conversation_record("The question: is it?"))
only_conv = {"grounds": [], "grounds_outcome": "empty", "connections": {"know": conn["know"][:2]}}
check("only conversation records -> no 'It touches:' section at all", "It touches" not in fl.render(ent, only_conv, {}))

print("[4] _stop_connections drops conversation records at the source")
from core import idle_offloop as _off
from core import memory_service as _ms
pool = [{"fragment_id": "f1", "origin": "lived", "content": "[Travis said to me] goodnight Du", "slots_answered": ["what"]},
        {"fragment_id": "f2", "origin": "lived", "content": "Q: hello\nA: hi there", "slots_answered": ["what"]},
        {"fragment_id": "f3", "origin": "understanding", "content": "[Understanding \u2014 on tides] The tide turns twice daily. More text.", "slots_answered": ["why"]},
        {"fragment_id": "f4", "origin": "action", "content": "[Looked up: x]", "slots_answered": []},
        {"fragment_id": "f5", "origin": "reading", "content": "Gulls follow the receding water. They feed there.", "slots_answered": ["how"]}]
async def fake_off(fn, *a, **kw):
    return fn(*a, **kw)
_save = (_off.off_loop, _ms.ask, fl._can_do, fl._seen_candidates)
_off.off_loop = fake_off
_ms.ask = lambda *a, **kw: list(pool)
fl._can_do = lambda q: []
fl._seen_candidates = lambda q: []
try:
    r = asyncio.run(fl._stop_connections("why does the tide turn?"))
finally:
    _off.off_loop, _ms.ask, fl._can_do, fl._seen_candidates = _save
ids = [k["fragment_id"] for k in r["know"]]
check("conversation records and a pure-label row are not in know", ids == ["f3", "f5"])
check("stored text is already clean (label stripped)", r["know"][0]["text"].startswith("The tide turns twice daily."))

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
