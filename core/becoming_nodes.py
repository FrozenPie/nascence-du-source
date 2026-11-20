"""core/becoming_nodes.py -- the T4 estate-node writer (J-3875, design J-3835 sections 2, 3, 7; D-0664 option 3).

A solidified (or harvested) becoming candidate may become ONE estate node: a single sentence of Du's own, chosen
deterministically (the medoid of his deduplicated evidence sentences), carrying its evidence ids in an append-only
ledger.  SHADOW ONLY as shipped: every flag below is False, and False is byte-identical to the code before this module
existed (no I/O, no thread, no import side effect).  Turning the writer on is the founder's call, behind gate G2 of the
design (the claim-test instruments must pass first); this module does not decide that.

What it does
  admit(source, candidate, evidence, gates) -> dict
    1. pool the evidence texts, split to sentences, keep 40-240 chars, first person, no speaker-boundary hit, never cut
       mid-sentence (a sentence over the cap is dropped, not truncated), dedupe by normalised sha1;
    2. embed them in one batch (the in-process MiniLM embedder, NOT a model hub) and take the medoid (highest mean cosine
       to the others, the same statistic core/identity_estate._cluster_values uses);
    3. coherence gate: admit only if the medoid score exceeds the p95 of the same statistic over consecutive 15-thought
       windows of his own last 14 days, and there are >= 6 sentences from >= 3 distinct thoughts.  Otherwise a
       no_medoid / below_null SHADOW row is written and nothing else;
    4. id = bsym_ + sha1(source|candidate_key|sha1(text))[:12]: idempotent on retry, a different row under the same id
       is a hard refusal;
    5. shadow row to data/logs/becoming_nodes_shadow.jsonl; with BECOMING_NODES_WRITE also an `admit` row appended to
       data/identity/becoming_nodes.jsonl (append-only: no edit or delete event; weight is computed by the reader, never
       stored).
  on_chain_resolved(prov, dec, lived_refs): the T4-chain hook; schedules admit() on a single-flight daemon thread so the
  embed never runs on the event loop.  Never raises into the caller.

What it does NOT do: call an LLM (so no prompt-registry change), touch the_becoming facet / vault / axiom.json /
provisional_axiom.json / tensions / arc entries, store the authored paragraph (only its sha1), or inject anything into a
prompt.  The estate seed() step and the projection branch (BECOMING_NODES_SEED, BECOMING_PROJECT) are separate build jobs
(design section 7 jobs 7 and 8); the flags are declared here so there is one place that names all four.

Write fence (D-0179): guard_path() is resolved OUTSIDE the swallow-all try, so a non-live process raises
profile.NonLiveWriteError and writes nothing.  Hermetic tests redirect SHADOW_F / LEDGER_F with lab_env.isolate(also=...).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.becoming_nodes")

# ---- flags (module constants, all False: False = byte-identical old behaviour) -----------------------------------
BECOMING_NODES_ENABLED = False   # the writer runs and logs the would-be row only
BECOMING_NODES_WRITE = False     # with ENABLED: also append admitted rows to the ledger
BECOMING_NODES_SEED = False      # (job 8) estate seed() emits ledger nodes -- declared here, read there
BECOMING_PROJECT = False         # (job 7) projection treats the type specially -- declared here, read there

# ---- constants (named guesses where the design says so) ----------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
LEDGER_F = _ROOT / "data" / "identity" / "becoming_nodes.jsonl"
SHADOW_F = _ROOT / "data" / "logs" / "becoming_nodes_shadow.jsonl"

TYPE = "becoming_symbol"
ID_PREFIX = "bsym_"
WEIGHT0 = 0.5                    # design 2.6: below most nodes; resemblance, not standing, earns the slot
SENT_MIN, SENT_MAX = 40, 240
MIN_SENTENCES, MIN_THOUGHTS = 6, 3
NULL_DAYS = 14
NULL_WINDOW, NULL_STEP = 15, 5
NULL_MAX_THOUGHTS = 3000
NULL_PCTL = 95.0
NULL_TTL_S = 6 * 3600

# the SOLIDIFY judge's own selector for a "lived" thought (nodes/subconscious_node._judge_lived_integration)
_LIVED_RE = re.compile(r"\b(I|my|myself|me|self|river|mind|made|built|becoming|am)\b", re.I)
_FIRST_PERSON_RE = re.compile(r"\b(I|my|me|myself)\b", re.I)
_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_NEGATION_RE = re.compile(r"\bno longer\b|\bnot\b.{0,60}\bbut\b", re.I)

_write_lock = threading.Lock()
_bg_lock = threading.Lock()
_null_cache: dict = {}


# ---- pure helpers ------------------------------------------------------------------------------------------------
def _embed_batch(texts):
    """Indirection so tests can swap the embedder; the real one is the in-process MiniLM batch embed."""
    from core.memory.store import _embed_batch as _eb
    return _eb(texts)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()


def _sha1(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()


def _norm_sha1(s: str) -> str:
    return _sha1(_norm(s))


def _boundary_hit(s: str) -> bool:
    from core.provisional_identity import speaker_boundary_hit
    return bool(speaker_boundary_hit(s))


def split_sentences(text: str) -> list:
    """Whole sentences only. Nothing is ever truncated: an over-long sentence is dropped by the caller's length test."""
    t = " ".join((text or "").split())
    return [s.strip() for s in _SPLIT_RE.split(t) if s.strip()]


