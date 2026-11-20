import json, sys
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
g = json.loads(Path(r"C:\Nascence\core\graphify-out\graph.json").read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in g.get("nodes", [])}
links = g.get("links", g.get("edges", []))

# find the Orchestrator node id
orch = [nid for nid, n in nodes.items()
        if "orchestrator" in str(n.get("label", "")).lower() and n.get("label", "").lower() in ("orchestrator",)]
orch = orch or [nid for nid, n in nodes.items() if n.get("label") == "Orchestrator"]
oid = orch[0]
print("Orchestrator id:", oid, "community:", nodes[oid].get("community"))

def comm(nid):
    return nodes.get(nid, {}).get("community", "?")
def lab(nid):
    return nodes.get(nid, {}).get("label", nid)
def src(nid):
    return str(nodes.get(nid, {}).get("source_location", "") or "")

out_edges, in_edges = [], []
for e in links:
    s, t = e.get("source"), e.get("target")
    rel = e.get("relation") or e.get("label") or e.get("type") or "edge"
    if s == oid:
        out_edges.append((rel, t))
    elif t == oid:
        in_edges.append((rel, s))

print(f"\nORCHESTRATOR → calls/uses ({len(out_edges)} out-edges), grouped by target file:")
byfile = defaultdict(list)
for rel, t in out_edges:
    f = src(t).split("\\")[-1].split("/")[-1] or "?"
    byfile[f].append(f"{lab(t)}[c{comm(t)}]")
for f in sorted(byfile, key=lambda k: -len(byfile[k])):
    print(f"  {f:<26} {', '.join(byfile[f][:8])}")

print(f"\nINTO Orchestrator ← ({len(in_edges)} in-edges) from file:")
byfile2 = defaultdict(list)
for rel, s in in_edges:
    f = src(s).split("\\")[-1].split("/")[-1] or "?"
    byfile2[f].append(f"{lab(s)}[c{comm(s)}]")
for f in sorted(byfile2, key=lambda k: -len(byfile2[k])):
    print(f"  {f:<26} {', '.join(byfile2[f][:8])}")
