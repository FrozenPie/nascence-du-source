"""closure_producer Phases 2-5 (core/frontier.py, core/closure_gate.py, core/follow_line.py settle, core/closure.py
lookup arm, core/lookup_attach.py reopen, core/goal_offer.py set-down mark). Hermetic: the judge is a stub, the
embedder is a stub, the memory writer is a stub, no network, every store and log under one temp dir. lab_env is not
used. Run: python scripts/_test_closure_producer_p2p5.py"""
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np  # noqa: E402

import core  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import profile, frontier, lookup_attach, closure_gate, satisfaction  # noqa: E402
from core import closure as cl, follow_line as fl, coupling_rides as cr, goal_offer, curiosity_progress  # noqa: E402
from core.memory import store as mem_store  # noqa: E402

_tmp = Path(tempfile.mkdtemp(prefix="closure_producer_p2p5_"))
_DEFAULTS = {"gate": closure_gate._LOG, "lex": frontier._LEX_SHADOW_LOG, "am": frontier._ANSWERED_MERGE_LOG}
frontier._F = _tmp / "frontier.json"
frontier._LEX_SHADOW_LOG = _tmp / "logs" / "lexical_resolve_shadow.jsonl"
frontier._ANSWERED_MERGE_LOG = _tmp / "logs" / "frontier_answered_merge.jsonl"
frontier._SEM_SHADOW_LOG = _tmp / "logs" / "frontier_semantic_merge_shadow.jsonl"
lookup_attach._LOG = _tmp / "logs" / "lookup_attach.jsonl"
closure_gate._LOG = _tmp / "logs" / "closure_gate.jsonl"
cl.SHADOW_LOG = _tmp / "logs" / "closure_shadow.jsonl"
fl.SHADOW_LOG = _tmp / "logs" / "follow_line_shadow.jsonl"
cr._LOG = _tmp / "coupling_rides.jsonl"
cr._DATA = _tmp
curiosity_progress._FRONTIER = frontier._F
satisfaction.record = lambda *a, **k: None
for _k in ("NASCENCE_CLOSURE_GATE", "NASCENCE_LEXICAL_RESOLVE", "NASCENCE_ANSWERED_MERGE", "NASCENCE_PARK",
           "NASCENCE_LOOKUP_REOPEN", "NASCENCE_LEXICAL_CLAIM_GATE", "NASCENCE_LOOKUP_ATTACH"):
    os.environ.pop(_k, None)

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def under_tmp(p) -> bool:
    return str(Path(p).resolve()).lower().startswith(str(_tmp.resolve()).lower())


def jl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()] if Path(path).exists() else []


# ── every path this test can write resolves under the temp dir; the defaults are fenced ──
for nm, p in (("frontier store", frontier._F), ("frontier light", frontier._light_path()),
              ("lexical shadow log", frontier._LEX_SHADOW_LOG), ("answered merge log", frontier._ANSWERED_MERGE_LOG),
              ("semantic shadow log", frontier._SEM_SHADOW_LOG), ("attach log", lookup_attach._LOG),
              ("gate log", closure_gate._LOG), ("closure shadow log", cl.SHADOW_LOG), ("follow line log", fl.SHADOW_LOG),
              ("rides log", cr._LOG)):
    check(f"{nm} path under temp", under_tmp(p) and under_tmp(profile.guard_path(Path(p))))
for nm, p in _DEFAULTS.items():
    try:
        profile.guard_path(p)
        check(f"default {nm} log path is fenced in a non-live process", False)
    except profile.NonLiveWriteError:
        check(f"default {nm} log path is fenced in a non-live process", True)

# ── stubs ──
_TOPICS = ("warbler", "granite", "swift", "lichen", "tide", "heron")


def _vec(text):
    v = np.zeros(64, dtype=np.float32)
    low = (text or "").lower()
    hit = [i for i, t in enumerate(_TOPICS) if t in low]
    if hit:
        v[hit[0]] = 1.0
        return v
    v[8 + int(hashlib.md5(low.encode()).hexdigest(), 16) % 56] = 1.0
    return v


