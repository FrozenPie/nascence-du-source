"""
Test suite — Lane 2 `_ask` failure attribution + failure evidence (J-1709, F-2331/F-2332, 2026-10-03).

Follow-through on J-1379 (F-1937/F-2005). The first real `no_output_by_cause_24h` read (F-2331) found 32 of
102 post-J-1379 no-output rows carrying `cause=None`: `_ask` returned cause None whenever
`parse_json_loose` returned a dict, but `tick()` treats a FALSY dict as no-output, so a reply that parsed to
an EMPTY OBJECT was logged with no cause and shown as "unknown" by `status()` (15.0 percent of steady-state
attempts, F-2332), and no-output rows carried neither the payload nor the reply, so nobody could say why.

What this job adds (observability only; no decision path, return value, constant, option or parser changes):
  1. `_ask` names that case `cause == "empty"` (a fifth label beside judge_panel's four) and still returns
     the empty dict itself, so `tick()` still takes exactly the same no-output branch as before.
  2. no-output rows with cause in empty / parse / timeout also log the payload text actually sent
     (`payload`, bounded, plus `payload_chars`); empty / parse additionally log a bounded raw-reply sample
     (`reply_head`, `reply_chars`, `eval_count`, `prompt_eval_count`), handed from `_ask` to `tick()` through a
     module-level slot so the `(parsed, gen_s, cause)` 3-tuple contract is untouched.
  3. `status()["no_output_by_cause_24h"]` already tallies any label; this proves "empty" shows up there.

HERMETIC, in the way J-1379's check was (F-2005) and this project's test-isolation rule demands: every data
path in core.lane2 (`_DATA/_LOG/_STATE/_HINTS/_LOG_WONDER`) is redirected to a fresh temp dir before anything
runs, `core.telemetry.log_llm_call` is stubbed, and `aiohttp.ClientSession` is replaced by a fake transport
that records each POST — zero real network calls (a guard on `socket.socket.connect` also refuses any
non-loopback connect), zero real data/ I/O. The REAL `_ask()`, `tick()` and `status()` run.

Run: python scripts/test_lane2_ask_failure_evidence.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402

# live-store watch: whatever this checkout's own data dir held BEFORE the repoint below must be byte-identical
# after (a worktree usually has no data/ at all, which is also fine — then the check is "still absent").
_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "llm_calls.jsonl", "nascence.log", "lane2_store.json")


def _snap() -> dict:
    out = {}
    for n in _WATCH:
        p = _ORIG_DATA / n
        out[n] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


_LIVE_BEFORE = _snap()

TMP = Path(tempfile.mkdtemp(prefix="j1709_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"
lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"

_telemetry_mod.log_llm_call = lambda *a, **k: None      # never touch a real telemetry store
_hab.phase1_metric_sheet = lambda: None                 # status() would otherwise READ the live phase-1 stores

CHECKS: list[tuple[str, bool]] = []


def check(name: str, cond) -> None:
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


# ── no real network: a refused non-loopback connect, counted ────────────────────────────────────────
_NONLOCAL_CONNECTS: list = []
_real_connect = socket.socket.connect


def _guard_connect(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        _NONLOCAL_CONNECTS.append(address)
        raise OSError("test guard: real network connect refused")
    return _real_connect(self, address, *a, **k)


socket.socket.connect = _guard_connect

# ── the faked aiohttp transport (records every POST; nothing leaves the process) ────────────────────
_SENT: list[dict] = []
_OUTCOME = {"mode": "ok", "body": None}


class _FakeResp:
    def __init__(self, ok, body):
        self.ok, self.body = ok, body

    def raise_for_status(self):
        if not self.ok:
            raise aiohttp.ClientError("simulated non-2xx")

    async def json(self):
        return self.body


class _FakePostCM:
    def __init__(self, mode, body):
        self.mode, self.body = mode, body

    async def __aenter__(self):
        if self.mode == "timeout":
            raise asyncio.TimeoutError()
        if self.mode == "connect":
            raise aiohttp.ClientConnectionError("simulated connection refused")
        if self.mode == "boom":
            raise RuntimeError("simulated unrelated crash")
        return _FakeResp(ok=(self.mode != "http"), body=self.body)

    async def __aexit__(self, *a):
        return False


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def post(self, url, json=None, timeout=None):
        _SENT.append({"url": url, "json": json})
        return _FakePostCM(_OUTCOME["mode"], _OUTCOME["body"])


_REAL_SESSION = aiohttp.ClientSession
aiohttp.ClientSession = lambda *a, **k: _FakeSession()


def reply(content, eval_count=2, prompt_eval_count=713) -> dict:
    """The :11444 custom hub's real envelope shape (F-2331 probe): created_at, done, eval_count, message
    (content + role only), model, prompt_eval_count — no thinking field, no done_reason."""
    return {"created_at": "2026-10-03T00:00:00Z", "done": True, "eval_count": eval_count,
            "message": {"role": "assistant", "content": content}, "model": "deepseek-r1:7b",
            "prompt_eval_count": prompt_eval_count}


def _set(mode="ok", body=None):
    _OUTCOME["mode"] = mode
    _OUTCOME["body"] = body if body is not None else reply('{"notice": "n"}')


def _slot():
    return getattr(lane2, "_LAST_ASK_REPLY", "MISSING")


def _rows() -> list[dict]:
    if not lane2._LOG.exists():
        return []
    return [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]


_PERCEPTS = {"available": ["world"], "missing": [], "run": 2,
             "world": {"place": "study", "standpoint": "at_the_desk"},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint"]}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}

# J-2164 (D-0414 b): the single retry-on-empty is switched OFF here so this suite keeps proving the J-1709 failure
# evidence on a single call; the retry itself is covered by scripts/test_lane2_retry_on_empty_J2164.py. The four
# retry keys are always present on a no-output row now (retried False, rest None).
lane2.RETRY_ON_EMPTY = False
RETRY_KEYS = {"retried", "retry_variant", "retry_cause", "retry_gen_s"}
OLD_SKIP_KEYS = {"ts", "kind", "skip", "model", "seat", "cause", "elapsed_s", "had_percepts"} | RETRY_KEYS
REPLY_KEYS = {"reply_head", "reply_chars", "eval_count", "prompt_eval_count"}
PAYLOAD_KEYS = {"payload", "payload_chars"}
PAYLOAD_CAP = getattr(lane2, "FAILURE_PAYLOAD_CHARS", 600)
REPLY_CAP = getattr(lane2, "FAILURE_REPLY_CHARS", 200)


# ── PART A — the REAL _ask(), faked transport only ──────────────────────────────────────────────────
async def part_a():
    # A1 — clean success: unchanged
    _set("ok")
    out, gen_s, cause = await lane2._ask("payload text")
    check("A1 clean success: parsed dict returned unchanged", out == {"notice": "n"})
    check("A1 clean success: cause is None", cause is None)
    check("A1 clean success: gen_s is a float >= 0", isinstance(gen_s, float) and gen_s >= 0)
    check("A1 clean success: no failure slot left behind", _slot() is None)
    check("A1 the user message the hub saw is exactly the payload passed in",
          _SENT[-1]["json"]["messages"][1]["content"] == "payload text")

    # A2 — a literal {} reply: its own cause, same empty dict out (so tick()'s branch is unchanged)
    _set("ok", reply("{}", eval_count=2, prompt_eval_count=713))
    out, gen_s, cause = await lane2._ask("payload text")
    check("A2 literal {}: cause == 'empty'", cause == "empty")
    check("A2 literal {}: first element is STILL the empty dict (decision path unchanged)",
          out == {} and isinstance(out, dict) and not out)
    check("A2 literal {}: gen_s is a float", isinstance(gen_s, float))
    s = _slot()
    check("A2 literal {}: failure slot carries the reply sample",
          isinstance(s, dict) and s.get("cause") == "empty" and s.get("reply_head") == "{}"
          and s.get("reply_chars") == 2 and s.get("eval_count") == 2 and s.get("prompt_eval_count") == 713)

    # A3 — whitespace then {}: whitespace preserved in the head (it is part of what the model sent)
    _set("ok", reply("\n \n{}\n", eval_count=5, prompt_eval_count=720))
    out, gen_s, cause = await lane2._ask("payload text")
    s = _slot()
    check("A3 whitespace then {}: cause == 'empty', first element {}", cause == "empty" and out == {})
    check("A3 whitespace then {}: head keeps the raw whitespace, chars == 6",
          isinstance(s, dict) and s.get("reply_head") == "\n \n{}\n" and s.get("reply_chars") == 6)

    # A4 — fenced empty object
    _set("ok", reply("```json\n{}\n```"))
    out, gen_s, cause = await lane2._ask("payload text")
    check("A4 fenced ```json {} ```: cause == 'empty'", cause == "empty" and out == {})

    # A5 — non-JSON reply: parse, with a sample
    _set("ok", reply("no json here at all", eval_count=9, prompt_eval_count=701))
    out, gen_s, cause = await lane2._ask("payload text")
    s = _slot()
    check("A5 non-JSON: out is None, cause == 'parse'", out is None and cause == "parse")
    check("A5 non-JSON: slot carries cause parse + head + counts",
          isinstance(s, dict) and s.get("cause") == "parse" and s.get("reply_head") == "no json here at all"
          and s.get("reply_chars") == 19 and s.get("eval_count") == 9 and s.get("prompt_eval_count") == 701)

    # A6 — a long non-JSON reply: the head is bounded, the true length is kept
    _set("ok", reply("z" * 5000))
    out, gen_s, cause = await lane2._ask("payload text")
    s = _slot()
    check("A6 5000-char reply: head bounded to the cap, true length kept",
          isinstance(s, dict) and len(s.get("reply_head") or "") == REPLY_CAP and s.get("reply_chars") == 5000)

    # A7 — an envelope with no message at all (error shape): parse, honest None counts, no crash
    _set("ok", {"error": "model not loaded"})
    out, gen_s, cause = await lane2._ask("payload text")
    s = _slot()
    check("A7 error envelope without message: cause == 'parse'", out is None and cause == "parse")
    check("A7 error envelope: sample says 0 chars and None counts",
          isinstance(s, dict) and s.get("reply_head") == "" and s.get("reply_chars") == 0
          and s.get("eval_count") is None and s.get("prompt_eval_count") is None)

    # A8 — non-int counts are not trusted
    _set("ok", reply("{}", eval_count="7", prompt_eval_count=True))
    out, gen_s, cause = await lane2._ask("payload text")
    s = _slot()
    check("A8 non-int / bool counts are logged as None",
          cause == "empty" and isinstance(s, dict) and s.get("eval_count") is None
          and s.get("prompt_eval_count") is None)

    # A9..A12 — the four judge_panel causes are unchanged, and none of them leaves a reply sample
    for mode, want in (("timeout", "timeout"), ("http", "http"), ("connect", "http"), ("boom", "exception")):
        _set(mode)
        out, gen_s, cause = await lane2._ask("payload text")
        check(f"A9 {mode}: out is None, cause == {want!r}", out is None and cause == want)
        check(f"A9 {mode}: gen_s is a float and no reply sample was left in the slot",
              isinstance(gen_s, float) and _slot() is None)

    # A10 — a failure's sample never survives into the next call
    _set("ok", reply("{}"))
    await lane2._ask("payload text")
    _set("ok")
    out, gen_s, cause = await lane2._ask("payload text")
    check("A10 sample from a failed call is cleared by the next successful call",
          cause is None and out == {"notice": "n"} and _slot() is None)


# ── PART B — the REAL tick() over the REAL _ask(), faked transport ──────────────────────────────────
async def tick_case(mode, body=None):
    _set(mode, body)
    before = len(_rows())
    sent_before = len(_SENT)
    rec = await lane2.tick()
    new = _rows()[before:]
    sent = _SENT[sent_before:]
    return rec, new, sent


async def part_b():
    # B1 — empty-object reply
    rec, new, sent = await tick_case("ok", reply("{}", eval_count=2, prompt_eval_count=713))
    check("B1 {} reply: tick() returns None (no-output branch, as before)", rec is None)
    check("B1 {} reply: exactly one row logged, a no-output skip",
          len(new) == 1 and new[0].get("kind") == "skip" and new[0].get("skip") == "no-output")
    r = new[0] if new else {}
    sent_payload = sent[0]["json"]["messages"][1]["content"] if sent else None
    check("B1 {} reply: cause == 'empty' (was None before J-1709)", r.get("cause") == "empty")
    check("B1 {} reply: payload == the text actually sent (transport capture)",
          sent_payload is not None and r.get("payload") == sent_payload[:PAYLOAD_CAP])
    check("B1 {} reply: payload_chars == full length sent",
          sent_payload is not None and r.get("payload_chars") == len(sent_payload))
    check("B1 {} reply: reply sample logged (head, chars, eval_count, prompt_eval_count)",
          r.get("reply_head") == "{}" and r.get("reply_chars") == 2 and r.get("eval_count") == 2
          and r.get("prompt_eval_count") == 713)
    check("B1 {} reply: every pre-existing skip-row key still present (additive only)",
          OLD_SKIP_KEYS <= set(r))
    check("B1 {} reply: exact new key set = old keys + payload + reply sample",
          set(r) == OLD_SKIP_KEYS | PAYLOAD_KEYS | REPLY_KEYS)
    check("B1 {} reply: had_percepts / model / seat unchanged in value",
          r.get("had_percepts") == ["world"] and r.get("model") == lane2.MODEL and r.get("seat") == lane2.BASE_URL)
    check("B1 {} reply: slot consumed by tick()", _slot() is None)

    # B2 — whitespace then {} through tick: the raw whitespace survives the JSONL round trip, one line per row
    rec, new, sent = await tick_case("ok", reply("\n\t {}\n", eval_count=4, prompt_eval_count=710))
    r = new[0] if new else {}
    check("B2 whitespace-then-{}: cause 'empty', head has the raw whitespace",
          r.get("cause") == "empty" and r.get("reply_head") == "\n\t {}\n")
    n_lines = sum(1 for l in open(lane2._LOG, encoding="utf-8") if l.strip())
    check("B2 the log is still one JSON object per line", n_lines == len(_rows()))

    # B3 — non-JSON reply
    rec, new, sent = await tick_case("ok", reply("sorry, I cannot do that", eval_count=7))
    r = new[0] if new else {}
    check("B3 non-JSON reply: cause == 'parse' with payload and reply sample",
          r.get("cause") == "parse" and PAYLOAD_KEYS <= set(r) and REPLY_KEYS <= set(r)
          and r.get("reply_head") == "sorry, I cannot do that" and r.get("eval_count") == 7)

    # B4 — timeout: payload yes, reply sample no (there is no reply)
    rec, new, sent = await tick_case("timeout")
    r = new[0] if new else {}
    check("B4 timeout: cause == 'timeout' and payload logged",
          r.get("cause") == "timeout" and PAYLOAD_KEYS <= set(r)
          and r.get("payload") == sent[0]["json"]["messages"][1]["content"][:PAYLOAD_CAP])
    check("B4 timeout: no reply-sample keys (nothing came back)", not (REPLY_KEYS & set(r)))

    # B5 — http / connect / exception rows are byte-for-byte the pre-J-1709 shape (no new keys)
    for mode, want in (("http", "http"), ("connect", "http"), ("boom", "exception")):
        rec, new, sent = await tick_case(mode)
        r = new[0] if new else {}
        check(f"B5 {mode}: cause == {want!r} and the row keeps exactly the old key set",
              r.get("cause") == want and set(r) == OLD_SKIP_KEYS)

    # B6 — a long payload is bounded in the row but sent whole
    saved = lane2.percept_lines
    lane2.percept_lines = lambda p: "x" * 1000
    try:
        rec, new, sent = await tick_case("ok", reply("{}"))
    finally:
        lane2.percept_lines = saved
    r = new[0] if new else {}
    sent_payload = sent[0]["json"]["messages"][1]["content"] if sent else ""
    check("B6 long payload: the hub still receives all 1000 chars (behaviour unchanged)",
          len(sent_payload) == 1000)
    check("B6 long payload: row keeps the bounded prefix and the true length",
          r.get("payload") == sent_payload[:PAYLOAD_CAP] and len(r.get("payload", "")) == PAYLOAD_CAP
          and r.get("payload_chars") == 1000)

    # B7 — a hint line is part of what was sent, so it is part of the logged payload
    saved_hint = lane2._consume_hint
    lane2._consume_hint = lambda percepts, now: {"topic": "tide", "kind": "world"}
    try:
        rec, new, sent = await tick_case("ok", reply("{}"))
    finally:
        lane2._consume_hint = saved_hint
    r = new[0] if new else {}
    sent_payload = sent[0]["json"]["messages"][1]["content"] if sent else ""
    check("B7 hint appended: the sent payload carries the hint line and so does the logged payload",
          "One more thing worth a look" in sent_payload and r.get("payload") == sent_payload[:PAYLOAD_CAP]
          and r.get("payload_chars") == len(sent_payload))

    # B8 — stale evidence can never ride onto a later tick's row
    lane2._LAST_ASK_REPLY = {"cause": "empty", "reply_head": "STALE", "reply_chars": 5,
                             "eval_count": 1, "prompt_eval_count": 1}
    rec, new, sent = await tick_case("timeout")
    r = new[0] if new else {}
    check("B8 stale slot + real timeout: the row carries no stale reply keys and the slot is cleared",
          r.get("cause") == "timeout" and not (REPLY_KEYS & set(r)) and _slot() is None)

    # B9 — the 3-tuple contract: a 1-arg stub of _ask (J-1379's own pattern) still drives tick() correctly,
    # and a stale slot whose cause does not match the stub's cause is not attached
    async def _stub(payload_text):
        return (None, 12.34, "parse")

    real_ask = lane2._ask
    lane2._ask = _stub
    lane2._LAST_ASK_REPLY = {"cause": "empty", "reply_head": "STALE", "reply_chars": 5,
                             "eval_count": 1, "prompt_eval_count": 1}
    try:
        rec, new, sent = await tick_case("ok")
    finally:
        lane2._ask = real_ask
    r = new[0] if new else {}
    check("B9 stubbed 3-tuple _ask: row carries cause/elapsed_s/had_percepts and the payload",
          rec is None and r.get("cause") == "parse" and r.get("elapsed_s") == 12.34
          and r.get("had_percepts") == ["world"] and PAYLOAD_KEYS <= set(r))
    check("B9 stubbed 3-tuple _ask: a stale slot with a different cause is NOT attached",
          not (REPLY_KEYS & set(r)) and "STALE" not in json.dumps(r) and _slot() is None)


# ── PART C — status(): the new label shows up in no_output_by_cause_24h ─────────────────────────────
def part_c():
    rows = _rows()
    expect: dict = {}
    for r in rows:
        if r.get("kind") == "skip" and r.get("skip") == "no-output":
            expect[r.get("cause") or "unknown"] = expect.get(r.get("cause") or "unknown", 0) + 1
    # a pre-J-1379-style cause-less row must still land in 'unknown', not vanish
    import time as _t
    now = round(_t.time(), 1)
    with open(lane2._LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now, "kind": "skip", "skip": "no-output"}) + "\n")
        # status() returns its short {"ticks": 0, "skips": ...} dict (no no_output_by_cause_24h key) when the
        # tail holds no tick row at all — pre-existing, untouched here — so one synthetic tick row (the same
        # minimal shape J-1379's check used) makes it take the full path this part is about.
        f.write(json.dumps({"ts": now, "kind": "tick", "run": 2, "notice": "n", "expect_next": "",
                            "grounding": {"grounded_share": 1.0}, "metaphor_flags": None,
                            "invention": {"invention_flag": False}, "coherence": {"verdict": "coherent"},
                            "prior_verdict": "none", "world_fields": ["place"], "expect_is_question": False,
                            "notice_judged": {"verdict": "not_sampled"},
                            "daylight_word_slip": {"night": False}}) + "\n")
    expect["unknown"] = expect.get("unknown", 0) + 1
    st = lane2.status()
    noc = st.get("no_output_by_cause_24h")
    check("C1 status() runs clean and returns a dict", isinstance(st, dict))
    check("C2 no_output_by_cause_24h tallies the 'empty' label the real ticks just logged",
          isinstance(noc, dict) and noc.get("empty", 0) >= 3 and noc.get("empty") == expect.get("empty"))
    check("C3 the whole tally equals what the log holds, label by label", noc == expect)
    check("C4 the cause-less legacy row still lands in 'unknown'", noc.get("unknown") == 1)
    check("C5 pre-existing 'skips' key still counts the same rows",
          isinstance(st.get("skips"), dict) and st["skips"].get("no-output") == sum(expect.values()))
    check("C6 pre-existing 'ticks' key intact (exactly the one synthetic tick row)", st.get("ticks") == 1)


async def main():
    await part_a()
    await part_b()


try:
    asyncio.run(main())
    part_c()
finally:
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect

# ── the hermetic-ness proof ─────────────────────────────────────────────────────────────────────────
check("Z1 core.lane2 data paths were redirected to the temp dir for the whole run",
      str(lane2._LOG).startswith(str(TMP)) and str(lane2._STATE).startswith(str(TMP)))
check("Z2 no non-loopback socket connect was attempted", not _NONLOCAL_CONNECTS)
check("Z3 the fake transport saw every POST (nothing else could have)", len(_SENT) > 0)
check("Z4 this checkout's own data/ watch-list is byte-identical before and after", _snap() == _LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)

n_fail = sum(1 for _, ok in CHECKS if not ok)
print(f"\n{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
