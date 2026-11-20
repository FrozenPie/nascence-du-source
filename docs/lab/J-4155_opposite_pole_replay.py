"""J-4155 / D-0798 (c): offline replay of the self lessons J-3446 replayed -- how many opposed pairs reach the pole gate
before (arg-max lexical neighbour only) and after (plus the opposite-pole candidate pass). Pure functions, no LLM call,
no embedder (J-3446: the semantic fallback rescued 0 of 243), no write anywhere except --out.

  python docs/lab/J-4155_opposite_pole_replay.py --in <dir holding copies of guidance_beliefs.json and
      guidance_shadow_log.jsonl> --out <result.json>

Pole tags: reported twice -- with J-3446's own regex (comparable to its 5/58) and with the module's _pole_tag (what the
pass uses). Whether the gate model then says CLASH on these pairs is NOT measured here (no model call).
"""
import argparse, collections, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: E402
from core import guidance_learning as gl  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
D = Path(a.inp)
beliefs = json.loads((D / "guidance_beliefs.json").read_text(encoding="utf-8"))
rows = [json.loads(l) for l in (D / "guidance_shadow_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
rows = [r for r in rows if r.get("is_guidance") and len((r.get("principle") or "").strip()) >= 15 and gl._domain(r) == "self"]

RIV = re.compile(r"\b(river|flow|flows|flux|current|fluid|fluidity|transient|shifting|impermanen\w*)", re.I)
BLT = re.compile(r"\b(observer|constant|commit\w*|construct\w*|anchor\w*|stable|durable|single direction|chosen|choose|chooses)", re.I)


def j3446_pole(t):
    x, y = bool(RIV.search(t)), bool(BLT.search(t))
    return "fluid" if x and not y else "durable" if y and not x else "mixed" if x and y else "none"


sb = [b for b in beliefs if (b.get("domain") or "self") == "self" and b.get("status") != "superseded"]
out = {}
for name, tag in (("j3446_regex", j3446_pole), ("module_pole_tag", gl._pole_tag)):
    C = collections.Counter()
    _orig = gl._pole_tag
    gl._pole_tag = tag          # the pass's own selection, under each tagger
    try:
        for r in rows:
            p = r["principle"].strip(); text = p + " " + (r.get("scope") or ""); ts = float(r["ts"])
            cands = [b for b in sb if p not in (b.get("captures") or []) and b.get("principle") != p
                     and float(b.get("first_ts", 0) or 0) < ts]   # J-3446's own causal filter
            if not cands:
                C["no_cands"] += 1; continue
            lp = tag(p)
            if lp not in ("fluid", "durable"):
                continue
            want = "durable" if lp == "fluid" else "fluid"
            if not any(gl._belief_pole(b)[0] == want if name == "module_pole_tag" else tag(b["principle"]) == want
                       for b in cands):
                continue
            C["lesson_has_opposite_belief_available"] += 1
            best, cb = max(((gl._overlap(text, b["principle"] + " " + b.get("scope", "")), b) for b in cands),
                           key=lambda x: x[0])
            lex_ok = best >= gl._SIM_RELATED
            before = lex_ok and {lp, tag(cb["principle"])} == {"fluid", "durable"}
            C["before_opposed_reaches_gate"] += int(before)
            oc = gl._opposite_pole_candidate(text, p, cands, exclude_ids={cb.get("id")} if before else set())
            after = before or oc is not None
            C["after_opposed_reaches_gate"] += int(after)
            C["pass_supplied_new_opposite"] += int(oc is not None and not before)
            if oc is not None:
                C["pass_cand_overlap_below_0.12"] += int(oc["overlap"] < gl._SIM_RELATED)
    finally:
        gl._pole_tag = _orig
    out[name] = dict(C)
out["n_self_lessons"] = len(rows)
out["n_live_self_beliefs"] = len(sb)
Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