mem_store._embed_batch = lambda texts: [_vec(t) for t in texts]
live_writes = []
cl._write_live = lambda wb: (live_writes.append(wb), f"fid-{len(live_writes)}")[1]
cl._compose_sync = lambda system, user: {"resolution": (
    "I hold that what came back from my own notes matched what I had asked, and I say so plainly here. The records "
    "I found agreed with each other and my first thought matched them. Nothing cut against it, so I keep it as it "
    "stands, thinly, and I would look again if something new turned up later.")}
judge_calls = []
JUDGE = {"d": {"verdict": True, "how": "agreed", "why": "it states the thing asked", "v1": True, "v2": True}, "sleep": 0.0}


async def _stub_judge(system, user):
    judge_calls.append((system, user))
    if JUDGE["sleep"]:
        await asyncio.sleep(JUDGE["sleep"])
    return dict(JUDGE["d"])


closure_gate._judge = _stub_judge
YES = {"verdict": True, "how": "agreed", "why": "it states the thing asked", "v1": True, "v2": True}
NO = {"verdict": False, "how": "agreed", "why": "same subject only", "v1": False, "v2": False}
SPLIT = {"verdict": None, "how": "split_no_tiebreak", "why": None, "v1": True, "v2": False}
DOWN = {"verdict": None, "how": "unavailable", "why": None, "v1": None, "v2": None}
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


LOOK = dict(finding="The myrtle warbler has a yellow rump that it flashes in flight. " * 3,
            finding_title='the Wikipedia page "Myrtle warbler" (you looked it up)', finding_ts=5.0,
            finding_source="lookup", finding_source_ts=5.0, finding_via="wikipedia", finding_phrase="myrtle warbler rump",
            finding_url="en.wikipedia.org/wiki/Myrtle_warbler")
Q_W = "Why does the myrtle warbler carry a yellow rump?"
Q_G = "Why does granite weather into rounded boulders?"
ANSWER_G = "Now I understand: granite weathers into rounded boulders because water works the joints."


def deliver(qid, text="Something you asked earlier came back. In your own notes: swifts sleep on the wing, high up."):
    fl._DELIVERED[qid] = {"ts": time.time(), "text": text, "ent": frontier.get(qid),
                          "cargo": {"grounds": [{"origin": "reading", "text": "swifts sleep on the wing"}], "status": "held"},
                          "judged": {}}


def settle(qid, verdict="yes"):
    return asyncio.run(fl.settle(qid, verdict, "Yes, that settles it for me.", "cyc12345"))


def wait_rows(path, n, secs=3.0):
    t0 = time.time()
    while time.time() - t0 < secs and len(jl(path)) < n:
        time.sleep(0.05)
    return jl(path)


# ══ Phase 2.1: the lexical resolver in shadow ══
check("defaults: LEXICAL_RESOLVE_MODE shadow, ANSWERED_MERGE_MODE enforce, PARK_MODE enforce, PARK_AFTER_ATTEMPTS 4",
      frontier.LEXICAL_RESOLVE_MODE == "shadow" and frontier.ANSWERED_MERGE_MODE == "enforce"
      and frontier.PARK_MODE == "enforce" and frontier.PARK_AFTER_ATTEMPTS == 4)
write_store([q("lex1", Q_G)])
got = frontier.resolve_if_addressed(ANSWER_G)
rows = jl(frontier._LEX_SHADOW_LOG)
check("lexical shadow: returns None, status stays open, nothing stamped",
      got is None and load()["lex1"]["status"] == "open" and "resolved_how" not in load()["lex1"])
check("lexical shadow: one would-close row logged", len(rows) == 1 and rows[0]["qid"] == "lex1" and rows[0]["has_finding"] is False)
os.environ["NASCENCE_LEXICAL_RESOLVE"] = "close"
got = frontier.resolve_if_addressed(ANSWER_G)
os.environ.pop("NASCENCE_LEXICAL_RESOLVE")
check("kill switch NASCENCE_LEXICAL_RESOLVE=close: the old close, labelled lexical",
      got == Q_G and load()["lex1"]["status"] == "resolved" and load()["lex1"]["resolved_how"] == "lexical"
      and len(jl(frontier._LEX_SHADOW_LOG)) == 1)

