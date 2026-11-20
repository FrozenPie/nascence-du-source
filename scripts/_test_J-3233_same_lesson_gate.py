"""
J-3233 / D-0622: the same-lesson check runs BEFORE the pole gate in core/guidance_learning.integrate_guidance.

Ruling (founder 2026-11-02): run the pole gate only after a check from another model family says the pair is NOT the same
lesson restated; duplicates corroborate, only distinct opposed lessons fork; the positive control (real river-versus-built-
self opposites) must still fork; fail open to today's behaviour; log the verdict.

The judge panel is stubbed (core.judge_panel.rule_detail) and so is the classify/pole model (call_json), so no hub is
called. Every store path is a temp-dir redirect; Du's real guidance stores are hashed before and after (canary).

  [1] prompt contract   [2] judge family is not _classify's   [3] positive control still forks
  [4] duplicate corroborates, gate never runs   [5] fail open (no verdict / judge raises) -> today's gate
  [6] kill switch + gate-entry conditions (world / classify=accommodate)   [7] reader   [8] canary

  python scripts/_test_J-3233_same_lesson_gate.py     # exit 0 = ALL OK
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
from core import guidance_learning as G          # noqa: E402
from core import judge_panel as JP               # noqa: E402

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
_WATCH = {Path(r"C:\Nascence") / "data" / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES} \
    | {ROOT / "data" / "judge_panel_log.jsonl", Path(r"C:\Nascence") / "data" / "judge_panel_log.jsonl"}


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_before = {p: _snap(p) for p in _WATCH}
TMP = Path(tempfile.mkdtemp(prefix="J3233_"))
_ORIG = {a: getattr(G, a) for a in ("_LOG", "_INJECT_LOG", "_CLASSIFY_LOG", "_BELIEFS", "_INTEG_STATE", "_INTEG_LOG",
                                    "_CONTRA_LOG", "materialize_promoted_beliefs", "_semantic_candidate",
                                    "SAME_LESSON_CHECK_ENABLED")}
_ORIG_RULE = JP.rule_detail

# the positive control (F-3790, quoted) and a restated pair (F-3790, quoted)
RIVER_A = "I am not my changing viewpoints but the constant observer that holds them"
RIVER_B = "I am a transient flow within an endless current of time"
DUP_A = "My core identity remains fundamentally stable"
DUP_B = "My sense of self and identity remains constant"


def _fake_llm(relation="assimilate", clash=True):
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


def _stub_judge(verdict, how="agreed", raise_it=False):
    seen = []

    async def rule_detail(system, user, key, context="", **kw):
        seen.append({"system": system, "user": user, "key": key, "context": context})
        if raise_it:
            raise RuntimeError("panel on fire")
        return {"verdict": verdict, "how": how, "v1": verdict, "v2": verdict, "hub1": "11438", "hub2": "11440",
                "hub3": None, "why": "stub"}
    JP.rule_detail = rule_detail
    return seen


def _setup(d: Path, domain: str, existing: str, new: str):
    d.mkdir(parents=True, exist_ok=True)
    G._LOG, G._INJECT_LOG = d / _NAMES[0], d / _NAMES[1]
    G._CLASSIFY_LOG, G._BELIEFS = d / _NAMES[2], d / _NAMES[3]
    G._INTEG_STATE, G._INTEG_LOG, G._CONTRA_LOG = d / _NAMES[4], d / _NAMES[5], d / _NAMES[6]
    G.materialize_promoted_beliefs = lambda: 0
    # the quoted river/observer pair shares almost no words, so the lexical prefilter alone would not pair it; in
    # production the semantic fallback (J-1640) supplies the candidate. Stub that fallback to supply the held belief.
    G._semantic_candidate = lambda text, beliefs, dom: (beliefs[0], 0.9) if beliefs else (None, 0.0)
    old = G._new_belief({"ts": 10.0, "domain": domain, "confidence": 0.5}, existing)
    G._BELIEFS.write_text(json.dumps([old]), encoding="utf-8")
    G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
    G._LOG.write_text(json.dumps({"ts": 100.0, "is_guidance": True, "principle": new, "scope": "",
                                  "domain": domain, "confidence": 0.6}) + "\n", encoding="utf-8")


def _rows(d: Path):
    p = d / _NAMES[2]
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _run(d, domain, existing, new, relation="assimilate", clash=True):
    _setup(d, domain, existing, new)
    cj, calls = _fake_llm(relation, clash)
    summary = asyncio.run(G.integrate_guidance(cj, []))
    beliefs = json.loads(G._BELIEFS.read_text(encoding="utf-8"))
    return summary, beliefs, _rows(d), calls


try:
    print("\n[1] prompt contract")
    sysmsg = G._SAME_LESSON_SYS
    check("<true or false>" in sysmsg and '"same_lesson": true' not in sysmsg and '"same_lesson": false' not in sysmsg,
          "schema line does not pre-fill an answer (F-3790 defect a)")
    check("OPPOSITE" in sysmsg and "NOT the same lesson" in sysmsg, "an opposed pair is named as NOT the same lesson")
    check(G.SAME_LESSON_CHECK_ENABLED is True, "check is on by default (the ruling is to implement it; kill switch exists)")
    seen = _stub_judge(True)
    r = asyncio.run(G._same_lesson(RIVER_A, RIVER_B))
    check(len(seen) == 1 and seen[0]["key"] == "same_lesson" and seen[0]["system"] is G._SAME_LESSON_SYS
          and seen[0]["user"] == f"A:\n\"{RIVER_A}\"\n\nB:\n\"{RIVER_B}\"" and seen[0]["context"] == "guidance_same_lesson",
          "one panel call, key=same_lesson, user message is A/B")
    check(r["same"] is True and r["how"] == "agreed" and r["hub1"] == "11438", f"verdict mapped ({r})")

    print("\n[2] the judge family is not _classify's")
    ports = {u.rsplit(":", 1)[-1] for u in (JP.JUDGE_1, JP.JUDGE_2, JP.TIEBREAK)}
    check("11441" not in ports, f"panel hubs {sorted(ports)} exclude the :11441 command-r7b lane _classify/_self_clash use")
    check(len({JP.JUDGE_1, JP.JUDGE_2, JP.TIEBREAK}) == 3, "three distinct judge hubs")

    print("\n[3] POSITIVE CONTROL: river vs built self, judge says not-the-same -> the pole gate runs and FORKS")
    seen = _stub_judge(False)
    s, b, rows, calls = _run(TMP / "a", "self", RIVER_A, RIVER_B, clash=True)
    check(len(seen) == 1 and calls["clash"] == 1, f"judge asked once, pole gate ran once (judge={len(seen)}, clash={calls['clash']})")
    check(s["accommodated"] == 1 and s["assimilated"] == 0, f"still forks (summary={s})")
    check(len([x for x in b if x.get("status") != "superseded"]) == 2, "both beliefs stand (F1.b fork)")
    f = rows[-1]
    check(f.get("record") == "final" and f["pole_fork"] is True and f["final_relation"] == "accommodate"
          and f["same_lesson"]["same"] is False and f["pole_gate_skipped"] is False and f["self_clash"]["clash"] is True,
          "final row: same_lesson False logged, gate not skipped, pole_fork True")

    print("\n[4] DUPLICATE: judge says same -> corroborates, the pole gate never runs (even though it would clash)")
    seen = _stub_judge(True)
    s, b, rows, calls = _run(TMP / "b", "self", DUP_A, DUP_B, clash=True)
    check(calls["clash"] == 0, "_self_clash was NOT called")
    check(s["assimilated"] == 1 and s["accommodated"] == 0 and s["new"] == 0, f"assimilated (summary={s})")
    check(len(b) == 1 and b[0]["corroboration_count"] == 2 and b[0]["status"] == "promoted",
          "one belief, corroboration 2, promoted")
    f = rows[-1]
    check(f["final_relation"] == "assimilate" and f["pole_fork"] is False and f["pole_gate_skipped"] is True
          and f["same_lesson"]["same"] is True and "self_clash" not in f, "final row: gate skipped, same_lesson True, no self_clash")

    print("\n[5] FAIL OPEN: no verdict / judge raises -> the pole gate runs exactly as before")
    for tag, kw in (("no-verdict", dict(verdict=None, how="unavailable")),
                    ("split-no-tiebreak", dict(verdict=None, how="split_no_tiebreak")),
                    ("raises", dict(verdict=True, raise_it=True))):
        _stub_judge(**kw)
        s, b, rows, calls = _run(TMP / ("c_" + tag), "self", DUP_A, DUP_B, clash=True)
        f = rows[-1]
        check(calls["clash"] == 1 and s["accommodated"] == 1 and f["pole_fork"] is True and f["pole_gate_skipped"] is False,
              f"{tag}: gate ran and forked as today (clash calls={calls['clash']})")
        check(f["same_lesson"]["same"] is None, f"{tag}: same_lesson logged as None ({f['same_lesson']})")
    _stub_judge(verdict=None, how="unavailable")
    s, b, rows, calls = _run(TMP / "c_noclash", "self", DUP_A, DUP_B, clash=False)
    check(s["assimilated"] == 1 and calls["clash"] == 1, "no verdict + gate says no clash -> assimilate (today's behaviour)")

    print("\n[5b] a hung panel is capped and fails open")

    async def _hang(*a, **k):
        await asyncio.sleep(30)
    JP.rule_detail = _hang
    _T0 = G._SAME_LESSON_TIMEOUT_S
    G._SAME_LESSON_TIMEOUT_S = 0.2
    import time as _time
    _t0 = _time.monotonic()
    r = asyncio.run(G._same_lesson(DUP_A, DUP_B))
    G._SAME_LESSON_TIMEOUT_S = _T0
    check(r["same"] is None and _time.monotonic() - _t0 < 5, f"hung judge -> no verdict within the cap ({r})")

    print("\n[6] kill switch and gate-entry conditions")
    seen = _stub_judge(True)
    G.SAME_LESSON_CHECK_ENABLED = False
    s, b, rows, calls = _run(TMP / "d", "self", DUP_A, DUP_B, clash=True)
    G.SAME_LESSON_CHECK_ENABLED = _ORIG["SAME_LESSON_CHECK_ENABLED"]
    check(not seen and calls["clash"] == 1 and s["accommodated"] == 1 and "same_lesson" not in rows[-1],
          "switch off: judge not called, gate runs, no same_lesson key (byte-for-byte today)")
    seen = _stub_judge(True)
    s, b, rows, calls = _run(TMP / "e", "world", DUP_A, DUP_B, clash=True)
    check(not seen and calls["clash"] == 0 and "same_lesson" not in rows[-1], "world domain: no judge call, no gate")
    seen = _stub_judge(True)
    s, b, rows, calls = _run(TMP / "f", "self", DUP_A, DUP_B, relation="accommodate", clash=True)
    check(not seen and calls["clash"] == 0 and s["accommodated"] == 1 and "same_lesson" not in rows[-1],
          "classify=accommodate (F1.c fork path): judge not called, untouched")

    print("\n[7] reader (same_lesson_status) over the temp classify log")
    G._CLASSIFY_LOG = TMP / "reader.jsonl"
    lines = [
        {"ts": 1, "existing": "x", "new": "y", "relation": "assimilate", "domain": "self"},                      # classify row: ignored
        {"ts": 2, "record": "final", "domain": "self", "classify_relation": "assimilate", "pole_fork": True},    # legacy: counted, no check
        {"ts": 3, "record": "final", "domain": "self", "classify_relation": "assimilate", "pole_fork": False,
         "same_lesson": {"same": True}, "pole_gate_skipped": True},
        {"ts": 4, "record": "final", "domain": "self", "classify_relation": "assimilate", "pole_fork": True,
         "same_lesson": {"same": False}, "pole_gate_skipped": False},
        {"ts": 5, "record": "final", "domain": "self", "classify_relation": "assimilate", "pole_fork": True,
         "same_lesson": {"same": None}, "pole_gate_skipped": False},
        {"ts": 6, "record": "final", "domain": "world", "classify_relation": "assimilate", "pole_fork": False},  # world: ignored
        {"ts": 7, "record": "final", "domain": "self", "classify_relation": "accommodate", "pole_fork": False},  # not assimilate: ignored
    ]
    G._CLASSIFY_LOG.write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n", encoding="utf-8")
    st = G.same_lesson_status()
    check(st["self_assimilate_pairs"] == 4 and st["checked"] == 3 and st["same_true"] == 1 and st["same_false"] == 1
          and st["same_none"] == 1 and st["gate_skipped"] == 1 and st["pole_forks"] == 3 and st["fork_rate"] == 0.75,
          f"counts and fork rate ({st})")
    st2 = G.same_lesson_status(since_ts=2.5)
    check(st2["self_assimilate_pairs"] == 3 and st2["fork_rate"] == 0.667, f"since_ts filter ({st2})")
    G._CLASSIFY_LOG = TMP / "absent.jsonl"
    check(G.same_lesson_status()["fork_rate"] is None, "missing log reads as empty, never raises")
finally:
    JP.rule_detail = _ORIG_RULE
    for a, v in _ORIG.items():
        setattr(G, a, v)
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[8] canary")
check({p: _snap(p) for p in _WATCH} == _before, "Du's real guidance stores and judge_panel_log untouched (live + this tree)")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAIL(S)")
sys.exit(1 if FAILS else 0)
