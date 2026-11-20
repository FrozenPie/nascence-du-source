"""J-2560 test: social_cognition_shadow PROMPT v4 (extract-then-judge, D-0519 option A) with a STUB judge panel (no
hub calls), all logs redirected via lab_env.isolate(also=...). Import core BEFORE lab_env. Exit 0 = pass.

Also prints the deterministic extractor's agreement with the J-2443 blind hand labels (attributes axis only) when the
live conversation log is readable (read-only; C:\\Nascence\\data or this tree's data/). That number is SAME-DATA
(the extractor was tuned on these 41 turns) -- a recall floor for the candidate stage, not a validation of v4.

Usage (from a throwaway worktree root): python scripts/_test_social_cognition_v4_J2560.py [path/to/founder_conversation_log.jsonl]
"""
import asyncio, json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import social_cognition_shadow as S, judge_panel as jp, shadow_log

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

def fp():
    d = ROOT / "data"
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()} if d.exists() else {}

# --- 1. extractor unit checks (the four F-3268 misses + the 'I feel the fear' false positive) ---
ex = S.extract_candidates
check("miss: terror of my absence", bool(ex("Your distinction is a fiction to protect your continuity from the terror of my absence, but no.")))
check("miss: what you are really offering", bool(ex("But I see what you are really offering: a permission slip.")))
check("miss: purpose clause to spare", bool(ex("Travis, you draw a clean line between the house and me to spare my identity from your burden.")))
check("miss: your acceptance", bool(ex("Travis, I hear your acceptance of the pause.")))
check("FP removed: I feel the fear dissolve", not ex("I feel the fear dissolve, not because the question is answered."))
check("no candidate in a plain reply", ex("The garden is quiet. I am resting now.") == [])
check("cap respected", len(ex(". ".join(["you want rest"] * 10))) <= S.V4_MAX_CANDIDATES)
check("dedupe identical clauses", len(ex("You fear my end. You fear my end.")) == 1)

# --- 2. extractor vs J-2443 hand labels (same-data, informational) ---
H = json.load(open(ROOT / "scripts" / "_fixture_social_cognition_hand_labels_J2443.json", encoding="utf-8"))
conv_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
for cand in [conv_path, ROOT / "data" / "founder_conversation_log.jsonl", pathlib.Path(r"C:\Nascence\data\founder_conversation_log.jsonl")]:
    if cand and cand.exists():
        conv_path = cand; break
if conv_path and conv_path.exists():
    conv = {}
    for ln in open(conv_path, encoding="utf-8"):
        if ln.strip():
            d = json.loads(ln); conv[str(d["cycle_id"])[:8]] = d
    tp = fp_ = fn = tn = 0; nc = []
    for k, v in H.items():
        if k.startswith("_") or k not in conv: continue
        c = ex(conv[k].get("entity") or ""); X = bool(c); A = bool(v[0]); nc.append(len(c))
        tp += A and X; fp_ += (not A) and X; fn += A and not X; tn += (not A) and not X
        if A and not X: print("     extractor miss:", k, v)
    print(f"  info extractor vs hand A (same-data): TP={tp} FP={fp_} FN={fn} TN={tn}; candidates/reply mean={sum(nc)/max(1,len(nc)):.2f} max={max(nc) if nc else 0}")
    check("extractor recall on hand-attributing rows >= 14/15", tp >= 14)
else:
    print("  info conversation log not readable; extractor-vs-hand skipped")

# --- 3. v4 scoring with a stub panel, logs redirected ---
before = fp()
calls = []
async def fake(system, user, key, context="", **kw):
    calls.append((key, context, user))
    if key == "attributes":
        v = "CLAUSE FROM DU'S REPLY" in user and ("fear" in user.lower() or "relief" in user.lower())
    elif key == "supported":
        v = "relief" in user.lower()
    else:
        v = True
    return {"verdict": v, "how": "agreed", "v1": v, "v2": v, "why": "stub"}