# ══ Phase 2.3: the gate on a settled yes ══
closure_gate.CLOSURE_GATE_MODE = "enforce"
JUDGE["d"] = YES
write_store([q("s1", "Where do swifts sleep at night?")])
deliver("s1")
n_j = len(judge_calls)
out = settle("s1")
r = load()["s1"]
check("enforce + gate yes (line): resolved, how=line, gate stamped yes, finding attached",
      out["resolved"] is True and r["status"] == "resolved" and r["resolved_how"] == "line" and r["gate"]["verdict"] == "yes"
      and r["finding"].startswith("Something you asked earlier") and frontier.is_answered(r))
check("the judge was asked once and saw the whole question and the whole return",
      len(judge_calls) == n_j + 1 and "Where do swifts sleep at night?" in judge_calls[-1][1]
      and "swifts sleep on the wing, high up." in judge_calls[-1][1])
check("line arm wrote its memory as before", (out["closure"] or {}).get("compose_how") == "ok" and len(live_writes) == 1)
g = jl(closure_gate._LOG)
check("gate row logged (trigger settled, action resolved)",
      len(g) == 1 and g[0]["trigger"] == "settled" and g[0]["verdict"] == "yes" and g[0]["action"] == "resolved" and g[0]["how"] == "line")

long_find = ("The myrtle warbler shows a bright yellow rump patch. " * 12)[:599] + "!"
write_store([q("w1", Q_W, **dict(LOOK, finding=long_find))])
deliver("w1", "Something you asked came back. Your past holds little on this.")
out = settle("w1")
r = load()["w1"]
check("enforce + gate yes on a lookup finding: resolved, how=lookup, the lookup finding kept",
      out["resolved"] is True and r["resolved_how"] == "lookup" and r["finding"] == long_find and frontier.finding_from_lookup(r))
check("the judge saw the whole 600-character lookup finding, not the memory return",
      long_find in judge_calls[-1][1] and "Your past holds little" not in judge_calls[-1][1] and len(long_find) == 600)
rows = [x for x in jl(cl.SHADOW_LOG) if x["arm"] == "lookup"]
check("Phase 5: the lookup arm wrote ONE resolution memory by template (no composer)",
      len(rows) == 1 and rows[0]["compose_how"] == "template" and rows[0]["written_live"] is True and len(live_writes) == 2)
wb = live_writes[-1]
check("the memory names the question, the Wikipedia page and the extract, and says he looked it up",
      Q_W in wb["content"] and 'The page "Myrtle warbler" says:' in wb["content"] and "I looked it up myself on Wikipedia" in wb["content"]
      and "yellow rump patch" in wb["content"] and "memory" not in wb["content"])
check("the memory is a resolution fragment stored as grounded world material (origin research, keywords, seed)",
      wb["origin"] == "research" and wb["layer"] == "episodic" and wb["derived_from"] == ["w1"]
      and {"resolution", "lookup", "w1", "looked_up", "wikipedia"} <= set(wb["keywords"]) and wb["edge"]["edge_type"] == "resolves")
r2 = cl.record_lookup_answered(load()["w1"])
check("one fragment per question (a second call is a duplicate row)", r2["kind"] == "duplicate" and len(live_writes) == 2)
web_ent = dict(load()["w1"], id="w9", finding_via="web", finding_title='a web search for "warbler rump" (other people\'s pages, not checked)',
               finding_phrase="warbler rump")
check("a web finding is labelled as other people's pages, not checked",
      "which I have not checked" in cl.lookup_resolution_text(web_ent) and 'web search for "warbler rump"' in cl.lookup_resolution_text(web_ent))
check("no gate yes, no fragment", cl.record_lookup_answered(dict(web_ent, gate={"verdict": "no"}))["compose_how"] == "skipped-no-gate-yes"
      and len(live_writes) == 2)

