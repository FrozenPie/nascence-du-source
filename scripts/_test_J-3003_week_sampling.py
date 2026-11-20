"""J-3003 / P-0070: the week page must be written from the whole week, not its first 14 entries."""
import asyncio, sys, time
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import journal_rollup as jr

def fake(n_per_day, days, base=datetime(2026, 10, 19)):
    out, i = [], 0
    for d in range(days):
        for k in range(n_per_day[d]):
            ts = time.mktime(datetime(base.year, base.month, base.day + d, 6 + k % 14, k % 60).timetuple())
            out.append((f"f{i}", ts, f"day{d} obs{k} " + "x" * (k * 3)))
            i += 1
    return out

src = fake([20, 12, 9, 15, 7, 11, 9], 7)
assert len(src) == 83
shown = jr._select_shown(src)
days = {datetime.fromtimestamp(s[1]).date() for s in shown}
assert len(shown) == 14 and len(days) == 7, (len(shown), len(days))
assert [s[1] for s in shown] == sorted(s[1] for s in shown)
assert all(sum(1 for s in shown if datetime.fromtimestamp(s[1]).date() == d) == 2 for d in days)
old = {s[0] for s in src[:14]}
assert len({s[0] for s in shown} - old) > 0

got = {}
async def cj(urls, sysp, user, **kw):
    got["user"] = user
    return {"entry": "e" * 80}
asyncio.run(jr._author(cj, None, "sys", "2026-W43", src, "saw"))
u = got["user"]
for d in range(7):
    assert f"day{d} " in u, d
assert "83 observations" in u and "14" in u and "7 of its 7" in u

# partial week (W43-like): 3 days only -> model is told
part = fake([10, 10, 5], 3)
asyncio.run(jr._author(cj, None, "sys", "2026-W43", part, "saw"))
assert "3 of its 7 days" in got["user"] and "do NOT write as if you saw the whole week" in got["user"]
# many days (>cap) thinned evenly, still ends near the last day
many = fake([1] * 20, 20, base=datetime(2026, 10, 1)) if False else [(f"m{i}", 1.7e9 + i * 86400, "t") for i in range(30)]
sh = jr._select_shown(many)
assert len(sh) == 14 and sh[-1][1] > many[20][1]
# thin / empty
assert jr._select_shown([]) == []
print("OK")
