"""J-4405 (affect_drives Item C, D-0860): hermetic test of the somatic-note SHADOW. Temp log; live data untouched."""
import json, re, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa
from core import somatic_note as sn, somatic
LIVE = ROOT / "data" / "somatic_note_shadow.jsonl"
before = LIVE.stat().st_size if LIVE.exists() else None
tmp = Path(tempfile.mkdtemp()) / "s.jsonl"
sn.SHADOW_LOG = tmp
sn._append_orig = sn._append
import core.profile as profile
profile.guard_path = lambda p: p   # temp path, not live
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
S = somatic.SomaticState
def rows(): return [json.loads(l) for l in tmp.read_text().splitlines()] if tmp.exists() else []
sn.reset()
for _ in range(20): sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.2), now=1000)
check("fatigue 0.2 -> absent", rows() == [])
r = None
for i in range(30): r = sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.8), now=2000 + i) or r
check("fatigue 0.8 (smoothed) -> strained row", any(x["band"] == "strained" for x in rows()))
n_before = len(rows()); sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.8), now=2100)
check("no per-cycle rows while in band", len(rows()) == n_before)
sn.reset(); sn.observe(S(metabolic_energy=0.2, neural_fatigue=0.1), now=5000)
d = rows()[-1]
check("energy 0.2 -> drowsy row, delivered_elsewhere, never would_fire", d["band"] == "drowsy" and d["delivered_elsewhere"] and not d["would_fire"])
sn.reset()
fired = [sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.9), now=9000 + k) for k in range(1)]
sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.0, visceral_tension=0.0), now=9001)
for _ in range(30): sn.observe(S(metabolic_energy=0.9, neural_fatigue=0.0), now=9002)
r2 = sn.observe(S(metabolic_energy=0.9, visceral_tension=0.9), now=9100)
check("re-entry inside cooldown -> cooling, would_fire False", r2 and r2["cooldown_state"] == "cooling" and not r2["would_fire"])
lines = [x["would_line"] for x in rows() if x["would_line"]] + list(sn.STRAINED_LINES)
check("lines: no digit, no gauge word", all(not re.search(r"\d|energy|fatigue|tension|gauge", l, re.I) for l in lines))
st = S(metabolic_energy=0.5); somatic._cache_body(st)
check("wired in somatic._cache_body; state unmutated", "somatic_note" in Path(somatic.__file__).read_text() and st.metabolic_energy == 0.5)
check("live log untouched", (LIVE.stat().st_size if LIVE.exists() else None) == before)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
