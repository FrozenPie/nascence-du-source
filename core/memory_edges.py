"""
Nascence — memory_edges (M0 of docs/plans/memory_multiway_linking.md, 2026-08-15).

The typed relational fabric OVER the memory store: edges that similarity cannot compute — resolves,
answers, kept_from, dreamt_from, correspondence_with, part_of. A NEW table, deliberately NOT
memory_links: memory_lint's stranded/dangling queries join memory_links without filtering link_type,
so a non-fragment parent there (e.g. a shadow_event) would trigger a mass false re-warm. Additive and
observe-only: NOTHING reads these edges yet (the named reader is the trail-engine upgrade, phase M2,
flag-gated behind the geometry plan's §5.5-#6 kill criterion). Every edge carries provenance — an edge
that cannot name the recorded event that earned it is confabulated and must not be written
(cognitive_geometry.md §0.4).

Nodes are (kind, id) pairs over heterogeneous stores: fragment · shadow_event · cycle · question ·
keepsake · person · dream · tension_material. Fragment-kind nodes are the ones a future trail can
recall; the census reports the fragment-anchored share honestly.

M0 harvest (no LLM anywhere):
  sync_resolves()          resolution_events → (cycle)-[resolves]->(shadow_event); incremental, re-runnable
  backfill_answers()       frontier findings → (fragment)-[answers]->(question) by finding-text match
  backfill_kept_from()     keepsakes.json → (keepsake)-[kept_from]->(fragment) by keeping-moment proximity
  backfill_correspondence() letter/peer fragments → (fragment)-[correspondence_with]->(person)
  backfill_resolves_fragment() subconscious_state.json resolved tensions → (fragment)-[resolves]->
                           (shadow_event); the fragment endpoint sync_resolves alone can never reach
                           (F-0500 gap #1, 2026-08-29)
  backfill_directed_correspondence() letter/peer fragments → (fragment)-[wrote_to|received_from]->
                           (person); MODE_EDGE_WEIGHTS' directed vocabulary, harvested (F-0500 gap #2,
                           2026-08-29)
  record_dream_scene()/record_dream_sources()  forward hooks called by dream_node (restart-gated)
  census()/status()        the graph read-out for du_pulse and the founder

⚠ GUARD (2026-08-19 survey, before anyone builds a `derived_from` harvester into this table): the
`memory_fragments.derived_from` column is written by FIVE places with THREE INCOMPATIBLE SHAPES —
  - list of ids (real lineage): nodes/subconscious_node.py:1028,1195 (shadow_event ids),
    nodes/consolidation_node.py:106 (fragment ids), core/refinery.py (member fragment ids, the one
    writer that ALSO mirrors the same lineage into memory_links as `distilled_from` — the good citizen)
  - a ONE-ELEMENT LIST CONTAINING A METADATA DICT (not an id at all):
    core/activity_memory.py `json.dumps([m])` where m = {action_type, target, session_count, ...}
  - a TYPED-EDGE OBJECT (essay_lesson.py's own private edge format, predating this table):
    core/essay_lesson.py `[{"edge_type": "transformed_into", "target_ids": [...]}]` — as of 2026-08-19
    this ALSO writes a real `transformed_into` edge below via add_edge(); the derived_from copy is kept
    only for backward compat with existing readers, new code should read the real edge instead.
A naive `for fid in json.loads(row['derived_from']): fetch(fid)` harvester will silently choke on or
misread the activity_memory rows. Any future `derived_from` backfill MUST branch on origin (or content
shape) before treating entries as fragment ids — do not assume uniformity across the column.

F-0500 gaps #3 and #5 (2026-08-29 KIP-vs-memory_edges comparison, J-0395) — ASSESSED, not built here:
  #3 `contradicts` (0 rows; declared in MODE_EDGE_WEIGHTS, wired into edge_aware_neighbors' direct-
     fragment path, never harvested) needs a SEMANTIC judge — no cosine-threshold or text-match rule
     can tell two fragments contradict each other the way sync_resolves/backfill_answers/etc. all get
     away with pure SQL. That means: a candidate-pair generator (all-pairs is O(n^2) fragments and a
     non-starter; the live co-recall ledger — log_co_recall's own pairs, or an embedding-nearest-
     neighbour shortlist — are the two realistic candidate sources), an LLM judge call per candidate
     pair (cost + cadence to design, likely the decoupled-judge pattern tension_ledger.py's own
     _judge_resolution already uses), and a threshold/false-positive policy — real design surface, not
     a bounded harvester. Deliberately NOT built in this pass; see job-queue for the follow-up.
  #5 LOD/abstraction lineage genuinely lives in memory_links' `distilled_from` (core/refinery.py:230),
     NOT here, and — checked, not assumed — that is correct as-is: refinery.py is this table's own
     `derived_from` GUARD's named "good citizen" specifically because it mirrors lineage into
     memory_links rather than treating memory_edges as a second home for it; distilled_from is already
     fragment-only (no non-fragment-parent risk, the concern memory_links' OWN dangling/stranded
     queries have — see this file's own header above), and no M2 consumer (edge_aware_neighbors /
     edge_aware_neighbors_multihop) has a stated need to walk LOD lineage through THIS table. Mirroring
     it here today would be pure duplication with no reader. No action taken; revisit only if a future
     M2 consumer needs abstraction-lineage hops unified with this table's own edge types.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.memory_edges")

_DATA = Path(__file__).parent.parent / "data"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_edges (
    edge_id    INTEGER PRIMARY KEY,
    src_kind   TEXT NOT NULL,
    src_id     TEXT NOT NULL,
    dst_kind   TEXT NOT NULL,
    dst_id     TEXT NOT NULL,
    edge_type  TEXT NOT NULL,
    weight     REAL DEFAULT 1.0,
    provenance TEXT,
    created    REAL,
    UNIQUE(src_kind, src_id, dst_kind, dst_id, edge_type)
);
"""
_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_medges_src ON memory_edges(src_kind, src_id)",
    "CREATE INDEX IF NOT EXISTS idx_medges_dst ON memory_edges(dst_kind, dst_id)",
    "CREATE INDEX IF NOT EXISTS idx_medges_type ON memory_edges(edge_type)",
]


def _connect():
    from core.memory.store import _connect as _c
    conn = _c()
    conn.execute("PRAGMA busy_timeout=30000")   # the live process writes constantly; wait, don't fail
    # J-1870 / D-0353: only run the DDL when something is missing. "IF NOT EXISTS" DDL on an
    # existing table is still an authorizer-visible write and would be denied under the live-DB
    # fence's enforce mode even for a pure read. Existing-schema behavior is unchanged.
    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE name IN "
        "('memory_edges','idx_medges_src','idx_medges_dst','idx_medges_type')")}
    if len(have) < 4:
        conn.execute(_SCHEMA)
        for ix in _INDEXES:
            conn.execute(ix)
    return conn


