"""J-4279: offline replay of core/follow_line.settle_overlap against the 48 J-4029 hand grades. Read-only.
Extracts the gate functions from core/follow_line.py by AST (no import of core, no live-store side effects)."""
import ast, json, re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
src = (R / "core/follow_line.py").read_text(encoding="utf-8")
tree = ast.parse(src)
want = {"_OVERLAP_STOP", "_content_terms", "settle_overlap", "SETTLE_OVERLAP_MIN"}
body = []
for n in tree.body:
    names = {t.id for t in getattr(n, "targets", []) if isinstance(t, ast.Name)} | ({n.name} if hasattr(n, "name") else set())
    if names & want:
        body.append(n)
ns = {"re": re}
exec(compile(ast.Module(body=body, type_ignores=[]), "follow_line_extract", "exec"), ns)
so = ns["settle_overlap"]
grades = json.load(open(R / "docs/lab/J-4029_data/hand_grades.json"))["grades_closures_by_index"]
rows = [json.loads(l) for l in open(R / "data/logs/follow_line_shadow.jsonl", encoding="utf-8") if l.strip()]
cl = [r for r in rows if r.get("kind") == "settled" and r.get("resolved") is True and r.get("closure_how") == "ok"][:48]
wr = {r["q_id"]: r for r in rows if r.get("kind") == "would_return"}
assert len(cl) == 48 == len(grades)
data = []
for c, g in zip(cl, grades):
    ret = (wr[c["q_id"]].get("return_text") or "")
    data.append((g, so(c["q"], ret, c["thought"])["score"]))
no = [s for g, s in data if g == "no"]; yes = [s for g, s in data if g == "yes"]; pt = [s for g, s in data if g == "partly"]
print("n no/yes/partly", len(no), len(yes), len(pt))
for nm, v in (("no", no), ("partly", pt), ("yes", yes)):
    v2 = sorted(v); print(nm, "scores sorted:", v2)
print("thr   reject_no  keep_yes  (reject = score < thr)  also partly_rejected")
hits = []
for i in range(5, 41):
    t = i / 100
    rn = sum(s < t for s in no) / len(no); ky = sum(s >= t for s in yes) / len(yes); rp = sum(s < t for s in pt) / len(pt)
    ok = rn >= .7 and ky >= .8
    if ok: hits.append(t)
    print(f"{t:.2f}  {rn:.3f}({sum(s<t for s in no)}/{len(no)})  {ky:.3f}({sum(s>=t for s in yes)}/{len(yes)})  {rp:.2f} {'<== MEETS BOTH' if ok else ''}")
print("thresholds meeting both:", hits)
