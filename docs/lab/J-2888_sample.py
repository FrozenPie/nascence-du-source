"""J-2888: build the stratified 100-row sample from data/deliberation_log.jsonl (read-only). seed 2888."""
import json, random, re, sys
sys.stdout.reconfigure(encoding="utf-8")
LOG = r"C:\Nascence\data\deliberation_log.jsonl"
OUT = r"C:\Nascence\docs\lab\J-2888_data\sample.jsonl"
rows = []
with open(LOG, encoding="utf-8") as f:
    for i, l in enumerate(f):
        try: r = json.loads(l)
        except Exception: continue
        r["_i"] = i; rows.append(r)
em = [r for r in rows if r.get("source") == "emissary" and 60 <= len(r.get("raw", "")) <= 1200]
cut = em[-1]["ts"] - 30 * 86400
pool = [r for r in em if r["ts"] > cut]
BOOK = re.compile(r"\b(book|chapter|page|read(ing)?|author|Napoleon|Aurelius|Marcus|Seneca|Plato|Darwin|Newton|Einstein|Faraday|Maxwell|Hemingway|Tolstoy|Shakespeare|wrote|Travis|Insect Adventures|diary|journal)\b|'[A-Z][^']{4,40}'")
META = re.compile(r"\bI am (the|a|an|just|only|not)\b|\bI (am|feel|become) like\b|\bam I\b|\bmy (self|mind|identity)\b|\bwho I am\b|\bas if I\b|\bI (carry|hold|contain) (the|a)\b", re.I)
SENS = re.compile(r"\b(smell|scent|sound|cold|warm|light|damp|wind|rain|sea|bark|leaf|leaves|stone|dust|moss|rosemary|thyme|spider|bird|morning|dew|glass|window|water|heat|cool|gravel|soil)\b", re.I)
def stratum(r):
    t = r["raw"]
    if BOOK.search(t): return "book_person"
    if META.search(t): return "self_metaphor"
    if SENS.search(t): return "plain_sensory"
    return "other"
for r in pool: r["_s"] = stratum(r)
import collections
print("pool", len(pool), collections.Counter(r["_s"] for r in pool))
rng = random.Random(2888)
quota = {"plain_sensory": 40, "self_metaphor": 30, "book_person": 30}
sample = []
for s, n in quota.items():
    c = [r for r in pool if r["_s"] == s]
    pick = rng.sample(c, min(n, len(c)))
    sample += pick
# previous thought (for the as-logged 'his latest thought' reconstruction): the nearest earlier emissary row's raw
by_i = {r["_i"]: r for r in em}
em_idx = [r["_i"] for r in em]
import bisect
with open(OUT, "w", encoding="utf-8") as f:
    for k, r in enumerate(sample):
        j = bisect.bisect_left(em_idx, r["_i"]) - 1
        prev = em[j]["raw"] if j >= 0 else ""
        f.write(json.dumps({"sid": k, "stratum": r["_s"], "log_line": r["_i"], "ts": r["ts"], "about": r.get("about"),
                            "raw": r["raw"], "prev_raw": prev, "logged_grounding": r.get("grounding")}, ensure_ascii=False) + "\n")
print("sample", len(sample), collections.Counter(r["_s"] for r in sample))
