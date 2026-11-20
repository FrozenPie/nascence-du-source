"""J-2985 (P-0026; F-3677, F-3678, F-3682, F-3684): the reply to a friend's letter.

  [1] the _rsys prompt has no named image ("breeze", "gust", "sea air", "retire it"), asks for the opening by
      structure ("begin with the first thing in their letter you want to answer"), and is gender-neutral
      (no he/him/his anywhere in the system prompt, for any of the 8 friends incl. Ada Lovelace).
  [2] the friend's letter is fed up to _REPLY_LETTER_CAP (3600) -- not 1200 -- so the longest letter ever seen
      (3,189 chars) is not cut; max_tokens is _REPLY_MAX_TOKENS (700); the user prompt names the friend, not "His".
  [3] _clean_reply_letter: literal backslash-n becomes a real newline; text is cut where a closing quote is followed
      by a JSON key (the stored 'Du", "metadata": { ...' residue); clean letters (quotes, commas, real newlines,
      a quoted phrase followed by a comma) pass through unchanged apart from strip(); None / non-str are safe.
  [4] the call site stores/sends the CLEANED reply (peers.record_reply and the fragment use _reply), the siblings
      (write-first _isys, J-3184 real-present block, "(my letter to X)" fragment shape) are untouched, and the base
      system core/model_client.py carries no part of this change.
Zero LLM, zero live data.   python scripts/_test_J-2985_reply_prompt.py   (exit 1 on any failure)"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core BEFORE lab_env / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from nodes import inner_monologue_node as imn  # noqa: E402
from core import peers  # noqa: E402

FAILS = []
BS = chr(92)   # one literal backslash, spelled out so no editor or shell layer can halve it


def check(name, got, want):
    ok = got == want
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  got={got!r} want={want!r}"))
    if not ok:
        FAILS.append(name)


path = ROOT / "nodes" / "inner_monologue_node.py"
src = path.read_text(encoding="utf-8")
tree = ast.parse(src)
rs = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
      and any(isinstance(t, ast.Name) and t.id == "_rsys" for t in n.targets)]
check("[1] exactly one _rsys assignment", len(rs), 1)

# [1]
for pk, per in peers.PERSONAS.items():
    rsys = eval(compile(ast.Expression(rs[0].value), "<rsys>", "eval"), {"_nm": per["name"]})
    low = rsys.lower()
    for bad in ("breeze", "gust", "sea air", "retire it", "stock formula", "arrived like"):
        check(f"[1] {pk}: no named image/formula {bad!r}", bad in low, False)
    check(f"[1] {pk}: no gendered pronoun", re.search(r"\b(he|him|his|she|her|hers)\b", low) is None, True)
    check(f"[1] {pk}: structural opening ask", "begin with the first thing in their letter you want to answer" in rsys, True)
    check(f"[1] {pk}: still true-of-your-own-days + JSON shape",
          "say only what is true of your own days" in rsys and 'Output ONLY JSON: {"letter": "your reply"}' in rsys, True)
    check(f"[1] {pk}: names the friend", per["name"] in rsys, True)

# [2]
check("[2] cap constant", imn._REPLY_LETTER_CAP, 3600)
check("[2] cap holds the longest letter seen (3189)", imn._REPLY_LETTER_CAP >= 3189, True)
check("[2] max tokens constant", imn._REPLY_MAX_TOKENS, 700)
call = src[src.index("_rd = await call_node_json(self.conscious_urls, _rsys,"):]
call = call[:call.index("_reply = ")]
check("[2] call uses the cap", "_last[:_REPLY_LETTER_CAP]" in call and "[:1200]" not in call, True)
check("[2] call uses max tokens const", "max_tokens=_REPLY_MAX_TOKENS" in call, True)
check("[2] user prompt names the friend", "+ _nm + \"'s letter to you:" in call and "His letter" not in call, True)

# [3]
c = imn._clean_reply_letter
lit_n = BS + "n"
check("[3] literal backslash-n -> newline",
      c("Dear Ernest," + lit_n + lit_n + "Your letter" + lit_n + "found me."), "Dear Ernest,\n\nYour letter\nfound me.")
check("[3] literal backslash-r backslash-n -> newline", c("a" + BS + "r" + BS + "n" + "b"), "a\nb")
real = ('Send word when the mail is in my hands again.' + lit_n + lit_n + 'Your friend,' + lit_n + 'Du",\n  "metadata": {\n'
        '    "timestamp": "2023-')
check("[3] metadata residue cut + literal newlines fixed", c(real),
      "Send word when the mail is in my hands again.\n\nYour friend,\nDu")
check("[3] residue cut with real newlines", c('Your friend,\nDu",\n  "metadata": {}'), "Your friend,\nDu")
check("[3] residue cut, no space", c('bye",   "x_1":1'), "bye")
for clean in ("Dear John,\n\nI liked 'the sea', and your \"wild, wide\" phrase, truly.\n\nDu",
              'He said "yes", then left. "No," I said.',
              "Plain letter, with a comma, and a question? Yes.\nSecond line."):
    check("[3] clean letter unchanged", c(clean), clean.strip())
check("[3] strip", c("  hi  \n"), "hi")
check("[3] None", c(None), "")
check("[3] non-str", c(12), "12")

# [4]
tail = src[src.index("_reply = _clean_reply_letter("):]
tail = tail[:tail.index("# Writing FIRST to a friend")]
check("[4] reply cleaned at the call site", '_reply = _clean_reply_letter((_rd or {}).get("letter", ""))' in src, True)
check("[4] record_reply gets the cleaned _reply", "_peers.record_reply(_pk, _reply" in tail, True)   # J-3025: now also route="reply"
# J-4052 re-pin: J-3656 raised the stored-fragment cap 1300 -> _STORED_LETTER_CAP (3600); the shape is otherwise the same.
check("[4] fragment shape untouched", 'f"(my letter to {_nm}) " + _reply[:_STORED_LETTER_CAP], layer="episodic",' in tail
      and "relevance=0.75, importance=0.8" in tail, True)
check("[4] J-3184 real-present block present", '_rpresent += "What was on your mind just now' in src, True)
check("[4] write-first prompt untouched", "Share the \"\n                                 \"thing that moved you to write" in src, True)
mc = (ROOT / "core" / "model_client.py").read_text(encoding="utf-8")
check("[4] model_client untouched (no _clean_reply_letter there)", "_clean_reply_letter" in mc, False)

print("\nFAILED: " + ", ".join(FAILS) if FAILS else "\nJ-2985 all ok")
sys.exit(1 if FAILS else 0)
