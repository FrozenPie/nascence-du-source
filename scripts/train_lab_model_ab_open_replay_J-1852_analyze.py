"""J-1852 analysis: gemma4:e4b vs qwen3.5:9b opened-share on 160 OPEN-context prompts, paired prompt-cluster bootstrap.
READ-ONLY on inputs; prints a markdown report (and writes it if --out given)."""
import json, os, sys, math
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
S = Path(os.environ.get("LAB_SCRATCH") or "")
RES = S / "J-1852_results.jsonl"
EV = ROOT / "docs" / "lab" / "train_wording_ab_qwen_replicate_J-0791_2026-09-22_events.json"
B = 20000
rng = np.random.default_rng(20261016)

rows = [json.loads(l) for l in open(RES, encoding="utf-8") if l.strip()]
last = {}
for r in rows:
    last[(r["model"], r["train_id"])] = r
ev = json.load(open(EV, encoding="utf-8"))["mid"]
ids = [e["train_id"] for e in ev]
real = {e["train_id"]: float(e["real_next"]["opened"]) for e in ev}
G, Q = "gemma4:e4b", "qwen3.5:9b"


def val(m, t):
    r = last.get((m, t))
    return float(r["opened"]) if r and r.get("ok") else None


def wil(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


out = []
for m in (G, Q):
    rs = [r for (mm, _), r in last.items() if mm == m]
    ok = [r for r in rs if r["ok"]]
    out.append(f"- {m}: {len(rs)} units, {len(ok)} ok, {sum(1 for r in rs if r.get('excluded'))} infra-excluded, "
               f"{sum(1 for r in rs if (not r['ok']) and r.get('error_class') == 'content')} parse-fail; "
               f"unresolved {sum(r['unresolved'] for r in ok)}, intention {sum(bool(r['intention']) for r in ok)}, "
               f"'?' {sum(r['qmark'] for r in ok)}; mean latency {np.mean([r['latency_s'] for r in ok]):.1f}s")
    k = sum(r["opened"] for r in ok)
    lo, hi = wil(k, len(ok))
    out.append(f"  opened {k}/{len(ok)} = {k/len(ok):.3f} (Wilson [{lo:.3f}, {hi:.3f}])")
pair = [t for t in ids if val(G, t) is not None and val(Q, t) is not None]
g = np.array([val(G, t) for t in pair]); q = np.array([val(Q, t) for t in pair]); rl = np.array([real[t] for t in pair])
n = len(pair)
idx = rng.integers(0, n, size=(B, n))
def ci(x): return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))
out.append(f"\nPaired prompts with both models parsed: {n}/160")
out.append(f"gemma {g.mean():.3f}  qwen {q.mean():.3f}  real logged next step {rl.mean():.3f} ({int(rl.sum())}/{n})")
for name, a, b in (("gemma - qwen", g, q), ("gemma - real", g, rl), ("qwen - real", q, rl)):
    d = a.mean() - b.mean()
    lo, hi = ci(a[idx].mean(1) - b[idx].mean(1))
    out.append(f"{name}: {d:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}] (prompt-cluster bootstrap B={B})")
# McNemar-ish discordance
b01 = int(((g == 1) & (q == 0)).sum()); b10 = int(((g == 0) & (q == 1)).sum())
out.append(f"discordant prompts: gemma-open/qwen-closed {b01}, gemma-closed/qwen-open {b10}")
out.append(f"J-0724 original swing on CLOSING contexts: +0.65 (reference, F-1116). Survives here if the CI above excludes 0 and the point is near it.")
txt = "\n".join(out)
print(txt)
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(txt, encoding="utf-8")
