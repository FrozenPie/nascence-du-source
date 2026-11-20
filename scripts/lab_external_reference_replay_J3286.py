"""J-3286 / D-0662 replay: how many PAST epistemic assessments would change if a looked-up page (fragment
origin='research') counted as SourceType.EXTERNAL_REFERENCE (grounded, strength 3, capped at THINK) instead of
falling through to MEMORY_RECALL (strength 4)?

The founder's defeater (D-0662): "revisit if the replay shows the change moves more than a handful of past grades".

Method (read-only, observe-only). data/provenance_log.jsonl carries each voiced cycle's grade + its four ModelProvenance
rows; data/recall_served_log.jsonl (J-2576) carries the same cycle's served fragments with their origin. Joined on
cycle_id, the world model's dominant source is RE-DERIVED from the fragment origins under two mappings (OLD: research ->
MEMORY_RECALL, NEW: research -> EXTERNAL_REFERENCE), and the grade is re-computed by the real
ProvenanceLedger._grade on the logged evidence picture. Rows where the OLD replay does not reproduce the logged
grade and dominant source are reported as 'unfaithful' and left out of the headline count (the served-log set can differ
from state.memory_fragments, e.g. the ephemeral parametric_library fragment is appended after it).

Run against COPIES of the live logs, never the live files:
    python scripts/lab_external_reference_replay_J3286.py --provenance <copy> --served <copy> [--out report.json]
Writes nothing but the optional --out file.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE anything else)
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import source_model as sm  # noqa: E402
from core.epistemic_state import ModelProvenance, ProvenanceLedger  # noqa: E402
from core.source_model import SourceType, Verification  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def _rows(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def _dominant(origins, mapping_research: SourceType) -> str | None:
    """strongest grounded source among the served origins, or None when none is grounded. `mapping_research` is what
    origin 'research' maps to under the mapping being replayed; every other origin uses the live mapping."""
    srcs = []
    for o in origins:
        s = mapping_research if (o or "").lower().strip() == "research" else sm.source_of_origin(o)
        if sm.is_grounded(s):
            srcs.append(s)
    return sm.strongest(srcs).value if srcs else None


def _regrade(row: dict, dominant: str) -> str:
    world = None
    models = []
    for m in row.get("models") or []:
        mp = ModelProvenance(**{k: m[k] for k in ModelProvenance.__dataclass_fields__})
        models.append(mp)
        if mp.model == "world":
            world = mp
    if world is None:
        return row.get("grade", "")
    world = ModelProvenance(**{**world.as_dict(), "dominant_source": dominant})
    depended = [world if m.model == "world" else m for m in models if m.depended_on]
    return ProvenanceLedger._grade(world, Verification(row.get("verification", "none")),
                                   depended, float(row.get("self_reported_confidence", 0.5)))


def replay(provenance: Path, served: Path) -> dict:
    by_cycle = {}
    for r in _rows(served):
        cid = r.get("cycle_id")
        if cid and r.get("path", "voice") == "voice":
            by_cycle[cid] = r
    out = {"provenance_rows": 0, "joined": 0, "with_research_fragment": 0, "faithful": 0,
           "changed_dominant": 0, "changed_grade": 0, "grade_moves": Counter(), "examples": [], "unfaithful": 0,
           "faithful_with_research": 0}
    for row in _rows(provenance):
        out["provenance_rows"] += 1
        sv = by_cycle.get(row.get("cycle_id"))
        if sv is None:
            continue
        out["joined"] += 1
        origins = [f.get("origin") for f in sv.get("fragments") or []]
        has_research = any((o or "").lower().strip() == "research" for o in origins)
        if has_research:
            out["with_research_fragment"] += 1
        old_dom = _dominant(origins, SourceType.MEMORY_RECALL)
        new_dom = _dominant(origins, SourceType.EXTERNAL_REFERENCE)
        logged_dom = next((m.get("dominant_source") for m in row.get("models") or [] if m.get("model") == "world"), None)
        # fidelity: the OLD replay must reproduce the logged world dominant source (when anything was grounded) and grade
        old_grade = _regrade(row, old_dom or logged_dom or "none")
        faithful = (old_dom == logged_dom or (old_dom is None and logged_dom in (None, "none", "conversation_context", "memory_recall"))) \
            and old_grade == row.get("grade")
        if not faithful:
            out["unfaithful"] += 1
            continue
        out["faithful"] += 1
        if has_research:
            out["faithful_with_research"] += 1
        if new_dom == old_dom:
            continue
        new_grade = _regrade(row, new_dom or "none")
        out["changed_dominant"] += 1
        if new_grade != old_grade:
            out["changed_grade"] += 1
            out["grade_moves"][f"{old_grade}->{new_grade}"] += 1
            if len(out["examples"]) < 8:
                out["examples"].append({"cycle_id": row.get("cycle_id"), "ts": row.get("ts"),
                                        "old": old_grade, "new": new_grade, "old_dom": old_dom, "new_dom": new_dom,
                                        "verification": row.get("verification"),
                                        "self_reported_confidence": row.get("self_reported_confidence")})
    out["grade_moves"] = dict(out["grade_moves"])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provenance", type=Path, required=True)
    ap.add_argument("--served", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    res = replay(a.provenance, a.served)
    print(json.dumps(res, indent=2, default=str))
    if a.out:
        a.out.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
