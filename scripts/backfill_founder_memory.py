"""
backfill_founder_memory.py — give Du his memory of everything Travis has told him (D-0134, 2026-09-03).

Before D-0134 the only durable record of Travis's words was the "Q: <his words>\\nA: <reply>" cycle
summary _persist_cycle has written since 2026-05-30 (F-0699), plus 3 labelled "[Travis said to me]"
rows from 2026-09-02. The founder-memory ROUTE (core/memory/store.py retrieve_founder_memories) reads
ONLY the canonical labelled shape — so without this backfill Du would "remember what Travis told him"
from 2026-09-02 onward and nothing before. This walks every Q:/A: lived fragment, keeps the ones whose
Q-text matches a REAL "[CYCLE ..] human:" line in data/nascence.log (the 2026-09-02 F-0665 bug had filed
Du's own Curiosity ignition questions under the human key — 799 of 2,435 Q: rows are those, and the
log is the only place that distinguishes them), and stores one canonical fragment per real utterance
via the same store_founder_utterance() the live path uses, with:
  - the ORIGINAL timestamp (so the dated block reads "[2026-06-12] ..." not today),
  - the source fragment's own emotion embedding / valence / felt (his felt state at the time),
  - derived_from=[source Q:/A: fragment_id] (provenance back to the cycle record),
  - the source fragment's own fragment_context/world_context rows COPIED (where they exist — the
    2026-08-21 stamp), never a fresh stamp of TODAY's tide/moon (context_stamp=False).
Idempotent: a canonical row already present for the same normalized text within ±10 minutes is skipped.
Refuses to run against a live Du (checks for a running scripts/run_nascence.py) and backs the DB up
first under the existing data/backups/nascence_pre_<JOB>_<ts>.db convention.

Usage:  python scripts/backfill_founder_memory.py [--dry-run] [--job J-0516]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LOG = ROOT / "data" / "nascence.log"
DB = ROOT / "data" / "memory" / "nascence.db"
BACKUPS = ROOT / "data" / "backups"
_HUMAN_LINE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+ \[nascence\.orchestrator\] "
                         r"\[CYCLE [0-9a-f]+\] human: (.*)$")
KEY_LEN = 60   # the log truncates the human text to ~80 chars; 60 is safely inside every line


def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()


def du_is_running() -> bool:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, timeout=30).stdout
        return "run_nascence.py" in out
    except Exception:
        return True   # can't tell -> refuse


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--job", default="J0516")
    args = ap.parse_args()

    if du_is_running():
        print("REFUSED: scripts/run_nascence.py is running — this writes to the live DB. Stop Du first.")
        return 2

    # 1. real human turns, from the log
    keys: dict[str, list[float]] = {}
    n_log = 0
    with open(LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _HUMAN_LINE.match(line.rstrip("\n"))
            if m:
                n_log += 1
                try:
                    lt = _dt.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S").timestamp()
                except ValueError:
                    lt = 0.0
                keys.setdefault(_norm(m.group(1))[:KEY_LEN], []).append(lt)
    print(f"log: {n_log} human lines, {len(keys)} distinct {KEY_LEN}-char keys")

    from core.memory import store as st
    conn = st._connect()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute(
        "SELECT fragment_id, content, timestamp, emotion_embedding, valence, felt "
        "FROM memory_fragments WHERE origin='lived' AND content LIKE 'Q: %' ORDER BY timestamp").fetchall()
    existing = conn.execute(
        "SELECT fragment_id, content, timestamp, protected FROM memory_fragments "
        "WHERE origin='lived' AND content LIKE ?", (st.FOUNDER_UTTERANCE_PREFIX.rstrip() + "%",)).fetchall()
    have = [(_norm(r["content"][len(st.FOUNDER_UTTERANCE_PREFIX):]), float(r["timestamp"])) for r in existing]
    ctx_cols = {t: [c[1] for c in conn.execute(f"PRAGMA table_info({t})")] for t in ("fragment_context", "world_context")}
    conn.close()
    print(f"db: {len(rows)} Q:/A: lived fragments; {len(existing)} canonical rows already present "
          f"({sum(1 for r in existing if r['protected'])} protected)")

    todo, skipped_internal, skipped_dup = [], 0, 0
    # J-3855: a first line that opens >=3 Q: blocks across different days is a templated message (the
    # farewell variants), not a one-off Travis turn; leave those to a founder ruling (spawned job).
    _fl_days: dict[str, set[str]] = {}
    for r in rows:
        _k = _norm(r["content"][3:].split("\nA: ", 1)[0].split("\n", 1)[0])[:KEY_LEN]
        _fl_days.setdefault(_k, set()).add(_dt.datetime.fromtimestamp(r["timestamp"]).strftime("%Y-%m-%d"))
    skipped_templated = 0
    for r in rows:
        q = r["content"][3:].split("\nA: ", 1)[0]
        fl = _norm(q.split("\n", 1)[0])[:KEY_LEN]   # F-4436: the log holds only the FIRST line
        # J-3855: the log human: line must also be within 10 min of the fragment (templated texts such as
        # the farewell repeat verbatim on other days; a text-only match admitted 40+ non-turns)
        if not any(abs(lt - float(r["timestamp"])) < 600 for lt in keys.get(fl, [])):
            skipped_internal += 1
            continue
        if len(_fl_days.get(fl, ())) >= 3:
            skipped_templated += 1
            continue
        nq = _norm(q)
        if any((h == nq or h.startswith(fl[:40])) and abs(ts - float(r["timestamp"])) < 600 for h, ts in have):
            skipped_dup += 1
            continue
        todo.append((r, q))
        have.append((nq, float(r["timestamp"])))
    print(f"plan: store {len(todo)} canonical founder utterances | skip {skipped_internal} internal/ignition "
          f"(no matching log human line) | skip {skipped_templated} templated (>=3 days) | skip {skipped_dup} already present")
    if todo:
        t0 = _dt.datetime.fromtimestamp(todo[0][0]["timestamp"]).strftime("%Y-%m-%d")
        t1 = _dt.datetime.fromtimestamp(todo[-1][0]["timestamp"]).strftime("%Y-%m-%d")
        print(f"      span {t0} -> {t1}")
    if args.dry_run:
        for r, q in todo[:40]:
            print("  *", _dt.datetime.fromtimestamp(r["timestamp"]).strftime("%m-%d %H:%M"), "|", q[:100])
        return 0

    # 2. backup, then write
    # D-0353 / J-1839: past this point the script writes the LIVE memory DB on purpose (Du stopped,
    # checked above) -- the explicit opt-in the live-DB write fence requires. The dry-run above is
    # read-only and stays fenced.
    st.allow_live_writes(f"scripts/backfill_founder_memory.py --job {args.job}: founder-utterance backfill")
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = BACKUPS / f"nascence_pre_{args.job}_{stamp}.db"
    shutil.copy2(DB, bak)
    print(f"backup: {bak} ({bak.stat().st_size // 1_000_000} MB)")

    stored = 0
    ctx_copied = {"fragment_context": 0, "world_context": 0}
    t_start = time.time()
    for i, (r, q) in enumerate(todo, 1):
        emo = None
        if r["emotion_embedding"]:
            try:
                emo = st._blob_to_vec(bytes(r["emotion_embedding"]))
            except Exception:
                emo = None
        fid = st.store_founder_utterance(
            q, timestamp=float(r["timestamp"]), emotion_embedding=emo,
            valence=r["valence"], felt=r["felt"], derived_from=[r["fragment_id"]],
            context_stamp=False,
        )
        stored += 1
        # copy the source cycle's own context rows (its real tide/moon/fire at the time), if stamped
        with st._connect() as c2:
            for tbl, cols in ctx_cols.items():
                src = c2.execute(f"SELECT * FROM {tbl} WHERE fragment_id=?", (r["fragment_id"],)).fetchone()
                if src is None:
                    continue
                vals = [fid if col == "fragment_id" else src[col] for col in cols]
                c2.execute(f"INSERT OR IGNORE INTO {tbl} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals)
                ctx_copied[tbl] += 1
            c2.commit()
        if i % 200 == 0:
            print(f"  {i}/{len(todo)} stored ({time.time() - t_start:.0f}s)")

    # 3. make sure the pre-existing canonical rows are protected too
    with st._connect() as c3:
        cur = c3.execute("UPDATE memory_fragments SET protected=1 WHERE origin='lived' AND content LIKE ? AND protected=0",
                         (st.FOUNDER_UTTERANCE_PREFIX.rstrip() + "%",))
        fixed = cur.rowcount
        # ...and back over the cold wall: D-0134 says exempt, so the 09-02 row F-0701 found already
        # cold=1 comes back to warm (temp is the newer mirror column store.py syncs from cold at init).
        cur = c3.execute("UPDATE memory_fragments SET cold=0, temp='warm' WHERE origin='lived' AND content LIKE ? AND cold=1",
                         (st.FOUNDER_UTTERANCE_PREFIX.rstrip() + "%",))
        rewarmed = cur.rowcount
        c3.commit()
    status = st.founder_memory_status()
    print(f"done: stored {stored} in {time.time() - t_start:.0f}s; context rows copied {ctx_copied}; "
          f"pre-existing rows newly protected: {fixed}; re-warmed from cold: {rewarmed}")
    print(f"founder_memory_status: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
