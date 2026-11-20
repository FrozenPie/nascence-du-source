"""
Test suite — peers.deliver_daily bounded regenerate-on-degenerate (J-1773, decide:D-0346, successor of J-1753).

D-0346 (RULED by travis, /decide-review 2026-10-04, "Regenerate, then skip"): a letter whose coherence check
fails (J-1667's non-Latin-letter ratio above 0.10) is REGENERATED, bounded at up to 2 retries with a VARIED request
(the :11439 hub is deterministic on the first request after a fresh load, F-2387 6a/6b), and if every attempt fails
the cycle is SKIPPED: no mailbox delivery, no thread append, retried at the next opportunity but rate-limited so a
persistently degenerate hub cannot spin. J-1667's observe log keeps recording every failed attempt.

HERMETIC and model-free: compose_letter is a scripted stub (no hub, no network); sensorium.deliver_letter is a
recorder; peer_metrics.freeze_baseline_if_absent / _du_world_context / the stance-judge and self-affirmation buffer are
stubs. Everything that could write under data/ runs inside lab_env.isolate(also=[peers._CORR_DIR,
peers._PEER_LETTER_QUALITY_LOG], db="empty") (a fresh empty DB in data/_lab/<stamp>/, never the live one), and the live
C:\\Nascence\\data stores (all 8 thread files, the quality log, nascence.db + wal/shm, nascence.log, peer_baseline.json)
are stat-ed / hashed before and after.

  [1] coherent-first            -> delivered on attempt 1, nothing logged, no cooldown, thread row byte-shape unchanged
  [2] degenerate-then-coherent  -> the RETRY is what is delivered and stored; 1 log row (attempt 1)
  [3] degenerate x2 -> coherent -> delivered on attempt 3; 2 log rows
  [4] always-degenerate         -> False, NO delivery, NO thread file, exactly 3 attempts logged (skipped on the last),
                                   the persona is still overdue (a skipped cycle is not "delivered"), cooldown set
  [5] rate limit (deliver_due)  -> the skipped persona is NOT retried inside the cooldown and the next persona
                                   delivers instead (no starvation); retried once the cooldown has expired
  [6] compose exception         -> on a retry: False + cooldown; on attempt 1: unchanged (False, no cooldown)
  [7] _flag_if_degenerate       -> verdict semantics, fail-open, a log-write failure does not flip a verdict
  [8] compose_letter request    -> attempt 1 / default is byte-identical to the shipped request (temp 0.85, same
                                   prompt); retries vary the temperature only (0.75, 0.65), never the prompt
  [9] challenge stance          -> stance chosen ONCE, same on every attempt; judge only on the delivered letter;
                                   a skipped letter gets the "before" buffer but no "after" and no judge
  [10] the live stores are untouched

Run: python scripts/test_peers_regenerate_on_degenerate.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# core.* BEFORE lab_env: lab_env inserts C:\Nascence at sys.path[0] when absent, which would otherwise let a later
# first-import of `core` resolve to the live checkout instead of this one.
from core import peers, peer_metrics, sensorium  # noqa: E402
from core import model_client  # noqa: E402

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert Path(peers.__file__).resolve().is_relative_to(ROOT), f"core.peers resolved outside {ROOT}: {peers.__file__}"

HAS_FEATURE = hasattr(peers, "_degenerate_skip_ts")      # False on pre-J-1773 code: checks then FAIL, they do not crash

# capture nascence.peers log records (and keep them off stderr): the skip decision must be VISIBLE in nascence.log
LOG_RECORDS: list[logging.LogRecord] = []


class _Capture(logging.Handler):
    def emit(self, record):
        LOG_RECORDS.append(record)


_peers_logger = logging.getLogger("nascence.peers")
_peers_logger.addHandler(_Capture())
_peers_logger.setLevel(logging.DEBUG)
_peers_logger.propagate = False

# ------------------------------------------------------------------------------------------------ live canary
LIVE = Path(r"C:\Nascence\data")
WATCH = ([LIVE / "peer_letter_quality_log.jsonl", LIVE / "peer_baseline.json", LIVE / "nascence.log",
          LIVE / "memory" / "nascence.db", LIVE / "memory" / "nascence.db-wal", LIVE / "memory" / "nascence.db-shm"]
         + [LIVE / "Correspondence" / p / "thread.jsonl" for p in list(peers.PERSONAS)])
SMALL = 5_000_000


def _snap() -> dict:
    out = {}
    for p in WATCH:
        if not p.exists():
            out[str(p)] = None
            continue
        st = p.stat()
        digest = hashlib.sha256(p.read_bytes()).hexdigest() if st.st_size <= SMALL else None
        out[str(p)] = (st.st_size, st.st_mtime_ns, digest)
    return out


LIVE_BEFORE = _snap()

# ------------------------------------------------------------------------------------------------ check helper
FAILS: list[str] = []
PASSES = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  ok    {name}")
    else:
        FAILS.append(name)
        print(f"  FAIL  {name}" + (f"   [{detail}]" if detail else ""))


# ------------------------------------------------------------------------------------------------ fixtures
def coherent(n: int) -> str:
    return (f"Dear friend, this is coherent letter number {n}. The river ran high this morning and I thought of "
            "your garden above the sea. " * 8).strip()


DEG = ["日子rait 안녕하세요 Привет мир αβγδε 你好世界 " * 8 + f" #{i}" for i in (1, 2, 3, 4)]


class H:
    """Scripted stand-ins; one instance reset per scenario."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.script: dict[str, list] = {}
        self.compose_calls: list[dict] = []
        self.delivered: list[tuple] = []
        self.buffer_calls: list[tuple] = []
        self.judge_calls: list[str] = []
        self.stance_calls = 0
        self.stance_value = None