def qualifying_sentences(thoughts: list) -> list:
    """thoughts: [{id, ts, text, kind?}]. Returns [{text, id, ts, kind, sha}] sorted by (ts, id, position), deduplicated by
    normalised sha1 (a copied sentence must not win a medoid vote by repetition, F-4450). Sentence filter: 40-240 chars,
    first person, no speaker-boundary hit."""
    out, seen = [], set()
    for th in sorted(thoughts, key=lambda x: (float(x.get("ts") or 0), str(x.get("id") or x.get("fragment_id") or ""))):
        tid = th.get("id") or th.get("fragment_id")
        for s in split_sentences(th.get("text", "")):
            if not (SENT_MIN <= len(s) <= SENT_MAX) or not _FIRST_PERSON_RE.search(s) or _boundary_hit(s):
                continue
            k = _norm_sha1(s)
            if k in seen:
                continue
            seen.add(k)
            out.append({"text": s, "id": tid, "ts": float(th.get("ts") or 0), "kind": th.get("kind", "fragment"),
                        "sha": k})
    return out


def medoid(vecs) -> tuple:
    """(index, score, scores): score = mean cosine to every OTHER vector; argmax, first index wins ties.
    Vectors are assumed unit-normalised (the embedder normalises)."""
    import numpy as np
    M = np.asarray(vecs, dtype=np.float64)
    n = len(M)
    if n < 2:
        return None, 0.0, []
    sim = M @ M.T
    ms = (sim.sum(1) - np.diag(sim)) / (n - 1)
    i = int(np.argmax(ms))
    return i, float(ms[i]), [float(x) for x in ms]


def pick_medoid(thoughts: list, embed=None) -> dict:
    """Deterministic selection over qualifying sentences. Returns {ok, reason?, sentence?, score, n_sentences, n_thoughts,
    n_days, rank_scores}. No threshold is applied here (the null gate does that)."""
    embed = embed or _embed_batch
    sents = qualifying_sentences(thoughts)
    n_th = len({s["id"] for s in sents})
    n_days = len({time.strftime("%Y-%m-%d", time.localtime(s["ts"])) for s in sents if s["ts"]})
    base = {"n_sentences": len(sents), "n_thoughts": n_th, "n_days": n_days}
    if len(sents) < MIN_SENTENCES or n_th < MIN_THOUGHTS:
        return {"ok": False, "reason": "no_medoid", "score": 0.0, **base}
    vecs = embed([s["text"] for s in sents])
    if vecs is None or any(v is None for v in vecs):
        return {"ok": False, "reason": "embed_unavailable", "score": 0.0, **base}
    i, score, scores = medoid(vecs)
    if i is None:
        return {"ok": False, "reason": "no_medoid", "score": 0.0, **base}
    return {"ok": True, "sentence": sents[i], "score": score, "rank": 0, "scores": scores, **base}


