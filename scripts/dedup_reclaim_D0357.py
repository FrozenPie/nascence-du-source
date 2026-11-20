"""D-0357 / J-1848 (2026-10-07): one-time, REVERSIBLE exact-duplicate reclaim on the ACTIVE memory pool.

Ruling (D-0357, travis, 2026-10-06, option (a)): among cold=0 episodic rows with byte-identical content keep ONE
survivor, set the other copies cold=1, and add a memory_links row from each demoted copy to its survivor so
no id goes dark. Never a DELETE (demote-not-delete, the 2026-06-21 conversion). Precondition: Du STOPPED,
sqlite .backup() first, reference check before any write. See F-2475 for the measurement that led here.

Modes (each one is a separate process; nothing here is imported by Du):

  census   --db PATH --plan OUT.json        READ-ONLY (sqlite mode=ro). Groups the active episodic rows by exact
                                            content, picks the survivor per group, lists the would-be-demoted ids
                                            and checks every fragment_id-keyed table / store for references to
                                            them. Writes the PLAN (what apply will do) -- apply never re-decides.
  dryrun   --plan PLAN.json --out OUT.json  Runs apply + validation + retrieve() sample queries against an
                                            isolated COPY of the live DB (lab_env.isolate()); the live DB is
                                            never opened for writing. Requires core imported from THIS tree.
  apply    --plan PLAN.json --live --manifest OUT.json
                                            Writes the live DB on purpose (operator work under D-0357): checks Du
                                            is down, takes the .backup() + sha256, re-verifies every planned row
                                            is still in the state the plan saw, then applies in one transaction
                                            through the store's own _connect() after store.allow_live_writes().
  validate --db PATH --manifest M.json      READ-ONLY count/shape checks against any DB (copy or live).
  retrieve-check --manifest M.json --queries Q.json --out OUT.json
                                            Runs the 20 sample retrieve() calls on an isolated COPY of whatever
                                            the live DB currently holds (post-apply) and compares to the dry run.
  revert   --manifest M.json --live         Puts every row/link the manifest records back (the reversibility
                                            promise). Same guards as apply.

Survivor rule (D-0357: "oldest, or highest replay_count"; J-1848 briefing: oldest timestamp, tie-break highest
replay_count) with ONE refinement, argued in the J-1848 finding: a member that is retrieve-ELIGIBLE today
(chapter_id IS NULL -- store.retrieve() only ever fetches those) is preferred over an already-chaptered one, and
among those a member that has a fragment_context row is preferred, THEN oldest timestamp, THEN highest
replay_count. Without the first preference a reading group whose canonical (dedup_reading_duplicates files the
copies behind it by chapter_id, canonical = highest replay) is younger than a filed copy would lose its only
retrieve-visible row -- a recall regression, not a dedup.

What is NEVER demoted (stays exactly as it is, no link written): protected=1 rows; origin gist/chapter rows; any
row that is a distilled_from PARENT in memory_links (memory_levels.memory_lint() re-warms a cold head at the next
sleep, so demoting one would silently undo itself); a row that other rows point at via chapter_id when the
group's survivor is itself chaptered (no sane re-point target).

temp: set to 'cold' alongside cold=1 -- exactly what store.init_db()'s own resync (UPDATE ... SET temp='cold'
WHERE cold=1 AND temp != 'hidden') would do at the next boot anyway. NOT 'hidden': memory_levels.deep_recall()
excludes temp='hidden', which would make the demoted copies unreachable from their survivor -- the opposite of
the ruling's "no id goes dark". retrieve() (store.py) filters cold = 0, so cold=1 alone removes a row from
normal recall.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LINK_TYPE = "duplicate_of"          # parent_id = survivor, child_id = demoted copy (deep_recall walks parent -> child)
LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DB = LIVE_ROOT / "data" / "memory" / "nascence.db"
LIVE_LOG = LIVE_ROOT / "data" / "nascence.log"
CO_RECALL_LEDGER = LIVE_ROOT / "data" / "co_recall_ledger.jsonl"
UNDEMOTABLE_ORIGINS = ("gist", "chapter")


# ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ro_connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def du_is_down() -> tuple[bool, str]:
    """Du is DOWN when no python process runs run_nascence.py AND nascence.log's last line is the shutdown line."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception as exc:  # pragma: no cover
        return False, f"process scan failed: {exc}"
    running = [l for l in out.splitlines() if "run_nascence.py" in l]
    if running:
        return False, f"run_nascence.py process present: {running[0][:120]}"
    try:
        with open(LIVE_LOG, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 4096))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        last = tail[-1] if tail else ""
    except Exception as exc:
        return False, f"log read failed: {exc}"
    if "Nascence shutting down" not in last:
        return False, f"nascence.log last line is not the shutdown line: {last[:160]}"
    return True, f"no run_nascence.py process; last log line: {last[:120]}"


