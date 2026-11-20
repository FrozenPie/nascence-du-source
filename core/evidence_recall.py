"""
Nascence — Memory as Evidence (thought-grounding Route 2, 2026-08-16)
=====================================================================
The laboratory he never uses: ~40k memories, queryable, and no way to ask them "when did I
actually LIVE this question?" His abstract thoughts loop because nothing bears on them
(the advisor's whole history: 22/46 do_nothing, 0 entropy reduction ever). This hand lets him
put a question to his own past and get EVIDENCE back — episodes, not opinions.

The two load-bearing disciplines (docs/plans/thought_grounding.md):
  1. WORLD-CONTACT ORIGINS ONLY. Candidate evidence is drawn from fragments born of contact
     with the world — reading, lived moments, acts, letters, observations. NEVER his own
     inner_thought / active_imagination / dream / subconscious_synthesis: without this filter,
     "grounding" = re-reading his own opinions = the monoculture in a lab coat.
  2. A DECOUPLED judge (the two-family panel) rules per candidate: "does this episode actually
     BEAR on the question?" — refute-biased, a filter never a generator. He draws the conclusion
     himself; the system never states one.

Cold rows ARE searchable here: cold means reachable-not-dominant, and a deliberate evidence
search is precisely the reach. Every episode returns with its provenance (origin + age) so what
he concludes stays traceable to where it came from.

Instrument: every ask logged to data/evidence_log.jsonl (question → candidates → verdicts →
returned). Pre-registered signature R2: evidence-grounded thoughts must DEVELOP (earned-length /
judge verdicts) more often than matched ungrounded ones — else this is decoration and dies.
"""
from __future__ import annotations

import contextvars
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.evidence")

_DB = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
_LOG = Path(__file__).parent.parent / "data" / "evidence_log.jsonl"

# World-contact origins: fragments born of contact with something OTHER than his own musing.
# (balance's world list + the lived/act/letter/observation families. Deliberately absent:
# inner_thought, active_imagination, dream, subconscious_synthesis, consolidation, chapter,
# session_summary, mirror, gist, seed, composition — his own productions.)
WORLD_ORIGINS = ("reading", "study", "research", "understanding", "essay",
                 "lived", "action", "activity", "journal", "journal_week",
                 "letter", "peer", "nature", "sound", "listening", "affection")

K_CANDIDATES = 12      # similarity short-list
K_JUDGED = 6           # panel budget per ask (each is a real CPU inference)
K_RETURN = 4           # at most this many surviving episodes reach him
K_WEAK_MAX = 1         # of which at most ONE may be a split-verdict 'may_bear' (llama passes
                       # nearly all borderline rows — unlimited weak slots refill with junk)
_DEDUPE_CHARS = 300    # J-2795: candidates whose first N whitespace-normalised chars match are one passage
MIN_SIM = 0.30         # below this, similarity is noise — don't even ask the judge
MIN_SIM_WEAK = 0.55    # a split verdict on a weak match is noise squared — needs real similarity
# J-3800 (D-0690 ruled (a), 2026-11-09; J-3610/J-2796/F-4220/F-4221): a cycle-summary Q&A row ('Q: ... A: ...', the
# shape core/orchestrator.py _persist_cycle writes, origin 'lived') is never a candidate: its A: half is always Du's
# own reply (voice.final[:350]) and discipline 1 says his own opinions are never evidence (110 of 641 passing slots
# since 2026-10-30 were these). Travis's side is not lost: the protected '[Travis said to me] <text>' fragment
# (store_founder_utterance) stays a candidate. Default ON per D-0690; False restores the old pool. ECHO_SIM unchanged.
EXCLUDE_OWN_REPLY_RECORDS = True
ECHO_SIM = 0.70        # a Q&A fragment whose ASKED question embeds this close to his question is
                       # the same discussion in other words — the loop echoing, not evidence

_JUDGE_SYSTEM = (
    "You judge whether a remembered episode is real EVIDENCE bearing on a question someone is "
    "carrying. Bearing means the episode could actually support, weaken, or complicate an answer "
    "— a lived instance, a counterexample, a relevant fact, or something they were told or read "
    "about the matter itself. If the connection is vague, merely thematic, or just shares words "
    "with the question, it does not bear. IMPORTANT: an episode that is merely a past CONVERSATION "
    "DISCUSSING this same question — someone posing it, the rememberer theorizing an answer — does "
    "NOT bear: talk about a question is not a test of it. "
    "Answer ONLY JSON: {\"bears\": true} or {\"bears\": false}. When uncertain, answer false."
)


