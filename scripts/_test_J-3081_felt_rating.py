"""J-3081 (F-3791 / F-3792): the felt capstone rating is lane-independent, observable, null on failure.

Nothing here opens a live store or calls a hub: call_json is a scripted fake, every file the code touches
(llm_latency, essay_lesson log/state) is a temp path. Run from the worktree:
    python scripts/_test_J-3081_felt_rating.py
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
from core import essay_lesson as el           # noqa: E402
from core import competence, telemetry         # noqa: E402

FAILS: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="J-3081_"))
TITLE = "One Young Man"
BG, HOT = "http://bg.test:11441", "http://hot.test:11433"
CHAIN = [BG, HOT]


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("  FAIL:", msg)


def _essay(n_chars: int) -> str:
    out, i = ["# Opening\n"], 0
    while sum(len(x) for x in out) < n_chars:
        i += 1
        out.append(f"Sentence number {i:04d} says something particular about the river and the drill.\n")
    return "".join(out)[:n_chars]


class FakeLanes:
    """call_json fake over a chain: BG answers `bg` (a value, an Exception, or a list of those, one per call);
    HOT answers `hot`. Behaves like model_client.call_node_json: walks the URLs it is handed, fills `served`."""
    def __init__(self, bg, hot):
        self.bg, self.hot, self.calls = (list(bg) if isinstance(bg, list) else [bg]), hot, []

    async def __call__(self, urls, sysmsg, user, **kw):
        self.calls.append({"urls": list(urls), "sys": sysmsg, "user": user, "kw": {k: v for k, v in kw.items() if k != "served"}})
        served = kw.get("served")
        for idx, u in enumerate(urls):
            r = (self.bg.pop(0) if len(self.bg) > 1 else self.bg[0]) if u == BG else self.hot
            if isinstance(r, Exception):
                continue
            if served is not None:
                served.update({"url": u, "model": "command-r7b" if u == BG else "qwen3.5:9b", "fallback": idx > 0})
            return r
        raise ValueError("exhausted")


def _predict(fake, essay, urls=CHAIN):
    with mock.patch.object(telemetry, "_LAT", TMP / "none.jsonl"), mock.patch.object(el, "_FELT_RETRY_PAUSE_S", 0.0):
        return asyncio.run(el.self_predict(fake, urls, TITLE, essay))


def test_one_lane_only():
    fake = FakeLanes({"grounding": 0.85}, {"grounding": 0.1})
    v = _predict(fake, _essay(5000))
    check(v == 0.85 and all(c["urls"] == [BG] for c in fake.calls), f"only the primary lane is asked: {v} {[c['urls'] for c in fake.calls]}")
    f = el._FELT[TITLE]
    check(f["served"] == {"url": BG, "model": "command-r7b", "fallback": False} and f["lane"]["model"] == "command-r7b" and f["rated"] is True,
          f"answering model + node + fallback flag logged: {f}")
    check(f["lane"]["node"] == BG, f"node logged from the recorder: {f['lane']}")


def test_fallback_cannot_change_the_number():
    # the background hub is down for both tries; the hot lane would say 0.1. The rating must be None, and the hot
    # lane must never be called.
    down = ConnectionError("down")
    fake = FakeLanes([down], {"grounding": 0.1})
    v = _predict(fake, _essay(5000))
    check(v is None, f"a down background hub gives unrated, not the hot lane's number: {v}")
    check(all(c["urls"] == [BG] for c in fake.calls) and len(fake.calls) == el._FELT_ATTEMPTS,
          f"the same lane is retried, the hot lane never: {[c['urls'] for c in fake.calls]}")
    f = el._FELT[TITLE]
    check(f["rated"] is False and f["parsed"] is False and (f["reason"] or "").startswith("call failed") and f["attempts"] == el._FELT_ATTEMPTS,
          f"reason + attempts logged: {f}")
    # first try fails, the retry on the SAME lane answers
    fake = FakeLanes([down, {"grounding": 0.9}], {"grounding": 0.1})
    v = _predict(fake, _essay(5000))
    check(v == 0.9 and el._FELT[TITLE]["attempts"] == 2 and el._FELT[TITLE]["served"]["fallback"] is False,
          f"a retry on the same lane keeps the lane's number: {v} {el._FELT[TITLE]}")
    # a caller handed a bare string URL still works
    fake = FakeLanes({"grounding": 0.7}, None)
    check(_predict(fake, _essay(5000), urls=BG) == 0.7 and fake.calls[0]["urls"] == [BG], "a str base_urls is one lane")
    # defensive: a recorder that says fallback -> unrated
    async def sneaky(urls, s, u, **kw):
        kw["served"].update({"url": HOT, "model": "qwen3.5:9b", "fallback": True})
        return {"grounding": 0.1}
    v = _predict(sneaky, _essay(5000))
    check(v is None and el._FELT[TITLE]["reason"] == "answered by a fallback lane", f"a fallback answer is never used: {v} {el._FELT[TITLE]}")


def test_failed_parse_is_null_not_half():
    for bad in ({"nothing": 1}, {"grounding": "high"}, {"grounding": None}, {"grounding": float("nan")}, ["x"], None):
        fake = FakeLanes(bad, None)
        v = _predict(fake, _essay(5000))
        f = el._FELT[TITLE]
        check(v is None and f["parsed"] is False and f["rated"] is False and len(fake.calls) == 1,
              f"unparseable {bad!r} -> None, asked once: {v} {f}")
    fake = FakeLanes({"grounding": 1.7}, None)
    check(_predict(fake, _essay(5000)) == 1.0, "an out-of-range number is clamped, still a rating")
    fake = FakeLanes({"grounding": 0.5}, None)
    check(_predict(fake, _essay(5000)) == 0.5 and el._FELT[TITLE]["rated"] is True, "a genuine 0.5 is still a rating")


def test_view_first_and_last_1500():
    long_e = _essay(5200)
    fake = FakeLanes({"grounding": 0.8}, None)
    _predict(fake, long_e)
    user = fake.calls[0]["user"]
    check(long_e[:1500].rstrip() in user and long_e[-1500:].lstrip() in user, "first and last 1,500 chars are in the prompt")
    check(long_e[1600:1700] not in user and el._FELT_ELIDED.strip() in user, "the middle is cut and the cut is marked")
    check(el._FELT[TITLE]["seen_chars"] == 3000, f"seen_chars logged: {el._FELT[TITLE]['seen_chars']}")
    short = _essay(2400)
    fake = FakeLanes({"grounding": 0.8}, None)
    _predict(fake, short)
    check(short in fake.calls[0]["user"] and el._FELT[TITLE]["seen_chars"] == 2400 and el._FELT_ELIDED.strip() not in fake.calls[0]["user"],
          "an essay that fits is shown whole")
    sysmsg = fake.calls[0]["sys"]
    check("book actually says" not in sysmsg and "reads as GROUNDED" in sysmsg and "opening and its ending" in sysmsg,
          "the question matches what the rater can see")
    check(not any(ch.isdigit() for ch in sysmsg.replace("/no_think", "")), "no digit anchor in the prompt (F-0689/F-0913)")
    check(fake.calls[0]["kw"]["temperature"] == 0.0 and fake.calls[0]["kw"]["max_tokens"] == 80, "temp 0 / 80 tokens unchanged")


def test_record_null_and_gates():
    for flag, pred, want_fed, want_calls in ((False, None, False, 0), (True, None, False, 0), (True, 0.8, True, 1)):
        comp, bf = mock.MagicMock(), mock.MagicMock()
        state: dict = {"history": [], "essayed": []}
        el._LOG = TMP / f"log_{flag}_{pred}.jsonl"
        el._FELT[TITLE] = {"lane": {"model": "command-r7b", "node": BG, "s": 1.0}, "raw": None if pred is None else pred,
                           "parsed": pred is not None, "seen_chars": 3000, "rated": pred is not None}
        with mock.patch.object(el, "_load", lambda: state), mock.patch.object(el, "_save", lambda d: None), \
                mock.patch.object(el, "mark_done", lambda b: None), mock.patch.object(el, "CAPSTONE_GATE", False), \
                mock.patch.object(el, "FELT_FEEDS_SELF_MODEL", flag), \
                mock.patch.object(competence, "record_drill_accuracy", comp.record_drill_accuracy), \
                mock.patch("core.book_feelings.capstone", bf), \
                mock.patch("core.memory.store.store_fragment", return_value="fid"), \
                mock.patch("core.memory.store.store_light_event", return_value=None), \
                mock.patch("core.study.write_tablet", return_value=None), \
                mock.patch("core.world_consolidation.file_book_notes", return_value={}), \
                mock.patch("core.study.archive_book_note_files", return_value={}):
            el.record("b", TITLE, "t", _essay(800), pred, 0.6, "f", source_ids=None)
            # status() reads the (mocked) state: unrated gap None must not raise
            s2 = el.status()
        row = json.loads(el._LOG.read_text(encoding="utf-8").splitlines()[-1])
        check(row["predicted"] == pred and row["felt"]["fed"] is want_fed, f"flag={flag} pred={pred}: row predicted/fed: {row['predicted']} {row['felt']}")
        check(row["measured"] == 0.6, "the measured grade is stored either way")
        felt_calls = sum(1 for c in comp.record_drill_accuracy.call_args_list if "predicted" in c.kwargs)
        check(felt_calls == want_calls, f"flag={flag} pred={pred}: predicted folded into competence {felt_calls}x, want {want_calls}")
        check(all(c.args[0] == "comprehension" and c.args[1] == 0.6 for c in comp.record_drill_accuracy.call_args_list)
              and len(comp.record_drill_accuracy.call_args_list) == 1, "the measured result still moves the comprehension belief once")
        check(bf.call_args.args[2] == (pred if want_fed else None), f"book valence gets predicted only when rated and fed: {bf.call_args}")
        check(state["history"][-1]["predicted"] == pred and state["history"][-1]["gap"] == (None if pred is None else round(abs(pred - 0.6), 2)),
              f"history row carries null for unrated: {state['history'][-1]}")
        check(s2["mean_gap"] == (None if pred is None else round(abs(pred - 0.6), 3)), f"status() mean_gap ignores unrated: {s2}")


def test_node_thought_text():
    # the call site in nodes/inner_monologue_node.py must not format None
    src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    i = src.index("async def _essay_lesson")
    block = src[i:i + 4500]
    check("predicted:.2f}; grounded" in block and "if predicted is not None else" in block and '"unrated"' in block,
          "the capstone call site handles predicted=None")


if __name__ == "__main__":
    for t in (test_one_lane_only, test_fallback_cannot_change_the_number, test_failed_parse_is_null_not_half,
              test_view_first_and_last_1500, test_record_null_and_gates, test_node_thought_text):
        print("RUN", t.__name__)
        try:
            t()
        except Exception as exc:       # a crash is a failure, not a pass
            import traceback
            traceback.print_exc()
            FAILS.append(f"{t.__name__} raised {exc!r}")
    print("FAILS:", "none" if not FAILS else FAILS)
    sys.exit(1 if FAILS else 0)
