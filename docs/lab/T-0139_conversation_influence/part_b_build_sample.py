# J-4074 Part B: build the blind sample exactly as part_b_prereg.md says. Read-only against nascence.db.
# usage: python part_b_build_sample.py <out_dir>
#   writes key.json (id -> cell, teaching, fragment id, ts; NOT for the judge) and judge/batch_NN.json (id, text only)
import sqlite3, json, sys, time, re, random, os, hashlib
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
OUT = sys.argv[1]; os.makedirs(OUT + '/judge', exist_ok=True)
rnd = random.Random(4074)
c = sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro', uri=True)
EXCL = re.compile(r"wu[\s-]?wei|無為|无为|cook ding|butcher|庖丁|mindful|amor fati|\btao\b|\bdao\b|taois|daois|lao ?zi|lao ?tzu|"
                  r"zhuang ?zi|chuang ?tzu|travis", re.I)
D = lambda m, d, h=0: time.mktime((2026, m, d, h, 0, 0, 0, 0, -1))
W_CELLS = {'before': (D(6, 3), D(8, 9)), 'after_same_model': (D(8, 10), D(8, 20)), 'd30': (D(8, 30), D(9, 19)),
           'd60': (D(9, 28), D(10, 19)), 'd90': (D(10, 28), D(11, 16))}
A_CELLS = {'before': (D(8, 21), D(9, 2)), 'd30': (D(9, 22), D(10, 13)), 'd60': (D(10, 22), D(11, 12))}
SETS = {
    'wuwei':    (W_CELLS, 50, "I am facing a question I cannot settle, a task that has stalled, something left unfinished."),
    'cookding': (W_CELLS, 40, "I am doing a piece of work with my hands or my mind, or planning how to carry out a task."),
    'amorfati': (A_CELLS, 50, "Something I did not want has happened, or I have met a limit in myself or the world that cannot be changed."),
    'mindful':  (W_CELLS, 30, "My attention is pulled between abstract thinking and what is physically here around me."),
}
rows = c.execute("select fragment_id,timestamp,content,embedding from memory_fragments where origin='inner_thought' and embedding is not null").fetchall()
seen, pool = set(), []
for fid, ts, co, emb in rows:
    co = co.strip()
    if not (80 <= len(co) <= 700) or EXCL.search(co): continue
    h = hashlib.sha1(co.encode('utf-8')).hexdigest()
    if h in seen: continue
    seen.add(h); pool.append((fid, ts, co, np.frombuffer(emb, dtype=np.float32)))
print('pool', len(pool), 'of', len(rows))
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
key, used = {}, set()
for name, (cells, n, desc) in SETS.items():
    q = model.encode(desc, normalize_embeddings=True).astype(np.float32)
    t0, t1 = min(a for a, b in cells.values()), max(b for a, b in cells.values())
    sub = [p for p in pool if t0 <= p[1] < t1]
    sims = np.array([float(p[3] @ q) for p in sub])
    thr = float(np.percentile(sims, 80))
    for cell, (a, b) in cells.items():
        el = [p for p, s in zip(sub, sims) if a <= p[1] < b and s >= thr and p[0] not in used]
        tot = sum(1 for p in sub if a <= p[1] < b)
        pick = rnd.sample(el, min(n, len(el)))
        print(f'{name:9s} {cell:17s} in cell {tot:6d} eligible {len(el):5d} drawn {len(pick)}  thr {thr:.3f}')
        for p in pick:
            used.add(p[0])
            key[p[0]] = {'teaching': name, 'cell': cell, 'ts': p[1], 'text': p[2]}
ids = list(key); rnd.shuffle(ids)
opaque = {}
for i, fid in enumerate(ids):
    oid = 'P' + hashlib.sha1((fid + 'j4074').encode()).hexdigest()[:6]
    assert oid not in opaque; opaque[oid] = fid; key[fid]['oid'] = oid
rep = rnd.sample(list(opaque), 150)
json.dump({'key': key, 'repeat': rep}, open(OUT + '/key.json', 'w', encoding='utf-8'), ensure_ascii=False)
def batches(oids, prefix, size=50):
    oids = list(oids); rnd.shuffle(oids)
    for b in range(0, len(oids), size):
        items = [{'id': o, 'text': key[opaque[o]]['text']} for o in oids[b:b + size]]
        json.dump(items, open(f'{OUT}/judge/{prefix}_{b//size:02d}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return (len(oids) + size - 1) // size
print('main batches', batches(opaque, 'batch'), 'repeat batches', batches(rep, 'again'), 'second-judge batches', batches(rep, 'other'))
print('passages', len(opaque))
