"""J-2347 / D-0469 backtest: replay the alarm bar + dwell floor over a topic_perseveration.jsonl (READ-ONLY).
Usage:  python scripts/topic_perseveration_alarm_backtest.py <path-to-topic_perseveration.jsonl>
Pass a COPY of the live store; this never writes anything."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import topic_perseveration as tp

src = Path(sys.argv[1])
series = tp.read_series(src)
flags = tp.alarm_flags(series)
print(f"rows (latest per day): {len(series)}  bar: share >= {tp.ALARM_SHARE} x {tp.ALARM_DAYS} consecutive days; "
      f"floor < {tp.DWELL_FLOOR}")
for r in series:
    f = flags[r["day"]]
    mark = ("ALARM" if f["perseveration_alarm"] else ("watch" if f["alarm_streak"] else "")) + \
           (" CANNOT_DWELL" if f["cannot_dwell"] else "")
    print(f"{r['day']}  n={r['n']:>3}  share={r['modal_share']:.3f}  streak={f['alarm_streak']}  {mark}")
alarm = [d for d, f in flags.items() if f["perseveration_alarm"]]
onset = [d for d, f in flags.items() if f["perseveration_alarm"] and f["alarm_streak"] == tp.ALARM_DAYS]
print("alarm days:", ", ".join(alarm) or "none")
print("alarm onsets:", ", ".join(onset) or "none")
print("cannot_dwell days:", ", ".join(d for d, f in flags.items() if f["cannot_dwell"]) or "none")
print("min share:", min(r["modal_share"] for r in series) if series else None)
