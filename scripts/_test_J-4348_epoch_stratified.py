"""J-4348: origin-stratified epoch sampler + shadow wiring. Offline, temp DB only, no model calls."""
import asyncio, json, os, sqlite3, sys, tempfile, types
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402
import core.memory.store as store  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j4348_"))
store.DB_PATH = tmp / "t.db"
conn = sqlite3.connect(str(store.DB_PATH))
conn.executescript("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL,
 layer TEXT NOT NULL DEFAULT 'episodic', relevance REAL NOT NULL DEFAULT 0.5, timestamp REAL NOT NULL,
 keywords TEXT NOT NULL DEFAULT '', embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived', derived_from TEXT NOT NULL DEFAULT '[]');""")
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)

mix = {"inner_thought": 394, "reading": 258, "action": 65, "study": 60, "active_imagination": 43}
rows, t = [], 1000.0
for o, k in mix.items():
    for i in range(k):
        rows.append((f"{o}{i}", f"{o} {i}", "episodic", 1000.0 + (len(rows) * 7919 % 919), o))
conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, timestamp, origin) VALUES (?,?,?,?,?)", rows)
conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, timestamp, origin) VALUES ('sem','x','semantic',1500,'reading')")
conn.commit()
a, b = 1000.0, 2000.0
st = store.get_fragments_spread_stratified(a, b, n=25)
from collections import Counter
c = Counter(r["origin"] for r in st)
check("1 exactly 25, no dups", len(st) == 25 and len({r["fragment_id"] for r in st}) == 25)
check("2 every origin present", set(c) == set(mix))
check("3 proportional ordering kept", c["inner_thought"] >= c["reading"] >= c["action"] >= 1)
sp = Counter(r["origin"] for r in store.get_fragments_spread(a, b, n=25))
check("4 stratified min-origin share >= spread's", min(c.values()) >= 1 and min(c[o] for o in mix) >= min(sp.get(o, 0) for o in mix))
check("5 oldest first, episodic only", [r["timestamp"] for r in st] == sorted(r["timestamp"] for r in st) and "sem" not in {r["fragment_id"] for r in st})
check("6 empty -> []", store.get_fragments_spread_stratified(5e6, 6e6) == [])
check("7 fewer than n -> all", len(store.get_fragments_spread_stratified(1000, 1010, n=25)) == len([r for r in rows if r[3] <= 1010]))
check("8 more origins than n -> n", len(store.get_fragments_spread_stratified(a, b, n=3)) == 3)

# wiring: flag off -> stratified never called, stored epoch from spread; shadow on -> log written, 2 calls
import scripts.run_nascence as rn  # noqa: E402
spread_rows = [{"origin": "inner_thought", "content": f"s{i}"} for i in range(5)]
strat_rows = [{"origin": o, "content": f"t{i}"} for i, o in enumerate(mix)]
calls, stored = [], []
async def fake_syn(state, frags):
    calls.append(frags[0]["content"]); return ("m", "imp-" + frags[0]["content"])
rn._epoch_synthesise = fake_syn
rn.get_fragments_spread = lambda x, y, n=25: spread_rows
rn.store_epoch = lambda **kw: stored.append(kw) or "abcdefgh"
store.get_fragments_spread_stratified = lambda x, y, n=25: strat_rows
state = types.SimpleNamespace(spirit_name="T")
for k in ("NASCENCE_EPOCH_STRATIFIED", "NASCENCE_EPOCH_STRATIFY_SHADOW"): os.environ.pop(k, None)
asyncio.run(rn._form_epoch(state, 0.0))
check("9 flags off: one call, spread arm stored", calls == ["s0"] and stored[-1]["impression"] == "imp-s0")
calls.clear(); sp_path = tmp / "shadow.jsonl"
os.environ["NASCENCE_EPOCH_STRATIFY_SHADOW"] = "1"; os.environ["NASCENCE_EPOCH_SHADOW_PATH"] = str(sp_path)
asyncio.run(rn._form_epoch(state, 0.0))
rec = json.loads(sp_path.read_text().splitlines()[0])
check("10 shadow: two calls, spread stored, both logged", len(calls) == 2 and stored[-1]["impression"] == "imp-s0"
      and rec["stored_arm"] == "spread" and rec["arms"]["stratified"]["impression"] == "imp-t0" and rec["arms"]["spread"]["impression"] == "imp-s0")
os.environ["NASCENCE_EPOCH_STRATIFIED"] = "1"; calls.clear()
asyncio.run(rn._form_epoch(state, 0.0))
check("11 live flag: stratified stored", stored[-1]["impression"] == "imp-t0")
import subprocess
out = subprocess.run([sys.executable, str(TREE / "scripts" / "epoch_stratify_shadow_read.py"), str(sp_path)], capture_output=True, text=True).stdout
check("12 reader prints both arms", "[spread]" in out and "[stratified]" in out)
print("\nALL PASS" if not fails else "\nFAILED: " + ", ".join(fails))
