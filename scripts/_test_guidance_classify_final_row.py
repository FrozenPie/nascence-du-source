"""
Regression for J-2221 (F-2911): guidance_classify_log.jsonl must carry the POLE-GATE final verdict, not only
classify()'s own pre-gate verdict.

F-2911: the J-1637 classify row is written inside _classify(), before integrate_guidance applies the F1 pole
gate (_self_clash). A gate-forked assimilate -> accommodate/pole_fork was invisible to the D-0328 misfire audit.
J-2221 appends ONE sibling row ({"record": "final", ...}) after the gate. Log-only, fail-open, verdict-neutral.

All stores are temp-path redirects (read side too: _LOG, _BELIEFS, _INTEG_STATE are read from the temp dir).
Canary: Du's real guidance stores (C:\\Nascence\\data and this tree's data/) are hashed before and after.

  [1] pole-gate fork  [2] self, no clash  [3] world accommodate (gate never runs)
  [4] logging failure never changes the verdict  [5] non-live default path refused  [6] canary

  python scripts/_test_guidance_classify_final_row.py     # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/

import asyncio
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                      # noqa: E402  (first -- F-2423)
from core import profile as P                    # noqa: E402
from core import guidance_learning as G          # noqa: E402
from core import judge_panel as _JP              # noqa: E402

# J-3233 / D-0622: integrate_guidance now asks the judge panel a same-lesson question before the pole gate. This test is
# about the pole gate's final row, so the panel is stubbed to "no verdict" (fail-open = the gate runs as before); no hub is
# called. scripts/_test_J-3233_same_lesson_gate.py covers the check itself.
_JP_RULE_ORIG = _JP.rule_detail


async def _no_verdict_panel(*a, **k):
    return {"verdict": None, "how": "unavailable", "v1": None, "v2": None, "hub1": None, "hub2": None, "hub3": None, "why": None}


_JP.rule_detail = _no_verdict_panel

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from this tree ({Path(core.__file__).parent})")

_NAMES = ("guidance_shadow_log.jsonl", "guidance_injection_log.jsonl", "guidance_classify_log.jsonl",
          "guidance_beliefs.json", "guidance_integration_state.json", "guidance_integration_log.jsonl",
          "guidance_contradictions_shadow.jsonl")
_WATCH = {Path(r"C:\Nascence") / "data" / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES}


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_before = {p: _snap(p) for p in _WATCH}
TMP = Path(tempfile.mkdtemp(prefix="J2221_"))
_ORIG = {a: getattr(G, a) for a in ("_LOG", "_INJECT_LOG", "_CLASSIFY_LOG", "_BELIEFS", "_INTEG_STATE",
                                    "_INTEG_LOG", "_CONTRA_LOG", "materialize_promoted_beliefs",
                                    "_semantic_candidate", "_log_classify")}

EXISTING = "commit fully to one direction and hold the chosen self steady"
NEW = "embrace the fluidity of shifting direction and let the chosen self flow"


def _fake_llm(relation: str, clash: bool):
    calls = {"classify": 0, "clash": 0}

    async def call_json(base_urls, sys_prompt, user, **k):
        if sys_prompt is G._CLASSIFY_SYS:
            calls["classify"] += 1
            return {"relation": relation}
        if sys_prompt is G._SELF_CLASH_SYS:
            calls["clash"] += 1
            return {"a_pole": "durable", "b_pole": "fluid" if clash else "durable"}
        return {}
    return call_json, calls


def _setup(d: Path, domain: str):
    d.mkdir(parents=True, exist_ok=True)
    G._LOG, G._INJECT_LOG = d / _NAMES[0], d / _NAMES[1]
    G._CLASSIFY_LOG, G._BELIEFS = d / _NAMES[2], d / _NAMES[3]
    G._INTEG_STATE, G._INTEG_LOG, G._CONTRA_LOG = d / _NAMES[4], d / _NAMES[5], d / _NAMES[6]
    G.materialize_promoted_beliefs = lambda: 0
    G._semantic_candidate = lambda *a, **k: (None, 0.0)
    old = G._new_belief({"ts": 10.0, "domain": domain, "confidence": 0.5}, EXISTING)
    G._BELIEFS.write_text(json.dumps([old]), encoding="utf-8")
    G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
    G._LOG.write_text(json.dumps({"ts": 100.0, "is_guidance": True, "principle": NEW, "scope": "",
                                  "domain": domain, "confidence": 0.6}) + "\n", encoding="utf-8")


def _rows(d: Path):
    p = d / _NAMES[2]
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _run(d, domain, relation, clash):
    _setup(d, domain)
    cj, calls = _fake_llm(relation, clash)
    summary = asyncio.run(G.integrate_guidance(cj, []))
    beliefs = json.loads(G._BELIEFS.read_text(encoding="utf-8"))
    return summary, beliefs, _rows(d), calls


try:
    print("\n[1] self domain, classify=assimilate, pole gate clashes -> fork")
    s, b, rows, calls = _run(TMP / "a", "self", "assimilate", True)
    check(bool(s) and s["accommodated"] == 1 and s["assimilated"] == 0, f"verdict is the pole fork (summary={s})")
    check(len(rows) == 2, f"two rows: classify + final ({len(rows)})")
    c, f = rows[0], rows[1]
    check("record" not in c and c["relation"] == "assimilate" and {"ts", "existing", "new", "relation", "domain"} <= set(c) <= {"ts", "existing", "new", "relation", "domain", "cand_score", "cand_path"},
          "J-1637 classify row shape unchanged (pre-gate assimilate)")
    check(f.get("record") == "final" and f["classify_relation"] == "assimilate" and f["final_relation"] == "accommodate"
          and f["pole_fork"] is True, "final row: assimilate -> accommodate, pole_fork=True")
    check(f["existing"] == c["existing"] and f["new"] == c["new"] and f["domain"] == c["domain"] == "self",
          "final row keyed by the same existing/new/domain as its classify row")
    check(f.get("self_clash") == {"clash": True, "a_pole": "durable", "b_pole": "fluid"}, "self_clash result carried")
    check(len([x for x in b if x.get("status") != "superseded"]) == 2, "both beliefs stand (F1.b fork)")

    print("\n[2] self domain, assimilate, no clash")
    s, b, rows, calls = _run(TMP / "b", "self", "assimilate", False)
    f = rows[-1]
    check(s["assimilated"] == 1 and len(rows) == 2, "assimilated; two rows")
    check(f["final_relation"] == "assimilate" and f["pole_fork"] is False and f["self_clash"]["clash"] is False,
          "final row: assimilate, pole_fork=False, self_clash ran (clash=False)")

    print("\n[3] world domain, classify=accommodate (pole gate never runs)")
    s, b, rows, calls = _run(TMP / "c", "world", "accommodate", True)
    f = rows[-1]
    check(calls["clash"] == 0 and s["accommodated"] == 1, "no _self_clash call; accommodated")
    check(f["classify_relation"] == f["final_relation"] == "accommodate" and f["pole_fork"] is False
          and "self_clash" not in f, "final row: accommodate unchanged, no self_clash key")

    print("\n[4] logging failure never changes the verdict")
    _ref_s, _ref_b, _, _ = _run(TMP / "d0", "self", "assimilate", True)

    def _boom(rec):
        raise RuntimeError("disk on fire")
    G._log_classify = _boom
    s, b, rows, calls = _run(TMP / "d1", "self", "assimilate", True)
    G._log_classify = _ORIG["_log_classify"]
    canon = lambda bs: sorted(json.dumps(x, sort_keys=True) for x in bs)
    check(s == _ref_s and canon(b) == canon(_ref_b), "summary + beliefs identical with the logger raising")
    check(rows == [], "nothing written when the logger fails")

    print("\n[5] non-live process at a default data/ path is refused by the fence")
    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    saved = (P._DATA, P._CANONICAL_DATA, P.LIVE)
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, False
    try:
        G._CLASSIFY_LOG = fake / _NAMES[2]
        G._log_classify({"ts": 1.0, "record": "final", "final_relation": "accommodate", "pole_fork": True})
        check(not (fake / _NAMES[2]).exists(), "final-row write refused (no file created)")
    finally:
        P._DATA, P._CANONICAL_DATA, P.LIVE = saved
finally:
    _JP.rule_detail = _JP_RULE_ORIG
    for a, v in _ORIG.items():
        setattr(G, a, v)
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[6] canary")
check({p: _snap(p) for p in _WATCH} == _before, "Du's real guidance stores untouched (live + this tree)")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAIL(S)")
sys.exit(1 if FAILS else 0)