h = H()


async def fake_compose(persona="darwin", thread="", du_context="", reply_to="", *, stance=None,
                       model_override=None, timeout=600, attempt=1):
    h.compose_calls.append({"persona": persona, "attempt": attempt, "thread": thread, "du_context": du_context,
                            "reply_to": reply_to, "stance": stance})
    queue = h.script.get(persona) or []
    if not queue:
        raise AssertionError(f"unexpected extra compose call for {persona} (attempt {attempt})")
    out = queue.pop(0)
    if isinstance(out, Exception):
        raise out
    return out


def fake_deliver(sender, text):
    h.delivered.append((sender, text))


def fake_choose_stance(persona):
    h.stance_calls += 1
    return h.stance_value


def fake_buffer(occasion, peer_label="Buddha", peer_key="buddha"):
    h.buffer_calls.append((occasion, peer_key))


async def fake_judge(persona, letter_text, reply_to):
    h.judge_calls.append(letter_text)
    return True


def fresh():
    """Wipe the (redirected) thread dir + quality log, clear the cooldown map, reset the stubs."""
    assert "_lab" in str(peers._CORR_DIR) and "_lab" in str(peers._PEER_LETTER_QUALITY_LOG), "isolation not active"
    shutil.rmtree(peers._CORR_DIR, ignore_errors=True)
    Path(peers._PEER_LETTER_QUALITY_LOG).unlink(missing_ok=True)
    if HAS_FEATURE:
        peers._degenerate_skip_ts.clear()
    h.reset()


def log_rows() -> list[dict]:
    p = Path(peers._PEER_LETTER_QUALITY_LOG)
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []
    return [r for r in rows if "event" not in r]      # J-2062 idle-unload event rows are covered by their own suite


def run(coro):
    return asyncio.run(coro)


def attempts() -> list:
    return [c["attempt"] for c in h.compose_calls]


