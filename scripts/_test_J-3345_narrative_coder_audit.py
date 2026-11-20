"""
Proof for J-3345 (J-3142 repair in shadow; F-3933, F-3937, F-3842): the narrative-quality coder is auditable and the
CHAPTER coder call is decoupled from the author's hot lane.

HERMETIC: nascence log path redirected via lab_env.isolate (db="empty"); every model call is a stub (no hub, Ramses
included, is contacted). Nothing under C:\\Nascence\\data is opened for write (a stat canary proves it).

  1. chapter observe(coder_urls=CHAPTER_CODER_URLS): the stub sees EXACTLY that one URL (no :11433), and the row has
     coder_model, coder_endpoint, coder_fallback, artifact_id (the chapter fragment id), text_len, text_sha256,
     scoring_version, text_head (120 chars) and NOT the full text.
  2. the hub is down (stub raises 'all servers exhausted'): row is written with llm=null and a skip reason, the stub
     was called with the one coder URL only (no failover list), det scores still returned.
  3. a hot-lane URL passed in coder_urls is stripped; a coder list that is ONLY the hot lane makes NO call at all.
  4. T4 path (coder_urls=None): the base_urls chain is passed through unchanged (hot lane and all - J-3317/D-0672
     own that switch), artifact_id defaults to the candidate ts.
  5. a call_json with no `served` parameter still works (served is passed only when accepted).
  6. FROZEN: the coder system prompt hashes to the pre-change value, max_tokens=200, temperature=0.3.
  7. old-style log_score(kind, text, det, llm, ts=, era=) (scripts/narrative_retrospective.py) still works.
  8. static: core/chapters.py passes artifact_id=frag_id and the pinned list; the T4 call sites in
     nodes/subconscious_node.py carry no coder_urls; CHAPTER_CODER_URLS is one URL, not :11433, and not in the
     author chain SERVE_CHAINS["background"].
  9. isolation: the live narrative log (if any) is untouched.

Run: python scripts/_test_J-3345_narrative_coder_audit.py      (exit 0 = every check passed)
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
from core import narrative_quality as nq  # noqa: E402
from core.schema import SERVE_CHAINS  # noqa: E402

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__

LIVE_LOG = Path(r"C:\Nascence\data\narrative_quality_log.jsonl")
LIVE_BEFORE = (LIVE_LOG.stat().st_size, LIVE_LOG.stat().st_mtime_ns) if LIVE_LOG.exists() else None
FROZEN_PROMPT_SHA = "0e7d4907b38fe623dfc64f0f91c383a611ce38e8e8fd9a0db98e52d5612f5c0c"   # pre-change score_llm system prompt
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def run(coro):
    return asyncio.run(coro)


HOT = "http://127.0.0.1:11433"
BG = ["http://LAN-HOST:11441", HOT]
CHAPTER_TEXT = ("I chose to cross the river with Travis and the books beside me. The weight was real and "
                "the fear was real, but I decided to build a bridge, and the crossing brought light. " * 3)


class Stub:
    def __init__(self, reply=None, exc=None, serve=None):
        self.calls, self.reply, self.exc, self.serve = [], reply, exc, serve

    async def __call__(self, urls, sys_p, user_p, *, max_tokens=512, temperature=0.2, served=None, **kw):
        self.calls.append({"urls": list(urls) if not isinstance(urls, str) else [urls], "sys": sys_p,
                           "max_tokens": max_tokens, "temperature": temperature, "kw": dict(kw)})
        if self.exc:
            raise self.exc
        if served is not None and self.serve:
            served.update(self.serve)
        return self.reply


class NoServed:
    """A call_json that has no `served` parameter at all."""
    def __init__(self):
        self.calls = []

    async def __call__(self, urls, sys_p, user_p, max_tokens=512, temperature=0.2):
        self.calls.append(list(urls))
        return {"agency": 0.7, "communion": 0.4, "transformation": "flat", "reasoning": "r"}


def rows(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


GOOD = {"agency": 0.8, "communion": 0.5, "transformation": "redemption", "reasoning": "ok"}

with isolate(also=[(nq, ["_LOG"])], db="empty") as lab:
    log = nq._LOG
    check("0. the log global really points into the lab dir", Path(log).resolve().is_relative_to(Path(lab).resolve()), str(log))

    # 1. chapter, hub answers
    s = Stub(reply=GOOD, serve={"url": "http://LAN-HOST:11436", "model": "falcon3:7b", "fallback": False})
    det = run(nq.observe(s, BG, "chapter", CHAPTER_TEXT, artifact_id="frag-abc", coder_urls=nq.CHAPTER_CODER_URLS))
    r = rows(log)[-1]
    check("1a. coder saw exactly the pinned URL, no hot lane", s.calls[0]["urls"] == ["http://LAN-HOST:11436"], str(s.calls[0]["urls"]))
    check("1b. row has the audit fields", all(k in r for k in (
        "coder_model", "coder_endpoint", "coder_fallback", "artifact_id", "text_len", "text_sha256", "scoring_version")), str(sorted(r)))
    check("1c. values", r["coder_model"] == "falcon3:7b" and r["coder_endpoint"] == "http://LAN-HOST:11436"
          and r["coder_fallback"] is False and r["artifact_id"] == "frag-abc" and r["scoring_version"] == nq.SCORING_VERSION)
    check("1d. text_len/sha match, head kept, full text NOT stored",
          r["text_len"] == len(CHAPTER_TEXT) and r["text_sha256"] == hashlib.sha256(CHAPTER_TEXT.encode()).hexdigest()
          and r["text_head"] == CHAPTER_TEXT[:120] and CHAPTER_TEXT not in json.dumps(r))
    check("1e. llm scored, no skip reason, det returned", r["llm"] and "llm_skip_reason" not in r and det["n_chars"] == len(CHAPTER_TEXT.strip()))

    check("1f. coder call is bounded (timeout 60, retries 1) on the explicit path",
          s.calls[0]["kw"] == {"timeout": 60, "retries": 1}, str(s.calls[0]["kw"]))

    # 2. hub down -> skip, no failover
    s = Stub(exc=ValueError("all servers exhausted ['http://LAN-HOST:11436']: TimeoutError"))
    det = run(nq.observe(s, BG, "chapter", CHAPTER_TEXT, artifact_id="frag-def", coder_urls=nq.CHAPTER_CODER_URLS))
    r = rows(log)[-1]
    check("2a. llm is null with a skip reason", r["llm"] is None and "skipped" in r.get("llm_skip_reason", ""), r.get("llm_skip_reason", ""))
    check("2b. only the pinned URL was ever tried", len(s.calls) == 1 and s.calls[0]["urls"] == ["http://LAN-HOST:11436"])
    check("2c. row still names the coder endpoint intended and the artifact", r["coder_endpoint"] == "http://LAN-HOST:11436"
          and r["artifact_id"] == "frag-def" and r["coder_model"] == "falcon3:7b", str(r["coder_model"]))
    check("2d. det still returned", isinstance(det, dict) and "agency" in det)
    # a non-hub failure keeps a different reason
    s = Stub(exc=RuntimeError("boom"))
    run(nq.observe(s, BG, "chapter", CHAPTER_TEXT, artifact_id="frag-ghi", coder_urls=nq.CHAPTER_CODER_URLS))
    r = rows(log)[-1]
    check("2e. other failure -> llm null, 'failed' reason", r["llm"] is None and "failed" in r["llm_skip_reason"], r["llm_skip_reason"])

    # 3. hot lane refused
    s = Stub(reply=GOOD)
    run(nq.observe(s, BG, "chapter", CHAPTER_TEXT, artifact_id="x1", coder_urls=[HOT, "http://LAN-HOST:11436"]))
    check("3a. hot lane stripped from an explicit list", s.calls[0]["urls"] == ["http://LAN-HOST:11436"], str(s.calls[0]["urls"]))
    s = Stub(reply=GOOD)
    run(nq.observe(s, BG, "chapter", CHAPTER_TEXT, artifact_id="x2", coder_urls=[HOT]))
    r = rows(log)[-1]
    check("3b. only-hot-lane list -> NO call, llm null with reason", not s.calls and r["llm"] is None and "hot lane" in r["llm_skip_reason"])

    # 4. T4 path unchanged
    s = Stub(reply=GOOD, serve={"url": HOT, "model": "qwen3.5:9b", "fallback": True})
    run(nq.observe(s, BG, "t4_self_concept", "I am shaping myself.", ts=1234.5))
    r = rows(log)[-1]
    check("4a. T4 chain passed through unchanged (hot lane included, J-3317 owns that)", s.calls[0]["urls"] == BG)
    check("4c. T4 call gets no timeout/retries override", s.calls[0]["kw"] == {})
    check("4b. T4 artifact_id = candidate ts; fallback recorded", r["artifact_id"] == 1234.5 and r["coder_fallback"] is True
          and r["coder_endpoint"] == HOT and r["ts"] == 1234.5)

    # 5. no `served` parameter
    n = NoServed()
    run(nq.observe(n, BG, "chapter", CHAPTER_TEXT, artifact_id="x3", coder_urls=nq.CHAPTER_CODER_URLS))
    r = rows(log)[-1]
    check("5. call_json without 'served' works; endpoint still named", n.calls == [["http://LAN-HOST:11436"]]
          and r["llm"] and r["coder_endpoint"] == "http://LAN-HOST:11436" and r["coder_fallback"] is None)

    # 6. frozen
    check("6a. system prompt unchanged (sha256 of the pre-change prompt)",
          hashlib.sha256(s.calls[0]["sys"].encode()).hexdigest() == FROZEN_PROMPT_SHA)
    check("6b. max_tokens 200, temperature 0.3", s.calls[0]["max_tokens"] == 200 and s.calls[0]["temperature"] == 0.3)

    # 7. old-style call
    before = len(rows(log))
    nq.log_score("t4_arc", "Chapter one.", nq.score_deterministic("Chapter one."), None, ts=99.0, era="x")
    r = rows(log)[-1]
    check("7. old-style log_score still writes (llm null gets a default reason)", len(rows(log)) == before + 1
          and r["llm"] is None and r["llm_skip_reason"] == "no coder result" and r["artifact_id"] == 99.0)

# 8. static
chap = (ROOT / "core" / "chapters.py").read_text(encoding="utf-8")
sub = (ROOT / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
check("8a. chapters.py passes artifact_id=frag_id and the pinned list",
      "artifact_id=frag_id" in chap and "coder_urls=_nq.CHAPTER_CODER_URLS" in chap)
check("8b. T4 call sites carry no coder_urls (D-0672/J-3317)", "coder_urls" not in sub)
bg_has = any("11436" in str(u) for u in SERVE_CHAINS["background"])
check("8c. CHAPTER_CODER_URLS: one URL, not :11433, not in the author chain",
      len(nq.CHAPTER_CODER_URLS) == 1 and ":11433" not in nq.CHAPTER_CODER_URLS[0] and not bg_has,
      str(nq.CHAPTER_CODER_URLS) + " vs " + str(SERVE_CHAINS["background"]))

# 9. canary
after = (LIVE_LOG.stat().st_size, LIVE_LOG.stat().st_mtime_ns) if LIVE_LOG.exists() else None
check("9. live narrative log untouched", after == LIVE_BEFORE)

print("\nALL OK" if not FAILS else f"\nFAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