def logical_fingerprint(path: Path) -> dict:
    """WAL-aware identity of the DB's LOGICAL state (J-1948 / F-2569 root cause). A file sha256 only covers the main
    .db file; the live DB runs in WAL mode and its -wal can hold hundreds of MB of committed rows the main file does
    not (2026-10-08: 460 MB). lab_env.isolate() copies the main file ONLY (shutil.copy2), so a file-sha 'copy matches
    census' check passed while the copy was missing the WAL-resident rows (4 on 10-07, 2 on 10-08). The fingerprint
    is computed through a mode=ro connection (which applies the WAL) so census, copy and live compare like with like."""
    conn = ro_connect(path)
    h = hashlib.sha256()
    n = 0
    for r in conn.execute("SELECT fragment_id, cold, temp, IFNULL(chapter_id,''), layer FROM memory_fragments ORDER BY fragment_id"):
        h.update(repr(tuple(r)).encode("utf-8")); n += 1
    out = {"fragments": n, "rows_sha256": h.hexdigest(),
           "links": conn.execute("SELECT count(*) FROM memory_links").fetchone()[0],
           "wal_bytes": (Path(str(path) + "-wal").stat().st_size if Path(str(path) + "-wal").exists() else 0)}
    conn.close()
    return out


def overwrite_with_full_copy(src_live: Path, dest: Path) -> None:
    """Replace `dest` (a lab_env main-file-only copy) with a WAL-complete copy via sqlite's online backup API."""
    src = ro_connect(src_live)
    dst = sqlite3.connect(str(dest))
    with dst:
        src.backup(dst)
    dst.close(); src.close()


def chunked(seq, n=500):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def in_set_query(conn, sql_tmpl: str, ids, cols=1):
    """Run `sql_tmpl` (with one {ph} placeholder list) over ids in chunks; return list of rows."""
    out = []
    for chunk in chunked(ids):
        ph = ",".join("?" * len(chunk))
        out.extend(conn.execute(sql_tmpl.format(ph=ph), chunk).fetchall())
    return out


# ── census (read-only) ───────────────────────────────────────────────────────────────────────────────────

