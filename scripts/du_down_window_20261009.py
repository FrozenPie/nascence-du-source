"""One-command runbook for the 2026-10-09 Du-down window. OPERATOR SCRIPT -- run it yourself, Du must be DOWN.

Runs, in this order, stopping at the first failing step (every step has its own Du-down check, backup and manifest):
  1. J-1976  tod/season backfill of 65,687 fragment_context rows      (scripts/backfill_phase_J1970.py)
  2. J-1965  D-0362 (C) clear of the 277-fragment active-reading batch (scripts/chapter_id_repair_apply_D0362C.py)
  3. J-1987  relabel 337 stored system sentences to origin=system_note  (scripts/relabel_system_notes_J1987.py)
  4. J-2023  D-0357 exact-duplicate reclaim: census -> dryrun -> apply -> validate -> retrieve-check
                                                                        (scripts/dedup_reclaim_D0357.py)
Every step is reversible from its manifest (see each script's `revert` mode). Nothing here starts Du or a server.

Usage:  python scripts/du_down_window_20261009.py            (all steps)
        python scripts/du_down_window_20261009.py --only 2   (one step; numbers as above)
        python scripts/du_down_window_20261009.py --dry      (print the commands, run nothing)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Nascence")
PY = sys.executable
WORK = ROOT / "data" / "backups" / "du_down_window_20261009"
LOG = WORK / "run.log"
DB = str(ROOT / "data" / "memory" / "nascence.db")
S = ROOT / "scripts"

PLAN = WORK / "dedup_plan.json"
DRY = WORK / "dedup_dryrun.json"
RETR = WORK / "dedup_retrieve_check.json"
DEDUP_MANIFEST = ROOT / "docs" / "reviews" / "dedup_D0357_J-1848_manifest.json"

STEPS = {
    1: ("J-1976 phase backfill", [
        [PY, str(S / "backfill_phase_J1970.py"), "precheck"],
        [PY, str(S / "backfill_phase_J1970.py"), "apply", "--live", "--manifest",
         str(ROOT / "data" / "backups" / "J-1970_backfill_manifest_J-1976.json")],
    ]),
    2: ("J-1965 chapter_id clear", [
        [PY, str(S / "chapter_id_repair_apply_D0362C.py"), "dryrun"],
        [PY, str(S / "chapter_id_repair_apply_D0362C.py"), "apply", "--live"],
    ]),
    3: ("J-1987 system_note relabel", [
        [PY, str(S / "relabel_system_notes_J1987.py"), "dryrun"],
        [PY, str(S / "relabel_system_notes_J1987.py"), "apply", "--live"],
    ]),
    4: ("J-2023 dedup reclaim", [
        [PY, str(S / "dedup_reclaim_D0357.py"), "census", "--db", DB, "--plan", str(PLAN)],
        [PY, str(S / "dedup_reclaim_D0357.py"), "dryrun", "--plan", str(PLAN), "--out", str(DRY)],
        [PY, str(S / "dedup_reclaim_D0357.py"), "apply", "--plan", str(PLAN), "--live", "--manifest", str(DEDUP_MANIFEST)],
        [PY, str(S / "dedup_reclaim_D0357.py"), "validate", "--db", DB, "--manifest", str(DEDUP_MANIFEST), "--plan", str(PLAN)],
        [PY, str(S / "dedup_reclaim_D0357.py"), "retrieve-check", "--manifest", str(DEDUP_MANIFEST), "--dryrun", str(DRY),
         "--out", str(RETR)],
    ]),
}


def run(cmd: list[str], dry: bool) -> int:
    line = " ".join(cmd)
    print(f"\n$ {line}", flush=True)
    if dry:
        return 0
    with open(LOG, "a", encoding="utf-8") as lf:
        lf.write(f"\n[{time.strftime('%H:%M:%S')}] $ {line}\n")
        p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
        for out in p.stdout:
            sys.stdout.write(out); lf.write(out)
        p.wait()
        lf.write(f"[exit {p.returncode}]\n")
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", type=int, choices=sorted(STEPS))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    if not a.dry:
        import importlib.util
        spec = importlib.util.spec_from_file_location("bf", S / "backfill_phase_J1970.py")
        bf = importlib.util.module_from_spec(spec); sys.modules["bf"] = bf; spec.loader.exec_module(bf)
        down, why = bf.du_is_down()
        print("Du down check:", down, "--", why)
        if not down:
            print("ABORT: Du is not verifiably down. Nothing was run.")
            return 1
    todo = [a.only] if a.only else sorted(STEPS)
    for n in todo:
        title, cmds = STEPS[n]
        print(f"\n===== STEP {n}: {title} =====", flush=True)
        for c in cmds:
            rc = run(c, a.dry)
            if rc != 0:
                print(f"\n!!! STEP {n} stopped: exit {rc}. Later steps NOT run. See {LOG}. Each script has a revert mode.")
                return rc
        print(f"===== STEP {n} OK =====", flush=True)
    print("\nAll requested steps finished. Tell Claude: it will commit the manifests, record findings, close J-1976/J-1965/"
          "J-1987/J-2023/J-1948/J-1848 and spawn the post-boot reads. Then you can start Du.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
