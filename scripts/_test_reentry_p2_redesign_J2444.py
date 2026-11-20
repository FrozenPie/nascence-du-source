"""Regression test for J-2444 (D-0489): within_cycle_reentry Phase 2 -- length-normalised collapse test + length-bounded
revise prompt (SHADOW ONLY). Offline: fake revise/embed, no LLM, no hub. Writes only under lab_env.isolate().
Prints a before/after fingerprint of the top level of C:\\Nascence\\data and fails on any change attributable to this test
(files written by the live Du process meanwhile are reported but only fail if they are the P2 files).
Exit 0 = pass. Run from a worktree."""
import asyncio, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                    # BEFORE lab_env (F-2423)
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import reentry, reentry_p2
import lab_env
reentry_p2.REVISE_PROMPT_VERSION[reentry_p2.KIND_COMMIT] = 2   # J-2593: this test pins the v2 prompt it was written for

LIVE = pathlib.Path(r"C:\Nascence") / "data"
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

def fp():
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in LIVE.iterdir() if p.is_file()}
before = fp()

# 1. normalised measure ------------------------------------------------------------------------------------------------
m0 = {"basin_rose": False, "overall_delta": 0.3}
n = reentry_p2.measure_norm("Short stand here.", "Short stand here, now a normal sentence.", m0)
check("one-line draft becoming a normal sentence is NOT inflation under the norm", not n["inflated_norm"] and not n["would_collapse_norm"]
      and n["would_admit_settled_norm"])
check("raw Phase-1 test WOULD have called it inflated (ratio>1.5)", reentry._LEN_INFLATE < len("Short stand here, now a normal sentence.") / len("Short stand here."))
n = reentry_p2.measure_norm("x" * 40, "y" * 700, m0)
check("a 700-char paragraph from a 40-char draft is still inflation", n["inflated_norm"] and n["would_collapse_norm"]
      and not n["would_admit_settled_norm"] and n["len_ratio_norm"] == round(700 / reentry_p2.LEN_FLOOR, 3))
n = reentry_p2.measure_norm("x" * 300, "y" * 330, {"basin_rose": True, "overall_delta": 0.3})
check("basin rise still collapses regardless of length", n["would_collapse_norm"] and not n["inflated_norm"])
check("phase-1 _measure untouched (no norm keys)", "len_ratio_norm" not in reentry._measure("a" * 50, "b" * 60, [1.0, 0.0], [0.0, 1.0], None))

# 2. prompt v2 ----------------------------------------------------------------------------------------------------------
d = "I will keep the garden journal every evening."
p = reentry_p2.build_revise_prompt(d, "The frost took the beans last week.", original=d)
tgt, lim = reentry_p2.length_budget(d)
check("v2 prompt carries target/limit anchored on max(draft, floor)", f"about {tgt} characters" in p and f"never more than {lim}" in p and tgt == reentry_p2.LEN_FLOOR)
check("v2 keeps neutral framing (no check/fix implication) and bans preamble", "Do not check it or fix it" in p and "No preamble" in p and "additional context" in p)
long_d = "z" * 250
check("limit is 1.3x for long drafts", reentry_p2.length_budget(long_d) == (250, 325))
p2 = reentry_p2.build_revise_prompt("a much longer pass-one output " * 20, "ingredient text", original=d)
check("pass-2 target stays anchored on the ORIGINAL draft (no ratchet)", f"about {tgt} characters" in p2)
reentry_p2.REVISE_PROMPT_V2 = False
check("flag off -> Phase 1 NEUTRAL prompt", reentry_p2.build_revise_prompt(d, "ing") == reentry._NEUTRAL.format(draft=d, ingredient="ing"))
reentry_p2.REVISE_PROMPT_V2 = True
check("token backstop in [40,220] and shrinks for short drafts", 40 <= reentry_p2._revise_cap(d) < 220 and reentry_p2._revise_cap("q" * 2000) == 220)

# 3. settle under isolate: rows carry v2 + norm fields, revise gets max_tokens when it accepts it ---------------------------
def embed(text):
    v = [0.0] * 64
    for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split():
        v[hash(w) % 64] += 1.0
    nn = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / nn for x in v]
SEEN = []
async def revise_kw(prompt, max_tokens=999):
    SEEN.append((prompt, max_tokens))
    return "Keep the garden journal each evening, noting the frost took the beans."
async def revise_plain(prompt):
    SEEN.append((prompt, None))
    return "Keep the garden journal each evening, noting the frost took the beans."
ING = ["The frost took the beans last week and nothing else in the row at all."]
with lab_env.isolate(db="empty", also=[(reentry_p2, ["_LOG", "_STATE"]), (reentry, ["_LOG", "_STATE"])]):
    rec = asyncio.run(reentry_p2.settle_shadow_p2(d, reentry_p2.KIND_COMMIT, revise=revise_kw, retrieve=lambda q: ING,
                                                  embed=embed, basin=None, level=0.3))
    check("settle row has revise_v2 + normalised fields", rec and rec["revise_v2"] is True and "len_ratio_norm" in rec
          and rec["draft_len"] == len(d) and rec["settled_len"] == len(rec["settled"]) and "would_collapse_norm" in rec)
    check("keyword-capable revise received the token cap", SEEN and SEEN[0][1] == reentry_p2._revise_cap(d) and "never more than" in SEEN[0][0])
    check("short stand + same-size rewrite: raw len_ratio shown, norm not inflated", rec["len_ratio"] > 1.0 and not rec["inflated_norm"])
    reentry_p2._claim_slot  # noqa  (cooldown state lives in the isolated _STATE)
    reentry_p2._STATE.write_text("{}", encoding="utf-8")
    SEEN.clear()
    rec2 = asyncio.run(reentry_p2.settle_shadow_p2(d, reentry_p2.KIND_COMMIT, revise=revise_plain, retrieve=lambda q: ING,
                                                   embed=embed, basin=None, level=0.3))
    check("plain revise(prompt) callables still work", rec2 and rec2["passes"] >= 1 and SEEN and SEEN[0][1] is None)
    st = reentry_p2.status()["commitment-formation"]
    check("status() reports a norm block", st.get("norm", {}).get("settles") == 2 and "collapse_rate" in st["norm"])

# 4. live data/ untouched by this test -------------------------------------------------------------------------------
after = fp()
changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
print("FINGERPRINT data/ top-level changed files:", changed or "none")
check("this test did not touch the P2/P1 live files", not [c for c in changed if c.startswith("reentry")])
sys.exit(1 if FAILS else 0)