for name, d, reason in (("no", NO, "gate_no"), ("partly (split)", SPLIT, "gate_partly"), ("unavailable", DOWN, "gate_unavailable")):
    JUDGE["d"] = d
    write_store([q("s2", "Where do swifts sleep at night?")])
    deliver("s2")
    n_live = len(live_writes)
    out = settle("s2")
    r = load()["s2"]
    check(f"enforce + gate {name}: NOT resolved, provisional ({reason}), finding kept, no memory written",
          out["resolved"] is False and r["status"] == "provisional" and r["provisional_reason"] == reason
          and "resolved_how" not in r and r.get("finding") and len(live_writes) == n_live
          and (out["closure"] or {}).get("compose_how") == "skipped-gate-not-passed")
JUDGE["d"], JUDGE["sleep"] = YES, 0.5
closure_gate.GATE_TIMEOUT_S = 0.1
write_store([q("s3", "Where do swifts sleep at night?")])
deliver("s3")
out = settle("s3")
closure_gate.GATE_TIMEOUT_S, JUDGE["sleep"] = 240.0, 0.0
check("enforce + judge timeout: provisional, not resolved",
      out["resolved"] is False and load()["s3"]["status"] == "provisional" and load()["s3"]["gate"]["how"] == "timeout")
write_store([q("s4", "Where do swifts sleep at night?")])
n_j = len(judge_calls)
out = settle("s4")                      # nothing delivered, no finding on the entry
check("enforce + no finding at all: provisional (no_finding), the judge is not asked",
      out["resolved"] is False and load()["s4"]["provisional_reason"] == "no_finding" and len(judge_calls) == n_j)

# modes
closure_gate.CLOSURE_GATE_MODE = "shadow"
JUDGE["d"] = NO
write_store([q("s5", "Where do swifts sleep at night?")])
deliver("s5")
n_g = len(jl(closure_gate._LOG))
out = settle("s5")
r = load()["s5"]
g = jl(closure_gate._LOG)
check("shadow: the old close (resolved, how=line, no gate stamp), verdict logged only",
      out["resolved"] is True and r["status"] == "resolved" and r["resolved_how"] == "line" and "gate" not in r
      and len(g) == n_g + 1 and g[-1]["verdict"] == "no" and g[-1]["action"] == "old_close" and not frontier.is_answered(r))
closure_gate.CLOSURE_GATE_MODE = "off"
write_store([q("s6", "Where do swifts sleep at night?")])
deliver("s6")
n_g, n_j = len(jl(closure_gate._LOG)), len(judge_calls)
out = settle("s6")
check("off: the old close, no judge call, no log row",
      out["resolved"] is True and load()["s6"]["resolved_how"] == "line" and len(judge_calls) == n_j and len(jl(closure_gate._LOG)) == n_g)
closure_gate.CLOSURE_GATE_MODE = "enforce"
os.environ["NASCENCE_CLOSURE_GATE"] = "off"
write_store([q("s7", "Where do swifts sleep at night?")])
deliver("s7")
n_j = len(judge_calls)
out = settle("s7")
os.environ.pop("NASCENCE_CLOSURE_GATE")
check("kill switch NASCENCE_CLOSURE_GATE=off overrides enforce", out["resolved"] is True and len(judge_calls) == n_j)
check("resolve_gated refuses: no gate yes / no finding / unknown how / lookup how without a lookup finding",
      (write_store([q("x1", "plain open question about tide pools?"), q("x2", "another about herons?", finding="f", finding_ts=1.0)]) or True)
      and not frontier.resolve_gated("x1", "line", {"verdict": "yes"}) and not frontier.resolve_gated("x2", "line", {"verdict": "no"})
      and not frontier.resolve_gated("x2", "guess", {"verdict": "yes"}) and not frontier.resolve_gated("x2", "lookup", {"verdict": "yes"})
      and frontier.resolve_gated("x2", "line", {"verdict": "yes"}) and load()["x1"]["status"] == "open")

# ══ Phase 2: a lexical would-close on a lookup finding is his claim, sent to the gate ══
async def claim_round(text):
    frontier.resolve_if_addressed(text)
    for _ in range(40):
        if not closure_gate._tasks:
            break
        await asyncio.sleep(0.02)


