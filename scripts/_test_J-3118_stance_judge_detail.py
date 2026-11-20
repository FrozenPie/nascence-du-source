"""
J-3118 (F-3846, P-0084): the stance-compliance judge's reasoning and answering hub are stored on the thread row, and
peer_metrics.stance_distribution() gives an honoured count and rate.
HERMETIC: peers._CORR_DIR / _PEER_LETTER_QUALITY_LOG live in a lab_env.isolate dir; model_client.call_node is stubbed
(no hub is called, Ramses included); sensorium.deliver_letter, the world context and the compose call are stubbed.
Nothing under C:\\Nascence\\data is opened for write (a stat canary proves it).

  1. judge answers on JUDGE_1 -> bool unchanged, detail = why[:200] + judge {url, model, fallback False}
  2. JUDGE_1 transport-fails, TIEBREAK answers -> judge.url is TIEBREAK, fallback True
  3. non-bool `honoured` / both hubs down -> None and NO detail (fail-open as before)
  4. deliver_daily (challenge stance) persists stance_honoured + stance_why + stance_judge on the thread row;
     a company-stance letter and a no-verdict row carry none of the new keys (byte shape unchanged)
  5. a stale detail from an earlier delivery never rides onto a later row
  6. call_node_json(served=None) and a plain call are unchanged (no served arg needed)
  7. stance_distribution: honoured_n / honoured / honoured_rate; n=1 reads honoured_n=1; no verdicts -> rate None
Run: python scripts/_test_J-3118_stance_judge_detail.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env)
from core import peers, peer_metrics, sensorium, model_client  # noqa: E402
from core.judge_panel import JUDGE_1, TIEBREAK  # noqa: E402

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__

LIVE = Path(r"C:\Nascence\data")
WATCH = [LIVE / "Correspondence" / p / "thread.jsonl" for p in list(peers.PERSONAS)]


def _snap():
    out = {}
    for p in WATCH:
        out[str(p)] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


LIVE_BEFORE = _snap()
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def run(coro):
    return asyncio.run(coro)


async def _judge_with_detail(persona, text, reply_to):
    """Judge + read the detail inside ONE task (the ContextVar is per-task, exactly as in deliver_daily)."""
    peers._STANCE_JUDGE_DETAIL.set(None)
    v = await peers._stance_compliance_judge(persona, text, reply_to)
    return v, peers._STANCE_JUDGE_DETAIL.get()


class Hubs:
    """Scripted call_node: url -> list of replies (str) or exceptions."""

    def __init__(self):
        self.script = {}
        self.calls = []

    async def __call__(self, base_url, system_prompt, user_prompt, **kw):
        self.calls.append(base_url)
        q = self.script.get(base_url) or []
        if not q:
            raise asyncio.TimeoutError()
        out = q.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


hubs = Hubs()
LONG_WHY = "x" * 300


def main():
    orig_call_node = model_client.call_node
    orig_compose, orig_choose = peers.compose_letter, peers._choose_stance
    orig_ctx, orig_buf = peers._du_world_context, peers._self_affirmation_buffer
    orig_deliver, orig_freeze = sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent
    try:
        with isolate(also=[(peers, ["_CORR_DIR", "_PEER_LETTER_QUALITY_LOG"])], db="empty") as lab_dir:
            assert "_lab" in str(peers._CORR_DIR), "isolation not active"
            model_client.call_node = hubs
            # --- 1
            hubs.script = {JUDGE_1: ['{"honoured": true, "why": "' + LONG_WHY + '"}']}
            v, d = run(_judge_with_detail("marcus", "a letter", "their words"))
            check("1 bool return unchanged (True)", v is True)
            check("1 why kept, first 200 chars", d and d["why"] == LONG_WHY[:200] and len(d["why"]) == 200, str(d)[:120])
            check("1 judge = JUDGE_1 hub, not fallback",
                  d and d["judge"]["url"] == JUDGE_1 and d["judge"]["fallback"] is False and d["judge"]["model"],
                  str(d and d["judge"]))
            # --- 2
            hubs.script = {JUDGE_1: [asyncio.TimeoutError()], TIEBREAK: ['{"honoured": false, "why": "no pushback"}']}
            v, d = run(_judge_with_detail("marcus", "a letter", ""))
            check("2 fallback answers: False, judge.url TIEBREAK, fallback True",
                  v is False and d["judge"]["url"] == TIEBREAK and d["judge"]["fallback"] is True and d["why"] == "no pushback",
                  str(d))
            # --- 3
            hubs.script = {JUDGE_1: ['{"honoured": "yes", "why": "w"}']}
            v, d = run(_judge_with_detail("marcus", "a letter", ""))
            check("3 non-bool honoured -> None and no detail", v is None and d is None)
            hubs.script = {}
            v, d = run(_judge_with_detail("marcus", "a letter", ""))
            check("3 both hubs down -> None and no detail", v is None and d is None)
            # --- 6
            hubs.script = {JUDGE_1: ['{"a": 1}']}
            r = run(model_client.call_node_json([JUDGE_1], "s", "u"))
            check("6 call_node_json without served unchanged", r == {"a": 1})

            # --- 4 / 5: deliver_daily end to end (stubs for everything but the judge + the thread append)
            letters = ["Dear friend, " + ("a coherent letter about the river. " * 12)] * 4
            peers._du_world_context = lambda: "CTX"
            peers._self_affirmation_buffer = lambda *a, **k: None
            sensorium.deliver_letter = lambda sender, text: None
            peer_metrics.freeze_baseline_if_absent = lambda *a, **k: False
            stances = []

            async def fake_compose(persona="darwin", thread="", du_context="", reply_to="", *, stance=None,
                                   model_override=None, timeout=600, attempt=1, **_kw):   # J-2980: deliver_daily now passes no_reply=True on no-reply letters
                return letters.pop(0)
            peers.compose_letter = fake_compose
            peers._choose_stance = lambda persona: stances.pop(0)

            stances[:] = ["challenge"]
            hubs.script = {JUDGE_1: ['{"honoured": true, "why": "he disagrees about the ferry"}']}
            ok = run(peers.deliver_daily("twain", force=True))
            rows = peers._read_thread("twain")
            r0 = rows[-1] if rows else {}
            check("4 delivered; row has stance + verdict + why + judge",
                  ok is True and r0.get("stance") == "challenge" and r0.get("stance_honoured") is True
                  and r0.get("stance_why") == "he disagrees about the ferry"
                  and r0.get("stance_judge", {}).get("url") == JUDGE_1, str(r0)[:300])

            # judge down on the next challenge letter -> a stale detail must not ride onto the row (5)
            stances[:] = ["mixed"]
            hubs.script = {}
            ok = run(peers.deliver_daily("twain", force=True))
            r1 = peers._read_thread("twain")[-1]
            check("5 no verdict -> none of stance_honoured/why/judge on the row",
                  ok is True and r1.get("stance") == "mixed"
                  and not ({"stance_honoured", "stance_why", "stance_judge"} & set(r1)), str(r1)[:300])

            stances[:] = ["company"]
            hubs.script = {}
            _calls_before = len(hubs.calls)
            ok = run(peers.deliver_daily("twain", force=True))
            r2 = peers._read_thread("twain")[-1]
            check("4 company letter: row keys exactly from/text/ts/stance",
                  ok is True and set(r2) == {"from", "text", "ts", "stance"}, str(sorted(r2)))
            check("4 company letter made no judge call", len(hubs.calls) == _calls_before)

            # --- 7 stance_distribution
            dist = peer_metrics.stance_distribution()["twain"]
            check("7 twain: n=3 stance rows, honoured_n=1, honoured=1, rate 1.0 (n=1 is visible as honoured_n=1)",
                  dist["n"] == 3 and dist["honoured_n"] == 1 and dist["honoured"] == 1 and dist["honoured_rate"] == 1.0,
                  str(dist))
            peers._append_thread("twain", "twain", "t", stance="challenge", stance_honoured=False)
            dist = peer_metrics.stance_distribution()["twain"]
            check("7 after a False verdict: honoured_n=2 honoured=1 rate 0.5",
                  dist["honoured_n"] == 2 and dist["honoured"] == 1 and dist["honoured_rate"] == 0.5, str(dist))
            peers._append_thread("smith", "smith", "t", stance="company")
            d2 = peer_metrics.stance_distribution()["smith"]
            check("7 no verdicts: honoured_n=0, rate None (not 0%)", d2["honoured_n"] == 0 and d2["honoured_rate"] is None, str(d2))
            # a user reply row (from != persona) never counts
            peers._append_thread("smith", "du", "reply")
            check("7 reply rows ignored", peer_metrics.stance_distribution()["smith"]["n"] == 1)
    finally:
        model_client.call_node = orig_call_node
        peers.compose_letter, peers._choose_stance = orig_compose, orig_choose
        peers._du_world_context, peers._self_affirmation_buffer = orig_ctx, orig_buf
        sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent = orig_deliver, orig_freeze
    check("live thread files untouched", _snap() == LIVE_BEFORE)
    print(f"\n{len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
