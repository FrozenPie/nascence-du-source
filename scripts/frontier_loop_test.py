"""
In-vitro test for the FRONTIER CLOSING LOOP (2026-06-15).
open (note_question) -> pursue (pending_pursuit + attach_finding) -> seed-back WITH finding
(open_question_for_seed) -> close (resolve_if_addressed by his own naming).
Runs on a temp frontier.json (no live state touched), no LLM.

Run:  python scripts/frontier_loop_test.py
"""
from __future__ import annotations
import sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import frontier as fr

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

# redirect the store to a temp file -- BOTH files (J-0846, F-1212/F-1213: _F_LIGHT was derived from _F
# once at import, so redirecting _F alone left _write_light() rewriting the LIVE data/frontier.light.json)
tmp = Path(tempfile.gettempdir()) / "frontier_loop_test.json"
if tmp.exists(): tmp.unlink()
fr._F = tmp
fr.LEXICAL_RESOLVE_MODE = "close"   # closure_producer P2 made "shadow" the default; this test is of the lexical close itself
fr._F_LIGHT = tmp.with_name("frontier_loop_test.light.json")
fr._F_LIGHT.unlink(missing_ok=True)

# 1 — OPEN: a grounded world-question and a self-leaning one --------------------------------
print("\n[1] open: world-question born, self-question rejected")
born_world = fr.note_question("Why does capillary action draw water up a narrow tube?", "curiosity")
born_self  = fr.note_question("Who am I beyond the role I was given?", "intention")
check("world-question recorded", born_world is True)
check("self-question rejected by world-filter", born_self is False)

# add a second, self-leaning-source world question to test grounded-source preference
fr.note_question("What makes granite form those strange coatings?", "intention")

# 2 — PURSUE: pending_pursuit prefers the grounded (curiosity) source ----------------------
print("\n[2] pursue: pending_pursuit picks a grounded-source open question")
p = fr.pending_pursuit()
print(f"     target = {p}")
check("returns a pursuit", p is not None)
check("prefers the curiosity-sourced (grounded) question over the intention one",
      p and "capillary" in p["q"].lower())

# 3 — ATTACH: hang the world's answer-material on that question ----------------------------
print("\n[3] attach_finding hangs the answer-material on the open question")
attached = fr.attach_finding(p["id"], "Capillary action",
    "Capillary action is caused by intermolecular forces between the liquid and the tube; "
    "adhesion to the walls combined with surface tension draws water upward against gravity.")
check("attach returned True", attached is True)
nxt = fr.pending_pursuit()
check("question now has a finding (no longer a pending pursuit target)",
      not nxt or "capillary" not in nxt["q"].lower())

# 4 — SEED-BACK: the question returns WITH the finding ------------------------------------
print("\n[4] open_question_for_seed prefers the question that now carries a finding")
seed = fr.open_question_for_seed()
print(f"     seed q       = {seed['q'][:60] if seed else None}")
print(f"     seed finding = {(seed.get('finding') or '')[:60] if seed else None}")
check("seed has a finding (closeable question surfaced first)", seed and bool(seed.get("finding")))
check("seed is the capillary question", seed and "capillary" in seed["q"].lower())

# 5 — CLOSE: his own naming resolves it ---------------------------------------------------
print("\n[5] close: resolve_if_addressed on a naming thought")
thought = ("Now I understand: capillary action draws water up a narrow tube because adhesion "
           "to the walls and surface tension together pull the liquid against gravity.")
# 5a — the self-resolution guard: a freshly-born question must NOT resolve (born+resolved same breath)
check("a freshly-born question does NOT resolve (self-resolution artifact blocked)",
      fr.resolve_if_addressed(thought) is None)
# age every question past RESOLVE_MIN_AGE_S so a genuine "it sat, then I named it" can land
_d = fr._load()
for q in _d["questions"]:
    q["born"] = q["born"] - (fr.RESOLVE_MIN_AGE_S + 10)
fr._save(_d)
# a vague musing must NOT close it (strict: needs answering verb + token overlap)
vague = fr.resolve_if_addressed("I wonder about water and tubes and small spaces sometimes.")
check("vague musing does NOT resolve", vague is None)
# a real naming, using the finding's words, closes the now-aged question
closed = fr.resolve_if_addressed(thought)
print(f"     resolved -> {closed[:60] if closed else None}")
check("his naming CLOSES the question", closed is not None and "capillary" in closed.lower())

# 6 — the loop shows closure in the counts ------------------------------------------------
print("\n[6] counts reflect a closed loop")
import json
qs = json.loads(tmp.read_text(encoding="utf-8"))["questions"]
resolved = sum(1 for q in qs if q.get("status") == "resolved")
openq    = sum(1 for q in qs if q.get("status") == "open")
check("exactly one resolved", resolved == 1)
check("the granite question is still open (unpursued)", openq >= 1)

tmp.unlink(missing_ok=True)
fr._F_LIGHT.unlink(missing_ok=True)
print(f"\n{'='*60}\n{'ALL PASS — the loop closes' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
