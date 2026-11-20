"""J-3415: origin x importance table of memory_fragments, opened read-only+immutable. Prints and writes JSON."""
import sqlite3, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1", uri=True)
rows = con.execute("select origin, count(*), round(avg(importance),3), sum(importance>=0.8), min(abstraction_level), max(abstraction_level), sum(cold) "
                   "from memory_fragments group by origin order by 2 desc").fetchall()
out = [dict(origin=r[0], n=r[1], avg_importance=r[2], n_ge_0_8=r[3], lvl_min=r[4], lvl_max=r[5], cold=r[6]) for r in rows]
p = ROOT / "docs" / "lab" / "J-3415_data" / "origin_reach.json"
p.write_text(json.dumps(out, indent=1), encoding="utf-8")
for o in out: print(o)
