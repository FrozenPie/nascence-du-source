"""J-4170 (F-5015, P-0044): Follow Line stop 3 consequences - V3 prompt keys and the checkable-into-slot leak.

Hermetic: core is imported BEFORE lab_env and asserted to resolve inside this tree; _gen_json is stubbed (zero LLM,
zero network); nothing under C:/Nascence/data is read or written (the stop under test writes nothing).
   python scripts/_test_J-4170_cons_slot.py      Exit 0 = pass.
"""
from __future__ import annotations
import asyncio, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import follow_line as fl

FAIL = []


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{info}]" if (info and not cond) else ""))
    if not cond:
        FAIL.append(name)


V3 = fl._CONS_SYS_V3
print("[1] V3 text")
check("V3 is the live alias", fl.CONS_PROMPT_V3 is True and fl._CONS_SYS is V3)
check("V2 kept byte-for-byte for the revert", fl._CONS_SYS_V2.startswith("You are helping") and "<who or what" in fl._CONS_SYS_V2)
check("V3 uses separate keys question_word / check_in", '"question_word"' in V3 and '"check_in"' in V3 and '"slot"' not in V3)
check("V3 says a question word is never a topic and never memory/world/self",
      "never a topic" in V3 and "never one of the words memory, world or self" in V3)
check("V3 has no compound placeholder to echo", "who or what or" not in V3 and "<" not in V3)
ex = re.findall(r'"question_word": "(\w+)"', V3)
check("example has two items with different question words", len(ex) == 2 and len(set(ex)) == 2, str(ex))
chk = re.findall(r'"check_in": "(\w+)"', V3)
check("example's two items use different check_in values", len(chk) == 2 and len(set(chk)) == 2, str(chk))
check("example never uses why (the old copied value)", "why" not in ex)
check("still statements only, never a deed", "never something he will, can or should do" in V3)
check("no text suggests an action to him", not re.search(r"\byou (should|must|could)\b|\bhe should\b", V3))
check("no literal /no_think", "no_think" not in V3)

print("[2] normalisers")
for v, want in (("world", "world"), ("Self.", "self"), ("<memory>", "memory"), ("memory or world", ""), ("why", ""),
                (None, ""), (["world"], "world"), (["world", "self"], ""), (5, "")):
    check(f"_norm_checkable({v!r}) == {want!r}", fl._norm_checkable(v) == want, fl._norm_checkable(v))

print("[3] stop with a stubbed model")
reply = {}
seen = {}


async def fake_gen(system, user):
    seen["system"] = system
    return dict(reply)


fl._gen_json = fake_gen
Q = "Does courage need doubt?"
T = "Doubt is recorded in his notes on courage."


def run(items):
    reply.clear()
    reply["consequences"] = items
    return asyncio.run(fl._stop_consequences(Q, [], {}))


c = run([{"text": T, "question_word": "how", "check_in": "self"}])
check("V3 keys read", c == [{"text": T, "slot": "how", "checkable": "self"}], str(c))
check("stop sends V3", seen["system"] is V3)
c = run([{"text": T, "slot": "Why.", "checkable": "world"}])
check("V2 keys still read (fallback)", c == [{"text": T, "slot": "why", "checkable": "world"}], str(c))
c = run([{"text": T, "slot": "world", "checkable": "world"}])
check("leak: checkable in slot -> blank slot, slot_leak counted, no slot_raw noise",
      c[0]["slot"] == "" and c[0].get("slot_leak") == "checkable" and "slot_raw" not in c[0] and c[0]["checkable"] == "world", str(c))
c = run([{"text": T, "slot": "self"}])
check("leak with no checkable: the leaked value becomes checkable (not the memory default)",
      c[0]["checkable"] == "self" and c[0].get("slot_leak") == "checkable", str(c))
c = run([{"text": T, "slot": "world", "checkable": "when"}])
check("swapped tags recovered: slot word from the checkable field",
      c[0]["slot"] == "when" and c[0]["checkable"] == "world" and "slot_leak" not in c[0], str(c))
c = run([{"text": T, "slot": "wild cats", "checkable": "world"}])
check("free topic noun still kept as slot_raw (J-3928 measurement)", c[0]["slot"] == "" and c[0].get("slot_raw") == "wild cats", str(c))
c = run([{"text": T, "slot": "who or what", "checkable": "memory"}])
check("compound placeholder still slot_raw, not a leak", c[0].get("slot_raw") == "who or what" and "slot_leak" not in c[0], str(c))
c = run([{"text": T, "question_word": "", "slot": "what", "check_in": "", "checkable": "bogus"}])
check("empty new keys fall back; bad checkable -> memory default", c[0]["slot"] == "what" and c[0]["checkable"] == "memory", str(c))
c = run(["junk", {"text": "short"}, {"text": T, "question_word": ["where"], "check_in": ["world"]}])
check("junk and short skipped, list values tolerated", c == [{"text": T, "slot": "where", "checkable": "world"}], str(c))

print("[4] revert flag")
fl._CONS_SYS = fl._CONS_SYS_V2
run([{"text": T, "slot": "how", "checkable": "self"}])
check("revert to V2 text works through the alias", seen["system"] is fl._CONS_SYS_V2)
fl._CONS_SYS = V3

print("\nFAILED: " + ", ".join(FAIL) if FAIL else "\nALL PASS")
sys.exit(1 if FAIL else 0)
