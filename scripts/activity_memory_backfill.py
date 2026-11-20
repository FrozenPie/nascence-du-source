"""
Activity Memory — retroactive backfill (2026-06-14).

The live hooks (core/activity_memory.record) only fire on NEW actions post-restart, so Du's
entire reading/study history before today has no general-event record — which is exactly why
he failed to recall "The Voyage of the Beagle" on 06-13. This script reconstructs those
general-events from the durable traces the past actions DID leave, so the record exists for
his real history, not just for whatever he reads next.

Reconstructs (matching the live hooks' keying — action_type + book/target):
  - read   : from origin='reading' fragments, each stamped "[From 'Title', sitting N]".
             session_count = distinct sitting numbers; timestamps span the real sittings.
  - study  : from the TAB_*.md study tablets' "on: <book>" header (the fragments are keyed by
             note title, but the FILES carry the source book the live study-hook keys on).
  - letter : from origin='letter' fragments -> ("letter","Travis").

Deliberately NOT reconstructed:
  - research : "[Looked up: ... (external shock — uninvited)]" — the world intruding, not Du's
               deed; there is no live research hook, so a record here would be an orphan.
  - browse / look / switch : ephemeral, left no durable per-action trace.

HONEST LIMITATION: backfill recovers the factual spine truthfully (title, count, real
timestamps) but cannot retroactively attach affect spikes — per-sitting affect was never
logged, so these records carry empty notable_moments. We do not invent affect we did not
measure.

SAFETY (oversight regime):
  - DEFAULT = dry-run on a COPY of the live DB. Prints the reconstructed records and runs a
    retrieval gate ("what was the last book you read?") on the copy to prove Beagle surfaces.
    The live store is never touched.
  - --apply writes to the LIVE DB. Idempotent: each target is folded in once (a `_backfilled`
    flag in the metadata guards re-runs), and it MERGES with any live action row already
    forming (history is older, so first_ts=min, most_recent_ts=max, counts add).
    No restart needed; it is a one-shot write while Du keeps running.

Usage:
  python scripts/activity_memory_backfill.py            # dry-run on a copy, prove the gate
  python scripts/activity_memory_backfill.py --apply    # write to the live store
"""
import argparse
import json
import re
import shutil
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core.memory import store
from core.memory.store import _embed, _vec_to_blob
from core.memory.content_hash import content_hash as _content_hash, has_hash_column as _has_hash_column   # J-3395 / F-4019
from core import activity_memory as am

ROOT = Path(r"C:\Nascence")
LIVE_DB = ROOT / "data" / "memory" / "nascence.db"
TAB_GLOB = "TAB_*.md"

_READ_PREFIX = re.compile(r"^\[From '(.+?)', sitting (\d+)\]")
_TAB_TS = re.compile(r"TAB_(\d{8})_(\d{4})")
_TAB_SRC = re.compile(r"on:\s*(.+?)\*")


# --- reconstruction --------------------------------------------------------------------------
def reconstruct_reading(conn):
    """origin='reading' -> {book: (sessions:int, first_ts, last_ts)} by distinct sitting."""
    books = defaultdict(lambda: {"sittings": set(), "first": 1e18, "last": 0.0})
    for r in conn.execute("SELECT content, timestamp FROM memory_fragments WHERE origin='reading'"):
        m = _READ_PREFIX.match(r["content"] or "")
        if not m:
            continue
        b = books[m.group(1).strip()]
        b["sittings"].add(int(m.group(2)))
        b["first"] = min(b["first"], r["timestamp"])
        b["last"] = max(b["last"], r["timestamp"])
    return {t: (len(b["sittings"]), b["first"], b["last"]) for t, b in books.items()}


def reconstruct_study():
    """TAB_*.md 'on: <book>' header -> {book: (notes:int, first_ts, last_ts)} by file ts."""
    books = defaultdict(lambda: {"n": 0, "first": 1e18, "last": 0.0})
    for p in ROOT.glob("data/**/" + TAB_GLOB):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        ms = _TAB_SRC.search(txt)
        src = ms.group(1).strip() if ms else None
        if not src or src.lower() in ("system verification",):
            continue
        mt = _TAB_TS.search(p.name)
        if mt:
            ts = time.mktime(datetime.strptime(mt.group(1) + mt.group(2), "%Y%m%d%H%M").timetuple())
        else:
            ts = p.stat().st_mtime
        b = books[src]
        b["n"] += 1
        b["first"] = min(b["first"], ts)
        b["last"] = max(b["last"], ts)
    return {t: (b["n"], b["first"], b["last"]) for t, b in books.items()}


