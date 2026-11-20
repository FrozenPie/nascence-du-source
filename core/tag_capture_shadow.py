"""
Nascence -- TAG-AND-CAPTURE, the would-be FIFTH replay stratum, SHADOW (sleep_dream_redesign; J-2582, idea I-0107,
finding F-3315 = the J-2529 read by scripts/tag_capture_read.py).

QUESTION. replay_strengthen (core/memory/store.py) replays the wake block's top-K by importance per origin stratum
(quotas 3/3/2/2). Synaptic tag-and-capture says a WEAK trace laid down shortly before a consequential event can be
captured by that event and consolidated too. F-3315 found the raw version non-selective (capture_rate 0.667, only
1.18x over an event-time shift null) and dominated by one perseverating sow loop (a refused FIRE scored twice, 64
identical 'You have no seed' refusals). This module computes, at each sleep, what a CORRECTED fifth stratum WOULD
pick, and logs it. Nothing else.

LAWS. Shadow only. Nothing enters the replay set; no importance / replay_count / any DB write (the DB is opened
mode=ro); nothing reaches a prompt, percept or preamble (D-0434). One write target: SHADOW_LOG, one row per sleep.
Fail-open: record_night() never raises into the sleep routine. Flag TAG_CAPTURE_SHADOW defaults OFF; the hook in
nodes/inner_monologue_node.py is restart-gated either way. replay_strengthen's own selection and quotas are NOT
touched (protected base system, additive only). Promotion into the live replay set is a founder call.

DECLARED BEFORE ANY RUN (F-3315's five corrections; do not tune to the outcome):
  (1) QUOTA_PER_NIGHT = 2 picks, ranked by consequence score (desc), then by number of distinct hands in the
      window (desc), then by fragment timestamp (asc).
  (2) ONE EVENT PER HAND PER CAPTURE WINDOW. Hand actions are first merged per (cycle, hand): a FIRE whose own
      answer was a refusal is ONE event of kind 'refusal', not deed + refusal. Inside one fragment's window each
      hand contributes at most one event (its max weight). Hand-less events (correction, wager_loss, retraction)
      are their own key each.
  (3) COLLAPSE REPEATED SAME-HAND REFUSALS INSIDE A BLOCK to one event: only the FIRST refusal of each hand in the
      wake block survives (its repeat count is kept on the event for the log, its weight stays 1.0).
  (4) CAPTURE_WINDOW_S = 1200 (20 min) after the fragment, and the event must fall inside the SAME wake block
      (since_ts, until_ts]; tags expire with the night. Identical to scripts/tag_capture_read.py.
  (5) Per-night log row: n_low, n_tagged, capture_rate, the picks (fragment ids + their event ids + hand family),
      and the event-shift null capture rate for that night (circular shift of event times within the block,
      N_SHIFT iterations, seed derived from the night).
  LOW-SALIENCE  episodic, chapter_id IS NULL, replay_count == 0, timestamp in (since_ts, until_ts]. Live, the hook
      runs AFTER replay_strengthen, so its picks already carry replay_count >= 1 and drop out on their own. For a
      replay of PAST nights (harness), exclude_top_k=True also removes replay_strengthen's own per-stratum top-K
      recomputed on current values (the tag_capture_read.py approximation).
  CONSEQUENCE CLASSES, weights and refusal regex: verbatim from scripts/tag_capture_read.py (deed 1.0, refusal 1.0,
      correction delta_social >= 0.5 weight X, wager_loss predicted-measured >= 0.2 weight gap, retraction 1.0).
  HAND FAMILY of a pick = the hand of its highest-weight event in the window (ties: earliest); a pick tagged only by
      hand-less events gets 'class:<kind>'.
  FALSIFIED IF (read job / harness): across replayed nights, > 50% of picks share one hand family, OR the per-night
      capture_rate stays above 0.5 (median over nights with n_low > 0 above 0.5).
"""
from __future__ import annotations

import bisect
import json
import logging
import random
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("nascence.tag_capture_shadow")

