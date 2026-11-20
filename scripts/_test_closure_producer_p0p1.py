"""closure_producer Phase 0 + Phase 1 (core/frontier.py, core/lookup_attach.py, core/web_hand.py, the backfill
script). Hermetic: network stubbed, the embedder stubbed (a deterministic bag-of-words vector), every store and
log under one temp dir. Run: python scripts/_test_closure_producer_p0p1.py"""
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np  # noqa: E402

from core import profile, frontier, lookup_attach, web_hand, web_research, satisfaction  # noqa: E402
from core.memory import store as mem_store  # noqa: E402

_tmp = Path(tempfile.mkdtemp(prefix="closure_producer_test_"))
_DEFAULT_ATTACH_LOG = lookup_attach._LOG
frontier._F = _tmp / "frontier.json"
lookup_attach._LOG = _tmp / "logs" / "lookup_attach.jsonl"
frontier._LEX_SHADOW_LOG = _tmp / "logs" / "lexical_resolve_shadow.jsonl"          # P2-P4 logs, same temp dir
frontier._ANSWERED_MERGE_LOG = _tmp / "logs" / "frontier_answered_merge.jsonl"
web_hand._LOG = _tmp / "lookup_log.jsonl"
web_hand._STATE = _tmp / "lookup_state.json"
satisfaction.record = lambda *a, **k: None

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def under_tmp(p) -> bool:
    return str(Path(p).resolve()).lower().startswith(str(_tmp.resolve()).lower())


# ── every path this test can write resolves under the temp dir ──
check("frontier store path under temp", under_tmp(frontier._F) and under_tmp(profile.guard_path(frontier._F)))
check("frontier light path under temp", under_tmp(frontier._light_path()))
check("attach log path under temp", under_tmp(profile.guard_path(lookup_attach._LOG)))
check("hand log + state under temp", under_tmp(web_hand._LOG) and under_tmp(web_hand._STATE))
try:
    profile.guard_path(_DEFAULT_ATTACH_LOG)
    check("default attach log path is fenced in a non-live process", False)
except profile.NonLiveWriteError:
    check("default attach log path is fenced in a non-live process", True)


# ── stubs: embedder, memory store, network ──
def _vec(text):
    v = np.zeros(512, dtype=np.float32)
    for w in "".join(ch if ch.isalnum() else " " for ch in (text or "").lower()).split():
        if len(w) > 2:
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1.0
    n = float(np.linalg.norm(v))
    return v / n if n else None


mem_store._embed_batch = lambda texts: [_vec(t) for t in texts]
stored = []
web_research.store_finding = lambda title, extract, via, extra_keywords=None: stored.append(("wiki", title))
web_research.store_web_results = lambda phrase, body: stored.append(("web", phrase))
_PAGE = "The myrtle warbler is a small New World warbler with a yellow rump. " * 12
web_research.wiki_titles = lambda phrase, limit=3: ["Myrtle warbler"]
web_research.wiki_page = lambda t: (t, _PAGE)
web_research.web_search = lambda phrase, limit=10: [
    {"title": "Field guide", "url": "https://audubon.org/c", "domain": "audubon.org", "snippet": "A field guide note."}]

NOW = time.time()


def q(qid, text, status="open", **kw):
    row = {"id": qid, "q": text, "source": "curiosity", "toks": sorted(frontier._toks(text)), "born": NOW - 7200,
           "last_seen": NOW - 7200, "last_offered": 0, "offers": 0, "encounters": 1, "status": status}
    row.update(kw)
    return row


def write_store(rows):
    frontier._F.write_text(json.dumps({"questions": rows}), encoding="utf-8")
    frontier._SEM_VEC_CACHE.clear()


def load():
    return {r["id"]: r for r in json.loads(frontier._F.read_text(encoding="utf-8"))["questions"]}


def reset_hand():
    web_hand._last.clear()
    if web_hand._STATE.exists():
        web_hand._STATE.unlink()
    web_hand.take_pending()