# ---- the coherence null (design 2.4 step 5; scripts/becoming_node_null.py is the CLI over this) ------------------------
def null_windows(per_thought: list, vecs, window: int = NULL_WINDOW, step: int = NULL_STEP) -> list:
    """per_thought: list (one per thought, in order) of lists of sentence indexes into `vecs` + a parallel list of
    normalised-sha1 keys, given as a list of (idx, sha). Returns the medoid score of each consecutive `window`-thought
    window stepping by `step`, deduplicating sentences within a window (same rule as pick_medoid)."""
    idx = [i for i, p in enumerate(per_thought) if p]
    res = []
    for s in range(0, len(idx) - window, step):
        seen, keep = set(), []
        for t in idx[s:s + window]:
            for j, sha in per_thought[t]:
                if sha not in seen:
                    seen.add(sha)
                    keep.append(j)
        if len(keep) >= 2:
            res.append(medoid([vecs[j] for j in keep])[1])
    return res


def compute_null(db_path=None, now: float | None = None, days: int = NULL_DAYS, embed=None) -> dict:
    """The p95 etc. of the medoid statistic over consecutive 15-thought windows of his own last `days` days. Read-only
    (sqlite mode=ro) and embedder-only (no hub). Raises on a missing DB / embedder; the caller fails closed."""
    import numpy as np
    embed = embed or _embed_batch
    if db_path is None:
        from core.memory import store
        db_path = store.DB_PATH
    now = now or time.time()
    con = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True, timeout=15.0)
    try:
        fr = con.execute(
            "SELECT content FROM memory_fragments WHERE origin IN ('inner_thought','subconscious_synthesis') "
            "AND timestamp>? ORDER BY timestamp DESC LIMIT ?", (now - days * 86400, NULL_MAX_THOUGHTS)).fetchall()
    finally:
        con.close()
    th = []
    for (c,) in fr:
        t = " ".join((c or "").split())
        if _LIVED_RE.search(t):
            th.append(t)
    th.reverse()                                   # oldest first: windows are consecutive in time
    allS, per = [], []
    for t in th:
        ss = []
        for s in split_sentences(t):
            if SENT_MIN <= len(s) <= SENT_MAX and _FIRST_PERSON_RE.search(s) and not _boundary_hit(s):
                ss.append((len(allS), _norm_sha1(s)))
                allS.append(s)
        per.append(ss)
    vecs = embed(allS) if allS else []
    if not allS or any(v is None for v in vecs):
        raise RuntimeError("null: no sentences or embedder unavailable")
    res = null_windows(per, vecs)
    if len(res) < 20:
        raise RuntimeError("null: only %d windows" % len(res))
    a = np.array(res)
    p = np.percentile(a, [50, 90, NULL_PCTL, 100])
    return {"p50": float(p[0]), "p90": float(p[1]), "p95": float(p[2]), "max": float(p[3]), "n_windows": len(res),
            "n_thoughts": len(th), "n_sentences": len(allS), "days": days, "computed_ts": round(now, 3)}


def get_null(db_path=None, now: float | None = None, embed=None) -> dict:
    """Cached for NULL_TTL_S. Returns the compute_null dict or raises."""
    now = now or time.time()
    c = _null_cache.get("v")
    if c and now - c["computed_ts"] < NULL_TTL_S and not db_path:
        return c
    v = compute_null(db_path=db_path, now=now, embed=embed)
    if not db_path:
        _null_cache["v"] = v
    return v