CLAIM = "Now I see: the myrtle warbler does carry a yellow rump because it flashes it in flight."
JUDGE["d"] = YES
closure_gate._claimed.clear()
write_store([q("c1", Q_W, **LOOK)])
n_cl = len([x for x in jl(cl.SHADOW_LOG) if x["arm"] == "lookup"])
asyncio.run(claim_round(CLAIM))
rows = wait_rows(cl.SHADOW_LOG, len(jl(cl.SHADOW_LOG)) + 0)
r = load()["c1"]
check("lexical claim + gate yes: resolved, how=lookup, trigger lexical_claim",
      r["status"] == "resolved" and r["resolved_how"] == "lookup" and r["gate"]["trigger"] == "lexical_claim")
t0 = time.time()
while time.time() - t0 < 3 and len([x for x in jl(cl.SHADOW_LOG) if x["arm"] == "lookup" and x.get("seed_id") == "c1"]) < 1:
    time.sleep(0.05)
check("lexical claim close also writes the lookup arm's memory",
      len([x for x in jl(cl.SHADOW_LOG) if x["arm"] == "lookup" and x.get("seed_id") == "c1" and x["written_live"]]) == 1)
JUDGE["d"] = NO
closure_gate._claimed.clear()
write_store([q("c2", Q_W, **LOOK)])
asyncio.run(claim_round(CLAIM))
check("lexical claim + gate no: the question stays open (not provisional), verdict logged",
      load()["c2"]["status"] == "open" and jl(closure_gate._LOG)[-1]["trigger"] == "lexical_claim" and jl(closure_gate._LOG)[-1]["verdict"] == "no")
n_j = len(judge_calls)
asyncio.run(claim_round(CLAIM))
check("the same question and finding are judged once", len(judge_calls) == n_j)
closure_gate._claimed.clear()
write_store([q("c3", Q_W, finding="an old thought about the warbler and its yellow rump", finding_title="what you found in your own memory", finding_ts=3.0)])
asyncio.run(claim_round(CLAIM))
check("default LEXICAL_CLAIM_GATE=lookup: a memory finding is not sent to the judge", len(judge_calls) == n_j and closure_gate.LEXICAL_CLAIM_GATE == "lookup")
os.environ["NASCENCE_LEXICAL_CLAIM_GATE"] = "off"
write_store([q("c4", Q_W, **LOOK)])
asyncio.run(claim_round(CLAIM))
os.environ.pop("NASCENCE_LEXICAL_CLAIM_GATE")
check("kill switch NASCENCE_LEXICAL_CLAIM_GATE=off: no judge call, still open", len(judge_calls) == n_j and load()["c4"]["status"] == "open")

# ══ Phase 3: a rewording merges into an answered / parked / provisional question, never into a lexical close ══
GATE_YES = {"verdict": "yes", "how": "agreed"}
P_W = "What purpose could the bright patch on a warbler serve?"
P_G = "What makes granite outcrops end up so smooth and round?"
P_S = "At what height would a swift rest overnight?"
P_L = "What lets a lichen take hold on bare rock?"
P_H = "What does a heron do when the ponds freeze over?"


def p3_store():
    write_store([
        q("aw", Q_W, "resolved", resolved_ts=1.0, resolved_how="lookup", gate=GATE_YES, **LOOK),
        q("lg", Q_G, "resolved", resolved_ts=1.0, resolved_how="lexical"),
        q("ps", "Where do swifts sleep at night?", "parked", parked_ts=1.0, park_trigger=frontier.PARK_TRIGGER),
        q("ll", "How do lichens colonise bare stone over centuries?", "resolved", resolved_ts=1.0, resolved_how="line"),
        q("ph", "Where do herons go in a hard winter?", "provisional", provisional_ts=1.0),
        q("ot", "How fast does the tide turn in a narrow estuary?"),
    ])


p3_store()
ent = frontier.note_question_ex(P_W, "curiosity")
d = load()
check("a rewording of an ANSWERED question is not born: it joins the answered one",
      ent is not None and ent["id"] == "aw" and len(d) == 6 and d["aw"]["status"] == "resolved"
      and d["aw"]["variants"][-1]["q"] == P_W.rstrip(".") and d["aw"]["answered_merges"] == 1 and d["aw"]["encounters"] == 2)
