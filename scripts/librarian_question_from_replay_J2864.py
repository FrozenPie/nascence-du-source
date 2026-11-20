"""J-2864 / F-3538 replay: old vs new core.librarian.question_from over Du's real raw thoughts.

Reads data/deliberation_log.jsonl READ-ONLY (the pre-grounding text the monologue hands the extractor,
lower-cased as the call site does), runs the pre-J-2864 extractor (loaded from git, default rev
223c95c6) and the current one on every row since --since (default 2026-09-03), and writes a summary and
the flip table under docs/lab/J-2864_data/. No model calls, no live writes.

    python scripts/librarian_question_from_replay_J2864.py [--log PATH] [--rev REV] [--since TS]
"""
import sys, os, json, re, subprocess, tempfile, importlib.util, collections, random
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import librarian as new  # noqa: E402  (core before any lab env)

INTERROG = re.compile(r"^(?:what|why|how|whether|if|who|where|when|which)\b", re.I)


def load_old(rev: str):
    src = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:core/librarian.py"],
                         capture_output=True, check=True).stdout.decode("utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="j2864_old_")) / "old_librarian.py"
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("old_librarian_j2864", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kind(q):
    if q is None:
        return "none"
    if q.startswith("the question of"):
        return "question_of"
    return "interrogative" if INTERROG.match(q) else "declarative"


def main():
    a = sys.argv[1:]
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    log = Path(opt("--log", "C:/Nascence/data/deliberation_log.jsonl"))
    rev = opt("--rev", "223c95c6")
    since = float(opt("--since", "1788400000"))
    out = Path(opt("--out", str(ROOT / "docs" / "lab" / "J-2864_data")))
    old = load_old(rev)
    c_old, c_new = collections.Counter(), collections.Counter()
    flips = []
    n = 0
    with open(log, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("ts", 0) < since:
                continue
            t = (d.get("raw") or "").lower()
            if not t:
                continue
            n += 1
            qo, qn = old.question_from(t), new.question_from(t)
            c_old[kind(qo)] += 1
            c_new[kind(qn)] += 1
            if qo != qn:
                flips.append({"ts": d.get("ts"), "old": qo, "new": qn, "kind_old": kind(qo), "kind_new": kind(qn)})
    summary = {"rows_scanned": n, "old_rev": rev, "old": dict(c_old), "new": dict(c_new),
               "n_changed": len(flips),
               "old_declarative_rate": round(c_old["declarative"] / max(1, n - c_old["none"]), 3),
               "new_declarative_rate": round(c_new["declarative"] / max(1, n - c_new["none"]), 3)}
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    random.seed(2864)
    sample = random.sample(flips, min(60, len(flips)))
    (out / "replay_flip_sample.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in sample) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    for x in sample[:25]:
        print(f"  {x['kind_old']:>13} -> {x['kind_new']:<13} {x['old']!r}\n{'':>32}=> {x['new']!r}")


if __name__ == "__main__":
    main()
