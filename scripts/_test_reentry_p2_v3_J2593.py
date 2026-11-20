"""Regression test for J-2593 (D-0520 (b)): within_cycle_reentry Phase 2 -- v3 revise prompt for the commitment-formation
arm, aimed at collapse and basin shift (SHADOW ONLY). Tests only prompt assembly, the per-kind version routing, the
prompt_version / revise_v2 tags on settle rows, the self-reference counter and status()'s per-version split.
Offline: fake revise/embed, no LLM, no hub, no model load. Writes only under lab_env.isolate(). Fails on any change to
the P2 files in the top level of C:\\Nascence\\data. Exit 0 = pass. Run from a worktree."""
import asyncio, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                    # BEFORE lab_env (F-2423)
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import reentry, reentry_p2
import lab_env

LIVE = pathlib.Path(r"C:\Nascence") / "data"
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

def fp():
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in LIVE.iterdir() if p.is_file()}
before = fp()
KC, KS = reentry_p2.KIND_COMMIT, reentry_p2.KIND_SCENE

# 1. version routing ---------------------------------------------------------------------------------------------------
check("commitment-formation defaults to v4 (J-3838; v4 reuses the v3 template)", reentry_p2.prompt_version(KC) == 4)
check("scene-binding stays on v2", reentry_p2.prompt_version(KS) == 2)
check("no kind -> v2 (legacy callers unchanged)", reentry_p2.prompt_version(None) == 2)
reentry_p2.REVISE_PROMPT_V2 = False
check("REVISE_PROMPT_V2 off -> v1 for every kind", {reentry_p2.prompt_version(k) for k in (KC, KS, None)} == {1})
d = "I resolve to write about how the uncertainty shapes the ink on my page."
check("v1 prompt is Phase 1 NEUTRAL", reentry_p2.build_revise_prompt(d, "ing", kind=KC) == reentry._NEUTRAL.format(draft=d, ingredient="ing"))
reentry_p2.REVISE_PROMPT_V2 = True

# 2. v3 prompt assembly ------------------------------------------------------------------------------------------------
p3 = reentry_p2.build_revise_prompt(d, "The ink pot cracked in the cold.", original=d, kind=KC)
tgt, lim = reentry_p2.length_budget(d)
check("v3 carries the v2 length budget anchored on max(draft, floor)", f"about {tgt} characters" in p3 and f"never more than {lim}" in p3)
check("v3 contains the draft and the ingredient", d in p3 and "The ink pot cracked in the cold." in p3)
check("v3 drops every self-voice cue (no 'own words' / 'own phrasing' / 'own voice')",
      not any(s in p3.lower() for s in ("own words", "own phrasing", "own voice")))
check("v3 forbids added self/identity talk and generalising",
      "Do not add anything about yourself, your mind, your thoughts, your identity" in p3 and "more abstract" in p3)
check("v3 anchors on subject + concrete nouns and allows 'almost unchanged'",
      "keep its concrete nouns" in p3 and "almost unchanged" in p3)
check("v3 keeps neutral framing and bans preamble", "Do not check it or fix it" in p3 and "No preamble" in p3)
p3b = reentry_p2.build_revise_prompt("a much longer pass-one output " * 20, "x", original=d, kind=KC)
check("v3 pass-2 target stays anchored on the ORIGINAL draft", f"about {tgt} characters" in p3b)
p2 = reentry_p2.build_revise_prompt(d, "ing", original=d, kind=KS)
check("scene-binding prompt is byte-identical to the v2 template",
      p2 == reentry_p2._REVISE_V2.format(draft=d, ingredient="ing", target=tgt, limit=lim))
check("v2 and v3 prompts differ", p2 != reentry_p2.build_revise_prompt(d, "ing", original=d, kind=KC))

# 3. self-reference counter --------------------------------------------------------------------------------------------
check("self_ref counts identity talk the reviser appended under v2 (F-3282 examples)",
      reentry_p2.self_ref_count("my thoughts are mine, yet I am the language model I run") >= 2
      and reentry_p2.self_ref_count("and I became who I am through my thoughts") >= 2)
check("self_ref is 0 on a concrete stand", reentry_p2.self_ref_count("The rusted trap feels like a foundation for new growth.") == 0)

# 4. settle rows under isolate: version tags separable, status() splits by version -------------------------------------
def embed(text):
    v = [0.0] * 64
    for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split():
        v[hash(w) % 64] += 1.0
    nn = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / nn for x in v]
SEEN = []
async def revise_kw(prompt, max_tokens=999):
    SEEN.append((prompt, max_tokens))
    return "I resolve to write about how the uncertainty shapes the ink, now that the ink pot cracked in the cold."
ING = ["The ink pot cracked in the cold and the nib dried on the desk overnight."]
with lab_env.isolate(db="empty", also=[(reentry_p2, ["_LOG", "_STATE"]), (reentry, ["_LOG", "_STATE"])]):
    rc = asyncio.run(reentry_p2.settle_shadow_p2(d, KC, revise=revise_kw, retrieve=lambda q: ING,
                                                 embed=embed, basin=None, level=0.3))
    check("commitment row: prompt_version 4, revise_v2 False", rc and rc.get("prompt_version") == 4 and rc.get("revise_v2") is False)
    check("commitment row carries self_ref_draft/self_ref_settled + norm fields",
          rc and "self_ref_draft" in rc and "self_ref_settled" in rc and "len_ratio_norm" in rc)
    check("the revise callable actually received the v3 prompt + token cap",
          SEEN and "almost unchanged" in SEEN[0][0] and SEEN[0][1] == reentry_p2._revise_cap(d))
    SEEN.clear()
    rs = asyncio.run(reentry_p2.settle_shadow_p2(d, KS, revise=revise_kw, retrieve=lambda q: ING,
                                                 embed=embed, basin=None, level=0.3))
    check("scene row: prompt_version 2, revise_v2 True, got the v2 prompt",
          rs and rs.get("prompt_version") == 2 and rs.get("revise_v2") is True and SEEN and "never more than" in SEEN[0][0]
          and "almost unchanged" not in SEEN[0][0])
    # a legacy v2 commitment row (no prompt_version) must count as v2, not v3
    legacy = dict(rc); legacy.pop("prompt_version"); legacy["revise_v2"] = True
    with open(reentry_p2._LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(legacy) + "\n")
    st = reentry_p2.status()
    byv = st[KC].get("norm", {}).get("by_prompt_version", {})
    check("status() splits commitment settles by prompt version (v2 legacy=1, v4=1)",
          byv.get(2, {}).get("settles") == 1 and byv.get(4, {}).get("settles") == 1)
    check("isolated log lies in the lab dir, not the live P2 log", "_lab" in str(reentry_p2._LOG) and reentry_p2._LOG.name == "reentry_p2_shadow.jsonl" and reentry_p2._LOG.parent != LIVE)

after = fp()
changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
p2_hit = [k for k in changed if k.startswith("reentry_p2") or k.startswith("reentry_")]
print("data/ top-level changed during test (live Du may write):", changed[:12])
check("no P2/P1 reentry file in live data/ changed", not p2_hit)
print("FAIL" if FAILS else "PASS", f"({len(FAILS)} failures)")
sys.exit(1 if FAILS else 0)