TAG_CAPTURE_SHADOW = False     # flag OFF by default (shadow, restart-gated); True = one row per sleep, nothing else

_ROOT = Path(__file__).parent.parent
_SHADOW = _ROOT / "data" / "logs" / "tag_capture_shadow.jsonl"     # the ONE write target
VERSION = 1

QUOTA_PER_NIGHT = 2
CAPTURE_WINDOW_S = 1200
BLOCK_CAP_S = 24 * 3600
CORRECTION_MIN = 0.5
WAGER_GAP_MIN = 0.2
N_SHIFT = 100
SEEK_MARGIN_S = 3600           # tail-reads start this much before the block, so slightly out-of-order lines survive
REFUSAL_RX = re.compile(r"(no seed|have no|there is no|nothing to|already;|too dark|cannot|can't|won't)", re.I)
STRATA = [  # core/memory/store.py replay_strengthen(), verbatim WHERE clauses and quotas (read only, never edited)
    ("origin IN ('reading','study','research')", 3),
    ("origin IN ('lived','social_notification')", 3),
    ("origin NOT IN ('reading','study','research','lived','social_notification','dream','action','activity')", 2),
    ("origin IN ('dream','action','activity')", 2),
]
_LOG_RX = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) ")
_CORR_RX = re.compile(r"correction detected .{0,4}delta_social=([0-9.]+)")
_CANNOT_RX = re.compile(r"\[monologue\] cannot ([a-z]+)[a-z ]*:")
_JTS_RX = re.compile(r'^\{"ts": ([0-9.]+)')


# ---- tail reads (files are append-ordered by time; binary-search the byte offset, never read the whole log) -------
def _log_ts(line: str) -> float | None:
    m = _LOG_RX.match(line)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000


def _json_ts(line: str) -> float | None:
    m = _JTS_RX.match(line)
    return float(m.group(1)) if m else None


def _lines_since(path: Path, t0: float, ts_of) -> list[str]:
    """Lines of an append-ordered text file from (about) the first line with ts >= t0 - SEEK_MARGIN_S."""
    if not path.exists():
        return []
    target = t0 - SEEK_MARGIN_S
    with open(path, "rb") as fh:
        fh.seek(0, 2)
        lo, hi = 0, fh.tell()
        while hi - lo > 65536:
            mid = (lo + hi) // 2
            fh.seek(mid)
            fh.readline()
            ts = None
            for _ in range(200):
                raw = fh.readline()
                if not raw:
                    break
                ts = ts_of(raw.decode("utf-8", "replace"))
                if ts is not None:
                    break
            if ts is None or ts >= target:
                hi = mid
            else:
                lo = mid
        fh.seek(lo)
        if lo:
            fh.readline()
        return fh.read().decode("utf-8", "replace").splitlines()


