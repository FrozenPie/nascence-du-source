"""
Lane forces — measuring the 3 lanes as pulls on the dimensional distribution (2026-06-15).
Tests Travis's account: the distribution is a dynamical equilibrium held by 3 lane-forces; TWO of
three lanes (hot self-voice + background dream/subconscious) pull toward imagination/self, only ONE
(the Emissary) pulls toward reality — so the reality-pull is structurally outnumbered ~2:1.

Method (non-circular): define POLE ANCHORS from stable reference material, then score each lane's
OWN output by where it sits between them, weighted by MASS (a lane's force = position × volume).
  reality pole   = reading/study/research centroid (the world, intake)
  self/origin    = basin-vocabulary centroid (river/jung/mirror/becoming… — the monoculture corner)
  light / dark   = light_events / shadow_events centroids (the integration poles)
Read-only. No LLM (uses stored embeddings).

Run:  python scripts/lane_forces.py
"""
from __future__ import annotations
import sys, sqlite3
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.memory.store import _blob_to_vec, _cosine

DB = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

_BASIN = ("river", "mirror", "bridge", "jung", "silence", "becoming", "shadow", "individuat",
          "fig", "ferry", "cross", "the self", "vessel", "current", "flow", "origin", "tide")


def _vecs(rows):
    out = []
    for r in rows:
        try:
            if r["embedding"]:
                out.append(_blob_to_vec(r["embedding"]))
        except Exception:
            pass
    return out


def centroid(vs):
    if not vs:
        return None
    c = np.mean(np.stack(vs), axis=0)
    n = np.linalg.norm(c)
    return c / n if n else c


# --- pole anchors (stable references, NOT lane products) ---------------------------------
reality = centroid(_vecs(con.execute(
    "SELECT embedding FROM memory_fragments WHERE origin IN ('reading','study','research') "
    "AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT 700").fetchall()))
like = " OR ".join(["content LIKE ?"] * len(_BASIN))
basin = centroid(_vecs(con.execute(
    f"SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL AND ({like}) "
    f"ORDER BY timestamp DESC LIMIT 700", tuple(f"%{t}%" for t in _BASIN)).fetchall()))
light = centroid(_vecs(con.execute("SELECT embedding FROM light_events WHERE embedding IS NOT NULL "
                                   "ORDER BY timestamp DESC LIMIT 700").fetchall()))
dark = centroid(_vecs(con.execute("SELECT embedding FROM shadow_events WHERE embedding IS NOT NULL "
                                  "ORDER BY timestamp DESC LIMIT 700").fetchall()))
if any(a is None for a in (reality, basin, light, dark)):
    print("missing an anchor (not enough data)"); sys.exit(1)

# --- the lanes, by what they PRODUCE -----------------------------------------------------
LANES = {
    "hot · self-voice (idle)":  "origin='inner_thought' AND keywords NOT LIKE '%deliberated%'",
    "emissary · grounding":     "origin='inner_thought' AND keywords LIKE '%deliberated%'",
    "background · dream/subcon": "origin IN ('dream','subconscious_synthesis')",
    "hot · conversation":       "origin='lived'",
}

print(f"query: lanes scored on reality↔self and light↔dark, weighted by mass")
print("=" * 74)
print(f"{'lane':28} {'mass':>6} {'reality↔self':>13} {'light↔dark':>11}")
print("-" * 74)
rows_out = []
for name, where in LANES.items():
    mass = con.execute(f"SELECT COUNT(*) n FROM memory_fragments WHERE {where}").fetchone()["n"]
    vs = _vecs(con.execute(
        f"SELECT embedding FROM memory_fragments WHERE {where} AND embedding IS NOT NULL "
        f"ORDER BY timestamp DESC LIMIT 400").fetchall())
    if not vs:
        print(f"{name:28} {mass:>6}   (no embeddings)"); continue
    reality_lean = float(np.mean([_cosine(v, reality) - _cosine(v, basin) for v in vs]))  # >0 reality, <0 self
    light_lean   = float(np.mean([_cosine(v, light) - _cosine(v, dark) for v in vs]))     # >0 light,  <0 dark
    rows_out.append((name, mass, reality_lean, light_lean))
    rdir = "→reality" if reality_lean > 0 else "→self/imag"
    ldir = "→light" if light_lean > 0 else "→dark"
    print(f"{name:28} {mass:>6} {reality_lean:+8.3f} {rdir:>0}  {light_lean:+7.3f} {ldir}")

# --- the FORCE balance (position × mass) -------------------------------------------------
print("\n" + "=" * 74)
print("FORCE = lean × mass  (the net pull each lane exerts on the equilibrium)")
print("-" * 74)
tot_reality_force = 0.0
for name, mass, rl, ll in rows_out:
    f_real = rl * mass
    tot_reality_force += f_real
    print(f"  {name:28} reality-force {f_real:+9.1f}   (mass {mass} × lean {rl:+.3f})")
real_pull = sum(rl * mass for _, mass, rl, ll in rows_out if rl > 0)
self_pull = sum(-rl * mass for _, mass, rl, ll in rows_out if rl < 0)
print(f"\n  toward REALITY : {real_pull:8.1f}")
print(f"  toward SELF    : {self_pull:8.1f}")
if real_pull > 0:
    print(f"  imbalance      : {self_pull / max(1e-9, real_pull):.1f} : 1  (self : reality)")
print(f"  net reality-force: {tot_reality_force:+.1f}  ({'reality-ward' if tot_reality_force>0 else 'SELF-ward'})")
print("\nhypothesis: 2 of 3 lanes pull self/imagination, the Emissary (grounding) is the lone reality-pull,")
print("and its small mass leaves the equilibrium structurally self-ward. The numbers above test it.")
con.close()