# ------------------------------------------------------------------------------------------------ scenarios
def s1_coherent_first():
    print("[1] coherent-first")
    fresh()
    h.script["twain"] = [coherent(1)]
    ok = run(peers.deliver_daily("twain", force=True))
    rows = peers._read_thread("twain")
    check("returns True", ok is True)
    check("one compose call, attempt 1", attempts() == [1], str(attempts()))
    check("delivered once, the coherent text", h.delivered == [("Mark Twain", coherent(1))], str(h.delivered))
    check("one thread row, shape unchanged (from/text/ts only)",
          len(rows) == 1 and set(rows[0]) == {"from", "text", "ts"} and rows[0]["text"] == coherent(1), str(rows))
    check("quality log empty", log_rows() == [])
    check("no cooldown set", not HAS_FEATURE or "twain" not in peers._degenerate_skip_ts)


def s2_degenerate_then_coherent():
    print("[2] degenerate-then-coherent")
    fresh()
    h.script["twain"] = [DEG[0], coherent(2)]
    ok = run(peers.deliver_daily("twain", force=True))
    rows = peers._read_thread("twain")
    check("returns True", ok is True)
    check("two compose calls, attempts 1,2", attempts() == [1, 2], str(attempts()))
    check("the retry's text is what is delivered", h.delivered == [("Mark Twain", coherent(2))], str(h.delivered)[:200])
    check("the thread holds only the retry's text",
          len(rows) == 1 and rows[0]["text"] == coherent(2) and DEG[0] not in rows[0]["text"], str(rows)[:200])
    lr = log_rows()
    check("one log row: attempt 1, not skipped",
          len(lr) == 1 and lr[0].get("attempt") == 1 and "skipped" not in lr[0] and lr[0]["persona"] == "twain"
          and lr[0]["non_latin_ratio"] > peers._DEGENERATE_NON_LATIN_RATIO, str(lr)[:300])
    inputs = {(c["thread"], c["du_context"], c["reply_to"], c["stance"]) for c in h.compose_calls}
    check("thread/du_context/reply_to/stance identical on both attempts", len(inputs) == 1, str(inputs)[:200])


def s3_degenerate_twice_then_coherent():
    print("[3] degenerate x2 then coherent")
    fresh()
    h.script["twain"] = [DEG[0], DEG[1], coherent(3)]
    ok = run(peers.deliver_daily("twain", force=True))
    rows = peers._read_thread("twain")
    check("returns True", ok is True)
    check("three compose calls, attempts 1,2,3", attempts() == [1, 2, 3], str(attempts()))
    check("delivered == the third attempt", h.delivered == [("Mark Twain", coherent(3))], str(h.delivered)[:200])
    check("thread == the third attempt only", len(rows) == 1 and rows[0]["text"] == coherent(3))
    lr = log_rows()
    check("two log rows (attempts 1,2), none skipped",
          [r.get("attempt") for r in lr] == [1, 2] and not any("skipped" in r for r in lr), str(lr)[:300])


def s4_always_degenerate():
    print("[4] always-degenerate")
    fresh()
    h.script["twain"] = [DEG[0], DEG[1], DEG[2]]
    t0 = time.time()
    LOG_RECORDS.clear()
    ok = run(peers.deliver_daily("twain", force=True))
    skipped_lines = [r for r in LOG_RECORDS if r.levelno == logging.WARNING and "SKIPPED" in r.getMessage()]
    check("the skip is logged once at WARNING (visible in nascence.log)", len(skipped_lines) == 1,
          str([r.getMessage()[:80] for r in LOG_RECORDS]))
    check("returns False", ok is False)
    check("exactly 3 compose attempts (bounded: no 4th)", attempts() == [1, 2, 3], str(attempts()))
    check("NO delivery to the mailbox", h.delivered == [], str(h.delivered)[:200])
    check("NO thread append (no file, no rows)",
          peers._read_thread("twain") == [] and not peers._thread_path("twain").exists())
    check("a skipped cycle is not 'delivered': last delivery ts still 0.0", peers._last_delivery_ts("twain") == 0.0)
    lr = log_rows()
    check("three attempts logged, attempts 1,2,3", [r.get("attempt") for r in lr] == [1, 2, 3], str(lr)[:400])
    check("only the last attempt carries skipped=true",
          [bool(r.get("skipped")) for r in lr] == [False, False, True], str(lr)[:400])
    check("each logged excerpt is that attempt's own text",
          [r["excerpt"] for r in lr] == [d[:200] for d in DEG[:3]])
    ts = getattr(peers, "_degenerate_skip_ts", {}).get("twain")
    check("cooldown recorded for twain", ts is not None and t0 - 1 <= ts <= time.time() + 1, str(ts))