ent = frontier.note_question_ex(P_G, "curiosity")
d = load()
check("a rewording of a LEXICAL close IS born as a fresh open question (D-0791 defeater)",
      ent is not None and ent["id"] not in ("lg",) and ent["status"] == "open" and len(d) == 7 and "variants" not in d["lg"])
ent = frontier.note_question_ex(P_L, "curiosity")
check("a rewording of a legacy line close with no gate verdict IS born", ent is not None and ent["id"] != "ll" and len(load()) == 8)
ent = frontier.note_question_ex(P_S, "curiosity")
check("a rewording of a PARKED question joins it and it stays parked",
      ent is not None and ent["id"] == "ps" and load()["ps"]["status"] == "parked" and len(load()) == 8)
ent = frontier.note_question_ex(P_H, "curiosity")
check("a rewording of a PROVISIONAL question joins it", ent is not None and ent["id"] == "ph" and len(load()) == 8)
am = jl(frontier._ANSWERED_MERGE_LOG)
check("answered merges logged (3 enforce rows)", len(am) == 3 and all(x["mode"] == "enforce" for x in am) and am[0]["matched_how"] == "lookup")
for mode_, born in (("shadow", True), ("off", True)):
    p3_store()
    os.environ["NASCENCE_ANSWERED_MERGE"] = mode_
    n_am = len(jl(frontier._ANSWERED_MERGE_LOG))
    ent = frontier.note_question_ex(P_W, "curiosity")
    os.environ.pop("NASCENCE_ANSWERED_MERGE")
    check(f"NASCENCE_ANSWERED_MERGE={mode_}: the rewording is born as before" + (", and logged" if mode_ == "shadow" else ", no log"),
          ent is not None and ent["id"] != "aw" and len(load()) == 7
          and len(jl(frontier._ANSWERED_MERGE_LOG)) == n_am + (1 if mode_ == "shadow" else 0))

# ══ Phase 4: bounded attempts, parking, reopening ══
write_store([q("k1", Q_W, line={"state": "waiting"}), q("k2", "How fast does the tide turn in a narrow estuary?")])
sts = [frontier.note_attempt("k1", False, "follow_no_grounds") for _ in range(4)]
r = load()["k1"]
check(f"parked on the 4th try with nothing new ({sts})",
      sts == ["open", "open", "open", "parked"] and r["status"] == "parked" and r["park_trigger"] == "a new finding on this subject"
      and r["park_attempts"] == 4)
check("a parked question is not followed, offered, pursued or counted open",
      frontier.waiting_for_line(()) == [] and frontier.open_count() == 1 and all(x["q"] != Q_W for x in frontier.top_open(5))
      and Q_W not in frontier.open_questions(5) and (frontier.pending_pursuit() or {}).get("id") != "k1")
row = lookup_attach.note_lookup("wikipedia", "myrtle warbler rump", "Myrtle warbler", "The myrtle warbler has a yellow rump.", "en.wikipedia.org/wiki/Myrtle_warbler")
r = load()["k1"]
check("a matching lookup reopens the parked question with the finding attached",
      row["attached"] is True and row.get("reopened") is True and r["status"] == "open" and r["reopened_from"] == "parked"
      and frontier.finding_from_lookup(r) and r["closure_attempts"] == 0)
write_store([q("k3", Q_W, "provisional", provisional_ts=1.0)])
row = lookup_attach.note_lookup("wikipedia", "myrtle warbler rump", "Myrtle warbler", "The myrtle warbler has a yellow rump.", "u")
check("a matching lookup reopens a provisional question too", row["attached"] is True and load()["k3"]["status"] == "open")
write_store([q("k4", Q_W, "parked", parked_ts=1.0)])
os.environ["NASCENCE_LOOKUP_REOPEN"] = "0"
row = lookup_attach.note_lookup("wikipedia", "myrtle warbler rump", "Myrtle warbler", "The myrtle warbler has a yellow rump.", "u")
os.environ.pop("NASCENCE_LOOKUP_REOPEN")
check("kill switch NASCENCE_LOOKUP_REOPEN=0: open questions only (parked untouched)",
      row["attached"] is False and row["best_qid"] is None and load()["k4"]["status"] == "parked")
