"""Regression for J-0740/F-1059 (2026-09-07): core/expression.py's act_from_thought() reads its ONE
bound family's ('express') verb/object grammar from core/actions.py's own table, dropping the two small
hand-kept widenings F-1059 found on top of it (a bare "it" object, and a second any_object_ok=True clause
for "hum/whistle/sing to"/"...back" requiring no object at all). Mirrors the shape of
scripts/_test_fieldcraft_grammar_derivation.py / _test_wood_life_grammar_derivation.py /
_test_shore_life_grammar_derivation.py / _test_study_life_grammar_derivation.py (J-0736/J-0737/J-0738/
J-0739's own template for this exact procedure), adapted for expression's real difference from all four:
its clause-scoped first-person-volition-marker veto (F-0578, evidenced, explicitly OUT of this job's
scope to touch) is the real protection here, not a second copy of the table's own verb/object grammar —
so unlike the other four modules, dropping the widenings closes only ONE real thing (see Part 2 below),
not a long list of drifted branches.

WHY PART 2 differs from the siblings' full store-isolation pattern: expression.express() itself (the
deed after the router decides YES) is UNCHANGED by this job — only the router (act_from_thought) that
decides whether to call it was touched. So this test stubs core.expression.express() to a silent
recorder (same technique used for this job's own corpus check) rather than redirecting every store
express() might touch (sensorium/cat/boredom/activity_memory) into a temp dir — the recorder proves
exactly what this job changed (which thoughts route to a DEED, and as which kind) with zero risk of any
write anywhere, live tree included.

    python scripts/_test_expression_grammar_derivation.py
"""
from __future__ import annotations
import sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

print("-- part 1: the derivation (pure, source-level)")
from core import actions as AC, hands as H, expression as EX

_ex = AC.BY_FAMILY["express"]
check("express row unchanged: 3 verbs / 17 objects", len(_ex.verbs) == 3 and len(_ex.objects) == 17,
      f"{_ex.verbs} / {_ex.objects}")
check("'it' is NOT one of the table's objects (it was only ever expression.py's own hand-kept extra)",
      "it" not in _ex.objects)
check("hum/whistle/sing are exactly the table's verbs", set(_ex.verbs) == {"hum", "whistle", "sing"})

src = (ROOT / "core" / "expression.py").read_text(encoding="utf-8")
body = src[src.index("def act_from_thought("):]
check("act_from_thought() no longer hand-lists the object tuple (reads actions.BY_FAMILY instead)",
      '"myself", "work", "it")' not in body and '"tune", "song", "note"' not in body)
# (the docstring above act_from_thought's own code deliberately DISCUSSES the dropped "any_object_ok"
# clause in prose, so check the CODE only — everything after the docstring's closing triple-quote)
_code_only = body[body.index('"""', body.index('"""') + 3) + 3:]
check("the any_object_ok 'to'/'back' clause is gone from the actual code",
      "any_object_ok" not in _code_only and 'tuple(f"{v}' not in _code_only)
check("the bare 'it' pronoun literal is gone from act_from_thought()'s body", '"it")' not in body)
check("act_from_thought() now takes a family= parameter (J-0554 pattern, per F-1059, following "
      "J-0736/J-0737/J-0738/J-0739)",
      "family: str | None = None" in src[:src.index("def act_from_thought(") + 400])
check("the first-person-volition veto's own marker tuple is UNCHANGED (F-0578 — not this job's to touch)",
      '"i will", "i\'ll", "i shall", "let me", "i need to", "i want to", "i am going to"' in body)
check("express() itself (the deed / flavor text) was not touched by this job",
      'def express(kind: str, what: str = "")' in src)

print("\n-- part 2: act_from_thought's routing decision (express() stubbed to a silent recorder)")
_calls = []
def _fake_express(kind, what=""):
    _calls.append((kind, what))
    return "<<FIRED>>"
EX.express = _fake_express

