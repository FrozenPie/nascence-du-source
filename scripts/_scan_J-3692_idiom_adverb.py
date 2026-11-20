r"""J-3692 (F-4310, object_epistemic_loop): two non-claim leaks in core.object_hypothesis.extract().
READ-ONLY on data/ (default C:\Nascence\data, override J3692_DATA); writes only docs/lab/J-3692_data/. Zero LLM.

DECLARED BEFORE ANY RESULT WAS LOOKED AT:
  (1) IDIOM: "kind of", "type of", "sort of" removed as claim words (flag NASCENCE_KIND_IDIOM_GATE). A hit is
      "idiom-only" when extract() returns it with the gate OFF and not with the gate ON (adverb flag held OFF).
  (2) ADVERB: POST-HOC EXTENSION of the J-3440 DEONTIC_PATTERN (flag NASCENCE_DEONTIC_ADVERB): an optional adverb
      (just|really|simply|only|still|now|then|also|finally|actually) between "I" and the modal, in the three
      alternatives "i <modal>", "i'm going to", "maybe i <modal>". Hits are "adverb-excluded" when extract()
      returns them with the flag OFF and not with it ON (idiom flag held OFF). "I keep trying to" is NOT covered
      (not an adverb); noted as a residual.
  CORPORA as in J-3440: B = pre-archive stored inferences re-read clause-scoped; C = monologue_log replay
  (thought + intention) against every distinct live (class, name) whose anchor occurs (upper bound: ignores the
  1800 s last-looked requirement).
  THRESHOLDS (share of baseline hits, B and C pooled): >=5% MATERIAL; 0.5-5% PRESENT; <0.5% NEGLIGIBLE.
  PRECISION: every removed hit is printed in full for hand read; a false removal is one where a real claim about the
  object is lost. Combined run (both ON) must remove exactly the union of the two sets.
"""
import json, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import object_hypothesis as oh

LIVE = Path(os.environ.get("J3692_DATA", r"C:\Nascence\data"))
OUT = HERE / "docs" / "lab" / "J-3692_data"
CFG = {"base": ("0", "0"), "idiom": ("1", "0"), "adverb": ("0", "1"), "both": ("1", "1")}

def ex(text, cls, nm, cfg):
    os.environ["NASCENCE_KIND_IDIOM_GATE"], os.environ["NASCENCE_DEONTIC_ADVERB"] = CFG[cfg]
    return oh.extract(text, cls, nm)

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def pct(a, b): return round(100.0 * a / b, 2) if b else 0.0
def verdict(s): return "MATERIAL" if s >= 5 else ("PRESENT" if s >= 0.5 else "NEGLIGIBLE")

def main():
    live = load(LIVE / "world_substrate.json")
    pre = load(LIVE / "world_substrate.pre_archive_20261018_184006.json")
    res = {c: {"hits": 0, "idiom": 0, "adverb": 0, "both_removed": 0, "union": 0} for c in ("B", "C")}
    removed = []
    def tally(corp, text, cls, nm, tag):
        r = {k: ex(text, cls, nm, k) for k in CFG}
        if not r["base"]: return
        t = res[corp]; t["hits"] += 1
        i = not r["idiom"]; a = not r["adverb"]; b = not r["both"]
        t["idiom"] += i; t["adverb"] += a; t["both_removed"] += b; t["union"] += (i or a)
        if i or a or (b != (i or a)):
            removed.append({"corpus": corp, "tag": tag, "idiom": i, "adverb": a, "both": b, "claim": r["base"][0]})
    for oid, o in pre.items():
        for inf in (o.get("inferences") or []):
            tally("B", inf.get("hypothesis", ""), o.get("object_class", ""), o.get("name", ""), oid)
    pairs = {(o.get("object_class", ""), o.get("name", "")) for o in live.values()}
    ap = {}
    for (c, n) in pairs:
        for a in oh.object_anchors(c, n): ap.setdefault(a, set()).add((c, n))
    big = re.compile(r"\b(" + "|".join(re.escape(a) for a in sorted(ap, key=len, reverse=True)) + r")s?\b")
    with open(LIVE / "monologue_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try: r = json.loads(line)
            except Exception: continue
            text = f"{r.get('thought', '')} {r.get('intention', '') or ''}"
            low = text.lower()
            if not oh._CLAIM_RE.search(low): continue
            found = set(big.findall(low))
            if not found: continue
            cp = set()
            for a in found: cp |= ap.get(a, set())
            first = None
            for (c, n) in cp:
                if ex(text, c, n, "base"): first = (c, n); break
            if first: tally("C", text, first[0], first[1], str(r.get("ts")))
    pooled = {k: res["B"][k] + res["C"][k] for k in res["B"]}
    rep = {"B": res["B"], "C": res["C"], "pooled": pooled,
           "idiom_share_pct": pct(pooled["idiom"], pooled["hits"]), "idiom_verdict": verdict(pct(pooled["idiom"], pooled["hits"])),
           "adverb_share_pct": pct(pooled["adverb"], pooled["hits"]), "adverb_verdict": verdict(pct(pooled["adverb"], pooled["hits"])),
           "combined_equals_union": pooled["both_removed"] == pooled["union"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scan.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    (OUT / "removed.json").write_text(json.dumps(removed, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep, indent=1))
    for e in removed: print(json.dumps(e, ensure_ascii=False))
    print("removed rows:", len(removed))
main()
