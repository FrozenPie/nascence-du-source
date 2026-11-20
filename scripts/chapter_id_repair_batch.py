"""
chapter_id repair -- clear-batch SELECTION (docs/staged/chapter_id_repair.md; D-0221 / D-0245 / D-0350).
=========================================================================================================
SELECTION ONLY. This module never writes: no UPDATE, no data/ path constant, nothing __file__-relative. It opens
the memory DB read-only (``mode=ro``) and returns the batch a clear WOULD touch, with every exclusion it applied
spelled out by fragment_id. Executing a batch (``UPDATE memory_fragments SET chapter_id=NULL``) is a separate,
founder-gated step (D-0245 holds all further batches; D-0221 governs their shape) that must take its rows from
``select_clear_batch()`` -- never from a hand-written query -- so the exclusions below are code, not convention.

Selection rule (J-0964 / F-1360, the methodology D-0221 was ruled on; first live write J-1128 / F-1548): for a
book title T, a reading/study fragment is MISFILED when its own leading-bracket tag genuinely cites T
(``core.world_consolidation._cites``, truncation-aware) but the gist it is currently filed behind does NOT cite T.

Two explicit, logged exclusions are applied on top of that rule, in this order:

1. ORIGIN EXCLUSION (D-0350, ruled 2026-10-06, built J-1837). Any fragment whose tag starts with
   ``ORIGIN_VICTIM_SUBJECT`` -- the 50-char gist subject of the second, 3.6%-read Darwin book, 'The Origin of
   Species by Means of Natural Selectio' -- is NEVER part of a clear batch, whatever title the batch is for.
   F-2413 (verified): the shipped ``_order_subjects`` processes the finished book's subject ('On the Origin of
   Species by Means of Natural Selec', the over-matcher) before this one, and the over-matcher's citation test
   accepts these tags, so once cleared they would be re-filed behind the WRONG gist at the next sweep(). 26 such
   fragments exist (2 tagged exactly the subject, 24 tagged 'The Origin of Species by Means of Natural Selection
   Or the P'), all currently filed behind the right gist (87eaa3c4). D-0350 chose this exclusion over shipping
   the topological ordering candidate (fixes 26, latently breaks 948) and over an identity-first claim.

2. IDENTITY-KEPT (J-1837, found while building 1). The F-1360 rule is asymmetric for an over-matching pair: the
   victim subject's own citation test also accepts the over-matcher's long reading tags, so a batch for T=victim
   flags the finished book's fragments as "misfiled" even when they sit behind the finished book's OWN gist (810
   of them live, 607 behind the 'On the Origin...' gists). A fragment whose tag IS its current gist's subject
   (equal, or the gist tag is the fragment tag's [:50] / word-boundary cut -- the two ways essay_lesson/
   grounded_learning ever truncate a title) is kept where it is. This does not shield the F-1615 case (a tag
   'About You Second Edition' behind the generic 'About You' gist is not an identity match) -- that case stays
   repairable, as D-0221's own first batch required.

Every call returns (and the CLI prints / writes with ``--out``) the kept rows AND both excluded sets with their
fragment_ids and tags, plus ``origin_exclusion_mismatch`` when the number of Origin-excluded rows seen in the
whole table differs from ``ORIGIN_EXCLUSION_EXPECTED`` -- a changed count means the Origin pair's population
moved (Du read more of the second book, or a row was cleared), which is D-0350's own defeater and must be looked
at before any batch runs.

    python scripts/chapter_id_repair_batch.py --title "About You Second Edition" [--db PATH] [--out report.json]
    python scripts/chapter_id_repair_batch.py --all-subjects [--out report.json]     # corpus-wide dry census
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# D-0350: the gist subject whose tagged fragments must never be cleared (exactly 50 chars -- the [:50] cut of
# 'The Origin of Species by Means of Natural Selection Or the Preservation of Favoured Races...').
ORIGIN_VICTIM_SUBJECT = "The Origin of Species by Means of Natural Selectio"
# The finished book's subject (the over-matcher). Documentation + the mismatch check only; never excluded.
ORIGIN_OVER_MATCHER_SUBJECT = "On the Origin of Species by Means of Natural Selec"
# F-2413 census 2026-10-04, re-counted J-1837 2026-10-06 against the live DB (max fragment ts 07:30:32): 26.
ORIGIN_EXCLUSION_EXPECTED = 26

assert len(ORIGIN_VICTIM_SUBJECT) == 50 and len(ORIGIN_OVER_MATCHER_SUBJECT) == 50


def open_ro(db_path: str | Path) -> sqlite3.Connection:
    """A read-only connection (SQLite URI ``mode=ro``): any write attempt raises at the driver level."""
    conn = sqlite3.connect(f"file:{Path(db_path).resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def default_db_path() -> Path:
    from core.memory.store import DB_PATH
    return DB_PATH


def is_origin_excluded(tag: str) -> bool:
    """D-0350 exclusion predicate: the fragment's TAG (not its body) starts with the victim subject."""
    return bool(tag) and tag.lower().startswith(ORIGIN_VICTIM_SUBJECT.lower())


