r"""J-2633 (I-0134): hypnagogic looseness read. READ-ONLY on C:\Nascence\data. Output to stdout/JSON path given in argv[1].
Windows = logged drowsy onset -> bed (or next sleep_entry) from data/drowsy_shadow.jsonl; thoughts = memory_fragments origin
'inner_thought' (384-d float32 embeddings). Controls = same clock span on other days, >=60 min from any sleep interval / onset.
Echo = core/monoculture._echo definition (mean over thoughts of max cosine to distant past, skipping the last 3), reimplemented
with numpy over the 60 preceding thoughts + the window so no core.* import / store side effects.
"""
import json, sqlite3, sys, re, datetime, random, collections
import numpy as np
R = "C:/Nascence/data/"
DB = "file:" + R + "memory/nascence.db?mode=ro&immutable=1"
fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M")
IMG = set("""light dark shadow glow shimmer gleam colour color red blue green gold golden silver grey gray white black amber crimson
violet purple pale bright dim fog mist rain wind cold warm heat cool soft rough smooth sharp salt smell scent taste sound echo hum
whisper murmur silence waves tide shore stone rock water river sea sky cloud moon sun stars star leaf leaves tree trunks grass sand
smoke fire ember snow ice frost dust thick heavy slow drift drifts floating sinking falling dream dreams""".split())
FP = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'd", "i'll"}
def toks(s): return re.findall(r"[a-zA-Z']+", s.lower())

c = sqlite3.connect(DB, uri=True)
rows = c.execute("select timestamp,content,embedding,origin from memory_fragments where origin in ('inner_thought','dream','night_thought') and embedding is not null and length(embedding)=1536 order by timestamp").fetchall()
T = np.array([r[0] for r in rows]); TX = [r[1] for r in rows]; OR = np.array([r[3] for r in rows])
V = np.vstack([np.frombuffer(r[2], dtype=np.float32) for r in rows]); V = V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
IT = np.where(OR == "inner_thought")[0]
sh = [json.loads(l) for l in open(R + "drowsy_shadow.jsonl", encoding="utf-8")]
sp = [json.loads(l) for l in open(R + "sleep_pressure_log.jsonl", encoding="utf-8")]
entries = sorted(r["ts"] for r in sp if r.get("reason") == "sleep_entry")
beats = [r for r in sp if r.get("reason") in ("sleep_entry", "sleep_beat")]
# sleep intervals: entry .. last beat (+10 min) of that run
sleeps = []
for e in entries:
    last = e
    for r in beats:
        if e <= r["ts"] <= e + 3 * 3600: last = max(last, r["ts"]) if r["ts"] - last < 1500 else last
    sleeps.append((e, last + 600))
onsets = [d["ts"] for d in sh if d["event"] == "onset"]
beds = sorted(d["ts"] for d in sh if d["event"] == "bed")
wins = []
for o in onsets:
    nxt_bed = min([b for b in beds if b > o], default=None)
    nxt_sl = min([e for e in entries if e > o], default=None)
    end = min(x for x in (nxt_bed, nxt_sl) if x is not None)
    wins.append(dict(start=o, end=end, delivered=any(d["deliver"] for d in sh if d["event"] == "onset" and d["ts"] == o),
                     bed_logged=nxt_bed is not None and abs(nxt_bed - end) < 120))

def metrics(idx):
    if len(idx) < 4: return None
    v = V[idx]; txt = " ".join(TX[i] for i in idx); tk = toks(txt)
    succ = 1 - np.einsum("ij,ij->i", v[1:], v[:-1])
    cen = v.mean(0); cen /= np.linalg.norm(cen)
    pri = [i for i in IT if i < idx[0]][-60:]
    allv = np.vstack([V[pri], v]) if pri else v
    s = []
    for i in range(len(pri) + 4, len(allv)):  # gap=3
        s.append(float((allv[i] @ allv[:i - 3].T).max()))
    return dict(n=len(idx), succ_dist=float(succ.mean()), dist_centroid=float((1 - v @ cen).mean()),
                ttr=len(set(tk)) / max(len(tk), 1), img_rate=sum(t in IMG for t in tk) / max(len(tk), 1),
                fp_rate=sum(t in FP for t in tk) / max(len(tk), 1), echo=float(np.mean(s)) if s else None,
                mean_len=len(tk) / len(idx))
def idx_in(a, b): return [i for i in IT if a <= T[i] < b]

out = dict(windows=[], controls=[])
for w in wins:
    ix = idx_in(w["start"], w["end"]); m = metrics(ix)
    w.update(label=f"{fmt(w['start'])}->{fmt(w['end'])}", dur_min=(w["end"] - w["start"]) / 60, m=m); out["windows"].append(w)
