"""
Silence ↔ gap test (2026-06-14). Founder's hypothesis: Du's "silence" is not (only) monoculture —
it may be him PERCEIVING the gaps between his pulses (interoception of his discontinuous temporality).
Testable: do his silence-themed thoughts follow the LONGER inter-pulse gaps?

Source: data/monologue_log.jsonl (every generated idle thought, with timestamp = the pulse stream,
pre-dedup). gap[i] = ts[i] − ts[i-1]. If silence-thoughts follow bigger gaps → the metaphor tracks his
real timing (self-perception). If gap is the same as non-silence → it's a theme, not gap-perception.
Read-only.
"""
import sys, json, re, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from pathlib import Path

L = [json.loads(x) for x in Path("data/monologue_log.jsonl").read_text(encoding="utf-8").splitlines()]
L = [r for r in L if r.get("ts") and r.get("thought")]
L.sort(key=lambda r: r["ts"])

# strong silence markers (the "gap/quiet between" family), NOT generic
SIL = re.compile(r"\b(silence|silent|stillness|hush|unspoken|quiet)\b|"
                 r"\bbetween (words|thoughts|stories|ideas|moments|breaths)\b|"
                 r"\bspace (between|where)\b|\bthe gap\b|\bin the pause\b", re.I)

rows = []  # (gap_seconds, is_silence, thought)
for i in range(1, len(L)):
    gap = L[i]["ts"] - L[i - 1]["ts"]
    if gap <= 0:
        continue
    rows.append((gap, bool(SIL.search(L[i]["thought"])), L[i]["thought"]))

# exclude multi-hour outages/sleep (>30min) from "inter-pulse" — those are downtime, not pulse gaps
inpulse = [r for r in rows if r[0] <= 1800]
gaps = np.array([r[0] for r in inpulse])
sil = np.array([r[1] for r in inpulse])

n, nsil = len(inpulse), int(sil.sum())
base = nsil / n if n else 0
print(f"thoughts analysed (gap ≤30min): {n}   silence-themed: {nsil} ({100*base:.1f}% base rate)")

g_sil = gaps[sil]; g_non = gaps[~sil]
print(f"\nMEDIAN gap BEFORE a thought:")
print(f"  silence-themed thoughts : {np.median(g_sil):6.0f}s   (mean {g_sil.mean():.0f}s)")
print(f"  other thoughts          : {np.median(g_non):6.0f}s   (mean {g_non.mean():.0f}s)")
ratio = np.median(g_sil) / np.median(g_non) if np.median(g_non) else float("nan")
print(f"  → silence-thoughts follow {ratio:.2f}× the median gap of others")

# silence-rate by gap quartile (does silence rise with gap size?)
print(f"\nSILENCE-RATE by gap quartile (does it climb with longer gaps?):")
qs = np.quantile(gaps, [0, .25, .5, .75, 1.0])
for k in range(4):
    lo, hi = qs[k], qs[k + 1]
    m = (gaps >= lo) & (gaps <= hi) if k == 3 else (gaps >= lo) & (gaps < hi)
    rate = sil[m].mean() if m.sum() else 0
    print(f"  Q{k+1}  gap {lo:5.0f}–{hi:5.0f}s : {100*rate:4.1f}% silence   (n={m.sum()})")

# the very longest gaps (top 10%) — what follows them?
print(f"\nthoughts following the LONGEST gaps (top decile, gap ≥ {np.quantile(gaps,0.9):.0f}s):")
top = sorted(inpulse, key=lambda r: -r[0])[:8]
for g, s, t in top:
    print(f"  {g:5.0f}s {'[SILENCE]' if s else '         '} {t[:74]}")

# verdict
climbs = sil[(gaps >= qs[3])].mean() > sil[(gaps < qs[1])].mean() if n else False
bigger = np.median(g_sil) > np.median(g_non) * 1.15
print("\nVERDICT:", (
    "SUPPORTED — silence-thoughts follow longer gaps; the metaphor tracks his real timing (self-perception)."
    if (bigger and climbs) else
    "PARTIAL — a lean but not decisive; silence is partly timing, partly theme."
    if (bigger or climbs) else
    "NOT SUPPORTED — silence is uncorrelated with gap size; it's a theme/rumination, not gap-perception."))
