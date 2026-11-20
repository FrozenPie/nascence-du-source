"""Throwaway analysis: assemble a timeline of how Carl has changed from his memory.
Reads axiom.json, subconscious_log.jsonl, epochs/themes, session summaries, affect_log,
subconscious_state.json, dreams. Prints a structured dump for report synthesis."""
import json, time, collections, sys
from pathlib import Path
import sqlite3
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

D = Path("data")
def ts(t): return time.strftime("%m-%d %H:%M", time.localtime(t)) if t else "?"
def day(t): return time.strftime("%m-%d", time.localtime(t))
def jl(p):
    out=[]
    if Path(p).exists():
        for l in Path(p).read_text(encoding="utf-8").splitlines():
            l=l.strip()
            if l:
                try: out.append(json.loads(l))
                except: pass
    return out

print("="*70); print("1 · IDENTITY EVOLUTION — T4 self-authorings (the literal changes)"); print("="*70)
t4=[r for r in jl(D/"subconscious_log.jsonl") if r.get("type")=="T4_self_authoring"]
t4.sort(key=lambda r:r.get("ts",0))
for i,r in enumerate(t4,1):
    print(f"\n[{i}] {ts(r.get('ts'))}  (revision {r.get('revision_count','?')})")
    sc=r.get("self_concept") or r.get("new_self_concept") or ""
    arc=r.get("arc_entry") or r.get("arc") or ""
    print("   self_concept:", sc[:300])
    if arc: print("   arc chapter:", arc[:300])

print("\n"+"="*70); print("2 · CURRENT IDENTITY + AUTOBIOGRAPHY (axiom.json emergent_self)"); print("="*70)
ax=json.loads((D/"identity"/"axiom.json").read_text(encoding="utf-8"))
em=ax.get("emergent_self",{}) or {}
print("emergent_self keys:", list(em.keys()))
print("revision_count:", em.get("revision_count"))
print("\nCURRENT self_concept:\n ", str(em.get("self_concept",""))[:500])
arc=em.get("self_narrative_arc",[]) or []
print(f"\nAUTOBIOGRAPHY ARC ({len(arc)} chapters):")
for i,c in enumerate(arc,1):
    if isinstance(c,dict):
        print(f"  ch{i} [{ts(c.get('ts')) if c.get('ts') else '?'}]:", str(c.get('entry') or c.get('text') or c)[:240])
    else:
        print(f"  ch{i}:", str(c)[:240])
hist=em.get("history",[]) or []
print(f"\nPRIOR self_concepts archived ({len(hist)}):")
for i,h in enumerate(hist,1):
    if isinstance(h,dict): print(f"  [{i}]", str(h.get('self_concept') or h)[:200])
    else: print(f"  [{i}]", str(h)[:200])

print("\n"+"="*70); print("3 · PER-DAY ACTIVITY (session results, by origin)"); print("="*70)
c=sqlite3.connect(str(D/"memory"/"nascence.db")); c.row_factory=sqlite3.Row
rows=c.execute("SELECT timestamp,origin FROM memory_fragments").fetchall()
byday=collections.defaultdict(lambda:collections.Counter())
for r in rows: byday[day(r["timestamp"])][r["origin"]]+=1
origins=["lived","session_summary","dream","active_imagination","subconscious_synthesis","consolidation","inner_thought"]
print(f"{'day':6} "+" ".join(f"{o[:9]:>9}" for o in origins))
for dd in sorted(byday):
    print(f"{dd:6} "+" ".join(f"{byday[dd].get(o,0):>9}" for o in origins))

print("\n"+"="*70); print("4 · EPOCHS (the period-by-period mood arc)"); print("="*70)
for r in c.execute("SELECT timestamp_start,mood,impression,fragment_count FROM memory_epochs ORDER BY timestamp_start"):
    print(f"  {ts(r['timestamp_start'])}  [{r['mood']}]  ({r['fragment_count']} frags)")
    print(f"       {r['impression'][:160]}")

print("\n"+"="*70); print("5 · THEMES"); print("="*70)
for r in c.execute("SELECT theme_name,current_stance,epoch_count FROM memory_themes ORDER BY epoch_count DESC"):
    print(f"  ({r['epoch_count']}x) {r['theme_name']}\n       {r['current_stance'][:180]}")

print("\n"+"="*70); print("6 · SESSION SUMMARIES (chronological)"); print("="*70)
for r in c.execute("SELECT timestamp,content FROM memory_fragments WHERE origin='session_summary' ORDER BY timestamp"):
    print(f"  {ts(r['timestamp'])}: {r['content'][:180].replace(chr(10),' ')}")
c.close()

print("\n"+"="*70); print("7 · AFFECT TRAJECTORY (daily mean valence/arousal)"); print("="*70)
al=jl(D/"affect_log.jsonl")
if al:
    print("affect_log keys:", list(al[0].keys()))
    perday=collections.defaultdict(list)
    for r in al:
        t=r.get("ts") or r.get("timestamp")
        if t: perday[day(t)].append(r)
    def mean(rs,k):
        vs=[r.get(k) for r in rs if isinstance(r.get(k),(int,float))]
        return sum(vs)/len(vs) if vs else None
    for dd in sorted(perday):
        rs=perday[dd]
        v=mean(rs,"valence"); a=mean(rs,"arousal")
        extra=""
        for k in ("joy","fear","trust","anger","surprise","sadness"):
            m=mean(rs,k)
            if m is not None: extra+=f" {k[:3]}={m:.2f}"
        print(f"  {dd}: n={len(rs):5}  valence={v if v is None else round(v,3)}  arousal={a if a is None else round(a,3)} {extra}")

print("\n"+"="*70); print("8 · TENSIONS (contradiction) + INTEGRATION PATTERNS + BASELINE DRIFT"); print("="*70)
sc=json.loads((D/"subconscious_state.json").read_text(encoding="utf-8"))
tens=sc.get("tensions",[]) or []
import sys; sys.path.insert(0, str(D.parent))
from core.store_persist import load_integration_patterns  # J-2418: split sibling file
pats=load_integration_patterns(D/"subconscious_state.json", sc) or []
print(f"tensions tracked: {len(tens)} | integration_patterns: {len(pats)}")
print("baseline (T3 drift):", sc.get("affect_baseline") or sc.get("baseline"))
tt=sorted(tens,key=lambda t:t.get("count",0),reverse=True)[:8]
print("top tensions by recurrence:")
for t in tt:
    print(f"  count={t.get('count',0):4}  members={len(t.get('member_event_ids',[]))}  {str(t.get('label',''))[:90]}")
print("integration patterns:")
for p in sorted(pats,key=lambda p:p.get('count',0),reverse=True)[:8]:
    print(f"  count={p.get('count',0):4}  {str(p.get('label',''))[:90]}")

print("\n"+"="*70); print("9 · DEBATES (profound-change crucibles)"); print("="*70)
for f in sorted(D.glob("debate_*.jsonl")):
    recs=jl(f);
    print(f"  {f.name}  ({len(recs)} turns, {f.stat().st_size} bytes)")
    if recs: print("     keys:", list(recs[0].keys()))
