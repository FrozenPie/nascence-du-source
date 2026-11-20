import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
c = sqlite3.connect(r'C:\Nascence\data\memory\nascence.db')
total = c.execute('SELECT COUNT(*) FROM memory_fragments').fetchone()[0]
seed  = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='seed'").fetchone()[0]
lived = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='lived'").fetchone()[0]
print(f'Total: {total} | seed: {seed} | lived: {lived}')
print()
print('--- lived fragments ---')
for r in c.execute("SELECT layer, substr(content,1,120) FROM memory_fragments WHERE origin='lived' ORDER BY timestamp").fetchall():
    print(f'[{r[0]}] {r[1]}')
