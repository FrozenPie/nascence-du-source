"""
J-3403 / D-0682 -- Salience ablation FOLLOW-UP: the high-urgency stratum only, once there are enough cycles.

Thin wrapper over scripts/lab_salience_ablation_J3164.py (that file is not edited).  It re-points the J-3164 harness at
docs/lab/J-3403_data/, restricts the arms to A1 (as logged), A2 (as logged, 2nd draw = noise-floor CONTROL) and U (urgency
word replaced by the deterministic one), and samples ONLY word-format Executive cycles whose logged urgency word is
"high" or "pressing".  It REFUSES to sample until at least MIN_CYCLES (60) distinct such cycles exist in the (copied) log.

    python scripts/lab_salience_hi_J3403.py count            # how many qualifying cycles exist right now (read-only)
    python scripts/lab_salience_hi_J3403.py sample           # gate: >= 60 distinct cycles, else exit 3 and write nothing
    python scripts/lab_salience_hi_J3403.py gen              # hot lane qwen3.5:9b (:11433), 3 arms per cycle
    python scripts/lab_salience_hi_J3403.py judge falcon     # falcon3:7b on :11440 (different family from the author arm)
    python scripts/lab_salience_hi_J3403.py report           # -> docs/lab/J-3403_data/report.json

Mixtral (Ramses) is deliberately NOT a judge arm here: Ramses is the founder's gaming machine.  A second local judge of a
different family (gemma4:12b on :11439) can be added to JUDGES below.

Live data is only ever COPIED (by the J-3164 helper) into a scratch dir and read from the copy.  Du must be down.
Nothing here writes to C:\\Nascence or calls Ramses.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MIN_CYCLES = 60
HI_WORDS = ("high", "pressing")

_spec = importlib.util.spec_from_file_location("lab_sal_3164", ROOT / "scripts" / "lab_salience_ablation_J3164.py")
lab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lab)

# re-point the harness (all phase functions read these module globals at call time)
lab.DATA = ROOT / "docs" / "lab" / "J-3403_data"
lab.SCRATCH = Path(tempfile.gettempdir()) / "J-3403"
lab.ARMS = ("A1", "A2", "U")
lab.PAIRS = (("A1", "A2"), ("A1", "U"))                 # A1-A2 is the control
lab.JUDGES = {"falcon": lab.JUDGES["falcon"]}            # local only, no Ramses


def qualifying(ex: list[dict], sal_by: dict) -> list[dict]:
    """Distinct (first-seen cycle_id) word-format Executive rows whose logged urgency word is high or pressing."""
    seen, out = set(), []
    for r in ex:
        m = lab._SAL_RE.search(r.get("user_prompt", ""))
        if not m or m.group(1) not in HI_WORDS or r["cycle_id"] in seen:
            continue
        seen.add(r["cycle_id"])
        s = sal_by.get(r["cycle_id"])
        r["_word"] = m.group(1)
        r["_model_urgency"] = s["output"].get("urgency") if s and isinstance(s.get("output"), dict) else None
        out.append(r)
    return out


def _load() -> tuple[list[dict], dict]:
    lab._copy_live()
    ex = lab._read_jsonl(lab.SCRATCH / "executive.jsonl")
    sal_by: dict = {}
    for s in lab._read_jsonl(lab.SCRATCH / "salience.jsonl"):
        sal_by.setdefault(s["cycle_id"], s)
    return ex, sal_by


def phase_count() -> int:
    ex, sal_by = _load()
    q = qualifying(ex, sal_by)
    c = Counter((r["input_type"], r["_word"]) for r in q)
    print(f"qualifying distinct word-format high/pressing Executive cycles: {len(q)} (gate {MIN_CYCLES}) {dict(c)}")
    if q:
        print(f"newest qualifying ts: {max(r['ts'] for r in q)}")
    return len(q)


def phase_sample() -> int:
    ex, sal_by = _load()
    q = qualifying(ex, sal_by)
    if len(q) < MIN_CYCLES:
        print(f"GATE NOT MET: {len(q)} < {MIN_CYCLES} qualifying cycles; nothing written.")
        return 3
    _, detect_corr = lab._core_funcs()
    out = lab.DATA / "sample.jsonl"
    if out.exists():
        out.unlink()
    for r in q:
        corr = detect_corr(r["raw_input"]) if r["input_type"] == "human" else None
        word, why = lab.det_urgency(r["input_type"], r["raw_input"], corr)
        lab._append(out, {"cycle_id": r["cycle_id"], "ts": r["ts"], "input_type": r["input_type"], "raw_input": r["raw_input"],
                          "logged_word": r["_word"], "logged_numeric_urgency": r["_model_urgency"],
                          "det_word": word, "det_why": why, "system_prompt": r["system_prompt"],
                          "user_prompt": r["user_prompt"], "logged_output": r["output"]})
    print(f"sampled {len(q)} high/pressing cycles -> {out}")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "count":
        phase_count()
    elif cmd == "sample":
        return phase_sample()
    elif cmd == "gen":
        lab.phase_gen()
    elif cmd == "judge":
        lab.phase_judge(sys.argv[2] if len(sys.argv) > 2 else "falcon", "--follow" in sys.argv, lab.PAIRS)
    elif cmd == "report":
        lab.phase_report()
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
