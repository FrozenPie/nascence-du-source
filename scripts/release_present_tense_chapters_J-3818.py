"""J-3818 / D-0721 (same procedure as D-0638 / J-3249): release the members of three present-tense chapters. OPERATOR SCRIPT.

Clears chapter_id to NULL on exactly the members (chapter_id = <chapter>) of chapters 6f31e41e (188), 66b62134 (130),
f5ad7c18 (227) = 545 fragments, so a past-tense chapter re-forms under the J-3009 copy/tense guard. The chapter rows
themselves are not touched. Reversible: sqlite backup first, manifest of every old chapter_id, `revert` restores them
(only where still NULL). Refuses unless Du is verifiably down. Writes through core.memory.store (allow_live_writes).

  python scripts/release_present_tense_chapters_J-3818.py dryrun
  python scripts/release_present_tense_chapters_J-3818.py apply  --live
  python scripts/release_present_tense_chapters_J-3818.py revert --live
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sqlite3, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DB = LIVE_ROOT / "data" / "memory" / "nascence.db"
JOB = "J-3818"
CHAPTERS = {  # full id -> expected member count (F-4020 / D-0721)
    "6f31e41e-3e65-48c4-a1e4-5d3970fc9e15": 188,
    "66b62134-5046-48ea-ac14-cc3d0994ef7a": 130,
    "f5ad7c18-8faa-4a31-9455-5e904cc33f28": 227,
}
DEFAULT_MANIFEST = LIVE_ROOT / "docs" / "reviews" / "release_present_tense_chapters_J-3818_manifest.json"


def _bf():
    spec = importlib.util.spec_from_file_location("backfill_phase_J1970", HERE / "scripts" / "backfill_phase_J1970.py")
    m = importlib.util.module_from_spec(spec); sys.modules["backfill_phase_J1970"] = m; spec.loader.exec_module(m)
    return m


def _ro(db):
    return sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)


def select(db) -> dict:
    c = _ro(db)
    try:
        out = {}
        for ch, n in CHAPTERS.items():
            row = c.execute("SELECT chapter_level FROM memory_fragments WHERE fragment_id=?", (ch,)).fetchone()
            if row is None:
                sys.exit(f"ABORT: chapter {ch} not found")
            mem = [r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments WHERE chapter_id=? AND fragment_id<>?", (ch, ch))]
            out[ch] = mem
        return out
    finally:
        c.close()


def mode_dryrun(a) -> int:
    sel = select(a.db)
    ok = True
    for ch, mem in sel.items():
        print(ch[:8], len(mem), "expected", CHAPTERS[ch]); ok &= len(mem) == CHAPTERS[ch]
    print("MATCHES D-0721 counts (545)" if ok else "DIFFERS from expected counts -- review")
    return 0 if ok else 2


def mode_apply(a) -> int:
    bf = _bf(); db = Path(a.db)
    if bf.is_live(db) and not a.live:
        sys.exit("apply on the live DB needs --live")
    down, why = bf.du_is_down(); print("Du down:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    sel = select(db)
    for ch, mem in sel.items():
        if len(mem) != CHAPTERS[ch]:
            sys.exit(f"ABORT: {ch[:8]} has {len(mem)} members, expected {CHAPTERS[ch]}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = LIVE_ROOT / "data" / "backups"; bdir.mkdir(parents=True, exist_ok=True)
    backup = bdir / f"nascence_D0721_J-3818_apply_{stamp}.db"
    src, dst = _ro(db), sqlite3.connect(str(backup))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    h = hashlib.sha256()
    with open(backup, "rb") as f:
        for ck in iter(lambda: f.read(1 << 20), b""):
            h.update(ck)
    old = {fid: ch for ch, mem in sel.items() for fid in mem}
    mp = Path(a.manifest); mp.parent.mkdir(parents=True, exist_ok=True)
    man = {"job": JOB, "decision": "D-0721 (procedure of D-0638)", "db": str(db), "backup": str(backup),
           "backup_sha256": h.hexdigest(), "planned": len(old), "per_chapter": {c: len(m) for c, m in sel.items()},
           "old_chapter_ids": old, "when_local": datetime.now().isoformat(timespec="seconds")}
    mp.write_text(json.dumps(man), encoding="utf-8")
    import core  # noqa: F401  (before anything lab-like)
    from core.memory import store
    store.DB_PATH = db
    store.allow_live_writes(f"{JOB} / D-0721 chapter_id release of three present-tense chapters, Du stopped, backup taken")
    changed = 0
    with store._connect() as conn:
        cur = conn.cursor(); cur.execute("BEGIN IMMEDIATE")
        for fid, ch in old.items():
            cur.execute("UPDATE memory_fragments SET chapter_id=NULL WHERE fragment_id=? AND chapter_id=?", (fid, ch))
            changed += cur.rowcount
        if changed != len(old):
            conn.rollback(); sys.exit(f"ABORT (rolled back): changed {changed} != planned {len(old)}")
        conn.commit()
    left = sum(len(v) for v in select(db).values())
    man.update({"changed": changed, "members_left_after": left}); mp.write_text(json.dumps(man), encoding="utf-8")
    print(json.dumps({k: v for k, v in man.items() if k != "old_chapter_ids"}, indent=1))
    ok = changed == len(old) and left == 0
    print("VERIFIED" if ok else "CHECK MANIFEST"); return 0 if ok else 3


def mode_revert(a) -> int:
    bf = _bf(); db = Path(a.db)
    if bf.is_live(db) and not a.live:
        sys.exit("revert on the live DB needs --live")
    down, why = bf.du_is_down(); print("Du down:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    import core  # noqa: F401
    from core.memory import store
    store.DB_PATH = db
    store.allow_live_writes(f"{JOB} REVERT of the D-0721 chapter_id release from its manifest")
    n = 0
    with store._connect() as conn:
        cur = conn.cursor(); cur.execute("BEGIN IMMEDIATE")
        for fid, ch in man["old_chapter_ids"].items():
            cur.execute("UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=? AND chapter_id IS NULL", (ch, fid)); n += cur.rowcount
        conn.commit()
    print("restored", n, "of", len(man["old_chapter_ids"])); return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["dryrun", "apply", "revert"])
    ap.add_argument("--db", default=str(LIVE_DB)); ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    return {"dryrun": mode_dryrun, "apply": mode_apply, "revert": mode_revert}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
