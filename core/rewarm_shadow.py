"""
Nascence -- Recall-induced re-warming, SHADOW ONLY (J-4420, plan memory_review_adoption section 6, M4b).

WHY. A cold or chaptered row is excluded from retrieve(); the only way back is the associative trail, on a
strong hop (core/associative_recall.py COLD_THRESHOLD). Recalling it does not re-warm it (F-5122). The first
level chosen under the founder's delegation (plan section 6.1, written by Claude, not a founder ruling) is
partial and temporary: when the trail SERVES a walled row and that row is then USED in the next output,
the row would be warm for 7 days (the scale of the trail's 7-day recency bump), then return to cold unless
recalled again. This module only LOGS that would-warm. It applies nothing: no cold=0 write, no chapter
change, no matrix change, nothing returned to any caller.

HOW.
  note_surfaced(entries, source)  -- called from associative_recall.recall_memory_fragments (the live cycle
      augmentation) and recall_fragments (the loops' recall), with the trail entries actually SERVED. Walled
      entries are kept in a small pending set (fragment_id, origin, trail activation, content).
  note_output(text, source)       -- called once the next output exists: the idle thought (inner monologue
      completion point) and the voice reply (VoiceNode._write_output). Pending entries are consumed and
      labelled in a daemon thread (the cycle never waits), with BOTH F-4273 labels:
        u4  -- the fragment and the output share a word 4-gram (J-3311 baseline label, same tokeniser);
        ue  -- max cosine over (fragment sentence x output sentence) >= 0.7038, the pre-registered J-3311
               threshold, in the same paraphrase-multilingual-MiniLM-L12-v2 space (store._embed_batch).
      Either label -> one "would_warm" row. Every labelling pass with any walled entry also writes one
      "scored" row (n walled, n used) so the daily volume has a denominator.

LOG. data/rewarm_shadow.jsonl, rows:
  {kind:"would_warm", ts, fragment_id, origin, trail_activation, used_label: "4gram"|"emb"|"both",
   emb_max_cos, would_warm_until (= ts + 7 d), surfaced_source, output_source, mode:"shadow"}
  {kind:"scored", ts, output_source, n_walled, n_used}
  Daily volume: scripts/rewarm_shadow_report.py (or daily_counts() below).

CONTRACT. Feeds nothing Du experiences (D-0434). Never raises into a caller; fail-open, debug log only.
Fenced with profile.guard_path (D-0179) and rebased for a named profile (core.profile). Restart-gated.
KILL SWITCH: REWARM_SHADOW_ON = False. MODE is "shadow" and there is no live mode: promotion needs a
separate ruling after this log and the cold-trail ablation (J-4414) are read.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.rewarm_shadow")

REWARM_SHADOW_ON = True
MODE = "shadow"                 # the only mode; nothing is ever applied

_LOG = Path(__file__).parent.parent / "data" / "rewarm_shadow.jsonl"

WARM_DAYS = 7.0                 # would-warm window (plan 6.1: the 7-day recency-bump scale)
T_EMB = 0.7038                  # F-4273 / J-3311 pre-registered embedding threshold (99th pct of the null)
PENDING_TTL_S = 1800.0          # a served row not followed by any output within 30 min is dropped unscored
MAX_PENDING = 60                # bound on the pending set
FRAG_SENT_CAP = 12              # J-3311 fragment_chunks cap
CHUNK_CHARS = 400               # J-3311 sentence cut

_WORD = re.compile(r"[a-z0-9']+")
_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")

_lock = threading.Lock()
_pending: dict[str, dict] = {}


# ----------------------------------------------------------------------------- J-3311 text helpers
def _words(t) -> list:
    return _WORD.findall((t or "").lower())


def _grams4(t) -> set:
    w = _words(t)
    return {tuple(w[i:i + 4]) for i in range(len(w) - 3)}


def _sentences(t, cap=None) -> list:
    out = [s.strip()[:CHUNK_CHARS] for s in _SPLIT.split(t or "") if len(_words(s)) >= 4]
    return out[:cap] if cap else out


def _fragment_chunks(t) -> list:
    s = _sentences(t, FRAG_SENT_CAP)
    if s:
        return s
    t = (t or "").strip()
    return [t[:CHUNK_CHARS]] if t else []


def _output_chunks(t) -> list:
    s = _sentences(t)
    if s:
        return s
    t = (t or "").strip()
    return [t[:CHUNK_CHARS]] if t else []


# ----------------------------------------------------------------------------- surfacing side
def note_surfaced(entries, source: str) -> None:
    """Remember the WALLED (cold or chaptered) rows among `entries` that a trail just served.
    `entries`: iterable of dicts with fragment_id, walled, origin, activation, content. Never raises."""
    try:
        if not REWARM_SHADOW_ON or not entries:
            return
        now = time.time()
        with _lock:
            for e in entries:
                if not isinstance(e, dict) or not e.get("walled"):
                    continue
                fid = e.get("fragment_id")
                content = e.get("content") or ""
                if not fid or not str(content).strip():
                    continue
                _pending[str(fid)] = {
                    "fragment_id": str(fid),
                    "origin": e.get("origin"),
                    "trail_activation": e.get("activation"),
                    "content": str(content),
                    "surfaced_ts": now,
                    "surfaced_source": source,
                }
            if len(_pending) > MAX_PENDING:
                for k in sorted(_pending, key=lambda k: _pending[k]["surfaced_ts"])[:len(_pending) - MAX_PENDING]:
                    _pending.pop(k, None)
    except Exception as exc:
        logger.debug("[rewarm] note_surfaced skipped: %s", exc)


def _take_pending(now: float) -> list:
    with _lock:
        items = [p for p in _pending.values() if now - p["surfaced_ts"] <= PENDING_TTL_S]
        _pending.clear()
    return items


# ----------------------------------------------------------------------------- labelling side
def _emb_max_cos(frag_text: str, out_vecs, embed_batch):
    """Max cosine over fragment sentences x output sentences (normalised vectors -> dot). None if unscorable."""
    import numpy as np
    chunks = _fragment_chunks(frag_text)
    if not chunks or out_vecs is None:
        return None
    fv = [v for v in embed_batch(chunks) if v is not None]
    if not fv:
        return None
    F = np.vstack([np.asarray(v, dtype=np.float32) for v in fv])
    return float(np.max(F @ out_vecs.T))


def label_and_log(items: list, text: str, output_source: str, embed_batch=None, log_path: Path | None = None,
                  now: float | None = None) -> list:
    """Label each pending item against `text` and append rows. Returns the would_warm rows written.
    `embed_batch` and `log_path` are injectable for tests; the defaults are store._embed_batch and the
    guard_path-fenced _LOG. Never raises."""
    rows: list = []
    try:
        if not items or not (text or "").strip():
            return rows
        now = time.time() if now is None else now
        if embed_batch is None:
            from core.memory.store import _embed_batch as embed_batch
        out_vecs = None
        try:
            import numpy as np
            ov = [v for v in embed_batch(_output_chunks(text)) if v is not None]
            if ov:
                out_vecs = np.vstack([np.asarray(v, dtype=np.float32) for v in ov])
        except Exception as exc:
            logger.debug("[rewarm] output embed failed (4-gram label only): %s", exc)
        g_out = _grams4(text)
        for it in items:
            u4 = bool(_grams4(it["content"]) & g_out)
            cos = None
            try:
                cos = _emb_max_cos(it["content"], out_vecs, embed_batch)
            except Exception as exc:
                logger.debug("[rewarm] fragment embed failed: %s", exc)
            ue = cos is not None and cos >= T_EMB
            if not (u4 or ue):
                continue
            rows.append({
                "kind": "would_warm",
                "ts": round(now, 3),
                "fragment_id": it["fragment_id"],
                "origin": it.get("origin"),
                "trail_activation": it.get("trail_activation"),
                "used_label": "both" if (u4 and ue) else ("4gram" if u4 else "emb"),
                "emb_max_cos": round(cos, 4) if cos is not None else None,
                "would_warm_until": round(now + WARM_DAYS * 86400.0, 3),
                "surfaced_source": it.get("surfaced_source"),
                "output_source": output_source,
                "mode": MODE,
            })
        if log_path is None:
            from core import profile
            log_path = profile.guard_path(_LOG)
        from core import shadow_log
        for r in rows:
            shadow_log.append(log_path, r)
        shadow_log.append(log_path, {"kind": "scored", "ts": round(now, 3), "output_source": output_source,
                                     "n_walled": len(items), "n_used": len(rows)})
    except Exception as exc:
        logger.debug("[rewarm] label_and_log skipped: %s", exc)
    return rows


def note_output(text: str, source: str) -> None:
    """The next output exists: consume the pending walled rows and label them off-thread. Never raises,
    never blocks the caller beyond a lock and a list copy."""
    try:
        if not REWARM_SHADOW_ON or not (text or "").strip():
            return
        items = _take_pending(time.time())
        if not items:
            return
        threading.Thread(target=label_and_log, args=(items, str(text), source),
                         name="rewarm-shadow", daemon=True).start()
    except Exception as exc:
        logger.debug("[rewarm] note_output skipped: %s", exc)


# ----------------------------------------------------------------------------- read side
def daily_counts(path: Path | None = None) -> dict:
    """{YYYY-MM-DD (UTC): {would_warm, distinct_fragments, scored_walled, by_label{...}}} from the log."""
    from datetime import datetime, timezone
    from core import shadow_log
    out: dict = {}
    seen: dict = {}
    for r in shadow_log.read_rows(path or _LOG):
        try:
            day = datetime.fromtimestamp(float(r.get("ts")), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            continue
        d = out.setdefault(day, {"would_warm": 0, "distinct_fragments": 0, "scored_walled": 0, "by_label": {}})
        if r.get("kind") == "would_warm":
            d["would_warm"] += 1
            lab = r.get("used_label") or "?"
            d["by_label"][lab] = d["by_label"].get(lab, 0) + 1
            seen.setdefault(day, set()).add(r.get("fragment_id"))
        elif r.get("kind") == "scored":
            d["scored_walled"] += int(r.get("n_walled") or 0)
    for day, ids in seen.items():
        out[day]["distinct_fragments"] = len(ids)
    return out