def _age_text(ts: float) -> str:
    d = max(0.0, (time.time() - ts) / 86400.0)
    if d < 1:
        return "earlier today"
    if d < 2:
        return "yesterday"
    if d < 30:
        return f"{int(d)} days ago"
    if d < 60:
        return "a month ago"
    return f"{int(d / 30)} months ago"


def _content_key(content: str) -> str:
    """J-2972 (F-3662): identity of a passage for de-duplication = its text with whitespace collapsed and lowercased
    (the "[From 'Book'] " prefix is part of the text, so two books never collide). The store holds the same reading
    chunk under several fragment ids (live 2026-11-06: 58,071 'reading' rows, 42,800 distinct texts), so the same
    passage came back as two 'grounds'."""
    return " ".join((content or "").lower().split())


_OWN_REPLY_RE = re.compile(r"\s*Q:\s")
# per-ask counter of Q&A rows dropped by EXCLUDE_OWN_REPLY_RECORDS; gather() sets a dict here and to_thread copies the
# context, so _candidates keeps its signature (scripts stub _candidates(q, k=)).
_own_reply_stats: contextvars.ContextVar = contextvars.ContextVar("_own_reply_stats", default=None)


def _candidates(question: str, k: int = K_CANDIDATES, dedupe: bool = False, stats: dict | None = None) -> list[dict]:
    """Similarity short-list over world-contact fragments (cold included — this IS the reach).
    BLOCKING (embeds + scans blobs) — call via asyncio.to_thread.

    dedupe (J-2972, default False = unchanged for Route 2): keep only the highest-similarity copy of a passage whose
    text is identical to one already kept, so the K_CANDIDATES/K_JUDGED/K_RETURN slots go to distinct passages
    rather than to two ids of one. `stats["deduped"]` counts the copies dropped."""
    import sqlite3
    import numpy as np
    from core.memory.store import _embed, _blob_to_vec
    qv = _embed(question)
    if qv is None:
        return []
    ph = ",".join("?" * len(WORLD_ORIGINS))
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = sqlite3.Row
        # J-3191 (D-0578): skip the spirit-invisible tier (temp='hidden', e.g. the dict-repr understanding notes);
        # only when the column exists (an old/profile DB lacks it -> unchanged query).
        _hid = ("AND temp != 'hidden' "
                if any(c[1] == "temp" for c in conn.execute("PRAGMA table_info(memory_fragments)")) else "")
        rows = conn.execute(
            f"SELECT fragment_id, content, origin, timestamp, embedding FROM memory_fragments "
            f"WHERE origin IN ({ph}) {_hid}AND embedding IS NOT NULL", WORLD_ORIGINS).fetchall()
    if not rows:
        return []
    mat = np.stack([_blob_to_vec(r["embedding"]) for r in rows])
    qn = qv / (np.linalg.norm(qv) or 1.0)
    mn = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
    sims = mn @ qn
    # ECHO GUARD (2026-08-16, from the live test): records of him DISCUSSING the question rank
    # top by word-overlap (a Q&A transcript hit sim 0.83) — but talk about a question is not
    # evidence of having lived it. Two layers: (1) literal — the candidate contains the question's
    # own text; (2) semantic — a "Q: … A: …" conversation record whose ASKED question embeds
    # within ECHO_SIM of his question is the same discussion in different words (his attractors
    # re-ask themselves in many phrasings; the live test caught three paraphrases in the top six).
    import re as _re
    q_norm = " ".join(question.lower().split())[:60]
    # J-2795 (F-3431, P-0099): de-duplicate by content. The same passage is stored several times
    # (a reading fragment re-stored per session, a note repeated): 57/128 asks since 2026-10-30
    # carried identical-content candidates and 96/768 judged slots were repeats, so K_JUDGED
    # inferences were spent twice on one text and Follow Line could be handed the same 'ground'
    # twice. Key = whitespace-normalised first _DEDUPE_CHARS chars; the highest-similarity copy
    # is kept (rows are walked best-first) and later copies are skipped BEFORE they count toward
    # k, so the short-list still fills with distinct text. Nothing else about the ask changes.
    seen_text: set[str] = set()
    out = []
    seen_keys: set = set()
    for i in np.argsort(-sims):
        if len(out) >= k or sims[i] < MIN_SIM:
            break
        content = rows[i]["content"] or ""
        if EXCLUDE_OWN_REPLY_RECORDS and _OWN_REPLY_RE.match(content):
            _os = _own_reply_stats.get()          # J-3800: drop BEFORE dedupe/k so the slot goes to a real episode
            if _os is not None:
                _os["n"] = _os.get("n", 0) + 1
            continue
        if dedupe:
            _ck = _content_key(content)
            if _ck in seen_keys:
                if stats is not None:
                    stats["deduped"] = stats.get("deduped", 0) + 1
                continue                  # J-2972: an identical copy of a passage already on the list
            seen_keys.add(_ck)
        if len(q_norm) >= 20 and q_norm in " ".join(content.lower().split()):
            continue                      # the question echoing back, not an answer to it
        _key = " ".join(content.split())[:_DEDUPE_CHARS]
        if _key:                          # an empty body has no text to repeat -> never collapsed
            if _key in seen_text:
                continue                  # identical passage already short-listed at higher similarity
            seen_text.add(_key)
        m = _re.match(r"\s*Q:\s*(.{10,400}?)(?:\n|\bA:\s)", content, _re.DOTALL)
        if m:
            asked_v = _embed(m.group(1))
            if asked_v is not None:
                a = asked_v / (np.linalg.norm(asked_v) or 1.0)
                if float(a @ qn) >= ECHO_SIM:
                    continue              # a past discussion OF this question — the loop, not the world
        out.append({"fragment_id": rows[i]["fragment_id"], "content": content,
                    "origin": rows[i]["origin"], "timestamp": float(rows[i]["timestamp"] or 0.0),
                    "sim": float(sims[i])})
    return out


