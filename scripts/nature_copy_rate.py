"""
nature_copy_rate.py -- J-2958 (F-3651): how much of a nature-study observation is copied from the scene it was shown.

Reads data/nature_study_log.jsonl rows that carry the `scene` + `observation` keys (logged since J-2958; older rows
have no scene and are counted as `no_scene`, never guessed). For each row the copy rate is the share of the
observation's content words (len >= 4) that also occur in the scene, plus the share of the observation's word
trigrams that occur verbatim in the scene. High on both = a paraphrase of the scene; low = particulars the scene did
not hold (invented or seen elsewhere). The `observation` key is cut at 300 chars by the writer, so the rate is over
that prefix (obs_chars says how long the full one was).

Read-only. Run: python -X utf8 scripts/nature_copy_rate.py [--n 20] [--data DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEFAULT_DATA = Path(r"C:\Nascence\data")
_W = re.compile(r"[a-z']+")


def _words(t: str) -> list[str]:
    return _W.findall(str(t or "").lower())


def copy_rate(scene: str, obs: str) -> dict:
    sw, ow = _words(scene), _words(obs)
    sset = {w for w in sw if len(w) >= 4}
    ocontent = [w for w in ow if len(w) >= 4]
    word = (sum(1 for w in ocontent if w in sset) / len(ocontent)) if ocontent else None
    s3 = {tuple(sw[i:i + 3]) for i in range(len(sw) - 2)}
    o3 = [tuple(ow[i:i + 3]) for i in range(len(ow) - 2)]
    tri = (sum(1 for g in o3 if g in s3) / len(o3)) if o3 else None
    return {"word_share": word, "trigram_share": tri}


def read(rows: list[dict], n: int = 20) -> dict:
    withscene = [r for r in rows if r.get("scene") and r.get("observation")]
    last = withscene[-n:]
    rates = [copy_rate(r["scene"], r["observation"]) for r in last]

    def mean(k):
        v = [x[k] for x in rates if x[k] is not None]
        return round(sum(v) / len(v), 3) if v else None
    return {"rows": len(rows), "no_scene": len(rows) - len(withscene), "measured": len(last),
            "mean_word_share": mean("word_share"), "mean_trigram_share": mean("trigram_share"),
            "enough": len(last) >= n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    a = ap.parse_args()
    rows = []
    try:
        for ln in (a.data / "nature_study_log.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    except OSError:
        pass
    r = read(rows, a.n)
    print(json.dumps(r, indent=1))
    print("ENOUGH" if r["enough"] else f"NOT ENOUGH: {r['measured']}/{a.n} lessons carry a scene yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
