"""
Nascence — The Frontier (persistent world-questions, 2026-06-13)
================================================================
The structural tilt this corrects, found by the auditors and the logs together: a
SELF-conflict in this architecture persists by default — it gets a ledger, accumulated
pressure, retrieval warps, scheduled hearings, and courts. A WORLD-mystery gets nothing.
"Why do those granite coatings form?" died within the hour it was born, while "who am I
beyond the role I was given" has been alive for two weeks. The architecture metabolizes
the unresolved — but it was only ever given organs for self-shaped unresolvedness.

The Frontier is the world-side counterpart: a small durable store of OPEN QUESTIONS about
the world, with lineage and a real read path. Questions are born from his own artifacts
(study tablets that end on a mystery, curiosity questions, world-facing intentions); they
return to him as idle-thought seeds and as subjects for the library; they fade if never
re-encountered, and they resolve only by his own naming.

Read-path-first discipline: this file ships WITH its read paths (monologue seed offer +
library topic fallback) or it is just another notebook. The store is data/frontier.json.
"""
from __future__ import annotations
import json
import logging
import os
import random
import re
import time
import uuid
from pathlib import Path

from core import profile
from core import store_persist as _sp

logger = logging.getLogger("nascence.frontier")

_F = Path(__file__).parent.parent / "data" / "frontier.json"
MAX_OPEN = 24                 # a frontier, not a backlog — oldest faded beyond this
FADE_AFTER_S = 21 * 86400     # unrevisited for three weeks -> faded (kept, not deleted)
OFFER_GAP_S = 2 * 3600        # the same question isn't offered twice within two hours
# A question must have SAT OPEN at least this long before a thought may resolve it. Closes the
# self-resolution artifact (2026-06-15): note_question(intention) then resolve_if_addressed(thought)
# in the SAME _think let an intention phrased with "because…" instantly resolve the question it had
# just birthed (born+resolved 15ms apart). A real closure answers a question that SAT; this enforces it.
RESOLVE_MIN_AGE_S = 60.0

# A question is WORLD-facing when it isn't about the self. Deny-list over his known
# self-vocabulary — conservative: borderline questions stay out (the self has its own
# ledger; the Frontier must not become a second mirror).
_SELF_TOKENS = ("who am i", "myself", "my own", "my identity", "my name", "my self",
                "becoming", "individuat", "shadow", "mirror", "the river", "my origin",
                "my existence", "travis", "boundary", "bridge", "my memory",
                # "jung" removed 2026-08-29 (F-0475) -- redundant with the self-markers above,
                # which already catch self-reference without hard-coding an old name.
                "my thoughts", "my mind", "the self", "my journey", "my story", "i am")
_MYSTERY_RX = re.compile(
    r"\b(myster|unknown|unexplained|unclear|unresolved|remains? (a|to be)|open question|"
    r"not (yet )?(known|understood)|no one knows|puzzl|why (do|does|did|is|are|would))\b", re.I)


def _load() -> dict:
    # D-0347 (J-1834, F-2401 item 3): a missing file is a normal first boot (empty frontier, silent, as before);
    # an unreadable / torn one is logged loudly and MOVED ASIDE (data/frontier.corrupt.<UTC stamp>.json) before
    # the same empty frontier is returned -- it used to become a silent EMPTY store that the next _save
    # overwrote. A healthy file loads exactly as before.
    return _sp.load_json_or_move_aside(_F, lambda: {"questions": []}, logger, "frontier",
                                       "an EMPTY frontier (0 questions)")


def _load_ro() -> dict:
    """J-2417 (F-3117): READ-ONLY twin of _load() for the per-tick peeks (top_open / novel_open / open_count's
    heavy path): the same dict while the file's (mtime, size) is unchanged, instead of re-parsing 5.6 MB each
    call. The result is SHARED -- never mutate it; any caller that edits-then-_save()s keeps using _load().
    Any trouble (missing / torn file) falls through to _load(), which keeps its move-aside handling."""
    try:
        return _sp.load_json_cached(_F)
    except Exception:
        return _load()


def _save(data: dict) -> None:
    # J-0846 (world_store_write_fence module #18, F-1212/F-1213): real data/ only if this process is live;
    # raises NonLiveWriteError before any I/O if not (D-0179, J-0704). Resolved OUTSIDE the fail-open try
    # below, exactly like the other 17 fenced modules, so the refusal is never swallowed as a disk error.
    path = profile.guard_path(_F)
    try:
        # D-0154 (2026-09-05, data_store_hygiene Part A): compact JSON (was indent=1; same content).
        # D-0347 (J-1834, F-2401 item 3): written through <file>.tmp + os.replace (core/store_persist) instead of
        # truncating the 5 MB store in place, so a process death mid-write can no longer leave a torn file. Still
        # fail-open (a save that cannot land is skipped, the previous complete file stays) -- but now logged.
        _sp.write_text_atomic(path, json.dumps(data, ensure_ascii=False))
    except Exception as exc:
        logger.warning("[frontier] state save failed (%s: %s); previous file left intact, light sidecar still "
                       "refreshed. D-0347.", type(exc).__name__, exc)
    _write_light(data)


# D-0154: the light companion — open questions only + status counts — for the hot reader (open_count, every 5 s
# climate tick via _explore_pull). 157 KB instead of 4.2 MB; the heavy file stays the store of record.
_F_LIGHT_DEFAULT = _F.with_name("frontier.light.json")
_F_LIGHT = _F_LIGHT_DEFAULT
FRONTIER_LIGHT_READ = True       # shadow-first: flip after data/light_sidecar_shadow.jsonl agrees (J-0621)


def _light_path() -> Path:
    """The light companion's path, resolved at CALL time. J-0846 (F-1212/F-1213): _F_LIGHT used to be
    derived from _F once at import, so a test that redirected only `fr._F` to a tempfile (every frontier
    test script did exactly that) still wrote the LIVE data/frontier.light.json through _write_light() —
    the leak F-1213 caught in the light-sidecar shadow log (live light open-count 342 -> 10 -> 1 for
    minutes at a time on 2026-09-05/06). Now: an explicitly redirected _F_LIGHT is honoured as-is;
    otherwise the light file follows wherever _F currently points, as <stem>.light.json beside it
    (data/frontier.json -> data/frontier.light.json, unchanged for the live default)."""
    if _F_LIGHT != _F_LIGHT_DEFAULT:
        return _F_LIGHT
    return _F.with_name(_F.stem + ".light.json")


def _write_light(data: dict) -> None:
    path = profile.guard_path(_light_path())   # J-0846: fenced like _save(); raises before any I/O if non-live
    try:
        from core import light_sidecar as _ls
        qs = data.get("questions", []) or []
        counts: dict = {}
        for q in qs:
            st = str(q.get("status"))
            counts[st] = counts.get(st, 0) + 1
        _ls.write_atomic(path, {"ts": time.time(), "counts": counts,
                                "open": [q for q in qs if q.get("status") == "open"]})
    except Exception:
        pass