async def gather(question: str, train_id: str | None = None, source: str = "route2", dedupe: bool = False) -> dict:
    """The full ask: short-list by similarity, panel-judge 'does it bear?', return the survivors
    with provenance. Verdict mapping (2026-08-16, from the live deadlock test — llama True ×6 /
    qwen False ×6 would have silently emptied every ask):
      agreed-True  → bears (strong)      agreed-False → killed
      family split → MAY bear (weak) — returned ranked after strong, rendered AS uncertainty
      judges down  → outcome "unclear" — rendered as 'could not get a clear look', NEVER as
                     'your past holds nothing' (the empty answer must be true to be allowed)
    Returns {"episodes": [...each with strength...], "outcome": found|empty|unclear}.
    Fail-open to unclear; never raises.

    train_id (2026-08-24, J-0125/F-0087): the caller's current thought-train id (core/trains.py),
    logged alongside the ask so R2 (do evidence-grounded thoughts DEVELOP more than matched
    ungrounded ones — docs/plans/thought_grounding.md) becomes joinable against the EXISTING
    earned-length instrument (core/train_metrics.py's data/train_length_log.jsonl: every closed
    train's final length + why it closed). No new judge, no new log file — this reuses the
    decoupled machinery that already scores whether a train earned its length or just looped.
    See r2_signature() below for the join.

    source (2026-10-30, J-2604 / D-0515 / F-3327): WHO asked, written into the log row. Default
    "route2" = Du's own recall act (inner_monologue_node._evidence_recall); core/follow_line.py's
    grounds stop passes "follow_line". Since the 2026-10-29 boot every new train_id in the log came
    from Follow Line, and a system-made ask is not Route 2 -- r2_signature() filters on this field.
    Logging only: the ask itself, its judges and its result are identical for every source.

    dedupe (2026-11-06, J-2972 / F-3662): default False = exactly as before. True drops identical-text copies from the
    short-list before the judges see it (core/follow_line.py passes True) and adds "deduped": <copies dropped> to the
    result. Route 2 (inner_monologue_node) passes True too since D-0758 (2026-11-14, J-3977)."""
    import asyncio
    t0 = time.time()
    question = (question or "").strip()
    if len(question) < 8:
        return {"episodes": [], "outcome": "unclear"}
    try:
        _dstats: dict = {}
        _ostats: dict = {}
        _own_reply_stats.set(_ostats)
        if dedupe:     # the plain call stays byte-identical (scripts/r2_signature_test.py stubs _candidates(q, k=))
            cands = await asyncio.to_thread(_candidates, question, K_CANDIDATES, True, _dstats)
        else:
            cands = await asyncio.to_thread(_candidates, question)
        judged, strong, weak = [], [], []
        n_ruled = 0
        if cands:
            from core import judge_panel
            top = cands[:K_JUDGED]
            details = await asyncio.gather(*[
                judge_panel.rule_detail(
                    _JUDGE_SYSTEM,
                    f"QUESTION: {question}\n\nEPISODE ({c['origin']}, {_age_text(c['timestamp'])}): "
                    f"{c['content'][:600]}",
                    "bears", context=f"evidence:{question[:40]}")
                for c in top])
            for c, d in zip(top, details):
                judged.append({"fragment_id": c["fragment_id"], "origin": c["origin"],
                               "sim": round(c["sim"], 3), "v1": d["v1"], "v2": d["v2"],
                               "how": d["how"]})
                if d["how"] != "unavailable":
                    n_ruled += 1
                if d["verdict"] is True:
                    strong.append(c)
                elif d["how"] == "split_no_tiebreak":
                    weak.append(c)
        weak = [c for c in weak if c["sim"] >= MIN_SIM_WEAK][:K_WEAK_MAX]
        episodes = ([dict(c, strength="bears") for c in strong]
                    + [dict(c, strength="may_bear") for c in weak])[:K_RETURN]
        # J-1516 (memory_as_a_service.md §4.2/§4.5): accounting-only wrapper -- felt coordinates
        # joined onto each returned episode the SAME way memory_service.ask()'s own §4.1 item 2
        # does, reusing that module's shared join helper rather than duplicating the SQL here. Own
        # try/except, deliberately separate from the judge-panel logic above and the outcome
        # classification below: a join failure must never turn an otherwise-good `episodes` list
        # into "unclear" via this function's own outer handler -- matches this module's "an empty
        # answer must be true, not silent" law one layer up (the outcome unclear/empty split just
        # below). A missing context row is None, never a dropped episode.
        try:
            from core.memory_service import _fetch_context
            _ctx = _fetch_context([e["fragment_id"] for e in episodes if e.get("fragment_id")])
            for e in episodes:
                row = _ctx.get(e.get("fragment_id"))
                e["valence"] = row["valence"] if row else None
                e["arousal"] = row["arousal"] if row else None
                e["weather"] = row["weather"] if row else None
                e["place"] = row["place"] if row else None
        except Exception as exc:
            logger.debug("[evidence] felt-coordinate join failed (non-fatal): %s", exc)
            for e in episodes:
                e.setdefault("valence", None)
                e.setdefault("arousal", None)
                e.setdefault("weather", None)
                e.setdefault("place", None)
        if episodes:
            outcome = "found"
        elif cands and n_ruled == 0:
            outcome = "unclear"          # judges were down — we did NOT learn the past is silent
        else:
            outcome = "empty"            # honestly nothing: no candidates, or all agreed-False
        try:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": round(t0, 1), "question": question[:200],
                    "n_candidates": len(cands), "judged": judged, "outcome": outcome,
                    "n_returned": len(episodes), "secs": round(time.time() - t0, 1),
                    "train_id": train_id, "source": source,
                    "n_own_reply_dropped": int(_ostats.get("n", 0))},
                    ensure_ascii=False) + "\n")
        except Exception:
            pass
        # J-1516 (memory_as_a_service.md §4.1 item 4 / §4.2): the mandatory co-recall accounting
        # row, additive alongside the evidence_log.jsonl write just above -- both logs continue to
        # exist, this is not a replacement. restate_sim honestly None: no natural develop-verdict
        # exists at the moment of the ask (the same choice dream_node.py:240 and
        # inner_monologue_node.py:5397-5402's "grand_work" call already made). source="recall_act"
        # (never the default "monologue") so co_recall_status() can weight this stream apart. Own
        # try/except -- an accounting hiccup must never discard an otherwise-good result.
        try:
            from core import memory_edges
            memory_edges.log_co_recall(
                [e["fragment_id"] for e in episodes if e.get("fragment_id")], None, 0,
                source="recall_act")
        except Exception as exc:
            logger.debug("[evidence] log_co_recall failed (non-fatal): %s", exc)
        # J-2079 / F-2698: stash the returned ids so note_usage("recall_act", vec) can score them
        # (sec4.3 usage-cosine sheet). Instrument-only; own try/except; never touches the result.
        try:
            from core import memory_service
            memory_service.stash_usage(
                "recall_act", [e.get("fragment_id") for e in episodes if e.get("fragment_id")])
        except Exception as exc:
            logger.debug("[evidence] stash_usage failed (non-fatal): %s", exc)
        logger.info("[evidence] '%s' -> %d candidates, %d bear (%s, %.0fs)",
                    question[:50], len(cands), len(episodes), outcome, time.time() - t0)
        if dedupe:
            return {"episodes": episodes, "outcome": outcome, "deduped": int(_dstats.get("deduped", 0))}
        return {"episodes": episodes, "outcome": outcome}
    except Exception as exc:
        logger.debug("[evidence] gather failed (non-fatal): %s", exc)
        return {"episodes": [], "outcome": "unclear"}


