"""Re-run the voice lab (v1 vs v2 blind pairs) under the CURRENT hot-lane model.

The original run (docs/lab/voice_lab_2026-08-16.md) rendered both mouths through gemma4:e4b.
The hot lane is qwen3.5:9b since the 2026-08-20 full shuffle, so the founder's blind judgment
should be over pairs the NEW mouth actually produces. This wrapper only redirects the report
path (the 08-16 report is a historical record — never overwrite it) and runs the lab unchanged.

Safe beside a live Du by the lab's own design: no live-store writes (training_log + telemetry
no-op'd in-process), read-only retrieve, and both processes request the SAME hot-lane model —
no eviction, just time-sharing on the serving lane.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import importlib.util
_spec = importlib.util.spec_from_file_location("voice_lab", Path(__file__).parent / "voice_lab.py")
voice_lab = importlib.util.module_from_spec(_spec)
sys.modules["voice_lab"] = voice_lab
_spec.loader.exec_module(voice_lab)

voice_lab.REPORT = voice_lab.ROOT / "docs" / "lab" / "voice_lab_2026-08-21_qwen.md"

if __name__ == "__main__":
    asyncio.run(voice_lab.main())