def s5_rate_limit_via_deliver_due():
    print("[5] rate limit through deliver_due")
    fresh()
    orig = peers.PERSONAS
    saved_gap = peers._GLOBAL_MIN_GAP_H
    peers.PERSONAS = {"twain": orig["twain"], "shackleton": orig["shackleton"]}      # twain (gap 4d) is most overdue
    try:
        h.script["twain"] = [DEG[0], DEG[1], DEG[2]]
        ok = run(peers.deliver_due())
        check("A: first deliver_due picks twain, all 3 attempts fail -> False",
              ok is False and [c["persona"] for c in h.compose_calls] == ["twain"] * 3, str(h.compose_calls)[:200])
        check("A: nothing delivered", h.delivered == [])
        n_before = len(h.compose_calls)
        h.script["shackleton"] = [coherent(5)]          # twain's script is EMPTY: a retry of twain would be recorded
        ok = run(peers.deliver_due())
        new = h.compose_calls[n_before:]
        check("B: next deliver_due does NOT retry twain inside the cooldown", all(c["persona"] != "twain" for c in new),
              str([c["persona"] for c in new]))
        check("B: the next persona (shackleton) delivers instead — no starvation",
              ok is True and [c["persona"] for c in new] == ["shackleton"]
              and h.delivered == [("Ernest Shackleton", coherent(5))], str(h.delivered)[:200])
        n_before = len(h.compose_calls)
        if HAS_FEATURE:
            peers._degenerate_skip_ts["twain"] -= peers._DEGENERATE_SKIP_COOLDOWN_H * 3600 + 1   # cooldown elapsed
        peers._GLOBAL_MIN_GAP_H = 0           # only to get past shackleton's just-made delivery (an existing gate)
        h.script["twain"] = [coherent(6)]
        ok = run(peers.deliver_due())
        new = h.compose_calls[n_before:]
        check("C: once the cooldown has expired twain is retried and delivers",
              ok is True and [c["persona"] for c in new] == ["twain"] and h.delivered[-1] == ("Mark Twain", coherent(6)),
              str(new)[:200])
        check("C: twain's thread now holds exactly the coherent letter",
              [r["text"] for r in peers._read_thread("twain")] == [coherent(6)])
    finally:
        peers.PERSONAS = orig
        peers._GLOBAL_MIN_GAP_H = saved_gap
    if HAS_FEATURE:
        peers._degenerate_skip_ts.clear()
        peers._degenerate_skip_ts["twain"] = 1000.0
        cd = peers._DEGENERATE_SKIP_COOLDOWN_H * 3600
        check("D: _on_degenerate_cooldown boundaries",
              peers._on_degenerate_cooldown("twain", now=1000.0 + cd - 1) is True
              and peers._on_degenerate_cooldown("twain", now=1000.0 + cd) is False
              and peers._on_degenerate_cooldown("shackleton", now=1000.0) is False)
    else:
        check("D: _on_degenerate_cooldown exists", False, "feature absent")


