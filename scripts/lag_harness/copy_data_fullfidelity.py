"""scripts/lag_harness/copy_data_fullfidelity.py (J-1892, F-2540): build a full-fidelity (small+medium stores) data/ copy inside the throwaway worktree $LAGH_SCRATCH/$LAGH_WT. Reads live files only; the DB via sqlite3 backup() from a mode=ro connection. Originally:
DB via sqlite3 backup() from a mode=ro connection."""
import os, sys, shutil, sqlite3, time, pathlib, json
SP = pathlib.Path(os.environ["LAGH_SCRATCH"])   # the scratch dir that holds the throwaway worktree (+ its data/ copy)
WT = SP / os.environ.get("LAGH_WT", "wt_head")
LIVE = pathlib.Path(r"C:\Nascence\data")
DST = WT / "data"
assert str(DST).lower().startswith(str(SP).lower())
DST.mkdir(exist_ok=True)
SKIP_DIRS = {"_trash","_lab","backups","_snapshots","training","logs","books","memory","_hold"}
BIG = 25_000_000
n=0; nb=0; tot=0
for p in LIVE.iterdir():
    try:
        if p.is_dir():
            if p.name in SKIP_DIRS: continue
            if sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) > 300_000_000: print("skip big dir",p.name); continue
            shutil.copytree(p, DST/p.name, dirs_exist_ok=True); n+=1
        else:
            if p.name.endswith(".lock"): continue
            sz=p.stat().st_size
            if sz<=BIG or p.suffix in (".npz",):
                shutil.copy2(p, DST/p.name); n+=1; tot+=sz
            elif p.suffix==".jsonl":
                with open(p,"rb") as f:
                    f.seek(sz-1_000_000); f.readline(); tail=f.read()
                (DST/p.name).write_bytes(tail); nb+=1
            else:
                print("skipped non-jsonl big", p.name, sz)
    except Exception as e:
        print("ERR",p.name,repr(e)[:100])
print("copied",n,"files/dirs; tailed",nb,"big jsonl; small bytes",tot)
# DB backup
(DST/"memory").mkdir(exist_ok=True)
t=time.time()
src=sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True, timeout=60)
dst=sqlite3.connect(str(DST/"memory"/"nascence.db"))
src.backup(dst, pages=4096)
dst.close(); src.close()
print("db backup secs", round(time.time()-t,1), os.path.getsize(DST/"memory"/"nascence.db"))
