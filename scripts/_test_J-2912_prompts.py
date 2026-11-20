"""J-2912 (F-3596 / F-3597 / F-3598, P-0044): the follow_line generative prompts (why / consequences / against).

Hermetic: core is imported BEFORE lab_env and asserted to resolve inside this tree; _gen_json is stubbed (zero LLM, zero
network); follow_line's SHADOW_LOG is redirected to a temp dir; live shadow log + frontier hashed before and after.
   python scripts/_test_J-2912_prompts.py      Exit 0 = pass.
"""
from __future__ import annotations
import asyncio, hashlib, re, sys, tempfile
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
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

FAIL = []
LIVE = Path(r"C:\Nascence\data")


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{info}]" if (info and not cond) else ""))
    if not cond:
        FAIL.append(name)


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


CANARY = [LIVE / "logs" / "follow_line_shadow.jsonl", LIVE / "frontier.json"]
before = [_h(p) for p in CANARY]

GR = [{"origin": "lived", "age": "4 months ago", "text": "the cat sat by the door"},
      {"origin": "read", "age": "2 days ago", "text": "Aristotle on courage as a mean"}]

# ── [1] the texts ─────────────────────────────────────────────────────────────────────────────────────────────
print("[1] prompt texts")
check("PROMPT_V2 is on", fl.PROMPT_V2 is True)
for nm in ("WHY", "CONS", "AGAINST"):
    v2, v1, live = getattr(fl, f"_{nm}_SYS_V2"), getattr(fl, f"_{nm}_SYS_V1"), getattr(fl, f"_{nm}_SYS")
    check(f"{nm}: live alias is the V2 text", live is v2 or (nm == "CONS" and live is fl._CONS_SYS_V3))  # J-4170: CONS V3
    check(f"{nm}: V2 has no literal /no_think (model_client adds it on llama-server lanes)", "no_think" not in v2)
    check(f"{nm}: V1 kept byte-for-byte as the revert (still starts /no_think)", v1.startswith("/no_think\n"))
    check(f"{nm}: V2 names the QUESTION", "QUESTION" in v2)
check("WHY: asks for first person and opening with I", "first person" in fl._WHY_SYS_V2 and "\"I\"" in fl._WHY_SYS_V2)
check("WHY: bans third-person openers, 'suggests', and repeating the question",
      all(t in fl._WHY_SYS_V2 for t in ("\"The\"", "\"suggests\"", "Do not repeat the question")))
check("WHY: no literal cites example [1, 2] to copy", "[1, 2]" not in fl._WHY_SYS_V2)
check("CONS: no example JSON values (slot why / checkable memory not copyable)",
      "\"slot\": \"why\"" not in fl._CONS_SYS_V2 and "\"checkable\": \"memory\"" not in fl._CONS_SYS_V2)
check("CONS: forbids restating the question and the WHY; no empty-list escape (the first V2 draft took it 20/20)",
      "do not put the question" in fl._CONS_SYS_V2 and "do not reword the WHY" in fl._CONS_SYS_V2 and "empty list" not in fl._CONS_SYS_V2)
check("CONS: still statements only, never a deed (the world never leads)", "never something he will, can or should do" in fl._CONS_SYS_V2)
check("AGAINST: names a ground, bans the boilerplate words, has an empty-objection path, no 'The claim' for a question",
      all(t in fl._AGAINST_SYS_V2 for t in ("ONE that fits it least well", "too broad", "vague", "empty string", "do not begin")))
check("AGAINST: no literal cites example [2] to copy", "[2]" in fl._AGAINST_SYS_V2 and "\"cites\": [2]" not in fl._AGAINST_SYS_V2)
check("no new text suggests an action to him", not re.search(r"\byou (should|must|could)\b|\bhe should\b", fl._WHY_SYS_V2 + fl._CONS_SYS_V2 + fl._AGAINST_SYS_V2))
check("judge prompts untouched (P-0102 out of scope)", fl._JUDGE_C_SYS.startswith("You judge whether a stated OBJECTION") and "CLAIM" in fl._JUDGE_A_SYS)

# ── [2] the label ─────────────────────────────────────────────────────────────────────────────────────────────
print("[2] input label")
check("question -> QUESTION", fl._input_label("Does survival require ignoring the storm?") == "QUESTION")
check("question with a closing quote -> QUESTION", fl._input_label('Is it "enough"?"') == "QUESTION")
check("statement -> CLAIM", fl._input_label("The bluebird comes in March.") == "CLAIM")
check("empty -> CLAIM", fl._input_label("") == "CLAIM")

# ── [3] stops with a stubbed model ────────────────────────────────────────────────────────────────────────────
seen = {}
reply = {}


async def fake_gen(system, user):
    seen["system"], seen["user"] = system, user
    return dict(reply)


