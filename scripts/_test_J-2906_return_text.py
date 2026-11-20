"""
Hermetic test for J-2906 (F-3578): the Follow Line return text is clean.
  - a return that hits the 1200 cap still ends with the closing question, never cut mid-word
  - no bracket store label / "Q:" tag leads an "It touches:" snippet; snippets cut on a boundary
  - the can_do clause states the procedure's NAME, never a quoted past reply spliced into "you have ... before"
  - "If this is so:" / "Your past holds little on this" logic untouched
Pure functions only: no model, no embedder, no data/ access.   Run: python scripts/_test_J-2906_return_text.py
"""
from __future__ import annotations
import re, sys
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

CLOSE = "Does it hold, or only part of it?"
long_sent = "The term travels across several traditions and carries a different weight in each of them, which is the point. "
ent = {"q": "what does the crossing mean?", "source": "asked", "about": "crossing"}
cargo = {"grounds": [{"origin": "reading", "age": "a month ago", "text": long_sent * 2}], "grounds_outcome": "found",
         "why": {"text": "Because " + long_sent * 2, "supports": "yes"}, "against": {"text": long_sent * 2},
         "consequences": [{"text": "Then " + long_sent * 5}, {"text": "And " + long_sent * 5}],
         "connections": {
             "know": [{"text": "[gist \u00b7 semantic] The Pagan Tribes of Borneo exhibit remnants of older customs like burning the dead, carvings of bulls and gold ornaments. The arrival of Islam and Europe changed much of this over the following centuries."},
                      {"text": "Q: How does the arrival of the Bluebird change the dynamics of the community?\nA: The garden is quiet now, save for the rustle of dry leaves."}],
             "can_do": [{"key": "talk:initial_reaction_to_maxwell_s_theories",
                         "statement": "Travis, observe the environment and consider the implications. Reflect on how the concept challenges"}],
             "seen": [{"text": "[Essay \u2014 on 'Bridges [and] fords'] the orange net tangled on the slick stones"}]}}
judged = {"a": "yes", "b": "yes", "c": "yes"}

print("[1] cap: closing question kept, no mid-word cut")
t = fl.render(ent, cargo, judged)
check("long return is within the cap", len(t) <= fl.RETURN_MAX_CHARS)
check("long return ends with the closing question", t.endswith(CLOSE))
body = t[: -len(CLOSE) - 1]
check("body ends on a sentence end or a '...' word-boundary cut", body.endswith((".", "!", "?", '."', "...")))
check("the body was actually trimmed (a real cap case: the full text is far over the cap)", len(" ".join([cargo["why"]["text"], cargo["against"]["text"]] + [c["text"] for c in cargo["consequences"]])) > fl.RETURN_MAX_CHARS and len(t) >= fl.RETURN_MAX_CHARS * 0.75)
check("no word is sliced: the last word kept is a whole word of the source (or the cut is on a sentence end)",
      body.endswith((".", "!", "?")) or re.findall(r"[A-Za-z']+", body.rstrip(".").rstrip())[-1] in re.findall(r"[A-Za-z']+", str(cargo)))
check("a short return passes through whole", fl.render(ent, {"grounds": [], "grounds_outcome": "empty"}, {}).endswith(CLOSE)
      and "Your past holds little on this." in fl.render(ent, {"grounds": [], "grounds_outcome": "empty"}, {}))

print("[2] store labels gone from 'It touches:'")
small = dict(cargo, grounds=[], why={}, against={}, consequences=[])
t2 = fl.render(ent, small, {"a": "no", "b": "no", "c": "no"})
touch = t2.split("It touches: ", 1)[1][: -len(CLOSE) - 1]
snips = touch.split(" | ")
check("three snippets (one know, the can_do clause, one seen -- the Q:/A: record skipped by J-2911)", len(snips) == 3)
check("no bracket label anywhere in the touch block", "[" not in touch and "]" not in touch)
check("no Q:/A: row tag", "Q:" not in touch and "\nA:" not in touch and " A: " not in touch)
# J-2911 (F-3595): a "Q: ... A: ..." cycle summary is a conversation record -> skipped, not kept as a touch
check("Q:/A: conversation record is skipped (J-2911), not kept as a touch", "Bluebird" not in touch and "The garden is quiet now" not in touch)
seen_only = dict(small, connections={"seen": cargo["connections"]["seen"]})
check("label with brackets inside is stripped whole", fl.render(ent, seen_only, {}).split("It touches: ", 1)[1].startswith("the orange net"))
check("label stripped from the first snippet", snips[0].startswith("The Pagan Tribes"))
check("an over-long snippet is cut on a sentence or word boundary, not at 200", len(snips[0]) <= fl.TOUCH_SNIPPET_CHARS and snips[0].endswith((".", "...")))
check("_strip_store_label: unbalanced leading bracket (old 200-cut label) -> ''", fl._strip_store_label("[Understanding \u2014 from 'Roughing It") == "")
check("_strip_store_label: plain text untouched", fl._strip_store_label("The garden is quiet.") == "The garden is quiet.")
check("_clip_boundary: fits -> untouched; word cut ends '...'",
      fl._clip_boundary("short one", 50) == "short one" and fl._clip_boundary("alpha beta gamma delta epsilon", 20) == "alpha beta gamma..."
      and fl._clip_boundary("One whole sentence here. And then a second one goes on", 30) == "One whole sentence here.")

print("[3] can_do clause")
check("names the procedure, not its stored reply", "something you have done before: initial reaction to maxwell s theories" in touch)
check("no 'you have <statement> before' splice", "Travis, observe the environment" not in t2 and not re.search(r"you have [A-Z]", t2) and " before |" not in t2)
check("empty key -> no clause", fl._did_before("") == "" and fl._did_before("world:") == "")

print("[4] untouched logic")
t_b = fl.render(ent, dict(cargo, why={}, against={}, connections={}), judged)   # J-2910: consequences need grounds
check("'If this is so:' still rendered when the judge says b yes", "If this is so: Then" in t_b)
check("'Your past holds little on this.' still rendered with no grounds", "Your past holds little on this." in t2)
check("no instruction to act", "you could" not in t.lower() and "you should" not in t.lower())
longq = dict(ent, q="word " * 80)
tq = fl.render(longq, {"grounds": [], "grounds_outcome": "empty"}, {})
check("a 220+ char question is cut on a word boundary inside its quote", '..."' in tq and "wor\"" not in tq)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
