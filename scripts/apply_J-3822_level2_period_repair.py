"""J-3822 (D-0727, J-3758, J-3010 / F-3713): repair the stored 'period' label of the 9 mislabelled level-2 chapters.

Each level-2 chapter's content starts '[A chapter of my life -- 'Title' (<Month DD> to <Month DD>)] body'. The label was
written from the member chapters' FORMATION times; the right span is the earliest start / latest end of the members' own
stored periods (core.chapters._cluster_span). Ruling D-0727: repair from the stored spans, backed-up one-shot script,
NO re-embed (the embedding column is never touched).

Touches, per fragment_id, ONLY: the '(A to B)' inside the leading bracket of `content`, and `content_hash` (derived
from content, blake2b of the exact content: left stale it would break the exact-dedup index, so it is re-stamped the
same way core/memory/store.py does for edited content). Every other column and the chapter body are left alone.

Default is a DRY RUN. --apply refuses unless Du is down (no run_nascence process), takes a sqlite-backup of the DB
first, applies in one transaction, and re-verifies. Idempotent: a row already carrying the right label is skipped.
Usage:  python scripts/apply_J-3822_level2_period_repair.py [--db PATH] [--apply]
"""
import sys, re, time, sqlite3, argparse, shutil, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401,E402  (before anything that touches sys.path)
from core.chapters import _cluster_span, _SPAN_RE  # noqa: E402
from core.memory.content_hash import content_hash, has_hash_column  # noqa: E402

# The 9 fragment-id prefixes the ruling covers (docs/lab/J-3010_data/level2_spans_J-3010.txt). The two level-2
# chapters formed later (9cd9f5b2, a406d224) already carry correct labels and are not in this set.
TARGETS = ["8007e495", "16c6727b", "8399c369", "2b552e9a", "bd24c821", "ec8a7311", "5a2364de", "55aeb059", "c8f88b32"]
fmt = lambda t: time.strftime("%B %d", time.localtime(t))


def du_running() -> bool:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_nascence' -and "
                          "$_.CommandLine -notmatch 'Get-CimInstance' } | Measure-Object | Select-Object -Expand Count"],
                         capture_output=True, text=True).stdout.strip()
    return out not in ("0", "")


def plan(c):
    rows = []
    for ch in c.execute("SELECT fragment_id, chapter_level, content FROM memory_fragments "
                        "WHERE origin='chapter' AND chapter_level=2 ORDER BY timestamp").fetchall():
        if ch["fragment_id"][:8] not in TARGETS:
            continue
        mem = [{"id": r["fragment_id"], "content": r["content"] or "", "ts": float(r["timestamp"])} for r in c.execute(
            "SELECT fragment_id, content, timestamp FROM memory_fragments WHERE chapter_id=?", (ch["fragment_id"],))]
        if not mem:
            raise SystemExit(f"{ch['fragment_id']}: no members linked, refusing")
        t0, t1 = _cluster_span(mem, 1)
        new_label = f"({fmt(t0)} to {fmt(t1)})"
        content = ch["content"]
        close = content.find("] ")
        head = content[:close + 1]
        m = list(re.finditer(r"\([A-Z][a-z]+ \d{1,2} to [A-Z][a-z]+ \d{1,2}\)", head))
        if len(m) != 1 or not _SPAN_RE.search(head):
            raise SystemExit(f"{ch['fragment_id']}: expected exactly one period label in the bracket, got {len(m)}")
        old_label = m[0].group(0)
        new_content = head[:m[0].start()] + new_label + head[m[0].end():] + content[close + 1:]
        assert new_content[m[0].end() - len(old_label) + len(new_label):] == content[m[0].end():], "body changed"
        rows.append((ch["fragment_id"], old_label, new_label, content, new_content))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data/memory/nascence.db"))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ro = not a.apply
    c = sqlite3.connect(f"file:{a.db}?mode=ro" if ro else a.db, uri=ro)
    c.row_factory = sqlite3.Row
    rows = plan(c)
    todo = [r for r in rows if r[1] != r[2]]
    for fid, old, new, _, _ in rows:
        print(fid[:8], old, "->", new, "" if old != new else "(already right)")
    print(f"{len(rows)} target rows found, {len(todo)} to change")
    if len(rows) != len(TARGETS):
        raise SystemExit("target set mismatch (expected %d)" % len(TARGETS))
    if not a.apply:
        print("DRY RUN: nothing written")
        return
    if du_running():
        raise SystemExit("Du is running (run_nascence process found): refusing to write")
    bak = Path(a.db).parent.parent / "backups" / ("nascence_%s_pre_J-3822.db" % time.strftime("%Y%m%d_%H%M%S"))
    bak.parent.mkdir(exist_ok=True)
    b = sqlite3.connect(str(bak))
    c.backup(b)
    b.close()
    print("backup:", bak, bak.stat().st_size, "bytes")
    stamp = has_hash_column(c)
    before = {r["fragment_id"]: dict(r) for r in c.execute("SELECT * FROM memory_fragments WHERE origin='chapter' AND chapter_level=2")}
    c.execute("BEGIN IMMEDIATE")
    for fid, old, new, content, new_content in todo:
        if stamp:
            c.execute("UPDATE memory_fragments SET content=?, content_hash=? WHERE fragment_id=? AND content=?",
                      (new_content, content_hash(new_content), fid, content))
        else:
            c.execute("UPDATE memory_fragments SET content=? WHERE fragment_id=? AND content=?", (new_content, fid, content))
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            c.execute("ROLLBACK")
            raise SystemExit(f"{fid}: update did not hit exactly one row, rolled back")
    c.execute("COMMIT")
    # verify: only content/content_hash differ, embedding byte-identical, labels now right
    after = {r["fragment_id"]: dict(r) for r in c.execute("SELECT * FROM memory_fragments WHERE origin='chapter' AND chapter_level=2")}
    changed = {fid: [k for k in before[fid] if before[fid][k] != after[fid][k]] for fid in before}
    bad = {f: k for f, k in changed.items() if set(k) - {"content", "content_hash"}}
    print("columns changed per row:", sorted({tuple(v) for v in changed.values()}))
    print("VERIFY other-columns-untouched:", "OK" if not bad else bad)
    again = [r for r in plan(c) if r[1] != r[2]]
    print("VERIFY remaining mismatches:", len(again))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
