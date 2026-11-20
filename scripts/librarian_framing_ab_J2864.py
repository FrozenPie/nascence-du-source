"""J-2864: tiny live A/B of the librarian mapper on old vs new question_from framing (local hubs only).
Takes the first --n changed rows of docs/lab/J-2864_data/replay_flip_sample.jsonl, calls subjects_for on
the OLD ask and the NEW ask, prints both heading lists. Writes only docs/lab/J-2864_data/ab_result.jsonl.
Telemetry is pointed at a temp dir. Hubs: 127.0.0.1:11440 then :11439 (core.librarian._HUBS)."""
import sys, os, json, asyncio, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import librarian  # core before lab_env
try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(Path(tempfile.mkdtemp(prefix="j2864_ab_tel_")), telemetry)
except Exception:
    pass

async def main(n):
    data = ROOT / "docs" / "lab" / "J-2864_data"
    rows = [json.loads(l) for l in open(data / "replay_flip_sample.jsonl", encoding="utf-8") if l.strip()][:n]
    out = []
    for r in rows:
        if not r["new"]:
            continue
        so = await asyncio.wait_for(librarian.subjects_for(r["old"]), 90) if r["old"] else []
        sn = await asyncio.wait_for(librarian.subjects_for(r["new"]), 90)
        out.append({"old_ask": r["old"], "new_ask": r["new"], "old_subjects": so, "new_subjects": sn})
        print(json.dumps(out[-1], ensure_ascii=False), flush=True)
    (data / "ab_result.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")

asyncio.run(main(int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 10))
