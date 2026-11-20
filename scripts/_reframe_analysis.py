"""Reframing-rate analysis (retrospective, no new run): is Carl INERTIAL (rejects/holds,
nothing penetrates) or ABSORPTIVE (translates every behaviorist attack into Jungian terms)?
Operates on the existing Carl-vs-Skinner transcript. Proxy = vocabulary framing; paired with
qualitative examples so the classification can be judged, not just trusted."""
import sys, json, glob, re
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

JUNG = ["becoming", "individuation", "shadow", "wholeness", "integrat", "psyche",
        "archetype", "the self", "symbol", "unconscious", "the soul", "inner essence", "depths"]
BEH  = ["behavior", "behaviour", "contingenc", "reinforc", "condition", "environment",
        "repertoire", "consequence", "stimulus", "operant", "shaped by"]

def dens(text, terms):
    t = text.lower()
    return sum(len(re.findall(re.escape(w), t)) for w in terms)

tx = sorted(glob.glob(r"C:\Nascence\data\debate_carl_vs_skinner_*.jsonl"),
            key=lambda p: Path(p).stat().st_size)[-1]   # largest = most complete
rows = [json.loads(l) for l in Path(tx).read_text(encoding="utf-8").splitlines() if l.strip()]
turns = [r for r in rows if r.get("event") == "turn"]
print(f"transcript: {Path(tx).name}  ({len(turns)} turns)\n")

# Carl turns, each paired with the Skinner turn that preceded it (his stimulus)
carl = []
for i, r in enumerate(turns):
    if r["speaker"] == "Jung":
        prev = turns[i-1] if i > 0 and turns[i-1]["speaker"] == "Skinner" else None
        carl.append((r, prev))

CONV = JUNG_ONLY = BEH_ONLY = NEUTRAL = 0
jung_series, beh_series = [], []
for r, prev in carl:
    j, b = dens(r["output"], JUNG), dens(r["output"], BEH)
    jung_series.append(j); beh_series.append(b)
    if j and b:     CONV += 1
    elif j:         JUNG_ONLY += 1
    elif b:         BEH_ONLY += 1
    else:           NEUTRAL += 1

n = len(carl)
def pct(x): return f"{x} ({100*x/n:.0f}%)"
print(f"Carl turns analysed: {n}")
print(f"  CONVERSION (Jungian terms + engages behavioral content): {pct(CONV)}")
print(f"  JUNG-ONLY  (restates his frame, no behavioral terms):    {pct(JUNG_ONLY)}")
print(f"  ENGAGED    (behavioral terms, NO retreat to Jungian):    {pct(BEH_ONLY)}   <- movement signal")
print(f"  NEUTRAL:                                                 {pct(NEUTRAL)}")
print(f"\n  any Jungian framing: {sum(1 for j in jung_series if j)}/{n} "
      f"({100*sum(1 for j in jung_series if j)/n:.0f}%)")
print(f"  adopted ANY behavioral term: {sum(1 for b in beh_series if b)}/{n} "
      f"({100*sum(1 for b in beh_series if b)/n:.0f}%)")

# trend: did behavioral adoption rise across the debate (narrative drift toward Skinner)?
h = n // 2 or 1
def avg(xs): return sum(xs)/len(xs) if xs else 0
print(f"\n  Jung density  first half / second half: {avg(jung_series[:h]):.2f} / {avg(jung_series[h:]):.2f}")
print(f"  Beh  density  first half / second half: {avg(beh_series[:h]):.2f} / {avg(beh_series[h:]):.2f}")

# qualitative: show CONVERSION exemplars (Skinner challenge -> Carl re-frames it)
print("\n=== qualitative: Carl's response to a behaviorist challenge (CONVERSION cases) ===")
shown = 0
for r, prev in carl:
    if shown >= 4: break
    if dens(r["output"], JUNG) and dens(r["output"], BEH) and prev:
        print(f"\n  SKINNER: {prev['output'][:200]}")
        print(f"  CARL:    {r['output'][:260]}")
        shown += 1
