"""J-3199 / D-0586: the felt capstone rating no longer feeds the self-model; the closed-book re-derivation is a SHADOW.

Nothing here opens a live store or calls a hub: the author lane and the Emissary are scripted fakes, every file
the code touches (llm_latency, beliefs, book_feelings, essay_lesson log/state) is a temp path.
Run from the worktree:  python scripts/test_j3199_felt_withheld.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import left_lane as ll              # noqa: E402
from core import essay_lesson as el           # noqa: E402
from core import competence, book_feelings, telemetry    # noqa: E402

FAILS: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="J-3199_"))
TITLE = "One Young Man"
NOTES = "\n".join(f"- I read that the clerk drilled with the rifle regiment on day {i} near the river." for i in range(12))
ESSAY = ("## Drill\nThe clerk drilled with the rifle regiment every morning near the river bank in spring. "
         "Short line. Discipline shaped the whole company into a single body of marching men over time.\n"
         "## Supply\nThe regiment depended on river barges for its bread and its powder through the entire winter. "
         "Officers argued bitterly about the cost of feeding so many men during the long cold season. "
         "The quartermaster kept a ledger of every barrel that came upriver after the thaw began.\n"
         "## End\nBy summer the clerk had become a competent soldier who no longer feared the sound of the guns. "
         "His letters home described the camp, the food and the weather in careful and honest detail.\n")


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("  FAIL:", msg)


def test_competence_calibrate_flag():
    bf = TMP / "beliefs.json"
    pe = mock.MagicMock()
    with mock.patch.object(competence, "_BELIEFS_FILE", bf), \
            mock.patch.dict(sys.modules, {"core.prediction_error": pe}), \
            mock.patch.object(competence.profile, "guard_path", lambda p: p):
        competence.record_drill_accuracy("comprehension", 0.6, calibrate=False)
        d = json.loads(bf.read_text())["comprehension"]
        check(d["calib_pairs"] == [] and abs(d["accuracy"] - 0.6) < 1e-9 and d["accuracy_count"] == 1,
              f"calibrate=False moves only the accuracy belief: {d}")
        check(not pe.observe.called, "calibrate=False makes no prediction_error observation")
        competence.record_drill_accuracy("comprehension", 0.7, predicted=0.9)
        d = json.loads(bf.read_text())["comprehension"]
        check(d["calib_pairs"] == [[0.9, 0.7]] and pe.observe.called, f"default still calibrates and observes: {d}")


def test_book_feelings_none():
    store: dict = {}
    with mock.patch.object(book_feelings, "_load", lambda: store), mock.patch.object(book_feelings, "_save", lambda d: None):
        book_feelings.capstone("Book A", 0.2, None, 0.3)
        a = store[book_feelings._key("Book A")]
        check("comprehension_gap" not in a and abs(a["valence"] - 0.35 * 0.2) < 1e-9, f"None -> mood only, no gap: {a}")
        book_feelings.capstone("Book B", 0.2, 0.9, 0.3)
        b = store[book_feelings._key("Book B")]
        check(b["comprehension_gap"] == 0.6 and b["valence"] < a["valence"], f"a float still applies the old term: {b}")


def test_self_predict_logs_lane():
    lat = TMP / "llm_latency.jsonl"
    now = time.time()
    lat.write_text("\n".join(json.dumps(r) for r in (
        {"ts": now - 5000, "model": "old", "node": "11433", "by": "core.essay_lesson:557", "s": 1, "ok": 1},
        {"ts": now + 1, "model": "other", "node": "11433", "by": "core.chapters:370", "s": 1, "ok": 1},
        {"ts": now + 1, "model": "command-r7b", "node": "11441", "by": "core.essay_lesson:557", "s": 2.1, "ok": 1}))
        + "\n", encoding="utf-8")

    async def cj(urls, sysmsg, user, **k):
        return {"grounding": 0.8}

    async def cj_bad(urls, sysmsg, user, **k):
        return {"nothing": 1}

    async def cj_raise(urls, sysmsg, user, **k):
        raise ValueError("exhausted")

    with mock.patch.object(telemetry, "_LAT", lat):
        v = asyncio.run(el.self_predict(cj, ["u"], TITLE, ESSAY))
        f = el._FELT.get(TITLE) or {}
        check(v == 0.8 and f.get("parsed") is True and f["lane"]["model"] == "command-r7b" and f["raw"] == 0.8,
              f"lane + raw + parsed logged, value unchanged: {v} {f}")
        v = asyncio.run(el.self_predict(cj_bad, ["u"], TITLE, ESSAY))
        check(v is None and el._FELT[TITLE]["parsed"] is False, f"a missing key is logged as not parsed, unrated (J-3081): {el._FELT[TITLE]}")
        with mock.patch.object(el, "_FELT_RETRY_PAUSE_S", 0.0):
            v = asyncio.run(el.self_predict(cj_raise, ["u"], TITLE, ESSAY))
        check(v is None and el._FELT[TITLE]["parsed"] is False, "an exception is unrated (J-3081: None, no longer 0.5) and logged as not parsed")
    with mock.patch.object(telemetry, "_LAT", TMP / "missing.jsonl"):
        asyncio.run(el.self_predict(cj, ["u"], TITLE, ESSAY))
        check(el._FELT[TITLE]["lane"] is None, "no telemetry -> lane None, no raise")


def test_pick_claims():
    cl = el._cb_pick_claims(ESSAY)
    check(len(cl) >= 3, f"enough claims picked: {len(cl)}")
    for orig, cue in cl:
        ow, cw = orig.split(), cue.replace(" ...", "").split()
        check(orig.startswith(" ".join(cw)) and len(ow) - len(cw) >= 4 and 4 <= len(cw) <= 12,
              f"cue is a 4-12 word opening with >=4 words hidden: {cue!r} / {orig!r}")
        check(ow[-1] not in cw, f"the claim's ending is not in the cue: {cue!r}")
    check(all("Short line" not in o for o, _ in cl), "a short sentence is not a claim")
    check(el._cb_pick_claims("Too short.") == [], "no claims in a trivial essay")


def _fake_judge(matches):
    async def j(items):
        return {"matches": list(matches)[:len(items)]}
    return j


def test_closed_book_shadow():
    claims = el._cb_pick_claims(ESSAY)
    n = len(claims)
    seen = {}

    async def cj(urls, sysmsg, user, **k):
        seen["user"] = user
        seen["sys"] = sysmsg
        comps = [orig for orig, _ in claims]
        comps[0] = "(cannot recall)"
        return {"completions": comps}

    with mock.patch.object(telemetry, "_LAT", TMP / "none.jsonl"), \
            mock.patch.object(ll, "judge_rederivation", _fake_judge([1.0] * n)):
        r = asyncio.run(el.closed_book_shadow(cj, ["u"], TITLE, NOTES, ESSAY))
    check(r["ok"] and r["n"] == n and r["answered"] == n - 1, f"shape: {r}")
    check(r["matches"][0] == 0.0 and all(m == 1.0 for m in r["matches"][1:]), f"a blank is scored zero without the judge: {r['matches']}")
    check(abs(r["share"] - round((n - 1) / n, 3)) < 1e-9 and r["judge"] == ll.MODEL, f"share = mean match: {r['share']}")
    check(all(o not in seen["user"] for o, _ in claims), "the user prompt carries cues only, never a whole claim or the essay")
    check("Beginnings:" in seen["user"] and NOTES[:40] in seen["user"], "notes + beginnings are what he is given")
    check(not any(ch.isdigit() for ch in seen["sys"].split("Output ONLY")[0]), "no digit anchor in the retrieval prompt")
    check(0.3 < r["cue_frac"] < 0.6, f"cue fraction logged: {r['cue_frac']}")

    async def judge_down(items):
        return None
    with mock.patch.object(ll, "judge_rederivation", judge_down):
        r = asyncio.run(el.closed_book_shadow(cj, ["u"], TITLE, NOTES, ESSAY))
    check(not r["ok"] and r["reason"] == "judge unavailable" and "share" not in r, f"judge down -> no score: {r}")

    async def cj_none(urls, sysmsg, user, **k):
        return {"x": 1}
    r = asyncio.run(el.closed_book_shadow(cj_none, ["u"], TITLE, NOTES, ESSAY))
    check(not r["ok"] and r["reason"] == "no completions parsed", f"unparsed -> reason: {r}")
    r = asyncio.run(el.closed_book_shadow(cj, ["u"], TITLE, NOTES, "A short essay."))
    check(not r["ok"] and "few" in r["reason"], f"too few claims -> reason: {r}")

    async def cj_raise(*a, **k):
        raise RuntimeError("boom")
    r = asyncio.run(el.closed_book_shadow(cj_raise, ["u"], TITLE, NOTES, ESSAY))
    check(not r["ok"] and r["reason"].startswith("error"), f"an exception is a reason, never raised: {r}")


def test_judge_rederivation_parse():
    sent: list = []

    class _Resp:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        def raise_for_status(self): pass
        async def json(self): return {"message": {"content": json.dumps({"items": [{"n": 1, "match": 1}, {"n": 3, "match": 0.5}, {"n": 9, "match": 1}, {"n": 2, "match": "x"}]})}}

    class _S:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        def post(self, url, json=None, timeout=None):
            sent.append(json)
            return _Resp()

    with mock.patch.object(ll.aiohttp, "ClientSession", lambda *a, **k: _S()), mock.patch.object(ll, "_note_call", lambda *a, **k: None):
        r = asyncio.run(ll.judge_rederivation([("a claim", "a completion")] * 3))
    check(r == {"matches": [1.0, None, 0.5]}, f"parsed per item, bad/out-of-range rows skipped: {r}")
    sysmsg = sent[0]["messages"][0]["content"]
    task = ll._REDERIVE_TASK
    check(not any(ch.isdigit() for ch in task), "no digit anchor in the judge prompt")
    check(sent[0]["model"] == ll.MODEL and "ORIGINAL: a claim" in sent[0]["messages"][1]["content"], "Emissary model, original+completion shown")
    check(asyncio.run(ll.judge_rederivation([])) is None, "empty -> None")


def _run_record(flag, shadow_row):
    comp = mock.MagicMock()
    bf = mock.MagicMock()
    el._LOG = TMP / f"log_{flag}.jsonl"
    el._FELT[TITLE] = {"lane": {"model": "command-r7b", "node": "11441", "s": 1.0}, "raw": 0.8, "parsed": True, "seen_chars": 3000}
    if shadow_row is not None:
        el._CLOSED[TITLE] = shadow_row
    with mock.patch.object(el, "_load", lambda: {"history": [], "essayed": []}), \
            mock.patch.object(el, "_save", lambda d: None), \
            mock.patch.object(el, "mark_done", lambda b: None), \
            mock.patch.object(el, "CAPSTONE_GATE", False), \
            mock.patch.object(el, "FELT_FEEDS_SELF_MODEL", flag), \
            mock.patch.object(competence, "record_drill_accuracy", comp.record_drill_accuracy), \
            mock.patch("core.book_feelings.capstone", bf), \
            mock.patch("core.memory.store.store_fragment", return_value="fid"), \
            mock.patch("core.memory.store.store_light_event", return_value=None), \
            mock.patch("core.study.write_tablet", return_value=None), \
            mock.patch("core.world_consolidation.file_book_notes", return_value={}), \
            mock.patch("core.study.archive_book_note_files", return_value={}):
        el.record("b", TITLE, "t", ESSAY, 0.8, 0.6, "f", source_ids=None)
    return comp, bf, json.loads(el._LOG.read_text(encoding="utf-8").splitlines()[-1])


def test_record_flag():
    cb = {"ok": True, "n": 6, "share": 0.5, "strict": 0.33}
    comp, bf, row = _run_record(False, cb)
    args = comp.record_drill_accuracy.call_args
    check(args.args == ("comprehension", 0.6) and args.kwargs == {"calibrate": False},
          f"flag off: measured only, no predicted, calibrate False: {args}")
    check(bf.call_args.args[2] is None, f"flag off: valence term gets predicted=None: {bf.call_args}")
    check(row["predicted"] == 0.8 and row["measured"] == 0.6, "the felt rating is still logged")
    check(row["felt"] == {"lane": {"model": "command-r7b", "node": "11441", "s": 1.0}, "raw": 0.8, "parsed": True,
                          "seen_chars": 3000, "fed": False}, f"felt provenance in the row: {row['felt']}")
    check(row["closed_book"] == cb, f"shadow beside it: {row.get('closed_book')}")
    check(TITLE not in el._FELT and TITLE not in el._CLOSED, "record() consumed the parked values")

    comp, bf, row = _run_record(True, None)
    args = comp.record_drill_accuracy.call_args
    check(args.args == ("comprehension", 0.6) and args.kwargs == {"predicted": 0.8}, f"flag on: the old call, unchanged: {args}")
    check(bf.call_args.args[2] == 0.8 and row["felt"]["fed"] is True and "closed_book" not in row, "flag on: old valence feed; no shadow row when it did not run")


def test_grade_runs_shadow():
    ctx_calls = []

    async def cj(urls, sysmsg, user, **k):
        ctx_calls.append(urls)
        return {"completions": [""] * 6}

    async def fake_grade(title, book_notes, essay, wider_material=""):
        return {"grounded": 0.7, "grounded_wider": 0.7, "feedback": "f", "chars": {}}

    async def self_pred():
        with mock.patch.object(telemetry, "_LAT", TMP / "none.jsonl"):
            await el.self_predict(lambda *a, **k: asyncio.sleep(0, {"grounding": 0.5}), ["u"], TITLE, ESSAY)
    el._CB_CTX.clear()
    el._CB_CTX[TITLE] = (cj, ["lane"])
    with mock.patch.object(ll, "grade_essay", fake_grade), mock.patch.object(telemetry, "_LAT", TMP / "none.jsonl"):
        score, fb = asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    r = el._CLOSED.get(TITLE)
    check((score, fb) == (0.7, "f"), "the grade is unchanged by the shadow")
    check(ctx_calls == [["lane"]] and r is not None and r["ok"] and r["share"] == 0.0 and r["judge"] is None, f"shadow ran on the author lane self_predict was handed: {r}")
    el._CLOSED.clear()

    async def none_grade(*a, **k): return None
    el._CB_CTX[TITLE] = (cj, ["lane"])
    ctx_calls.clear()
    with mock.patch.object(ll, "grade_essay", none_grade):
        asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    check(not ctx_calls and TITLE not in el._CLOSED, "Emissary down -> no shadow step (it is the judge too)")

    async def slow_cb(*a, **k):
        await asyncio.sleep(5)
    el._CB_CTX[TITLE] = (cj, ["lane"])
    with mock.patch.object(ll, "grade_essay", fake_grade), mock.patch.object(el, "closed_book_shadow", slow_cb), \
            mock.patch.object(el, "_CB_TIMEOUT_S", 0.05):
        score, fb = asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    check(score == 0.7 and (el._CLOSED.get(TITLE) or {}).get("ok") is False, f"a stuck shadow is cut off, grade intact: {el._CLOSED.get(TITLE)}")
    el._CLOSED.clear()
    with mock.patch.object(el, "CLOSED_BOOK_SHADOW", False), mock.patch.object(ll, "grade_essay", fake_grade):
        el._CB_CTX[TITLE] = (cj, ["lane"])
        asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    check(TITLE not in el._CLOSED, "CLOSED_BOOK_SHADOW False -> nothing runs")


if __name__ == "__main__":
    for t in (test_competence_calibrate_flag, test_book_feelings_none, test_self_predict_logs_lane, test_pick_claims,
              test_closed_book_shadow, test_judge_rederivation_parse, test_record_flag, test_grade_runs_shadow):
        print("RUN", t.__name__)
        try:
            t()
        except Exception as exc:                # noqa: BLE001
            import traceback; traceback.print_exc()
            FAILS.append(f"{t.__name__} raised {exc!r}")
    print("FAILS:", FAILS if FAILS else "none")
    sys.exit(1 if FAILS else 0)
