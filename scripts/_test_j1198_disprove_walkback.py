"""Unit test for J-1198's build of D-0213's WALK-BACK (Travis re-ruled D-0213 on 2026-09-18; F-1682: no build job
ever existed): in scripts/train_state_invitro.py's _disprove(), the FIRST disprove call (_DISPROVE_SYSTEM /
objection_found) keeps its TIEBREAK -> UNDETERMINED fallback byte-for-byte, and the SECOND call (_SCOPE_SYSTEM /
scope_only) uses its normal verdict logic again: a verdict decided through TIEBREAK is used (True ->
held_within_scope, False -> objected), a second call that itself reached no verdict (None) is still 'objected'
(J-0835's fail-conservative design -- see the note in _disprove's docstring: the J-1198 briefing said "stays
UNDETERMINED as today" but neither today's code nor the pre-J-0986 code does that).

No network, no file writes: core.judge_panel.rule_detail is replaced by a fake that returns a scripted result per
call. scripts/train_state_invitro.py cannot be imported (its top level runs Part 1's in-vitro checks and a live
replay), so the pieces under test are AST-extracted and exec'd (same technique as J-0986's own offline test).

  python scripts/_test_j1198_disprove_walkback.py                    # exit 0 = every scenario passes AND every
                                                                     # mutant is killed
  python scripts/_test_j1198_disprove_walkback.py --script PATH      # run the scenarios against another copy of the
                                                                     # script (e.g. the pre-J-1198 blob: the two
                                                                     # walk-back scenarios must FAIL there)
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ap = argparse.ArgumentParser()
ap.add_argument("--script", default=str(ROOT / "scripts" / "train_state_invitro.py"))
ap.add_argument("--no-mutants", action="store_true", help="skip the mutation check (used when testing an old copy)")
ARGS = ap.parse_args()
SCRIPT = Path(ARGS.script)

import core.judge_panel as jp  # noqa: E402  (the WORKTREE copy; printed below)

print("core.judge_panel.__file__ =", jp.__file__)
assert str(Path(jp.__file__).resolve()).lower().startswith(str(ROOT).lower()), "core.judge_panel resolves outside this root"
print("script under test        =", SCRIPT)

# --------------------------------------------------------------------------------------------- extraction
SRC = SCRIPT.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
WANT_ASSIGN = {"_DISPROVE_SYSTEM", "_SCOPE_SYSTEM", "_TIEBREAK_WHY_CAVEAT"}
WANT_FUNC = {"_disprove", "_tiebreak_why_caveat"}
SEG: dict = {}
for node in TREE.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id in WANT_ASSIGN:
        SEG[node.targets[0].id] = ast.get_source_segment(SRC, node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in WANT_FUNC:
        SEG[node.name] = ast.get_source_segment(SRC, node)
missing = (WANT_ASSIGN | WANT_FUNC) - set(SEG)
assert not missing, f"could not extract {missing} from {SCRIPT}"


def build(disprove_src: str | None = None) -> dict:
    ns: dict = {"__name__": "j1198_extracted"}
    for name in ("_DISPROVE_SYSTEM", "_SCOPE_SYSTEM", "_TIEBREAK_WHY_CAVEAT", "_tiebreak_why_caveat"):
        exec(SEG[name], ns)
    exec(disprove_src or SEG["_disprove"], ns)
    return ns


# --------------------------------------------------------------------------------------------- scenarios
def R(verdict, how, why=None):
    """A rule_detail() result dict (every key the real one returns)."""
    return {"v1": None, "v2": None, "verdict": verdict, "how": how, "err1": None, "err2": None, "err3": None,
            "why1": None, "why2": None, "why3": None, "why": why}


ORIG = "orig objection why"
UND = "UNDETERMINED"
NARROW_FALLBACK = "(narrower claim earned; no why-text returned)"
ORIG_FALLBACK = "(objection found; no why-text returned)"

# name, first result (or Exception), second result (or Exception / None = must not be called), expected dict, n calls
SCENARIOS = [
    # ---- FIRST call: unchanged (the fallback is restricted to this call, per D-0213's re-ruling) ----
    ("first_agreed_false_is_held", R(False, "agreed", "fine"), None,
     dict(status="held", objection=[], how="agreed", scope_how=None), 1),
    ("first_tiebreak_true_is_UNDETERMINED", R(True, "tiebreak", "tb"), None,
     dict(status=UND, objection=[], how="tiebreak", scope_how=None), 1),
    ("first_tiebreak_false_is_UNDETERMINED", R(False, "tiebreak", "tb"), None,
     dict(status=UND, objection=[], how="tiebreak", scope_how=None), 1),
    ("first_unavailable_is_UNDETERMINED", R(None, "unavailable"), None,
     dict(status=UND, objection=[], how="unavailable", scope_how=None), 1),
    ("first_split_no_tiebreak_is_UNDETERMINED", R(None, "split_no_tiebreak"), None,
     dict(status=UND, objection=[], how="split_no_tiebreak", scope_how=None), 1),
    ("first_exception_is_UNDETERMINED", RuntimeError("boom"), None,
     dict(status=UND, objection=[], how="exception", scope_how=None, error="boom"), 1),
    # ---- SECOND call: agreed cases, unchanged ----
    ("second_agreed_true_is_held_within_scope", R(True, "agreed", ORIG), R(True, "agreed", "narrow claim"),
     dict(status="held_within_scope", objection=["narrow claim"], how="agreed", scope_how="agreed"), 2),
    ("second_agreed_false_is_objected", R(True, "agreed", ORIG), R(False, "agreed", "no narrower claim"),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="agreed"), 2),
    # ---- SECOND call: the WALK-BACK (J-0986 made both of these UNDETERMINED) ----
    ("second_TIEBREAK_true_is_held_within_scope (walk-back)", R(True, "agreed", ORIG), R(True, "tiebreak", "tb narrow"),
     dict(status="held_within_scope", objection=["tb narrow"], how="agreed", scope_how="tiebreak"), 2),
    ("second_TIEBREAK_false_is_objected (walk-back)", R(True, "agreed", ORIG), R(False, "tiebreak", "tb none"),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="tiebreak"), 2),
    # ---- SECOND call: reached no verdict (None) -> 'objected', deliberately unchanged ----
    ("second_unavailable_stays_objected", R(True, "agreed", ORIG), R(None, "unavailable"),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="unavailable"), 2),
    ("second_split_no_tiebreak_stays_objected", R(True, "agreed", ORIG), R(None, "split_no_tiebreak"),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="split_no_tiebreak"), 2),
    ("second_exception_stays_objected", R(True, "agreed", ORIG), RuntimeError("boom2"),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="exception", scope_error="boom2"), 2),
    # ---- why-text fallbacks ----
    ("second_true_without_why_uses_fallback_text", R(True, "agreed", ORIG), R(True, "agreed", None),
     dict(status="held_within_scope", objection=[NARROW_FALLBACK], how="agreed", scope_how="agreed"), 2),
    ("first_true_no_why__second_TIEBREAK_false__objected_with_fallback_text (walk-back)",
     R(True, "agreed", None), R(False, "tiebreak", None),
     dict(status="objected", objection=[ORIG_FALLBACK], how="agreed", scope_how="tiebreak"), 2),
]


def run_scenario(ns: dict, sc) -> list:
    name, first, second, exp, n_calls = sc
    calls: list = []

    async def fake_rule_detail(system, user, key, context="", num_predict=200):
        calls.append({"system": system, "user": user, "key": key})
        r = first if key == "objection_found" else second
        if isinstance(r, Exception):
            raise r
        if r is None:
            raise AssertionError(f"scenario {name}: an unexpected {key!r} call was made")
        return dict(r)

    real = jp.rule_detail
    jp.rule_detail = fake_rule_detail
    fails: list = []
    try:
        try:
            res = asyncio.run(ns["_disprove"]("CLAIM TEXT", ["support one", "support two"]))
        except AssertionError as exc:
            return [str(exc)]
    finally:
        jp.rule_detail = real
    for k, v in exp.items():
        got = res.get(k)
        if k == "error":
            if v not in (got or ""):
                fails.append(f"{k}: expected to contain {v!r}, got {got!r}")
        elif k == "scope_error":
            if v not in (res.get("scope_error") or ""):
                fails.append(f"{k}: expected to contain {v!r}, got {res.get('scope_error')!r}")
        elif got != v:
            fails.append(f"{k}: expected {v!r}, got {got!r}")
    if len(calls) != n_calls:
        fails.append(f"rule_detail called {len(calls)}x, expected {n_calls}x")
    # the prompts each call was made with
    if calls:
        c1 = calls[0]
        if c1["key"] != "objection_found" or c1["system"] != ns["_DISPROVE_SYSTEM"]:
            fails.append("first call is not (_DISPROVE_SYSTEM, 'objection_found')")
        if "CLAIM: CLAIM TEXT" not in c1["user"] or "  1. support one" not in c1["user"]:
            fails.append("first call's user prompt lost the claim/support block")
    if len(calls) >= 2:
        c2 = calls[1]
        if c2["key"] != "scope_only" or c2["system"] != ns["_SCOPE_SYSTEM"]:
            fails.append("second call is not (_SCOPE_SYSTEM, 'scope_only')")
        why_line = "WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: " + (first.get("why") or ORIG_FALLBACK)
        if why_line not in c2["user"]:
            fails.append("second call's user prompt does not carry the first call's why-text")
    return fails


def run_all(ns: dict) -> dict:
    return {sc[0]: run_scenario(ns, sc) for sc in SCENARIOS}


def caveat_checks(ns: dict) -> list:
    f = ns["_tiebreak_why_caveat"]
    fails = []
    if not f("held_within_scope", "agreed", "tiebreak"):
        fails.append("caveat must be LIVE again for a held_within_scope row whose scope_how is tiebreak")
    if f("held_within_scope", "agreed", "agreed"):
        fails.append("caveat must stay empty for an agreed held_within_scope row")
    if f("objected", "agreed", "tiebreak"):
        fails.append("caveat must stay empty for an objected row (its quote is the first call's agreed why-text)")
    if f("UNDETERMINED", "tiebreak", "tiebreak") or f("held", "agreed", None):
        fails.append("caveat must be empty for held / UNDETERMINED (nothing quoted)")
    return fails


# --------------------------------------------------------------------------------------------- mutants
def mutate(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, f"mutation anchor not found exactly once: {old!r} ({src.count(old)}x)"
    return src.replace(old, new)


SECOND_INTERCEPT = ('    if scope_verdict is True:\n'
                    '        narrower = scope_why or "(narrower claim earned; no why-text returned)"')
MUTANTS = [
    # the J-0986 state: second-call TIEBREAK -> UNDETERMINED reinstated (the walk-back reverted)
    ("M1 reinstate the J-0986 second-call intercept",
     lambda s: mutate(s, SECOND_INTERCEPT,
                      '    if scope_how == "tiebreak":\n'
                      '        return {"status": "UNDETERMINED", "objection": [], "how": how, "error": None,\n'
                      '                "scope_how": scope_how, "scope_error": None}\n' + SECOND_INTERCEPT)),
    # the FIRST call's fallback removed
    ("M2 drop the FIRST call's tiebreak intercept",
     lambda s: mutate(s, '    if how == "tiebreak":\n'
                         '        return {"status": "UNDETERMINED", "objection": [], "how": how, "error": None,\n'
                         '                "scope_how": None, "scope_error": None}\n', "")),
    # True/False mapping of the second call flipped
    ("M3 flip the second call's True/False mapping",
     lambda s: mutate(s, SECOND_INTERCEPT.replace("is True", "is True"), SECOND_INTERCEPT.replace("is True", "is False"))),
    # the briefing's literal (but non-existent-"today") reading: a verdict-None second call -> UNDETERMINED
    ("M4 verdict-None second call -> UNDETERMINED (the briefing's literal reading)",
     lambda s: mutate(s, SECOND_INTERCEPT,
                      '    if scope_verdict is None:\n'
                      '        return {"status": "UNDETERMINED", "objection": [], "how": how, "error": None,\n'
                      '                "scope_how": scope_how, "scope_error": None}\n' + SECOND_INTERCEPT)),
    # the second call stops carrying the first call's why-text
    ("M5 second prompt drops the first call's why-text",
     lambda s: mutate(s, 'f"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: {original_why}\\n\\n"',
                      '"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: (omitted)\\n\\n"')),
]


def main() -> int:
    ns = build()
    results = run_all(ns)
    bad = {k: v for k, v in results.items() if v}
    print(f"\n[scenarios] {len(results) - len(bad)}/{len(results)} pass")
    for k, v in results.items():
        print(("  PASS  " if not v else "  FAIL  ") + k)
        for m in v:
            print("        -", m)
    cav = caveat_checks(ns)
    print(f"[caveat helper] {'PASS' if not cav else 'FAIL'}")
    for m in cav:
        print("        -", m)
    rc = 0 if (not bad and not cav) else 1

    if ARGS.no_mutants:
        return rc
    print("\n[mutation check] each mutant must be KILLED (>=1 scenario fails):")
    survived = []
    for name, fn in MUTANTS:
        mutated_ns = build(fn(SEG["_disprove"]))
        r = run_all(mutated_ns)
        killed_by = [k for k, v in r.items() if v]
        print(f"  {'KILLED  ' if killed_by else 'SURVIVED'} {name}" + (f"  <- {len(killed_by)} scenario(s): {killed_by[:3]}" if killed_by else ""))
        if not killed_by:
            survived.append(name)
    if survived:
        print("MUTANTS SURVIVED:", survived)
        rc = 1
    print("\nRESULT:", "ALL OK" if rc == 0 else "FAILED")
    return rc


if __name__ == "__main__":
    sys.exit(main())