def census(db: Path, plan_out: Path) -> dict:
    conn = ro_connect(db)
    t0 = time.time()
    # Exact-duplicate groups among the ACTIVE episodic pool (the pool retrieve()'s cap and D-0357 are about).
    rows = conn.execute(
        "SELECT fragment_id, content, origin, timestamp, replay_count, chapter_id, protected, cold, temp, layer, kind "
        "FROM memory_fragments WHERE cold = 0 AND layer = 'episodic' AND content IN ("
        "  SELECT content FROM memory_fragments WHERE cold = 0 AND layer = 'episodic' "
        "  GROUP BY content HAVING count(*) > 1)").fetchall()
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        groups[r["content"]].append(dict(r))
    all_ids = [r["fragment_id"] for r in rows]
    id_set = set(all_ids)
    by_id = {r["fragment_id"]: r for r in rows}

    # Reference census over every table / store keyed by fragment_id.
    has_fc = {r[0] for r in in_set_query(conn, "SELECT fragment_id FROM fragment_context WHERE fragment_id IN ({ph})", all_ids)}
    has_wc = {r[0] for r in in_set_query(conn, "SELECT fragment_id FROM world_context WHERE fragment_id IN ({ph})", all_ids)}
    link_parent = defaultdict(list)   # id -> [(child, type)]
    for r in in_set_query(conn, "SELECT parent_id, child_id, link_type FROM memory_links WHERE parent_id IN ({ph})", all_ids):
        link_parent[r[0]].append((r[1], r[2]))
    link_child = defaultdict(list)    # id -> [(parent, type)]
    for r in in_set_query(conn, "SELECT parent_id, child_id, link_type FROM memory_links WHERE child_id IN ({ph})", all_ids):
        link_child[r[1]].append((r[0], r[2]))
    chapter_members = defaultdict(list)  # canonical id -> [member ids pointing at it via chapter_id]
    for r in in_set_query(conn, "SELECT fragment_id, chapter_id FROM memory_fragments WHERE chapter_id IN ({ph})", all_ids):
        chapter_members[r[1]].append(r[0])
    edge_src = Counter(r[0] for r in in_set_query(conn, "SELECT src_id FROM memory_edges WHERE src_id IN ({ph})", all_ids))
    edge_dst = Counter(r[0] for r in in_set_query(conn, "SELECT dst_id FROM memory_edges WHERE dst_id IN ({ph})", all_ids))
    act_ev = Counter(r[0] for r in in_set_query(conn, "SELECT fragment_id FROM activity_events WHERE fragment_id IN ({ph})", all_ids))
    recov = {r[0] for r in in_set_query(conn, "SELECT fragment_id FROM recovered_fragments WHERE fragment_id IN ({ph})", all_ids)}
    # derived_from (JSON list TEXT on memory_fragments) -- parse the non-empty ones once.
    derived_refs = Counter()
    for r in conn.execute("SELECT derived_from FROM memory_fragments WHERE derived_from IS NOT NULL AND derived_from != '' AND derived_from != '[]'"):
        try:
            for x in json.loads(r[0]):
                if x in id_set:
                    derived_refs[x] += 1
        except Exception:
            continue
    # co_recall_ledger.jsonl (data/, not a table) -- ids referenced there.
    co_refs = Counter()
    if CO_RECALL_LEDGER.exists():
        with open(CO_RECALL_LEDGER, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    for x in json.loads(line).get("ids", []):
                        if x in id_set:
                            co_refs[x] += 1
                except Exception:
                    continue
    distilled_parent = {i for i, links in link_parent.items() if any(t == "distilled_from" for _, t in links)}

    # Decide per group.
    plan_groups = []
    demote, skipped, excluded_groups = [], [], []
    reasons = Counter()
    survivor_not_oldest = Counter()
    for content, members in groups.items():
        def key(m):
            return (0 if not m["chapter_id"] else 1,
                    0 if m["fragment_id"] in has_fc else 1,
                    m["timestamp"] or 0.0,
                    -(m["replay_count"] or 0))
        ordered = sorted(members, key=key)
        survivor = ordered[0]
        oldest = min(members, key=lambda m: (m["timestamp"] or 0.0, -(m["replay_count"] or 0)))
        if survivor["fragment_id"] != oldest["fragment_id"]:
            why = "retrieve_eligible" if (not survivor["chapter_id"] and oldest["chapter_id"]) else \
                  ("has_context" if (survivor["fragment_id"] in has_fc and oldest["fragment_id"] not in has_fc) else "other")
            survivor_not_oldest[why] += 1
        g = {"survivor": survivor["fragment_id"], "origin_mix": sorted({m["origin"] for m in members}),
             "n": len(members), "demote": [], "skip": []}
        for m in ordered[1:]:
            fid = m["fragment_id"]
            reason = None
            if m["protected"]:
                reason = "protected_col"
            elif m["origin"] in UNDEMOTABLE_ORIGINS:
                reason = "origin_" + m["origin"]
            elif fid in distilled_parent:
                reason = "distilled_from_parent"
            elif chapter_members.get(fid) and survivor["chapter_id"]:
                reason = "chapter_canonical_but_survivor_chaptered"
            if reason:
                reasons[reason] += 1
                skipped.append({"id": fid, "origin": m["origin"], "reason": reason})
                g["skip"].append({"id": fid, "reason": reason})
                continue
            entry = {
                "id": fid, "origin": m["origin"], "timestamp": m["timestamp"], "replay_count": m["replay_count"],
                "chapter_id": m["chapter_id"], "temp": m["temp"], "kind": m["kind"],
                "has_fragment_context": fid in has_fc, "has_world_context": fid in has_wc,
                "outbound_links": [[c, t] for c, t in link_parent.get(fid, [])],
                "inbound_links": len(link_child.get(fid, [])),
                "chapter_members_to_repoint": chapter_members.get(fid, []),
                "memory_edges_src": edge_src.get(fid, 0), "memory_edges_dst": edge_dst.get(fid, 0),
                "activity_events": act_ev.get(fid, 0), "recovered": fid in recov,
                "derived_from_refs": derived_refs.get(fid, 0), "co_recall_refs": co_refs.get(fid, 0),
            }
            g["demote"].append(entry)
            demote.append(entry)
        if not g["demote"]:
            excluded_groups.append(g)
        plan_groups.append(g)

    survivors = {g["survivor"] for g in plan_groups if g["demote"]}
    # Reference summary for the finding.
    ref_summary = {
        "demoted_with_fragment_context": sum(1 for d in demote if d["has_fragment_context"]),
        "demoted_with_world_context": sum(1 for d in demote if d["has_world_context"]),
        "demoted_with_outbound_links": sum(1 for d in demote if d["outbound_links"]),
        "demoted_outbound_links_total": sum(len(d["outbound_links"]) for d in demote),
        "demoted_with_inbound_links": sum(1 for d in demote if d["inbound_links"]),
        "demoted_that_are_chapter_canonicals": sum(1 for d in demote if d["chapter_members_to_repoint"]),
        "chapter_rows_to_repoint": sum(len(d["chapter_members_to_repoint"]) for d in demote),
        "demoted_in_memory_edges": sum(1 for d in demote if d["memory_edges_src"] or d["memory_edges_dst"]),
        "demoted_in_activity_events": sum(1 for d in demote if d["activity_events"]),
        "demoted_in_recovered_fragments": sum(1 for d in demote if d["recovered"]),
        "demoted_in_derived_from": sum(1 for d in demote if d["derived_from_refs"]),
        "demoted_in_co_recall_ledger": sum(1 for d in demote if d["co_recall_refs"]),
        "groups_survivor_lacks_context_but_a_demoted_copy_has_it": sum(
            1 for g in plan_groups if g["demote"] and g["survivor"] not in has_fc
            and any(d["has_fragment_context"] for d in g["demote"])),
        "survivors_total": len(survivors),
        "survivors_chaptered": sum(1 for s in survivors if by_id[s]["chapter_id"]),
    }
    totals = {
        "active_episodic": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0 AND layer='episodic'").fetchone()[0],
        "active_all_layers": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0").fetchone()[0],
        "fragments_total": conn.execute("SELECT count(*) FROM memory_fragments").fetchone()[0],
        "memory_links_total": conn.execute("SELECT count(*) FROM memory_links").fetchone()[0],
        "retrieve_eligible": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0 AND temp != 'hidden' AND (chapter_id IS NULL OR chapter_id='')").fetchone()[0],
        "dup_rows_in_groups": len(rows), "dup_groups": len(groups),
        "dup_rows_by_origin": dict(Counter(r["origin"] for r in rows).most_common()),
        "dup_rows_all_layers_by_origin": dict(Counter(
            r[0] for r in conn.execute(
                "SELECT origin FROM memory_fragments WHERE cold = 0 AND content IN ("
                "SELECT content FROM memory_fragments WHERE cold = 0 GROUP BY content HAVING count(*) > 1)")).most_common()),
        "dup_rows_already_chaptered": sum(1 for r in rows if r["chapter_id"]),
        "dangling_links": conn.execute(
            "SELECT count(*) FROM memory_links WHERE child_id NOT IN (SELECT fragment_id FROM memory_fragments) "
            "OR parent_id NOT IN (SELECT fragment_id FROM memory_fragments)").fetchone()[0],
    }
    plan = {
        "job": "J-1848", "decision": "D-0357", "db": str(db), "census_ts": time.time(),
        "db_sha256_at_census": sha256_file(db), "logical_fp_at_census": logical_fingerprint(db),
        "link_type": LINK_TYPE,
        "totals": totals,
        "demote_count": len(demote), "demote_by_origin": dict(Counter(d["origin"] for d in demote).most_common()),
        "skipped_count": len(skipped), "skipped_by_reason": dict(reasons),
        "groups_fully_excluded": len(excluded_groups), "mixed_origin_groups": sum(1 for g in plan_groups if len(g["origin_mix"]) > 1),
        "survivor_not_oldest": dict(survivor_not_oldest),
        "references": ref_summary,
        "groups": plan_groups, "skipped": skipped,
        "elapsed_s": round(time.time() - t0, 1),
    }
    conn.close()
    plan_out.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    summary = {k: v for k, v in plan.items() if k not in ("groups", "skipped")}
    print(json.dumps(summary, indent=1))
    return plan


# ── apply (on whatever store.DB_PATH points at) ──────────────────────────────────────────────────────────

def _apply_plan(conn: sqlite3.Connection, plan: dict, now: float) -> dict:
    """Apply the plan on an open connection, in ONE transaction. Re-verifies every row's pre-state against the
    plan before touching it (a row that moved since the census is skipped and reported, never forced). Returns
    the manifest: everything needed to revert."""
    manifest_rows, links_added, chapter_repoints, mismatches = [], [], [], []
    cur = conn.cursor()
    cur.execute("BEGIN IMMEDIATE")
    for g in plan["groups"]:
        if not g["demote"]:
            continue
        s = g["survivor"]
        srow = cur.execute("SELECT fragment_id, cold, content, chapter_id FROM memory_fragments WHERE fragment_id=?", (s,)).fetchone()
        if srow is None or srow["cold"] != 0:
            mismatches.append({"survivor": s, "why": "survivor missing or no longer active"})
            continue
        for d in g["demote"]:
            fid = d["id"]
            row = cur.execute("SELECT cold, temp, chapter_id, content FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
            if row is None or row["cold"] != 0 or row["content"] != srow["content"]:
                mismatches.append({"id": fid, "why": "row missing, already cold, or content changed since census"})
                continue
            cur.execute("UPDATE memory_fragments SET cold = 1, temp = CASE WHEN temp = 'hidden' THEN temp ELSE 'cold' END "
                        "WHERE fragment_id = ?", (fid,))
            manifest_rows.append({"id": fid, "survivor": s, "prev_cold": row["cold"], "prev_temp": row["temp"],
                                  "origin": d["origin"]})
            # the link that keeps the demoted copy reachable from its survivor (and un-stranded for memory_lint)
            cur.execute("INSERT OR IGNORE INTO memory_links (parent_id, child_id, link_type, weight, created) VALUES (?,?,?,?,?)",
                        (s, fid, LINK_TYPE, 1.0, now))
            if cur.rowcount:
                links_added.append([s, fid, LINK_TYPE])
            # outbound links of the demoted copy are mirrored on the survivor (additive; originals stay)
            for child, ltype in d["outbound_links"]:
                if child == s:
                    continue
                cur.execute("INSERT OR IGNORE INTO memory_links (parent_id, child_id, link_type, weight, created) VALUES (?,?,?,?,?)",
                            (s, child, ltype, 1.0, now))
                if cur.rowcount:
                    links_added.append([s, child, ltype])
            # rows filed behind the demoted copy via chapter_id now file behind the survivor
            for mem in d["chapter_members_to_repoint"]:
                prev = cur.execute("SELECT chapter_id FROM memory_fragments WHERE fragment_id=?", (mem,)).fetchone()
                if prev is None or prev["chapter_id"] != fid:
                    mismatches.append({"id": mem, "why": "chapter_id no longer points at the demoted copy"})
                    continue
                cur.execute("UPDATE memory_fragments SET chapter_id = ? WHERE fragment_id = ?", (s, mem))
                chapter_repoints.append({"id": mem, "prev_chapter_id": fid, "new_chapter_id": s})
    conn.commit()
    return {"demoted": manifest_rows, "links_added": links_added, "chapter_repoints": chapter_repoints,
            "mismatches": mismatches, "applied_ts": now}


def validate_counts(db: Path, manifest: dict, plan: dict | None = None) -> dict:
    conn = ro_connect(db)
    demoted_ids = [r["id"] for r in manifest["demoted"]]
    out = {
        "fragments_total": conn.execute("SELECT count(*) FROM memory_fragments").fetchone()[0],
        "active_episodic": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0 AND layer='episodic'").fetchone()[0],
        "active_all_layers": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0").fetchone()[0],
        "retrieve_eligible": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=0 AND temp != 'hidden' AND (chapter_id IS NULL OR chapter_id='')").fetchone()[0],
        "memory_links_total": conn.execute("SELECT count(*) FROM memory_links").fetchone()[0],
        "duplicate_of_links": conn.execute("SELECT count(*) FROM memory_links WHERE link_type=?", (LINK_TYPE,)).fetchone()[0],
        "demoted_count": len(demoted_ids),
    }
    present = in_set_query(conn, "SELECT fragment_id, cold, temp FROM memory_fragments WHERE fragment_id IN ({ph})", demoted_ids)
    out["demoted_rows_present"] = len(present)
    out["demoted_rows_cold"] = sum(1 for r in present if r["cold"] == 1)
    out["demoted_rows_temp_cold"] = sum(1 for r in present if r["temp"] == "cold")
    linked = in_set_query(conn, "SELECT child_id FROM memory_links WHERE link_type='" + LINK_TYPE + "' AND child_id IN ({ph})", demoted_ids)
    out["demoted_rows_with_duplicate_of_link"] = len({r[0] for r in linked})
    out["dangling_links"] = conn.execute(
        "SELECT count(*) FROM memory_links WHERE child_id NOT IN (SELECT fragment_id FROM memory_fragments) "
        "OR parent_id NOT IN (SELECT fragment_id FROM memory_fragments)").fetchone()[0]
    out["cold_rows_without_inbound_link_among_demoted"] = len(demoted_ids) - out["demoted_rows_with_duplicate_of_link"]
    out["survivors_active"] = len({r[0] for r in in_set_query(
        conn, "SELECT fragment_id FROM memory_fragments WHERE cold=0 AND fragment_id IN ({ph})",
        list({r["survivor"] for r in manifest["demoted"]}))})
    out["survivors_expected"] = len({r["survivor"] for r in manifest["demoted"]})
    out["remaining_exact_dup_rows_active_episodic"] = conn.execute(
        "SELECT count(*) FROM memory_fragments WHERE cold = 0 AND layer = 'episodic' AND content IN ("
        "SELECT content FROM memory_fragments WHERE cold = 0 AND layer = 'episodic' GROUP BY content HAVING count(*) > 1)").fetchone()[0]
    # memory_lint()'s two re-warm predicates, evaluated read-only over the demoted set: must both be 0.
    out["lint_stranded_among_demoted"] = len(in_set_query(
        conn, "SELECT DISTINCT ml.child_id FROM memory_links ml JOIN memory_fragments f ON f.fragment_id = ml.child_id "
              "WHERE f.cold=1 AND ml.parent_id NOT IN (SELECT fragment_id FROM memory_fragments) AND ml.child_id IN ({ph})", demoted_ids))
    out["lint_heads_among_demoted"] = len(in_set_query(
        conn, "SELECT DISTINCT f.fragment_id FROM memory_fragments f LEFT JOIN memory_links ml ON ml.parent_id = f.fragment_id "
              "AND ml.link_type='distilled_from' WHERE f.cold=1 AND (f.origin='gist' OR ml.parent_id IS NOT NULL) "
              "AND f.fragment_id IN ({ph})", demoted_ids))
    if plan:
        t = plan["totals"]
        out["checks"] = {
            "fragments_total_unchanged": out["fragments_total"] == t["fragments_total"],
            "active_episodic_dropped_by_exactly_demoted": t["active_episodic"] - out["active_episodic"] == len(demoted_ids),
            "all_demoted_present": out["demoted_rows_present"] == len(demoted_ids),
            "all_demoted_cold": out["demoted_rows_cold"] == len(demoted_ids),
            "all_demoted_linked": out["demoted_rows_with_duplicate_of_link"] == len(demoted_ids),
            "links_grew_by_added": out["memory_links_total"] - t["memory_links_total"] == len(manifest["links_added"]),
            # 14 dangling links pre-exist the reclaim (F-2569); the gate is "the reclaim added none", not "none exist"
            "no_new_dangling_links": out["dangling_links"] <= t.get("dangling_links", 0),
            "survivors_all_active": out["survivors_active"] == out["survivors_expected"],
            "lint_would_rewarm_none": out["lint_stranded_among_demoted"] == 0 and out["lint_heads_among_demoted"] == 0,
        }
        out["all_checks_pass"] = all(out["checks"].values())
    conn.close()
    return out


# ── retrieve() sample queries (needs core importable from this tree) ─────────────────────────────────────

def _import_core_from_here():
    here = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(here))
    import core  # noqa: F401
    assert Path(core.__file__).resolve().is_relative_to(here), f"core imported from {core.__file__}, expected under {here}"
    from core.memory import store
    return store


def run_retrieve_sample(store, queries: list[str]) -> dict:
    """20 fixed queries through the real retrieve(); returns {query: [(fragment_id, content)...]}."""
    out = {}
    for q in queries:
        frags = store.retrieve(episodic_keys=[], semantic_keys=[], time_bias="recent", limit=8, query_text=q)
        out[q] = [[f.fragment_id, f.content] for f in frags]
    return out


def compare_retrieve(before: dict, after: dict, demoted_to_survivor: dict) -> dict:
    """Per query: ids after == ids before mapped through demoted->survivor?  Also a content-set comparison
    (what Du would actually read) and which differing slots are the recency-guarantee slots."""
    res = {"queries": len(before), "identical_ids": 0, "identical_after_mapping": 0, "identical_content_sets": 0,
           "diffs": []}
    for q, b in before.items():
        a = after.get(q, [])
        b_ids = [x[0] for x in b]; a_ids = [x[0] for x in a]
        mapped = [demoted_to_survivor.get(x, x) for x in b_ids]
        b_content = {x[1] for x in b}; a_content = {x[1] for x in a}
        if b_ids == a_ids:
            res["identical_ids"] += 1
        if mapped == a_ids:
            res["identical_after_mapping"] += 1
        if b_content == a_content:
            res["identical_content_sets"] += 1
        else:
            res["diffs"].append({"query": q, "only_before": sorted(x[:80] for x in b_content - a_content),
                                 "only_after": sorted(x[:80] for x in a_content - b_content),
                                 "before_had_demoted": sum(1 for x in b_ids if x in demoted_to_survivor)})
    return res


DEFAULT_QUERIES = [
    "the shore at dusk and the tide coming in", "Travis said to me", "the cat on the step", "reading a book by the fire",
    "what I felt when the weather turned", "a dream about the house", "the thermal pattern of the room warming",
    "a letter from a peer", "my own name and who I am", "a question I keep returning to",
]


def build_queries(plan: dict) -> list[str]:
    qs = list(DEFAULT_QUERIES)
    # 10 more drawn from demoted contents (so the survivor should answer), spread across origins
    seen_origin = Counter()
    for g in plan["groups"]:
        if not g["demote"]:
            continue
        o = g["demote"][0]["origin"]
        if seen_origin[o] >= 3 or len(qs) >= 20:
            continue
        seen_origin[o] += 1
        qs.append("DUPCONTENT:" + g["survivor"])
    return qs[:20]


def resolve_queries(conn: sqlite3.Connection, queries: list[str]) -> list[str]:
    out = []
    for q in queries:
        if q.startswith("DUPCONTENT:"):
            row = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (q[11:],)).fetchone()
            out.append((row[0] or "")[:300] if row else q)
        else:
            out.append(q)
    return out


