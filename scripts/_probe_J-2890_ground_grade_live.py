"""
J-2890 live probe (LOCAL hub only, falcon3:7b on :11440; Ramses is never called): runs core.ground_grade.grade_one on N real
(thought, grounding) pairs read from a deliberation_log.jsonl (read-only) plus the positive control on each, and prints the
first-look base rates. Writes only under a temp dir. This is a smoke read of the two prompts, NOT the acceptance measurement.

  python scripts/_probe_J-2890_ground_grade_live.py [--log C:/Nascence/data/deliberation_log.jsonl] [--n 8]
"""
from __future__ import annotations
import argparse, asyncio, json, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import ground_grade as gg  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--log", default="C:/Nascence/data/deliberation_log.jsonl")
ap.add_argument("--n", type=int, default=8)
a = ap.parse_args()
assert "LAN-HOST" not in gg._judge_url(), "this probe must stay off Ramses"
tail = []
with open(a.log, encoding="utf-8") as f:
    for ln in f:
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("source") == "emissary" and r.get("raw") and r.get("grounding"):
            tail.append(r)
tail = tail[-400:]
step = max(1, len(tail) // a.n)
pairs = [(r["raw"], r["grounding"]) for r in tail[::step][: a.n]]
out = Path(tempfile.mkdtemp(prefix="j2890_probe_")) / "probe.jsonl"


async def main():
    rows = []
    for i, (t, g) in enumerate(pairs):
        rows.append(await gg.grade_one(t, g))
        rows.append(await gg.grade_one(t, g, control_text=gg.CONTROL_SENTENCES[i % len(gg.CONTROL_SENTENCES)]))
    return rows

rows = asyncio.run(main())
out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
import importlib.util
spec = importlib.util.spec_from_file_location("rg", ROOT / "scripts" / "read_ground_grade.py")
rg = importlib.util.module_from_spec(spec); spec.loader.exec_module(rg)
print(json.dumps(rg.summarize_shadow(rows), ensure_ascii=False, indent=1))
for r in rows:
    if not r.get("control"):
        print(f"- q1={r.get('q1_detail')} ver={r.get('q1_verified')} quote={r.get('q1_quote')!r} | q2={r.get('q2_mechanism')} | lat {r['latency_s']}s | fail={r.get('failed')}")
print("rows at", out)