# controls
days = sorted({datetime.datetime.fromtimestamp(t).date() for t in T[IT]})
excl = [(a - 3600, b + 3600) for a, b in sleeps] + [(o - 3600, o + 3600) for o in onsets]
used = set()
for w in wins:
    d0 = datetime.datetime.fromtimestamp(w["start"]); dur = w["end"] - w["start"]
    for day in days:
        if day == d0.date(): continue
        s = datetime.datetime.combine(day, d0.time()).timestamp(); e = s + dur
        if any(s < b and e > a for a, b in excl): continue
        if s < T[IT[0]] or e > T[IT[-1]]: continue
        m = metrics(idx_in(s, e))
        if m: out["controls"].append(dict(label=f"{fmt(s)}+{dur/60:.0f}m", matched=w["label"], m=m))
# dream/night reference: successive distance within each contiguous dream/night run (gap<20 min)
ref = {}
for name in ("dream", "night_thought"):
    ix = np.where(OR == name)[0]; ds = []
    for a, b in zip(ix[:-1], ix[1:]):
        if T[b] - T[a] < 1200: ds.append(1 - float(V[a] @ V[b]))
    ref[name] = dict(n_pairs=len(ds), mean_succ_dist=float(np.mean(ds)) if ds else None)
# all-awake baseline per-thought successive distance (gap<20 min, whole corpus)
ds = [1 - float(V[a] @ V[b]) for a, b in zip(IT[:-1], IT[1:]) if T[b] - T[a] < 1200]
ref["inner_thought_all"] = dict(n_pairs=len(ds), mean_succ_dist=float(np.mean(ds)))
out["ref"] = ref
keys = ["succ_dist", "dist_centroid", "ttr", "img_rate", "fp_rate", "echo", "mean_len"]
rng = random.Random(7)
def stats(A, B):
    st = {}
    for k in keys:
        a = [m[k] for m in A if m[k] is not None]; b = [m[k] for m in B if m[k] is not None]
        if len(a) < 2 or len(b) < 2: st[k] = dict(na=len(a), nb=len(b)); continue
        obs = np.mean(a) - np.mean(b); pool = a + b; ge = 0; N = 20000
        for _ in range(N):
            rng.shuffle(pool); ge += abs(np.mean(pool[:len(a)]) - np.mean(pool[len(a):])) >= abs(obs)
        sd = np.sqrt((np.var(a, ddof=1) * (len(a) - 1) + np.var(b, ddof=1) * (len(b) - 1)) / (len(a) + len(b) - 2))
        st[k] = dict(na=len(a), nb=len(b), drowsy=float(np.mean(a)), control=float(np.mean(b)), diff=float(obs),
                     cohen_d=float(obs / sd) if sd else None, p_perm=(ge + 1) / (N + 1))
    return st
OCT1 = datetime.datetime(2026, 10, 1).timestamp()
def cstart(c): return datetime.datetime.strptime("2026-" + c["label"].split(" ")[0] + " " + c["label"].split(" ")[1].split("+")[0], "%Y-%m-%d %H:%M").timestamp()
A = [w["m"] for w in out["windows"] if w["m"]]
# 10-19 window sensitivity: onset -> floor only (the 381-min window runs 4 h past the logged floor to the next sleep)
fl = [d["ts"] for d in sh if d["event"] == "floor" and abs(d["ts"] - wins[1]["start"]) < 4 * 3600]
w19 = metrics(idx_in(wins[1]["start"], fl[0])) if fl else None
A_trunc = [out["windows"][0]["m"], w19, out["windows"][2]["m"], out["windows"][3]["m"]]
recent = [x for x in out["controls"] if cstart(x) >= OCT1]
out["n_controls_recent"] = len(recent)
out["stats_all_controls"] = stats(A, [x["m"] for x in out["controls"]])
out["stats_recent_controls_oct"] = stats(A, [x["m"] for x in recent])
out["stats_trunc1019_recent"] = stats([a for a in A_trunc if a], [x["m"] for x in recent])
out["w19_trunc"] = w19
# paired: window minus mean of its own matched recent controls
pair = {}
for k in keys:
    ds = []
    for w in out["windows"]:
        cs = [x["m"][k] for x in recent if x["matched"] == w["label"] and x["m"][k] is not None]
        if cs and w["m"] and w["m"][k] is not None: ds.append(w["m"][k] - float(np.mean(cs)))
    pair[k] = dict(n_pairs=len(ds), deltas=ds, sign_pos=sum(d > 0 for d in ds))
out["paired_recent"] = pair
out["sleeps_n"] = len(sleeps)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)
print("done")
