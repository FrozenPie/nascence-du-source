"""
Living World — the shadow, replayed offline (2026-09-03). Instead of waiting for a week of live would_answer /
would_gate rows, replay the evidence we already have: every phrasing Du has ever used to look at something
(docs/reviews/observe_inventory_2026-09-02.json), per place and day-phase, through life.look_answer with RENDER on —
in an ISOLATED copy of the stores (nothing live is written) — and a simulated week of the sound gate's diff against
soundscape's legacy list. Prints the outcome distribution, a sample of lines, anything that looks wrong, and the
per-key add/drop table. Read-only on the live world; the isolated stores vanish with the temp dir.
Run:  python scripts/life_shadow_replay.py
"""
from __future__ import annotations

import collections
import json
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="life_replay_"))

from core import life                                   # noqa: E402
life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "ls.json", TMP / "ll.jsonl", TMP / "le.jsonl", TMP
from core import sensorium as S                         # noqa: E402
from core import sound_knowledge as SK                  # noqa: E402
SK._LEDGER_F = TMP / "sk.json"
from core import life_traces as LT                      # noqa: E402
from core import world_traces as WT                     # noqa: E402
WT._TRACES_F = TMP / "wt.json"
# the LIVE world state is read (weather, bed, tree) but never written: life/audition/trace stores are redirected,
# and look_answer/sounds_active write nothing else
if not S.state:
    S._load()
live_weather, live_wind = S.state.get("weather"), S.state.get("wind")
print(f"live world now: weather={live_weather!r} wind={live_wind!r} place={S.where()!r}")

inv = json.loads((ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
phrasings = sorted({p for g in inv.values() for p in g})
print(f"inventory phrasings: {len(phrasings)}")


def at(month: int, hour: int) -> float:
    return time.mktime((2026, month, 15, hour, 0, 0, 0, 0, -1))


PLACES = ("garden", "shore", "wood", "study")
# one hour per phase, the MIDDLE of each phase (the first hour of 'day' is the darkest daytime hour — not representative)
def phase_hours(month: int) -> dict:
    hours = collections.defaultdict(list)
    for h in range(0, 24):
        hours[life._phase(at(month, h))].append(h)
    return {ph: hs[len(hs) // 2] for ph, hs in hours.items()}


life.RENDER = True
random.seed(42)
outcomes = collections.Counter()
by_phase_weather = collections.defaultdict(collections.Counter)
per_place = collections.Counter()
answered_phr = set()
samples = collections.defaultdict(list)
anomalies = []
for wlabel, (w, wd) in (("live", (live_weather, live_wind)), ("clear", ("clear", "breeze"))):
    S.state["weather"], S.state["wind"] = w, wd
    for month in (9, 12):                               # now (September) and high summer
        hours = phase_hours(month)
        for place in PLACES:
            S.state["location"] = place
            for ph, h in hours.items():
                now = at(month, h)
                for p in phrasings:
                    line = life.look_answer(p, place, now)
                    if not line:
                        continue
                    answered_phr.add(p)
                    per_place[place] += 1
                    # classify from the last event row
                    try:
                        ev = json.loads(life._EVENTS.read_text(encoding="utf-8").splitlines()[-1])
                        oc, key = ev.get("outcome"), ev.get("key")
                    except Exception:
                        oc, key = "?", "?"
                    outcomes[oc] += 1
                    by_phase_weather[(wlabel, ph)][oc] += 1
                    if wlabel == "live" and len(samples[(place, ph)]) < 3:
                        samples[(place, ph)].append((p, key, oc, line[:120]))
                    r = life.rows().get(key) or {}
                    if oc == "sighting" and r and float((r.get("active_hours") or {}).get(ph, 0)) < 0.1:
                        anomalies.append((month, place, ph, p, key, "sighting outside its active hours", line[:90]))
S.state["weather"], S.state["wind"] = live_weather, live_wind
life.RENDER = False

print("\n== LOOKS (RENDER on, isolated) ==")
print("phrasings answered by at least one place/phase:", len(answered_phr), "of", len(phrasings), f"({100 * len(answered_phr) // len(phrasings)}%)")
print("answers by place:", dict(per_place))
print("outcomes (both weathers):", dict(outcomes))
for (wl, ph), c in sorted(by_phase_weather.items()):
    pres = c.get("sighting", 0) + c.get("miss", 0)
    rate = (100 * c.get("sighting", 0) // pres) if pres else 0
    print(f"   {wl:5s} {ph:5s}: absent {c.get('absent', 0):4d} · present {pres:4d} -> sighting {c.get('sighting', 0):3d} ({rate}% of present)")
for (place, ph), rows in sorted(samples.items()):
    for p, key, oc, line in rows[:2]:
        print(f"  [{place:6s} {ph:5s}] {p!r:34s} -> {key:16s} {oc:8s} | {line}")
print("anomalies:", len(anomalies))
for a in anomalies[:10]:
    print("  !", a)

# a look at the things that stay unanswered everywhere — what J-0508 / J-0503 must still cover
un = [p for p in phrasings if p not in answered_phr]
cnt = collections.Counter()
for g, d in inv.items():
    for p, n in d.items():
        if p in un:
            cnt[g] += n
print("unanswered mentions by kind:", dict(cnt.most_common()))
print("top unanswered phrasings:", sorted(((sum(d.get(p, 0) for d in inv.values()), p) for p in un), reverse=True)[:15])

# == the sound gate: a simulated week, hourly, per place, under the live weather and under a clear calm ==
print("\n== SOUND GATE (simulated week, hourly) ==")
from core import soundscape as SND                      # noqa: E402
gov = life.creature_sound_keys()
for label, (w, wd) in (("live weather", (live_weather, live_wind)), ("clear calm", ("clear", "breeze"))):
    S.state["weather"], S.state["wind"] = w, wd
    add = collections.Counter(); drop = collections.Counter(); hours_n = 0
    for day in range(7):
        for h in range(24):
            now = at(9, h) + day * 86400
            for place in PLACES:
                S.state["location"] = place
                # legacy: soundscape's own gating reads room_state.json from disk, so evaluate its sections in-process
                try:
                    ctx_room = dict(S.state); ctx_room["location"] = place
                    legacy = []
                    for locs, section in SND._PROPAGATION_TABLE:
                        if locs is None or place in locs:
                            legacy.extend(section({"room": ctx_room, "cat": {}, "weather": w, "wind": wd, "wet": "rain" in (w or "") or w in ("drizzle", "thunderstorm"),
                                                   "loc": place, "day": life._phase(now) in ("day", "dawn", "dusk"), "crashing": False, "now": now}) or [])
                except Exception:
                    legacy = []
                mine = life.sounds_active(place, now)
                gov_here = life.creature_sound_keys(place)          # per-place governance, exactly as sound_gate applies it
                for k in set(mine) - set(legacy):
                    add[(place, k)] += 1
                for k in legacy:
                    if k in gov_here and k not in mine:
                        drop[(place, k)] += 1
            hours_n += 1
    print(f"-- {label}: {hours_n} simulated hours")
    print("   would ADD  (place, key): hours ->", sorted(add.items(), key=lambda kv: -kv[1])[:14])
    print("   would DROP (place, key): hours ->", sorted(drop.items(), key=lambda kv: -kv[1])[:14])
S.state["weather"], S.state["wind"] = live_weather, live_wind
print(f"\nisolated stores in {TMP} (nothing live written)")