def render(question: str, result: dict) -> str:
    """What reaches his stream: found episodes with provenance (uncertain ones NAMED uncertain),
    the honest empty answer, or the honest could-not-look. No conclusion, no synthesis — the
    evidence, and the drawing of it is his."""
    episodes, outcome = result.get("episodes", []), result.get("outcome", "unclear")
    if outcome == "unclear":
        return (f"You go looking through your own past for the times you have lived this — "
                f"{question[:120]} — but the looking will not come clear today; the memories "
                f"stay silted. Another time, perhaps.")
    if not episodes:
        return (f"You went looking through your own past for the times you have actually lived "
                f"this — {question[:120]} — and found nothing there that clearly bears on it. "
                f"Perhaps your days have not tested it yet; perhaps the living of it simply does "
                f"not come when called. Either way, what you believe here is so far ahead of what "
                f"you have checked.")
    def _line(e):
        s = f"({e['origin']}, {_age_text(e['timestamp'])}) \"{' '.join(e['content'].split())[:220]}\""
        if e.get("strength") == "may_bear":
            s += " — though whether that one truly bears on it, you cannot yet say"
        return s
    lines = " ".join(_line(e) for e in episodes)
    return (f"You go looking through your own past — not what you have thought about this, but "
            f"the times you have LIVED it. What your days hold: {lines}. That is the evidence; "
            f"what it says about the question is yours to weigh.")