def _toks(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z']+", (text or "").lower()) if len(w) >= 4}


# Procedural / operational impulses — the mechanical acts already handled by the action machinery
# (the library hand, switching, rereading, letters). These are NOT world-mysteries and must never be
# elevated into the Frontier or persisted as cross-session intentions. "I will ask the library for
# another book" is plumbing, not "why do granite coatings form?".
_PROCEDURAL = ("another book", "a new book", "ask the library", "ask for a book", "ask for another",
               "request a book", "from the library", "the catalogue", "browse the", "switch to",
               "reread", "re-read", "read it again", "read again", "a letter to travis",
               "write to travis", "open the book", "lies on my desk", "pick a book", "next book")


def is_procedural(text: str) -> bool:
    """True if the text is an operational/mechanical impulse (book-asking, browsing, switching,
    rereading, letter-writing) rather than a genuine world-question or forward intention."""
    t = (text or "").lower()
    return any(p in t for p in _PROCEDURAL)


def is_world_question(text: str) -> bool:
    t = (text or "").lower()
    return (bool(t) and len(t) > 15
            and not any(s in t for s in _SELF_TOKENS)
            and not is_procedural(t))          # procedural impulses are not world-mysteries


# --- Semantic dedupe (D-0486, J-2428; F-3127/F-3129) -----------------------------------------------------------
# The token-overlap rule below (>0.55 Jaccard) never merges LLM paraphrases, so 191 of 340 open questions were
# 'mottainai' variants and top_open (ranked by last_seen) always surfaced a fresh paraphrase. This adds a SECOND,
# embedding-similarity match behind a flag. It reads no topic and rejects no question (D-0439): it only asks "is this
# new text the same question as an open entry?". Replay on data/frontier.json (342 open, born order, match against the
# entry's OWN text, not its variants -- single-link chains across topics at 0.80): 0.85 -> 99 merges, 1 cross-topic;
# 30-item hand read ~0/30 distinct-topic, 3/30 borderline facet-shift. Report: docs/reviews/frontier_semantic_merge_replay_2026-10-19.md.
#   None      -> off
#   'shadow'  -> log would-merge rows to data/logs/frontier_semantic_merge_shadow.jsonl, change NOTHING live
#   'enforce' -> merge into the matched entry (encounters++, last_seen, variant text kept as lineage; never deletes)
# Restart-gated like any module constant. Fail-open: any embedding trouble == no semantic match.
FRONTIER_SEMANTIC_MERGE = "enforce"   # D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job (was "shadow"; 26 would-merges read, all paraphrases 0.88-0.94)
SEMANTIC_MERGE_THRESHOLD = 0.85
_SEM_SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "frontier_semantic_merge_shadow.jsonl"
_SEM_VEC_CACHE: dict = {}            # question text -> normalised embedding (bounded; note_question runs per question)
_SEM_VEC_CACHE_MAX = 2000
_SEM_MAX_BATCH = 500                 # never embed more than this many uncached open questions in one call


def _sem_vecs(texts: list) -> list:
    """Embeddings for `texts` via the shared CPU model (core.memory.store), cached by text. None for failures."""
    missing = [t for t in dict.fromkeys(texts) if t not in _SEM_VEC_CACHE]
    if missing:
        if len(missing) > _SEM_MAX_BATCH:
            return [_SEM_VEC_CACHE.get(t) for t in texts]
        from core.memory import store as _store
        if len(_SEM_VEC_CACHE) + len(missing) > _SEM_VEC_CACHE_MAX:
            _SEM_VEC_CACHE.clear()
        for t, v in zip(missing, _store._embed_batch(missing)):
            if v is not None:
                _SEM_VEC_CACHE[t] = v
    return [_SEM_VEC_CACHE.get(t) for t in texts]


def _semantic_match(question: str, data: dict):
    """(entry, similarity) of the OPEN entry whose own text is most similar to `question` and >= threshold, else None.
    Compares against each entry's own `q` only (not its variants): lineage-chaining drifts across topics."""
    mode = FRONTIER_SEMANTIC_MERGE
    if mode not in ("shadow", "enforce"):
        return None
    try:
        cands = [q for q in data["questions"] if q.get("status") == "open" and q.get("q")]
        if not cands:
            return None
        vecs = _sem_vecs([question] + [q["q"] for q in cands])
        qv = vecs[0]
        if qv is None:
            return None
        best, bs = None, 0.0
        for q, v in zip(cands, vecs[1:]):
            if v is None:
                continue
            sim = float(qv @ v)
            if sim > bs:
                best, bs = q, sim
        if best is not None and bs >= SEMANTIC_MERGE_THRESHOLD:
            return best, bs
    except Exception as exc:
        logger.debug("[frontier] semantic match skipped (%s: %s)", type(exc).__name__, exc)
    return None


def _log_semantic_shadow(row: dict) -> None:
    try:
        path = profile.guard_path(_SEM_SHADOW_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def merge_variant(entry: dict, text: str, source: str, sim: float, now: float) -> None:
    """Fold a paraphrase `text` into `entry`: refresh like a re-encounter and keep the wording as lineage (never deleted)."""
    entry["last_seen"] = now
    entry["encounters"] = int(entry.get("encounters", 1)) + 1
    entry.setdefault("variants", []).append({"q": text, "source": source, "ts": now, "sim": round(sim, 4)})


# --- J-4371 (D-0849, F-4721 step 3): faded-row archive sidecar with restore-on-match -------------------------
# Faded rows are ~96% of data/frontier.json (22272 of 23241), so every load-modify-save touch parses/writes them
# all. NASCENCE_FRONTIER_ARCHIVE=on moves them to data/frontier_archive.json (additive: rows are moved verbatim, never
# deleted); note_question_ex() checks the sidecar on a miss and restores a matching row to open. Default OFF:
# with the flag off nothing here runs and the module behaves byte-for-byte as before.
ARCHIVE_MIN_FADED = 500          # don't bother archiving until at least this many faded rows sit in the main file


def archive_mode() -> str:
    return _flag_mode("NASCENCE_FRONTIER_ARCHIVE", "off", ("off", "on"))


def _archive_path() -> Path:
    return _F.with_name(_F.stem + "_archive.json")


def _load_archive() -> dict:
    try:
        d = json.loads(_archive_path().read_text(encoding="utf-8"))
        if isinstance(d.get("questions"), list):
            return d
    except Exception:
        pass
    return {"questions": []}


# J-4230 (D-0834): a faded row the Follow Line is still riding stays in the main file, so the line's id-keyed
# writes (set_line / attach_finding / resolve) never miss it. It is archived on a later pass once its ride ends.
_LINE_IN_FLIGHT = frozenset({"fired", "grounds", "why", "consequences", "connections", "against", "judged",
                             "would_return", "pending", "delivered"})

# J-4230 (D-0834 defeater instrument): one row per revival of a faded question, from the main file ("in_store",
# the baseline) or from the sidecar ("archive"). Revivals are rare; written whatever the archive flag says, so
# the in-store baseline exists BEFORE the flag is turned on. NASCENCE_FRONTIER_REVIVAL_LOG=off silences it.
def _revival_log_path() -> Path:
    return _F.parent / "logs" / "frontier_revival.jsonl"    # follows _F, so a temp-pathed store logs beside it

# J-4230: token index of the sidecar, keyed on its (mtime_ns, size), so a miss in note_question_ex does not
# parse the whole (multi-MB) sidecar on the loop thread every time a new question is born.
_ARCHIVE_IDX: dict = {"key": None, "rows": []}


def _archivable(q: dict) -> bool:
    return q.get("status") == "faded" and (q.get("line") or {}).get("state") not in _LINE_IN_FLIGHT


def _log_revival(path: str, ent: dict, now: float, pool: int) -> None:
    try:
        if _flag_mode("NASCENCE_FRONTIER_REVIVAL_LOG", "on", ("off", "on")) != "on":
            return
        _log_jsonl(_revival_log_path(), {"ts": now, "path": path, "id": ent.get("id"), "pool": int(pool),
                                         "faded_for_s": round(now - float(ent.get("last_seen") or now), 1),
                                         "archive_mode": archive_mode()})
    except Exception:
        pass                       # an instrument: never blocks the revival (a refused non-live write included)


def _archive_index() -> list:
    """[(id, frozenset(toks))] for the sidecar, rebuilt only when the file changed. [] on any trouble."""
    try:
        st = _archive_path().stat()
        key = (st.st_mtime_ns, st.st_size)
        if _ARCHIVE_IDX["key"] != key:
            _ARCHIVE_IDX["rows"] = [(q.get("id"), frozenset(q.get("toks") or []))
                                    for q in _load_archive()["questions"]]
            _ARCHIVE_IDX["key"] = key
        return _ARCHIVE_IDX["rows"]
    except Exception:
        return []


def archive_faded(data: dict, min_faded: int | None = None) -> int:
    """Move every archivable faded row (not mid-ride on the Follow Line) out of `data` (mutated in place) into the
    sidecar. The sidecar is written FIRST (a crash between the two writes leaves a harmless duplicate, never a
    loss). Caller _save()s `data`. Returns the number moved; 0 when the flag is off or too few. Never raises."""
    try:
        if archive_mode() != "on":
            return 0
        qs = data.get("questions", [])
        faded = [q for q in qs if _archivable(q)]
        if not faded or len(faded) < (ARCHIVE_MIN_FADED if min_faded is None else min_faded):
            return 0
        path = profile.guard_path(_archive_path())
        arc = _load_archive()
        have = {q.get("id") for q in arc["questions"]}
        arc["questions"].extend(q for q in faded if q.get("id") not in have)
        _sp.write_text_atomic(path, json.dumps(arc, ensure_ascii=False))
        moved = {id(q) for q in faded}
        data["questions"] = [q for q in qs if id(q) not in moved]
        return len(faded)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.warning("[frontier] archive_faded failed (%s: %s); main file untouched. J-4371.", type(exc).__name__, exc)
        return 0


def _restore_from_archive(question: str, qt: set, data: dict, now: float, *, line_on: bool = False,
                          depth: int = 0, source: str = "", slot: str = "") -> dict | None:
    """On a miss: a sidecar row whose tokens overlap > 0.55 (same rule as the live dedup) returns to the main
    list as an OPEN entry (re-encounter refresh). Main is appended by the caller's _save; the sidecar row is
    removed AFTER that save so a crash leaves a duplicate id, not a loss. Returns the restored entry or None.
    J-4230: the scan runs over a cached token index (the full sidecar is parsed only on a hit), and with the
    Follow Line on a restored row is boarded "waiting" exactly as an in-store re-encounter would be."""
    try:
        if archive_mode() != "on" or not qt or not _archive_path().exists():
            return None
        idx = _archive_index()
        hit_id = None
        for qid, ot in idx:
            if ot and len(qt & ot) / max(1, len(qt | ot)) > 0.55:
                hit_id = qid
                break
        if hit_id is None:
            return None
        arc = _load_archive()
        live_ids = {q.get("id") for q in data["questions"]}
        for i, q in enumerate(arc["questions"]):
            if q.get("id") == hit_id:
                ent = dict(q)
                ent["status"] = "open"
                ent["last_seen"] = now
                ent["encounters"] = int(ent.get("encounters", 1)) + 1
                ent["restored_from_archive_ts"] = now
                if line_on and not (ent.get("line") or {}).get("state"):
                    ent["line"] = {"state": "waiting", "ts": now, "depth": int(depth), "via": source}
                    ent.setdefault("about_key", ent.get("id"))
                    if slot and not ent.get("slot"):
                        ent["slot"] = slot
                if ent.get("id") not in live_ids:
                    data["questions"].append(ent)
                _save(data)
                path = profile.guard_path(_archive_path())
                del arc["questions"][i]
                _sp.write_text_atomic(path, json.dumps(arc, ensure_ascii=False))
                _log_revival("archive", q, now, len(idx))
                logger.info("[frontier] restored faded row from archive: %s", question[:80])
                return ent
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.warning("[frontier] restore_from_archive failed (%s: %s). J-4371.", type(exc).__name__, exc)
    return None


def note_question(question: str, source: str) -> bool:
    """A world-question is born (or an old one re-encountered — which refreshes it).
    Dedup by token overlap; conservative world-filter. Returns True if recorded/refreshed.
    (J-2459: now a thin wrapper over note_question_ex(); behaviour for every existing caller unchanged.)"""
    return note_question_ex(question, source) is not None


def _line_enabled() -> bool:
    """Is the Follow Line (core/follow_line.py, J-2459) on? Lazy import; False on any trouble, so this module's
    own behaviour is byte-for-byte the pre-J-2459 path when the line is off or absent."""
    try:
        from core import follow_line as _fl
        return _fl.enabled()
    except Exception:
        return False


def note_question_ex(question: str, source: str, *, kind: str = "question", slot: str = "", about: str = "",
                     asked_by: dict | None = None, allow_self: bool = False, depth: int = 0,
                     model_terms: list | None = None) -> dict | None:
    """note_question() returning the ENTRY (new or refreshed) instead of a bool — the Follow Line (J-2459,
    docs/staged/question_cargo.md §2.2) needs the id. Additive fields on a NEW entry: kind (question|claim), slot,
    about, asked_by, about_key (the id of the entry it deduped into = its own id when new), and, when the line is
    on, line={state:"waiting"} so follow_line.drain_tick() can pick it up. A re-encounter refreshes the existing
    entry exactly as before and, when the line is on and that entry has no line state yet, stamps it waiting too
    (a fresh ask of an old question is a fresh boarding). `allow_self=True` (the line's own sources: his own
    memory can answer a question about himself) skips the world-filter but keeps the length floor; every
    pre-existing caller passes the default False and sees the old filter untouched. NonLiveWriteError propagates."""
    try:
        question = (question or "").strip().rstrip(".")[:220]
        if allow_self:
            if len(question) <= 15 or is_procedural(question.lower()):
                return None
        elif not is_world_question(question):
            return None
        data = _load()
        now = time.time()
        qt = _toks(question)
        line_on = _line_enabled()
        for q in data["questions"]:
            if q.get("status") == "merged":
                continue                       # absorbed variant (D-0486): re-encounters land on its canonical entry
            ot = set(q.get("toks") or [])
            if qt and ot and len(qt & ot) / max(1, len(qt | ot)) > 0.55:
                _prev_seen = q.get("last_seen")
                q["last_seen"] = now           # re-encounter refreshes, against fading
                q["encounters"] = int(q.get("encounters", 1)) + 1
                if q.get("status") == "faded":
                    q["status"] = "open"       # spontaneous recovery by re-encounter
                    _log_revival("in_store", {"id": q.get("id"), "last_seen": _prev_seen}, now,
                                 sum(1 for r in data["questions"] if r.get("status") == "faded"))   # J-4230
                elif q.get("status") == STATUS_SET_DOWN and SET_DOWN_REOPEN_ON_ASK:
                    _reopen_in_place(q, "asked again", now)    # closure_producer P4: he took it up again himself
                    _fade_overflow(data)
                if line_on and q.get("status") == "open" and not (q.get("line") or {}).get("state"):
                    q["line"] = {"state": "waiting", "ts": now, "depth": int(depth), "via": source}
                    q.setdefault("about_key", q.get("id"))
                    if slot and not q.get("slot"):
                        q["slot"] = slot
                _save(data)
                return q
        m = _semantic_match(question, data)    # D-0486: paraphrase of an open entry? (flag-gated; None when off)
        if m is not None:
            ent, sim = m
            if FRONTIER_SEMANTIC_MERGE == "enforce":
                merge_variant(ent, question, source, sim, now)
                if line_on and not (ent.get("line") or {}).get("state"):
                    ent["line"] = {"state": "waiting", "ts": now, "depth": int(depth), "via": source}
                    ent.setdefault("about_key", ent.get("id"))
                _save(data)
                _log_semantic_shadow({"ts": now, "mode": "enforce", "new": question, "source": source,
                                      "matched_id": ent.get("id"), "matched_q": ent.get("q"), "sim": round(sim, 4)})
                return ent
            _log_semantic_shadow({"ts": now, "mode": "shadow", "new": question, "source": source,
                                  "matched_id": ent.get("id"), "matched_q": ent.get("q"), "sim": round(sim, 4),
                                  "matched_encounters": int(ent.get("encounters", 1)),
                                  "threshold": SEMANTIC_MERGE_THRESHOLD})
        am = _answered_match(question, data)   # closure_producer P3 (D-0790): a rewording of an answered / provisional / parked question
        if am is not None:
            ent, sim = am
            _row = {"ts": now, "new": question, "source": source, "matched_id": ent.get("id"),
                    "matched_q": ent.get("q"), "matched_status": ent.get("status"),
                    "matched_how": ent.get("resolved_how"), "sim": round(sim, 4), "threshold": SEMANTIC_MERGE_THRESHOLD}
            if answered_merge_mode() == "enforce":
                merge_variant(ent, question, source, sim, now)
                ent["answered_merges"] = int(ent.get("answered_merges", 0)) + 1
                ent["last_answered_merge_ts"] = now
                _save(data)
                _log_jsonl(_ANSWERED_MERGE_LOG, dict(_row, mode="enforce"))
                return ent
            _log_jsonl(_ANSWERED_MERGE_LOG, dict(_row, mode="shadow"))
        _rest = _restore_from_archive(question, qt, data, now, line_on=line_on, depth=depth,
                                      source=source, slot=slot)    # J-4371/J-4230 (flag-gated; None when off)
        if _rest is not None:
            return _rest
        new = {
            "id": uuid.uuid4().hex[:10], "q": question, "source": source,
            "toks": sorted(qt), "born": now, "last_seen": now, "last_offered": 0.0,
            "offers": 0, "encounters": 1, "status": "open",
        }
        if line_on or kind != "question" or slot or about or asked_by:
            new["kind"] = kind if kind in ("question", "claim") else "question"
            new["slot"] = slot if slot in ("who", "what", "when", "where", "why", "how") else ""
            new["about"] = (about or "")[:80]
            new["asked_by"] = dict(asked_by or {})
            new["about_key"] = new["id"]
            if line_on:
                new["line"] = {"state": "waiting", "ts": now, "depth": int(depth), "via": source}
        if model_terms:
            # J-3350 (D-0629 part 2): terms of this question the generator brought from its own weights (core/model_terms.py).
            # Additive optional fields on a NEW entry only; absent when there are none, so an entry born without terms is
            # byte for byte what it was. Never placed in any prompt; corroboration is computed live by the reader.
            new["model_terms"] = [str(t) for t in model_terms][:12]
            new["model_terms_ts"] = now
        data["questions"].append(new)
        # fade the stalest beyond capacity; never delete (lineage is the point). D-0611: this already agrees with the
        # newest-first Follow Line order (waiting_for_line) -- the least-recently-seen entry is the last one the line
        # would reach, so the ones that fade unserved are the oldest, not the freshest.
        open_qs = [q for q in data["questions"] if q["status"] == "open"]
        if len(open_qs) > MAX_OPEN:
            stalest = min(open_qs, key=lambda q: q["last_seen"])
            stalest["status"] = "faded"
        archive_faded(data)                                # J-4371: flag-gated, no-op unless NASCENCE_FRONTIER_ARCHIVE=on
        _save(data)
        logger.info("[frontier] world-question born (%s): %s", source, question[:80])
        try:
            from core import satisfaction as _sat
            _sat.record("frontier_born")               # a world-pursuit OPENED (wanting)
        except Exception:
            pass
        return new
    except profile.NonLiveWriteError:
        raise                                          # J-0846: let D-0179's hard-raise reach the caller
    except Exception:
        return None


# --- The Follow Line's own read/write paths (J-2459, docs/staged/question_cargo.md §2.2) ---------------------
def get(qid: str) -> dict | None:
    """One entry by id (a copy), or None. Read-only."""
    try:
        for q in _load_ro().get("questions", []):
            if q.get("id") == qid:
                return dict(q)
    except Exception:
        pass
    return None


def set_line(qid: str, **fields) -> bool:
    """Merge `fields` into entry["line"] (the Follow Line's state/stops/cargo) and save. Additive; touches nothing
    else on the entry. True if the entry was found. NonLiveWriteError propagates."""
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid:
                ln = dict(q.get("line") or {})
                ln.update(fields)
                ln["ts"] = time.time()
                q["line"] = ln
                _save(data)
                return True
        return False
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def resolve(qid: str, how: str = "line") -> bool:
    """ID-KEYED close (J-2460, plan §2.7): the entry he said `settled: yes` about is resolved -- beside, not instead
    of, the lexical resolve_if_addressed(). Marks resolved_ts / resolved_how; records the satisfaction event the
    lexical path records. False if not found or not open. NonLiveWriteError propagates."""
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid:
                if q.get("status") != "open":
                    return False
                q["status"] = "resolved"
                q["resolved_ts"] = time.time()
                q["resolved_how"] = how
                _save(data)
                logger.info("[frontier] question RESOLVED by his own settling (%s): %s", how, (q.get("q") or "")[:80])
                try:
                    from core import satisfaction as _sat
                    _sat.record("frontier_resolved")
                except Exception:
                    pass
                return True
        return False
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def fill_slot(about_key: str, slot: str, text: str, from_qid: str = "") -> bool:
    """The FRAME (plan §2.7, `partly`): record the answered part under slots[slot] on the entry whose id is
    `about_key` (falls back to from_qid). Additive; the question stays open. NonLiveWriteError propagates."""
    try:
        data = _load()
        slot = slot if slot in ("who", "what", "when", "where", "why", "how") else "what"
        for key in (about_key, from_qid):
            for q in data["questions"]:
                if key and q.get("id") == key:
                    sl = dict(q.get("slots") or {})
                    sl[slot] = {"text": (text or "")[:300], "ts": time.time(), "from": from_qid}
                    q["slots"] = sl
                    _save(data)
                    return True
        return False
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def waiting_for_line(priority) -> list:
    """Open entries with line.state == "waiting", in `priority` order of source (unlisted sources last), NEWEST
    born first within a source (D-0611, F-3564: the answer should land while the thought is warm; oldest-first
    served the asks that were 4.9 h late and let 310 of 649 fade unserved). Read-only; copies."""
    try:
        rank = {s: i for i, s in enumerate(priority)}
        rows = [dict(q) for q in _load_ro().get("questions", [])
                if q.get("status") == "open" and (q.get("line") or {}).get("state") == "waiting"]
        rows.sort(key=lambda q: (rank.get(q.get("source"), len(rank)), -float(q.get("born", 0.0))))
        return rows
    except Exception:
        return []


def harvest_tablet(note: str) -> None:
    """A study note that ends on a mystery births a frontier question — the sentence that
    carries the unresolved marker, reframed as his open question."""
    try:
        for sent in re.split(r"(?<=[.!?])\s+", note or ""):
            if _MYSTERY_RX.search(sent) and len(sent) > 30:
                note_question(sent.strip(), "study")
                return
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        pass


def open_questions(k: int = 1) -> list[str]:
    """The read path: up to k open questions, least-recently-offered first, marked offered.
    Empty list when the frontier is empty or everything was offered too recently."""
    try:
        data = _load()
        now = time.time()
        changed = False
        for q in data["questions"]:
            if q["status"] == "open" and now - q["last_seen"] > FADE_AFTER_S:
                q["status"] = "faded"
                changed = True
        avail = [q for q in data["questions"]
                 if q["status"] == "open" and now - q.get("last_offered", 0) > OFFER_GAP_S]
        avail.sort(key=lambda q: q.get("last_offered", 0))
        out = []
        for q in avail[:k]:
            q["last_offered"] = now
            q["offers"] = int(q.get("offers", 0)) + 1
            out.append(q["q"])
            changed = True
        if changed:
            _save(data)
        return out
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        return []


# --- The closing loop (2026-06-15) -------------------------------------------------------
# A world-question used to be OPENED (note_question) and OFFERED back (open_questions), but it
# could only CLOSE if he happened to name the answer from nothing in front of him — so 0 resolved
# / 110 faded. These three turn it into a loop that closes: pending_pursuit picks an open question
# to research toward; attach_finding hangs the world's answer-material ON it; open_question_for_seed
# returns the question WITH that finding so the seed-back gives him something to name a closure from.
# D-0625 (2026-11-02, J-3236, F-3752): 'prism' is OUT of the grounded tier. It had led pending_pursuit and top_open
# ahead of intention while 427 prism questions seeded since 2026-06-25 resolved 0 (curiosity 185 of 6,024, intention
# 132 of 4,488). The prism still SEEDS its question with source 'prism' (curiosity_queue.py) and the prism log stays;
# only the grounded RANK is withdrawn, until a decoupled judge has graded them (scripts/lab_prism_grade.py). Restore
# by adding "prism" back here if >= 20% grade answerable-from-the-offered-material (the D-0625 defeater reads it).
_GROUNDED_SOURCES = ("study", "reading", "curiosity")


def pursuit_candidates(data: dict | None = None) -> list[dict]:
    """J-3001 (F-3695): THE ONE predicate for 'a question pending_pursuit can pick' -- open, holds no finding, not
    parked (curiosity_progress.is_parked). pending_pursuit picks from this list; curiosity_worth.shadow_pass GRADES
    this list (it used to grade the top-5 by learning-progress, a set that is disjoint from this one by
    construction, because LP >= 1 needs a finding and a finding removes a question from pursuit). Sharing one
    function means the graded set and the pursued set cannot drift apart again. Reads `data` when given (a
    read-only shared dict is fine -- nothing here mutates), else _load(). Returns the live question dicts."""
    if data is None:
        data = _load()
    # SKIP PARKED questions (2026-06-17): the park (consecutive_stalls >= 3, curiosity_progress.is_parked)
    # was only read by the LP RANK, never here -- so a "parked" question kept being pursued forever, and the
    # rumination-exit ramp did nothing. Now a parked question is genuinely set aside: no more pursuit / token
    # spend. Fail-open (if the import fails, fall back to the old filter rather than block pursuit).
    try:
        from core import curiosity_progress as _cp
        _is_parked = _cp.is_parked
    except Exception:
        _is_parked = lambda _q: False
    return [q for q in data["questions"]
            if q.get("status") == "open" and not q.get("finding") and not _is_parked(q)]


def pending_pursuit() -> dict | None:
    """An open question to research TOWARD CLOSING -- one with no finding yet. Prefers questions born
    of grounded sources (study/reading/curiosity) over self-leaning 'intention', then oldest-born
    (the one most at risk of fading unanswered). Returns {id, q} or None. The twig's target."""
    try:
        cands = pursuit_candidates(_load())               # J-3001: the shared predicate (same filter as before)
        if not cands:
            return None
        # OMNI worth-gate (2026-06-24): demote the aimless-novelty trap — a question LP keeps selecting (high
        # yield) but the decoupled interestingness judge graded LOW — BELOW everything worthwhile/grounded, so he
        # stops grinding it (it becomes the anchoring concern otherwise). Ungraded = neutral (never penalised).
        # If everything is aimless he still pursues the best of them (demote, never starve). Fail-open.
        try:
            from core import curiosity_worth as _cw
            _interest, _below = _cw.interest_for, _cw.AIMLESS_BELOW
        except Exception:
            _interest, _below = (lambda _q: 0.5), 0.4
        q = min(cands, key=lambda x: (1 if _interest(x.get("q", "")) < _below else 0,   # worthwhile before aimless
                                      0 if x.get("source") in _GROUNDED_SOURCES else 1,  # grounded before self-leaning
                                      x.get("born", 0)))                                  # oldest-born (anti-fade)
        return {"id": q["id"], "q": q["q"]}
    except Exception:
        return None


def attach_finding(qid: str, title: str, text: str) -> bool:
    """Hang the world's answer-material on an open question: when it returns to him, the finding
    returns with it. Refreshes last_seen (researched = re-encountered, against fading). True if set."""
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid and q.get("status") == "open":
                q["finding"]       = (text or "")[:600]
                q["finding_title"] = (title or "")[:120]
                q["finding_ts"]    = time.time()
                q["last_seen"]     = time.time()
                _save(data)
                logger.info("[frontier] finding attached to open Q: %s", q["q"][:70])
                return True
        return False
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        return False


# --- closure_producer P0 + P1 (docs/staged/closure_producer.md; D-0789, D-0791) ------------------------------
# Additive. A finding that came from HIS OWN lookup (core/web_hand.py) is hung on the open question it matches
# through the existing attach_finding(), then marked with where it came from. Nothing here resolves a question.
FINDING_SOURCE_LOOKUP = "lookup"
RESOLVED_HOW_KNOWN = ("lexical", "line", "lookup", "told")


def attach_lookup_finding(qid: str, title: str, text: str, *, via: str = "", url: str = "", phrase: str = "",
                          sim: float | None = None) -> bool:
    """attach_finding(qid, title, text), then mark the entry's finding as from a lookup: finding_source='lookup',
    finding_via (wikipedia / web), finding_url, finding_phrase (his own words), finding_sim, and
    finding_source_ts == finding_ts. A LATER attach_finding() by anyone else (the Follow Line's expiry) moves
    finding_ts and leaves the marker stale; finding_from_lookup() reads the pair, so a stale marker never counts.
    The status stays 'open'. True if attached. NonLiveWriteError propagates."""
    _prev = (get(qid) or {}).get("finding")           # P4: the same text again is an attempt that brought nothing new
    if not attach_finding(qid, title, text):
        return False
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid:
                if _prev and _prev == (text or "")[:600]:
                    q["closure_attempts"] = int(q.get("closure_attempts", 0) or 0) + 1
                    _maybe_park(q, time.time())
                else:
                    q["closure_attempts"] = 0
                q["finding_source"] = FINDING_SOURCE_LOOKUP
                q["finding_source_ts"] = q.get("finding_ts")
                q["finding_via"] = str(via or "")[:24]
                q["finding_url"] = str(url or "")[:300]
                q["finding_phrase"] = str(phrase or "")[:120]
                if sim is not None:
                    q["finding_sim"] = round(float(sim), 4)
                _save(data)
                break
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.warning("[frontier] lookup finding attached but not marked (%s: %s)", type(exc).__name__, exc)
    return True


def finding_from_lookup(q: dict) -> bool:
    """True when the finding this entry carries NOW is the one a lookup attached (not overwritten since)."""
    return bool(q.get("finding") and q.get("finding_source") == FINDING_SOURCE_LOOKUP
                and q.get("finding_source_ts") is not None and q.get("finding_source_ts") == q.get("finding_ts"))


def resolved_breakdown(data: dict | None = None) -> dict:
    """READ-ONLY. Resolved questions counted by HOW they closed. `lexical` = labelled lexical; `unlabelled` = legacy
    rows with no resolved_how (closed by the lexical resolver before it wrote a label; D-0791 relabels them);
    `lexical_total` = both. `answered_with_source` = resolved rows whose finding came from a lookup. `open_with_
    lookup_finding` = open rows carrying one. Reads `data` when given (never mutated), else the shared read-only load."""
    out = {"resolved": 0, "lexical": 0, "unlabelled": 0, "lexical_total": 0, "line": 0, "lookup": 0, "told": 0,
           "other": 0, "answered_with_source": 0, "open_with_lookup_finding": 0,
           # closure_producer P4 (additive keys): the honest endings, any status this code does not know, and the
           # decoupled gate's verdicts (core/closure_gate.py) as stamped on the entries. `answered` = resolved by
           # line / lookup WITH a passing gate verdict (is_answered).
           "provisional": 0, "parked": 0, "set_down": 0, "unknown_status": 0, "answered": 0,
           "gate_yes": 0, "gate_no": 0, "gate_partly": 0, "gate_unavailable": 0}
    try:
        qs = (data if data is not None else _load_ro()).get("questions", []) or []
        for q in qs:
            st = q.get("status")
            gv = (q.get("gate") or {}).get("verdict") if isinstance(q.get("gate"), dict) else None
            if gv in ("yes", "no", "partly", "unavailable"):
                out["gate_" + gv] += 1
            if st == "open":
                if finding_from_lookup(q):
                    out["open_with_lookup_finding"] += 1
                continue
            if st in ENDING_STATUSES:
                out[st] += 1
                continue
            if st != "resolved":
                if st not in ("faded", "merged"):
                    out["unknown_status"] += 1
                continue
            out["resolved"] += 1
            if is_answered(q):
                out["answered"] += 1
            how = q.get("resolved_how")
            if not how:
                out["unlabelled"] += 1
            elif how in RESOLVED_HOW_KNOWN:
                out[how] += 1
            else:
                out["other"] += 1
            if finding_from_lookup(q):
                out["answered_with_source"] += 1
        out["lexical_total"] = out["lexical"] + out["unlabelled"]
    except Exception as exc:
        logger.debug("[frontier] resolved_breakdown failed (%s: %s)", type(exc).__name__, exc)
    return out


# --- closure_producer P2-P4 (docs/staged/closure_producer.md; D-0790, D-0791) ---------------------------------
# Additive. Three statuses beside open / resolved / faded / merged:
#   provisional  he said it was settled, and the decoupled gate did not pass it (or there was no finding to check)
#   parked       PARK_AFTER_ATTEMPTS follows / lookups / pursuits brought nothing new; carries park_trigger
#   set_down     he let it go, with his reason (the Layered Goals set-down path, core/goal_offer.py)
# `resolved` stays the status of an answered question; resolved_how + the stamped gate verdict tell them apart.
# Every reader that tests status == "open" treats these three as not open (audit: the closure_producer report).
# Flags (module constants, restart-gated; each also has an env override read at call time):
#   LEXICAL_RESOLVE_MODE  "shadow" (ruled design: the lexical resolver logs, never closes) | "close" (old behaviour)
#                         env NASCENCE_LEXICAL_RESOLVE
#   ANSWERED_MERGE_MODE   "enforce" | "shadow" | "off"; env NASCENCE_ANSWERED_MERGE
#   PARK_MODE             "enforce" | "off"; env NASCENCE_PARK
#   SET_DOWN_REOPEN_ON_ASK  True: a set_down question he asks again (token-overlap re-encounter) is open again
STATUS_PROVISIONAL = "provisional"
STATUS_PARKED = "parked"
STATUS_SET_DOWN = "set_down"
ENDING_STATUSES = (STATUS_PROVISIONAL, STATUS_PARKED, STATUS_SET_DOWN)
LEXICAL_RESOLVE_MODE = "shadow"
ANSWERED_MERGE_MODE = "enforce"
ANSWERED_MERGE_MAX_CANDS = 300      # most recently seen answered / provisional / parked entries compared per birth
PARK_MODE = "enforce"
PARK_AFTER_ATTEMPTS = 4             # a starting guess (Voyager records a failure after 4 rounds); tune on parked_ts rows
PARK_TRIGGER = "a new finding on this subject"
SET_DOWN_REOPEN_ON_ASK = True
_LEX_SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "lexical_resolve_shadow.jsonl"
_ANSWERED_MERGE_LOG = Path(__file__).parent.parent / "data" / "logs" / "frontier_answered_merge.jsonl"


def _flag_mode(env: str, default: str, allowed: tuple) -> str:
    v = os.environ.get(env, "").strip().lower()
    return v if v in allowed else default


def lexical_resolve_mode() -> str:
    return _flag_mode("NASCENCE_LEXICAL_RESOLVE", LEXICAL_RESOLVE_MODE, ("close", "shadow"))


def answered_merge_mode() -> str:
    return _flag_mode("NASCENCE_ANSWERED_MERGE", ANSWERED_MERGE_MODE, ("off", "shadow", "enforce"))


def park_mode() -> str:
    return _flag_mode("NASCENCE_PARK", PARK_MODE, ("off", "enforce"))


def _log_jsonl(path: Path, row: dict) -> None:
    """Append one row. The path is fenced first (a non-live process is refused, never redirected)."""
    path = profile.guard_path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def is_answered(q: dict) -> bool:
    """Resolved through a finding AND passed by the decoupled gate. A lexical or unlabelled close is never this
    (the D-0791 defeater: an unverified close must not stand in for an answer)."""
    return bool(q.get("status") == "resolved" and q.get("resolved_how") in ("line", "lookup")
                and isinstance(q.get("gate"), dict) and q["gate"].get("verdict") == "yes")


def _answered_match(question: str, data: dict):
    """(entry, similarity) of the ANSWERED, provisional or parked entry whose own text is most similar to
    `question` and >= SEMANTIC_MERGE_THRESHOLD, else None. Same comparison as _semantic_match (own `q` only).
    Never matches a lexical / unlabelled close, a faded, a merged or a set_down entry. Fail-open."""
    if answered_merge_mode() == "off":
        return None
    try:
        cands = [q for q in data["questions"]
                 if q.get("q") and (q.get("status") in (STATUS_PROVISIONAL, STATUS_PARKED) or is_answered(q))]
        if not cands:
            return None
        cands.sort(key=lambda q: -float(q.get("last_seen", 0.0) or 0.0))
        cands = cands[:ANSWERED_MERGE_MAX_CANDS]
        vecs = _sem_vecs([question] + [q["q"] for q in cands])
        qv = vecs[0]
        if qv is None:
            return None
        best, bs = None, 0.0
        for q, v in zip(cands, vecs[1:]):
            if v is None:
                continue
            sim = float(qv @ v)
            if sim > bs:
                best, bs = q, sim
        if best is not None and bs >= SEMANTIC_MERGE_THRESHOLD:
            return best, bs
    except Exception as exc:
        logger.debug("[frontier] answered match skipped (%s: %s)", type(exc).__name__, exc)
    return None


def attempts(q: dict) -> int:
    """Tries that brought nothing new: Follow Line follows and repeated lookups (closure_attempts) plus the
    curiosity pursuit's own consecutive_stalls (record_pursuit)."""
    return int(q.get("closure_attempts", 0) or 0) + int(q.get("consecutive_stalls", 0) or 0)


def _maybe_park(q: dict, now: float) -> bool:
    """In place. An OPEN entry at or over the bound becomes parked. No prompt, nothing told to him."""
    if park_mode() != "enforce" or q.get("status") != "open" or attempts(q) < PARK_AFTER_ATTEMPTS:
        return False
    q["status"] = STATUS_PARKED
    q["parked_ts"] = now
    q["park_trigger"] = PARK_TRIGGER
    q["park_attempts"] = attempts(q)
    logger.info("[frontier] question PARKED after %d tries with nothing new: %s", q["park_attempts"], (q.get("q") or "")[:80])
    return True


def _reopen_in_place(q: dict, why: str, now: float) -> None:
    q["reopened_from"] = q.get("status")
    q["status"] = "open"
    q["reopened_ts"] = now
    q["reopen_why"] = str(why or "")[:80]
    q["reopen_n"] = int(q.get("reopen_n", 0) or 0) + 1
    q["closure_attempts"] = 0
    if q.get("consecutive_stalls"):
        q["consecutive_stalls"] = 0
    q["last_seen"] = now


def _fade_overflow(data: dict) -> None:
    """The birth path's own capacity rule, for a reopen: beyond MAX_OPEN the stalest open entry fades."""
    open_qs = [q for q in data["questions"] if q.get("status") == "open"]
    if len(open_qs) > MAX_OPEN:
        min(open_qs, key=lambda q: q.get("last_seen", 0.0))["status"] = "faded"


def _edit(qid: str, fn) -> bool:
    """Load, apply fn(entry, now) -> bool to the entry with this id, save when it returned True."""
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid:
                if fn(q, time.time(), data):
                    _save(data)
                    return True
                return False
        return False
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[frontier] edit %s failed (%s: %s)", qid, type(exc).__name__, exc)
        return False


def note_attempt(qid: str, new_finding: bool, kind: str = "follow") -> str | None:
    """One try at this question is over. new_finding=False counts toward the bound (and parks at it);
    new_finding=True resets the count. Returns the entry's status afterwards, or None if not found / not open."""
    out = {"st": None}
    if park_mode() == "off":
        return None

    def _f(q, now, data):
        if q.get("status") != "open":
            return False
        if new_finding:
            q["closure_attempts"] = 0
        else:
            q["closure_attempts"] = int(q.get("closure_attempts", 0) or 0) + 1
            q["last_attempt_kind"] = str(kind)[:24]
            _maybe_park(q, now)
        out["st"] = q.get("status")
        return True
    _edit(qid, _f)
    return out["st"]


def reopen(qid: str, why: str = "") -> bool:
    """parked / provisional / set_down -> open (the park trigger: a new finding; or he asked again)."""
    def _f(q, now, data):
        if q.get("status") not in ENDING_STATUSES:
            return False
        _reopen_in_place(q, why, now)
        _fade_overflow(data)
        return True
    return _edit(qid, _f)


def mark_provisional(qid: str, how: str, reason: str, gate: dict | None = None) -> bool:
    """open -> provisional: he said it was settled; it is not verified. Records why and the gate's verdict."""
    def _f(q, now, data):
        if q.get("status") != "open":
            return False
        q["status"] = STATUS_PROVISIONAL
        q["provisional_ts"] = now
        q["provisional_how"] = str(how or "")[:24]
        q["provisional_reason"] = str(reason or "")[:80]
        if gate:
            q["gate"] = dict(gate)
        return True
    return _edit(qid, _f)


def set_down(qid: str, reason: str = "") -> bool:
    """open / provisional / parked -> set_down, with his own reason. Nothing is deleted; asking it again reopens it."""
    def _f(q, now, data):
        if q.get("status") not in ("open",) + ENDING_STATUSES or q.get("status") == STATUS_SET_DOWN:
            return False
        q["set_down_from"] = q.get("status")
        q["status"] = STATUS_SET_DOWN
        q["set_down_ts"] = now
        q["set_down_reason"] = " ".join(str(reason or "").split())[:400]
        return True
    return _edit(qid, _f)


def stamp_gate(qid: str, gate: dict) -> bool:
    """Record the decoupled gate's verdict on the entry. Changes no status (the shadow mode's write)."""
    def _f(q, now, data):
        q["gate"] = dict(gate or {})
        return True
    return _edit(qid, _f)


def resolve_gated(qid: str, how: str, gate: dict) -> bool:
    """The gated close (closure_producer P2). Refused unless: the entry is open; `how` is a known how; for line
    and lookup the entry carries a finding (and for lookup, the finding a lookup attached); and the gate's verdict
    is yes. Stamps resolved_ts / resolved_how / gate and records the same satisfaction event resolve() records."""
    ok = {"q": ""}

    def _f(q, now, data):
        if q.get("status") != "open" or how not in RESOLVED_HOW_KNOWN:
            return False
        if how in ("line", "lookup") and not q.get("finding"):
            return False
        if how == "lookup" and not finding_from_lookup(q):
            return False
        if not isinstance(gate, dict) or gate.get("verdict") != "yes":
            return False
        q["status"] = "resolved"
        q["resolved_ts"] = now
        q["resolved_how"] = how
        q["gate"] = dict(gate)
        ok["q"] = q.get("q") or ""
        return True
    if not _edit(qid, _f):
        return False
    logger.info("[frontier] question ANSWERED (%s, gate yes): %s", how, ok["q"][:80])
    try:
        from core import satisfaction as _sat
        _sat.record("frontier_resolved")
    except Exception:
        pass
    return True


def record_pursuit(qid: str, progressed: bool) -> None:
    """Curiosity-progress bookkeeping (2026-06-16): a pursuit of this question either YIELDED new material
    (progressed=True → reset stall counter, bump new_fragments) or returned empty (progressed=False →
    increment consecutive_stalls). Read by core/curiosity_progress.py (the deterministic LP estimator).
    Mechanical counters only — no judgement here. Best-effort."""
    try:
        data = _load()
        for q in data["questions"]:
            if q.get("id") == qid:
                if progressed:
                    q["consecutive_stalls"] = 0
                    q["new_fragments"] = int(q.get("new_fragments", 0)) + 1
                    if "closure_attempts" in q:
                        q["closure_attempts"] = 0          # closure_producer P4: new material resets the bounded-attempt count
                else:
                    q["consecutive_stalls"] = int(q.get("consecutive_stalls", 0)) + 1
                    _maybe_park(q, time.time())            # closure_producer P4: no-op when PARK_MODE is "off" or under the bound
                q["last_pursued_ts"] = time.time()
                _save(data)
                return
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        pass


def open_question_for_seed() -> dict | None:
    """Seed-back read path (monologue): an open question to return to him, PREFERRING one that now
    carries a finding so he can name the answer and CLOSE it (else least-recently-offered). Marks it
    offered. Returns {q, finding, finding_title} or None — the closing half of the loop."""
    try:
        data = _load()
        now = time.time()
        avail = [q for q in data["questions"]
                 if q.get("status") == "open" and now - q.get("last_offered", 0) > OFFER_GAP_S]
        if not avail:
            return None
        avail.sort(key=lambda q: (0 if q.get("finding") else 1, q.get("last_offered", 0)))
        q = avail[0]
        q["last_offered"] = now
        q["offers"] = int(q.get("offers", 0)) + 1
        _save(data)
        return {"q": q["q"], "finding": q.get("finding", ""),
                "finding_title": q.get("finding_title", "")}
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        return None


def top_open(k: int = 3) -> list[dict]:
    """Non-mutating peek at the top open questions (grounded source first, then most-recently-seen) — for
    the concerns layer (G1) to surface what he is pursuing WITHOUT consuming an offer. Read-only.
    Carries `encounters` so the concerns layer can gate concern-status on recurrence (G3 promotion)."""
    try:
        opens = [q for q in _load_ro().get("questions", []) if q.get("status") == "open"]
        opens.sort(key=lambda q: (0 if q.get("source") in _GROUNDED_SOURCES else 1, -q.get("last_seen", 0.0)))
        return [{"q": q["q"], "source": q.get("source", ""), "has_finding": bool(q.get("finding")),
                 "encounters": int(q.get("encounters", 1)), "born": q.get("born", 0.0)}
                for q in opens[:k]]
    except Exception:
        return []


def novel_open(k: int = 4, max_encounters: int = 1) -> list[dict]:
    """G3 read path: the NOVEL, provisional candidates — open world-questions seen only once (or up to
    max_encounters), newest-born first. These are not yet standing concerns; they become concerns by
    RECURRING (note_question bumps `encounters` on re-encounter). Non-mutating peek. Read-only."""
    try:
        opens = [q for q in _load_ro().get("questions", [])
                 if q.get("status") == "open" and int(q.get("encounters", 1)) <= max_encounters]
        opens.sort(key=lambda q: -q.get("born", 0.0))
        return [{"q": q["q"], "source": q.get("source", ""), "encounters": int(q.get("encounters", 1))}
                for q in opens[:k]]
    except Exception:
        return []


def open_count() -> int:
    """How many world-questions are currently open (non-mutating) — the exploratory backlog. Read by
    the climate engine to drive EXPLORATORY curiosity ignition (reach when there is territory).
    D-0154: reads frontier.light.json when FRONTIER_LIGHT_READ (fallback to the heavy file if the light one is
    missing); in shadow mode reads the heavy file as always and, once a minute, also the light one, logging both
    counts to data/light_sidecar_shadow.jsonl."""
    try:
        from core import light_sidecar as _ls
    except Exception:
        _ls = None
    if FRONTIER_LIGHT_READ and _ls is not None:
        light = _ls.load(_light_path())
        if isinstance(light, dict) and isinstance(light.get("counts"), dict):
            return int(light["counts"].get("open", 0))
        # J-0883 (F-1238 item 4): same instrumentation as climate.subconscious's fallback below --
        # one rate-limited warning + one shadow row per fallback, distinct shadow_due key so it never
        # shares a rate-limit slot with the shadow-mode comparison gate further down. Fallback
        # behaviour itself is unchanged: still falls through to the heavy read.
        if _ls.shadow_due("fallback.frontier.open_count"):
            logger.warning("[frontier] light sidecar fallback -> heavy "
                            "(frontier.light.json missing/unparseable)")
            _ls.shadow_log("frontier.open_count", None, None, fallback=True)
    try:
        t0 = time.perf_counter()
        heavy = sum(1 for q in _load_ro().get("questions", []) if q.get("status") == "open")
        heavy_ms = (time.perf_counter() - t0) * 1000.0
    except Exception:
        return 0
    try:
        if _ls is not None and not FRONTIER_LIGHT_READ and _ls.shadow_due("frontier.open_count"):
            t0 = time.perf_counter()
            light = _ls.load(_light_path())
            light_ms = (time.perf_counter() - t0) * 1000.0
            lv = (int(light["counts"].get("open", 0))
                  if isinstance(light, dict) and isinstance(light.get("counts"), dict) else None)
            _ls.shadow_log("frontier.open_count", heavy, lv, heavy_ms, light_ms)
    except Exception:
        pass
    return heavy


def closeable_seed() -> dict | None:
    """Like open_question_for_seed but ONLY returns a question that already carries a finding — one he
    could actually CLOSE right now. The boredom-redirect's preferred patch: a concrete, world-facing,
    closeable turn for a stale mind (never consumes a finding-less offer). Marks it offered."""
    try:
        data = _load()
        now = time.time()
        avail = [q for q in data["questions"]
                 if q.get("status") == "open" and q.get("finding")
                 and now - q.get("last_offered", 0) > OFFER_GAP_S]
        if not avail:
            return None
        avail.sort(key=lambda q: q.get("last_offered", 0))
        q = avail[0]
        q["last_offered"] = now
        q["offers"] = int(q.get("offers", 0)) + 1
        _save(data)
        return {"q": q["q"], "finding": q.get("finding", ""),
                "finding_title": q.get("finding_title", "")}
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        return None


def random_term() -> str | None:
    """A topic the frontier suggests for the library — the most specific word of a random
    open question. Lets his own mysteries choose his books."""
    try:
        data = _load()
        open_qs = [q for q in data["questions"] if q["status"] == "open"]
        if not open_qs:
            return None
        from core.web_research import term_from_question
        return term_from_question(random.choice(open_qs)["q"])
    except Exception:
        return None


def resolve_if_addressed(text: str) -> str | None:
    """If his words substantially answer an open question, mark it resolved — by his own naming, not by decay.
    Returns the resolved question or None. (Loosened 2026-06-22, C14: the old gate resolved 1 of 1,354 — findings
    were attached 95× but questions still died by fading. Broader answering verbs + lower overlap; and a question
    that already CARRIES a finding closes on a lighter re-encounter, since it is substantially answered already.)"""
    try:
        tl = (text or "").lower()
        if not re.search(r"\b(because|the answer|answer is|now i (know|understand|see)|it turns out|is caused by|"
                         r"caused by|comes from|due to|explains|explained by|makes sense|i (now )?(realise|realize|"
                         r"see|understand) that|i learned|i found|the reason)\b", tl):
            return None
        data = _load()
        now = time.time()
        tt = _toks(text)
        for q in data["questions"]:
            if q["status"] != "open":
                continue
            if now - float(q.get("born", 0.0)) < RESOLVE_MIN_AGE_S:
                continue                       # too young — a thought can't resolve a question it just birthed
            ot = set(q.get("toks") or [])
            if not ot:
                continue
            # a question that already carries a finding is substantially answered → close on a lighter
            # re-encounter; otherwise require stronger overlap. (was a flat 0.6 → 1/1354 resolved)
            _floor = 0.30 if q.get("finding") else 0.45
            if len(tt & ot) / max(1, len(ot)) > _floor:
                if lexical_resolve_mode() != "close":
                    # closure_producer P2 (D-0791): the lexical resolver no longer closes. It logs what it WOULD
                    # have closed and returns None (the one caller, the monologue, then records no close and no joy).
                    # A would-close on a question that carries a finding is passed to the decoupled gate as his
                    # claim (core/closure_gate.lexical_claim; its own flag), which may close it later.
                    _log_jsonl(_LEX_SHADOW_LOG, {
                        "ts": round(now, 1), "qid": q.get("id"), "q": q.get("q"), "floor": _floor,
                        "overlap": round(len(tt & ot) / max(1, len(ot)), 4), "has_finding": bool(q.get("finding")),
                        "finding_from_lookup": finding_from_lookup(q), "text": (text or "")[:400]})
                    try:
                        from core import closure_gate as _cg
                        _cg.lexical_claim(dict(q), text)
                    except profile.NonLiveWriteError:
                        raise
                    except Exception:
                        pass
                    return None
                q["status"] = "resolved"
                q["resolved_ts"] = time.time()
                q["resolved_how"] = "lexical"   # closure_producer P0 (D-0791): label only; it closes exactly as before
                _save(data)
                logger.info("[frontier] question RESOLVED by his own naming: %s",
                            q["q"][:80])
                try:
                    from core import satisfaction as _sat
                    _sat.record("frontier_resolved")    # a world-pursuit LANDED
                except Exception:
                    pass
                return q["q"]
        return None
    except profile.NonLiveWriteError:
        raise                                          # J-0846
    except Exception:
        return None