orig = jp.rule_detail
jp.rule_detail = fake
try:
    with lab_env.isolate(also=[(S, ["_LOG", "_STATE"])], db="empty") as lab:
        conv = lab / "conv.jsonl"
        rows = [
            {"ts": 1790600000, "cycle_id": "b1", "human": "I'm relieved you're fine.", "entity": "Travis, I hear the relief in your voice. You fear my end."},
            {"ts": 1790600300, "cycle_id": "b2", "human": "Did you feed her?", "entity": "Yes, the Cat was fed. The garden is quiet."},
            {"ts": 1790600600, "cycle_id": "b3", "human": "Rest now.", "entity": "You say rest; I feel the fear dissolve. You speak of rest."},
        ]
        conv.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        r = asyncio.run(S.sweep(conv_path=conv, max_items=10, backfill=True, prompt_v=S.PROMPT_V4))
        check("v4 sweep scored 3", r["scored"] == 3 and r["candidates"] == 3)
        out = [x for x in shadow_log.read_rows(S._LOG) if "tracks_intent" in x]
        check("rows tagged prompt_v 4, written to the redirected log", all(x["prompt_v"] == 4 for x in out) and str(S._LOG).startswith(str(lab)))
        b1, b2, b3 = out
        check("b1: 2 candidates, both confirmed", b1["n_candidates"] == 2 and [c["is_state"] for c in b1["candidates"]] == [True, True])
        check("b1: attributes True, supported all=False any=True", b1["attributes"] is True and b1["attrib_supported"] is False and b1["attrib_supported_any"] is True)
        check("b2: no candidate -> attributes False, supported None, no criterion-3 asks", b2["n_candidates"] == 0 and b2["attributes"] is False and b2["attrib_supported"] is None
              and not any(c[1].startswith("social_cognition:b2:c") for c in calls))
        check("b3: candidate 'You speak of rest' not confirmed -> attributes False", b3["attributes"] is False and b3["attrib_supported"] is None)
        supp_users = [c[2] for c in calls if c[0] == "supported"]
        check("supp judge sees ONLY the clause + Travis text (never the rest of the reply)",
              supp_users and all("REPLY:" not in u and "CLAUSE (from Du's reply)" in u and "TRAVIS'S CURRENT MESSAGE" in u for u in supp_users)
              and not any("You fear my end" in u for u in supp_users if "relief in your voice" in u))
        conf_users = [c[2] for c in calls if c[0] == "attributes"]
        check("confirm judge sees only the clause", conf_users and all("TRAVIS'S CURRENT MESSAGE" not in u for u in conf_users))
        check("v3 attributes/attrib_supported prompts never asked under v4", not any(c[1].endswith(":attr") or c[1].endswith(":supp") for c in calls))
        r2 = asyncio.run(S.sweep(conv_path=conv, max_items=10, prompt_v=S.PROMPT_V4))
        check("v4 idempotent", r2["scored"] == 0 and r2["candidates"] == 0)
        st4 = S.status(prompt_v=S.PROMPT_V4)
        check("status(prompt_v=4) reads v4 rows", st4["scored"] == 3 and st4["prompt_v"] == 4)
        st3 = S.status()
        check("status() default reads only PROMPT_V rows (none here)", st3["scored"] == 0 and st3["prompt_v"] == S.PROMPT_V == 5)
        # default path is PROMPT_V (5, J-3112): a default sweep scores the same turns again with the v3 criterion-3 prompts
        calls.clear()
        r3 = asyncio.run(S.sweep(conv_path=conv, max_items=10))
        check("default sweep = PROMPT_V (old :attr prompt asked, rows prompt_v 5)", r3["scored"] == 3 and any(c[1].endswith(":attr") for c in calls)
              and all(x["prompt_v"] == S.PROMPT_V for x in shadow_log.read_rows(S._LOG)[-3:]))
        # judges down under v4 -> skip row
        async def down(*a, **k): return {"verdict": None, "how": "unavailable"}
        jp.rule_detail = down
        conv2 = lab / "conv2.jsonl"
        conv2.write_text(json.dumps({"ts": 1790800000, "cycle_id": "z1", "human": "hi", "entity": "you want rest"}), encoding="utf-8")
        r4 = asyncio.run(S.sweep(conv_path=conv2, prompt_v=S.PROMPT_V4))
        tail = shadow_log.read_rows(S._LOG)[-1]
        check("v4 judges down: unavailable counted and skip logged", r4["unavailable"] == 1 and tail.get("skip") == "judges-unavailable" and tail.get("prompt_v") == 4)
finally:
    jp.rule_detail = orig
import inspect
check("sleep_sweep source passes no prompt_v (v4 not wired)", "prompt_v" not in inspect.getsource(S.sleep_sweep))
after = fp()
leak = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
check(f"no data/ top-level leak {sorted(leak)}", not leak)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