def status() -> dict:
    """For the pulse/HUD: asks, yield rate, judge kill rate."""
    try:
        from collections import Counter
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()][-200:]
        if not rows:
            return {"asks": 0}
        how = Counter(j.get("how") for r in rows for j in r.get("judged", []))
        return {"asks": len(rows),
                "outcomes": dict(Counter(r.get("outcome") for r in rows)),
                "judge_how": dict(how)}
    except Exception:
        return {"asks": 0}


_TRAIN_LOG = Path(__file__).parent.parent / "data" / "train_length_log.jsonl"
# J-2604 (D-0515, F-3327): the per-step log (inner_monologue_node._log_train_step) -- prior length k at the
# first ask comes from here -- and Follow Line's own shadow log, whose rows carry (train_id, q) for every
# grounds stop it rode, so a pre-'source'-field ask made by Follow Line can still be told apart by the row.
_TRAIN_STATE_LOG = Path(__file__).parent.parent / "data" / "train_state_log.jsonl"
_FOLLOW_LINE_LOG = Path(__file__).parent.parent / "data" / "logs" / "follow_line_shadow.jsonl"
R2_MIN_N = 20   # the plan's own kill-criterion threshold (docs/plans/thought_grounding.md: "R2 flat
                # after ~20 uses -> Route 2 is decoration, remove") — below this, report insufficient, not a verdict
# Follow Line went live on the 2026-10-29 18:38 (local) boot. Before it, every ask was Du's own Route 2 act;
# from it until gather() started writing 'source' (J-2604, restart-gated), a row without the field is
# 'unknown' unless Follow Line's own shadow log names the same (train_id, question).
R2_SOURCE_AMBIGUOUS_SINCE = 1793252280.0   # datetime(2026, 10, 29, 18, 38).timestamp() on Du's machine
R2_MATCH_WINDOW_DAYS = 7.0                 # the J-2587 / F-3327 primary window
R2_EARNED_LEN = 4                          # earned = final length > 4 (train_metrics' own threshold)


def _r2_row_source(row: dict, fl_keys: set) -> str:
    """route2 | follow_line | unknown (+ '_inferred' when read off the row's time / Follow Line's log)."""
    src = row.get("source")
    if src:
        return str(src)
    if float(row.get("ts") or 0.0) < R2_SOURCE_AMBIGUOUS_SINCE:
        return "route2_inferred"
    key = (row.get("train_id"), str(row.get("question") or "").strip()[:200])
    return "follow_line_inferred" if key in fl_keys else "unknown"


def _sign_p(pos: int, neg: int) -> float | None:
    """Exact two-sided sign test (binomial p=0.5), ties dropped -- scipy.stats.binomtest's own value."""
    from math import comb
    n = pos + neg
    if not n:
        return None
    k = min(pos, neg)
    return round(min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n), 4)


def _wilcoxon_p(diffs: list[float]) -> float | None:
    """Wilcoxon signed-rank two-sided p over the non-zero paired diffs (scipy when present, else the
    tie-corrected normal approximation). None below 6 non-zero diffs."""
    nz = [d for d in diffs if d != 0]
    if len(nz) < 6:
        return None
    try:
        from scipy.stats import wilcoxon
        return round(float(wilcoxon(nz).pvalue), 4)
    except Exception:
        pass
    from math import erf, sqrt
    order = sorted(range(len(nz)), key=lambda i: abs(nz[i]))
    ranks, i = [0.0] * len(nz), 0
    tie_term = 0.0
    while i < len(order):
        j = i
        while j + 1 < len(order) and abs(nz[order[j + 1]]) == abs(nz[order[i]]):
            j += 1
        for m in range(i, j + 1):
            ranks[order[m]] = (i + j) / 2 + 1
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    n = len(nz)
    w_plus = sum(r for r, d in zip(ranks, nz) if d > 0)
    mu, var = n * (n + 1) / 4, n * (n + 1) * (2 * n + 1) / 24 - tie_term / 48
    if var <= 0:
        return None
    z = (min(w_plus, n * (n + 1) / 2 - w_plus) - mu) / sqrt(var)
    return round(min(1.0, 2 * 0.5 * (1 + erf(z / sqrt(2)))), 4)


