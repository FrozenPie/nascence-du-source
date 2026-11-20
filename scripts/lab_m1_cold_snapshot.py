"""J-3993: read-only snapshot of fragment availability flags, for the pre-registered M1 run (atlas 6.4).
Run ON 2026-12-01 (not before): python scripts/lab_m1_cold_snapshot.py
Writes docs/lab/j3993_data/cold_snapshot_<UTC date>.csv.gz (id,timestamp,cold,protected,origin)."""
import sqlite3, gzip, datetime as dt, os
out_dir = 'C:/Nascence/docs/lab/j3993_data'
os.makedirs(out_dir, exist_ok=True)
c = sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro', uri=True)
p = f"{out_dir}/cold_snapshot_{dt.datetime.now(dt.timezone.utc):%Y-%m-%d}.csv.gz"
n = 0
with gzip.open(p, 'wt') as f:
    f.write('id,timestamp,cold,protected,origin\n')
    for r in c.execute('select fragment_id,timestamp,cold,protected,origin from memory_fragments'):
        f.write(','.join(str(x) for x in r) + '\n'); n += 1
print(p, n)
