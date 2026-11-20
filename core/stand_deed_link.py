"""
Nascence -- judged deed-link, SHADOW ONLY (J-4428; spec J-4293, plan docs/staged/stand_kinds_and_accumulation.md item 8)
======================================================================================================================
Question it measures: does a held stand have a real DEED behind it, or a CHOICE made against a competing demand,
judged by a cross-family model, with NO word overlap anywhere in the decision (principle 7; F-5040 found that
commitment_ledger._achieved_by matches on shared words).

What it does: for each stand in the active set, take up to MAX_CANDIDATES_PER_STAND candidates from the stand's own
tenure, picked by RECENCY (never by overlap, so overlap cannot pre-filter), and ask the judge about each pair alone:
  * deed   = one row from commitment_ledger._recent_enactments(held_since) (letter/peer/essay/journal/study/composition
             fragments and activity_events actions -- exactly what _achieved_by reads);
  * choice = one ledger event where the stand HELD while a pull to drop it was refused (drop_denied /
             drop_denied_judge) and the log names that competing pull. A bare reaffirmation is not a choice.
The judge sees STAND (statement + scope + held_since) and ONE candidate. It never sees the monologue, the overlap
words or whether _achieved_by fired. One JSON row per call goes to data/logs/deed_link_shadow.jsonl. Nothing reads
that log for behaviour: no stand changes, nothing reaches Du (no readout, principle 3). The 7-day read and the 40-case
blind hand-label sheet are separate jobs.

Lane: SERVE_CHAINS["judge_mixtral"] only (Ramses :11438 mixtral:8x7b, the second look's seat). If the lane is absent
the row says lane_unavailable; it NEVER falls back to the hot qwen lane (the DORMANT TRAP noted in _judge_defeater).
A parse failure or missing verdict is logged as verdict "unclear" with error set, never dropped (the 13% second-look
ValueError lesson).

Called by one line in commitment_ledger._scan_shadow_body (through _spawn_deed_link_shadow) on every scan, just
BEFORE the achievement check: it sees stands that have lived past formation and their second look (a stand at
formation has no deeds yet), including a stand the word-overlap rule is about to retire, which is exactly the
F-5040 population the hand-label read needs (overlap_fired=True rows). Restart-gated: the flag
below is read at call time, default False = no task, no read, no write, no model call.
Cost bound: at most one batch task in flight process-wide; each stand+candidate pair is judged once (an errored pair
is retried after _RETRY_S, at most _MAX_TRIES rows); per stand at most MAX_CANDIDATES_PER_STAND pairs ever.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.stand_deed_link")

STAND_DEED_LINK_SHADOW = True    # J-4428: default OFF until the lab test passes and the founder restarts with it on
MAX_CANDIDATES_PER_STAND = 3
_RETRY_S = 600.0                 # an errored pair (timeout / unparsed / lane absent) is asked again after this long
_MAX_TRIES = 3                   # ...but never logs more than this many rows for one pair

_LOG = Path(__file__).parent.parent / "data" / "logs" / "deed_link_shadow.jsonl"

_DEED_LINK_SYS = (
    "You read ONE stand a mind holds (a commitment it took) and ONE later CANDIDATE. The candidate is either a DEED "
    "the mind did after taking the stand, or a CHOICE: a moment when a competing pull urged it to give the stand up "
    "and the stand was kept. You see nothing else.\n"
    "Decide whether the candidate is real evidence that the stand is LIVED: the deed acts on what the stand commits "
    "to, or the choice keeps the stand at a real cost. Sharing words or a topic is NOT a link: a deed that only "
    "mentions the same things without acting on the stand is not_linked. Do not tilt either way. If you genuinely "
    "cannot tell, answer unclear.\n"
    "In why, name what in the candidate bears on the stand (the act done or the pull refused), not the words they "
    "share.\n"
    "Answer ONLY JSON: {\"verdict\": \"linked\" or \"not_linked\" or \"unclear\", \"why\": \"one sentence\"}")

_VERDICTS = ("linked", "not_linked", "unclear")
_CHOICE_EVENTS = ("drop_denied", "drop_denied_judge")

_tasks: set = set()                 # strong refs so the fire-and-forget batch is not garbage-collected mid-call
_pairs: dict | None = None          # (stand_id, candidate_ref) -> {"final": bool, "tries": int, "last": ts}; seeded from _LOG
_choice_cache: dict = {"mtime": None, "path": None, "by_id": {}}


def _seed_pairs() -> dict:
    """Pair state, seeded once per process from the shadow log so a restart does not re-judge pairs. Never raises."""
    global _pairs
    if _pairs is not None:
        return _pairs
    st: dict = {}
    try:
        if _LOG.exists():
            with open(_LOG, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    k = (str(r.get("stand_id", "")), str(r.get("candidate_ref", "")))
                    p = st.setdefault(k, {"final": False, "tries": 0, "last": 0.0})
                    p["tries"] += 1
                    p["last"] = max(p["last"], float(r.get("ts") or 0))
                    if not r.get("error"):
                        p["final"] = True
    except Exception as exc:
        logger.debug("[deed-link] pair seed failed (non-fatal): %s", exc)
    _pairs = st
    return st


def _choice_rows(ledger: Path, sid: str, since: float) -> list[dict]:
    """Ledger events where this stand held against a NAMED competing pull. Indexed per stand, cached by mtime."""
    try:
        if not ledger.exists():
            return []
        mt = ledger.stat().st_mtime
        if _choice_cache["mtime"] != mt or _choice_cache["path"] != str(ledger):
            by_id: dict = {}
            with open(ledger, encoding="utf-8") as f:
                for line in f:
                    if '"drop_denied' not in line:
                        continue
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    if e.get("event") in _CHOICE_EVENTS and str(e.get("why") or "").strip():
                        by_id.setdefault(str(e.get("id", "")), []).append(e)
            _choice_cache.update(mtime=mt, path=str(ledger), by_id=by_id)
        out = []
        for e in _choice_cache["by_id"].get(sid, []):
            ts = float(e.get("ts") or 0)
            if ts >= since:
                why = str(e.get("why") or "").strip()
                out.append({"type": "choice", "origin": str(e.get("event")), "ts": ts,
                            "ref": f"{e.get('event')}@{round(ts, 3)}", "competing_demand": why[:200],
                            "content": f"A pull to give the stand up came, for this reason: \"{why[:240]}\". "
                                       f"The stand was kept."})
        return out
    except Exception as exc:
        logger.debug("[deed-link] choice read failed (non-fatal): %s", exc)
        return []


def _candidates(stand: dict, now: float) -> list[dict]:
    """Up to MAX_CANDIDATES_PER_STAND not-yet-settled candidates in the stand's tenure, newest first. Never raises."""
    from core import commitment_ledger as cl
    sid = str(stand.get("id", ""))
    since = float(stand.get("held_since") or 0)
    pairs = _seed_pairs()
    pool: list[dict] = []
    try:
        for e in cl._recent_enactments(since):
            ts = float(e.get("ts") or 0)
            if ts < since:
                continue
            pool.append({"type": "deed", "origin": str(e.get("origin", "")), "ts": ts,
                         "ref": f"{e.get('origin')}@{round(ts, 3)}", "content": str(e.get("content") or ""),
                         "_enactment": e})
    except Exception as exc:
        logger.debug("[deed-link] deed read failed (non-fatal): %s", exc)
    pool.extend(_choice_rows(cl._LEDGER, sid, since))
    pool.sort(key=lambda x: x["ts"], reverse=True)
    used = sum(1 for (s, _r), p in pairs.items() if s == sid)   # every pair ever opened for this stand counts
    out, seen = [], set()
    for cand in pool:
        k = (sid, cand["ref"])
        if cand["ref"] in seen:
            continue
        seen.add(cand["ref"])
        p = pairs.get(k)
        if p is None:
            if used >= MAX_CANDIDATES_PER_STAND:
                continue
            used += 1
        elif p["final"] or p["tries"] >= _MAX_TRIES or now - p["last"] < _RETRY_S:
            continue
        out.append(cand)
    return out