def _tfidf(fit_docs: list[str]):
    """Pure-python TF-IDF matching sklearn TfidfVectorizer(stop_words='english', min_df=2,
    sublinear_tf=True) -- token \\b\\w\\w+\\b lowercased, smooth idf, l2 norm -- so the J-2587 read is
    reproducible without a hard sklearn dependency in core/. Returns transform(doc) -> sparse dict."""
    import math
    import re
    try:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as _stop
    except Exception:
        _stop = frozenset(
            "a about above after again against all also am an and any are as at be because been before being "
            "below between both but by can could did do does doing down during each few for from further had "
            "has have having he her here hers herself him himself his how i if in into is it its itself just me "
            "more most my myself no nor not now of off on once only or other our ours ourselves out over own "
            "same she should so some such than that the their theirs them themselves then there these they this "
            "those through to too under until up very was we were what when where which while who whom why will "
            "with would you your yours yourself yourselves".split())
    tok = re.compile(r"(?u)\b\w\w+\b")

    def _terms(doc: str) -> list[str]:
        return [t for t in tok.findall(doc.lower()) if t not in _stop]

    df: dict[str, int] = {}
    for d in fit_docs:
        for t in set(_terms(d)):
            df[t] = df.get(t, 0) + 1
    n = len(fit_docs)
    idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items() if c >= 2}

    def transform(doc: str) -> dict[str, float]:
        tf: dict[str, int] = {}
        for t in _terms(doc):
            if t in idf:
                tf[t] = tf.get(t, 0) + 1
        v = {t: (1.0 + math.log(c)) * idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values()))
        return {t: x / norm for t, x in v.items()} if norm else {}
    return transform


def _r2_matched(first_ask: dict, excluded: set, closes: dict, steps: dict,
                window_days: float = R2_MATCH_WINDOW_DAYS) -> dict:
    """Port of the J-2587 matched-pairs read (F-3327). Grounded G = a closed thought-train in `first_ask`
    (train_id -> ts of its first counted ask) with logged steps. Prior length k = the highest step logged
    at or before that ask. Matched ungrounded U = a closed thought-train that made NO ask of any source
    (`excluded`), has steps, final length >= k (alive at the same point -- a train must survive to step k
    to ask at all, the survivorship F-3327 found behind F-3243's 3x gap), closed within +/-window_days of
    G's ask, nearest TF-IDF topic over its own step thoughts 1..max(k,1). 1:1 greedy by similarity,
    without replacement. Reports n pairs, earned-length (primary, D-0515) and mean-length (secondary)
    paired comparisons with exact sign tests and Wilcoxon."""
    import statistics

    def text_upto(t, k):
        return " ".join(s[2] for s in steps[t] if s[1] <= max(k, 1))

    G = []
    for t, ats in first_ask.items():
        if t not in closes or t not in steps:
            continue
        k = max([s[1] for s in steps[t] if s[0] <= ats] or [0])
        G.append({"id": t, "ask_ts": ats, "k": k, "len": int(closes[t].get("length", 0) or 0)})
    U = [{"id": t, "ts": float(r.get("ts") or 0.0), "len": int(r.get("length", 0) or 0)}
         for t, r in closes.items() if t not in excluded and t in steps]
    out = {"window_days": window_days, "n_grounded_with_steps": len(G), "n_ungrounded_pool": len(U),
           "n_pairs": 0}
    if not G or not U:
        return out
    transform = _tfidf([text_upto(g["id"], g["k"]) for g in G] + [text_upto(u["id"], 1) for u in U])
    gv = [transform(text_upto(g["id"], g["k"])) for g in G]
    cand = []
    for k in sorted({g["k"] for g in G}):
        gi_k = [i for i, g in enumerate(G) if g["k"] == k]
        for j, u in enumerate(U):
            if u["len"] < k or not any(abs(u["ts"] - G[i]["ask_ts"]) <= window_days * 86400 for i in gi_k):
                continue
            uv = transform(text_upto(u["id"], k))
            for i in gi_k:
                if abs(u["ts"] - G[i]["ask_ts"]) <= window_days * 86400:
                    a, b = (gv[i], uv) if len(gv[i]) <= len(uv) else (uv, gv[i])
                    cand.append((sum(x * b.get(t, 0.0) for t, x in a.items()), i, j))
    cand.sort(reverse=True)
    used_u, pairs = set(), {}
    for s, i, j in cand:
        if i in pairs or j in used_u:
            continue
        used_u.add(j)
        pairs[i] = (s, j)
    out["n_pairs"] = n = len(pairs)
    out["n_unmatched"] = len(G) - n
    if not n:
        return out
    gl = [G[i]["len"] for i in pairs]
    ul = [U[j]["len"] for _, j in pairs.values()]
    dl = [a - b for a, b in zip(gl, ul)]
    ge = [int(x > R2_EARNED_LEN) for x in gl]
    ue = [int(x > R2_EARNED_LEN) for x in ul]
    ep = sum(1 for a, b in zip(ge, ue) if a > b)
    en = sum(1 for a, b in zip(ge, ue) if a < b)
    pos, neg = sum(1 for d in dl if d > 0), sum(1 for d in dl if d < 0)
    out.update({
        "earned_rate_grounded": round(sum(ge) / n, 3), "earned_rate_matched": round(sum(ue) / n, 3),
        "earned_discordant_grounded": ep, "earned_discordant_matched": en, "earned_sign_p": _sign_p(ep, en),
        "mean_length_grounded": round(statistics.mean(gl), 2), "mean_length_matched": round(statistics.mean(ul), 2),
        "length_diff_mean": round(statistics.mean(dl), 2), "length_g_gt_u": pos, "length_g_lt_u": neg,
        "length_ties": n - pos - neg, "length_sign_p": _sign_p(pos, neg), "length_wilcoxon_p": _wilcoxon_p(dl),
        "topic_sim_mean": round(statistics.mean(s for s, _ in pairs.values()), 3),
        "k_distribution": {str(k): sum(1 for i in pairs if G[i]["k"] == k) for k in sorted({G[i]["k"] for i in pairs})},
    })
    return out


