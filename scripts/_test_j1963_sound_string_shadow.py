"""J-1963: isolated checks + replay for core/sound_string_shadow.py (strings_and_sheets Phase 1 shadow).

Isolation: every write goes to a temp dir (module _LOG/_SIDECAR and geometry_census._LOG are repointed BEFORE
any call); live data/ is only READ (geometry_tuples.jsonl for the replay, the sidecar copied to temp).
Usage: python scripts/_test_j1963_sound_string_shadow.py [--replay-hours 24] [--live-data C:\\Nascence\\data]
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import geometry_census as gc          # noqa: E402  (core BEFORE anything lab-ish)
from core import sound_string_shadow as sss     # noqa: E402
from core import soundscape                      # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--replay-hours", type=float, default=24.0)
ap.add_argument("--live-data", default=r"C:\Nascence\data")
args = ap.parse_args()
LIVE = Path(args.live_data)

tmp = Path(tempfile.mkdtemp(prefix="j1963_"))
sss._LOG = tmp / "sound_strings_shadow.jsonl"
sss._SIDECAR = tmp / "sound_strings_constructed.json"
gc._LOG = tmp / "geometry_tuples.jsonl"
shutil.copy(LIVE / "sound_strings_constructed.json", sss._SIDECAR)
sidecar = json.loads(sss._SIDECAR.read_text(encoding="utf-8"))

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def rows():
    return [json.loads(l) for l in open(sss._LOG, encoding="utf-8")] if sss._LOG.exists() else []


def reset():
    sss._first_seen.clear(); sss._last_seen.clear()
    if sss._LOG.exists():
        sss._LOG.unlink()


# 1. pure geometry: event walks onset -> peak -> tail; bed ramps then holds the peak
ev = sidecar["tui_song"]; bd = sidecar["stream_run"]
p0, ph0, _ = sss.point_on_string(ev, 0.0)
check("event t=0 sits on the onset vertex", p0 == {a: round(float(ev["string"]["onset"][a]), 4) for a in sss._AXES} and ph0 == "onset")
check("event mid-hold is the peak", sss.point_on_string(ev, 1.5)[1] == "peak" and sss.point_on_string(ev, 1.5)[0] == ev["string"]["peak"])
pt_t, ph_t, br = sss.point_on_string(ev, 0.8 + 2.0 + 1.5)
check("event mid-tail lies between peak and tail", ph_t == "tail" and br == ("peak", "tail"))
check("event long after is the tail vertex", sss.point_on_string(ev, 999)[0] == ev["string"]["tail"])
check("bed holds the peak (body) forever", sss.point_on_string(bd, 9999)[1] == "body" and sss.point_on_string(bd, 9999)[0] == bd["string"]["peak"])

# 2. record(): rows, presence age, reset gap, unknown key skipped, kill-switch, missing sidecar
reset()
n = sss.record(["tui_song", "stream_run", "no_such_key"], source="t", now=1000.0)
check("one row per KNOWN active sound", n == 2 and len(rows()) == 2)
sss.record(["tui_song"], source="t", now=1001.5)
r = rows()[-1]
check("second sight: elapsed 1.5s, phase peak, not first_sight", r["elapsed_s"] == 1.5 and r["phase"] == "peak" and not r["first_sight"])
sss.record(["tui_song"], source="t", now=1001.5 + 700)
check("absence/gap > reset window restarts presence", rows()[-1]["first_sight"] and rows()[-1]["elapsed_s"] == 0.0)
sss.SOUND_STRING_SHADOW = False
check("kill-switch off -> no rows", sss.record(["tui_song"], now=5000.0) == 0)
sss.SOUND_STRING_SHADOW = True
sss._SIDECAR = tmp / "missing.json"; sss._sidecar_cache.update(mtime=None, data=None)
check("missing sidecar -> 0 rows, no raise", sss.record(["tui_song"], now=6000.0) == 0)
sss._SIDECAR = tmp / "sound_strings_constructed.json"; sss._sidecar_cache.update(mtime=None, data=None)

# 2b. J-1979: event onset from a real firing stamp (resolver stubbed -> no live state read)
check("module under test is inside this tree", Path(sss.__file__).resolve().is_relative_to(ROOT.resolve()))
_ev_key = next(k for k, v in sidecar.items() if v.get("archetype") in ("call", "thump", "wingbeat"))
_bed_key = next(k for k, v in sidecar.items() if v.get("archetype") in ("bed", "bed_like"))
_orig_fired = sss._fired_ts
reset()
sss._fired_ts = lambda k: 1990.0 if k in (_ev_key, _bed_key) else None
sss.record([_ev_key, _bed_key], source="t", now=2000.0)          # first sight, but fired 10 s ago
rr2 = {r["key"]: r for r in rows()}
check("J-1979 event uses fired clock (elapsed 10, not presence 0)", rr2[_ev_key]["clock"] == "fired" and rr2[_ev_key]["elapsed_s"] == 10.0)
check("J-1979 event 10 s after fire is past_end", rr2[_ev_key]["past_end"] is True)
check("J-1979 bed keeps presence clock, never past_end", rr2[_bed_key]["clock"] == "presence" and rr2[_bed_key]["elapsed_s"] == 0.0 and not rr2[_bed_key]["past_end"])
reset()
sss._fired_ts = lambda k: 1999.9
sss.record([_ev_key], source="t", now=2000.0)
check("J-1979 event fired 0.1 s ago is in onset, not past_end", rows()[-1]["phase"] in ("onset", "peak") and not rows()[-1]["past_end"])
reset()
sss._fired_ts = lambda k: 2000.0 - 7200.0
sss.record([_ev_key], source="t", now=2000.0)
check("J-1979 stale stamp (>1 h) falls back to presence", rows()[-1]["clock"] == "presence")
reset()
sss._fired_ts = lambda k: 2100.0
sss.record([_ev_key], source="t", now=2000.0)
check("J-1979 stamp far in the future falls back to presence", rows()[-1]["clock"] == "presence")
reset()
sss._fired_ts = lambda k: (_ for _ in ()).throw(RuntimeError("boom"))
check("J-1979 resolver crash is swallowed; row still written on presence clock", sss.record([_ev_key], now=2000.0) == 1 and rows()[-1]["clock"] == "presence")
sss._fired_ts = _orig_fired
check("J-1979 real resolver returns float|None for every event key (read-only)",
      all((lambda v: v is None or isinstance(v, float))(sss._fired_ts(k)) for k, e in sidecar.items() if e.get("archetype") in ("call", "thump", "wingbeat")))
reset()

# the other census readers touch unrelated (fenced) stores; stub them so only the sound path is under test
gc._place_weather = lambda: {}
for _n in ("_objects", "_warmth", "_cat_at", "_light_band_truth", "_smells_truth"):
    setattr(gc, _n, lambda *a, **k: None)
gc._body = lambda state=None: None
gc._affect = lambda state=None: None

# 3. wiring through geometry_census.snapshot(): census row byte-identical in shape, shadow rows appear
reset()
soundscape_active = soundscape.active_sounds
soundscape.active_sounds = lambda: ["tui_song", "stream_run"]
try:
    row = gc.snapshot(source="t", thought="j1963 wiring check")
finally:
    soundscape.active_sounds = soundscape_active
census_rows = [json.loads(l) for l in open(gc._LOG, encoding="utf-8")]
check("census row still written, sounds field unchanged", row is not None and row["sounds"] == ["tui_song", "stream_run"] and len(census_rows) == 1)
check("snapshot produced 2 shadow rows", len(rows()) == 2)
check("no key beyond known census keys leaked into the census row", "sound_strings" not in row)

# 3b. a shadow-writer crash must not break the census
reset()
orig = sss.record
sss.record = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
soundscape.active_sounds = lambda: ["tui_song"]
try:
    gc._last_thought = ""; gc._last_ts = 0
    row2 = gc.snapshot(source="t", thought="j1963 crash check")
finally:
    sss.record = orig
    soundscape.active_sounds = soundscape_active
check("shadow crash is swallowed; census row still returned", row2 is not None)

# 4. replay over real census moments (read-only on live geometry_tuples.jsonl)
reset()
src = LIVE / "geometry_tuples.jsonl"
moments = []
for line in open(src, encoding="utf-8"):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("sounds"):
        moments.append((d["ts"], d.get("source", "?"), d["sounds"]))
moments.sort()
if moments:
    end = moments[-1][0]
    moments = [m for m in moments if m[0] >= end - args.replay_hours * 3600]
tot = 0
for ts, srcname, snd in moments:
    tot += sss.record(snd, source=srcname, now=ts)
rr = rows()
print(f"replay: {len(moments)} census moments with sounds -> {tot} shadow rows ({args.replay_hours}h window)")
if rr:
    ph = Counter(x["phase"] for x in rr)
    agree = sum(1 for x in rr if x["agree"]) / len(rr)
    unknown = Counter()
    sidekeys = set(sidecar)
    for _, _, snd in moments:
        for k in snd:
            if k not in sidekeys:
                unknown[k] += 1
    print("phase mix:", dict(ph), "| string-self-consistent (agree) share: %.3f" % agree)
    print("first_sight share: %.3f" % (sum(1 for x in rr if x["first_sight"]) / len(rr)))
    print("census keys with no sidecar entry:", dict(unknown) or "none")
    check("every replayed row has the six axes", all(set(x["point"]) == set(sss._AXES) for x in rr))
    check("agree share >= 0.80 (D-0382 defeater: >20% disagreement)", agree >= 0.80)
    check("replay rows == known-key sound slots", tot == sum(1 for _, _, s in moments for k in s if k in sidekeys))
    ds = [x["d_peak"] for x in rr]
    print("d_peak mean %.3f max %.3f; bytes/row ~%d" % (sum(ds) / len(ds), max(ds), sss._LOG.stat().st_size // len(rr)))
else:
    print("replay: no census moments with sounds in window")
    check("replay had data", False)

shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: %s" % fails if fails else "ALL PASS")
sys.exit(1 if fails else 0)