# ---- events ---------------------------------------------------------------------------------------------------------
def load_events(root: Path, since_ts: float, until_ts: float) -> list[dict]:
    """Consequence events in (since_ts, until_ts], already merged per (cycle, hand) -- correction (2), first half."""
    data = root / "data"
    ev: list[dict] = []
    for line in _lines_since(data / "hands_trace.jsonl", since_ts, _json_ts):
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = float(r.get("ts") or 0)
        if not (since_ts < ts <= until_ts):
            continue
        per_hand: dict[str, str] = {}
        for d in r.get("dispatch") or []:
            fam = d.get("family")
            if d.get("decision") == "FIRE" and fam and fam != "look":
                per_hand.setdefault(fam, "deed")
        for h in r.get("hands") or []:
            if isinstance(h, dict) and h.get("hand") and h.get("hand") != "look" \
                    and REFUSAL_RX.search(str(h.get("answer") or "")):
                per_hand[h["hand"]] = "refusal"          # a refused FIRE is ONE refusal event, not deed + refusal
        for hand, kind in per_hand.items():
            ev.append({"ts": ts, "kind": kind, "w": 1.0, "hand": hand, "id": f"{r.get('cycle')}:{hand}"})
    for line in _lines_since(data / "nascence.log", since_ts, _log_ts):
        if "correction detected" not in line and "[monologue] cannot " not in line:
            continue
        ts = _log_ts(line)
        if ts is None or not (since_ts < ts <= until_ts):
            continue
        c = _CORR_RX.search(line)
        if c and float(c.group(1)) >= CORRECTION_MIN:
            ev.append({"ts": ts, "kind": "correction", "w": float(c.group(1)), "hand": None,
                       "id": "nascence.log@" + line[:23]})
            continue
        k = _CANNOT_RX.search(line)
        if k:
            ev.append({"ts": ts, "kind": "refusal", "w": 1.0, "hand": k.group(1), "id": "nascence.log@" + line[:23]})
    for line in _lines_since(data / "logs" / "recall_wager_shadow.jsonl", since_ts, _json_ts):
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = float(r.get("ts") or 0)
        gap = float(r.get("predicted") or 0) - float(r.get("measured") or 0)
        if since_ts < ts <= until_ts and gap >= WAGER_GAP_MIN:
            ev.append({"ts": ts, "kind": "wager_loss", "w": round(gap, 3), "hand": None, "id": f"wager:{r.get('cycle_id')}"})
    rp = data / "retractions.jsonl"
    if rp.exists():
        for line in rp.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            ts = float(r.get("ts") or 0)
            if since_ts < ts <= until_ts:
                ev.append({"ts": ts, "kind": "retraction", "w": 1.0, "hand": None, "id": f"retraction@{ts}"})
    ev.sort(key=lambda e: (e["ts"], e["id"]))
    return ev


def collapse_refusals(events: list[dict]) -> tuple[list[dict], int]:
    """Correction (3): keep only the FIRST refusal of each hand in the block. Returns (events, n_dropped)."""
    first: dict[str, dict] = {}
    out, dropped = [], 0
    for e in events:
        if e["kind"] == "refusal" and e["hand"]:
            if e["hand"] in first:
                first[e["hand"]]["repeats"] = first[e["hand"]].get("repeats", 1) + 1
                dropped += 1
                continue
            e = dict(e)
            first[e["hand"]] = e
        out.append(e)
    return out, dropped


# ---- fragments ------------------------------------------------------------------------------------------------------
def _db_path() -> Path:
    from core.memory import store as _store
    return Path(_store.DB_PATH)


def low_salience(db_path: Path, since_ts: float, until_ts: float, exclude_top_k: bool = False) -> list[dict]:
    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        top: set[str] = set()
        if exclude_top_k:
            for where, quota in STRATA:
                for (fid,) in conn.execute(
                        "SELECT fragment_id FROM memory_fragments WHERE layer='episodic' AND timestamp > ? AND timestamp <= ? "
                        f"AND chapter_id IS NULL AND {where} ORDER BY (importance - 0.08 * replay_count) DESC, timestamp DESC "
                        "LIMIT ?", (since_ts, until_ts, quota)):
                    top.add(fid)
        rows = conn.execute(
            "SELECT fragment_id, timestamp, origin FROM memory_fragments WHERE layer='episodic' AND timestamp > ? "
            "AND timestamp <= ? AND chapter_id IS NULL AND COALESCE(replay_count,0)=0 ORDER BY timestamp",
            (since_ts, until_ts)).fetchall()
    finally:
        conn.close()
    return [{"fid": f, "ts": float(t), "origin": o} for f, t, o in rows if f not in top]


# ---- scoring --------------------------------------------------------------------------------------------------------
def _window(frag_ts: float, keys: list[float], events: list[dict], until_ts: float) -> list[dict]:
    lo = bisect.bisect_right(keys, frag_ts)
    hi = bisect.bisect_right(keys, min(frag_ts + CAPTURE_WINDOW_S, until_ts))
    best: dict[str, dict] = {}                      # correction (2): one event per hand per window
    for e in events[lo:hi]:
        k = e["hand"] if e["hand"] else e["id"]
        if k not in best or e["w"] > best[k]["w"]:
            best[k] = e
    return list(best.values())