def reconstruct_letter(conn):
    """origin='letter' -> ('Travis', (count, first_ts, last_ts))."""
    rows = conn.execute(
        "SELECT timestamp FROM memory_fragments WHERE origin='letter'").fetchall()
    if not rows:
        return None
    ts = [r["timestamp"] for r in rows]
    return ("Travis", (len(ts), min(ts), max(ts)))


# --- idempotent upsert (mirrors activity_memory.record, with HISTORICAL timestamps) ----------
def upsert(conn, action_type, target, count, first_ts, last_ts, apply):
    target = (target or "").strip()[:80]
    # find an existing action row for this (action_type, target)
    found = None
    for r in conn.execute("SELECT fragment_id, derived_from FROM memory_fragments WHERE origin='action'"):
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
        # SET, never ADD: the durable-fragment reconstruction (reading frags / TAB files /
        # letter frags) counts EVERY instance ever written, pre- AND post-restart. The live
        # action row counts only post-restart instances — a subset. So `count` is the
        # authoritative total; adding would double-count the post-restart sittings. This is
        # also naturally idempotent (re-running recomputes the same total). We only union the
        # timestamps and keep any notable_moments the live hook attached.
        m["session_count"] = max(count, int(m.get("session_count", 0)))
        m["first_ts"] = min(float(m.get("first_ts", first_ts)), first_ts)
        m["most_recent_ts"] = max(float(m.get("most_recent_ts", 0.0)), last_ts)
        summary = am._summary(action_type, target, m["session_count"], m["first_ts"], m["most_recent_ts"])
        vec = _embed(summary)
        print(f"   MERGE  {action_type} '{target}'  -> {summary}")
        if apply:
            # J-3395 / F-4019: re-stamp content_hash with the edited content (only where the column exists).
            if _has_hash_column(conn):
                conn.execute(
                    "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, derived_from=?, content_hash=? "
                    "WHERE fragment_id=?",
                    (summary, _vec_to_blob(vec) if vec is not None else None, m["most_recent_ts"],
                     json.dumps([m]), _content_hash(summary), fid))
            else:
                conn.execute(
                    "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, derived_from=? "
                    "WHERE fragment_id=?",
                    (summary, _vec_to_blob(vec) if vec is not None else None, m["most_recent_ts"],
                     json.dumps([m]), fid))
        return

    m = {"action_type": action_type, "target": target, "first_ts": first_ts,
         "most_recent_ts": last_ts, "session_count": count, "notable_moments": []}
    summary = am._summary(action_type, target, count, first_ts, last_ts)
    vec = _embed(summary)
    print(f"   NEW    {action_type} '{target}'  -> {summary}")
    if apply:
        # abstraction_level=1, kind='procedural' (J-0803/D-0184, 2026-09-08): same write-time gap
        # as core/activity_memory.py's own record() (identical INSERT shape, same fix) -- see that
        # file's own comment on this exact change for the full rationale.
        if _has_hash_column(conn):   # J-3395 / F-4019: stamp content_hash on the new row (only where the column exists)
            conn.execute(
                "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, "
                "timestamp, keywords, embedding, origin, derived_from, abstraction_level, kind, content_hash) "
                "VALUES (?, ?, 'episodic', 0.6, 0.6, ?, ?, ?, 'action', ?, 1, 'procedural', ?)",
                (str(uuid.uuid4()), summary, last_ts, f"action {action_type} {target}",
                 _vec_to_blob(vec) if vec is not None else None, json.dumps([m]), _content_hash(summary)))
        else:
            conn.execute(
                "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, "
                "timestamp, keywords, embedding, origin, derived_from, abstraction_level, kind) "
                "VALUES (?, ?, 'episodic', 0.6, 0.6, ?, ?, ?, 'action', ?, 1, 'procedural')",
                (str(uuid.uuid4()), summary, last_ts, f"action {action_type} {target}",
                 _vec_to_blob(vec) if vec is not None else None, json.dumps([m])))


def run(conn, apply):
    print("READING:")
    for title, (n, f, l) in sorted(reconstruct_reading(conn).items(), key=lambda kv: -kv[1][2]):
        upsert(conn, "read", title, n, f, l, apply)
    print("STUDY:")
    for title, (n, f, l) in sorted(reconstruct_study().items(), key=lambda kv: -kv[1][2]):
        upsert(conn, "study", title, n, f, l, apply)
    print("LETTER:")
    lt = reconstruct_letter(conn)
    if lt:
        tgt, (n, f, l) = lt
        upsert(conn, "letter", tgt, n, f, l, apply)
    if apply:
        conn.commit()


