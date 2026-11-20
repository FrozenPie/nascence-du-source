"""
_test_J3402_urgency_shadow.py -- proving test for J-3402 (D-0682): core/urgency_shadow.py, the observe-only shadow of
the deterministic urgency beside Salience's model urgency, and its three hooks in core/orchestrator.py.

Run from a WORKTREE:  python scripts/_test_J3402_urgency_shadow.py

No live store, no model, no Ramses.  _LOG is pointed at a tempdir file.  Checks:
  A static   the three hooks exist, in the right order relative to the three consumers; each is wrapped in a bare
             try/except; the consumers' own lines are untouched (state.salience.urgency still the only urgency read);
             the module is in core.profile's rebase list; the module makes no model call and imports no node.
  B parity   det_urgency == scripts/lab_salience_ablation_J3164.det_urgency on a battery; bandwidth() == the REAL
             Orchestrator._compute_attention; tension_after() == the REAL SomaticEngine.tick_cycle (telemetry stubbed);
             warp arithmetic checked against the orchestrator's source expression.
  C rows     the three hooks produce ONE complete row per cycle with the documented fields, and no hook mutates the
             live state (salience.urgency unchanged by the shadow).
  D safety   kill switch writes nothing; a cycle that never reaches the somatic tick is flushed partial by the next
             cycle; garbage state never raises; the write fence refuses a non-live process under data/.
  E reader   scripts/urgency_shadow_summary.py runs on the temp log.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core FIRST -- live-store safety rule)
from core import profile  # noqa: E402
from core import urgency_shadow as US  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree under test: {core.__file__}"
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


TMP = Path(tempfile.mkdtemp(prefix="J3402_"))
TMP_LOG = TMP / "training" / "urgency_shadow.jsonl"
US._LOG = TMP_LOG
real_data_log = TREE / "data" / "training" / "urgency_shadow.jsonl"
SRC = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")


def rows() -> list[dict]:
    if not US._LOG.exists():
        return []
    return [json.loads(l) for l in US._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── A static ─────────────────────────────────────────────────────────────────────────────────────────────
print("A static")
i1 = SRC.find("_ush.observe_climate(self.state)")
iw = SRC.find("bumped = min(1.0, self.state.salience.urgency")
i2 = SRC.find("_ush.observe_attention(self.state)")
ica = SRC.find("self._compute_attention()\n")
i3 = SRC.find("_ush.observe_somatic(")
it = SRC.find("self.somatic.tick_cycle(")
check(SRC.count("_ush.observe_climate(") == 1 and SRC.count("_ush.observe_attention(") == 1
      and SRC.count("_ush.observe_somatic(") == 1, "exactly one call per hook in orchestrator.py")
check(0 < i1 < iw, "observe_climate sits BEFORE the climate warp mutates salience.urgency")
check(0 < ica < i2, "observe_attention sits AFTER _compute_attention()")
check(0 < i3 < it, "observe_somatic sits BEFORE somatic.tick_cycle()")
for name, pos in (("climate", i1), ("attention", i2), ("somatic", i3)):
    pre = SRC[max(0, pos - 260):pos]
    post = SRC[pos:pos + 700]
    check("try:" in pre and re.search(r"except Exception:\s*\n\s*pass", post) is not None,
          f"{name} hook is try/except-wrapped")
check("urgency        = self.state.salience.urgency if self.state.salience else 0.0," in SRC
      and "narrowing = 0.5 * aff.arousal + 0.3 * aff.fear + 0.4 * urgency" in SRC
      and "bumped = min(1.0, self.state.salience.urgency\n                         + 0.10 * c.shadow_activation\n"
          "                         + 0.05 * c.world_model_strain)" in SRC,
      "the three consumers still read the model urgency, byte-for-byte")
check(not re.search(r"urgency\s*=\s*_ush", SRC), "no consumer is assigned from the shadow")
check("core.urgency_shadow" in (TREE / "core" / "profile.py").read_text(encoding="utf-8"),
      "module is in core.profile's rebase list")
msrc = (TREE / "core" / "urgency_shadow.py").read_text(encoding="utf-8")
check("call_node" not in msrc and "call_json" not in msrc and "from nodes" not in msrc,
      "no model call, no node import in the shadow module")

# ── B parity ─────────────────────────────────────────────────────────────────────────────────────────────
print("B parity")
spec = importlib.util.spec_from_file_location("lab_j3164", TREE / "scripts" / "lab_salience_ablation_J3164.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
battery = [("human", "hello there", None), ("internal", "what is a river", None),
           ("human", "I need this right now, it is urgent", None), ("internal", "no time to waste on this", None),
           ("human", "ok", "contradiction"), ("human", "do it immediately, you got that wrong", "contradiction"),
           ("timer", "quickly now", None), ("human", "", None), ("human", "Before it's too late", "x")]
check(all(US.det_urgency(*b) == lab.det_urgency(*b) for b in battery),
      f"det_urgency == J-3164 lab rule on {len(battery)} cases")
check(US.URGENCY_NUM == lab.URGENCY_NUM, "URGENCY_NUM table == the lab's")
check(US._TIME_PRESSURE.pattern == lab._TIME_PRESSURE.pattern, "time-pressure regex == the lab's")
check([US.det_urgency("human", "x", None)[0], US.det_urgency("internal", "x", None)[0],
       US.det_urgency("human", "urgent", "c")[0], US.det_urgency("internal", "urgent", None)[0]]
      == ["moderate", "low", "pressing", "high"], "word table: human=moderate internal=low both=pressing time-pressure=high")

from core import orchestrator as ORCH  # noqa: E402
from core import schema as S  # noqa: E402
import core.attention_schema_loop as ASL  # noqa: E402
ASL.observe_schema = lambda s: None          # the real _compute_attention calls this; keep it away from any store


def mk_state(arousal=0.3, fear=0.1, urgency=0.1, input_type="human", raw="hello", climate=None, cycle_id="c1"):
    st = S.CognitiveState(spirit_name="t", axiom="t")
    st.cycle_id = cycle_id
    st.input_type = input_type
    st.raw_input = raw
    st.affect.arousal = arousal
    st.affect.fear = fear
    st.salience = S.SalienceOutput(urgency=urgency, focus=["river"], interrupt=False, reasoning="t")
    st.climate = climate
    return st


ok_bw = True
for ar in (0.0, 0.3, 0.7, 1.0):
    for fe in (0.0, 0.2, 0.9):
        for u in (0.0, 0.15, 0.45, 0.7, 0.9, 1.0):
            st = mk_state(ar, fe, u)
            ORCH.Orchestrator._compute_attention(SimpleNamespace(state=st))
            if st.attention.bandwidth != US.bandwidth(ar, fe, u):
                ok_bw = False
check(ok_bw, "bandwidth() == the REAL Orchestrator._compute_attention over a 72-point grid")

from core import somatic as SOM  # noqa: E402
SOM.read_telemetry = lambda: {"gpu_temp": 0.0, "cpu_percent": 0.0}
SOM._cache_body = lambda s: None
ok_t = True
for prev in (0.0, 0.4, 1.0):
    for ar in (0.0, 0.3, 1.0):
        for u in (0.0, 0.15, 0.9, 1.0):
            eng = SOM.SomaticEngine(SOM.SomaticState())
            eng.state.visceral_tension = prev
            eng.tick_cycle(output_tokens=10, critic_retries=0, urgency=u, arousal=ar, cycle_ms=100.0)
            if eng.state.visceral_tension != US.tension_after(prev, u, ar):
                ok_t = False
check(ok_t, "tension_after() == the REAL SomaticEngine.tick_cycle over a 36-point grid")
check(US.warped(0.9, US.warp_bump(1.0, 1.0)) == 1.0 and abs(US.warp_bump(0.5, 0.2) - 0.06) < 1e-12
      and US.warped(0.2, 0.0) == 0.2, "warp arithmetic: +0.10*shadow +0.05*strain, capped at 1.0")

# ── C rows ───────────────────────────────────────────────────────────────────────────────────────────────
print("C rows")
clim = SimpleNamespace(shadow_activation=0.8, world_model_strain=0.4)
st = mk_state(arousal=0.5, fear=0.2, urgency=0.1, input_type="human", raw="please answer right now", climate=clim)
US.observe_climate(st)
check(st.salience.urgency == 0.1, "observe_climate does not mutate salience.urgency")
bumped = min(1.0, st.salience.urgency + 0.10 * clim.shadow_activation + 0.05 * clim.world_model_strain)
st.salience.urgency = bumped                 # emulate the orchestrator's own warp so later hooks see what it sees
ORCH.Orchestrator._compute_attention(SimpleNamespace(state=st))
US.observe_attention(st)
US.observe_somatic(st, urgency=st.salience.urgency, arousal=st.affect.arousal, prev_tension=0.2)
check(st.salience.urgency == bumped, "later hooks do not mutate salience.urgency either")
R = rows()
check(len(R) == 1 and R[0]["complete"] is True, "one complete row for the cycle")
r = R[0]
check(r["cycle_id"] == "c1" and r["input_type"] == "human", "cycle_id and input_type recorded")
check(r["model"]["urgency_raw"] == 0.1 and r["model"]["word"] == "low", "model urgency recorded PRE-warp, with its word")
check(r["det"]["word"] == "high" and r["det"]["urgency"] == 0.7 and r["det"]["time_pressure"] is True,
      "deterministic word: human + time-pressure phrase => high (0.7)")
check(abs(r["climate"]["bump"] - (0.1 * 0.8 + 0.05 * 0.4)) < 1e-4
      and abs(r["climate"]["model_warped"] - bumped) < 1e-4
      and abs(r["climate"]["det_warped"] - min(1.0, 0.7 + 0.1)) < 1e-4,
      "climate warp result for both arms (model arm equals what the warp actually produced)")
bw = r["bandwidth"]
check(bw["model"] == bw["live_attention_bandwidth"], "model-arm bandwidth equals the live attention bandwidth")
check(bw["det"] == US.bandwidth(0.5, 0.2, 0.8) and bw["delta"] == round(bw["det"] - bw["model"], 2),
      "det-arm bandwidth uses the det urgency + the same climate bump, same affect; delta recorded")
sm = r["somatic"]
check(sm["model_tension_after"] == US.tension_after(0.2, bumped, 0.5)
      and sm["det_tension_after"] == US.tension_after(0.2, 0.8, 0.5)
      and sm["model_term"] == round(0.6 * bumped, 4), "somatic term/target/tension-after for both arms")
check("_bump" not in r and "_det_num" not in r, "private working keys are not written")
check(not real_data_log.exists(), "the real data/training/urgency_shadow.jsonl was not created")

# ── D safety ─────────────────────────────────────────────────────────────────────────────────────────────
print("D safety")
n0 = len(rows())
US.URGENCY_SHADOW_ENABLED = False
s2 = mk_state(cycle_id="c-off")
US.observe_climate(s2)
US.observe_attention(s2)
US.observe_somatic(s2, urgency=0.1, arousal=0.3, prev_tension=0.0)
check(len(rows()) == n0 and not US._PENDING, "kill switch: nothing written, nothing pending")
US.URGENCY_SHADOW_ENABLED = True

s3 = mk_state(cycle_id="c-partial", input_type="internal", raw="a quiet thought")
US.observe_climate(s3)                       # ... this cycle never reaches the somatic tick
s4 = mk_state(cycle_id="c-next", input_type="internal", raw="another thought")
US.observe_climate(s4)                       # the next cycle flushes c-partial
R = rows()
check(len(R) == n0 + 1 and R[-1]["cycle_id"] == "c-partial" and R[-1]["complete"] is False
      and R[-1]["bandwidth"] is None and R[-1]["somatic"] is None,
      "a cycle that never ticked is flushed PARTIAL by the next one")
US.observe_somatic(s4, urgency=0.1, arousal=0.3, prev_tension=0.0)
check(rows()[-1]["cycle_id"] == "c-next" and rows()[-1]["complete"] is True and not US._PENDING,
      "next cycle completes normally")

s5 = mk_state(cycle_id="c-nosal")
s5.salience = None
US.observe_climate(s5)
US.observe_attention(s5)
US.observe_somatic(s5, urgency=0.0, arousal=0.3, prev_tension=0.0)
last = rows()[-1]
check(last["cycle_id"] == "c-nosal" and last["model"]["has_salience"] is False and last["model"]["urgency_raw"] is None
      and last["bandwidth"]["model"] == US.bandwidth(0.3, 0.1, 0.0),
      "no salience output: row still written, model arm reads 0.0 like the consumer")

try:
    for bad in (None, object(), SimpleNamespace()):
        US.observe_climate(bad)
        US.observe_attention(bad)
        US.observe_somatic(bad, urgency=None, arousal=None, prev_tension=None)
    check(True, "garbage state never raises")
except Exception as exc:
    check(False, f"garbage state raised {exc!r}")

US._LOG = real_data_log                      # the fence must refuse a NON-LIVE process writing under data/
try:
    US._write({"x": 1})
    check(False, "write fence did not refuse a non-live write under data/")
except profile.NonLiveWriteError:
    check(True, "write fence refuses a non-live process under data/")
check(not real_data_log.exists(), "...and nothing was created at the real path")
US._LOG = TMP_LOG

# ── E reader ─────────────────────────────────────────────────────────────────────────────────────────────
print("E reader")
p = subprocess.run([sys.executable, str(TREE / "scripts" / "urgency_shadow_summary.py"), "--log", str(TMP_LOG), "--json"],
                   capture_output=True, text=True, encoding="utf-8")
try:
    js = json.loads(p.stdout)
    check(p.returncode == 0 and js["rows"] == len(rows()) and "human" in js["by_type"], "summary runs on the temp log")
    check("det_outside_model_range" in js["by_type"]["human"], "summary computes the defeater comparison")
except Exception as exc:
    check(False, f"summary failed: {exc!r} {p.stderr[-300:]}")
p2 = subprocess.run([sys.executable, str(TREE / "scripts" / "urgency_shadow_summary.py"), "--log", str(TMP / "none.jsonl")],
                    capture_output=True, text=True, encoding="utf-8")
check(p2.returncode == 0 and "0 rows" in p2.stdout, "summary on a missing log prints 0 rows, no crash")

print("\n" + ("ALL PASS" if not _fails else f"{_fails} FAIL"))
sys.exit(1 if _fails else 0)