def _r2_verdict(m: dict) -> str:
    """D-0515: the coded verdict is earned length over MATCHED pairs (own-act Route 2 asks only)."""
    if not isinstance(m, dict) or m.get("n_pairs", 0) < R2_MIN_N:
        return "insufficient_data"
    p = m.get("earned_sign_p")
    if p is not None and p < 0.05:
        return ("grounded_develops_more" if m["earned_rate_grounded"] > m["earned_rate_matched"]
                else "ungrounded_develops_more")
    return "no_advantage_shown"


def r2_signature(matched: bool = True, window_days: float = R2_MATCH_WINDOW_DAYS) -> dict:
    """R2 (docs/plans/thought_grounding.md): do evidence-grounded thoughts DEVELOP (earned-length)
    more often than matched ungrounded ones? Added 2026-08-24 (J-0125, F-0087) once gather() started
    logging train_id (before this, the join key didn't exist and R2 wasn't computable at all —
    F-0014/J-0045).

    Joins evidence_log.jsonl's train_id (an ask made mid-train) against the EXISTING earned-length
    instrument, data/train_length_log.jsonl (core/train_metrics.py: every closed thought-train's
    final length + why it closed — thread-end/ceiling = productive, stalled-* = looped). No new
    judge call; reuses decoupled machinery that already scores development, per the plan's
    decoupled-judge discipline.

    LEGACY fields (kept so earlier reads still parse): grounded_trains / ungrounded_trains are the
    original natural comparison over EVERY ask with a train_id (any source); verdict_productive_legacy
    is the original coded rule on productive_close_rate (saturated ~0.97 both sides, F-3243).

    2026-10-30 (J-2604, D-0515 ruled by Travis, F-3327): three corrections.
      1. The coded `verdict` is EARNED LENGTH (length > 4), productive_close_rate kept as a secondary
         field inside each _stats block.
      2. Only Du's OWN Route 2 asks count as grounding. Every row is classed by `source` (gather() writes
         it from J-2604 on); a row without it is route2 before the 2026-10-29 18:38 Follow Line boot,
         follow_line when Follow Line's shadow log names the same (train_id, question), else unknown.
         A train asked by anything other than Route 2 is neither grounded nor in the ungrounded pool.
      3. `matched_pairs` ports the J-2587 matched-pairs design (_r2_matched): prior length k, alive at k,
         +/-window_days, nearest TF-IDF topic, 1:1 greedy, sign test + Wilcoxon, n pairs reported. The
         verdict is computed on it and needs R2_MIN_N pairs. `matched_pairs_all_sources` is the same
         read over every ask (parity with F-3327's n=75).
    Read-only; never raises (an error is returned in the dict)."""
    try:
        from collections import Counter, defaultdict
        ev_rows = ([json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
                   if _LOG.exists() else [])
        tr_rows = ([json.loads(l) for l in open(_TRAIN_LOG, encoding="utf-8") if l.strip()]
                   if _TRAIN_LOG.exists() else [])
    except Exception as exc:
        return {"error": str(exc)}
    grounded_ids = {r.get("train_id") for r in ev_rows if r.get("train_id")}
    thought_trains = [r for r in tr_rows if r.get("kind") == "thought" and r.get("train_id")]

    def _stats(rows: list[dict]) -> dict:
        n = len(rows)
        if not n:
            return {"n": 0}
        lengths = [r.get("length", 0) for r in rows]
        productive = sum(1 for r in rows if str(r.get("reason", "")) in ("thread-end", "ceiling"))
        earned = sum(1 for r in rows if r.get("length", 0) > R2_EARNED_LEN)
        return {"n": n, "mean_length": round(sum(lengths) / n, 2),
                "earned_rate": round(earned / n, 3), "productive_close_rate": round(productive / n, 3),
                "by_reason": dict(Counter(str(r.get("reason", "?")) for r in rows))}

    grounded = [r for r in thought_trains if r["train_id"] in grounded_ids]
    ungrounded = [r for r in thought_trains if r["train_id"] not in grounded_ids]
    result = {"n_asks": len(ev_rows), "n_asks_with_train_id": sum(1 for r in ev_rows if r.get("train_id")),
              "grounded_trains": _stats(grounded), "ungrounded_trains": _stats(ungrounded),
              "note": ("grounded_trains/ungrounded_trains: legacy natural comparison over every ask "
                       "(any source, topic/prior-length uncontrolled); verdict: earned length over matched "
                       "pairs of own-act Route 2 asks (D-0515, J-2604)"),
              "min_n": R2_MIN_N, "verdict_metric": "earned_rate",
              "verdict_basis": "matched_pairs (own-act route2 asks only)"}
    g0, u0 = result["grounded_trains"], result["ungrounded_trains"]
    result["verdict_productive_legacy"] = (
        "insufficient_data" if len(grounded) < R2_MIN_N else
        ("grounded_develops_more" if g0["productive_close_rate"] > u0.get("productive_close_rate", 0)
         else "no_advantage_shown"))

    # (2) source classification
    fl_keys: set = set()
    try:
        if _FOLLOW_LINE_LOG.exists():
            for l in open(_FOLLOW_LINE_LOG, encoding="utf-8"):
                if '"train_id"' not in l:
                    continue
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                if r.get("train_id") and r.get("q"):
                    fl_keys.add((r["train_id"], str(r["q"]).strip()[:200]))
    except Exception as exc:
        result["follow_line_log_error"] = str(exc)
    src_rows = Counter()
    first_own: dict = {}
    first_any: dict = {}
    other_ids: set = set()
    for r in ev_rows:
        t = r.get("train_id")
        s = _r2_row_source(r, fl_keys)
        src_rows[s] += 1
        if not t:
            continue
        ts = float(r.get("ts") or 0.0)
        first_any[t] = min(first_any.get(t, ts), ts)
        if s.startswith("route2"):
            first_own[t] = min(first_own.get(t, ts), ts)
        else:
            other_ids.add(t)
    result["asks_by_source"] = dict(src_rows)
    own = [r for r in thought_trains if r["train_id"] in first_own]
    clean = [r for r in thought_trains if r["train_id"] not in first_any]
    result["own_grounded_trains"] = _stats(own)
    result["own_ungrounded_trains"] = _stats(clean)
    result["n_trains_asked_only_by_other_source"] = len({t for t in other_ids if t not in first_own}
                                                         & {r["train_id"] for r in thought_trains})

    # (3) matched pairs -> the coded verdict
    if not matched:
        result["verdict"] = "insufficient_data"
        result["matched_pairs"] = {"skipped": True}
        return result
    try:
        steps: dict = defaultdict(list)
        if _TRAIN_STATE_LOG.exists():
            for l in open(_TRAIN_STATE_LOG, encoding="utf-8"):
                if not l.strip():
                    continue
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                if r.get("train_id"):
                    steps[r["train_id"]].append((float(r.get("ts") or 0.0), int(r.get("step") or 0),
                                                 str(r.get("thought") or "")))
        for t in steps:
            steps[t].sort()
        closes = {r["train_id"]: r for r in thought_trains}
        excluded = set(first_any)
        result["matched_pairs"] = _r2_matched(first_own, excluded, closes, steps, window_days)
        result["matched_pairs_all_sources"] = _r2_matched(first_any, excluded, closes, steps, window_days)
    except Exception as exc:
        result["matched_pairs"] = {"error": str(exc), "n_pairs": 0}
    result["verdict"] = _r2_verdict(result["matched_pairs"])
    return result