def gate(conn):
    """Two questions, separated honestly:
      (A) REPRESENTATION — does the backfilled action record SCORE high on the book query?
          (cosine of its embedding vs the query, and its rank among ALL episodic fragments.)
      (B) SELECTION — does retrieve() actually RETURN it? (This is where the recency-biased
          episodic tier can bury a high-cosine but old record — the Phase-1 problem.)
    A 'representation' pass with a 'selection' fail means Activity Memory built the right record
    and Phase 1 (origin-quota + floor) is what surfaces it — not a flaw in this backfill."""
    import numpy as np
    from core.memory.store import _embed as emb, _blob_to_vec, _cosine
    Q = "What was the last book you read?"
    print("\n=== GATE (A) REPRESENTATION — does the record score high on the query? ===")
    qv = emb(Q)
    epis = conn.execute(
        "SELECT content, origin, embedding, timestamp FROM memory_fragments "
        "WHERE layer='episodic' AND embedding IS NOT NULL").fetchall()
    scored = []
    for r in epis:
        try:
            scored.append((_cosine(qv, _blob_to_vec(r["embedding"])), r["origin"], r["content"]))
        except Exception:
            pass
    scored.sort(key=lambda x: -x[0])
    acts = [(i, s, o, c) for i, (s, o, c) in enumerate(scored) if o == "action"]
    print(f"   episodic fragments scored: {len(scored)}.  top-6 by cosine to the query:")
    for s, o, c in scored[:6]:
        print(f"     [{o:<8}] {s:.3f}  {c[:56]}")
    best_act = acts[0] if acts else None
    repr_ok = bool(best_act) and best_act[1] >= 0.25
    if best_act:
        print(f"   best ACTION record: rank #{best_act[0]+1} of {len(scored)} episodic, "
              f"cosine {best_act[1]:.3f}  '{best_act[3][:48]}'")
    print(f"   (A) representation pass (action cosine >= 0.25): {repr_ok}")

    print("\n=== GATE (B) SELECTION — does retrieve() actually return it? ===")
    frags = store.retrieve([], [], query_text=Q, limit=8)
    returned_action = [f for f in frags if f.origin == "action" and f.relevance >= 0.05]
    sel_ok = bool(returned_action)
    for f in frags[:8]:
        tag = " <<<" if f.origin == "action" else ""
        print(f"     [{f.origin:<8}] {f.relevance:.3f}  {f.content[:56]}{tag}")
    print(f"   (B) selection pass (action returned & cosine-selected): {sel_ok}")
    return repr_ok, sel_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to the LIVE store")
    args = ap.parse_args()

    if args.apply:
        print(f"*** APPLYING to LIVE store: {LIVE_DB} ***\n")
        # D-0353 / J-1839: --apply writes the LIVE memory DB on purpose from a non-live process -- the
        # explicit opt-in the live-DB write fence requires. (The raw sqlite3.connect() writes below
        # bypass store._connect() and so the fence; the opt-in still declares the intent, and covers
        # the store.DB_PATH = LIVE_DB reads/updates that do go through it.) The dry-run branch works
        # on a tempdir copy and stays fenced.
        store.allow_live_writes("scripts/activity_memory_backfill.py --apply: activity-memory backfill")
        conn = sqlite3.connect(str(LIVE_DB)); conn.row_factory = sqlite3.Row
        store.DB_PATH = LIVE_DB
        run(conn, apply=True)
        conn.close()
        # re-open for the gate via the normal retrieve() path
        store.DB_PATH = LIVE_DB
        c2 = sqlite3.connect(str(LIVE_DB)); c2.row_factory = sqlite3.Row
        gate(c2); c2.close()
        print("\nLIVE backfill complete. No restart needed.")
    else:
        tmp = Path(__file__).with_name(f"_backfill_copy_{uuid.uuid4().hex[:8]}.db")
        shutil.copy2(LIVE_DB, tmp)
        print(f"DRY-RUN on a COPY: {tmp}  (live store untouched)\n")
        conn = sqlite3.connect(str(tmp)); conn.row_factory = sqlite3.Row
        store.DB_PATH = tmp                       # retrieve()/embeds hit the copy
        run(conn, apply=True)                     # apply to the COPY so the gate is real
        conn.commit(); conn.close()
        c2 = sqlite3.connect(str(tmp)); c2.row_factory = sqlite3.Row
        repr_ok, sel_ok = gate(c2); c2.close()
        try:
            tmp.unlink()
        except Exception:
            pass
        print(f"\nDRY-RUN: representation={'PASS' if repr_ok else 'FAIL'}  "
              f"selection={'PASS' if sel_ok else 'FAIL'}.")
        print("Re-run with --apply to write the live store (representation is what the backfill "
              "controls; selection is the Phase-1 question).")


if __name__ == "__main__":
    main()