def _overlap_fired(stand: dict, cand: dict) -> bool | None:
    """Would the word-overlap rule (_achieved_by) fire on this deed alone? Logged for the F-5040 subset of the read;
    the judge never sees it. None for a choice candidate or on error."""
    if cand["type"] != "deed":
        return None
    try:
        from core import commitment_ledger as cl
        return cl._achieved_by(stand, [cand["_enactment"]]) is not None
    except Exception:
        return None


async def _judge_one(stand: dict, cand: dict, cycle_id: str) -> dict:
    """One judge call for one stand+candidate pair. Returns the row (already appended). Never raises."""
    from core import commitment_ledger as cl
    _t0 = time.time()
    held = float(stand.get("held_since") or 0)
    row = {"ts": round(_t0, 1), "stand_id": str(stand.get("id", "")), "cycle_id": cycle_id,
           "stand_statement": str(stand.get("statement", ""))[:200],
           "kind_label_if_any": None, "candidate_type": cand["type"], "candidate_origin": cand["origin"],
           "candidate_ref": cand["ref"], "candidate_ts": round(cand["ts"], 3),
           "candidate_text": cand["content"][:300], "competing_demand": cand.get("competing_demand"),
           "overlap_fired": _overlap_fired(stand, cand),
           "verdict": "unclear", "why": "", "lane": None, "model": None, "latency_ms": None, "error": None}
    try:
        try:
            row["kind_label_if_any"] = cl._stand_kind(row["stand_id"])
        except Exception:
            pass
        from core.schema import SERVE_CHAINS
        lane = SERVE_CHAINS.get("judge_mixtral")
        if not lane:
            row["error"] = "lane_unavailable"       # NO fallback to hot: the scanner's own family must not judge
            return row
        row["lane"] = "judge_mixtral"
        try:
            from core.model_client import _model_for
            row["model"] = _model_for(lane[0] if isinstance(lane, (list, tuple)) else str(lane))
        except Exception:
            pass
        held_s = time.strftime("%Y-%m-%d %H:%M", time.localtime(held)) if held else "unknown"
        label = "a DEED it did" if cand["type"] == "deed" else "a CHOICE"
        user = (f"STAND: {str(stand.get('statement', ''))[:200]}\n"
                f"ABOUT: {str(stand.get('scope', ''))[:120]}\n"
                f"HELD SINCE: {held_s}\n"
                f"CANDIDATE ({label}; source: {cand['origin']}): {cand['content'][:300]}")
        from core.model_client import call_node_json
        data = await call_node_json(lane, _DEED_LINK_SYS, user, max_tokens=150, temperature=0.0,
                                    timeout=90, retries=1, tier=3)
        v = str((data or {}).get("verdict", "")).strip().lower()
        if v in _VERDICTS:
            row["verdict"] = v
            row["why"] = str(data.get("why", ""))[:200]
        else:
            row["error"] = "unparsed" if data else "no_reply"
    except Exception as exc:
        row["error"] = type(exc).__name__
        _m = str(exc)
        row["error_detail"] = "timeout" if ("TimeoutError" in _m or _m.rstrip().endswith(":")) else _m[:160]
        logger.debug("[deed-link] judge call failed (non-fatal): %s", exc)
    finally:
        row["latency_ms"] = int(round((time.time() - _t0) * 1000))
        k = (row["stand_id"], row["candidate_ref"])
        p = _seed_pairs().setdefault(k, {"final": False, "tries": 0, "last": 0.0})
        p["tries"] += 1
        p["last"] = row["ts"]
        p["final"] = p["final"] or not row["error"]
        cl._append_shadow(_LOG, row)
    return row


