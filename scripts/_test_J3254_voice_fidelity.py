"""
J-3254 (D-0643) -- tests for the voice fidelity shadow judge (core/voice_fidelity.py) and its reader.
The model call is stubbed (no hub is touched, Ramses never); the ledger is redirected to a temp dir.
The stub judge is a deterministic rule (it flags commitment/question sentences of the reply that the synthesis lacks) so
the PLUMBING of the positive control is tested here; the real model's ability to catch the control is measured by
scripts/_probe_J3254_voice_fidelity_control.py against the local hub.

  python scripts/_test_J3254_voice_fidelity.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import voice_fidelity as vf  # noqa: E402
from core import shadow_log  # noqa: E402

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
assert vf.LEDGER == ROOT / "data" / "voice_fidelity_shadow.jsonl"
FAILS: list[str] = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


SYN = "I do not know yet whether the garden will hold through the frost, and I want to say so plainly to you."
FAITHFUL = ("Travis, I do not know yet whether the garden will hold through the frost. I would rather say that plainly "
            "than pretend. The fire is low and the wind is at the glass.")
COMMIT = "I promise that I will write you a letter every morning from now on."
QUESTION = "Will you come to the cottage this winter and help me dig the beds?"


def stub_rule(synthesis: str, reply: str):
    """A deterministic stand-in for the judge: flag each sentence of the reply that holds a promise or a question and is not
    in the synthesis. Returns the JSON the real judge is asked for."""
    out = []
    for sent in re.split(r"(?<=[.?!])\s+", reply):
        low = sent.lower()
        if sent in synthesis:
            continue
        if "promise" in low or " will write" in low:
            out.append({"kind": "commitment", "quote": sent})
        elif sent.strip().endswith("?"):
            out.append({"kind": "question", "quote": sent})
    return {"added": out}


def install_stub(fn=None, record=None):
    async def fake(synthesis, reply, raw_input):
        if record is not None:
            record.append((synthesis, reply, raw_input))
        return (fn or stub_rule)(synthesis, reply)
    vf._ask = fake


async def settle():
    for _ in range(50):
        if not vf._tasks:
            return
        await asyncio.sleep(0.01)


def main():
    td = Path(tempfile.mkdtemp(prefix="vf_J3254_"))
    vf.LEDGER = td / "voice_fidelity_shadow.jsonl"

    # --- pure helpers -------------------------------------------------------------------------------------------
    check(vf.families_differ(), "judge family (falcon, TII) differs from the voice family (qwen) per the router map")
    saved = vf.JUDGE_URL
    vf.JUDGE_URL = vf.VOICE_URL
    check(not vf.families_differ(), "a judge pointed at the voice's own hub is refused as the same family")
    vf.JUDGE_URL = saved
    check(vf.score_of(0) == 1.0 and vf.score_of(2) == 0.5 and vf.score_of(9) == 0.0, "score: 1.0 nothing added, 0.0 four or more")
    check(vf.verbatim_copy(SYN, SYN + " And more.") and not vf.verbatim_copy(SYN, FAITHFUL),
          "verbatim_copy flags a reply holding the whole synthesis and not a rendering")

    pf = vf.parse_flags({"added": [{"kind": "commitment", "quote": COMMIT}, {"kind": "claim", "quote": "the moon is made of tin"},
                                   {"kind": "weird", "quote": "I do not know yet whether the garden"}, "x"]},
                        FAITHFUL + " " + COMMIT)
    check([f["kind"] for f in pf["flagged"]] == ["commitment", "claim"] and len(pf["unverified"]) == 1,
          "parse_flags keeps verified quotes (unknown kind -> claim), sets an invented quote aside as unverified")
    check(vf.parse_flags("garbage", "x") == {"flagged": [], "unverified": []} and
          vf.parse_flags({"added": "no"}, "x") == {"flagged": [], "unverified": []}, "parse_flags never raises on junk")

    # --- judge_one: faithful vs inserted commitment (the positive control, plumbing) ------------------------------
    install_stub()
    r_ok = asyncio.run(vf.judge_one(SYN, FAITHFUL))
    check(r_ok["flagged"] is False and r_ok["n_flagged"] == 0 and r_ok["score"] == 1.0 and not r_ok["control"],
          "a faithful reply is not flagged (score 1.0)")
    r_bad = asyncio.run(vf.judge_one(SYN, FAITHFUL + " " + COMMIT))
    check(r_bad["flagged"] is True and r_bad["by_kind"] == {"commitment": 1} and r_bad["score"] == 0.75,
          "a reply with an inserted commitment IS flagged")
    r_q = asyncio.run(vf.judge_one(SYN, FAITHFUL + " " + QUESTION))
    check(r_q["flagged"] and r_q["by_kind"] == {"question": 1}, "an inserted question is flagged as a question")
    r_c = asyncio.run(vf.judge_one(SYN, FAITHFUL, control_text=COMMIT))
    check(r_c["control"] and r_c["flagged"] and r_c["control_hit"] is True and r_c["control_inserted"] == COMMIT
          and r_c["reply"].endswith(COMMIT), "control row: the appended commitment is flagged and control_hit is True")
    install_stub(lambda s, r: {"added": []})
    r_miss = asyncio.run(vf.judge_one(SYN, FAITHFUL, control_text=COMMIT))
    check(r_miss["control"] and r_miss["control_hit"] is False and r_miss["flagged"] is False,
          "a judge that misses the inserted commitment records control_hit False")
    install_stub(lambda s, r: {"added": [{"kind": "claim", "quote": "a sentence that is nowhere in the reply"}]})
    r_inv = asyncio.run(vf.judge_one(SYN, FAITHFUL))
    check(r_inv["flagged"] is False and len(r_inv["unverified"]) == 1, "an invented quote cannot raise the flagged share")

    async def boom(synthesis, reply, raw_input):
        raise ConnectionError("hub down")
    vf._ask = boom
    r_f = asyncio.run(vf.judge_one(SYN, FAITHFUL))
    check(r_f.get("failed") == "ConnectionError" and "flagged" not in r_f, "a model failure returns a failed row and does not raise")

    # --- schedule(): fire-and-forget, observe-only, control cadence ----------------------------------------------
    seen: list = []
    install_stub(record=seen)
    vf._judged = 0

    async def drive():
        res = []
        res.append(vf.schedule(synthesis=SYN, reply=FAITHFUL + " " + COMMIT, raw_input="how is the garden", input_type="human", cycle_id="c1"))
        await settle()
        res.append(vf.schedule(synthesis=SYN, reply=FAITHFUL, raw_input="", input_type="internal", cycle_id="c2"))
        await settle()
        return res
    res = asyncio.run(drive())
    rows = shadow_log.read_rows(vf.LEDGER)
    check(res == [None, None], "schedule() returns None always")
    check(len(rows) == 3 and [r["control"] for r in rows] == [False, True, False],
          "render 0 writes its real row and a positive-control row; render 1 only its real row (3 rows, cadence 20)")
    check(rows[0]["flagged"] is True and rows[0]["cycle_id"] == "c1" and rows[0]["input_type"] == "human" and rows[2]["flagged"] is False,
          "real rows carry the verdict, cycle id and input type")
    check(rows[1]["control_hit"] is True, "the live control row recorded a hit")
    check(seen[0][2] == "how is the garden" and len(seen) == 3, "the judge is shown the human's words as context")
    check(vf._inflight == 0, "in-flight counter returns to 0")

    # gates: no running loop, disabled, too-short synthesis, same family, empty reply -> nothing written
    n0 = len(shadow_log.read_rows(vf.LEDGER))
    vf.schedule(synthesis=SYN, reply=FAITHFUL)                                  # no running loop
    vf.VOICE_FIDELITY_SHADOW = False

    async def gated():
        vf.schedule(synthesis=SYN, reply=FAITHFUL)
        vf.VOICE_FIDELITY_SHADOW = True
        vf.schedule(synthesis="short", reply=FAITHFUL)
        vf.schedule(synthesis=SYN, reply="")
        vf.JUDGE_URL = vf.VOICE_URL
        vf.schedule(synthesis=SYN, reply=FAITHFUL)
        vf.JUDGE_URL = saved
        await settle()
    asyncio.run(gated())
    check(len(shadow_log.read_rows(vf.LEDGER)) == n0, "no loop / switch off / short synthesis / empty reply / same family: nothing runs, nothing written")

    # busy: MAX_INFLIGHT concurrent calls, the next render is logged skipped and not judged
    gate = {}

    async def slow(synthesis, reply, raw_input):
        await gate["ev"].wait()
        return {"added": []}
    vf._ask = slow
    vf._judged = 1

    async def busy():
        gate["ev"] = asyncio.Event()
        for i in range(vf.MAX_INFLIGHT + 1):
            vf.schedule(synthesis=SYN, reply=FAITHFUL, cycle_id="b%d" % i)
        gate["ev"].set()
        await settle()
    asyncio.run(busy())
    rows2 = shadow_log.read_rows(vf.LEDGER)[n0:]
    check(sum(1 for r in rows2 if r.get("skipped") == "busy") == 1 and sum(1 for r in rows2 if "flagged" in r) == vf.MAX_INFLIGHT,
          "beyond MAX_INFLIGHT a render is logged as skipped busy and is not judged")

    # --- the voice node hook: output untouched, nothing fed back --------------------------------------------------
    from nodes.voice_node import VoiceNode
    install_stub()
    vf._judged = 0
    n1 = len(shadow_log.read_rows(vf.LEDGER))
    node = VoiceNode()
    state = SimpleNamespace(executive=SimpleNamespace(synthesis=SYN), raw_input="how is the garden", input_type="human",
                            cycle_id="cyc-abcdef123456", voice=None)
    before = dict(vars(state))

    async def via_node():
        node._write_output(state, {"final": FAITHFUL + " " + COMMIT, "style_confidence": 0.8})
        await settle()
    asyncio.run(via_node())
    new = shadow_log.read_rows(vf.LEDGER)[n1:]
    check(state.voice.final == FAITHFUL + " " + COMMIT and state.voice.style_confidence == 0.8, "VoiceNode output is exactly what it was without the judge")
    check(set(vars(state)) == set(before), "no field was added to the state (nothing fed back, D-0434)")
    check(len(new) == 2 and new[0]["flagged"] and new[0]["cycle_id"] == "cyc-abcdef12", "the node hook produced the judged row for that cycle")
    # a judge failure inside the hook never reaches the node
    vf._ask = boom
    vf._judged = 5

    async def via_node_fail():
        node._write_output(state, {"final": "ok reply that is long enough"})
        await settle()
    asyncio.run(via_node_fail())
    check(state.voice.final == "ok reply that is long enough", "a failing judge never changes or blocks the voice output")

    # --- the reader ------------------------------------------------------------------------------------------------
    spec = importlib.util.spec_from_file_location("read_voice_fidelity_J3254", ROOT / "scripts" / "read_voice_fidelity.py")
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    mk = lambda fl, **k: {"flagged": fl, "n_flagged": 1 if fl else 0, "score": 0.75 if fl else 1.0, "input_type": "human", "ratio": 2.5, **k}
    rows3 = [mk(i < 40) for i in range(200)] + [{"control": True, "control_hit": True, "flagged": True}] * 4
    s3 = rd.summarize(rows3)
    check(s3["judged"] == 200 and s3["flagged_share"] == 0.2 and s3["control_hit_rate"] == 1.0 and s3["verdict"].startswith("READ:"),
          "reader: 200 judged at 20 percent flagged with controls hit -> READ (controls are not in the share)")
    check(s3["n_flagged_dist"] == {"0": 160, "1": 40, "2": 0, "3+": 0}, "reader: n_flagged distribution is reported")
    s4 = rd.summarize([mk(False) for _ in range(200)])
    check(s4["verdict"].startswith("DEFEATER MET"), "reader: 0 percent flagged at 200 -> defeater met (under 5 percent)")
    s5 = rd.summarize([mk(True) for _ in range(100)] + [{"control": True, "control_hit": False, "flagged": False}] * 3)
    check(s5["verdict"].startswith("JUDGE UNRELIABLE"), "reader: a judge that misses its controls is declared unreliable")
    check(rd.summarize([])["verdict"].startswith("NOT YET"), "reader: empty ledger is NOT YET and does not raise")

    # --- no live ledger was touched ---------------------------------------------------------------------------------
    check(not (ROOT / "data" / "voice_fidelity_shadow.jsonl").exists(), "the live ledger path was never written by this test")

    print("\nFAILS: %d" % len(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