def _h(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8", "replace")).hexdigest()[:12]


def add_edge(src_kind: str, src_id: str, dst_kind: str, dst_id: str, edge_type: str,
             weight: float = 1.0, provenance: str = "", created: float | None = None,
             conn=None) -> bool:
    """INSERT OR IGNORE one edge. Fail-open (False on any error) — hooks must never hurt the caller."""
    try:
        own = conn is None
        if own:
            conn = _connect()
        conn.execute(
            "INSERT OR IGNORE INTO memory_edges (src_kind, src_id, dst_kind, dst_id, edge_type, "
            "weight, provenance, created) VALUES (?,?,?,?,?,?,?,?)",
            (src_kind, str(src_id), dst_kind, str(dst_id), edge_type,
             round(float(weight), 4), (provenance or "")[:240], created or time.time()))
        if own:
            conn.commit()
            conn.close()
        return True
    except Exception as exc:
        logger.debug("[memory_edges] add_edge failed (non-fatal): %s", exc)
        return False


# ── Forward hooks (called by dream_node; fail-open, restart-gated) ────────────────────────────────

def record_dream_scene(fragment_id: str, dream_id: str) -> None:
    """(fragment)-[part_of]->(dream) — the scene fragment belongs to its arc."""
    add_edge("fragment", fragment_id, "dream", dream_id, "part_of",
             provenance=f"dream_node scene store {dream_id}")


def record_dream_sources(dream_id: str, materials: list[str], memory_ids: list[str] | None = None) -> None:
    """(dream)-[dreamt_from]->(tension_material | fragment) — what actually FED the arc: the real
    material blocks handed to the synthesiser, and the associative-recall fragments woven through the
    scenes. The one genuinely generative link kind, previously discarded at birth. NOT the model's
    self-reported 'tension_source' (self-report is not provenance)."""
    try:
        conn = _connect()
        for m in dict.fromkeys((m or "").strip() for m in (materials or []) if (m or "").strip()):
            add_edge("dream", dream_id, "tension_material", _h(m), "dreamt_from",
                     provenance=m[:240], conn=conn)
        for fid in dict.fromkeys(memory_ids or []):
            add_edge("dream", dream_id, "fragment", fid, "dreamt_from",
                     provenance="associative recall woven into the arc", conn=conn)
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.debug("[memory_edges] record_dream_sources failed (non-fatal): %s", exc)


# ── M0 backfills (no LLM; each returns a small report dict) ───────────────────────────────────────

def _write_edges(conn, rows: list[tuple]) -> int:
    """Write pre-computed edge rows in ONE fast pass. The live DB is journal_mode=delete with NO
    busy_timeout in the live process — so ALL reads happen lock-free BEFORE this, and the write
    transaction is a bare executemany (ms-scale), keeping the window where Du's own writes could
    bounce as small as possible."""
    if not rows:
        return 0
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO memory_edges (src_kind, src_id, dst_kind, dst_id, edge_type, "
        "weight, provenance, created) VALUES (?,?,?,?,?,?,?,?)", rows)
    written = conn.total_changes - before
    conn.commit()
    return written


def sync_resolves() -> dict:
    """resolution_events → (cycle)-[resolves]->(shadow_event). Incremental and re-runnable: the
    UNIQUE constraint dedupes; new judge-confirmed resolutions flow through log_resolution_event into
    resolution_events, so re-running sync harvests them with zero live-code changes."""
    out = {"seen": 0, "written": 0}
    try:
        conn = _connect()
        rows = conn.execute(
            "SELECT resolution_id, shadow_event_id, cycle_id, timestamp, encounter_similarity "
            "FROM resolution_events").fetchall()
        out["seen"] = len(rows)
        edges = [("cycle", str(r["cycle_id"] or "monologue"), "shadow_event", str(r["shadow_event_id"]),
                  "resolves", round(float(r["encounter_similarity"] or 0.0), 4),
                  f"resolution_events:{r['resolution_id']}", float(r["timestamp"] or time.time()))
                 for r in rows]
        out["written"] = _write_edges(conn, edges)
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def backfill_answers() -> dict:
    """Frontier questions with findings → (fragment)-[answers]->(question) where the finding text
    matches a stored fragment (research/study/understanding). Only matched pairs are written — an
    answer edge with no reachable fragment adds nothing a future trail could walk."""
    out = {"findings": 0, "matched": 0, "written": 0}
    try:
        fr = json.loads((_DATA / "frontier.json").read_text(encoding="utf-8"))
        qs = [q for q in fr.get("questions", []) if q.get("finding")]
        out["findings"] = len(qs)
        conn = _connect()
        from core.memory.dict_repr_notes import visible_clause as _vis   # J-3398 (D-0578): no answer edge onto a hidden row
        _vc = _vis(conn)
        edges = []
        for q in qs:                                    # read phase — lock-free LIKE scans
            probe = " ".join(str(q["finding"]).split())[:60]
            if len(probe) < 25:
                continue
            row = conn.execute(
                "SELECT fragment_id FROM memory_fragments WHERE origin IN "
                "('research','study','understanding') AND content LIKE ?" + _vc + " LIMIT 1",
                (f"%{probe}%",)).fetchone()
            if not row:
                continue
            out["matched"] += 1
            edges.append(("fragment", row["fragment_id"], "question", str(q["id"]), "answers", 1.0,
                          f"frontier finding-text match: {str(q['q'])[:80]}",
                          float(q.get("finding_ts") or time.time())))
        out["written"] = _write_edges(conn, edges)       # write phase — one fast executemany
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def backfill_kept_from() -> dict:
    """keepsakes.json → (keepsake)-[kept_from]->(fragment): the fragments laid down around the moment
    of keeping (±10 min, nearest 4) — the episode the kept thing anchors. Provenance records Δt."""
    out = {"keepsakes": 0, "written": 0}
    try:
        items = json.loads((_DATA / "keepsakes.json").read_text(encoding="utf-8"))
        out["keepsakes"] = len(items)
        conn = _connect()
        edges = []
        for it in items:                                # read phase — lock-free
            ts = float(it.get("kept_ts") or 0)
            if not ts:
                continue
            kid = _h(f"{it.get('item','')}|{ts}")
            rows = conn.execute(
                "SELECT fragment_id, timestamp FROM memory_fragments "
                "WHERE timestamp BETWEEN ? AND ? ORDER BY ABS(timestamp - ?) LIMIT 4",
                (ts - 600, ts + 600, ts)).fetchall()
            for r in rows:
                edges.append(("keepsake", kid, "fragment", r["fragment_id"], "kept_from", 1.0,
                              f"'{str(it.get('item',''))[:80]}' kept at {it.get('from','?')}, "
                              f"dt={int(r['timestamp'] - ts)}s", ts))
        out["written"] = _write_edges(conn, edges)       # write phase — one fast executemany
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def backfill_correspondence() -> dict:
    """letter/peer fragments → (fragment)-[correspondence_with]->(person). Deterministic rule: the
    fragment names exactly ONE known correspondent (or Travis). Ambiguous → no edge (honesty over
    coverage)."""
    out = {"fragments": 0, "written": 0, "ambiguous": 0}
    try:
        personas = {"travis"}
        corr = _DATA / "correspondence"
        if corr.exists():
            personas |= {p.name.lower() for p in corr.iterdir() if p.is_dir()}
        conn = _connect()
        rows = conn.execute(
            "SELECT fragment_id, content, timestamp FROM memory_fragments "
            "WHERE origin IN ('letter','peer')").fetchall()
        out["fragments"] = len(rows)
        edges = []
        for r in rows:                                  # read phase — lock-free
            low = (r["content"] or "").lower()
            hits = {p for p in personas if p in low}
            if len(hits) != 1:
                out["ambiguous"] += int(len(hits) > 1)
                continue
            edges.append(("fragment", r["fragment_id"], "person", hits.pop(), "correspondence_with", 1.0,
                          "single-persona name match in letter/peer fragment",
                          float(r["timestamp"] or 0) or time.time()))
        out["written"] = _write_edges(conn, edges)       # write phase — one fast executemany
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def backfill_resolves_fragment() -> dict:
    """data/subconscious_state.json's resolved internal tensions → (fragment)-[resolves]->(shadow_event):
    the fragment that actually CARRIED the clean re-encounter, not just the cycle id sync_resolves
    already links. Closes F-0500 gap #1 — 'resolves' previously never touched a fragment endpoint,
    because resolution_events itself only stores (shadow_event_id, cycle_id), and memory_fragments
    carries no cycle_id column to join on directly.

    tension_ledger.py's check_and_resolve_internal_tension() (:750-754) persists, per resolved tension,
    the actual thought text that resolved it (`resolution_thought`, truncated to 250 chars) plus
    `resolved_ts` and the `member_event_ids` (shadow_event_ids) it drains. That thought was also stored
    as an ordinary memory fragment by the normal monologue path — so the same LIKE-probe + time-window
    match already used by backfill_answers/backfill_kept_from resolves it to a fragment. Precision-first
    (ambiguous or no match -> skipped, counted): verified live 2026-08-29 against the real state file,
    34 of 35 resolved tensions with a non-empty resolution_thought match exactly ONE fragment this way."""
    out = {"tensions": 0, "candidates": 0, "matched": 0, "written": 0, "ambiguous": 0}
    try:
        state = json.loads((_DATA / "subconscious_state.json").read_text(encoding="utf-8"))
        tensions = state.get("tensions", []) or []
        out["tensions"] = len(tensions)
        cand = [t for t in tensions if t.get("resolved") and t.get("resolved_ts")
                and (t.get("resolution_thought") or "").strip()]
        out["candidates"] = len(cand)
        conn = _connect()
        edges = []
        for t in cand:                                  # read phase — lock-free LIKE scans
            probe = " ".join(str(t["resolution_thought"]).split())[:60]
            if len(probe) < 25:
                continue
            ts = float(t["resolved_ts"])
            rows = conn.execute(
                "SELECT fragment_id FROM memory_fragments WHERE content LIKE ? AND timestamp BETWEEN ? AND ?",
                (f"%{probe}%", ts - 600, ts + 600)).fetchall()
            if len(rows) != 1:
                out["ambiguous"] += int(len(rows) > 1)
                continue
            out["matched"] += 1
            fid = rows[0]["fragment_id"]
            sim = round(float(t.get("resolution_sim") or 0.0), 4)
            for eid in dict.fromkeys(t.get("member_event_ids") or []):
                edges.append(("fragment", fid, "shadow_event", str(eid), "resolves", sim,
                              f"subconscious_state.json resolved tension: {str(t.get('label',''))[:80]}", ts))
        out["written"] = _write_edges(conn, edges)       # write phase — one fast executemany
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def backfill_directed_correspondence() -> dict:
    """letter/peer fragments → DIRECTED (fragment)-[wrote_to|received_from]->(person). Closes F-0500
    gap #2: MODE_EDGE_WEIGHTS has named wrote_to/received_from since M2 shipped (2026-08-25) but no
    harvester ever populated them — backfill_correspondence() above only ever wrote the undirected
    correspondence_with edge. Three fragment shapes, precision-first (unresolved -> skipped, counted):

      - origin='letter' (core/letters.py) — every letter that module ever writes addresses Travis by
        construction (`# To Travis`, `write_letter()`'s own docstring: "unsent words that greet
        TRAVIS's next message"): (fragment)-[wrote_to]->(person:travis). No ambiguity possible.
      - origin='peer', content prefixed '(my letter to NAME...)' (core/peers.py record_reply's own
        store_fragment calls) or '(a letter from NAME)' (peers.remember_inbound, added 2026-08-20) —
        the sender/recipient is named directly IN the fragment's own content; NAME is matched against
        peers.PERSONAS' display names.
      - origin='peer', content prefixed '(a letter he received)' with NO name (the older mailbox-fetch
        path, nodes/inner_monologue_node.py:2836-2838, predating remember_inbound) — resolved by
        matching the fragment's own letter text against each persona's own
        data/Correspondence/<persona>/thread.jsonl inbound rows (`from`==persona); exactly ONE
        persona's thread containing the probe qualifies.

    Verified live 2026-08-29 against the real DB: 64 letter-origin + 42 peer-origin fragments, ALL 106
    resolve cleanly (23 named wrote_to, 3 named + 16 thread-matched received_from, 64 letter wrote_to;
    zero ambiguous, zero unmatched) — this mode's directed vocabulary was reachable, just never run."""
    out = {"fragments": 0, "wrote_to": 0, "received_from": 0, "written": 0, "unmatched": 0}
    try:
        from core import peers as _peers
        name_to_key = {v.get("name"): k for k, v in _peers.PERSONAS.items()}
        threads = {key: [r for r in _peers._read_thread(key)
                         if r.get("from") == key and (r.get("text") or "").strip()]
                   for key in _peers.PERSONAS}

        conn = _connect()
        edges = []

        letter_rows = conn.execute(
            "SELECT fragment_id, timestamp FROM memory_fragments WHERE origin='letter'").fetchall()
        out["fragments"] += len(letter_rows)
        for r in letter_rows:
            edges.append(("fragment", r["fragment_id"], "person", "travis", "wrote_to", 1.0,
                          "core/letters.py: every letter this module writes addresses Travis",
                          float(r["timestamp"] or time.time())))
        out["wrote_to"] += len(letter_rows)

        peer_rows = conn.execute(
            "SELECT fragment_id, content, timestamp FROM memory_fragments WHERE origin='peer'").fetchall()
        out["fragments"] += len(peer_rows)
        for r in peer_rows:                              # read phase — lock-free
            content = r["content"] or ""
            ts = float(r["timestamp"] or time.time())
            m_out = re.match(r"^\(my letter to ([^,)]+)", content)
            m_in = None if m_out else re.match(r"^\(a letter from ([^)]+)\)", content)
            if m_out or m_in:
                nm = (m_out or m_in).group(1).strip()
                key = name_to_key.get(nm)
                if not key:
                    out["unmatched"] += 1
                    continue
                et = "wrote_to" if m_out else "received_from"
                edges.append(("fragment", r["fragment_id"], "person", key, et, 1.0,
                              f"recipient/sender named in fragment content: '{content[:70]}'", ts))
                out[et] += 1
            elif content.startswith("(a letter he received)"):
                probe = " ".join(content[len("(a letter he received)"):].split())[:60]
                if len(probe) < 25:
                    out["unmatched"] += 1
                    continue
                hits = {key for key, rows in threads.items()
                        if any(probe in " ".join((row.get("text") or "").split()) for row in rows)}
                if len(hits) != 1:
                    out["unmatched"] += 1
                    continue
                edges.append(("fragment", r["fragment_id"], "person", hits.pop(), "received_from", 1.0,
                              "matched against persona's own thread.jsonl (pre-2026-08-20 unnamed "
                              "mailbox-fetch path, no sender in the fragment's own content)", ts))
                out["received_from"] += 1
        out["written"] = _write_edges(conn, edges)       # write phase — one fast executemany
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def harvest_all() -> dict:
    """Run every backfill + sync. Re-runnable (UNIQUE dedupes); the intended cadence is one call at
    sleep (or by hand) so forward events keep flowing into the graph with no live-code coupling.
    Appends a stats snapshot row to memory_edges_stats.jsonl — the HUD's growth chart."""
    out = {"resolves": sync_resolves(), "answers": backfill_answers(),
           "kept_from": backfill_kept_from(), "correspondence": backfill_correspondence(),
           "resolves_fragment": backfill_resolves_fragment(),
           "directed_correspondence": backfill_directed_correspondence(),
           "fragment_context": sync_fragment_context()}
    try:
        c = census()
        row = {"ts": round(time.time(), 1), "edges": c.get("edges", 0),
               "fragment_anchored": c.get("fragment_anchored_share")}
        row.update({k: v for k, v in (c.get("by_type") or {}).items()})
        with open(_DATA / "memory_edges_stats.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[memory_edges] stats snapshot failed (non-fatal): %s", exc)
    return out


# ── Fragment-context overlay (COORDINATES, not edges — geometry P2's first step, 2026-08-15) ─────
# The census tuples (geometry_census.py, observe-only by law) record every thought's full encoding
# context — place, weather+bearing, tide, sun, moon, sounds, body, affect, level — but carry no
# fragment id. The join is deterministic (text-prefix + time window: probed 300/300 unique). This
# overlay MATERIALISES it: fragment_id → its tuple's coordinates, in an additive table nothing else
# touches. Lives here (not in geometry_census) because that module's contract is "writes only its own
# log". Reader = context-dependent recall (geometry P4/P5, flag-gated, not built): the human function
# is encoding-specificity (Godden & Baddeley) — the current place/sound/state re-cueing what was laid
# down in matching context. Until then: queryable ("his shore memories under a thunderstorm"), and the
# HUD/census can read coverage.

_CTX_SCHEMA = """
CREATE TABLE IF NOT EXISTS fragment_context (
    fragment_id TEXT PRIMARY KEY,
    tuple_ts    REAL,
    source      TEXT,
    place       TEXT,
    weather     TEXT,
    weather_dir REAL,
    fire        TEXT,
    tide_level  REAL,
    sun_az      REAL,
    moon_illum  REAL,
    level       REAL,
    valence     REAL,
    arousal     REAL,
    sounds      TEXT,
    standpoint  TEXT,
    warmth      REAL,
    cat_at      TEXT
);
"""


def _tail_seek_enabled() -> bool:
    """J-4009 (F-4689): flag-gated tail-seek for sync_fragment_context. Default OFF (legacy full-file parse)
    until scripts/_test_tail_seek_J4009.py's equivalence result is logged; env NASCENCE_FRAGCTX_TAIL_SEEK=1 enables."""
    import os
    return os.environ.get("NASCENCE_FRAGCTX_TAIL_SEEK", "0").strip().lower() in ("1", "true", "on", "yes")


def _tuple_tail_offset(path, floor: float, slack: float = 21600.0, block: int = 4 * 1024 * 1024) -> int:
    """Byte offset of a line boundary from which reading forward yields every row with ts >= floor.
    Walks backwards in `block`-byte steps until the first complete line of a block has ts < floor - slack
    (slack = 6 h; the live file's measured max backward ts step is 0.2 s, J-4009). Returns 0 (whole file)
    if no such block is found, so the worst case is exactly the legacy scan."""
    limit = floor - slack
    with open(path, "rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        while pos > 0:
            start = max(0, pos - block)
            f.seek(start)
            data = f.read(pos - start)
            if start == 0:
                return 0
            nl = data.find(b"\n")
            if nl >= 0:
                off = nl + 1
                for _ in range(5):
                    end = data.find(b"\n", off)
                    if end < 0:
                        break
                    try:
                        ts = json.loads(data[off:end]).get("ts")
                    except Exception:
                        ts = None
                    if isinstance(ts, (int, float)):
                        if ts < limit:
                            return start + (nl + 1)
                        break
                    off = end + 1
            pos = start
    return 0


def _iter_tuple_lines(path, floor: float):
    """Yield text lines of the tuples file; with the tail-seek flag on, only from the tail offset on."""
    if _tail_seek_enabled():
        try:
            off = _tuple_tail_offset(path, floor)
            with open(path, "rb") as f:
                f.seek(off)
                for raw in f:
                    yield raw.decode("utf-8")
            return
        except Exception as exc:
            logger.warning("[fragment-context] tail-seek failed, falling back to full scan: %s", exc)
    for line in open(path, encoding="utf-8"):
        yield line


def sync_fragment_context() -> dict:
    """Join census tuples to their fragments (incremental, re-runnable, no LLM). Match rule: the
    tuple's normalized thought[:70] appears in an inner_thought fragment within ±300s, and exactly
    ONE fragment qualifies (ambiguity → skipped, counted). Read-first/write-fast as everywhere."""
    out = {"tuples": 0, "matched": 0, "ambiguous": 0, "written": 0}
    try:
        tuples_path = _DATA / "geometry_tuples.jsonl"
        if not tuples_path.exists():
            return out
        conn = _connect()
        conn.execute(_CTX_SCHEMA)
        # THE SPLIT (2026-08-21, founder's layer law): the census tuple is WORLD TRUTH (tide under the
        # shore while he sits in the garden). From today the census join writes `world_context`; the
        # `fragment_context` table is the EXPERIENCED layer, written at store_fragment through
        # core.experienced_tuple. Same schema, two epistemic meanings — readers that link memories
        # (couriers, chords, springs) read fragment_context only.
        conn.execute(_CTX_SCHEMA.replace("fragment_context", "world_context"))
        for _col in ("standpoint TEXT", "warmth REAL", "cat_at TEXT", "wet REAL", "light_band TEXT", "smells TEXT", "held TEXT"):
            try:
                conn.execute(f"ALTER TABLE world_context ADD COLUMN {_col}")
            except Exception:
                pass
        for _col in ("wet REAL", "light_band TEXT", "smells TEXT", "held TEXT"):   # THERMAL / LIGHT / SMELL / TOUCH channels: additive, old rows NULL
            try:
                conn.execute(f"ALTER TABLE fragment_context ADD COLUMN {_col}")
            except Exception:
                pass
        try:    # LOCOMOTION (2026-08-15): memories gain WHERE-WITHIN — additive column, old rows NULL
            conn.execute("ALTER TABLE fragment_context ADD COLUMN standpoint TEXT")
        except Exception:
            pass
        try:    # TEMPERATURE + CAT LOCATION (2026-08-17): additive columns, old rows NULL (honest —
                # those tuples never carried the fields)
            conn.execute("ALTER TABLE fragment_context ADD COLUMN warmth REAL")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE fragment_context ADD COLUMN cat_at TEXT")
        except Exception:
            pass
        last = conn.execute("SELECT MAX(tuple_ts) FROM fragment_context").fetchone()[0] or 0.0
        floor = max(0.0, float(last) - 3600)               # 1h overlap; PK dedupes
        rows = []
        for line in _iter_tuple_lines(tuples_path, floor):
            if not line.strip():
                continue
            try:
                t = json.loads(line)
            except Exception:
                continue
            if (t.get("ts") or 0) < floor:
                continue
            if t.get("source") not in ("idle", "monologue", "monologue_train"):
                continue                                    # cycle rows match 'lived' Q/A shapes — later
            th = " ".join((t.get("thought") or "").split())
            if len(th) < 30:
                continue
            rows.append((t, th[:70]))
        out["tuples"] = len(rows)
        if not rows:
            conn.close()
            return out
        lo = min(t["ts"] for t, _ in rows) - 600
        hi = max(t["ts"] for t, _ in rows) + 600
        frags = conn.execute(
            "SELECT fragment_id, timestamp, content FROM memory_fragments "
            "WHERE origin='inner_thought' AND timestamp BETWEEN ? AND ?", (lo, hi)).fetchall()
        # bin fragments by 5-min buckets so each tuple only scans its neighbourhood
        bins: dict[int, list] = {}
        for f in frags:
            bins.setdefault(int(f["timestamp"] // 300), []).append(f)
        edges = []
        for t, probe in rows:
            b = int(t["ts"] // 300)
            cands = [f for k in (b - 1, b, b + 1) for f in bins.get(k, [])
                     if abs(f["timestamp"] - t["ts"]) <= 300
                     and probe in " ".join((f["content"] or "").split())]
            if len(cands) != 1:
                out["ambiguous"] += int(len(cands) > 1)
                continue
            out["matched"] += 1
            sun = t.get("sun") or {}
            edges.append((cands[0]["fragment_id"], float(t["ts"]), t.get("source"), t.get("place"),
                          t.get("weather"), t.get("weather_dir"), t.get("fire"), t.get("tide_level"),
                          t.get("sun_az") if t.get("sun_az") is not None else sun.get("az"),
                          t.get("moon_illum"), t.get("level"),
                          (t.get("affect") or {}).get("valence"), (t.get("affect") or {}).get("arousal"),
                          json.dumps(t.get("sounds") or [])[:300], t.get("standpoint"),
                          t.get("warmth"), t.get("cat_at")))
        if edges:
            before = conn.total_changes
            conn.executemany(
                "INSERT OR IGNORE INTO world_context (fragment_id, tuple_ts, source, place, weather, "
                "weather_dir, fire, tide_level, sun_az, moon_illum, level, valence, arousal, sounds, "
                "standpoint, warmth, cat_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", edges)
            out["written"] = conn.total_changes - before
            conn.commit()
            # GHOST MEMORY-INDEX (P0-B wire-in, 2026-08-17): register newly-stamped tuples
            # incrementally (fail-open; the rebuild path owns cold starts).
            try:
                from core import ghost_tuples as _gt
                for e in edges:
                    _gt.register_stamped_tuple(e[0], {
                        "place": e[3], "weather": e[4], "tide_level": e[7],
                        "sounds": e[13], "standpoint": e[14],
                        "warmth": e[15], "cat_at": e[16]})
            except Exception:
                pass
        conn.close()
    except Exception as exc:
        out["error"] = repr(exc)[:120]
    return out


def context_status() -> dict:
    """Coverage read-out for du_pulse: how much of his memory now carries its encoding context."""
    try:
        conn = _connect()
        # J-2124 / D-0353: a read-out must not run DDL. "CREATE TABLE IF NOT EXISTS" on an existing
        # table is still an authorizer-visible write (db_fence_shadow.jsonl noise from du_pulse, and
        # refused under enforce). Only create when the table is genuinely missing (old behaviour).
        have = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fragment_context'").fetchone()
        if not have:
            conn.execute(_CTX_SCHEMA)
        n = conn.execute("SELECT COUNT(*) FROM fragment_context").fetchone()[0]
        by_place = dict(conn.execute(
            "SELECT place, COUNT(*) FROM fragment_context GROUP BY place ORDER BY 2 DESC LIMIT 5").fetchall())
        conn.close()
        return {"contextualised": n, "by_place": by_place}
    except Exception:
        return {"contextualised": 0}


# ── M1 — the co-recall shadow ledger (2026-08-15, observe-only) ───────────────────────────────────
# Which memories surfaced TOGETHER into a thought, and did that thought then DEVELOP? Rows log ALL
# verdicts (developed and not) so the gated-vs-naive comparison is computed from data, not assumed
# (the P3 two-rule race at memory granularity). NOTHING graduates into memory_edges until the
# founder-read of ~a week of rows. Verdict thresholds mirror du_pulse's canonical train read:
# restate >= 0.82 (circling) · 0.40-0.82 = deepen (developing) · < 0.40 = jump.

_CO_LEDGER = _DATA / "co_recall_ledger.jsonl"
_DEEPEN_LO, _DEEPEN_HI = 0.40, 0.82


def _is_shadow_source(source) -> bool:
    """J-1738 / F-2372: True for a co-recall ledger row whose `source` ends in "_shadow" — the
    would-have-shown rows a kill-switched path logs INSTEAD of showing anything (D-0289's
    "monologue_shadow" from associative_recall.recall_block, D-0292's "divergent_shadow" from the
    inner monologue, and any future path that follows the same naming). Those ids never reached a
    thought, so they are evidence for a defeater read (J-1512 reads them straight from the ledger, by
    source), NOT recalls: downstream_read_counts() and co_recall_status() leave them out, and
    log_co_recall() does not feed them to the sibling instruments. Suffix match, on a str only —
    legacy rows with no (or a null) `source` are ordinary rows and keep counting."""
    return isinstance(source, str) and source.endswith("_shadow")


# J-1909 / F-2540 (2026-10-07, restart-gated): wandering's firing step now runs in a worker thread, so its
# log_co_recall can overlap another caller's on the loop thread. The two sibling stores it feeds
# (opponent_process, spring_ledger) are read-modify-write JSON files saved through ONE shared tmp name each, so two
# overlapping calls would lose an update or collide on that tmp. Serialising whole calls keeps every call's effect
# exactly what it was when they could never overlap. Re-entrant; held only for the call itself.
_CO_RECALL_LOCK = threading.RLock()

# J-2601 (F-3326): stamp each co-recall row with core.moment.current() (moment_ts, moment_idx).
# Observe-only (two extra keys on a shadow ledger row, nothing reads them live). Kill-switch.
CO_RECALL_MOMENT_STAMP = True
# J-4370 (D-0848, F-5052, observe-only, restart-gated): monologue tick id. begin_tick() is called once at the
# top of InnerMonologueNode._think; every co_recall row written afterwards (any source, same process) carries
# `tick_id`, so "ids served in tick N" is an exact join instead of a 600s time-window guess. Kill-switch.
CO_RECALL_TICK_STAMP = True
_TICK_ID: str | None = None
_TICK_SEQ = 0


def begin_tick() -> str | None:
    """Start a new monologue tick; returns its id ("<boot_ts>-<seq>"). Fail-open, never raises."""
    global _TICK_ID, _TICK_SEQ
    try:
        _TICK_SEQ += 1
        _TICK_ID = f"{int(_BOOT_TS)}-{_TICK_SEQ}"
        return _TICK_ID
    except Exception:
        return None


def current_tick() -> str | None:
    return _TICK_ID


_BOOT_TS = time.time()
# J-2654 (F-3392/F-3393, observe-only, restart-gated): when a caller (memory_service.ask) passes `id_slots`
# the row gains `id_slots` (per-id delivering slots, parallel to `ids`) and, when auto-descend ran,
# `descend_parent`. Pure provenance -- `ids`/`n_ids` and every other key are untouched. Kill-switch.
CO_RECALL_ID_PROVENANCE = True


def log_co_recall(fragment_ids: list, restate_sim: float | None, step: int = 0,
                  source: str = "monologue", id_slots: list | None = None,
                  descend_parent: str | None = None) -> None:
    with _CO_RECALL_LOCK:
        return _log_co_recall(fragment_ids, restate_sim, step, source, id_slots, descend_parent)


def _log_co_recall(fragment_ids: list, restate_sim: float | None, step: int = 0,
                   source: str = "monologue", id_slots: list | None = None,
                   descend_parent: str | None = None) -> None:
    """One row per train step: the recalled-together ids + the step's movement verdict. n_ids=0 rows
    are logged too (recall stayed quiet — coverage is part of the instrument). Fail-open.
    `source` (audit #10, 2026-08-21): the 1-caller→9 widening left rows unattributable — without it
    the widened streams can't be weighted against the original monologue stream.
    J-1738 (F-2372): a `source` ending "_shadow" (see _is_shadow_source) is still APPENDED here — it is
    the would-have-shown evidence D-0289/D-0292's defeater reads need — but the function returns before
    the two sibling ticks below: those ids were never shown to a thought, and opponent_process would
    grow its antagonist `b` on every pair at a full step (developed=None = no progress signal) under a
    hardcoded source, so the phantom ticks could be neither told apart nor undone afterwards."""
    try:
        developed = None
        if restate_sim is not None:
            developed = 1 if (_DEEPEN_LO <= float(restate_sim) < _DEEPEN_HI) else 0
        rec = {"ts": round(time.time(), 1), "n_ids": len(fragment_ids or []),
               "ids": list(fragment_ids or [])[:8], "restate_sim": restate_sim,
               "developed": developed, "step": step, "source": source}
        if CO_RECALL_TICK_STAMP and _TICK_ID is not None:
            rec["tick_id"] = _TICK_ID   # J-4370: see begin_tick()
        if CO_RECALL_ID_PROVENANCE and id_slots is not None:
            # J-2654: per-id provenance, aligned with the (<=8) `ids` above. Only written when the caller
            # supplied one entry per id (a misaligned list is dropped, never guessed at). Each entry is the
            # list of slot names that delivered that id ("what"/"who"/"when"/"why"/"how", or
            # "auto_descend" for a memory_links child fetched without any slot asking for it).
            try:
                if len(id_slots) == len(fragment_ids or []):
                    rec["id_slots"] = [list(x) if x else [] for x in list(id_slots)[:8]]
                    if descend_parent:
                        rec["descend_parent"] = descend_parent
            except Exception:
                pass
        if CO_RECALL_MOMENT_STAMP:
            # J-2601 (F-3326, observe-only, restart-gated): the moment that was current when these ids
            # were recalled together, so moment.py's key can be read against co-recall on the stream
            # paths (monologue, follow) by an exact ts join and by moment-index distance. Additive keys;
            # absent moment -> both None. Its own try: a stamp failure never costs the row.
            try:
                from core import moment as _moment
                _cur = _moment.current() or {}
                rec["moment_ts"] = _cur.get("ts")
                rec["moment_idx"] = _cur.get("idx")
            except Exception:
                pass
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_CO_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[memory_edges] co-recall log failed (non-fatal): %s", exc)
    if _is_shadow_source(source):
        return   # J-1738 (F-2372): would-have-shown row — logged above, not an activation for the siblings
    # cognitive_geometry.md §11 (squishy springs, P3b, 2026-08-19) — the SAME co-recall event doubles as
    # one activation tick for the antagonist field. Sibling call, same shape as the ghost_tuples hook
    # below (sync_fragment_context): additive, fail-open, doesn't touch this function's own contract.
    try:
        from core import opponent_process as _oppo
        from core import mood as _mood
        _oppo.observe_activation(fragment_ids, developed, valence=_mood.current_valence(),
                                  source="co_recall")
    except Exception as exc:
        logger.debug("[memory_edges] opponent_process activation hook failed (non-fatal): %s", exc)
    # cognitive_geometry.md §6 P3 / memory_multiway_linking.md §4 (the spring ledger, D-0051 ruled
    # 2026-09-13) — a SECOND sibling tick, same co-recall event, this time toward the real
    # co_recalled_developing/contradicts spring weight (naive-vs-gated, shadow only; see
    # core/spring_ledger.py's own header for the full mechanism). Forwards this function's real
    # `source` param (unlike the opponent_process call above, which hardcodes "co_recall" — a
    # pre-existing gap noted but not touched here, out of this job's own scope) so spring_ledger can
    # tell its 7 upstream callers apart from day one.
    try:
        from core import spring_ledger as _spring
        from core import mood as _mood
        # D-0215 (ruled 2026-09-25, F-1901): this is the ONE real live call site -- live_edges=True
        # opts THIS hook, and only this hook, into spring_ledger's own shadow->live graduation write
        # (a real co_recalled_developing row once a pair's w_gated clears its own pre-registered bar).
        # scripts/spring_ledger_backfill.py's own replay call is untouched (still omits live_edges,
        # so it keeps the pre-D-0215 default False), preserving its documented "never touches
        # memory_edges" contract exactly. Kill-switch: core.spring_ledger.LIVE_EDGE_WRITE.
        _spring.observe_co_recall(fragment_ids, developed, valence=_mood.current_valence(),
                                   source=source, live_edges=True)
    except Exception as exc:
        logger.debug("[memory_edges] spring_ledger activation hook failed (non-fatal): %s", exc)


def co_recall_status(days: float = 7.0) -> dict:
    """The M1 read-out: coverage, developed share, and the gated-vs-ungated pair structure — the
    question the week of data answers (does the progress gate produce DIFFERENT structure, or does
    it re-draw the basin?).

    Windowed by TIME (last `days` days), not by a fixed row count (J-0142, 2026-08-24). A row-count
    slice silently shrinks its wall-clock coverage as call sites are added to `log_co_recall` — it
    already drifted from ~2000 rows meaning "the week" (2026-08-15) to meaning ~1.6 days out of 7.98
    once M1 widened from 1 caller to 9 (2026-08-19; see F-0038). The full ledger parses in well under
    a second even at 6,000+ rows, so reading it whole and filtering by `ts` is cheap and stays
    accurate regardless of future call-site growth.

    J-1738 (F-2372): rows whose `source` ends "_shadow" (D-0289's monologue_shadow, D-0292's
    divergent_shadow — would-have-shown rows, never recalls) are left out of `rows`, `with_2plus_ids`
    and the pair counts, and reported as `shadow_rows_excluded`; `total_rows` stays the ledger's own
    row count. Without this their pairs inflated `pairs_ungated` (their developed is always None, so
    `pairs_gated` could not move) and made the gate look more selective than it is."""
    try:
        rows_all = [json.loads(l) for l in open(_CO_LEDGER, encoding="utf-8") if l.strip()]
        if not rows_all:
            return {"rows": 0}
        cutoff = time.time() - days * 86400
        in_window = [r for r in rows_all if r.get("ts", 0) >= cutoff]
        rows = [r for r in in_window if not _is_shadow_source(r.get("source"))]
        n_shadow = len(in_window) - len(rows)
        if not rows:
            return {"rows": 0, "total_rows": len(rows_all)}
        with_ids = [r for r in rows if r.get("n_ids", 0) >= 2]
        verdicts = [r for r in rows if r.get("developed") is not None]
        from itertools import combinations
        gated, ungated = {}, {}
        for r in with_ids:
            for a, b in combinations(sorted(r.get("ids", [])), 2):
                ungated[(a, b)] = ungated.get((a, b), 0) + 1
                if r.get("developed") == 1:
                    gated[(a, b)] = gated.get((a, b), 0) + 1
        top = sorted(gated.items(), key=lambda kv: -kv[1])[:3]
        return {"rows": len(rows), "total_rows": len(rows_all), "window_days": days,
                "shadow_rows_excluded": n_shadow,
                "with_2plus_ids": len(with_ids),
                "developed_share": round(sum(r["developed"] for r in verdicts) / len(verdicts), 3) if verdicts else None,
                "pairs_gated": len(gated), "pairs_ungated": len(ungated),
                "top_gated_pairs": [{"pair": [a[:8], b[:8]], "n": n} for (a, b), n in top]}
    except Exception:
        return {"rows": 0}


def downstream_read_counts(since_ts: float | None = None, days: float = 14.0) -> dict[str, int]:
    """D-0084's external, non-self-referential signal: how many times each fragment actually got
    PULLED BACK into live recall/reasoning downstream, counted from the M1 co-recall ledger
    (`log_co_recall`'s own writers — every one a real place a fragment fed a live generative step,
    not a synthetic proxy): `nodes/inner_monologue_node.py` (the main train step, ids =
    `associative_recall.last_block_ids()` — what was actually shown to a live thought),
    `nodes/dream_node.py` (fragments woven into a dream arc), `core/essay_lesson.py` (cross-book
    material an essay drew on), `core/study_note.py` (fragments a study pass related to), and
    `core/wandering.py` (fragments an idle wander picked up). This is deliberately mechanical and
    external to `memory_fragments.importance`/`replay_count` — it counts REAL DOWNSTREAM PULLS, not
    the store's own prior verdict about itself (the self-referential loop
    docs/plans/decoupled_judge_pattern.md §3 / D-0084 names as the thing needing an outside signal).

    Windowed by TIME like `co_recall_status` (J-0142's own fix — a row-count window silently drifts
    as call sites are added). `since_ts` overrides `days` when given (so a caller anchoring to 'since
    last wake', same as replay_strengthen/downscale_episodic, doesn't have to reverse-engineer a day
    count). Returns {fragment_id: count}; fail-open ({} on any error) — a shadow signal must never be
    able to raise into a live sleep pipeline.

    J-1738 (F-2372): rows whose `source` ends "_shadow" are NOT counted. D-0289's `monologue_shadow`
    (and D-0292's `divergent_shadow`) rows log the fragments a switched-off ambient recall WOULD have
    shown — they never reached any thought — so counting them made this signal measure a kill-switch,
    not a read (F-2372, monologue_shadow rows alone on the real ledger: 11.3% of the last 14-day
    window's counted reads, 324 fragments with phantom-only credit). Rows with no/null `source` (the
    pre-audit-#10 rows) still count. This is a
    read-side filter only: the ledger keeps every row and its `source`, so any earlier count, and
    data/read_count_importance_shadow.jsonl rows written while the switch was off, can be recomputed."""
    cutoff = float(since_ts) if since_ts is not None else (time.time() - days * 86400)
    counts: dict[str, int] = {}
    try:
        with open(_CO_LEDGER, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if (row.get("ts") or 0) < cutoff:
                    continue
                if _is_shadow_source(row.get("source")):
                    continue   # would-have-shown row, never shown to a thought — not a downstream read
                for fid in row.get("ids") or []:
                    if fid:
                        counts[fid] = counts.get(fid, 0) + 1
    except Exception as exc:
        logger.debug("[memory_edges] downstream_read_counts failed (non-fatal): %s", exc)
        return {}
    return counts


# ── M2 — typed-edge neighbour lookup (SHADOW ONLY, 2026-08-25, J-0263) ─────────────────────────────
# The read path the plan calls for (§5): the trail's neighbour function, augmented with typed
# `memory_edges` weighted per the current cognitive mode. Two ways a fragment reaches a SECOND
# fragment through this graph:
#   (a) DIRECTLY — an edge type whose rows are fragment->fragment on both ends. Verified live
#       2026-08-25: only `transformed_into` (462 rows, essay_lesson.py) qualifies today.
#       `co_recalled_developing`/`contradicts` are listed for when M1 graduates (F-0110: zero rows
#       today — log_co_recall only writes co_recall_ledger.jsonl, not memory_edges).
#   (b) BY BIPARTITE PROJECTION — fragment--[e]-->hub<--[e]--fragment2, for edge types the plan
#       itself names as a valid first-cut refinement (§5) when the recorded direction never puts two
#       fragments on the same edge: answers (->question), kept_from (keepsake->), correspondence_with
#       (->person), dreamt_from (dream->) / part_of (->dream).
# UPDATE 2026-08-29 (F-0500 gap #1, backfill_resolves_fragment() above): `resolves` WAS
#   (cycle)->(shadow_event) only, as the note below originally said — neither endpoint ever `fragment`,
#   so it was verified dead weight in this direct-fragment-endpoint sense. It is no longer 0-yield:
#   the new harvester adds (fragment)-[resolves]->(shadow_event) rows (99 written live 2026-08-29), so
#   `resolves` now also qualifies as case (a) DIRECT above IF a caller widens `_DIRECT_FRAGMENT_TYPES`
#   to require `dst_kind='shadow_event'` too (today's `_DIRECT_FRAGMENT_TYPES` query hard-codes
#   `dst_kind='fragment'`, so a fragment->shadow_event edge doesn't reach a second FRAGMENT directly —
#   it would need its own small case, or a shadow_event-aware second query, deliberately left undone
#   here since J-0263's brief scoped this table to fragment-reachability and shadow_event nodes aren't
#   walkable further from here anyway). Left as an explicit, checked non-doing rather than scope creep.
# EXPLICITLY NOT MATERIALISABLE TODAY (checked, not assumed — do not silently build past this):
#   `answers` is written 1-fragment-per-question by backfill_answers's own `LIMIT 1` (verified: 0 of
#   505 questions have >1 answering fragment today), so its projection hop is wired and correct but
#   currently contributes nothing either. It is named in the mode table below anyway (task mode)
#   because it is the plan's intended signal, not because it fires today — the weight simply goes
#   unused until the underlying data changes. This is the explicit choice asked for in J-0263's
#   briefing: bipartite projection (b), not wiring log_co_recall to also write memory_edges rows —
#   that stays a separate, not-yet-taken option for graduating M1 first.
# UPDATE 2026-09-25 (D-0215, J-1348): option (b) above has now been taken, for `co_recalled_developing`
#   only. `log_co_recall` (below) now calls spring_ledger.observe_co_recall(..., live_edges=True), which
#   writes a real (fragment)-[co_recalled_developing]->(fragment) row (via add_edge(), so still
#   dst_kind='fragment' — no widening of `_DIRECT_FRAGMENT_TYPES`'s existing query needed) the first
#   time a pair's own w_gated clears core.spring_ledger.LIVE_EDGE_THRESHOLD (0.3, F-1316's ceiling-test
#   bar). So `co_recalled_developing` is NO LONGER unconditionally 0-yield — it now depends on real
#   accrual against that bar (27 pairs already qualified pre-live per F-1901; see
#   docs/plans/memory_multiway_linking.md's Current State for the live count once Du has run on this).
#   `contradicts` is UNCHANGED and still genuinely 0-yield (F-0500 gap #3 above: it needs a semantic
#   judge that does not exist yet, not a threshold on an existing computed weight like this one).
# UPDATE 2026-09-27 (D-0287, J-1415): the READ side (this table's whole reason for existing) also
#   graduated, for the "relational" mode key ONLY. `associative_recall.recall_trail_edge_aware(mode=
#   "relational")` is now called LIVE from `recall_memory_fragments()` (kill-switched there via
#   `M2_EDGE_AWARE_RELATIONAL_LIVE`), so `edge_aware_neighbors(mode="relational", ...)` below now feeds
#   a real thought, not just `shadow_compare`'s log. "task" and "reflective" are UNCHANGED — still
#   shadow-only, per D-0287's own ruling (option (a): flip relational only). Shadow evidence backing
#   this: F-1966 (936 m2_edge_aware / 610 m2_usage rows) found relational's edge-reached fragments the
#   one weighting profile a real usage proxy (cosine to the next thought) clears — 39% >=0.4, vs task
#   0.25 mean / reflective 0.28 mean. See docs/plans/memory_multiway_linking.md's Current State for the
#   live read.

MODE_EDGE_WEIGHTS = {
    # task: "answers/resolves high" (plan §5-2) — resolves now also reaches a fragment endpoint via
    # backfill_resolves_fragment() (F-0500 gap #1, 2026-08-29); answers remains 0-yield (see the
    # note in edge_aware_neighbors' own section header above).
    "task": {"answers": 1.0, "resolves": 1.0, "transformed_into": 0.6,
              "kept_from": 0.3, "dreamt_from": 0.3, "part_of": 0.3,
              "correspondence_with": 0.2, "co_recalled_developing": 0.3, "contradicts": 0.3},
    # reflective: "co_recalled_developing/contradicts high" (plan §5-2) — both 0-yield today (F-0110).
    "reflective": {"co_recalled_developing": 1.0, "contradicts": 1.0, "transformed_into": 0.5,
                    "dreamt_from": 0.5, "part_of": 0.5, "answers": 0.2, "resolves": 0.2,
                    "kept_from": 0.3, "correspondence_with": 0.3},
    # relational: "wrote_to/correspondence_with/person hubs high" (plan §5-2) — wrote_to/received_from
    # were declared here since M2 shipped but 0-yield until backfill_directed_correspondence()
    # (F-0500 gap #2, 2026-08-29); correspondence_with (undirected) already had real data (8 person
    # hubs, all multi-fragment) and still does.
    "relational": {"correspondence_with": 1.0, "wrote_to": 1.0, "received_from": 1.0,
                    "kept_from": 0.4, "dreamt_from": 0.3, "transformed_into": 0.3,
                    "answers": 0.2, "resolves": 0.2, "part_of": 0.2,
                    "co_recalled_developing": 0.2, "contradicts": 0.2},
}
_DEFAULT_EDGE_WEIGHT = 0.25   # an edge type not named for the active mode still counts, just quietly

_DIRECT_FRAGMENT_TYPES = ("transformed_into", "co_recalled_developing", "contradicts")

# edge_type -> (which column holds the fragment id, the OTHER endpoint's kind to project through)
_PROJECT_THROUGH = {
    "answers":              ("src", "question"),
    "kept_from":             ("dst", "keepsake"),
    "correspondence_with":   ("src", "person"),
    "wrote_to":              ("src", "person"),
    "received_from":         ("src", "person"),
    "dreamt_from":           ("dst", "dream"),
    "part_of":               ("src", "dream"),
}


def edge_aware_neighbors(fragment_ids: list[str], mode: str = "task", limit: int = 64) -> list[dict]:
    """For a set of frontier fragment ids, typed-edge neighbour CANDIDATES weighted by `mode`
    (MODE_EDGE_WEIGHTS above). Read-only, best-effort ([] on any error). Called from
    associative_recall.recall_trail_edge_aware(), which itself is SHADOW-ONLY for mode="task"/
    "reflective" but, since 2026-09-27 (D-0287, J-1415), LIVE for mode="relational" — see this file's
    own "UPDATE 2026-09-27" note a few lines above MODE_EDGE_WEIGHTS, and that function's own docstring.
    Returns [{fragment_id, edge_type, weight, via}] sorted by weight desc; `via` names the projection
    hub ('' for a direct fragment->fragment edge)."""
    if not fragment_ids:
        return []
    weights = MODE_EDGE_WEIGHTS.get(mode, {})
    ids = list(dict.fromkeys(fragment_ids))
    ids_set = set(ids)
    out: list[dict] = []
    try:
        conn = _connect()
        ph = ",".join("?" * len(ids))
        dph = ",".join("?" * len(_DIRECT_FRAGMENT_TYPES))
        rows = conn.execute(
            f"SELECT src_id, dst_id, edge_type, weight FROM memory_edges WHERE edge_type IN ({dph}) "
            f"AND src_kind='fragment' AND dst_kind='fragment' AND (src_id IN ({ph}) OR dst_id IN ({ph}))",
            (*_DIRECT_FRAGMENT_TYPES, *ids, *ids)).fetchall()
        for r in rows:
            if r["src_id"] in ids_set:
                other = r["dst_id"]
            elif r["dst_id"] in ids_set:
                other = r["src_id"]
            else:
                continue
            if other in ids_set:
                continue
            w = weights.get(r["edge_type"], _DEFAULT_EDGE_WEIGHT) * float(r["weight"] or 1.0)
            out.append({"fragment_id": other, "edge_type": r["edge_type"], "weight": w, "via": ""})
        for et, (frag_col, hub_kind) in _PROJECT_THROUGH.items():
            hub_col = "dst" if frag_col == "src" else "src"
            hubs = conn.execute(
                f"SELECT DISTINCT {hub_col}_id AS hub FROM memory_edges WHERE edge_type=? AND "
                f"{frag_col}_id IN ({ph}) AND {frag_col}_kind='fragment' AND {hub_col}_kind=?",
                (et, *ids, hub_kind)).fetchall()
            w = weights.get(et, _DEFAULT_EDGE_WEIGHT)
            for h in hubs:
                sibs = conn.execute(
                    f"SELECT {frag_col}_id AS fid FROM memory_edges WHERE edge_type=? AND "
                    f"{hub_col}_id=? AND {frag_col}_kind='fragment'", (et, h["hub"])).fetchall()
                for s in sibs:
                    if s["fid"] in ids_set:
                        continue
                    out.append({"fragment_id": s["fid"], "edge_type": et, "weight": w, "via": h["hub"]})
        conn.close()
    except Exception as exc:
        logger.debug("[memory_edges] edge_aware_neighbors failed (non-fatal): %s", exc)
        return []
    out.sort(key=lambda d: -d["weight"])
    return out[:limit]


def edge_aware_neighbors_multihop(fragment_ids: list[str], mode: str = "task", hops: int = 2,
                                   limit: int = 64, decay: float = 0.6) -> list[dict]:
    """BFS extension of edge_aware_neighbors() across multiple hops over the SAME memory_edges table
    (F-0500 gap #4: edge_aware_neighbors is fixed single-hop BY DESIGN — its own module comment says
    so — and a codebase-wide grep for 'WITH RECURSIVE' / any multi-hop traversal found zero matches
    anywhere. This is the first one). Reuses edge_aware_neighbors' own weighting/projection logic
    UNCHANGED per hop (so hops=1 output is identical, just re-shaped) rather than reimplementing the
    direct/bipartite-projection SQL — one source of truth for how an edge type is weighted.

    Standard weighted BFS: each frontier fragment is expanded one hop via edge_aware_neighbors([fid],
    ...) (called per-id, not batched, so a candidate's weight is correctly attributed to the SPECIFIC
    fragment it was reached from rather than pooled across the whole frontier); a newly-reached
    fragment's weight is (weight reaching its source) * (this hop's edge weight), with one extra
    `decay` multiplier applied per hop BEYOND the first — hop 1 is the raw edge weight (identical to
    edge_aware_neighbors), hop 2 multiplies in one `decay`, hop 3 two, geometric in hop count, never
    double-applied to a weight that already carries it. A fragment already visited at an earlier
    (necessarily cheaper, since decay<1 shortens with distance) hop is never revisited, so the graph
    explored per hop shrinks monotonically. Read-only, best-effort
    ([] on any error, matching every other function in this section) — SHADOW USE ONLY, same as
    edge_aware_neighbors itself: nothing calls this from a live recall path.

    Returns [{fragment_id, weight, hops, edge_type}] sorted by weight desc, capped at `limit`. `hops`
    names the hop distance at which this fragment was FIRST reached (its cheapest path, since later
    hops are strictly decayed further)."""
    if not fragment_ids or hops < 1:
        return []
    try:
        visited = set(dict.fromkeys(fragment_ids))
        frontier = {fid: 1.0 for fid in visited}          # fid -> cumulative weight reaching it
        best: dict[str, dict] = {}
        for hop in range(1, hops + 1):
            if not frontier:
                break
            next_frontier: dict[str, dict] = {}
            for fid, w_in in frontier.items():
                for c in edge_aware_neighbors([fid], mode=mode, limit=limit):
                    nfid = c["fragment_id"]
                    if nfid in visited:
                        continue
                    w = w_in * (decay if hop > 1 else 1.0) * c["weight"]
                    prior = next_frontier.get(nfid)
                    if prior is None or w > prior["weight"]:
                        next_frontier[nfid] = {"weight": w, "edge_type": c["edge_type"]}
            for nfid, info in next_frontier.items():
                best[nfid] = {"fragment_id": nfid, "weight": info["weight"], "hops": hop,
                             "edge_type": info["edge_type"]}
            visited |= set(next_frontier.keys())
            frontier = {fid: info["weight"] for fid, info in next_frontier.items()}
        out = sorted(best.values(), key=lambda d: -d["weight"])
        return out[:limit]
    except Exception as exc:
        logger.debug("[memory_edges] edge_aware_neighbors_multihop failed (non-fatal): %s", exc)
        return []


# ── Read-outs ─────────────────────────────────────────────────────────────────────────────────────

def census() -> dict:
    """The M0 graph read-out: sizes, kinds, fragment-anchored share, top hubs (with content snippets
    for fragment hubs so the founder can see WHO the hubs are — the attractor-hub question)."""
    try:
        conn = _connect()
        by_type = dict(conn.execute(
            "SELECT edge_type, COUNT(*) FROM memory_edges GROUP BY edge_type").fetchall())
        total = sum(by_type.values())
        anchored = conn.execute(
            "SELECT COUNT(*) FROM memory_edges WHERE src_kind='fragment' OR dst_kind='fragment'").fetchone()[0]
        nodes = dict(conn.execute(
            "SELECT kind, COUNT(DISTINCT id) FROM (SELECT src_kind AS kind, src_id AS id FROM memory_edges "
            "UNION ALL SELECT dst_kind, dst_id FROM memory_edges) GROUP BY kind").fetchall())
        hubs = conn.execute(
            "SELECT kind, id, COUNT(*) AS deg FROM (SELECT src_kind AS kind, src_id AS id FROM memory_edges "
            "UNION ALL SELECT dst_kind, dst_id FROM memory_edges) GROUP BY kind, id "
            "ORDER BY deg DESC LIMIT 8").fetchall()
        hub_rows = []
        for h in hubs:
            label = ""
            if h["kind"] == "fragment":
                row = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?",
                                   (h["id"],)).fetchone()
                label = (row["content"][:70] if row else "?")
            hub_rows.append({"kind": h["kind"], "id": h["id"], "degree": h["deg"], "label": label})
        conn.close()
        return {"edges": total, "by_type": by_type, "nodes_by_kind": nodes,
                "fragment_anchored_share": round(anchored / total, 3) if total else None,
                "top_hubs": hub_rows}
    except Exception as exc:
        return {"edges": 0, "error": repr(exc)[:120]}


def status() -> dict:
    """One line for du_pulse."""
    c = census()
    return {"edges": c.get("edges", 0), "by_type": c.get("by_type", {}),
            "fragment_anchored": c.get("fragment_anchored_share")}