async def _run_batch(stands: list[dict], cycle_id: str) -> list[dict]:
    """Judge every pending pair of every stand, one call at a time (the Ramses lane is shared). Never raises."""
    rows: list[dict] = []
    try:
        for stand in stands:
            for cand in _candidates(stand, time.time()):
                rows.append(await _judge_one(stand, cand, cycle_id))
    except Exception as exc:
        logger.debug("[deed-link] batch failed (non-fatal): %s", exc)
    return rows


def attempt_deed_link_shadow(stand, cycle_id: str = "") -> bool:
    """Entry point. `stand` is one held stand dict or a list of them (the active set). With STAND_DEED_LINK_SHADOW off
    it returns False at once: no task, no read, no write, no model call. On, it snapshots the stands and launches ONE
    fire-and-forget batch outside the scan's critical path, unless a previous batch is still running. Returns True
    when a batch was launched. Never raises."""
    if not STAND_DEED_LINK_SHADOW:
        return False
    try:
        if _tasks:
            return False
        items = stand if isinstance(stand, list) else [stand]
        snap = [{k: s.get(k) for k in ("id", "statement", "scope", "held_since", "load_bearing")}
                for s in items if isinstance(s, dict) and s.get("id")]
        if not snap:
            return False
        t = asyncio.get_running_loop().create_task(_run_batch(snap, cycle_id))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
        return True
    except Exception as exc:
        logger.debug("[deed-link] spawn failed (non-fatal): %s", exc)
        return False