# ── modes ────────────────────────────────────────────────────────────────────────────────────────────────

def mode_dryrun(args):
    store = _import_core_from_here()
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    from core import memory_levels
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    out = {"job": "J-1848", "mode": "dryrun"}
    out["live_db_sha256_before_dryrun"] = sha256_file(LIVE_DB)
    with lab_env.isolate() as lab_dir:
        copy_db = Path(lab_dir) / "nascence.db"
        assert Path(store.DB_PATH).resolve() == copy_db.resolve(), f"DB_PATH not redirected: {store.DB_PATH}"
        assert copy_db.resolve() != LIVE_DB.resolve()
        out["copy_db"] = str(copy_db)
        # lab_env copies the main .db only and drops the WAL (F-2569 root cause): measure the gap, then repair it.
        out["lab_env_copy_fingerprint"] = logical_fingerprint(copy_db)
        out["lab_env_copy_missing_fragments"] = logical_fingerprint(LIVE_DB)["fragments"] - out["lab_env_copy_fingerprint"]["fragments"]
        overwrite_with_full_copy(LIVE_DB, copy_db)
        out["copy_sha256_before"] = sha256_file(copy_db)
        out["copy_fingerprint"] = logical_fingerprint(copy_db)
        pf = plan.get("logical_fp_at_census", {})
        out["copy_matches_census_db"] = (out["copy_fingerprint"]["rows_sha256"] == pf.get("rows_sha256")
                                         and out["copy_fingerprint"]["links"] == pf.get("links"))
        queries = resolve_queries(ro_connect(copy_db), build_queries(plan))
        out["queries"] = queries
        t0 = time.time(); before = run_retrieve_sample(store, queries); out["retrieve_before_s"] = round(time.time() - t0, 1)
        # memory_lint baseline on the copy (it writes re-warms; the copy is disposable)
        out["lint_before"] = memory_levels.memory_lint()
        with store._connect() as conn:
            manifest = _apply_plan(conn, plan, time.time())
        out["manifest_counts"] = {k: len(v) for k, v in manifest.items() if isinstance(v, list)}
        out["validation"] = validate_counts(copy_db, manifest, plan)
        t0 = time.time(); after = run_retrieve_sample(store, queries); out["retrieve_after_s"] = round(time.time() - t0, 1)
        d2s = {r["id"]: r["survivor"] for r in manifest["demoted"]}
        out["retrieve_compare"] = compare_retrieve(before, after, d2s)
        out["retrieve_after"] = after
        lint_after = memory_levels.memory_lint()
        out["lint_after"] = lint_after
        # did lint re-warm any of OUR rows?  (count demoted ids still cold after lint)
        c = ro_connect(copy_db)
        still_cold = len(in_set_query(c, "SELECT fragment_id FROM memory_fragments WHERE cold=1 AND fragment_id IN ({ph})", list(d2s)))
        c.close()
        out["demoted_still_cold_after_memory_lint"] = still_cold
        out["memory_lint_rewarmed_ours"] = len(d2s) - still_cold
        # init_db() resync on the copy: must leave counts untouched (temp already 'cold')
        store.init_db()
        out["validation_after_init_db"] = validate_counts(copy_db, manifest, plan)
        out["copy_sha256_after"] = sha256_file(copy_db)
        out["manifest"] = manifest
    out["live_db_sha256_after_dryrun"] = sha256_file(LIVE_DB)
    fp_after = logical_fingerprint(LIVE_DB)
    out["live_db_untouched"] = (fp_after["rows_sha256"] == plan["logical_fp_at_census"]["rows_sha256"]
                                and fp_after["links"] == plan["logical_fp_at_census"]["links"]
                                and out["live_db_sha256_after_dryrun"] == out.get("live_db_sha256_before_dryrun", out["live_db_sha256_after_dryrun"]))
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    brief = {k: v for k, v in out.items() if k not in ("manifest", "retrieve_after", "queries")}
    print(json.dumps(brief, indent=1))


