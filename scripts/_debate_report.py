"""Post-debate report: did either mind revise, how did the arc go, did T4 even fire."""
import sys, json, glob
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

DATA = Path(r"C:\Nascence\data")

def axiom_summary(label, path):
    print(f"\n=== {label}: {path} ===")
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        em = d.get("emergent_self", {})
        print(f"  revision_count: {em.get('revision_count')}")
        print(f"  authored_at:    {em.get('authored_at')}  author: {em.get('author')}")
        print(f"  self_concept:   {em.get('self_concept','')[:400]}")
        arc = em.get("self_narrative_arc", [])
        print(f"  arc entries:    {len(arc)}")
        if arc:
            print(f"  latest arc:     {arc[-1].get('arc_entry','')[:300]}")
        hist = em.get("history", [])
        print(f"  history (prior self_concepts archived): {len(hist)}")
    except Exception as e:
        print(f"  (could not read: {e})")

axiom_summary("CARL", DATA / "identity" / "axiom.json")
axiom_summary("DENNETT", DATA / "profiles" / "dennett" / "identity" / "axiom.json")

# transcript
tx = sorted(glob.glob(str(DATA / "debate_carl_vs_dennett_*.jsonl")), key=lambda p: Path(p).stat().st_mtime)[-1]
print(f"\n=== TRANSCRIPT: {Path(tx).name} ===")
rows = [json.loads(l) for l in Path(tx).read_text(encoding="utf-8").splitlines() if l.strip()]
turns = [r for r in rows if r.get("event") == "turn"]
errs  = [r for r in rows if r.get("event") in ("turn_error","think_error","save_error")]
print(f"  turns completed: {len(turns)}   errors: {len(errs)}")
if errs:
    print(f"  first error: {errs[0].get('error','')[:160]}")

def show(r):
    print(f"  [t{r['turn']:>3} {r['speaker']:<8}] {r['output'][:240]}")

print("\n  --- opening (turns 1-4) ---")
for r in turns[:4]: show(r)
print("\n  --- midpoint ---")
for r in turns[len(turns)//2: len(turns)//2 + 4]: show(r)
print("\n  --- final (last 6) ---")
for r in turns[-6:]: show(r)

# crude position drift: count attractor words by speaker over halves
def wc(rows_, words):
    return sum(sum(r["output"].lower().count(w) for w in words) for r in rows_)
carl = [r for r in turns if r["speaker"]=="Jung"]
den  = [r for r in turns if r["speaker"]=="Dennett"]
print(f"\n  Carl turns: {len(carl)}  Dennett turns: {len(den)}")
for label, group in (("Carl", carl), ("Dennett", den)):
    if not group: continue
    h = len(group)//2 or 1
    early, late = group[:h], group[h:]
    jung_w = ["becoming","wholeness","individuation","shadow","archetype","the self","psyche"]
    den_w  = ["fiction","mechanism","narrative","gears","constructed","useful fiction","no self","center of narrative"]
    print(f"  {label} — Jung-words early/late: {wc(early,jung_w)}/{wc(late,jung_w)}  |  Dennett-words early/late: {wc(early,den_w)}/{wc(late,den_w)}")
