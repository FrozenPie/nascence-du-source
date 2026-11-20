"""J-4346: isolated checks for soundscape.mix() shadow + reader. All writes go to a temp dir."""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import soundscape as sc          # noqa: E402  (core BEFORE anything lab-ish)
sys.path.insert(0, str(ROOT / "scripts"))
import soundscape_mix_shadow_read as rd    # noqa: E402

fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)

tmp = Path(tempfile.mkdtemp(prefix="j4346_"))
sc._MIX_LOG = tmp / "soundscape_mix_shadow.jsonl"

check("flag default OFF", sc.MIX_SHADOW is False)
check("off -> no row", sc._mix_shadow_record("study", 1000.0) == 0 and not sc._MIX_LOG.exists())

keys = [k for k in ("waves_crashing", "tide_pool_trickle", "kingfisher_call", "gull_cries") if k in sc._SOUNDS]
m = sc.mix(keys, now=5000.0)
check("mix returns a dict with all keys", m is not None and m["n_active"] == len(keys))
check("n_audible <= n_active, masked complements", m["n_audible"] + len(m["masked"]) == m["n_active"])
check("composite has six axes", set(m["composite"]) == set(sc._AXES))
solo = sc.mix(["waves_crashing"], now=5000.0)
check("a lone sound is never masked", solo["masked"] == [] and solo["n_audible"] == 1)
check("mix of nothing -> None, never raises", sc.mix([], now=1.0) is None and sc.mix(["no_such_key"], now=1.0) is None)
aud = m["audibility"]
check("audibility never exceeds own energy", all(a <= sc.coords(k)["energy"] + 1.0 for k, a in aud.items()))

sc.MIX_SHADOW = True
orig = sc.active_sounds
sc.active_sounds = lambda: keys
try:
    check("on -> one row", sc._mix_shadow_record("shore", 9000.0) == 1)
    check("throttled inside the interval", sc._mix_shadow_record("shore", 9010.0) == 0)
    check("next interval writes", sc._mix_shadow_record("shore", 9100.0) == 1)
    sc.world_tick("shore", 5.0)   # fail-open path through the loop hook
    rows = [json.loads(l) for l in open(sc._MIX_LOG, encoding="utf-8")]
    check("rows carry place + composite", all("place" in r and "composite" in r for r in rows))
    sc._mix_shadow_record = lambda *a, **k: 1 / 0
    try:
        sc.world_tick("shore", 5.0); ok = True
    except Exception:
        ok = False
    check("a failing recorder cannot break world_tick", ok)
finally:
    sc.active_sounds = orig
    sc.MIX_SHADOW = False

# reader on synthetic rows: tick steps small, place steps big, masked share 0.3, n_audible <= 4
syn = []
for i in range(300):
    pl = "study" if (i // 50) % 2 == 0 else "shore"
    base = 0.2 if pl == "study" else 0.7
    syn.append({"ts": i * 30.0, "place": pl, "n_active": 5, "n_audible": 3, "masked": ["a", "b"] if i % 3 else ["a"],
                "keys": ["a", "b", "c"], "composite": {x: base + 0.001 * (i % 5) for x in sc._AXES}})
r = rd.evaluate(syn)
check("reader PASS on a healthy synthetic log", r["verdict"] == "PASS" and r["masked_share"] == round(sum(len(x["masked"]) for x in syn) / 1500, 4))
dead = [dict(x, masked=[]) for x in syn]
check("reader FAIL when the law is dead (0% masked)", rd.evaluate(dead)["verdict"] == "FAIL")
check("reader INSUFFICIENT on few rows", rd.evaluate(syn[:5])["verdict"] == "INSUFFICIENT")
print("FAILS:", fails or "none")
sys.exit(1 if fails else 0)