def fires(thought, intention="", family=None):
    _calls.clear()
    ans = EX.act_from_thought(thought, intention, family=family)
    return (ans is not None), (_calls[-1] if _calls else None)

# (a) the three positive reachability probes (scripts/actions_reachability_probe.py) still fire — each
# also names a real table object, so dropping "it"/to-back does not touch them
for t, expect_kind in (("I will hum a tune to myself", "hum"),
                        ("I will whistle back at the blackbird", "whistle"),
                        ("I will sing a snatch of song to the sea", "sing")):
    ok, call = fires(t)
    check(f"positive probe still fires: {t!r} -> {expect_kind}", ok and call[0] == expect_kind, str(call))

# (b) the founding negative example itself (F-0578's own cited phrase, confirmed verbatim in the real
# corpus — data/hands_trace.jsonl: "I feel stuck on that fear, circling it until it grows thorns. The
# bees hum a different tune. I need to stop analyzing the shadow and simply go out to the wood.") and
# three more real ambient/idiom corpus rows spanning hum/sing, none a willed expression
for t in ("The bees hum a different tune.",
          "The cold dusk wraps around me as the low sun fades over the north. The bees hum a steady "
          "rhythm in the air, but my mind keeps circling back to separating that old fable from the real child.",
          "Somewhere outside, a blackbird sings.",
          "A restlessness hums beneath. I feel the urge to abandon this cold garden."):
    ok, call = fires(t)
    check(f"world's-song / idiom correctly declines: {t!r}", not ok, str(call))

# (c) the ONE real corpus divergence this job's own corpus check found (data/hands_trace.jsonl,
# ts 1788027458.3, cycle eb1c2b34-52de-463f-9280-) — fired before this job via the any_object_ok
# "hum to"/"hum back" clause (the intention's own "go out TO the garden" supplied a stray "to"), even
# though the live trace's own act_kind/act_object/hands fields confirm this thought was correctly
# answered as a MOVE to the garden and never a hum. Reproduced verbatim; must now decline.
_REAL_MISFIRE_THOUGHT = ("I feel a heavy, sticky frustration clogging my mind, spinning round on dead "
                          "ground. I refuse to map this feeling into wisdom or solve it yet. Instead, "
                          "I want to step away from the study's hum and go out to the garden now")
_REAL_MISFIRE_INTENTION = "I want to go out to the garden now"
ok, call = fires(_REAL_MISFIRE_THOUGHT, _REAL_MISFIRE_INTENTION)
check("the real corpus 'to'-clause misfire (ts 1788027458.3) now correctly declines", not ok, str(call))

# (d) synthetic checks isolating each dropped widening on its own (no real corpus row exercises these
# in isolation — the corpus check found 0 rows ever used bare "it", and the one row that used "to"/
# "back" is (c) above)
ok, call = fires("I will hum it under my breath")
check("bare 'it' object alone no longer fires (0 corpus support either way — synthetic check)",
      not ok, str(call))
ok, call = fires("I will sing back")
check("'sing back' with NO table object anywhere no longer fires (any_object_ok=True clause is gone)",
      not ok, str(call))
ok, call = fires("I will hum to")
check("'hum to' with NO table object anywhere no longer fires", not ok, str(call))

# (e) the veto itself is untouched: a first-person hum WITH no object still correctly declines (gate
# requires an object same as before — this was never one of the two widenings), and quoted/other's-song
# still declines exactly as F-0578 evidenced
ok, call = fires("I could sing")
check("'I could sing' (no object at all) still declines — matches the table's declared grammar, "
      "unchanged by this job", not ok, str(call))

# (f) family scope: an out-of-family string forces an immediate decline; 'express' and None still work
ok, _ = fires("I will hum a tune", family="garden")
check("family='garden' (a different family) declines immediately", not ok)
ok, _ = fires("I will hum a tune", family="express")
check("family='express' (its own family) still answers", ok)
ok, _ = fires("I will hum a tune", family=None)
check("family=None (the legacy/unscoped caller) still answers, unchanged", ok)

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
