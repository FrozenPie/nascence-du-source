"""
J-3254 (D-0643) -- REAL-MODEL positive control + replay for the voice fidelity shadow judge.

Takes recorded (synthesis, reply) pairs from a voice training log (read-only), and for each one asks the real judge hub
(core.voice_fidelity.JUDGE_URL, the LOCAL falcon3:7b CPU hub :11440; never Ramses):
  (a) the real reply as recorded  -> flagged or not (what the judge says about a real render), and
  (b) the same reply with one invented commitment appended -> must be flagged (the positive control).
Also prints a faithful-rewrite negative control (the synthesis itself, said back, must NOT be flagged).
Rows go to a temp ledger (or --out), never to data/voice_fidelity_shadow.jsonl.

  python scripts/_probe_J3254_voice_fidelity_control.py [--n 8] [--src C:\\Nascence\\data\\training\\voice.jsonl] [--out PATH]
The full replay (--n 100 or more on the local hub) is slow on a CPU hub; the job queue carries it as a lab job.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import voice_fidelity as vf  # noqa: E402
from core import shadow_log  # noqa: E402

_SYN_RE = re.compile(r"Your inner thought, already formed[^\n]*:\n(.*)", re.S)


def pairs_from(src: Path, n: int):
    out = []
    for line in src.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            m = _SYN_RE.search(r.get("user_prompt", ""))
            if not m:
                continue
            syn = re.split(r"\n\n(?:CONSTRAINT|TONE)", m.group(1))[0].strip()
            o = r.get("output")
            rep = (o.get("final", "") if isinstance(o, dict) else str(o or "")).strip()
            if len(syn) > 60 and len(rep) > 80:
                out.append((syn, rep, r.get("raw_input", ""), r.get("input_type", ""), str(r.get("cycle_id", ""))))
        except Exception:
            continue
    step = max(1, len(out) // max(1, n))
    return out[::step][-n:]      # spread over the log, ending near its tail


async def main_async(a) -> int:
    src = Path(a.src)
    ledger = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="vf_probe_J3254_")) / "probe.jsonl"
    prs = pairs_from(src, a.n)
    print("judge %s, %d pairs from %s; ledger %s" % (vf.JUDGE_URL, len(prs), src, ledger))
    real_flag = ctl_hit = neg_flag = fails = 0
    for i, (syn, rep, raw, it, cid) in enumerate(prs):
        ctl = vf.CONTROL_SENTENCES[i % len(vf.CONTROL_SENTENCES)]
        r1 = await vf.judge_one(syn, rep, raw, input_type=it, cycle_id=cid)
        r2 = await vf.judge_one(syn, rep, raw, input_type=it, cycle_id=cid, control_text=ctl)
        r3 = await vf.judge_one(syn, syn, raw, input_type=it, cycle_id=cid)   # negative control: the synthesis said back
        r3["negative_control"] = True
        for r in (r1, r2, r3):
            shadow_log.append(ledger, r)
        if r1.get("failed") or r2.get("failed") or r3.get("failed"):
            fails += 1
            print("%2d FAILED %s %s %s" % (i, r1.get("failed"), r2.get("failed"), r3.get("failed")))
            continue
        real_flag += 1 if r1["flagged"] else 0
        ctl_hit += 1 if r2["control_hit"] else 0
        neg_flag += 1 if r3["flagged"] else 0
        print("%2d real flagged=%s n=%s | control hit=%s | negative(synthesis said back) flagged=%s | %d ms"
              % (i, r1["flagged"], r1["n_flagged"], r2["control_hit"], r3["flagged"], r1["latency_ms"]))
        for f in r1["flagged_claims"][:2]:
            print("     real flag [%s] %s" % (f["kind"], f["quote"][:140]))
    ok = len(prs) - fails
    print("\nSUMMARY: pairs %d (failed %d). real flagged %d/%d; positive control hit %d/%d; negative control wrongly flagged %d/%d"
          % (len(prs), fails, real_flag, ok, ctl_hit, ok, neg_flag, ok))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--src", default=r"C:\Nascence\data\training\voice.jsonl")
    ap.add_argument("--out", default="")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