def is_identity_of(tag: str, gist_tag: str) -> bool:
    """Is `tag` (a reading/study fragment's tag) the same title as `gist_tag` (its current gist's subject)?
    True when equal, or when gist_tag is tag's hard [:50] cut or its word-boundary (_smart_cut) cut --
    the only two truncations a gist tag ever receives. A gist tag that is merely a shorter prefix title
    ('About You' vs 'About You Second Edition') is NOT an identity."""
    from core.essay_lesson import _smart_cut
    t, g = (tag or "").strip().lower(), (gist_tag or "").strip().lower()
    if not t or not g:
        return False
    return t == g or t[:50] == g or _smart_cut(t) == g


def select_misfiled(conn: sqlite3.Connection, title: str) -> tuple[list[dict], int]:
    """The F-1360 rule, unchanged: rows whose own tag cites `title` but whose current gist's tag does not.
    Returns (misfiled_rows, already_correct_count). Each row: fragment_id, origin, tag, chapter_id, gist_tag."""
    from core.world_consolidation import _cites, _cites_clause, _tag_of
    clause, params = _cites_clause(title)
    cand = conn.execute(
        f"SELECT fragment_id, origin, content, chapter_id FROM memory_fragments "
        f"WHERE origin IN ('reading','study') AND {clause} AND chapter_id IS NOT NULL", params).fetchall()
    gist_cache: dict[str, str] = {}
    misfiled: list[dict] = []
    correct = 0
    for r in cand:
        if not _cites(title, r["content"]):
            continue
        cid = r["chapter_id"]
        if cid not in gist_cache:
            g = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (cid,)).fetchone()
            gist_cache[cid] = (g["content"] if g else "") or ""
        if _cites(title, gist_cache[cid]):
            correct += 1
            continue
        misfiled.append({"fragment_id": r["fragment_id"], "origin": r["origin"], "tag": _tag_of(r["content"]),
                         "chapter_id": cid, "gist_tag": _tag_of(gist_cache[cid])})
    return misfiled, correct


