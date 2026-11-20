"""
J-2673 -- negative-control arm for the J-2663 placement effect (place and weather).
Pre-registration sheet: docs/lab/rank_matched_negctrl_J-2673_2026-11-16.md (committed before any judge call).

Reuses scripts/lab_rank_matched_replication.py (and through it lab_rank_matched_control.py) UNCHANGED. The only additions:
  1. after load_cohort(), the arm dimension's coordinate codes are permuted (fixed seed) among the fragments that have a code
     (code >= 0), so the context-match term still re-sorts the pool but carries no real information;
  2. a new query seed (SEED2) and exclusion of the J-2657 ids AND the J-2663 ids (place and weather results files).
Usage: python scripts/lab_rank_matched_negctrl_J-2673.py --arm place|weather --n 90 --out <json> --cache <jsonl> --lab-root <dir> [--stage items]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT))
sys.path.insert(0, str(WT / "scripts"))
import lab_rank_matched_replication as r                   # J-2663 driver, unchanged

PERM_SEED = 20261031 + 2673 + 77
r.SEED2 = 20261031 + 2673                                    # new query seed (J-2663 used 20261031 + 2663)
LAB = WT / "docs" / "lab"
J63 = {a: LAB / f"rank_matched_replication_2026-10-31_results_{a}.json" for a in ("place", "weather")}
_orig_used = r.used_ids


def used_ids_ext():
    used, d = _orig_used()
    ext = {a: list(v) for a, v in used.items()}
    for a, p in J63.items():
        dd = json.load(open(p, encoding="utf-8"))
        ext.setdefault(a + "_J2663", []).extend(it["query_id"] for it in dd["items"])
    return ext, d


r.used_ids = used_ids_ext


def _arm_from_argv():
    return sys.argv[sys.argv.index("--arm") + 1]


def patch_cohort():
    import lab_geometric_perturbation_sweep as v1
    orig = v1.load_cohort
    arm = _arm_from_argv()

    def load_permuted(*a, **k):
        C = orig(*a, **k)
        code = C.code[arm]
        idx = np.nonzero(code >= 0)[0]
        rng = np.random.default_rng(PERM_SEED + r.OFF[arm])
        vals = code[idx].copy()
        rng.shuffle(vals)
        new = code.copy()
        new[idx] = vals
        print(f"NEGCTRL permuted {arm} codes among {len(idx)} coded fragments; unchanged positions "
              f"{int((new[idx] == code[idx]).sum())}/{len(idx)} (chance agreement expected)", flush=True)
        C.code[arm] = new
        return C
    v1.load_cohort = load_permuted


if __name__ == "__main__":
    import core                                            # core BEFORE lab_env
    assert str(Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
    lab_root = None
    for i, x in enumerate(sys.argv):
        if x == "--lab-root":
            lab_root = Path(sys.argv[i + 1]); del sys.argv[i:i + 2]; break
    assert lab_root is not None
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env, os
    lab_env._LAB_ROOT = lab_root
    lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    patch_cohort()
    with lab_env.isolate(db="empty") as _lab:
        assert str(Path(_lab).resolve()).lower().startswith(str(lab_root.resolve()).lower()), _lab
        os.environ["J2663_LAB_DIR"] = str(_lab)
        r.main()
