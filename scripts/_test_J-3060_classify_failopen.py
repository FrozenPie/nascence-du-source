"""
J-3060 (F-3772, P-0018): _classify must not fail open to "assimilate".

  [1] call_json -> None / "{}" / garbage / non-dict / raising: relation is "unrelated", failed=True, reason set,
      NEVER "assimilate"; the classify log row carries failed + reason (exception case is now logged too)
  [2] a genuine verdict still passes through unchanged and carries no failed/reason
  [3] cand_score / cand_path land on the classify row (and are absent when not passed: old rows stay comparable)
  [4] integrate_guidance end to end: a failed classify makes the lesson its OWN tentative belief; corroboration of the
      candidate is NOT raised, nothing promoted; the final row carries classify_failed + classify_reason; cand_path
      is "lexical" when the lexical pass found the candidate
  [5] _CLASSIFY_SYS is byte-identical to master's (D-0328: this job must not touch the prompt)
  [6] canary: real guidance stores untouched

  python scripts/_test_J-3060_classify_failopen.py     # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/

import asyncio
import hashlib
import json
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

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core imported from this tree")


async def _no_verdict_panel(*a, **k):
    return {"verdict": None, "how": "unavailable", "v1": None, "v2": None, "hub1": None, "hub2": None, "hub3": None, "why": None}


_JP.rule_detail = _no_verdict_panel

_NAMES = ("guidance_shadow_log.jsonl", "guidance_injection_log.jsonl", "guidance_classify_log.jsonl",
          "guidance_beliefs.json", "guidance_integration_state.json", "guidance_integration_log.jsonl",
          "guidance_contradictions_shadow.jsonl")
_WATCH = {Path(r"C:\Nascence") / "data" / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES}


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_before = {p: _snap(p) for p in _WATCH}
TMP = Path(tempfile.mkdtemp(prefix="J3060_"))
_ORIG = {a: getattr(G, a) for a in ("_LOG", "_INJECT_LOG", "_CLASSIFY_LOG", "_BELIEFS", "_INTEG_STATE",
                                    "_INTEG_LOG", "_CONTRA_LOG", "materialize_promoted_beliefs", "_semantic_candidate")}

EXISTING = "commit fully to one direction and hold the chosen self steady"
NEW = "commit fully to one direction and keep the chosen self steady through doubt"


def _redirect(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    G._LOG, G._INJECT_LOG = d / _NAMES[0], d / _NAMES[1]
    G._CLASSIFY_LOG, G._BELIEFS = d / _NAMES[2], d / _NAMES[3]
    G._INTEG_STATE, G._INTEG_LOG, G._CONTRA_LOG = d / _NAMES[4], d / _NAMES[5], d / _NAMES[6]
    G.materialize_promoted_beliefs = lambda: 0
    G._semantic_candidate = lambda *a, **k: (None, 0.0)


def _rows(d: Path):
    p = d / _NAMES[2]
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _stub(reply):
    async def call_json(base_urls, sys_prompt, user, **k):
        if reply == "RAISE":
            raise RuntimeError("hub down")
        return reply
    return call_json


try:
    print("\n[1] failure shapes never return assimilate")
    for label, reply, want in (("None", None, "bad_reply"), ("empty dict", {}, "bad_reply"),
                               ("garbage str", "assimilate please", "bad_reply"),
                               ("unknown relation", {"relation": "maybe"}, "bad_reply"),
                               ("raise", "RAISE", "exception")):
        d = TMP / ("f_" + label.replace(" ", "_"))
        _redirect(d)
        out = asyncio.run(G._classify(_stub(reply), [], EXISTING, NEW, "self"))
        rows = _rows(d)
        check(out.get("relation") == "unrelated" and out.get("failed") is True and out.get("reason") == want,
              f"{label}: unrelated + failed + reason={want} (got {out})")
        check(len(rows) == 1 and rows[0].get("failed") is True and rows[0].get("reason") == want
              and rows[0]["relation"] == "unrelated", f"{label}: logged once with failed/reason ({rows})")

    print("\n[2] genuine verdicts unchanged")
    for rel in ("assimilate", "accommodate", "unrelated"):
        d = TMP / ("g_" + rel)
        _redirect(d)
        out = asyncio.run(G._classify(_stub({"relation": " " + rel.upper() + " "}), [], EXISTING, NEW, "world"))
        rows = _rows(d)
        check(out == {"relation": rel}, f"{rel}: returned as-is, no failed/reason ({out})")
        check(len(rows) == 1 and "failed" not in rows[0] and "reason" not in rows[0] and rows[0]["relation"] == rel,
              f"{rel}: row has no failure marks")

    print("\n[3] cand_score / cand_path on the row")
    d = TMP / "c1"
    _redirect(d)
    asyncio.run(G._classify(_stub({"relation": "assimilate"}), [], EXISTING, NEW, "self", cand_score=0.34567891, cand_path="semantic"))
    r = _rows(d)[0]
    check(r.get("cand_score") == 0.3457 and r.get("cand_path") == "semantic", f"score/path logged ({r})")
    d = TMP / "c2"
    _redirect(d)
    asyncio.run(G._classify(_stub({"relation": "assimilate"}), [], EXISTING, NEW, "self"))
    r = _rows(d)[0]
    check(set(r) == {"ts", "existing", "new", "relation", "domain"}, f"old row shape when not passed ({sorted(r)})")

    print("\n[4] integrate_guidance end to end, classify failing")
    for label, reply, want in (("bad_reply", None, "bad_reply"), ("exception", "RAISE", "exception")):
        d = TMP / ("e_" + label)
        _redirect(d)
        old = G._new_belief({"ts": 10.0, "domain": "self", "confidence": 0.5}, EXISTING)
        G._BELIEFS.write_text(json.dumps([old]), encoding="utf-8")
        G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
        G._LOG.write_text(json.dumps({"ts": 100.0, "is_guidance": True, "principle": NEW, "scope": "",
                                      "domain": "self", "confidence": 0.6}) + "\n", encoding="utf-8")
        s = asyncio.run(G.integrate_guidance(_stub(reply), []))
        beliefs = json.loads(G._BELIEFS.read_text(encoding="utf-8"))
        rows = _rows(d)
        check(bool(s) and s["assimilated"] == 0 and s["new"] == 1 and s["promoted"] == 0, f"{label}: own new belief, nothing assimilated/promoted ({s})")
        check(len(beliefs) == 2 and beliefs[0]["corroboration_count"] == 1 and beliefs[0]["status"] == "tentative",
              f"{label}: candidate corroboration NOT raised, still tentative")
        c = [x for x in rows if "record" not in x]
        f = [x for x in rows if x.get("record") == "final"]
        check(len(c) == 1 and c[0].get("reason") == want and c[0].get("cand_path") == "lexical"
              and isinstance(c[0].get("cand_score"), float) and c[0]["cand_score"] >= G._SIM_RELATED,
              f"{label}: classify row has reason, cand_path=lexical, cand_score ({c})")
        check(len(f) == 1 and f[0].get("classify_failed") is True and f[0].get("classify_reason") == want
              and f[0]["final_relation"] == "unrelated", f"{label}: final row marks the failure ({f})")

    print("\n[5] prompt untouched (D-0328)")
    import subprocess
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", "master:core/guidance_learning.py"],
                             capture_output=True, text=True, encoding="utf-8", timeout=30).stdout
        if "_CLASSIFY_SYS = (" in src:
            ns = {}
            start = src.index("_CLASSIFY_SYS = (")
            end = src.index("\n)\n", start) + 3
            exec(src[start:end], ns)
            check(ns["_CLASSIFY_SYS"] == G._CLASSIFY_SYS, "_CLASSIFY_SYS identical to master's")
        else:
            check(False, "could not read master's _CLASSIFY_SYS")
    except Exception as exc:
        check(False, f"git show failed: {exc}")
finally:
    for a, v in _ORIG.items():
        setattr(G, a, v)

print("\n[6] canary")
check(all(_snap(p) == _before[p] for p in _WATCH), "real guidance stores untouched (live + this tree)")
print("\nALL OK" if not FAILS else f"\n{FAILS} FAIL(S)")
sys.exit(1 if FAILS else 0)