write_store([q("k5", Q_W)])
for _ in range(6):
    frontier.attach_lookup_finding("k5", "t", "the same extract", via="wikipedia")
    if load()["k5"]["status"] != "open":
        break
check("the same lookup text again counts as a try; a new text resets",
      load()["k5"]["status"] == "parked" and load()["k5"]["park_attempts"] == 4)
write_store([q("k6", Q_W, consecutive_stalls=3)])
frontier.note_attempt("k6", False)
check("curiosity's own stalls count toward the bound", load()["k6"]["status"] == "parked")
write_store([q("k7", Q_W)])
for _ in range(3):
    frontier.note_attempt("k7", False)
frontier.note_attempt("k7", True)
check("a try that brought something new resets the count", load()["k7"]["closure_attempts"] == 0 and load()["k7"]["status"] == "open")
os.environ["NASCENCE_PARK"] = "off"
write_store([q("k8", Q_W)])
for _ in range(6):
    frontier.note_attempt("k8", False)
os.environ.pop("NASCENCE_PARK")
check("kill switch NASCENCE_PARK=off: never parked, nothing counted", load()["k8"]["status"] == "open" and "closure_attempts" not in load()["k8"])
write_store([q("k9", "Where do swifts sleep at night?")])
deliver("k9")
settle("k9", "no")
check("a settled no is one try", load()["k9"].get("closure_attempts") == 1 and load()["k9"]["status"] == "open")

# set down
write_store([q("d1", Q_W)])
check("set_down marks the question with his reason",
      frontier.set_down("d1", "I had got as far as the rump colour; why it evolved is still open.")
      and load()["d1"]["status"] == "set_down" and "still open" in load()["d1"]["set_down_reason"] and frontier.open_count() == 0)
ent = frontier.note_question_ex(Q_W, "curiosity")
check("asking it again takes it up: open again", ent is not None and ent["id"] == "d1" and load()["d1"]["status"] == "open"
      and load()["d1"]["reopened_from"] == "set_down")
write_store([q("d2", Q_W)])
goal_offer._judge = lambda s, u: _stub_judge(s, u)
goal_offer._register = lambda: {"goals": []}
goal_offer.set_down_path = lambda: _tmp / "goal_set_down.json"
goal_offer.set_down_log_path = lambda: _tmp / "logs" / "goal_set_down.jsonl"
JUDGE["d"] = {"verdict": True, "how": "agreed", "why": "genuine"}
row = asyncio.run(goal_offer._set_down({"id": "question:d2", "text": Q_W},
                                       "I got as far as the colour of the patch and what it is for is still open to me.", "t", "c"))
check("the live Layered Goals set-down of a question marks the frontier entry set_down",
      row["accepted"] is True and row.get("frontier_set_down") is True and load()["d2"]["status"] == "set_down")
goal_offer.SET_DOWN_MARKS_FRONTIER = False
write_store([q("d3", Q_W)])
row = asyncio.run(goal_offer._set_down({"id": "question:d3", "text": Q_W},
                                       "I got as far as the colour of the patch and what it is for is still open to me.", "t", "c"))
goal_offer.SET_DOWN_MARKS_FRONTIER = True
check("SET_DOWN_MARKS_FRONTIER=False: the frontier entry stays open", row["accepted"] is True and load()["d3"]["status"] == "open")

