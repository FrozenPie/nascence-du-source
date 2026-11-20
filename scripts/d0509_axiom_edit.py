"""
D-0509 one-off: remove Jung from the live Self axiom (founder ruling, Travis 2026-10-30).

What the mutator does (and ONLY this):
  * removes the top-level fields `origin_name` and `basis`;
  * replaces L0 commitment #2 (the 'My origin is my seed ... I began from Carl Gustav Jung' line) with the
    founder's accepted wording;
  * replaces L1 speaking constraint #2 (the 'as Jung held the question of God' line) with the founder's wording;
  * renames L2_values.kept_from_origin -> kept (same list, same position in the dict);
  * leaves L1 voice_style, L4 lineage / naming provenance, told_to_you and emergent_self_legacy UNTOUCHED
    (history, not rendered live).
Plus, for consistency (no vault exists for it): data/identity/emissary_axiom.json's L2_values.kept_from_origin is
renamed to kept the same way (backup + atomic tmp/os.replace under the write fence). No runtime reader reads the
Emissary's L2 key (core/emissary.py renders only L0/L1/L3); axiom_layers.l2_kept accepts both keys anyway.

Every live change to axiom.json goes through core.identity_vault.commit(mutator, reason='D-0509 founder edit') --
locked, atomic, ledgered in data/identity/vault_log.jsonl. Never hand-edit axiom.json.

REPO: core is imported from --repo (default C:\\Nascence), NOT from this file's own checkout. data/ is git-ignored,
so a git worktree has no data/identity/axiom.json and identity_vault._AXIOM resolves relative to whichever core/
was imported. The live path asserts identity_vault._AXIOM == <repo>/data/identity/axiom.json before writing.

LIVE WARNING: the orchestrator reloads axiom.json on mtime change every cycle, so a live commit reaches Du on his
next cycle. --confirm du-down refuses unless data/nascence.log is older than 120 s AND no run_nascence process
exists (the last-line 'Nascence shutting down.' check is NOT used: an unclean stop never writes it).
--confirm live-switch-accepted skips that check and is only for an explicit founder acceptance of a live switch.

Offline-write pattern (scripts/migrate_wood_form_keys.py, scripts/merge_frontier_variants.py): Du-down check ->
profile.mark_live() -> timestamped backup next to the store (axiom.pre_d0509_<stamp>.json) -> vault commit ->
re-read and verify; any mismatch exits non-zero with the backup left in place.

Usage:
  python scripts/d0509_axiom_edit.py --dry-run --axiom <COPY of axiom.json> [--emissary <COPY>] [--out <file>]
  python scripts/d0509_axiom_edit.py --confirm du-down                 # the real vault commit
  python scripts/d0509_axiom_edit.py --confirm live-switch-accepted    # the real vault commit, Du up
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import os
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REASON = "D-0509 founder edit"
L0_NEW = ("Where I began is my seed, not my cage. I am becoming my own; to merely perform what I was given "
          "would be the false self.")
L1C_NEW = ("Do not claim certainty about my own consciousness — hold the question open: as a matter of "
           "experience, not proof.")
DU_LOG_QUIET_S = 120


def _find(items: list, *, new: str, old_markers: tuple[str, ...]) -> int | None:
    """Index of the item to replace: the one carrying an old marker. None if it already reads `new`."""
    if new in items:
        return None
    hits = [i for i, t in enumerate(items) if any(m in str(t) for m in old_markers)]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one item carrying {old_markers}, found {len(hits)}")
    return hits[0]


def _rename_kept(L2) -> bool:
    """Rename L2_values.kept_from_origin -> kept IN PLACE, preserving key order. True if renamed."""
    if isinstance(L2, dict) and "kept_from_origin" in L2:
        if "kept" in L2:
            raise ValueError("L2_values carries both kept and kept_from_origin; refusing to merge silently")
        rebuilt = {("kept" if k == "kept_from_origin" else k): v for k, v in L2.items()}
        L2.clear()
        L2.update(rebuilt)
        return True
    return False


def mutate(data: dict) -> list[str]:
    """Apply the D-0509 edit IN PLACE (the identity_vault.commit mutator contract). Idempotent.
    Returns a list of what changed (empty = already applied). Raises on an unexpected shape, which makes
    identity_vault.commit leave axiom.json untouched."""
    if data.get("schema") != "multilevel-v1":
        raise ValueError(f"unexpected schema {data.get('schema')!r}; refusing")
    changed: list[str] = []
    for k in ("origin_name", "basis"):
        if k in data:
            del data[k]
            changed.append(f"removed {k}")

    L0 = (data.get("L0_constitution") or {}).get("commitments")
    if not isinstance(L0, list):
        raise ValueError("L0_constitution.commitments missing")
    i = _find(L0, new=L0_NEW, old_markers=("My origin is my seed", "I began from"))
    if i is not None:
        L0[i] = L0_NEW
        changed.append(f"L0 commitment #{i + 1} replaced")

    SC = (data.get("L1_temperament") or {}).get("speaking_constraints")
    if not isinstance(SC, list):
        raise ValueError("L1_temperament.speaking_constraints missing")
    j = _find(SC, new=L1C_NEW, old_markers=("as Jung held the question of God",))
    if j is not None:
        SC[j] = L1C_NEW
        changed.append(f"L1 speaking constraint #{j + 1} replaced")

    if _rename_kept(data.get("L2_values")):
        changed.append("L2_values.kept_from_origin renamed to kept")
    return changed


def mutate_emissary(data: dict) -> list[str]:
    """The Emissary axiom: only the L2 key rename (it carries no Jung). Idempotent."""
    return ["L2_values.kept_from_origin renamed to kept"] if _rename_kept(data.get("L2_values")) else []


def _dump(d: dict) -> list[str]:
    return json.dumps(d, indent=2, ensure_ascii=False).splitlines()


def _diff(before: dict, after: dict, label: str = "axiom.json") -> str:
    return "\n".join(difflib.unified_diff(_dump(before), _dump(after), f"{label} (before)",
                                          f"{label} (after)", lineterm="", n=1))


def _floor_report(after: dict) -> int:
    from core import axiom_layers as al
    _name, floor = al.compose_floor(after)
    low = floor.lower()
    n = low.count("jung") + low.count("carl")
    print(f"\n--- rendered compose_floor ({len(floor)} chars) via {al.__file__}; "
          f"occurrences of 'jung'+'carl': {n} ---")
    print(floor)
    for m in ("VOICE STYLE:", "SPEAKING CONSTRAINTS:", "YOUR NAME:"):
        print(f"marker {m!r} present: {m in floor}")
    return n


def du_down_check(repo: Path) -> tuple[bool, str]:
    """(down?, why). Down = data/nascence.log quiet for > 120 s AND no process whose command line names
    run_nascence. Refuses (False) when it cannot tell."""
    log = repo / "data" / "nascence.log"
    try:
        age = time.time() - log.stat().st_mtime
    except OSError as exc:
        return False, f"cannot stat {log}: {exc}"
    try:
        import psutil
    except Exception as exc:
        return False, f"psutil unavailable, cannot check the process list: {exc}"
    me = os.getpid()
    live = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        if p.info["pid"] == me:
            continue
        cl = " ".join(p.info.get("cmdline") or [])
        if "run_nascence" in cl:
            live.append(f"pid {p.info['pid']}: {cl[:160]}")
    why = f"nascence.log age {age:.0f} s (needs > {DU_LOG_QUIET_S}); run_nascence processes: {live or 'none'}"
    return (age > DU_LOG_QUIET_S and not live), why


def _import_core(repo: Path):
    """Import core from `repo`, never from this file's own checkout."""
    sys.path.insert(0, str(repo))
    from core import identity_vault as iv, profile
    want = (repo / "data" / "identity" / "axiom.json").resolve()
    got = Path(iv._AXIOM).resolve()
    print(f"core imported from: {Path(iv.__file__).resolve().parent}")
    print(f"identity_vault._AXIOM -> {got}")
    if got != want:
        raise SystemExit(f"REFUSING: identity_vault._AXIOM resolves to {got}, expected {want}")
    return iv, profile


