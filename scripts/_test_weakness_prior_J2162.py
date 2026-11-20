"""
_test_weakness_prior_J2162.py -- J-2162 (D-0436 A): core/weakness_prior.py + its book_selection / school hooks.

Isolation: core is imported BEFORE lab_env; every path global (weakness_prior._LOG/_BELIEFS, book_selection
COVERAGE/LOG/META, school STATE) is redirected into a temp dir; reading_history and _interest_terms are
stubbed so nothing reads live data. Exit 1 on any failed check.
Run: python -X utf8 scripts/_test_weakness_prior_J2162.py
"""
from __future__ import annotations

import json
import random
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402
from core import weakness_prior as wp, book_selection as bs, school, reading_history  # noqa: E402
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__

FAIL: list[str] = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


BELIEFS = {
    "paradox_holding": {"confidence": 0.79, "evidence_count": 937, "accuracy": None},
    "fieldcraft": {"confidence": 0.5, "evidence_count": 0, "accuracy": 1.0},      # zero evidence: ignored
    "mathematics": {"confidence": 0.81, "evidence_count": 81, "accuracy": 0.9998},
    "observation": {"confidence": 0.81, "evidence_count": 178, "accuracy": 0.459},
    "history_culture": {"confidence": 0.80, "evidence_count": 263, "accuracy": 0.2},
}
ROWS = [{"title": f"History of Place {i}", "subjects": "{'History'}", "downloads": 100 + i, "language": "['en']",
         "type": "Text"} for i in range(5)] + \
       [{"title": f"Cookery {i}", "subjects": "{'Cooking'}", "downloads": 100 + i, "language": "['en']",
         "type": "Text"} for i in range(40)]

