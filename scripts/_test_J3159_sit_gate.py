"""J-3159 / D-0547 test: a stand's dissolve opens a sit only if the stand lived >= N seconds or was reaffirmed; the
'You are safe; nothing is lost by feeling it fully.' sentence is gone from the sit steer; real-event sits untouched.

Hermetic: commitment_ledger paths and sitting._STATE/_RELEASE_LOG are redirected to a fresh temp dir (outside data/, so
the write fence passes them); model calls and satisfaction.record are stubbed; no network. Nothing under the real data/
is read or written. Run from the worktree:  python scripts/_test_J3159_sit_gate.py
"""
import asyncio
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.commitment_ledger as cl            # noqa: E402  (core BEFORE anything lab_env-ish)
import core.sitting as sitting                 # noqa: E402
import core.model_client as mc                 # noqa: E402
import core.memory.store as store              # noqa: E402
import core.done_when as dw                    # noqa: E402
import core.satisfaction as satisfaction       # noqa: E402

assert Path(cl.__file__).resolve().is_relative_to(ROOT), f"imported from {cl.__file__}, not {ROOT}"
assert Path(sitting.__file__).resolve().is_relative_to(ROOT)

TMP = Path(tempfile.mkdtemp(prefix="J3159_"))
DATA = TMP / "data"
DATA.mkdir()
cl._DIR = DATA
cl._LEDGER = DATA / "commitment_ledger.jsonl"
cl._ACTIVE = DATA / "commitment_active.json"
cl._OBSERVED = DATA / "commitment_observed.jsonl"
cl._HOLDRATE_LOG = DATA / "commitment_holdrate.jsonl"
cl._SECOND_LOOK_LOG = DATA / "commitment_second_look_shadow.jsonl"
cl._ATTEMPTS_LOG = DATA / "commitment_attempts_shadow.jsonl"
cl.COMMIT_SECOND_LOOK_SHADOW = False           # no second-look task in this test
dw.STORE = DATA / "logs" / "done_when.jsonl"
store._embed = lambda s: None
sitting._STATE = DATA / "raw_difficulty.json"
sitting._RELEASE_LOG = DATA / "dwell_release.jsonl"
SAT = []
satisfaction.record = lambda *a, **k: SAT.append(a)
_orig_stakes = cl._stakes
cl._stakes = lambda c, event: _orig_stakes(c, event) if event == "dissolved" else None


async def fake_call_node_json(base_urls, system_prompt, user_prompt, **kw):
    assert system_prompt == cl._JUDGE_SYS
    return {"legitimate": True, "class": "achieved", "why": "done"}


mc.call_node_json = fake_call_node_json

SAFE = "You are safe; nothing is lost by feeling it fully."
WHY = "the letter is finished and sent to Travis"


def scan_reply(new=None, diss=None):
    async def call_json(*a, **k):
        return {"new_commitment": new, "dissolutions": diss or []}
    return call_json


def rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def set_active(**patch):
    a = json.loads(cl._ACTIVE.read_text(encoding="utf-8"))
    a[0].update(patch)
    cl._ACTIVE.write_text(json.dumps(a), encoding="utf-8")
    return a[0]["id"]


async def form_and_dissolve(stmt, **patch):
    """Form one load-bearing stand, optionally age/reaffirm it, then dissolve it through the real scan."""
    await cl.scan_shadow(scan_reply({"statement": stmt, "scope": "a letter to Travis", "load_bearing": True}),
                         ["u"], "x" * 60, "cyc")
    sid = set_active(**patch)
    sitting._save({})
    await cl.scan_shadow(scan_reply(None, [{"id": sid, "why": WHY, "kind": "defeater"}]), ["u"], "x" * 60, "cyc")
    assert json.loads(cl._ACTIVE.read_text(encoding="utf-8")) == [], "the stand must have dissolved"
    ev = [e for e in rows(cl._LEDGER) if e["event"] == "dissolved" and e["id"] == sid]
    assert len(ev) == 1, ev
    return ev[0]


