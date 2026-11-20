"""J-1843 / F-2476: backup_identity must not raw-copy nascence.db into data/_snapshots/daily/.

Runs entirely in a disposable tree: copies scripts/backup_identity.py + scripts/retention.py into a temp
root, so the module's __file__-relative ROOT is the temp dir and the real data/ is never touched.
    python scripts/_test_j1843_backup_identity_no_db.py
"""
import importlib.util, os, shutil, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
fails = []
def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  {detail}"))
    if not ok: fails.append(name)

tmp = Path(tempfile.mkdtemp(prefix="j1843_"))
try:
    (tmp / "scripts").mkdir()
    (tmp / "scripts" / "__init__.py").write_text("")
    for n in ("backup_identity.py", "retention.py"):
        shutil.copy2(HERE / n, tmp / "scripts" / n)
    d = tmp / "data"
    (d / "identity").mkdir(parents=True); (d / "memory").mkdir()
    (d / "identity" / "axiom.json").write_text("{}")
    (d / "memory" / "nascence.db").write_bytes(b"x" * 5_000_000)
    (d / "reading_state.json").write_text("{}")
    (d / "subconscious_state.json").write_text("{}")
    sys.path.insert(0, str(tmp))
    spec = importlib.util.spec_from_file_location("bi_j1843", tmp / "scripts" / "backup_identity.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    check("module ROOT is the temp tree (not live)", Path(m.ROOT).resolve() == tmp.resolve(), str(m.ROOT))
    line = m.backup()
    day = next((tmp / "data" / "_snapshots" / "daily").iterdir())
    names = sorted(p.name for p in day.iterdir())
    check("identity files snapshotted", names == ["axiom.json", "reading_state.json", "subconscious_state.json"], names)
    check("no nascence.db copy", "nascence.db" not in names)
    check("snapshot dir tiny", sum(p.stat().st_size for p in day.iterdir()) < 1000)
    check("report line says 3 new, not 'retained'", "3 new file(s)" in line and "retained" not in line, line)
    line2 = m.backup()
    check("second call same day adds nothing", "0 new file(s)" in line2, line2)
    # retention still governs the dir: an old, non-tier day gets quarantined by the unchanged retention rule
    # 20240102 is the first-of-month keeper; 20240103 (a Wednesday, >14 d old) falls outside every tier
    keep = tmp / "data" / "_snapshots" / "daily" / "20240102"; keep.mkdir()
    old = tmp / "data" / "_snapshots" / "daily" / "20240103"; old.mkdir()
    (keep / "axiom.json").write_text("{}"); (old / "axiom.json").write_text("{}")
    line3 = m.backup()
    check("retention still quarantines out-of-tier day", keep.exists() and not old.exists() and "1 quarantined" in line3, line3)
finally:
    sys.path.remove(str(tmp)) if str(tmp) in sys.path else None
    shutil.rmtree(tmp, ignore_errors=True)
print("ALL PASS" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