def s6_compose_exception():
    print("[6] compose exception")
    fresh()
    h.script["twain"] = [DEG[0], RuntimeError("hub down")]
    ok = run(peers.deliver_daily("twain", force=True))
    check("exception on a retry: False, 2 attempts, nothing delivered/appended",
          ok is False and attempts() == [1, 2] and h.delivered == [] and peers._read_thread("twain") == [])
    check("exception on a retry: the attempt-1 flag is logged, not marked skipped",
          [(r.get("attempt"), "skipped" in r) for r in log_rows()] == [(1, False)])
    check("exception on a retry: cooldown set (no spin)", HAS_FEATURE and "twain" in peers._degenerate_skip_ts)
    fresh()
    h.script["twain"] = [RuntimeError("hub down")]
    ok = run(peers.deliver_daily("twain", force=True))
    check("exception on attempt 1: unchanged (False, 1 attempt, no log, NO cooldown)",
          ok is False and attempts() == [1] and log_rows() == [] and not (HAS_FEATURE and peers._degenerate_skip_ts))


def s7_flag_semantics():
    print("[7] _flag_if_degenerate")
    fresh()
    f = peers._flag_if_degenerate
    check("coherent -> False, no row", f("twain", coherent(1)) is False and log_rows() == [])
    check("under 20 alphabetic chars -> False even if non-Latin", f("twain", "日本語") is False and log_rows() == [])
    check("None / non-str input -> False, never raises", f("twain", None) is False)   # type: ignore[arg-type]
    check("degenerate -> True, row carries attempt", f("twain", DEG[0], attempt=2) is True
          and [r.get("attempt") for r in log_rows()] == [2])
    f("twain", DEG[1], attempt=3, last_attempt=True)
    check("last_attempt adds skipped=true", log_rows()[-1].get("skipped") is True)
    saved = peers._PEER_LETTER_QUALITY_LOG
    blocker = Path(saved).parent / "a_file_not_a_dir"
    blocker.write_text("x", encoding="utf-8")
    peers._PEER_LETTER_QUALITY_LOG = blocker / "q.jsonl"        # mkdir/open must fail
    try:
        check("a log-WRITE failure does not flip the verdict (still True)", f("twain", DEG[2]) is True)
    finally:
        peers._PEER_LETTER_QUALITY_LOG = saved
        blocker.unlink(missing_ok=True)


def s8_compose_letter_request():
    print("[8] compose_letter request construction")
    rec: list[tuple] = []

    async def fake_call_node(url, system, user, **kw):
        rec.append((url, system, user, kw))
        return "  a letter  "

    saved = model_client.call_node
    model_client.call_node = fake_call_node
    try:
        kw = dict(thread="T", du_context="D", reply_to="R", stance=None)
        ret = run(peers.compose_letter("twain", **kw))                  # default: no `attempt` passed
        for a in (1, 2, 3, 9):
            run(peers.compose_letter("twain", attempt=a, **kw))
    finally:
        model_client.call_node = saved
    p = peers.PERSONAS["twain"]
    expected_user = peers._build_user("T", "D", "R", None)
    default, a1, a2, a3, a9 = rec
    check("default call == the shipped request (temp 0.85, same prompt/args)",
          default[3]["temperature"] == 0.85 and default[2] == expected_user and default[0] == p["url"]
          and default[3]["max_tokens"] == 1600 and default[3]["json_mode"] is False
          and default[3]["model_override"] == p["model"] and default[3]["num_gpu"] == p["num_gpu"]
          and default[3]["timeout"] == 600, str(default[3]))
    check("attempt=1 is identical to the default call", a1 == default)
    check("retries vary the temperature: attempt 2 -> 0.75, 3 -> 0.65 (and 9 clamps to 0.65)",
          (a2[3]["temperature"], a3[3]["temperature"], a9[3]["temperature"]) == (0.75, 0.65, 0.65),
          str([x[3]["temperature"] for x in rec]))
    check("the prompt is byte-identical on every attempt (only sampling varies)",
          len({x[2] for x in rec}) == 1 and rec[0][2] == expected_user)
    check("compose_letter still returns the stripped model text", ret == "a letter", repr(ret))