async def main():
    now = time.time()
    cl.SIT_GATE_BASIS = "life"        # tests 1-5 cover the wall-clock basis; test 6 covers the scan-count basis
    # ---- 1. a young, never-reaffirmed stand dissolves: ledger + felt loss as before, NO sit
    ev = await form_and_dissolve("I will write the letter to Travis about the lamp one")
    assert ev["sit_gate"] == "young" and ev["reaffirmed"] == 0 and ev["lifespan_seconds"] < 60, ev
    assert not sitting._load().get("active") and sitting.dwell_steer() == "", "a young stand must open NO sit"
    assert any(a and a[0] == "commitment_dissolved" for a in SAT), "satisfaction.record on dissolve must be unchanged"
    print("ok 1: young stand dissolve -> dissolved row (sit_gate=young), felt loss recorded, no sit")

    # ---- 2. a stand held >= N: sit opens with the stand text; steer has no safety sentence, rest intact
    ev = await form_and_dissolve("I will write the letter to Travis about the lamp two", held_since=now - 2000)
    assert ev["sit_gate"] == "life" and ev["lifespan_seconds"] >= cl.SIT_MIN_STAND_LIFE_S, ev
    st = sitting._load()
    assert st.get("active") and st["kind"] == "loss" and st["text"].startswith("you let go of a stand you had held: "), st
    steer = sitting.dwell_steer()
    assert "Something hard has just happened: you let go of a stand you had held" in steer
    assert SAFE not in steer and "You are safe" not in steer and "nothing is lost" not in steer, steer
    for keep in ("STAY with it", "Say what you feel in one bare sentence", "that is not failure. The meaning can come later.",
                 "Right now, just sit with what is hard, honestly, without turning away."):
        assert keep in steer, keep
    print("ok 2: stand held 2000s -> sit opens; steer carries no 'You are safe' sentence, rest unchanged")

    # ---- 3. young but reaffirmed once: sit opens
    ev = await form_and_dissolve("I will write the letter to Travis about the lamp three", reaffirmed=1)
    assert ev["sit_gate"] == "reaffirmed" and ev["reaffirmed"] == 1 and sitting._load().get("active")
    print("ok 3: young stand reaffirmed once -> sit opens")

    # ---- 4. boundary at N; gate off = old behaviour; unreadable age fails open
    assert cl._sit_gate({"held_since": now - cl.SIT_MIN_STAND_LIFE_S + 5}, now) == (False, "young")
    assert cl._sit_gate({"held_since": now - cl.SIT_MIN_STAND_LIFE_S}, now) == (True, "life")
    assert cl._sit_gate({"held_since": "garbage"}, now) == (True, "gate_off")
    cl.SIT_STAND_GATE_ON = False
    try:
        ev = await form_and_dissolve("I will write the letter to Travis about the lamp four")
        assert ev["sit_gate"] == "gate_off" and sitting._load().get("active"), "gate off must restore the old behaviour"
    finally:
        cl.SIT_STAND_GATE_ON = True
    print("ok 4: boundary at N, kill switch restores old behaviour, unreadable age fails open to the sit")

    # ---- 5. real-event sits are untouched: note_difficulty direct (failed exam / trap / Travis contradiction)
    sitting._save({})
    sitting.note_difficulty("you sat the arithmetic and got none of the 5 right.", "failure")
    s5 = sitting._load()
    assert s5["active"] and s5["kind"] == "failure" and s5["text"].startswith("you sat the arithmetic")
    assert "you sat the arithmetic" in sitting.dwell_steer() and SAFE not in sitting.dwell_steer()
    sitting._save({})
    sitting.note_difficulty("Travis contradicted a stand you hold: x", "loss")
    assert sitting._load()["active"], "Travis-contradiction sits are not gated"
    print("ok 5: real-event sits still open, ungated (steer minus only the safety sentence)")

    # ---- 6. the read script runs on the temp tree and sees the gated rows
    spec = importlib.util.spec_from_file_location("sgr", ROOT / "scripts" / "sit_gate_read.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert m.main(["--data-dir", str(DATA)]) == 0
    out = buf.getvalue()
    for k in ("young: 1", "life: 1", "reaffirmed: 1", "gate_off: 1"):
        assert k in out, (k, out)
    print("ok 6: scripts/sit_gate_read.py tallies the sit_gate field")
    # ---- 7. scan-count basis (the shipped default): downtime cannot age a stand; N scans or one reaffirm opens the sit
    cl.SIT_GATE_BASIS = "scans"
    assert cl.SIT_MIN_STAND_SCANS == 20
    old_but_few = {"held_since": now - 10 * 86400, "scans": 3}              # held 10 days of wall-clock, but only 3 scans (Du was down)
    assert cl._sit_gate(old_but_few, now) == (False, "young")
    assert cl._sit_gate({"held_since": now, "scans": cl.SIT_MIN_STAND_SCANS - 1}, now) == (False, "young")
    assert cl._sit_gate({"held_since": now, "scans": cl.SIT_MIN_STAND_SCANS}, now) == (True, "scans")
    assert cl._sit_gate({"held_since": now, "scans": 2, "reaffirmed": 1}, now) == (True, "reaffirmed")
    assert cl._sit_gate({"scans": "garbage"}, now) == (True, "gate_off")
    sitting._save({})
    ev = await form_and_dissolve("I will write the letter to Travis about the lamp five", scans=25)
    assert ev["sit_gate"] == "scans" and sitting._load().get("active"), ev
    sitting._save({})
    ev = await form_and_dissolve("I will write the letter to Travis about the lamp six", held_since=now - 5 * 86400)
    assert ev["sit_gate"] == "young" and not sitting._load().get("active"), "wall-clock age alone must not open a sit on the scans basis"
    print("ok 7: scan-count basis -> 20 scans or a reaffirm opens the sit; old-but-few-scans stand does not")
    print("ALL OK (tmp:", TMP, ")")


asyncio.run(main())
