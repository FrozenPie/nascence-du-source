"""
archive_contaminated_inferences.py — D-0462 / J-2359 (object_epistemic_loop O1)
================================================================================
Moves the provenance-empty inferences (supporting_observations == []) out of data/world_substrate.json
into data/archive/contaminated_inferences_pre_fix.jsonl. Archive, never delete (D-0462, travis
2026-10-17). These were written by the legacy whole-text inference latch in
nodes/inner_monologue_node.py (see core/object_hypothesis.py's docstring for what it recorded).

DRY-RUN BY DEFAULT. Without --apply nothing is written anywhere except an optional --report file
OUTSIDE data/. Run it against a scratch copy with --store to look first:

    python scripts/archive_contaminated_inferences.py --store <copy>.json --report <scratch>/report.json

--apply (founder-chosen moment, Du DOWN):
  1. refuses if the store is the real data/world_substrate.json and the last line of data/nascence.log
     is not 'Nascence shutting down.' (Du up = the live process owns the file; its 5 s cache would
     write the old inferences straight back);
  2. declares this process the one deliberate writer (profile.mark_live(), the seed_memory.py /
     backfill_essays.py precedent) and resolves EVERY write path through profile.guard_path();
  3. writes a full backup of the store next to it (world_substrate.pre_archive_<stamp>.json);
  4. appends one archive row per inference (idempotent: ids already in the archive are not re-added);
  5. rewrites the store atomically (tmp + replace, the same shape as world_substrate._save()), then
     re-reads both files and verifies the counts. Any mismatch -> exit 2, backup left in place.

Every other field of every object is carried through unchanged; only the archived inference dicts
leave the store. An inference that still points at a superseded_by/provenance survives untouched.
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_STORE = ROOT / "data" / "world_substrate.json"
DEFAULT_ARCHIVE = ROOT / "data" / "archive" / "contaminated_inferences_pre_fix.jsonl"
DEFAULT_LOG = ROOT / "data" / "nascence.log"
SHUTDOWN_LINE = "Nascence shutting down."
REASON = "provenance-empty (supporting_observations == []), legacy whole-text latch; D-0462"


def is_contaminated(inf: dict) -> bool:
    return not (inf.get("supporting_observations") or [])


def plan(store: dict) -> dict:
    """Pure: what an archive pass would move. Nothing is written."""
    from core import object_hypothesis as oh
    moved, kept = [], 0
    by_obj, by_loc, by_cls = collections.Counter(), collections.Counter(), collections.Counter()
    passes_new_gate = []
    for oid, o in store.items():
        for inf in o.get("inferences") or []:
            if is_contaminated(inf):
                moved.append((oid, inf))
                by_obj[oid] += 1
                by_loc[o.get("location", "?")] += 1
                by_cls[o.get("object_class", "?")] += 1
                h = oh.extract(inf.get("hypothesis", ""), o.get("object_class", ""), o.get("name", ""))
                if h:
                    passes_new_gate.append({"object_id": oid, "inference_id": inf.get("inference_id"),
                                            "clause": h[0]})
            else:
                kept += 1
    total = len(moved) + kept
    return {
        "objects": len(store),
        "inferences_total": total,
        "to_archive": len(moved),
        "survive_in_store": kept,
        "objects_touched": len(by_obj),
        "objects_left_with_inferences": sum(
            1 for o in store.values() if any(not is_contaminated(i) for i in o.get("inferences") or [])),
        "by_object_top20": by_obj.most_common(20),
        "by_location": dict(by_loc),
        "by_class": dict(by_cls),
        "confidence": dict(collections.Counter(i.get("confidence") for _, i in moved)),
        "hypothesis_len_ge_279": sum(1 for _, i in moved if len(i.get("hypothesis", "")) >= 279),
        "would_pass_new_clause_gate": passes_new_gate,
        "_moved": moved,
    }


def du_is_down(log_path: Path) -> bool:
    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 4096))
            tail = f.read().decode("utf-8", errors="replace").splitlines()
        last = next((ln for ln in reversed(tail) if ln.strip()), "")
        return last.rstrip().endswith(SHUTDOWN_LINE)
    except OSError:
        return False


def apply(store_path: Path, archive_path: Path, log_path: Path, p: dict, store: dict) -> int:
    from core import profile
    real = profile._data_relative(store_path.resolve()) is not None   # any recognized data/ root, incl. the canonical one
    if real:
        if store_path.resolve() != DEFAULT_STORE.resolve():
            log_path = store_path.resolve().parent / "nascence.log"
        if not du_is_down(log_path):
            print("REFUSED: Du does not look down (last line of %s is not %r)." % (log_path, SHUTDOWN_LINE))
            return 3
    profile.mark_live()
    store_w = profile.guard_path(store_path)
    archive_w = profile.guard_path(archive_path)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_w = profile.guard_path(store_path.with_name(store_path.stem + f".pre_archive_{stamp}.json"))
    shutil.copy2(store_w, backup_w)
    print("backup:", backup_w)

    already = set()
    if archive_w.exists():
        for ln in archive_w.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    already.add(json.loads(ln)["inference"]["inference_id"])
                except Exception:
                    pass
    archive_w.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    appended = 0
    with open(archive_w, "a", encoding="utf-8") as f:
        for oid, inf in p["_moved"]:
            if inf.get("inference_id") in already:
                continue
            o = store[oid]
            f.write(json.dumps({"archived_at": now, "job": "J-2359", "reason": REASON, "object_id": oid,
                                "object_class": o.get("object_class"), "object_name": o.get("name"),
                                "location": o.get("location"), "inference": inf},
                               ensure_ascii=False) + "\n")
            appended += 1
    moved_ids = {(oid, inf.get("inference_id")) for oid, inf in p["_moved"]}
    for oid, o in store.items():
        o["inferences"] = [i for i in (o.get("inferences") or []) if (oid, i.get("inference_id")) not in moved_ids]
    tmp = store_w.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(store_w)

    chk = json.loads(store_w.read_text(encoding="utf-8"))
    left = sum(len(o.get("inferences") or []) for o in chk.values())
    still_empty = sum(1 for o in chk.values() for i in o.get("inferences") or [] if is_contaminated(i))
    arch_ids = set()
    for ln in archive_w.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            arch_ids.add(json.loads(ln)["inference"]["inference_id"])
    ok = (len(chk) == p["objects"] and left == p["survive_in_store"] and still_empty == 0
          and all(inf.get("inference_id") in arch_ids for _, inf in p["_moved"]))
    print(f"applied: archived +{appended} rows (archive now {len(arch_ids)} ids); store inferences left {left}; "
          f"objects {len(chk)}; verify={'OK' if ok else 'MISMATCH'}")
    return 0 if ok else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    ap.add_argument("--nascence-log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--report", type=Path, default=None, help="write the dry-run report JSON here (not under data/)")
    ap.add_argument("--apply", action="store_true", help="really archive (default: dry-run, writes nothing)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    store = json.loads(a.store.read_text(encoding="utf-8"))
    p = plan(store)
    rep = {k: v for k, v in p.items() if not k.startswith("_")}
    rep["store"] = str(a.store)
    rep["mode"] = "APPLY" if a.apply else "DRY-RUN"
    print(json.dumps({k: v for k, v in rep.items() if k != "would_pass_new_clause_gate"}, indent=1, ensure_ascii=False))
    print("would_pass_new_clause_gate:", len(p["would_pass_new_clause_gate"]))
    for r in p["would_pass_new_clause_gate"]:
        print("  ", r["object_id"], "|", r["clause"])
    if a.report:
        if (ROOT / "data") in a.report.resolve().parents:
            print("REFUSED: --report must not be under data/")
            return 4
        a.report.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    if not a.apply:
        print("DRY-RUN: nothing written.")
        return 0
    return apply(a.store, a.archive, a.nascence_log, p, store)


if __name__ == "__main__":
    sys.exit(main())