def apply_exclusions(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Split F-1360-flagged rows into (kept, origin_excluded, identity_kept). Pure."""
    kept: list[dict] = []
    origin_ex: list[dict] = []
    ident: list[dict] = []
    for r in rows:
        if is_origin_excluded(r.get("tag", "")):
            origin_ex.append(r)
        elif is_identity_of(r.get("tag", ""), r.get("gist_tag", "")):
            ident.append(r)
        else:
            kept.append(r)
    return kept, origin_ex, ident


def count_origin_population(conn: sqlite3.Connection) -> dict:
    """How many reading/study rows carry the victim's tag right now, and how many of them are unfiled
    (NULL chapter_id) -- D-0350's defeater. Table-wide, independent of any batch title."""
    from core.world_consolidation import _tag_of
    rows = conn.execute("SELECT fragment_id, content, chapter_id FROM memory_fragments "
                        "WHERE origin IN ('reading','study') AND content LIKE ?",
                        (f"%{ORIGIN_VICTIM_SUBJECT}%",)).fetchall()
    hits = [r for r in rows if is_origin_excluded(_tag_of(r["content"]))]
    return {"origin_tagged_total": len(hits),
            "origin_tagged_null_chapter": sum(1 for r in hits if r["chapter_id"] is None),
            "origin_tagged_ids": [r["fragment_id"] for r in hits]}


def select_clear_batch(conn: sqlite3.Connection, title: str, log=print) -> dict:
    """The one sanctioned way to build a clear batch. Always applies both exclusions and reports them."""
    misfiled, correct = select_misfiled(conn, title)
    kept, origin_ex, ident = apply_exclusions(misfiled)
    pop = count_origin_population(conn)
    report = {
        "ts": time.time(), "title": title, "rule": "F-1360 + D-0350 origin exclusion + J-1837 identity-kept",
        "already_correct": correct, "flagged_misfiled": len(misfiled),
        "batch": kept, "batch_size": len(kept),
        "origin_excluded": origin_ex, "origin_excluded_count": len(origin_ex),
        "identity_kept": ident, "identity_kept_count": len(ident),
        "origin_population": {k: v for k, v in pop.items() if k != "origin_tagged_ids"},
        "origin_exclusion_expected": ORIGIN_EXCLUSION_EXPECTED,
        "origin_exclusion_mismatch": pop["origin_tagged_total"] != ORIGIN_EXCLUSION_EXPECTED,
        "origin_null_chapter_exposed": pop["origin_tagged_null_chapter"] > 0,
    }
    if log:
        log(f"[chapter_id_repair_batch] T={title!r}: flagged={len(misfiled)} kept={len(kept)} "
            f"origin_excluded={len(origin_ex)} identity_kept={len(ident)} already_correct={correct}")
        for r in origin_ex:
            log(f"  EXCLUDED (D-0350 origin) {r['fragment_id']} tag={r['tag']!r} behind={r['chapter_id'][:8]} ({r['gist_tag'][:40]!r})")
        for r in ident:
            log(f"  KEPT (identity of its gist) {r['fragment_id']} tag={r['tag'][:50]!r} behind={r['chapter_id'][:8]}")
        if report["origin_exclusion_mismatch"]:
            log(f"  WARNING: origin-tagged population is {pop['origin_tagged_total']}, expected "
                f"{ORIGIN_EXCLUSION_EXPECTED} -- D-0350 defeater territory, review before any clear")
        if report["origin_null_chapter_exposed"]:
            log(f"  WARNING: {pop['origin_tagged_null_chapter']} origin-tagged rows are UNFILED (NULL chapter_id) "
                f"-- D-0350 defeater, live exposure")
    return report


def gist_subjects(conn: sqlite3.Connection) -> set[str]:
    """sweep()'s own subject derivation, read-only."""
    import re
    out: set[str] = set()
    for r in conn.execute("SELECT content FROM memory_fragments WHERE origin IN ('essay','understanding')"):
        m = re.search(r"(?:on|from) '([^']+)'", r["content"] or "")
        if m:
            out.add(m.group(1).strip())
    return out


# ---------------------------------------------------------------------------------------------------------------
# D-0362 (C) / J-1897 -- UN-FILE ACTIVE-READING BOOKS ONLY.  ADDITIVE: nothing above this line is changed.
#
# D-0362 (ruled 2026-10-07, travis): before J-1837's stricter-only finished-gate fix, ~8 genuinely UNFINISHED books
# filed their reading/study notes behind a one-day gist of their own (F-2519: 568 such rows behind 10 gist subjects).
# Ruling (C): clear only the books Du is still actively reading (pct below ~40) and leave the rest filed. This is
# SELECTION ONLY, like everything in this module (no UPDATE; applying is gated by D-0245's hold).
#
# Why a second selector: ``select_misfiled`` (F-1360) flags a row only when its gist does NOT cite the book. These
# rows sit behind a gist that DOES cite their book (it is the book's own gist), so F-1360 flags none of them -- and
# J-1837's identity-kept guard (tag IS its gist's subject) would keep every one of them even if it did. Here the
# criterion is different and explicit: the book is unfinished (no strict reading_state entry for it has a completed
# pass) while the legacy finished-gate lookup said it was finished, i.e. the filing was a FALSE-PASS filing. The
# identity-kept guard is therefore deliberately NOT applied (its purpose, protecting a FINISHED book's notes behind
# its own gist, does not hold for an unfinished book); it is reported (``identity_kept_would_have_kept``) so the
# bypass is visible. The Origin exclusion (D-0350) IS applied.
# ---------------------------------------------------------------------------------------------------------------
UNFILE_PCT_BELOW = 40.0  # D-0362 (C): "still actively reading (pct below about 40)"


def _stem_words(key: str) -> str:
    return Path(key).stem.replace("_", " ")


def strict_state_entries(subject: str, st: dict) -> list[tuple[str, dict]]:
    """Every reading_state entry whose file stem genuinely cites the gist subject (the strict reference F-2519
    used: ``essay_lesson._cites_this_book(subject[:50], stem-with-spaces)``). Sorted by key (deterministic)."""
    from core.essay_lesson import _cites_this_book
    return sorted(((k, v) for k, v in st.items()
                   if not k.startswith("_") and isinstance(v, dict) and _cites_this_book(subject[:50], _stem_words(k))),
                  key=lambda kv: kv[0])


def false_open_subjects(subjects, st: dict, completion_pct: float) -> list[str]:
    """Gist subjects whose LEGACY finished-gate lookup (first state key containing the title's single longest word)
    says 'finished at least once' while at least one strict entry exists and NONE of the strict entries has a
    completed pass -- the F-2519 'false-open real books'."""
    from core.world_consolidation import _passes_of, _state_entries_for
    out = []
    for s in sorted(subjects):
        legacy, _full = _state_entries_for(s, st)
        if legacy is None or _passes_of(legacy, completion_pct) < 1:
            continue
        strict = strict_state_entries(s, st)
        if strict and all(_passes_of(v, completion_pct) < 1 for _k, v in strict):
            out.append(s)
    return out


def head_gate_passes(subject: str, st: dict, completion_pct: float) -> int:
    """``core.world_consolidation._completed_passes_for`` evaluated against a reading_state DICT (a copy), not the
    live file: min(legacy lookup, full-title lookup) -- the gate the next sweep() runs (J-1837, F-2413)."""
    from core.world_consolidation import _passes_of, _state_entries_for
    legacy, full = _state_entries_for(subject, st)
    if legacy is None:
        return 0
    n = _passes_of(legacy, completion_pct)
    if full is not None:
        n = min(n, _passes_of(full, completion_pct))
    return n


def would_reclaim(subject: str, tag: str, st: dict) -> bool:
    """J-1966 / D-0386 (b): would ``subject``'s sweep() pass claim a NULL-chapter row carrying ``tag``? Exactly the
    claim test ``core.world_consolidation._file_book_notes`` applies to a candidate: the tag cites the subject's
    signature AND (J-1895 / D-0359 shape 3) the tag does not resolve to a DIFFERENT reading_state book than the
    subject. A one-word signature ({king} for 'The Mad King') cites a tag naming a longer, different title
    ('King Arthur and the Knights of the Round Table') on words alone; the book-identity exclusion is what stops
    that claim, so the re-file collision guard must apply it too or it over-holds rows the sweep would never take."""
    from core.essay_lesson import _cites_this_book
    from core.world_consolidation import _tag_names_other_book
    return _cites_this_book(subject[:50], tag) and not _tag_names_other_book(subject, tag, st)


def select_unfile_active_books(conn: sqlite3.Connection, st: dict, now: float | None = None,
                               pct_below: float = UNFILE_PCT_BELOW, subjects=None, completion_pct: float | None = None,
                               log=print) -> dict:
    """D-0362 (C) dry-run selection. ``st`` is the parsed reading_state dict (a COPY); ``subjects`` defaults to the
    false-open real-book subjects derived from it (``false_open_subjects``). For each subject: its own gist ids,
    the reading/study fragments filed behind them whose tag cites the book, the book's strict state entries
    (pct / last_read_ts / passes), and an active-reading verdict. A subject falls under (C) when it is unfinished
    (no strict completed pass) AND its highest strict pct is below ``pct_below``. Returns the report incl. the
    exact sorted fragment_id set to clear, its size and sha256."""
    import hashlib
    import re
    from core.essay_lesson import _cites_this_book
    from core.world_consolidation import _passes_of, _state_entries_for, _tag_of
    if completion_pct is None:
        from core.reading import COMPLETION_PCT as completion_pct
    now = time.time() if now is None else now
    all_subjects = gist_subjects(conn)
    subj_list = sorted(subjects) if subjects is not None else false_open_subjects(all_subjects, st, completion_pct)
    gist_ids: dict[str, set] = {s: set() for s in subj_list}
    for r in conn.execute("SELECT fragment_id, content FROM memory_fragments WHERE origin IN ('essay','understanding')"):
        m = re.search(r"(?:on|from) '([^']+)'", r["content"] or "")
        if m and m.group(1).strip() in gist_ids:
            gist_ids[m.group(1).strip()].add(r["fragment_id"])
    frs = conn.execute("SELECT fragment_id, origin, content, chapter_id FROM memory_fragments "
                       "WHERE origin IN ('reading','study') AND chapter_id IS NOT NULL").fetchall()
    cur = st.get("_current_book") or ""
    # RE-FILE COLLISION GUARD (D-0245's own concern, F-1615): once a row is cleared, the next sweep() lets ANY subject
    # whose gate is open and whose signature the row's tag satisfies claim it -- not just the book it belongs to. A row
    # whose tag is also cited by another OPEN-gate subject would be re-filed behind that WRONG gist, so it is HELD
    # out of the batch (reported, not cleared).
    open_subjects = sorted(x for x in all_subjects if head_gate_passes(x, st, completion_pct) >= 1)
    held = []
    per, batch, origin_ex, kept_rows, ident_would_keep = [], [], [], [], []
    for s in subj_list:
        strict = strict_state_entries(s, st)
        legacy, full = _state_entries_for(s, st)
        pcts = [float(v.get("pct", 0) or 0) for _k, v in strict]
        passes = [_passes_of(v, completion_pct) for _k, v in strict]
        last = [float(v.get("last_read_ts", 0) or 0) for _k, v in strict]
        max_pct = max(pcts) if pcts else None
        unfinished = bool(strict) and all(p < 1 for p in passes)
        under_c = unfinished and max_pct is not None and max_pct < pct_below
        own = [r for r in frs if r["chapter_id"] in gist_ids[s] and _cites_this_book(s[:50], _tag_of(r["content"]))]
        info = {"subject": s,
                "entries": [{"file": Path(k).name, "pct": v.get("pct"), "passes": _passes_of(v, completion_pct),
                             "last_read_ts": v.get("last_read_ts"),
                             "days_since_read": (round((now - float(v["last_read_ts"])) / 86400.0, 1)
                                                 if v.get("last_read_ts") else None),
                             "is_current_book": k == cur} for k, v in strict],
                "max_pct": max_pct, "unfinished": unfinished,
                "legacy_gate_passes": (_passes_of(legacy, completion_pct) if legacy else 0),
                "fulltitle_gate_passes": (_passes_of(full, completion_pct) if full is not None else None),
                "min_days_since_read": (round((now - max(last)) / 86400.0, 1) if last and max(last) else None),
                "gist_ids": sorted(gist_ids[s]), "filed_behind_own_gist": len(own), "under_C": under_c, "cleared": 0}
        for r in own:
            row = {"fragment_id": r["fragment_id"], "origin": r["origin"], "tag": _tag_of(r["content"]),
                   "chapter_id": r["chapter_id"], "subject": s}
            if is_identity_of(row["tag"], s):
                ident_would_keep.append(row)
            if not under_c:
                kept_rows.append(row)
            elif is_origin_excluded(row["tag"]):
                origin_ex.append(row)
            elif [x for x in open_subjects if x != s and would_reclaim(x, row["tag"], st)]:
                row["would_be_claimed_by"] = [x for x in open_subjects if x != s and would_reclaim(x, row["tag"], st)]
                held.append(row)
                info["held_by_collision"] = info.get("held_by_collision", 0) + 1
            else:
                batch.append(row)
                info["cleared"] += 1
        per.append(info)
    seen, uniq = set(), []
    for r in batch:
        if r["fragment_id"] not in seen:
            seen.add(r["fragment_id"])
            uniq.append(r)
    ids = sorted(seen)
    pop = count_origin_population(conn)
    report = {"ts": now, "rule": "D-0362 (C): unfinished book (no strict completed pass) AND max strict pct < %.1f; "
                                 "Origin exclusion applied; re-file collision guard applied; identity-kept guard deliberately bypassed (see module note)" % pct_below,
              "pct_below": pct_below, "subjects": per, "subjects_under_C": [p["subject"] for p in per if p["under_C"]],
              "batch_ids": ids, "batch_size": len(ids),
              "batch_sha256": hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest(),
              "batch": uniq, "left_filed_not_under_C": len(kept_rows), "left_filed_rows": kept_rows,
              "origin_excluded": origin_ex, "origin_excluded_count": len(origin_ex),
              "refile_collision_held": held, "refile_collision_held_count": len(held),
              "open_gate_subjects": len(open_subjects),
              "identity_kept_would_have_kept": len([r for r in ident_would_keep if r["fragment_id"] in seen]),
              "origin_population": {k: v for k, v in pop.items() if k != "origin_tagged_ids"},
              "origin_exclusion_mismatch": pop["origin_tagged_total"] != ORIGIN_EXCLUSION_EXPECTED}
    if log:
        log(f"[chapter_id_repair_batch] D-0362(C): subjects={len(per)} under_C={len(report['subjects_under_C'])} "
            f"batch={len(ids)} sha256={report['batch_sha256'][:16]} left_filed={len(kept_rows)} origin_excluded={len(origin_ex)} "
            f"refile_collision_held={len(held)}")
        for p in per:
            log(f"  {'CLEAR' if p['under_C'] else 'LEAVE'} {p['subject'][:50]!r} max_pct={p['max_pct']} "
                f"filed_own={p['filed_behind_own_gist']} cleared={p['cleared']}")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--title", action="append", default=[], help="book title / gist subject (repeatable)")
    ap.add_argument("--all-subjects", action="store_true", help="every gist subject (corpus-wide dry census)")
    ap.add_argument("--db", default=None, help="memory DB path (default: core.memory.store.DB_PATH), opened mode=ro")
    ap.add_argument("--out", default=None, help="write the full JSON report (every id) here")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--unfile-active-books", action="store_true",
                    help="D-0362 (C) dry run: ids behind the OWN gist of unfinished books with pct below --pct-below")
    ap.add_argument("--reading-state", default=None, help="reading_state.json COPY (required with --unfile-active-books)")
    ap.add_argument("--pct-below", type=float, default=UNFILE_PCT_BELOW)
    a = ap.parse_args(argv)
    conn = open_ro(a.db or default_db_path())
    if a.unfile_active_books:
        if not a.reading_state:
            ap.error("--unfile-active-books needs --reading-state PATH (a COPY of data/reading_state.json)")
        st = json.loads(Path(a.reading_state).read_text(encoding="utf-8"))
        rep = select_unfile_active_books(conn, st, pct_below=a.pct_below, log=(lambda *_: None) if a.quiet else print)
        print("[chapter_id_repair_batch] D-0362C TOTAL " + json.dumps({k: rep[k] for k in (
            "batch_size", "batch_sha256", "subjects_under_C", "left_filed_not_under_C", "origin_excluded_count", "refile_collision_held_count",
            "identity_kept_would_have_kept", "origin_exclusion_mismatch")}, ensure_ascii=False))
        if a.out:
            Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[chapter_id_repair_batch] report -> {a.out}")
        conn.close()
        return 0
    titles = list(a.title)
    if a.all_subjects:
        titles += sorted(gist_subjects(conn))
    if not titles:
        ap.error("give --title or --all-subjects")
    log = (lambda *_: None) if a.quiet else print
    reports = [select_clear_batch(conn, t, log=log) for t in titles]
    tot = {"titles": len(reports), "batch_total": sum(r["batch_size"] for r in reports),
           "origin_excluded_total": sum(r["origin_excluded_count"] for r in reports),
           "identity_kept_total": sum(r["identity_kept_count"] for r in reports),
           "flagged_total": sum(r["flagged_misfiled"] for r in reports),
           "already_correct_total": sum(r["already_correct"] for r in reports),
           "origin_population": reports[0]["origin_population"] if reports else {},
           "origin_exclusion_mismatch": any(r["origin_exclusion_mismatch"] for r in reports),
           "origin_null_chapter_exposed": any(r["origin_null_chapter_exposed"] for r in reports)}
    print("[chapter_id_repair_batch] TOTAL " + json.dumps(tot, ensure_ascii=False))
    if a.out:
        Path(a.out).write_text(json.dumps({"total": tot, "reports": reports}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[chapter_id_repair_batch] report -> {a.out}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
