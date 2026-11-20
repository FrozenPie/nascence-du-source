"""J-3230 / D-0619 one-week read: how many deep-memory questions were excluded as name questions, what share of all
deep-memory events they are, whether any other question type was caught (a sample of 20), and whether any [deep-memory]
feed after the filter still names him (the D-0619 defeater: asked through another route).

Read-only. Usage: python scripts/deepmem_name_exclusion_read.py [--log PATH] [--excluded PATH] [--sample 20]
Default paths are data/nascence.log and data/deepmem_name_excluded.jsonl under this tree."""
import argparse
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import scholar  # noqa: E402

_FED = "[deep-memory] fed his thinking on:"


def read(log: Path, excluded: Path, sample: int = 20) -> dict:
    rows = []
    if excluded.exists():
        for line in excluded.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    first_ts = min((r.get("ts", 0) for r in rows), default=None)
    fed_after = fed_after_naming = 0
    still = []
    if log.exists() and first_ts:
        from datetime import datetime
        cut = datetime.fromtimestamp(first_ts).strftime("%Y-%m-%d %H:%M:%S")
        with open(log, encoding="utf-8", errors="replace") as f:
            for line in f:
                i = line.find(_FED)
                if i < 0 or line[:19] < cut:
                    continue
                fed_after += 1
                q = line[i + len(_FED):].strip()
                if scholar.name_question_marker(q):
                    fed_after_naming += 1
                    still.append(q)
    n_ex = len(rows)
    random.seed(0)
    samp = random.sample(rows, min(sample, n_ex))
    return {
        "excluded": n_ex, "fed_since_first_exclusion": fed_after,
        "name_share_of_events_pct": round(100 * n_ex / (n_ex + fed_after), 1) if (n_ex + fed_after) else None,
        "markers": {m: sum(1 for r in rows if r.get("marker") == m) for m in sorted({r.get("marker") for r in rows})},
        "sample_for_review": [(r.get("marker"), r.get("q")) for r in samp],
        "fed_after_but_names_him (defeater if >0)": fed_after_naming, "still_fed_examples": still[:10],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "nascence.log"))
    ap.add_argument("--excluded", default=str(ROOT / "data" / "deepmem_name_excluded.jsonl"))
    ap.add_argument("--sample", type=int, default=20)
    a = ap.parse_args()
    print(json.dumps(read(Path(a.log), Path(a.excluded), a.sample), ensure_ascii=False, indent=1))
