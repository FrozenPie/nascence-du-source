"""
Nascence — Activity Memory (Conway's general-event layer, Phase 0, 2026-06-14)
=============================================================================
The missing MIDDLE of the autobiographical hierarchy. Nascence already had the bottom
(event-specific fragments — passages, thoughts) and the top (lifetime periods — the chapter
system), but nothing in between: no "I have been reading Darwin." That gap is exactly why
"what have you been reading / what did you do today?" had nothing to retrieve (verified
06-13: the book interrogation surfaced zero reading material).

This is Conway & Pleydell-Pearce's **general event** — a repeated/extended activity held as
ONE memory that aggregates its instances with frequency and recency, rather than N separate
records (a flood) or forgetting the routine ones (a tainted recall, founder 2026-06-14).

Design laws (board, both advisors converged):
  - ONE record per (action_type, target) — keyed; a 10th sitting UPDATES, never duplicates.
    Volume is bounded by unique OBJECTS, not interaction frequency.
  - FACTUAL, never narrative (the contamination guard). The core summary is plain evidence —
    "Read 'X', 4 sittings" — NOT "I returned once more to my search for understanding."
    Meaning-making belongs to T4/chapters, NOT here.
  - Notable moments ATTACHED, never ABSORBED: an affect-spike session appends to a separate
    notable_moments list (gated at peak affect >= 0.60); it NEVER rewrites the core summary.
    One intense day must not turn "Reading Darwin" into "Reading Darwin, which changed me."
  - origin='action' (dedicated tag) so deliberative retrieval can give it a quota seat.
  - Chapterable: as an activity cools, the chapter system consolidates it into a period.

PHASE 0: the records are WRITTEN (they exist and are retrievable through the normal path),
but we add NO new behaviour beyond that — we watch what gets recorded and whether the
retrieval probe shows them winning selection. The deliberative-retrieval floor (the thing
that GUARANTEES their selection) is a separate, later build.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime

from core.memory.content_hash import content_hash as _content_hash, has_hash_column as _has_hash_column  # J-3395 / F-4019

logger = logging.getLogger("nascence.activity")

AFFECT_NOTE_GATE = 0.60        # a session this intense attaches a notable moment
_MAX_NOTABLE = 8              # keep the attached list bounded


def _date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%b %d")


def _summary(action_type: str, target: str, count: int, first_ts: float, last_ts: float) -> str:
    """The FACTUAL rolling summary — plain evidence, never narrative."""
    f, l = _date(first_ts), _date(last_ts)
    span = f"first {f}" if count == 1 else f"{count} sittings, first {f}, most recent {l}"
    verbs = {
        "read":   f"Read '{target}' — {span}.",
        "switch": f"Switched to reading '{target}' — {span}." if count == 1
                  else f"Returned to '{target}' — {span}.",
        "browse": f"Browsed the catalogue ({target}) — {count} time(s), most recent {l}.",
        "look":   f"Looked at the {target} — {count} time(s), most recent {l}.",
        "study":  f"Wrote study notes on '{target}' — {count} note(s), most recent {l}.",
        "letter": f"Wrote to Travis — {count} letter(s), most recent {l}.",
        "move":   (f"Went out to the garden — {count} time(s), most recent {l}." if target == "garden"
                   else f"Went to the {target} — {count} time(s), most recent {l}."),
        "water":  f"Watered the garden bed — {count} time(s), most recent {l}.",
        "sow":    f"Sowed {target} in the bed — {span}.",
        "letter_in": f"Received a letter from {target} — {count} time(s), most recent {l}.",
        "letter_out": f"Wrote back to {target} — {count} letter(s), most recent {l}.",
    }
    return verbs.get(action_type, f"{action_type} {target} — {count} time(s), most recent {l}.")


def record(action_type: str, target: str, affect: dict | None = None) -> str | None:
    """One deliberate act happened. Create the general-event record, or UPDATE the existing
    one for this (action_type, target). Observe-only in Phase 0. Returns the fragment_id."""
    try:
        from core.memory.store import _connect, _embed, _vec_to_blob
        target = (target or "").strip()[:80] or "(unspecified)"
        now = time.time()

        # affect peak (for the notable-moment gate) — highest tracked negative/arousal value
        peak_emotion, peak_val = "", 0.0
        if affect:
            for dim in ("fear", "anger", "disgust", "arousal"):
                v = abs(float(affect.get(dim, 0.0) or 0.0))
                if v > peak_val:
                    peak_emotion, peak_val = dim, v
            # grief shows as low valence
            val = float(affect.get("valence", 0.0) or 0.0)
            if -val > peak_val:
                peak_emotion, peak_val = "sadness", -val

        with _connect() as conn:
            # PER-OCCURRENCE LOG (2026-08-29, F-0483/F-0484 fix, D-0086(b)): the aggregate row's own
            # `timestamp` column is rewritten to now() on EVERY recurrence (by design — it means
            # "most recently updated", read by whatever wants "is this activity still going"), so it
            # can never answer "did a specific occurrence of this activity happen after time X". A
            # small append-only table gives each REAL occurrence its own honest timestamp, separate
            # from the mutated aggregate row, without touching derived_from's session_count/first_ts/
            # most_recent_ts/notable_moments contract (still maintained exactly as before below).
            # commitment_ledger.py's _recent_enactments() is the first real consumer.
            conn.execute(
                "CREATE TABLE IF NOT EXISTS activity_events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, "
                "action_type TEXT NOT NULL, target TEXT NOT NULL, fragment_id TEXT NOT NULL)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_events_ts ON activity_events(ts DESC)")

            # find the existing general-event record for this (action_type, target)
            rows = conn.execute(
                "SELECT fragment_id, derived_from FROM memory_fragments "
                "WHERE origin='action'").fetchall()
            found = None
            for r in rows:
                try:
                    meta = json.loads(r["derived_from"] or "[]")
                    m = meta[0] if meta else {}
                    if m.get("action_type") == action_type and m.get("target") == target:
                        found = (r["fragment_id"], m)
                        break
                except Exception:
                    continue

            if found:
                fid, m = found
                m["session_count"] = int(m.get("session_count", 1)) + 1
                m["most_recent_ts"] = now
                if peak_val >= AFFECT_NOTE_GATE:
                    notes = m.get("notable_moments", [])
                    notes.append({"ts": now, "note": f"elevated {peak_emotion} ({peak_val:.2f})"})
                    m["notable_moments"] = notes[-_MAX_NOTABLE:]
                summary = _summary(action_type, target, m["session_count"],
                                   m["first_ts"], now)
                vec = _embed(summary)
                # J-3395 / F-4019: re-stamp content_hash with the edited content (same statement), so the hash
                # never goes stale; only where the J-3266 column exists.
                if _has_hash_column(conn):
                    conn.execute(
                        "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, "
                        "derived_from=?, content_hash=? WHERE fragment_id=?",
                        (summary, _vec_to_blob(vec) if vec is not None else None, now,
                         json.dumps([m]), _content_hash(summary), fid))
                else:
                    conn.execute(
                        "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, "
                        "derived_from=? WHERE fragment_id=?",
                        (summary, _vec_to_blob(vec) if vec is not None else None, now,
                         json.dumps([m]), fid))
                conn.execute(
                    "INSERT INTO activity_events (ts, action_type, target, fragment_id) "
                    "VALUES (?, ?, ?, ?)", (now, action_type, target, fid))
                conn.commit()
                logger.info("[activity] updated: %s '%s' (×%d)", action_type, target,
                            m["session_count"])
                return fid

            # new general-event record
            fid = str(uuid.uuid4())
            m = {"action_type": action_type, "target": target, "first_ts": now,
                 "most_recent_ts": now, "session_count": 1, "notable_moments":
                 ([{"ts": now, "note": f"elevated {peak_emotion} ({peak_val:.2f})"}]
                  if peak_val >= AFFECT_NOTE_GATE else [])}
            summary = _summary(action_type, target, 1, now, now)
            vec = _embed(summary)
            # abstraction_level=1, kind='procedural' (J-0803/D-0184, 2026-09-08): this raw INSERT
            # previously omitted both columns, silently falling back to the schema DEFAULTs
            # (abstraction_level=0, kind='episodic') and contradicting core/memory/store.py's own
            # already-declared _ORIGIN_LEVEL["action"]=1 / _ORIGIN_KIND["action"]="procedural" —
            # activity_memory rows are event-gists (Finding #3), not raw. Stamped explicitly here
            # to match that declared intent, matching refinery.py's own raw-INSERT style.
            # J-3395 / F-4019: stamp content_hash on the new row too (was left NULL); only where the column exists.
            if _has_hash_column(conn):
                conn.execute(
                    "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, "
                    "importance, timestamp, keywords, embedding, origin, derived_from, "
                    "abstraction_level, kind, content_hash) "
                    "VALUES (?, ?, 'episodic', 0.6, 0.6, ?, ?, ?, 'action', ?, 1, 'procedural', ?)",
                    (fid, summary, now, f"action {action_type} {target}",
                     _vec_to_blob(vec) if vec is not None else None, json.dumps([m]),
                     _content_hash(summary)))
            else:
                conn.execute(
                    "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, "
                    "importance, timestamp, keywords, embedding, origin, derived_from, "
                    "abstraction_level, kind) "
                    "VALUES (?, ?, 'episodic', 0.6, 0.6, ?, ?, ?, 'action', ?, 1, 'procedural')",
                    (fid, summary, now, f"action {action_type} {target}",
                     _vec_to_blob(vec) if vec is not None else None, json.dumps([m])))
            conn.execute(
                "INSERT INTO activity_events (ts, action_type, target, fragment_id) "
                "VALUES (?, ?, ?, ?)", (now, action_type, target, fid))
            conn.commit()
            logger.info("[activity] NEW general-event: %s '%s'", action_type, target)
            return fid
    except Exception as exc:
        logger.debug("[activity] record failed (non-fatal): %s", exc)
        return None