def _hand_family(hit: list[dict]) -> str:
    e = sorted(hit, key=lambda x: (-x["w"], x["ts"]))[0]
    return e["hand"] if e["hand"] else f"class:{e['kind']}"


def _n_tagged(frags: list[dict], events: list[dict], until_ts: float) -> int:
    keys = [e["ts"] for e in events]
    n = 0
    for f in frags:
        lo = bisect.bisect_right(keys, f["ts"])
        hi = bisect.bisect_right(keys, min(f["ts"] + CAPTURE_WINDOW_S, until_ts))
        n += hi > lo
    return n


def compute_night(since_ts: float, until_ts: float, *, root: Path | None = None, db_path: Path | None = None,
                  exclude_top_k: bool = False, kind: str | None = None) -> dict:
    """The would-be fifth stratum for one wake block. Pure read; returns the shadow row (does not write it)."""
    root = Path(root) if root is not None else _ROOT
    since_ts = max(float(since_ts), float(until_ts) - BLOCK_CAP_S)
    frags = low_salience(Path(db_path) if db_path is not None else _db_path(), since_ts, until_ts, exclude_top_k)
    raw = load_events(root, since_ts, until_ts)
    events, n_dropped = collapse_refusals(raw)
    keys = [e["ts"] for e in events]
    scored = []
    for f in frags:
        hit = _window(f["ts"], keys, events, until_ts)
        if hit:
            scored.append((sum(e["w"] for e in hit), len(hit), f, hit))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]["ts"]))
    picks = [{"fragment_id": f["fid"], "frag_ts": round(f["ts"], 1), "origin": f["origin"], "score": round(v, 3),
              "hand_family": _hand_family(hit),
              "event_ids": [e["id"] for e in sorted(hit, key=lambda x: x["ts"])],
              "event_kinds": [e["kind"] for e in sorted(hit, key=lambda x: x["ts"])]}
             for v, _n, f, hit in scored[:QUOTA_PER_NIGHT]]
    span = max(until_ts - since_ts, 1.0)
    rng = random.Random(int(until_ts))
    null = []
    if frags and events:
        for _ in range(N_SHIFT):
            off = rng.uniform(0, span)
            sh = sorted(({"ts": since_ts + ((e["ts"] - since_ts + off) % span)} for e in events), key=lambda x: x["ts"])
            null.append(_n_tagged(frags, sh, until_ts))
    by_kind: dict[str, int] = {}
    for e in events:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
    n_low, n_tag = len(frags), len(scored)
    return {
        "ts": round(time.time(), 1), "v": VERSION, "kind": kind, "since_ts": round(since_ts, 1),
        "until_ts": round(until_ts, 1), "block_h": round((until_ts - since_ts) / 3600, 2),
        "n_low": n_low, "n_events_raw": len(raw), "n_events": len(events), "n_refusals_collapsed": n_dropped,
        "events_by_kind": by_kind, "n_tagged": n_tag,
        "capture_rate": round(n_tag / n_low, 4) if n_low else None,
        "null_capture_rate": round(sum(null) / len(null) / n_low, 4) if null and n_low else None,
        "null_p95_tagged": sorted(null)[int(0.95 * len(null)) - 1] if null else None,
        "quota": QUOTA_PER_NIGHT, "picks": picks,
    }


def _append(row: dict, path: Path | None = None) -> None:
    from core import profile
    target = Path(path) if path is not None else profile.guard_path(_SHADOW)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def record_night(since_ts: float, until_ts: float | None = None, kind: str | None = None) -> dict | None:
    """Sleep hook (call AFTER replay_strengthen). Flag off -> no-op. Never raises; the return value is ignored."""
    if not TAG_CAPTURE_SHADOW:
        return None
    try:
        row = compute_night(since_ts, until_ts if until_ts is not None else time.time(), kind=kind)
        _append(row)
        return row
    except Exception as exc:
        logger.debug("[tag_capture] shadow row failed (non-fatal): %s", exc)
        return None