def attach_rows():
    if not lookup_attach._LOG.exists():
        return []
    return [json.loads(x) for x in lookup_attach._LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


# ── Phase 0: the lexical close writes resolved_how ──
write_store([q("lex1", "Why does granite weather into rounded boulders?")])
os.environ["NASCENCE_LEXICAL_RESOLVE"] = "close"   # P2 made "shadow" the default; this check is of the old close path
got = frontier.resolve_if_addressed("Now I understand: granite weathers into rounded boulders because water works the joints.")
os.environ.pop("NASCENCE_LEXICAL_RESOLVE")
row = load()["lex1"]
check("lexical close still closes (returns the question)", got == "Why does granite weather into rounded boulders?")
check("lexical close writes resolved_how='lexical'", row["status"] == "resolved" and row.get("resolved_how") == "lexical")
write_store([q("ln1", "Where do swifts sleep?")])
check("resolve(how='line') unchanged", frontier.resolve("ln1") and load()["ln1"]["resolved_how"] == "line")

# ── Phase 0: breakdown on a synthetic store, legacy rows included ──
LOOK = dict(finding="x", finding_title="t", finding_ts=5.0, finding_source="lookup", finding_source_ts=5.0)
write_store([
    q("a", "legacy one", "resolved", resolved_ts=1.0),
    q("b", "legacy two", "resolved", resolved_ts=1.0, finding="memory", finding_title="what you found in your own memory", finding_ts=2.0),
    q("c", "labelled lexical", "resolved", resolved_ts=1.0, resolved_how="lexical", **LOOK),
    q("d", "line one", "resolved", resolved_ts=1.0, resolved_how="line"),
    q("e", "line two", "resolved", resolved_ts=1.0, resolved_how="line", **LOOK),
    q("f", "lookup", "resolved", resolved_ts=1.0, resolved_how="lookup", **LOOK),
    q("g", "told", "resolved", resolved_ts=1.0, resolved_how="told"),
    q("h", "odd", "resolved", resolved_ts=1.0, resolved_how="something_else"),
    # a lookup marker whose finding was overwritten later (finding_ts moved): must NOT count
    q("i", "stale marker", "resolved", resolved_ts=1.0, resolved_how="line", finding="memory", finding_title="m",
      finding_ts=9.0, finding_source="lookup", finding_source_ts=5.0),
    q("j", "open with lookup finding", "open", **LOOK),
    q("k", "open plain", "open"),
    q("l", "faded", "faded"),
])
before_bytes = frontier._F.read_bytes()
bd = frontier.resolved_breakdown()
_P0_KEYS = ("resolved", "lexical", "unlabelled", "lexical_total", "line", "lookup", "told", "other",
            "answered_with_source", "open_with_lookup_finding")     # P4 added keys beside these; these are unchanged
check(f"breakdown counts ({bd})",
      {k: bd[k] for k in _P0_KEYS} == {"resolved": 9, "lexical": 1, "unlabelled": 2, "lexical_total": 3, "line": 3, "lookup": 1, "told": 1,
             "other": 1, "answered_with_source": 3, "open_with_lookup_finding": 1})
check("breakdown is read-only (file bytes unchanged)", frontier._F.read_bytes() == before_bytes)
check("breakdown accepts a passed dict", frontier.resolved_breakdown({"questions": []})["resolved"] == 0)

# ── Phase 0: the backfill script, dry run then write, on the temp file only ──
import closure_producer_backfill_lexical as bf  # noqa: E402
check("backfill dry run exits 0 and writes nothing",
      bf.main(["--file", str(frontier._F)]) == 0 and frontier._F.read_bytes() == before_bytes)
check("backfill --write exits 0", bf.main(["--file", str(frontier._F), "--write"]) == 0)
rows = load()
check("backfill labelled the two legacy rows only",
      rows["a"]["resolved_how"] == "lexical" and rows["b"]["resolved_how"] == "lexical"
      and rows["a"].get("resolved_how_backfilled") is True and rows["d"]["resolved_how"] == "line"
      and "resolved_how" not in rows["k"] and "resolved_how_backfilled" not in rows["c"])
check("backfill kept a backup beside the file", any(".bak_closure_producer_" in p.name for p in _tmp.iterdir()))
bd = frontier.resolved_breakdown()
check("after backfill: unlabelled 0, lexical 3", bd["unlabelled"] == 0 and bd["lexical"] == 3)
_real_fp = bf._fingerprint
_n = {"n": 0}


def _moving_fp(path):
    _n["n"] += 1
    return (_n["n"], 0, "x")


write_store([q("a", "legacy one", "resolved", resolved_ts=1.0)])
bf._fingerprint = _moving_fp
rc = bf.main(["--file", str(frontier._F), "--write"])
bf._fingerprint = _real_fp
check("backfill refuses when the file changed during the run", rc == 3 and "resolved_how" not in load()["a"])

# ── Phase 1: above the threshold the result is attached and the question stays open ──
Q_WARBLER = "Why does the myrtle warbler carry a yellow rump?"
Q_GRANITE = "How do lichens colonise bare granite over centuries?"
write_store([q("w1", Q_WARBLER), q("g1", Q_GRANITE), q("r1", "the myrtle warbler yellow rump", "resolved", resolved_ts=1.0)])
m = lookup_attach.best_open_match("the myrtle warbler yellow rump", "Myrtle warbler")
check(f"best match is the open warbler question, never the resolved twin (score {m['score']})",
      m["qid"] == "w1" and m["score"] >= lookup_attach.ATTACH_THRESHOLD and m["open_n"] == 2)
reset_hand()
ans = web_hand.consult("I will look up the myrtle warbler yellow rump on Wikipedia.")
row = load()["w1"]
check("hand answered normally", bool(ans) and ans.startswith('You asked Wikipedia about "the myrtle warbler yellow rump".'))
check("finding attached", row.get("finding", "").startswith("The myrtle warbler is a small") and len(row["finding"]) <= 600)
check("question still OPEN, no resolved_how", row["status"] == "open" and "resolved_how" not in row and "resolved_ts" not in row)
check("finding marked as from a lookup, with source, title, url and his phrase",
      row.get("finding_source") == "lookup" and row.get("finding_via") == "wikipedia"
      and row.get("finding_url") == "en.wikipedia.org/wiki/Myrtle_warbler"
      and row.get("finding_phrase") == "the myrtle warbler yellow rump" and frontier.finding_from_lookup(row))
check(f"finding title is truthful ({row.get('finding_title')!r})",
      row.get("finding_title") == 'the Wikipedia page "Myrtle warbler" (you looked it up)'
      and "memory" not in row["finding_title"])
check("the other open question untouched", "finding" not in load()["g1"])
lr = attach_rows()
check("one attach log row under temp, attached true",
      len(lr) == 1 and lr[0]["attached"] is True and lr[0]["best_qid"] == "w1" and lr[0]["phrase"] == "the myrtle warbler yellow rump"
      and lr[0]["title"] == "Myrtle warbler" and lr[0]["best_score"] >= lookup_attach.ATTACH_THRESHOLD
      and under_tmp(lookup_attach._LOG))
check("open_with_lookup_finding counted", frontier.resolved_breakdown()["open_with_lookup_finding"] == 1)
seed = frontier.closeable_seed()
check("what returns to him carries the truthful title", bool(seed) and seed["finding_title"].startswith("the Wikipedia page"))
# a later attach by another writer (the Follow Line's expiry) makes the marker stale
frontier.attach_finding("w1", "what you found in your own memory", "an old thought")
check("an overwritten finding no longer counts as from a lookup", not frontier.finding_from_lookup(load()["w1"]))

# ── below the threshold: no attach, logged ──
write_store([q("w1", Q_WARBLER), q("g1", Q_GRANITE)])
reset_hand()
ans = web_hand.consult("I will look up porcupine quills on Wikipedia.")
lr = attach_rows()
check("below threshold: hand answers, nothing attached", bool(ans) and all("finding" not in r for r in load().values()))
check("below threshold: logged attached false with the best score",
      len(lr) == 2 and lr[-1]["attached"] is False and lr[-1]["best_score"] is not None
      and lr[-1]["best_score"] < lookup_attach.ATTACH_THRESHOLD)

# ── web source: attaches with the web label ──
reset_hand()
ans = web_hand.consult("I will search the web for the myrtle warbler yellow rump.")
row = load()["w1"]
check("web result attached, labelled as a web search, still open",
      bool(ans) and row.get("finding_via") == "web" and row["finding_title"].startswith('a web search for "')
      and "not checked" in row["finding_title"] and row["status"] == "open" and row.get("finding_url") == "https://audubon.org/c")

# ── no open question: logged, nothing attached ──
write_store([q("r1", "the myrtle warbler yellow rump", "resolved", resolved_ts=1.0)])
reset_hand()
n0 = len(attach_rows())
ans = web_hand.consult("I will look up the myrtle warbler yellow rump on Wikipedia.")
lr = attach_rows()
check("no open question: hand answers, row logged, best_qid None",
      bool(ans) and len(lr) == n0 + 1 and lr[-1]["best_qid"] is None and lr[-1]["attached"] is False
      and "finding" not in load()["r1"])

# ── kill switch ──
write_store([q("w1", Q_WARBLER)])
reset_hand()
n0 = len(attach_rows())
os.environ["NASCENCE_LOOKUP_ATTACH"] = "0"
ans = web_hand.consult("I will look up the myrtle warbler yellow rump on Wikipedia.")
os.environ.pop("NASCENCE_LOOKUP_ATTACH")
check("kill switch: hand answers, no attach, no log row",
      bool(ans) and "finding" not in load()["w1"] and len(attach_rows()) == n0)

# ── the hand survives an attach that raises ──
reset_hand()
_real = lookup_attach.note_lookup


def _boom(*a, **k):
    raise RuntimeError("attach blew up")


lookup_attach.note_lookup = _boom
ans = web_hand.consult("I will look up the myrtle warbler yellow rump on Wikipedia.")
lookup_attach.note_lookup = _real
check("hand returns its normal answer when attach raises",
      bool(ans) and ans.startswith('You asked Wikipedia about') and web_hand.take_pending() is True)
reset_hand()
_real_match = lookup_attach.best_open_match
lookup_attach.best_open_match = _boom
n0 = len(attach_rows())
ans = web_hand.consult("I will look up the myrtle warbler yellow rump on Wikipedia.")
lookup_attach.best_open_match = _real_match
lr = attach_rows()
check("an error inside the match is logged, not raised",
      bool(ans) and len(lr) == n0 + 1 and "attach blew up" in lr[-1].get("error", "") and lr[-1]["attached"] is False)

# ── nothing landed outside the temp dir ──
_wt_data = Path(__file__).resolve().parent.parent / "data"
check("no lookup_attach log under this checkout's data/", not (_wt_data / "logs" / "lookup_attach.jsonl").exists()
      or _wt_data.resolve() == Path("C:/Nascence/data").resolve())

print()
print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
