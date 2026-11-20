"""J-3090 lab runner: re-grade the post-fix decomposed-critic rejections inside lab_env.isolate().

Reads the LIVE critic_shadow_alongside.jsonl / llm_latency.jsonl / emissary_axiom.json read-only, calls ONE local
non-gemma, non-qwen grader hub per run, writes ONLY under docs/lab/J-3090_data/. isolate(db="empty") redirects the
shared store's DB_PATH away from the live nascence.db as a backstop (scripts/critic_grade.py never touches it);
the live DB's size+mtime are printed before and after.

  python scripts/_lab_J-3090_regrade.py <model> <port> [--per-flag|--per-row] [--neutral] [--since 2026-07-06]
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import core  # noqa: F401  (core BEFORE lab_env: see lab_env F-2423)
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

import critic_grade as cg  # noqa: E402

LIVE = Path(r"C:\Nascence\data")
OUTDIR = ROOT / "docs" / "lab" / "J-3090_data"


def _live_db_sig() -> tuple[int, float] | None:
    p = LIVE / "memory" / "nascence.db"
    try:
        st = p.stat()
        return (st.st_size, st.st_mtime)
    except OSError:
        return None


def main() -> None:
    model, port = sys.argv[1], sys.argv[2]
    per_flag = "--per-row" not in sys.argv
    since = "2026-07-06"
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    task = "neutral" if "--neutral" in sys.argv else "emissary"
    tag = model.split(":")[0] + ("_flag" if per_flag else "_row") + ("_neutral" if task == "neutral" else "")
    before = _live_db_sig()
    print("live DB before:", before)
    cg._emissary._AXIOM_PATH = LIVE / "identity" / "emissary_axiom.json"
    cg._emissary._cache = None
    with isolate(db="empty"):
        asyncio.run(cg.main(
            200, since=since, per_flag=per_flag, exclude_failed=LIVE / "llm_latency.jsonl",
            url=f"http://127.0.0.1:{port}", model=model, timeout_s=900.0, task=task,
            shadow=LIVE / "logs" / "critic_shadow_alongside.jsonl",
            out=OUTDIR / f"grades_{tag}.jsonl"))
    after = _live_db_sig()
    print("live DB after :", after, "UNCHANGED" if before == after else "CHANGED (!!)")


if __name__ == "__main__":
    main()