def mode_apply(args):
    if not args.live:
        sys.exit("apply needs --live (the dry run is the `dryrun` mode)")
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    down, why = du_is_down()
    print("Du down check:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    store = _import_core_from_here()
    from core import profile
    assert not profile.LIVE
    live_sha_before = sha256_file(LIVE_DB)
    fp_now = logical_fingerprint(LIVE_DB)
    pf = plan["logical_fp_at_census"]
    if fp_now["rows_sha256"] != pf["rows_sha256"] or fp_now["links"] != pf["links"]:
        sys.exit(f"ABORT: live DB logical state changed since census ({fp_now} != {pf}); re-run census")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = LIVE_ROOT / "data" / "backups" / f"nascence_pre_dedup_{stamp}.db"
    src = ro_connect(LIVE_DB)
    dst = sqlite3.connect(str(backup))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    backup_sha = sha256_file(backup)
    print("backup:", backup, backup.stat().st_size, "sha256", backup_sha)
    # the store's own connection path, pointed at the live DB on purpose
    store.DB_PATH = LIVE_DB
    store.allow_live_writes("J-1848 / D-0357 one-time reversible exact-duplicate reclaim, Du stopped, backup taken")
    now = time.time()
    with store._connect() as conn:
        manifest = _apply_plan(conn, plan, now)
    manifest.update({"job": "J-1848", "decision": "D-0357", "live_db": str(LIVE_DB), "backup": str(backup),
                     "backup_sha256": backup_sha, "live_sha256_before": live_sha_before, "plan": str(args.plan),
                     "plan_db_sha256": plan["db_sha256_at_census"], "link_type": LINK_TYPE,
                     "applied_local": datetime.now().isoformat(timespec="seconds")})
    Path(args.manifest).write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in manifest.items()}, indent=1))