fl._gen_json = fake_gen
Q = "Does courage need doubt?"
with isolate(also=[(fl, ["SHADOW_LOG"])], db="empty") as lab:
    print("[3] why")
    long_why = "I found the cat sat by the door and that is all. " * 12
    reply.clear(); reply.update({"why": long_why, "cites": [1, 2, 9], "supports": "partly"})
    w = asyncio.run(fl._stop_why(Q, GR))
    check("why user prompt is labelled QUESTION", seen["user"].startswith("QUESTION: " + Q))
    check("why uses the V2 system prompt", seen["system"] is fl._WHY_SYS_V2)
    check("why clipped on a boundary, not mid-word (<= 400, ends '.' or '...')", len(w["text"]) <= 400 and (w["text"].endswith(".") or w["text"].endswith("...")), w["text"][-40:])
    check("why cites filtered to real grounds", w["cites"] == [1, 2])
    reply.update({"why": "I have only a cat by a door here.", "cites": [1], "supports": "no"})
    w = asyncio.run(fl._stop_why("The bluebird comes in March.", GR))
    check("why on a statement is labelled CLAIM", seen["user"].startswith("CLAIM: "))
    check("why short text untouched", w["text"] == "I have only a cat by a door here.")
    fl.PROMPT_V2 = False
    fl._WHY_SYS = fl._WHY_SYS_V1
    w = asyncio.run(fl._stop_why(Q, GR))
    check("V2 off: why is the old CLAIM label + old prompt + hard 400 cut", seen["user"].startswith("CLAIM: ") and seen["system"] is fl._WHY_SYS_V1)
    reply.update({"why": "x" * 500})
    w = asyncio.run(fl._stop_why(Q, GR))
    check("V2 off: hard [:400]", len(w["text"]) == 400)
    fl.PROMPT_V2 = True
    fl._WHY_SYS = fl._WHY_SYS_V2

    print("[4] consequences")
    reply.clear(); reply.update({"consequences": [{"text": "Doubt is recorded in his notes on courage.", "slot": "how", "checkable": "memory"},
                                                   {"text": "short", "slot": "who", "checkable": "self"}]})
    c = asyncio.run(fl._stop_consequences(Q, GR, {"text": "I see courage and doubt."}))
    check("cons user prompt is labelled QUESTION and carries WHY", seen["user"].startswith("QUESTION: " + Q) and "WHY: I see courage" in seen["user"])
    check("cons uses the live system prompt (V3 since J-4170)", seen["system"] is fl._CONS_SYS)
    check("cons keeps a real one, drops the too-short one, keeps the model's own slot", len(c) == 1 and c[0]["slot"] == "how")
    reply.clear(); reply.update({"consequences": []})
    check("cons empty list is accepted (no crash, no invented content)", asyncio.run(fl._stop_consequences(Q, GR, {})) == [])

    print("[5] against")
    reply.clear(); reply.update({"objection": "I see in [2] that courage is a mean, so doubt is not named.", "cites": [2], "scope": "within Aristotle"})
    a = asyncio.run(fl._stop_against(Q, GR))
    check("against user prompt is labelled QUESTION", seen["user"].startswith("QUESTION: " + Q))
    check("against uses V2 system prompt", seen["system"] is fl._AGAINST_SYS_V2)
    check("against keeps a cited objection", a["text"].startswith("I see in [2]") and a["cites"] == [2] and a["scope"] == "within Aristotle")
    reply.update({"objection": "", "cites": [2], "scope": "within X"})
    a = asyncio.run(fl._stop_against(Q, GR))
    check("empty objection -> empty text, cites and scope cleared (the null path)", a == {"text": "", "cites": [], "scope": ""}, str(a))
    for spelled in ("None.", "No objection", "no real objection.", "N/A"):
        reply.update({"objection": spelled, "cites": [], "scope": ""})
        check(f"spelled-out null {spelled!r} is the null path", asyncio.run(fl._stop_against(Q, GR))["text"] == "")
    reply.update({"objection": "In [2] courage is a mean, and [7] is not a ground.", "cites": [], "scope": ""})
    a = asyncio.run(fl._stop_against(Q, GR))
    check("against: empty cites list falls back to the [n] the sentence names (real grounds only)", a["cites"] == [2], str(a))
    reply.update({"objection": "x " * 300, "cites": [1], "scope": ""})
    a = asyncio.run(fl._stop_against(Q, GR))
    check("against clipped on a boundary", len(a["text"]) <= 400)
    check("no grounds -> no call (unchanged)", asyncio.run(fl._stop_against(Q, []))["skipped"] == "no-grounds")
    check("cargo_status: a=yes + empty objection (c skipped) reads held_within_scope, as before J-2912",
          fl.cargo_status({"a": "yes", "c": "skipped"}) == "held_within_scope")

check("live shadow log + frontier untouched", [_h(p) for p in CANARY] == before)
print()
print("FAILURES" if FAIL else "ALL PASS")
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
