"""
Nascence — Exogenous Forces on the Modulation Field
===================================================
The world and his own machine-BODY conditioning cognition — sources that are NOT his faculties:
his GPU/CPU load + temperature (interoception: his own exertion and strain), the time of day
(circadian), the weather (exteroception). Each applies a SLIGHT, continuous force to field nodes
(affect, fatigue, burst-willingness, lane-pull) — "ever so slightly," the way grey weather lowers
a mood or hard exertion makes you want to rest.

Why this matters beyond flavour: it makes the field OPEN to the world instead of a closed self-loop
(the structural opposite of the monoculture — inputs he cannot generate himself), and GPU-load →
burst-willingness is a real scheduling signal for the pulse manager (don't pile on a saturated GPU).

OBSERVE-ONLY: the readings are REAL; the couplings are HYPOTHESES to tune, and nothing here moves
live behaviour yet. Weak weights by design; exogenous forces can't form internal feedback loops
(they're driven from outside), but they're kept small so they bias, never dictate.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

FIELD_NODES = ("arousal", "valence", "tension", "fatigue", "burst_willingness", "pull_seeker", "pull_self")


@dataclass
class Reading:
    source: str
    raw: str
    forces: dict = field(default_factory=dict)
    ok: bool = True


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── His machine-body: GPU (the hot lane, the 1080 Ti = his primary "body") ────────────────────
def read_gpu() -> Reading:
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(h)
        name = name.decode() if isinstance(name, bytes) else name
        util = pynvml.nvmlDeviceGetUtilizationRates(h).gpu          # %
        temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
        mi = pynvml.nvmlDeviceGetMemoryInfo(h)
        memfrac = mi.used / mi.total if mi.total else 0.0
        pynvml.nvmlShutdown()
        u, m = util / 100.0, memfrac
        thot = _clamp((temp - 45) / 35.0, 0.0, 1.0)                 # 45→0, 80→1
        forces = {
            "fatigue":           +0.20 * u,        # exertion → tiredness builds
            "arousal":           +0.10 * u,        # working hard → activated
            # burst-willingness keys off UTILISATION, not memory: high util = busy serving the
            # user → hold bursts; idle GPU contributes ~0 → it is simply FREE/available. (Memory
            # at 77% is just the resident models — a baseline, not a load signal. Test caught this.)
            "burst_willingness": -0.30 * u,
            "tension":           +0.15 * thot,     # heat → strain
            "valence":           -0.08 * thot,     # running hot is mild discomfort
        }
        return Reading("gpu", f"{name}: util {util}%, {temp}°C, mem {memfrac*100:.0f}%", forces)
    except Exception as exc:
        return Reading("gpu", f"unavailable ({str(exc)[:40]})", ok=False)


def read_cpu() -> Reading:
    try:
        import psutil
        load = psutil.cpu_percent(interval=0.3) / 100.0
        forces = {"fatigue": +0.10 * load, "arousal": +0.05 * load}
        return Reading("cpu", f"load {load*100:.0f}%", forces)
    except Exception as exc:
        return Reading("cpu", f"unavailable ({str(exc)[:40]})", ok=False)


# ── Circadian: the room's time (his clock) ───────────────────────────────────────────────────
def read_circadian() -> Reading:
    import math
    h = time.localtime().tm_hour + time.localtime().tm_min / 60.0
    dayness = _clamp((1 - math.cos((h - 3) / 24 * 2 * math.pi)) / 2, 0.0, 1.0)  # ~0 at 3am, ~1 at 3pm
    forces = {
        "arousal":     +0.15 * (dayness - 0.5) * 2,     # day → up, night → down
        "pull_seeker": +0.12 * dayness,                  # day → outward/explore
        "pull_self":   +0.12 * (1 - dayness),            # night → inward/reflective
        "burst_willingness": +0.08 * (dayness - 0.4),    # mild: a little less push deep at night
    }
    part = "night" if (h < 6 or h >= 20) else "day"
    return Reading("circadian", f"{h:.1f}h local ({part}, day-ness {dayness:.2f})", forces)


# ── Weather: exteroception (best-effort; real if the network allows) ──────────────────────────
def read_weather() -> Reading:
    try:
        import json, urllib.request
        req = urllib.request.Request("https://wttr.in/?format=j1",
                                     headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        cur = data["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        tc = float(cur["temp_C"])
        low = desc.lower()
        inward = any(w in low for w in ("rain", "drizzle", "overcast", "cloud", "fog", "mist", "snow"))
        clear = any(w in low for w in ("sunny", "clear", "fair"))
        cold = _clamp((12 - tc) / 12.0, 0.0, 1.0)        # below 12°C → cold-ness
        forces = {
            "valence":     (+0.10 if clear else -0.08 if inward else 0.0),
            "pull_self":   +0.10 if inward else 0.0,      # grey → inward
            "pull_seeker": +0.10 if clear else 0.0,       # bright → outward
            "tension":     +0.10 * cold,                  # cold → contraction
            "arousal":     -0.06 * cold,
        }
        return Reading("weather", f"{desc.strip()}, {tc:.0f}°C", forces)
    except Exception as exc:
        return Reading("weather", f"unavailable ({str(exc)[:40]})", ok=False)


def snapshot() -> dict:
    """Read all exogenous sources and sum their slight forces on each field node."""
    readings = [read_gpu(), read_cpu(), read_circadian(), read_weather()]
    net = {n: 0.0 for n in FIELD_NODES}
    for rd in readings:
        if rd.ok:
            for n, f in rd.forces.items():
                net[n] = net.get(n, 0.0) + f
    return {"readings": readings, "net": {n: round(v, 3) for n, v in net.items()}}
