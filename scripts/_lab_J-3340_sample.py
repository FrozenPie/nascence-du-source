"""J-3340 step 1: sample first-person sentences from last 14d of inner_thought (read-only DB)."""
import sqlite3, re, random, json, time, sys
sys.stdout.reconfigure(encoding="utf-8")
c = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
since = time.time() - 14 * 86400
rows = c.execute("select fragment_id, content, timestamp from memory_fragments where origin='inner_thought' and timestamp>?", (since,)).fetchall()
FP = re.compile(r"\b(I|I'm|I've|I'll|I'd|my|mine|myself|me)\b|\bwhat I am\b", re.I)
STRICT = re.compile(r"\bI (am|have|was|hold|carry|keep|know|believe|think|feel|notice|want|need|do|can|cannot|will|would)\b|\bmy\b|\bwhat I am\b|\bI'm\b|\bI've\b", re.I)
sents = []
for fid, txt, ts in rows:
    for s in re.split(r"(?<=[.!?])\s+|\n+", txt or ""):
        s = s.strip()
        if 25 <= len(s) <= 400 and STRICT.search(s):
            sents.append((fid, s))
print("thoughts", len(rows), "first-person sentences (wide)", len(sents))
seen = set(); uniq = []
for fid, s in sents:
    k = re.sub(r"\W+", " ", s.lower())[:80]
    if k in seen: continue
    seen.add(k); uniq.append((fid, s))
print("unique", len(uniq))
random.seed(3340)
pick = random.sample(uniq, 120)
json.dump([{"i": i, "fid": f, "s": s} for i, (f, s) in enumerate(pick)], open("docs/lab/J-3340_data/sample120.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for i, (f, s) in enumerate(pick[:6]): print(i, s[:160])