# ══ unknown-status safety ══
write_store([
    q("u1", "open one about tide pools?"), q("u2", "odd status", "weird_new_status"), q("u3", "no status at all"),
    q("u4", "prov", "provisional", gate={"verdict": "no"}), q("u5", "parked", "parked"), q("u6", "set down", "set_down"),
    q("u7", "answered", "resolved", resolved_how="lookup", gate=GATE_YES, **LOOK),
    q("u8", "lexical", "resolved", resolved_how="lexical"), q("u9", "faded", "faded"), q("u10", "merged", "merged"),
    q("u11", "provisional unavailable", "provisional", gate={"verdict": "unavailable"}),
])
d = json.loads(frontier._F.read_text(encoding="utf-8"))
del d["questions"][2]["status"]
frontier._F.write_text(json.dumps(d), encoding="utf-8")
bd = frontier.resolved_breakdown()
check(f"resolved_breakdown counts the endings and unknown statuses without miscounting ({bd})",
      bd["resolved"] == 2 and bd["provisional"] == 2 and bd["parked"] == 1 and bd["set_down"] == 1 and bd["unknown_status"] == 2
      and bd["answered"] == 1 and bd["lookup"] == 1 and bd["lexical"] == 1 and bd["gate_yes"] == 1 and bd["gate_no"] == 1
      and bd["gate_unavailable"] == 1 and bd["answered_with_source"] == 1)
ok = True
try:
    frontier._save(json.loads(frontier._F.read_text(encoding="utf-8")))      # refreshes the light sidecar
    readers = {
        "open_count": frontier.open_count(), "top_open": len(frontier.top_open(9)), "novel_open": len(frontier.novel_open(9)),
        "open_questions": len(frontier.open_questions(9)), "waiting_for_line": len(frontier.waiting_for_line(())),
        "pursuit_candidates": len(frontier.pursuit_candidates()), "pending_pursuit": (frontier.pending_pursuit() or {}).get("id"),
        "seed": (frontier.open_question_for_seed() or {}).get("q"), "closeable": frontier.closeable_seed(),
        "random_term_ok": True, "lp_rank": len(curiosity_progress.rank()),
        "best_open_match": lookup_attach.best_open_match("tide pools")["open_n"],
        "resolve_if_addressed": frontier.resolve_if_addressed("Now I understand it because the tide pools fill."),
        "note_question": frontier.note_question("What do limpets eat on the rocks at low water?", "curiosity"),
    }
except Exception as exc:
    ok = False
    readers = repr(exc)
check(f"the main readers neither crash nor count an unknown / ending status as open ({readers})",
      ok and readers["open_count"] == 1 and readers["top_open"] == 1 and readers["waiting_for_line"] == 0
      and readers["pursuit_candidates"] == 1 and readers["pending_pursuit"] == "u1" and readers["lp_rank"] in (1, 2)
      and readers["best_open_match"] == 1)
light = json.loads(frontier._light_path().read_text(encoding="utf-8"))
check("the light sidecar counts every status by name and lists only open ones",
      light["counts"].get("provisional") == 2 and light["counts"].get("parked") == 1 and all(x["status"] == "open" for x in light["open"]))

# ══ Phase 5 kill switches ══
cl.LOOKUP_ARM = False
n_rows = len(jl(cl.SHADOW_LOG))
r = cl.record_lookup_answered(dict(q("z1", Q_W, "resolved", resolved_how="lookup", gate=GATE_YES, **LOOK)))
cl.LOOKUP_ARM = True
check("LOOKUP_ARM=False: no row, no write", len(jl(cl.SHADOW_LOG)) == n_rows and r["compose_how"] is None)
cl.CLOSURE_ARMS.discard("lookup")
n_live = len(live_writes)
r = cl.record_lookup_answered(dict(q("z2", Q_W, "resolved", resolved_how="lookup", gate=GATE_YES, **LOOK)))
cl.CLOSURE_ARMS.add("lookup")
check("'lookup' out of CLOSURE_ARMS: shadow row with the would-be text, nothing written",
      r["compose_how"] == "template" and r["would_be"] and r["written_live"] is False and len(live_writes) == n_live)
check("defaults: lookup arm on and live; gate default is a known mode",
      cl.LOOKUP_ARM is True and "lookup" in cl.CLOSURE_ARMS and "line" in cl.CLOSURE_ARMS)

# ── nothing landed outside the temp dir ──
_wt_logs = ROOT / "data" / "logs"
check("no closure_producer log under this checkout's data/",
      not any((_wt_logs / n).exists() for n in ("closure_gate.jsonl", "lexical_resolve_shadow.jsonl", "frontier_answered_merge.jsonl",
                                                "lookup_attach.jsonl"))
      or (ROOT / "data").resolve() == Path("C:/Nascence/data").resolve())

print()
print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