tmp = Path(tempfile.mkdtemp(prefix="J-2162_"))
with mock.patch.object(wp, "_LOG", tmp / "weak.jsonl"), mock.patch.object(wp, "_lab", lambda: False), \
        mock.patch.object(bs, "COVERAGE", tmp / "cov.json"), mock.patch.object(bs, "LOG", tmp / "bs.jsonl"), \
        mock.patch.object(bs, "META", tmp / "meta.csv"), mock.patch.object(school, "STATE", tmp / "school.json"), \
        mock.patch.object(bs, "_rows", lambda: iter([dict(r) for r in ROWS])), \
        mock.patch.object(bs, "_interest_terms", lambda: set()), \
        mock.patch.object(reading_history, "shelf_keys", lambda: set()), \
        mock.patch.object(reading_history, "is_known", lambda t, k: False):
    (tmp / "meta.csv").write_text("x")

    # --- weakest_domain
    check("weakest = lowest graded accuracy", wp.weakest_domain(BELIEFS) == ("history_culture", 0.2))
    check("ungraded / zero-evidence domains skipped",
          wp.weakest_domain({"a": {"accuracy": None, "evidence_count": 5}, "b": {"accuracy": 0.1, "evidence_count": 0}}) is None)
    check("garbage beliefs -> None, no raise", wp.weakest_domain({"x": 3}) is None)

    # --- prior 0: weights returned IS the input, slot named for shadow
    w = [(r, 1.0) for r in ROWS]
    out, slot = wp.apply_to_weighted(w, BELIEFS)
    check("prior 0.0: weighted list untouched (identity)", out is w)
    check("prior 0.0: slot is a history book", slot is not None and "History" in slot["title"])

    # --- prior > 0: bounded, not forced
    with mock.patch.object(wp, "WEAKNESS_PRIOR", 0.2):
        out, slot = wp.apply_to_weighted(w, BELIEFS)
        tot = sum(x for _, x in out)
        sw = [x for r, x in out if r is slot][0]
        check("prior 0.2: slot mass ~ 0.2 of draw", abs(sw / tot - (1 + 45 * 0.25) * 0 - sw / tot) < 1 and 0.19 < sw / tot < 0.30,
              f"{sw/tot:.3f}")
        check("prior 0.2: others unchanged", all(x == 1.0 for r, x in out if r is not slot))
    with mock.patch.object(wp, "WEAKNESS_PRIOR", 5.0):
        check("prior clamped (never forced)", wp._prior() == wp.MAX_PRIOR < 0.5)
        out, slot = wp.apply_to_weighted(w, BELIEFS)
        sw = [x for r, x in out if r is slot][0]
        check("clamped: slot mass < 1", sw / sum(x for _, x in out) < 0.6)

    # --- no book analogue / no candidate -> neutral
    out, slot = wp.apply_to_weighted(w, {"fieldcraft": {"accuracy": 0.0, "evidence_count": 3}})
    check("domain with no shelf analogue -> no slot", slot is None and out is w)
    out, slot = wp.apply_to_weighted([(r, 1.0) for r in ROWS[5:]], BELIEFS)
    check("no matching candidate -> no slot", slot is None)

    # --- fail-open
    with mock.patch.object(wp, "weakest_domain", side_effect=RuntimeError("boom")):
        out, slot = wp.apply_to_weighted(w, BELIEFS)
        check("fail-open on internal error", out is w and slot is None)

    # --- select_explore integration, prior 0: log row + no key leakage into the pick rows
    with mock.patch.object(wp, "weakest_domain", lambda b=None: ("history_culture", 0.2)):
        random.seed(1)
        picks = bs.select_explore(1)
    check("select_explore still returns a pick", len(picks) == 1)
    check("pick row has no weakness keys", set(picks[0]) == set(ROWS[0]) and "weak" not in json.dumps(picks[0]).lower())
    rows = [json.loads(x) for x in (tmp / "weak.jsonl").read_text().splitlines()]
    check("book shadow row logged", len(rows) == 1 and rows[0]["arm"] == "book" and rows[0]["prior"] == 0.0)
    check("shadow row records slot + match flag", rows[0]["slot_title"] and isinstance(rows[0]["matched"], bool))

    # --- prior 0 doesn't change the draw distribution: same seed, hook on vs hook neutralised
    with mock.patch.object(wp, "weakest_domain", lambda b=None: ("history_culture", 0.2)):
        random.seed(7); a = [bs.select_explore(1)[0]["title"] for _ in range(30)]
    with mock.patch.object(wp, "apply_to_weighted", lambda w, b=None: (w, None)):
        random.seed(7); b = [bs.select_explore(1)[0]["title"] for _ in range(30)]
    check("prior 0.0 draw sequence identical to no-hook baseline", a == b)

    # --- prior > 0 raises the history pick rate, but never to 100%
    def rate():
        n = 0
        random.seed(3)
        for _ in range(400):
            n += "History" in bs.select_explore(1)[0]["title"]
        return n / 400
    with mock.patch.object(wp, "weakest_domain", lambda b=None: ("history_culture", 0.2)):
        base = rate()
        with mock.patch.object(wp, "WEAKNESS_PRIOR", 0.3):
            lifted = rate()
    check("prior 0.3 lifts slot pick rate but is not forced", base < lifted < 0.9, f"{base:.2f}->{lifted:.2f}")

    # --- select_explore survives a broken module (fail-open)
    with mock.patch.object(wp, "apply_to_weighted", side_effect=RuntimeError("x")), \
            mock.patch.object(wp, "log_book_pick", side_effect=RuntimeError("y")):
        check("select_explore fail-open when hooks raise", len(bs.select_explore(1)) == 1)

    # --- school shadow: logged once per period, directive unchanged
    n0 = len((tmp / "weak.jsonl").read_text().splitlines())
    with mock.patch.object(wp, "weakest_domain", lambda b=None: ("mathematics", 0.1)):
        wp._LAST_SCHOOL_KEY[0] = None
        s1 = wp.school_shadow("reading", now=1_760_000_000)
        wp.school_shadow("reading", now=1_760_000_100)
        wp.school_shadow("math", now=1_760_003_000)
    lines = (tmp / "weak.jsonl").read_text().splitlines()
    check("school shadow maps domain->subject", s1 == "math")
    check("school shadow deduped per period", len(lines) - n0 == 2, str(len(lines) - n0))
    last = json.loads(lines[-1])
    check("school row matched flag", last["arm"] == "school" and last["matched"] is True)
    with mock.patch.object(school, "current_subject", lambda now=None: "math"):
        d1 = school.directive()
    with mock.patch.object(wp, "school_shadow", side_effect=RuntimeError("z")), \
            mock.patch.object(school, "current_subject", lambda now=None: "math"):
        d2 = school.directive()
    check("school.directive unchanged by (and fail-open on) the shadow hook", d1 == d2 and "weak" not in d1.lower())

    # --- lab mode writes nothing
    n = len((tmp / "weak.jsonl").read_text().splitlines())
    with mock.patch.object(wp, "_lab", lambda: True):
        wp.log_book_pick(None, [])
    check("lab mode writes nothing", len((tmp / "weak.jsonl").read_text().splitlines()) == n)

    # --- real beliefs file loads and has a weakest domain (read-only)
    live = wp.weakest_domain()
    check("live beliefs readable (read-only)", live is None or isinstance(live[0], str), str(live))

print(f"\n{'ALL PASS' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
sys.exit(1 if FAIL else 0)
