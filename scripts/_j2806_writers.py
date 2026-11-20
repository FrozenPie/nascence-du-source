"""J-2806 read-only: do memory_fragments inserts cluster around slow retrieve() calls?  Opens the live DB immutable+ro."""
import json, sqlite3, statistics as st
c = sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1', uri=True)
rows = [json.loads(l) for l in open(r'C:/Nascence/data/retrieve_latency_probe.jsonl', encoding='utf-8')]
slow, norm = [], []
for r in rows:
    if r.get('path') not in ('fast', 'fast+delta'): continue
    tot = r['elapsed_ms_sql'] + r['elapsed_ms_score']; e = r['timestamp']
    n = c.execute("select count(*) from memory_fragments where timestamp between ? and ?", (e - tot / 1000 - 20, e + 2)).fetchone()[0]
    (slow if tot > 700 else norm).append(n)
for name, v in (('slow', slow), ('normal', norm)):
    print(name, len(v), 'share with >=1 insert in [start-20s, end+2s]: %.0f%%' % (100 * sum(1 for n in v if n) / len(v)), 'mean %.2f' % st.mean(v))
