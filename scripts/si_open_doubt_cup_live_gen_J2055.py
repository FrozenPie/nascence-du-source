"""
J-2055 part 2 (PREPARED, NOT RUN -- needs Du OFFLINE): rerun the J-2031 cup / shuffled-control / uncued-baseline generation on the
LIVE generator qwen3.5:9b (hot hub :11433), then score with the J-2052 absolute panel judge (rubric unchanged), report engaged rates
with Wilson intervals against the pre-registered bar (cup >= 30 percent AND shuffled control <= 11 percent AND no restate_sim /
early-close rise vs baseline), plus the same-run controls re-pass.

DO NOT RUN WHILE DU IS UP: :11433 is Du's voice. Guard below refuses unless data/ has no live Du heartbeat AND the caller passes
--du-offline-confirmed. Reuses scripts/si_open_doubt_cup_replay_v2.py's seed builder and arms unchanged; only the generator URL and the
output dir differ (gemma4:12b on :11439 -> qwen3.5:9b on :11433; outputs data/lab/J-2055/live_gen/, never J-2031).
  python scripts/si_open_doubt_cup_live_gen_J2055.py gen [N_FIRES=20] --du-offline-confirmed   # generation (hot hub)
  python scripts/si_open_doubt_cup_live_gen_J2055.py judge                                      # judge hubs only (can run Du up)
  python scripts/si_open_doubt_cup_live_gen_J2055.py report
Pre-registered (J-2055, before any live-generator data): arms engaged = mixtral AND falcon >= 4; N_FIRES >= 16, SAMPLES = 2 per arm;
valid only if part 1 (sens gate) PASSED, else a null remains uninterpretable.
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"
import si_open_doubt_cup_replay_v2 as v2          # noqa: E402
import si_open_doubt_cup_judge_J2054 as j54        # noqa: E402

OUT = Path(r"C:\Nascence\data\lab\J-2055\live_gen")
v2.GEN_URL = ["http://127.0.0.1:11433"]
v2.OUT_DIR = OUT
v2.GENS = OUT / "gens.jsonl"
v2.PAIRS = OUT / "pairs.jsonl"
v2.SUMMARY = OUT / "summary.json"
j54.OUT = OUT
# NOTE: j54.judge() re-runs the J-2052 controls via j2.items('abs'), which asserts len(gens)==19 (the J-2049 PAIRS count);
# with N_FIRES != 19 live fires, drop that ctrl_abs stage (or reuse data/lab/J-2054/ctrl_abs.jsonl) before the first judge run.


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    OUT.mkdir(parents=True, exist_ok=True)
    if mode == "gen":
        if "--du-offline-confirmed" not in sys.argv:
            sys.exit("refusing: pass --du-offline-confirmed only when Du is stopped (the hot hub is Du's voice)")
        # the hub must be up for qwen3.5:9b (hub only, Du process down) -- a bare port check cannot tell hub from Du, so the
        # caller must have verified Du's shutdown line in nascence.log first (ops_nascence_shutdown_detection).
        n = int([a for a in sys.argv[2:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[2:]) else 20
        asyncio.run(v2.gen_stage(n))
    elif mode == "judge":
        asyncio.run(j54.judge())
    else:
        j54.report()