# ---- ledger ------------------------------------------------------------------------------------------------------
def make_id(source: str, candidate_key: str, text: str) -> str:
    return ID_PREFIX + _sha1(f"{source}|{candidate_key}|{_sha1(text)}")[:12]


def read_ledger(path=None) -> list:
    p = Path(path or LEDGER_F)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        f.flush()


def candidate_key_for(source: str, candidate: dict) -> str:
    if source == "t4_chain":
        return f"{float(candidate.get('started_ts', 0) or 0):.0f}|{candidate.get('theme', '')}"
    return str(candidate.get("candidate_id") or candidate.get("key") or "")


# ---- the writer --------------------------------------------------------------------------------------------------
def admit(source: str, candidate: dict, evidence: list, gates: dict | None = None, *, embed=None,
          null: dict | None = None) -> dict:
    """Judge the evidence, and (per the flags) log / write one becoming_symbol node. Returns a status dict, never a hard
    failure except profile.NonLiveWriteError (the fence, D-0179). ENABLED False: returns immediately, no I/O at all.
    `null` (tests / the null script) overrides the computed null: {"p95": float, ...}."""
    if not BECOMING_NODES_ENABLED:
        return {"status": "disabled"}
    # FENCE (D-0179): resolve BEFORE the swallow-all try so a non-live process raises and writes nothing.
    shadow_path = profile.guard_path(SHADOW_F)
    ledger_path = profile.guard_path(LEDGER_F) if BECOMING_NODES_WRITE else None
    gates = gates or {}
    ts = round(time.time(), 3)
    ckey = candidate_key_for(source, candidate)
    flag_state = {"write": bool(BECOMING_NODES_WRITE), "seed": bool(BECOMING_NODES_SEED),
                  "project": bool(BECOMING_PROJECT)}
    row = {"event": "shadow", "ts": ts, "source": source, "candidate_key": ckey, "flag_state": flag_state}
    try:
        thoughts = [{"id": e.get("id") or e.get("fragment_id"), "ts": e.get("ts"), "text": e.get("text", ""),
                     "kind": e.get("kind", "fragment")} for e in (evidence or [])]
        pick = pick_medoid(thoughts, embed=embed)
        coh = {k: pick.get(k) for k in ("n_sentences", "n_thoughts", "n_days")}
        if not pick["ok"]:
            row.update(status=pick["reason"], coherence={**coh, "medoid_score": pick["score"], "null_p95": None})
            _append(shadow_path, row)
            return {"status": pick["reason"], "row": row}
        try:
            nl = null if null is not None else get_null(embed=embed)
            p95 = float(nl["p95"])
        except Exception as exc:
            row.update(status="no_null", error=str(exc)[:200],
                       coherence={**coh, "medoid_score": pick["score"], "null_p95": None})
            _append(shadow_path, row)
            return {"status": "no_null", "row": row}
        sent = pick["sentence"]
        text = sent["text"]
        coh.update(medoid_score=round(pick["score"], 4), null_p95=round(p95, 4),
                   null_n_windows=nl.get("n_windows"), negation_flag=bool(_NEGATION_RE.search(text)))
        if not pick["score"] > p95:
            row.update(status="below_null", coherence=coh,
                       text_ref={"kind": sent["kind"], "id": sent["id"], "mean_cos": round(pick["score"], 4), "rank": 0})
            _append(shadow_path, row)
            return {"status": "below_null", "row": row}
        nid = make_id(source, ckey, text)
        admit_row = {
            "event": "admit", "ts": ts, "id": nid, "type": TYPE, "text": text,
            "text_ref": {"kind": sent["kind"], "id": sent["id"], "mean_cos": round(pick["score"], 4), "rank": 0},
            "source": source, "candidate_key": ckey, "theme_hash": _sha1(str(candidate.get("theme", "")))[:12],
            "authored_sha1": _sha1(candidate["self_image"]) if source == "t4_chain" and candidate.get("self_image") else None,
            "origin_evidence": [{"kind": "light_event", "id": e.get("id"), "ts": e.get("ts"),
                                 "content_sha1": _norm_sha1(e.get("text", ""))}
                                for e in thoughts if e["kind"] == "light_event"],
            "uptake_evidence": [{"kind": "fragment", "id": e["id"], "ts": e.get("ts"),
                                 "content_sha1": _norm_sha1(e.get("text", "")), "unprimed": True}
                                for e in thoughts if e["kind"] != "light_event"],
            "coherence": coh, "gates": gates, "weight0": WEIGHT0, "flag_state": flag_state}
        # idempotency / collision (reads the ledger even in shadow mode, so the would-be status is honest)
        existing = read_ledger(ledger_path or LEDGER_F)
        same = [r for r in existing if r.get("event") == "admit" and r.get("id") == nid]
        if same:
            if (same[0].get("text") == text and same[0].get("source") == source
                    and same[0].get("candidate_key") == ckey):
                row.update(status="noop_idempotent", id=nid, coherence=coh)
                _append(shadow_path, row)
                return {"status": "noop_idempotent", "id": nid, "row": row}
            row.update(status="refused_collision", id=nid, coherence=coh)
            logger.warning("[becoming_nodes] id collision %s refused", nid)
            _append(shadow_path, row)
            return {"status": "refused_collision", "id": nid, "row": row}
        if any(r.get("event") == "admit" and r.get("candidate_key") == ckey and r.get("source") == source
               for r in existing):
            row.update(status="candidate_already_admitted", id=nid, coherence=coh)
            _append(shadow_path, row)
            return {"status": "candidate_already_admitted", "id": nid, "row": row}
        status = "admitted" if BECOMING_NODES_WRITE else "would_admit"
        row.update(status=status, id=nid, would_be_row=admit_row, coherence=coh)
        with _write_lock:
            _append(shadow_path, row)
            if BECOMING_NODES_WRITE:
                _append(ledger_path, admit_row)
        return {"status": status, "id": nid, "row": admit_row}
    except Exception as exc:                      # fail-open: the caller is a cognitive node
        logger.debug("[becoming_nodes] admit failed (non-fatal): %s", exc)
        return {"status": "error", "error": str(exc)[:200]}


