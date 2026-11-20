"""
In-vitro test for EXPLORATORY curiosity ignition (2026-06-15, backlog-driven fix). No LLM, temp stores.
THE FIX: exploration is now keyed on the FRONTIER BACKLOG, not quietness — so a ruminating mind (shadow
pegged) can STILL reach out. Tests:
A) backlog present + HIGH shadow → ignites EXPLORATORY (shadow no longer starves it — the bug).
B) high strain + backlog → still classifies DEFENSIVE (strain dominates).
C) EMPTY backlog → quiet mind does NOT ignite (don't reach into a void).
D) kill switch disables the exploratory term.

Run:  python scripts/exploratory_ignition_test.py
"""
from __future__ import annotations
import sys, asyncio, tempfile, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import climate_engine as ce
from core.climate_engine import ClimateEngine, ClimateField
from core import frontier as fr
from core import light_sidecar as _ls

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

iglog = Path(tempfile.gettempdir()) / "ignition_log_test.jsonl"
if iglog.exists(): iglog.unlink()
ce._IGNITION_LOG = iglog
# J-0846 (F-1213): this process's own open_count() shadow rows (heavy-vs-light comparison, when
# FRONTIER_LIGHT_READ is off) used to append straight into the LIVE data/light_sidecar_shadow.jsonl --
# the "heavy 342 -> 0/10" rows of 2026-09-05/06 were THIS script's temp-frontier reads, not Du's.
_shadow_tmp = Path(tempfile.gettempdir()) / "ignition_light_sidecar_shadow_test.jsonl"
_shadow_tmp.unlink(missing_ok=True)
_ls.SHADOW_LOG = _shadow_tmp
_light_tmps = []

def set_backlog(n):
    ftmp = Path(tempfile.gettempdir()) / f"ignition_frontier_{n}.json"
    if ftmp.exists(): ftmp.unlink()
    fr._F = ftmp
    # J-0846 (F-1212/F-1213): redirect the light sidecar too -- _F_LIGHT was derived from _F once at
    # import, so redirecting _F alone left _write_light() rewriting the LIVE data/frontier.light.json.
    # (core/frontier.py now also derives the light path from the current _F, but be explicit here.)
    fr._F_LIGHT = ftmp.with_name(f"ignition_frontier_{n}.light.json")
    fr._F_LIGHT.unlink(missing_ok=True)
    _light_tmps.append(fr._F_LIGHT)
    qs = ["why does capillary action lift water in a narrow tube",
          "what makes granite form its strange surface coatings",
          "how do distant stars produce their steady light",
          "why do rivers meander across the flat plains",
          "what causes the ocean tides to rise and fall",
          "how do honeybees navigate back to the distant hive",
          "why does iron rust when left in the damp air",
          "how do buried seeds know which way is up",
          "why does solid ice float on top of liquid water",
          "what makes the evening sky turn red at sunset"]
    for q in qs[:n]:
        fr.note_question(q, "curiosity")
    return fr.open_count()

def fresh(field):
    e = ClimateEngine(ignition_callback=None)
    e.dissonance.value = 0.0
    e.dissonance.last_ignition_ts = 0.0
    e._contrib = {"strain":0,"completion":0,"shadow":0,"explore":0}
    e.field = field
    return e

def last_log():
    lines = [l for l in iglog.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None

# A — backlog + HIGH shadow still ignites exploratory (THE FIX) -------------------------
print("\n[A] backlog present + HIGH shadow (0.97) STILL ignites EXPLORATORY (shadow no longer starves)")
ce.EXPLORATORY_IGNITION = True
n = set_backlog(10)
print(f"     frontier backlog: {n} open")
e = fresh(ClimateField(shadow_activation=0.97, world_model_strain=0.0,
                       completion_tension=0.0, integration_drive=0.0))
for _ in range(80):
    e._tick_dissonance(60.0)
print(f"     dissonance after accumulation (shadow loud!): value={e.dissonance.value:.3f} explore_value={e.dissonance.explore_value:.3f}")
check("a ruminating (loud-shadow) mind with a backlog reaches threshold", e.dissonance.explore_value >= 1.0)
asyncio.run(e._ignite())
rec = last_log()
print(f"     ignition: trigger={rec['trigger']} contrib={rec['contrib']}")
check("classified EXPLORATORY", rec and rec["trigger"] == "exploratory")

# B — strain dominates -> defensive ----------------------------------------------------
print("\n[B] high strain + backlog -> DEFENSIVE (strain outweighs explore)")
set_backlog(10)
e = fresh(ClimateField(shadow_activation=1.0, world_model_strain=1.0,
                       completion_tension=0.5, integration_drive=0.0))
for _ in range(30):
    e._tick_dissonance(60.0)
asyncio.run(e._ignite())
rec = last_log()
print(f"     trigger={rec['trigger']} contrib={rec['contrib']}")
check("classified DEFENSIVE", rec["trigger"] == "defensive")

# C — empty backlog -> no exploratory ignition (don't reach into a void) ----------------
print("\n[C] EMPTY backlog -> a quiet mind does NOT ignite (nothing to reach for)")
set_backlog(0)
e = fresh(ClimateField(shadow_activation=0.0, world_model_strain=0.0,
                       completion_tension=0.0, integration_drive=0.0))
for _ in range(80):
    e._tick_dissonance(60.0)
print(f"     dissonance with empty backlog: {e.dissonance.value:.3f}")
check("empty backlog -> no exploratory accumulation", e.dissonance.value < 1.0)

# D — kill switch ----------------------------------------------------------------------
print("\n[D] kill switch disables the exploratory term")
ce.EXPLORATORY_IGNITION = False
set_backlog(10)
e = fresh(ClimateField(shadow_activation=0.0))
for _ in range(80):
    e._tick_dissonance(60.0)
print(f"     dissonance with kill switch OFF: {e.dissonance.value:.3f}")
check("kill switch off -> no exploratory ignition even with a backlog", e.dissonance.value < 1.0)
ce.EXPLORATORY_IGNITION = True

iglog.unlink(missing_ok=True)
_shadow_tmp.unlink(missing_ok=True)
for _p in _light_tmps:
    _p.unlink(missing_ok=True)
print(f"\n{'='*62}\n{'ALL PASS — a ruminating mind can now reach out' if ok_all else 'FAILURES ABOVE'}\n{'='*62}")
sys.exit(0 if ok_all else 1)
