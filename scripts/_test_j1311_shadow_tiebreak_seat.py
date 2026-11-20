"""Unit test for J-1311's build of D-0213's shadow-observe ruling (Travis, 2026-09-23, citing F-1850):
"Build gemma4:12b as the scope_only TIEBREAK-seat candidate, but shadow-observe it before fully trusting
it live." In scripts/train_state_invitro.py's `_disprove()`, whenever the SECOND (scope_only) call lands
on TIEBREAK, a NEW `_shadow_observe_candidate_tiebreak_seat()` call fires: it calls gemma4:12b directly
with the arm (c) polarity-explicit wording (byte-identical to scripts/lab_j1240_tiebreak_seat.py's own
already-characterized POLARITY arm) and logs what gemma WOULD have answered alongside TIEBREAK's real
verdict -- WITHOUT touching `scope_verdict`/`scope_how`/`scope_why`, or therefore anything `_disprove()`
returns.

Three things this test exists to prove, none of which "it compiles" can show on its own:
  1. The shadow call fires exactly when scope_how == "tiebreak" -- never on the FIRST call's own tiebreak
     fallback, never on agreed/unavailable/split_no_tiebreak second calls.
  2. `_disprove()`'s own return value is IDENTICAL whether the shadow call succeeds, returns a surprising
     answer, raises, or can't even write its own log -- the real merge verdict never depends on gemma.
  3. The shadow call's own system/user/key are exactly what D-0213's ruling + this job's briefing asked
     for: the polarity-explicit system prompt (byte-identical to lab_j1240's own POLARITY arm, cross-
     checked against that script's own source, not just this file's own internal assert), the IDENTICAL
     `scope_user` string the real second call already built (never re-derived), key
     "narrower_claim_earned", hub CANDIDATE_TIEBREAK_URL (byte-identical to lab_j1240's own CANDIDATE_URL).

No network, no real file writes into anything live: core.judge_panel.rule_detail AND core.judge_panel._ask
are both replaced by fakes that return a scripted result per call; the shadow log global is redirected to
a temp file per scenario and cleaned up after. scripts/train_state_invitro.py cannot be imported (its top
level runs Part 1's in-vitro checks and a live replay), so the pieces under test are AST-extracted and
exec'd (same technique as scripts/_test_j1198_disprove_walkback.py).

  python scripts/_test_j1311_shadow_tiebreak_seat.py                 # exit 0 = every scenario passes AND
                                                                      # every mutant is killed
  python scripts/_test_j1311_shadow_tiebreak_seat.py --script PATH   # run against another copy of the file
  python scripts/_test_j1311_shadow_tiebreak_seat.py --no-mutants    # skip the mutation check
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ap = argparse.ArgumentParser()
ap.add_argument("--script", default=str(ROOT / "scripts" / "train_state_invitro.py"))
ap.add_argument("--lab1240", default=str(ROOT / "scripts" / "lab_j1240_tiebreak_seat.py"),
                help="cross-checked for byte-identical arm (c) wording -- never imported, AST-extracted only")
ap.add_argument("--no-mutants", action="store_true", help="skip the mutation check (used when testing an old copy)")
ARGS = ap.parse_args()
SCRIPT = Path(ARGS.script)
LAB1240 = Path(ARGS.lab1240)

import core.judge_panel as jp  # noqa: E402  (the WORKTREE copy; printed below)

print("core.judge_panel.__file__ =", jp.__file__)
assert str(Path(jp.__file__).resolve()).lower().startswith(str(ROOT).lower()), "core.judge_panel resolves outside this root"
print("script under test        =", SCRIPT)
print("cross-check source       =", LAB1240)

# --------------------------------------------------------------------------------------------- extraction
SRC = SCRIPT.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
WANT_ASSIGN = {"_DISPROVE_SYSTEM", "_SCOPE_SYSTEM", "CANDIDATE_TIEBREAK_URL", "_SHADOW_TIEBREAK_LOG",
              "_SCOPE_TAIL_BOOL_FIRST", "_SHADOW_TIEBREAK_TAIL_POLARITY", "_SHADOW_TIEBREAK_SYSTEM"}
WANT_FUNC = {"_disprove", "_shadow_observe_candidate_tiebreak_seat"}
SEG: dict = {}
for node in TREE.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id in WANT_ASSIGN:
        SEG[node.targets[0].id] = ast.get_source_segment(SRC, node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in WANT_FUNC:
        SEG[node.name] = ast.get_source_segment(SRC, node)
missing = (WANT_ASSIGN | WANT_FUNC) - set(SEG)
assert not missing, f"could not extract {missing} from {SCRIPT} -- names moved/renamed?"

# cross-check source: lab_j1240_tiebreak_seat.py's own already-characterized (F-1850) arm (c) tail + URL,
# AST-extracted only (this script is NEVER imported -- its own top level does real hub probes/asserts).
L1240_SRC = LAB1240.read_text(encoding="utf-8")
L1240_TREE = ast.parse(L1240_SRC)
L1240_WANT = {"_TAIL_POLARITY", "CANDIDATE_URL"}
L1240_SEG: dict = {}
for node in L1240_TREE.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id in L1240_WANT:
        L1240_SEG[node.targets[0].id] = ast.literal_eval(node.value)
missing1240 = L1240_WANT - set(L1240_SEG)
assert not missing1240, f"could not extract {missing1240} from {LAB1240} -- names moved/renamed?"


def build(disprove_src: str | None = None, shadow_src: str | None = None) -> dict:
    # _SHADOW_TIEBREAK_LOG's own real source references the file-level `_DATA_DIR` import (from
    # nodes.inner_monologue_node) this test deliberately never imports -- a placeholder is enough here
    # since run_scenario() always overwrites ns["_SHADOW_TIEBREAK_LOG"] with a real tmp path before any
    # call; only the ASSIGNMENT's own presence/shape (still extracted, still exec'd) is under test.
    # `json` is seeded too: the real module imports it at file level (line 4, "import sys, json") and
    # `_shadow_observe_candidate_tiebreak_seat()` relies on that module global for json.dumps() -- same
    # as every other name (Path, etc.) this exec'd namespace would otherwise lack.
    ns: dict = {"__name__": "j1311_extracted", "_DATA_DIR": Path(tempfile.gettempdir()), "json": json}
    for name in ("_DISPROVE_SYSTEM", "_SCOPE_SYSTEM", "CANDIDATE_TIEBREAK_URL", "_SHADOW_TIEBREAK_LOG",
                "_SCOPE_TAIL_BOOL_FIRST", "_SHADOW_TIEBREAK_TAIL_POLARITY", "_SHADOW_TIEBREAK_SYSTEM"):
        exec(SEG[name], ns)
    exec(shadow_src or SEG["_shadow_observe_candidate_tiebreak_seat"], ns)
    exec(disprove_src or SEG["_disprove"], ns)
    return ns


# --------------------------------------------------------------------------------------------- static checks
def static_checks(ns: dict) -> list:
    fails = []
    if ns["CANDIDATE_TIEBREAK_URL"] != L1240_SEG["CANDIDATE_URL"]:
        fails.append(f"CANDIDATE_TIEBREAK_URL {ns['CANDIDATE_TIEBREAK_URL']!r} != lab_j1240's own "
                    f"CANDIDATE_URL {L1240_SEG['CANDIDATE_URL']!r}")
    if not ns["_SHADOW_TIEBREAK_SYSTEM"].endswith(L1240_SEG["_TAIL_POLARITY"]):
        fails.append("_SHADOW_TIEBREAK_SYSTEM does not end with lab_j1240's own _TAIL_POLARITY -- "
                    "the arm (c) wording this job's briefing required reusing has drifted")
    prefix_here = ns["_SCOPE_SYSTEM"][: -len(ns["_SCOPE_TAIL_BOOL_FIRST"])]
    if not ns["_SHADOW_TIEBREAK_SYSTEM"].startswith(prefix_here):
        fails.append("_SHADOW_TIEBREAK_SYSTEM's prefix is not _SCOPE_SYSTEM's own prefix")
    if "narrower_claim_earned" not in ns["_SHADOW_TIEBREAK_SYSTEM"] or "scope_only" in \
            ns["_SHADOW_TIEBREAK_SYSTEM"][len(prefix_here):]:
        fails.append("_SHADOW_TIEBREAK_SYSTEM's own tail does not rename the key as expected")
    return fails


# --------------------------------------------------------------------------------------------- scenarios
def R(verdict, how, why=None):
    """A rule_detail() result dict (every key the real one returns)."""
    return {"v1": None, "v2": None, "verdict": verdict, "how": how, "err1": None, "err2": None, "err3": None,
            "why1": None, "why2": None, "why3": None, "why": why}


ORIG = "orig objection why"
UND = "UNDETERMINED"

# name, first rule_detail() result, second rule_detail() result (or None = second call must not happen),
# fake _ask() outcome ("v","why","err","el" or an Exception, or None = _ask must not be called),
# expected _disprove() return (subset), expect_shadow_log (bool)
SCENARIOS = [
    ("first_agreed_false__no_second_no_shadow", R(False, "agreed", "fine"), None, None,
     dict(status="held", how="agreed", scope_how=None), False),
    ("first_tiebreak__no_second_no_shadow", R(True, "tiebreak", "tb"), None, None,
     dict(status=UND, how="tiebreak", scope_how=None), False),
    ("second_agreed_true__no_shadow", R(True, "agreed", ORIG), R(True, "agreed", "narrow"), None,
     dict(status="held_within_scope", objection=["narrow"], how="agreed", scope_how="agreed"), False),
    ("second_agreed_false__no_shadow", R(True, "agreed", ORIG), R(False, "agreed", "none"), None,
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="agreed"), False),
    ("second_unavailable__no_shadow", R(True, "agreed", ORIG), R(None, "unavailable"), None,
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="unavailable"), False),
    # ---- the shadow-observe branch: scope_how == "tiebreak" ----
    ("second_TIEBREAK_true__shadow_fires_gemma_agrees",
     R(True, "agreed", ORIG), R(True, "tiebreak", "tb narrow"), ("v", "gemma:agrees", None, 12.3),
     dict(status="held_within_scope", objection=["tb narrow"], how="agreed", scope_how="tiebreak"), True),
    ("second_TIEBREAK_false__shadow_fires_gemma_disagrees",
     R(True, "agreed", ORIG), R(False, "tiebreak", "tb none"), ("v", "gemma:disagrees", None, 9.8),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="tiebreak"), True),
    # ---- fail-open: the shadow call itself blows up, or returns a value inverted from the real one ----
    ("second_TIEBREAK_true__shadow_ask_raises__real_result_unaffected",
     R(True, "agreed", ORIG), R(True, "tiebreak", "tb narrow"), RuntimeError("gemma hub down"),
     dict(status="held_within_scope", objection=["tb narrow"], how="agreed", scope_how="tiebreak"), True),
    ("second_TIEBREAK_false__shadow_ask_disagrees_with_TIEBREAK__real_result_still_objected",
     # gemma answers the OPPOSITE of what TIEBREAK decided -- a real, plausible disagreement (F-1850's own
     # unanimous-match was 80%, not 100%) -- the real status must still be TIEBREAK's, never gemma's.
     R(True, "agreed", ORIG), R(False, "tiebreak", "tb none"), ("v", "gemma:True, disagrees with live False", None, 15.0),
     dict(status="objected", objection=[ORIG], how="agreed", scope_how="tiebreak"), True),
]


async def _fake_ask_factory(ask_outcome, calls: list):
    async def fake_ask(session, url, system, user, key, timeout=90, num_predict=200):
        calls.append({"url": url, "system": system, "user": user, "key": key, "timeout": timeout})
        if isinstance(ask_outcome, Exception):
            raise ask_outcome
        return ask_outcome
    return fake_ask


def run_scenario(ns: dict, sc, tmp_dir: Path) -> list:
    name, first, second, ask_outcome, exp, expect_shadow_log = sc
    rd_calls: list = []
    ask_calls: list = []
    fails: list = []

    async def fake_rule_detail(system, user, key, context="", num_predict=200):
        rd_calls.append({"system": system, "user": user, "key": key})
        r = first if key == "objection_found" else second
        if r is None:
            raise AssertionError(f"scenario {name}: an unexpected {key!r} rule_detail() call was made")
        return dict(r)

    async def fake_ask(session, url, system, user, key, timeout=90, num_predict=200):
        ask_calls.append({"url": url, "system": system, "user": user, "key": key, "timeout": timeout})
        if ask_outcome is None:
            raise AssertionError(f"scenario {name}: an unexpected _ask() call was made (shadow should not fire)")
        if isinstance(ask_outcome, Exception):
            raise ask_outcome
        return ask_outcome

    log_path = tmp_dir / f"{name}.jsonl"
    ns["_SHADOW_TIEBREAK_LOG"] = log_path

    real_rule_detail, real_ask = jp.rule_detail, jp._ask
    jp.rule_detail, jp._ask = fake_rule_detail, fake_ask
    try:
        try:
            res = asyncio.run(ns["_disprove"]("CLAIM TEXT", ["support one", "support two"]))
        except AssertionError as exc:
            return [str(exc)]
        except Exception as exc:
            # a genuinely broken shadow call (both fail-open layers gone, see mutant M2) propagating
            # all the way out of _disprove() IS the failure this test exists to catch -- report it as
            # a clean FAIL instead of crashing the whole run.
            return [f"_disprove() itself raised {type(exc).__name__}: {exc} "
                   f"(the shadow call must never be able to do this)"]
    finally:
        jp.rule_detail, jp._ask = real_rule_detail, real_ask

    for k, v in exp.items():
        got = res.get(k)
        if got != v:
            fails.append(f"{k}: expected {v!r}, got {got!r}")

    if expect_shadow_log:
        if len(ask_calls) != 1:
            fails.append(f"expected exactly 1 shadow _ask() call, got {len(ask_calls)}")
        else:
            c = ask_calls[0]
            if c["url"] != ns["CANDIDATE_TIEBREAK_URL"]:
                fails.append(f"shadow _ask() hit {c['url']!r}, expected CANDIDATE_TIEBREAK_URL {ns['CANDIDATE_TIEBREAK_URL']!r}")
            if c["key"] != "narrower_claim_earned":
                fails.append(f"shadow _ask() key was {c['key']!r}, expected 'narrower_claim_earned'")
            if c["system"] != ns["_SHADOW_TIEBREAK_SYSTEM"]:
                fails.append("shadow _ask() system prompt is not _SHADOW_TIEBREAK_SYSTEM")
            if rd_calls and c["user"] != rd_calls[-1]["user"]:
                fails.append("shadow _ask() user prompt is not the SAME scope_user the real second call used "
                            "(re-derived instead of reused)")
        if not log_path.exists():
            fails.append("expected a shadow log row to be written, but the log file does not exist")
        else:
            import json
            rows = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            if len(rows) != 1:
                fails.append(f"expected exactly 1 shadow log row, got {len(rows)}")
            else:
                row = rows[0]
                if row.get("live_verdict") != second.get("verdict"):
                    fails.append(f"logged live_verdict {row.get('live_verdict')!r} != real TIEBREAK verdict {second.get('verdict')!r}")
                if row.get("live_why") != second.get("why"):
                    fails.append(f"logged live_why {row.get('live_why')!r} != real TIEBREAK why {second.get('why')!r}")
                if not isinstance(ask_outcome, Exception):
                    if row.get("shadow_verdict") != ask_outcome[0] or row.get("shadow_why") != ask_outcome[1]:
                        fails.append(f"logged shadow_verdict/why {row.get('shadow_verdict')!r}/{row.get('shadow_why')!r} "
                                    f"!= fake _ask() outcome {ask_outcome[0]!r}/{ask_outcome[1]!r}")
                elif not row.get("shadow_err"):
                    fails.append("shadow _ask() raised but the logged row has no shadow_err")
    else:
        if ask_calls:
            fails.append(f"expected 0 shadow _ask() calls, got {len(ask_calls)}")
        if log_path.exists():
            fails.append("expected no shadow log file to be written")
    return fails


def run_all(ns: dict, tmp_dir: Path) -> dict:
    return {sc[0]: run_scenario(ns, sc, tmp_dir) for sc in SCENARIOS}


# --------------------------------------------------------------------------------------------- mutants
def mutate(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, f"mutation anchor not found exactly once: {old!r} ({src.count(old)}x)"
    return src.replace(old, new)


GATE = '    if scope_how == "tiebreak":\n        try:'
CALL_SITE_GUARD = (
    '    if scope_how == "tiebreak":\n'
    '        try:\n'
    '            await _shadow_observe_candidate_tiebreak_seat(claim, scope_user, scope_verdict, scope_why,\n'
    '                                                           context="lab:J-1311_shadow_tiebreak_seat")\n'
    '        except Exception:\n'
    '            pass   # the shadow instrument must never affect the real disprove verdict, ever\n')
CALL_SITE_NO_GUARD = (
    '    if scope_how == "tiebreak":\n'
    '        await _shadow_observe_candidate_tiebreak_seat(claim, scope_user, scope_verdict, scope_why,\n'
    '                                                       context="lab:J-1311_shadow_tiebreak_seat")\n')
HELPER_GUARD = (
    '    try:\n'
    '        async with aiohttp.ClientSession() as session:\n'
    '            v, why, err, el = await _jp._ask(session, CANDIDATE_TIEBREAK_URL, _SHADOW_TIEBREAK_SYSTEM,\n'
    '                                             scope_user, "narrower_claim_earned", timeout=90,\n'
    '                                             num_predict=_jp._NUM_PREDICT)\n'
    '        row["shadow_verdict"], row["shadow_why"] = v, why\n'
    '        row["shadow_err"], row["shadow_elapsed_s"] = err, el\n'
    '    except Exception as exc:\n'
    '        row["shadow_err"] = f"{type(exc).__name__}: {exc}"[:200]\n')
HELPER_NO_GUARD = (
    '    async with aiohttp.ClientSession() as session:\n'
    '        v, why, err, el = await _jp._ask(session, CANDIDATE_TIEBREAK_URL, _SHADOW_TIEBREAK_SYSTEM,\n'
    '                                         scope_user, "narrower_claim_earned", timeout=90,\n'
    '                                         num_predict=_jp._NUM_PREDICT)\n'
    '    row["shadow_verdict"], row["shadow_why"] = v, why\n'
    '    row["shadow_err"], row["shadow_elapsed_s"] = err, el\n')
# (name, disprove_mutator_or_None, shadow_mutator_or_None) -- either mutator may be None (unchanged).
MUTANTS = [
    # the gate fires on every second call, not just tiebreak-decided ones
    ("M1 shadow fires unconditionally (gate removed)",
     lambda s: mutate(s, GATE, '    if True:\n        try:'), None),
    # BOTH fail-open layers removed at once (call site + the helper's own internal guard): a single
    # layer alone can never be killed by a black-box scenario here, because the OTHER layer still
    # catches it -- that is defense-in-depth working as intended, not an untested mutant. Stripping
    # both together is the honest test of "if all shadow fail-open protection were gone, would a
    # broken gemma call corrupt/crash the real disprove path" -- yes, per run_scenario()'s own
    # broadened except Exception clause turning that crash into a clean FAIL.
    ("M2 both fail-open guards removed (call-site try/except AND the helper's own internal one)",
     lambda s: mutate(s, CALL_SITE_GUARD, CALL_SITE_NO_GUARD),
     lambda s: mutate(s, HELPER_GUARD, HELPER_NO_GUARD)),
    # the shadow call is (wrongly) given the bool-first _SCOPE_SYSTEM instead of the polarity one
    ("M3 shadow uses _SCOPE_SYSTEM instead of _SHADOW_TIEBREAK_SYSTEM",
     None, lambda s: mutate(s, "_SHADOW_TIEBREAK_SYSTEM,\n                                             scope_user, \"narrower_claim_earned\"",
                            "_SCOPE_SYSTEM,\n                                             scope_user, \"narrower_claim_earned\"")),
    # the shadow call is (wrongly) given the live TIEBREAK-role key instead of the renamed one
    ("M4 shadow uses key 'scope_only' instead of 'narrower_claim_earned'",
     None, lambda s: mutate(s, '"narrower_claim_earned", timeout=90', '"scope_only", timeout=90')),
]


def main() -> int:
    print("\n[static checks] cross-referencing lab_j1240_tiebreak_seat.py's own already-characterized wording:")
    ns0 = build()
    st = static_checks(ns0)
    for m in st:
        print("  FAIL -", m)
    if not st:
        print("  PASS - CANDIDATE_TIEBREAK_URL and the arm (c) tail both match lab_j1240 byte-for-byte")

    with tempfile.TemporaryDirectory(prefix="j1311_shadow_test_") as tmp:
        tmp_dir = Path(tmp)
        results = run_all(ns0, tmp_dir)
        bad = {k: v for k, v in results.items() if v}
        print(f"\n[scenarios] {len(results) - len(bad)}/{len(results)} pass")
        for k, v in results.items():
            print(("  PASS  " if not v else "  FAIL  ") + k)
            for m in v:
                print("        -", m)
        rc = 0 if (not bad and not st) else 1

        if ARGS.no_mutants:
            return rc
        print("\n[mutation check] each mutant must be KILLED (>=1 scenario fails):")
        survived = []
        for name, disprove_fn, shadow_fn in MUTANTS:
            disprove_src = disprove_fn(SEG["_disprove"]) if disprove_fn else SEG["_disprove"]
            shadow_src = shadow_fn(SEG["_shadow_observe_candidate_tiebreak_seat"]) if shadow_fn \
                else SEG["_shadow_observe_candidate_tiebreak_seat"]
            mutated_ns = build(disprove_src, shadow_src)
            with tempfile.TemporaryDirectory(prefix="j1311_shadow_mutant_") as mtmp:
                r = run_all(mutated_ns, Path(mtmp))
            killed_by = [k for k, v in r.items() if v]
            print(f"  {'KILLED  ' if killed_by else 'SURVIVED'} {name}"
                 + (f"  <- {len(killed_by)} scenario(s): {killed_by[:3]}" if killed_by else ""))
            if not killed_by:
                survived.append(name)
        if survived:
            print("MUTANTS SURVIVED:", survived)
            rc = 1
        print("\nRESULT:", "ALL OK" if rc == 0 else "FAILED")
        return rc


if __name__ == "__main__":
    sys.exit(main())
