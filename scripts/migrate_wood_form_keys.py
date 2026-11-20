"""
migrate_wood_form_keys.py — J-2388 / F-3087 (object_epistemic_loop guardrail: Layer 1 never read by text)
==========================================================================================================
Copies the two observable-form keys that core/world_substrate.get_generative_state() used to read out of
Layer 1 (causal_state original_structure / wood_type, 2026-08-14) into Layer 2 (physical_state structure /
wood_type) for every object that carries them, so the look / inspect_end / scrape / smell / pick_up prose of
driftwood no longer depends on Layer 1. COPY, not move: causal_state is left exactly as it is (it stays the
hidden ground truth; nothing is deleted). Values are copied verbatim, so every percept is byte-identical
(see scripts/test_object_epistemic_wood_form.py). New spawns already mirror the keys (spawn_object, J-2388);
get_generative_state() reads physical_state only (J-2411, Layer-1 fallback removed after the 2026-10-18 apply).

DRY-RUN BY DEFAULT. Without --apply nothing is written anywhere except an optional --report file OUTSIDE
data/:

    python scripts/migrate_wood_form_keys.py --store <copy>.json --report <scratch>/report.json

--apply (founder-chosen moment, Du DOWN; same shape as scripts/archive_contaminated_inferences.py):
  1. refuses if the store is under a data/ root and the last line of nascence.log is not
     'Nascence shutting down.' (Du up = the live process owns the file; its 5 s cache would write the old
     state straight back) -> exit 3;
  2. profile.mark_live(), every write path through profile.guard_path();
  3. full backup next to the store (world_substrate.pre_formkeys_<stamp>.json);
  4. atomic rewrite (tmp + replace), then re-read and verify: every planned key present with the planned
     value, causal_state of every object unchanged, every other field unchanged, object count unchanged.
     Any mismatch -> exit 2, backup left in place.
Idempotent: an object whose physical_state already holds the key is skipped (and a conflicting value is
reported, never overwritten).
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_STORE = ROOT / "data" / "world_substrate.json"
DEFAULT_LOG = ROOT / "data" / "nascence.log"
SHUTDOWN_LINE = "Nascence shutting down."
# (Layer-2 physical_state key, Layer-1 causal_state key) — the same pairs as world_substrate._FORM_KEYS
FORM_KEYS = (("structure", "original_structure"), ("wood_type", "wood_type"))


def plan(store: dict) -> dict:
    """Pure: which (object, key, value) copies a pass would make. Nothing is written."""
    copies, already, conflicts = [], 0, []
    for oid, o in store.items():
        cs, ps = o.get("causal_state") or {}, o.get("physical_state") or {}
        for l2, l1 in FORM_KEYS:
            if l1 not in cs:
                continue
            if l2 in ps:
                if ps[l2] == cs[l1]:
                    already += 1
                else:
                    conflicts.append({"object_id": oid, "key": l2, "layer2": ps[l2], "layer1": cs[l1]})
                continue
            copies.append({"object_id": oid, "object_class": o.get("object_class"),
                           "location": o.get("location"), "key": l2, "from": l1, "value": cs[l1]})
    return {
        "objects": len(store),
        "objects_with_layer1_form_keys": len({oid for oid, o in store.items()
                                              if any(l1 in (o.get("causal_state") or {}) for _, l1 in FORM_KEYS)}),
        "copies_planned": len(copies),
        "objects_touched": len({c["object_id"] for c in copies}),
        "already_layer2": already,
        "conflicts": conflicts,
        "copies": copies,
    }


def migrated(store: dict, p: dict) -> dict:
    """Pure: a deep copy of the store with the planned copies made."""
    out = copy.deepcopy(store)
    for c in p["copies"]:
        out[c["object_id"]].setdefault("physical_state", {})[c["key"]] = c["value"]
    return out


def verify(before: dict, after: dict, p: dict) -> list[str]:
    bad = []
    if set(before) != set(after):
        bad.append("object set changed")
    planned = {(c["object_id"], c["key"]): c["value"] for c in p["copies"]}
    for oid, o in before.items():
        a = after.get(oid)
        if a is None:
            continue
        if a.get("causal_state") != o.get("causal_state"):
            bad.append(f"{oid}: causal_state changed")
        for k in set(o) | set(a):
            if k != "physical_state" and o.get(k) != a.get(k):
                bad.append(f"{oid}: field {k} changed")
        ps0, ps1 = o.get("physical_state") or {}, a.get("physical_state") or {}
        for k in set(ps0) | set(ps1):
            if (oid, k) in planned:
                if ps1.get(k) != planned[(oid, k)]:
                    bad.append(f"{oid}: physical_state.{k} != planned")
            elif ps0.get(k) != ps1.get(k):
                bad.append(f"{oid}: physical_state.{k} changed unplanned")
    return bad


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


def apply(store_path: Path, log_path: Path, p: dict, store: dict) -> int:
    from core import profile
    real = profile._data_relative(store_path.resolve()) is not None
    if real:
        if store_path.resolve() != DEFAULT_STORE.resolve():
            log_path = store_path.resolve().parent / "nascence.log"
        if not du_is_down(log_path):
            print("REFUSED: Du does not look down (last line of %s is not %r)." % (log_path, SHUTDOWN_LINE))
            return 3
    if not p["copies"]:
        print("applied: nothing to copy (already migrated); store untouched; verify=OK")
        return 0
    profile.mark_live()
    store_w = profile.guard_path(store_path)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_w = profile.guard_path(store_path.with_name(store_path.stem + f".pre_formkeys_{stamp}.json"))
    shutil.copy2(store_w, backup_w)
    print("backup:", backup_w)
    new = migrated(store, p)
    tmp = store_w.with_suffix(".tmp")
    tmp.write_text(json.dumps(new, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(store_w)
    chk = json.loads(store_w.read_text(encoding="utf-8"))
    bad = verify(store, chk, p)
    print(f"applied: {len(p['copies'])} keys copied on {p['objects_touched']} objects; objects {len(chk)}; "
          f"verify={'OK' if not bad else 'MISMATCH'}")
    for b in bad[:20]:
        print("  ", b)
    return 0 if not bad else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--nascence-log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--report", type=Path, default=None, help="write the dry-run report JSON here (not under data/)")
    ap.add_argument("--apply", action="store_true", help="really copy the keys (default: dry-run, writes nothing)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    store = json.loads(a.store.read_text(encoding="utf-8"))
    p = plan(store)
    # a dry-run also proves the planned result verifies, without writing it
    dry_bad = verify(store, migrated(store, p), p)
    rep = dict(p, store=str(a.store), mode="APPLY" if a.apply else "DRY-RUN", dry_verify=dry_bad or "OK")
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if a.report:
        if (ROOT / "data") in a.report.resolve().parents:
            print("REFUSED: --report must not be under data/")
            return 4
        a.report.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    if p["conflicts"]:
        print(f"REFUSED: {len(p['conflicts'])} conflicting Layer-2 values; resolve by hand first.")
        return 5
    if not a.apply:
        print("DRY-RUN: nothing written.")
        return 0
    return apply(a.store, a.nascence_log, p, store)


if __name__ == "__main__":
    sys.exit(main())