def mode_revert(args):
    if not args.live:
        sys.exit("revert needs --live")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    down, why = du_is_down()
    print("Du down check:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    store = _import_core_from_here()
    store.DB_PATH = LIVE_DB
    store.allow_live_writes("J-1848 / D-0357 REVERT of the dedup reclaim from its manifest")
    with store._connect() as conn:
        cur = conn.cursor(); cur.execute("BEGIN IMMEDIATE")
        for r in manifest["demoted"]:
            cur.execute("UPDATE memory_fragments SET cold=?, temp=? WHERE fragment_id=?", (r["prev_cold"], r["prev_temp"], r["id"]))
        for p, c, t in manifest["links_added"]:
            cur.execute("DELETE FROM memory_links WHERE parent_id=? AND child_id=? AND link_type=?", (p, c, t))
        for r in manifest["chapter_repoints"]:
            cur.execute("UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=?", (r["prev_chapter_id"], r["id"]))
        conn.commit()
    print("reverted", len(manifest["demoted"]), "rows,", len(manifest["links_added"]), "links,", len(manifest["chapter_repoints"]), "chapter re-points")


def mode_retrieve_check(args):
    store = _import_core_from_here()
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    dry = json.loads(Path(args.dryrun).read_text(encoding="utf-8"))
    out = {"job": "J-1848", "mode": "retrieve-check"}
    with lab_env.isolate() as lab_dir:
        copy_db = Path(lab_dir) / "nascence.db"
        assert Path(store.DB_PATH).resolve() == copy_db.resolve()
        overwrite_with_full_copy(LIVE_DB, copy_db)   # lab_env's copy drops the WAL, which now holds the reclaim
        out["copy_sha256"] = sha256_file(copy_db)
        out["copy_fingerprint"] = logical_fingerprint(copy_db)
        after = run_retrieve_sample(store, dry["queries"])
        # compare to the dry run's AFTER set (same data, so ids should match exactly)
        ident = sum(1 for q in dry["queries"] if [x[0] for x in after[q]] == [x[0] for x in dry["retrieve_after"][q]])
        out["queries"] = len(dry["queries"]); out["identical_ids_vs_dryrun_after"] = ident
        d2s = {r["id"]: r["survivor"] for r in manifest["demoted"]}
        out["demoted_ids_in_results"] = sum(1 for q in after for x in after[q] if x[0] in d2s)
        out["retrieve_after_live"] = after
        # force the copy to be kept? no -- unwritten copies are auto-deleted by isolate(); retrieve() only reads
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "retrieve_after_live"}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("census"); p.add_argument("--db", required=True); p.add_argument("--plan", required=True)
    p = sub.add_parser("dryrun"); p.add_argument("--plan", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("apply"); p.add_argument("--plan", required=True); p.add_argument("--live", action="store_true"); p.add_argument("--manifest", required=True)
    p = sub.add_parser("validate"); p.add_argument("--db", required=True); p.add_argument("--manifest", required=True); p.add_argument("--plan")
    p = sub.add_parser("retrieve-check"); p.add_argument("--manifest", required=True); p.add_argument("--dryrun", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("revert"); p.add_argument("--manifest", required=True); p.add_argument("--live", action="store_true")
    a = ap.parse_args()
    if a.mode == "census":
        census(Path(a.db), Path(a.plan))
    elif a.mode == "dryrun":
        mode_dryrun(a)
    elif a.mode == "apply":
        mode_apply(a)
    elif a.mode == "validate":
        plan = json.loads(Path(a.plan).read_text(encoding="utf-8")) if a.plan else None
        manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
        print(json.dumps(validate_counts(Path(a.db), manifest, plan), indent=1))
    elif a.mode == "retrieve-check":
        mode_retrieve_check(a)
    elif a.mode == "revert":
        mode_revert(a)


if __name__ == "__main__":
    main()