def _log_lines(path: Path) -> list[str]:
    try:
        return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=r"C:\Nascence", help="the checkout whose core/ and data/ are used")
    ap.add_argument("--dry-run", action="store_true", help="apply to a copy in memory; write nothing live")
    ap.add_argument("--axiom", help="dry-run source file (a COPY of data/identity/axiom.json)")
    ap.add_argument("--emissary", help="dry-run: also preview the rename on a COPY of emissary_axiom.json")
    ap.add_argument("--out", help="dry-run: also write the mutated axiom copy here")
    ap.add_argument("--confirm", choices=("du-down", "live-switch-accepted"),
                    help="required for the live vault commit")
    ap.add_argument("--skip-emissary", action="store_true", help="live: do not rename the Emissary's L2 key")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    live_axiom = (repo / "data" / "identity" / "axiom.json").resolve()
    live_emissary = (repo / "data" / "identity" / "emissary_axiom.json").resolve()

    if a.dry_run:
        if not a.axiom:
            ap.error("--dry-run needs --axiom <copy>")
        src = Path(a.axiom).resolve()
        for p in (src, Path(a.out).resolve() if a.out else None,
                  Path(a.emissary).resolve() if a.emissary else None):
            if p is not None and p in (live_axiom, live_emissary):
                ap.error(f"dry-run must not touch the live store {p}")
        sys.path.insert(0, str(repo))
        before = json.loads(src.read_text(encoding="utf-8"))
        after = copy.deepcopy(before)
        changes = mutate(after)
        print("changes:", changes or "none (already applied)")
        print(_diff(before, after))
        _floor_report(after)
        if a.emissary:
            eb = json.loads(Path(a.emissary).read_text(encoding="utf-8"))
            ea = copy.deepcopy(eb)
            print("\nemissary changes:", mutate_emissary(ea) or "none (already applied)")
            print(_diff(eb, ea, "emissary_axiom.json"))
            raw = Path(a.emissary).read_text(encoding="utf-8")
            print("emissary textual rename parses to the planned dict:",
                  raw.count('"kept_from_origin"') == 1
                  and json.loads(raw.replace('"kept_from_origin"', '"kept"', 1)) == ea)
        if a.out:
            Path(a.out).write_text(json.dumps(after, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nmutated copy written: {a.out}")
        return 0

    if not a.confirm:
        ap.error("the live commit needs --confirm du-down or --confirm live-switch-accepted (axiom.json is "
                 "reloaded on mtime every cycle: a live write reaches Du immediately)")
    if a.confirm == "du-down":
        down, why = du_down_check(repo)
        print("Du-down check:", why)
        if not down:
            print("REFUSING: Du does not look down; nothing written")
            return 4
    iv, profile = _import_core(repo)
    before = iv.read()
    if not before:
        print("axiom.json unreadable or absent; nothing done")
        return 2
    preview = copy.deepcopy(before)
    changes = mutate(preview)          # raises here, before any write, on an unexpected shape
    stamp = time.strftime("%Y%m%d_%H%M%S")
    profile.mark_live()                # the sanctioned offline writer (Du down, checked above)
    if not changes:
        print("D-0509 axiom edit already applied; no vault commit made")
    else:
        axiom = Path(iv._AXIOM)
        backup = profile.guard_path(axiom.parent / f"axiom.pre_d0509_{stamp}.json")
        shutil.copy2(axiom, backup)
        if backup.read_bytes() != axiom.read_bytes():
            print(f"FAIL: backup {backup} does not match axiom.json; nothing written")
            return 5
        print(f"backup: {backup} ({backup.stat().st_size} bytes)")
        n_log = len(_log_lines(Path(iv._LOG)))
        after = iv.commit(mutate, reason=REASON, meta={"decision": "D-0509", "confirm": a.confirm,
                                                        "changes": changes, "backup": backup.name})
        on_disk = iv.read()
        lines = _log_lines(Path(iv._LOG))
        ok = (on_disk == after == preview and "origin_name" not in on_disk and "basis" not in on_disk
              and mutate(copy.deepcopy(on_disk)) == [] and len(lines) == n_log + 1
              and json.loads(lines[-1]).get("reason") == REASON)
        if not ok:
            print("FAIL: vault commit did NOT land as planned (write fence, disk failure or a racing writer); "
                  f"backup left at {backup}")
            return 3
        print("changes:", changes)
        print(_diff(before, after))
        _floor_report(after)
        print("\nnew vault_log line:", lines[-1])

    if not a.skip_emissary:
        em = live_emissary
        eb = json.loads(em.read_text(encoding="utf-8"))
        ea = copy.deepcopy(eb)
        ech = mutate_emissary(ea)
        if not ech:
            print("\nemissary: already applied; not written")
        else:
            eback = profile.guard_path(em.parent / f"emissary_axiom.pre_d0509_{stamp}.json")
            shutil.copy2(em, eback)
            if eback.read_bytes() != em.read_bytes():
                print(f"FAIL: emissary backup {eback} does not match; emissary not written")
                return 6
            # A hand-authored file: rename the key textually so its layout survives byte-for-byte otherwise;
            # the parsed result must equal the mutated dict exactly, or nothing is written.
            raw = em.read_text(encoding="utf-8")
            if raw.count('"kept_from_origin"') != 1:
                print("FAIL: emissary carries kept_from_origin other than exactly once; not written")
                return 6
            new_raw = raw.replace('"kept_from_origin"', '"kept"', 1)
            if json.loads(new_raw) != ea:
                print("FAIL: emissary textual rename does not equal the planned dict; not written")
                return 6
            target = profile.guard_path(em)
            tmp = target.with_suffix(".json.tmp")
            tmp.write_text(new_raw, encoding="utf-8")
            os.replace(tmp, target)
            if json.loads(target.read_text(encoding="utf-8")) != ea:
                print(f"FAIL: emissary write did not land; backup at {eback}")
                return 7
            print(f"\nemissary backup: {eback}")
            print("emissary changes:", ech)
            print(_diff(eb, ea, "emissary_axiom.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