def s9_challenge_stance():
    print("[9] challenge stance (stance chosen once; judge only on the delivered letter)")
    fresh()
    h.stance_value = "challenge"
    h.script["twain"] = [DEG[0], coherent(9)]
    ok = run(peers.deliver_daily("twain", force=True))
    check("delivered on the retry; stance chosen exactly once",
          ok is True and h.stance_calls == 1 and attempts() == [1, 2])
    check("both attempts carried stance='challenge'", [c["stance"] for c in h.compose_calls] == ["challenge"] * 2)
    check("judge ran once, on the coherent letter only", h.judge_calls == [coherent(9)], str(h.judge_calls)[:200])
    check("buffer: 'before' once, 'after' once (not once per attempt)",
          [b[0] for b in h.buffer_calls] == ["before", "after"], str(h.buffer_calls))
    check("thread row records the stance and the judge verdict",
          [(r.get("stance"), r.get("stance_honoured")) for r in peers._read_thread("twain")] == [("challenge", True)])
    fresh()
    h.stance_value = "challenge"
    h.script["twain"] = [DEG[0], DEG[1], DEG[2]]
    ok = run(peers.deliver_daily("twain", force=True))
    check("skipped: False, no judge call, no thread, no 'after' buffer",
          ok is False and h.judge_calls == [] and peers._read_thread("twain") == []
          and [b[0] for b in h.buffer_calls] == ["before"], str(h.buffer_calls))


async def _no_sleep(seconds):
    return None


# ------------------------------------------------------------------------------------------------ main
def main() -> int:
    originals = {
        "compose_letter": peers.compose_letter, "_choose_stance": peers._choose_stance,
        "_du_world_context": peers._du_world_context, "_self_affirmation_buffer": peers._self_affirmation_buffer,
        "_stance_compliance_judge": peers._stance_compliance_judge,
        "_retry_sleep": getattr(peers, "_retry_sleep", None),
    }
    orig_deliver = sensorium.deliver_letter
    orig_freeze = peer_metrics.freeze_baseline_if_absent
    try:
        with isolate(also=[(peers, ["_CORR_DIR", "_PEER_LETTER_QUALITY_LOG"])], db="empty") as lab_dir:
            print("lab dir:", lab_dir)
            peers.compose_letter = fake_compose
            peers._retry_sleep = _no_sleep           # J-2062: no real 370 s waits for the :11439 personas
            peers._choose_stance = fake_choose_stance
            peers._du_world_context = lambda: "DU-WORLD-CONTEXT"
            peers._self_affirmation_buffer = fake_buffer
            peers._stance_compliance_judge = fake_judge
            sensorium.deliver_letter = fake_deliver
            peer_metrics.freeze_baseline_if_absent = lambda *a, **k: False
            for fn in (s1_coherent_first, s2_degenerate_then_coherent, s3_degenerate_twice_then_coherent,
                       s4_always_degenerate, s5_rate_limit_via_deliver_due, s6_compose_exception,
                       s7_flag_semantics, s9_challenge_stance):
                try:
                    fn()
                except Exception as exc:                         # a crash is a failed scenario, not a silent skip
                    FAILS.append(f"{fn.__name__} crashed: {type(exc).__name__}: {exc}")
                    print(f"  FAIL  {fn.__name__} crashed: {type(exc).__name__}: {exc}")
            for k, v in originals.items():                      # s8 needs the REAL compose_letter
                setattr(peers, k, v)
            try:
                s8_compose_letter_request()
            except Exception as exc:
                FAILS.append(f"s8 crashed: {type(exc).__name__}: {exc}")
                print(f"  FAIL  s8 crashed: {type(exc).__name__}: {exc}")
    finally:
        for k, v in originals.items():
            setattr(peers, k, v)
        sensorium.deliver_letter = orig_deliver
        peer_metrics.freeze_baseline_if_absent = orig_freeze
    print("[10] live stores untouched")
    check("every watched live file is byte/stat-identical to before", _snap() == LIVE_BEFORE,
          str({k: (LIVE_BEFORE[k], v) for k, v in _snap().items() if LIVE_BEFORE[k] != v}))
    print(f"\n{PASSES} checks passed, {len(FAILS)} failed")
    for n in FAILS:
        print("  FAILED:", n)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