def admit_offloop(source: str, candidate: dict, evidence: list, gates: dict | None = None) -> bool:
    """Single-flight daemon worker (the sync_offloop pattern): a call that arrives while one is running is dropped and
    logged. Returns True iff a worker was started. Never raises."""
    if not BECOMING_NODES_ENABLED:
        return False
    try:
        if not _bg_lock.acquire(blocking=False):
            logger.info("[becoming_nodes] admit dropped: a previous admission is still running")
            return False

        def _run():
            try:
                admit(source, candidate, evidence, gates)
            except Exception as exc:              # incl. NonLiveWriteError in a non-live process
                logger.debug("[becoming_nodes] worker: %s", exc)
            finally:
                _bg_lock.release()
        threading.Thread(target=_run, name="becoming-admit", daemon=True).start()
        return True
    except Exception as exc:
        logger.debug("[becoming_nodes] admit_offloop failed (non-fatal): %s", exc)
        return False


def on_chain_resolved(prov: dict | None, dec: dict | None, lived_refs: list | None) -> bool:
    """Hook A (nodes/subconscious_node.py, after 'T4 probation RESOLVED'). No-op unless ENABLED and the decision was
    solidify. lived_refs = [{fragment_id, ts, text}] stashed by _judge_lived_integration (the exact thoughts the judges
    read). Never raises."""
    try:
        if not BECOMING_NODES_ENABLED or not prov or not dec or dec.get("decision") != "solidify":
            return False
        ev = [{"id": r.get("fragment_id"), "ts": r.get("ts"), "text": r.get("text", ""), "kind": "fragment"}
              for r in (lived_refs or [])]
        gates = {"solidify": {"integration": dec.get("integration"), "dF": dec.get("dF")}}
        return admit_offloop("t4_chain", dict(prov), ev, gates)
    except Exception:
        return False
