"""J-3431: synthetic check of the uptime instrument (temp dir only, no live data)."""
import sys, json, tempfile, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import j3431_standlife_downtime as m

def L(t, kind=""):
    s = datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S") + ",000 [nascence.x] "
    if kind == "boot":
        s += "Memory store initialised at C:" + chr(92) + "Nascence" + chr(92) + "data" + chr(92) + "memory" + chr(92) + "nascence.db"
    elif kind == "shut":
        s += "Nascence shutting down."
    else:
        s += "tick"
    return s

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    t0 = datetime.datetime(2026, 7, 10).timestamp()
    lines = [L(t0, "boot")] + [L(t0 + i * 60) for i in range(1, 60)] + [L(t0 + 3600, "shut")]       # up 0..3600
    t1 = t0 + 3600 + 7200                                                                              # 2 h down
    lines += [L(t1, "boot")] + [L(t1 + i * 60) for i in range(1, 30)]                                  # up 1740 s
    (d / "nascence.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    m.DATA = d
    parsed = m.parse_log()
    iv = m.up_intervals(parsed, 600.0, 0.0)
    assert len(iv) == 2, iv
    starts = [x[0] for x in iv]
    # stand held at t0+1800, dissolved at t1+900: wall 9000 s, up 1800 + 900 = 2700 s
    up = m.uptime_between(iv, starts, t0 + 1800, t1 + 900)
    assert abs(up - 2700) < 1, up
    assert abs(m.uptime_between(iv, starts, t0 + 3700, t0 + 7000)) < 1e-6          # entirely down
    assert abs(m.uptime_between(iv, starts, t0 + 100, t0 + 200) - 100) < 1e-6      # entirely up
    # same file with no shutdown line and no boot marker still cuts on the 600 s gap
    iv2 = m.up_intervals([(t, "") for t, _ in parsed], 600.0, 0.0)
    assert len(iv2) == 2, iv2
print("J-3431 standlife instrument test OK")
