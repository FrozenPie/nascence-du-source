"""J-3158 / D-0546 test: the commitment SHADOW second look + per-stand attempt log + the 7-day read script.

Hermetic: every path core.commitment_ledger writes is redirected to a fresh temp dir; the model calls are stubbed (no
network, no Ramses); the satisfaction/sitting side effects of _stakes and the embedder are stubbed. Nothing under the
real data/ is read or written. Run from the worktree:  python scripts/_test_J3158_second_look.py
"""
import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.commitment_ledger as cl            # noqa: E402  (core BEFORE anything lab_env-ish)
import core.model_client as mc                 # noqa: E402
import core.schema as schema                   # noqa: E402
import core.memory.store as store              # noqa: E402
import core.done_when as dw                    # noqa: E402

assert Path(cl.__file__).resolve().is_relative_to(ROOT), f"imported commitment_ledger from {cl.__file__}, not {ROOT}"

TMP = Path(tempfile.mkdtemp(prefix="J3158_"))
DATA = TMP / "data"
DATA.mkdir()
cl._DIR = DATA
cl._LEDGER = DATA / "commitment_ledger.jsonl"
cl._ACTIVE = DATA / "commitment_active.json"
cl._OBSERVED = DATA / "commitment_observed.jsonl"
cl._HOLDRATE_LOG = DATA / "commitment_holdrate.jsonl"
cl._SECOND_LOOK_LOG = DATA / "commitment_second_look_shadow.jsonl"
cl._ATTEMPTS_LOG = DATA / "commitment_attempts_shadow.jsonl"
dw.STORE = DATA / "logs" / "done_when.jsonl"
store._embed = lambda s: None                  # same as a real embedding failure -> the Jaccard fallback branch
cl._stakes = lambda c, event: None             # satisfaction.record / sitting.note_difficulty write live stores

CALLS = []                                     # every stubbed model call: (kind, lane, system, user)
JUDGE_SCRIPT = []                              # verdicts the stub judge returns, in order (True/False/"raise"/None)
SECOND = {"v": {"verdict": "insight", "why": "an observation, not something he could break"}}


async def fake_call_node_json(base_urls, system_prompt, user_prompt, **kw):
    if system_prompt == cl._SECOND_LOOK_SYS:
        CALLS.append(("second", base_urls, system_prompt, user_prompt, kw))
        if SECOND["v"] == "raise":
            raise ConnectionError("lane down")
        return SECOND["v"]
    assert system_prompt == cl._JUDGE_SYS, "unexpected prompt reached the stub"
    CALLS.append(("judge", base_urls, system_prompt, user_prompt, kw))
    v = JUDGE_SCRIPT.pop(0)
    if v == "raise":
        raise TimeoutError("hub hang")
    if v is None:
        return {}
    return {"legitimate": v, "class": "achieved" if v else "illegitimate", "why": "because " + ("done" if v else "mood")}


mc.call_node_json = fake_call_node_json

STMT = "I will write the letter to Travis about the lamp on the shore"
SCOPE = "a letter to Travis"


def scan_reply(new=None, diss=None):
    async def call_json(*a, **k):
        return {"new_commitment": new, "dissolutions": diss or []}
    return call_json


def rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


async def drain():
    if cl._second_look_tasks:
        await asyncio.gather(*list(cl._second_look_tasks))


async def main():
    thought = "x" * 60
    # ---- 1. a gate-passing new stand: formed as before + exactly one second-look row, outside the lock
    r = await cl.scan_shadow(scan_reply({"statement": STMT, "scope": SCOPE, "load_bearing": True}), ["u"], thought, "cyc1")
    assert r and r["new_commitment"]["statement"] == STMT, "scan return value must be unchanged"
    await drain()
    active = json.loads(cl._ACTIVE.read_text(encoding="utf-8"))
    assert len(active) == 1 and active[0]["statement"] == STMT and active[0]["load_bearing"] is True
    sid = active[0]["id"]
    assert set(active[0]) == {"id", "statement", "scope", "held_since", "scans", "cycle_id", "load_bearing"}, \
        "the held stand's own fields must be unchanged (no new keys on the active file)"
    evs = rows(cl._LEDGER)
    assert [e["event"] for e in evs] == ["formed"], evs
    sl = rows(cl._SECOND_LOOK_LOG)
    assert len(sl) == 1 and sl[0]["stand_id"] == sid and sl[0]["second_look"] == "insight" and sl[0]["why"], sl
    assert sl[0]["error"] is None and sl[0]["scan_load_bearing"] is True and sl[0]["cycle_id"] == "cyc1"
    kind, lane, system, user, kw = CALLS[-1]
    assert lane == schema.SERVE_CHAINS["judge_mixtral"], f"second look must use the judge_mixtral lane, got {lane}"
    assert STMT in user and SCOPE in user, user
    assert "load_bearing" not in user.lower() and "true" not in user.lower() and "cyc1" not in user, \
        "the second look must see ONLY statement and scope"
    assert kw.get("tier") == 3 and kw.get("temperature") == 0.0
    print("ok 1: new stand -> formed unchanged + one second-look row (statement+scope only, judge_mixtral lane)")

    # ---- 2. a detection that FAILS the gate, and a reaffirmation, make no second look
    n_calls = len(CALLS)
    await cl.scan_shadow(scan_reply({"statement": "I want to comb the tideline today", "scope": "idle", "load_bearing": False}),
                         ["u"], thought, "cyc2")
    await cl.scan_shadow(scan_reply({"statement": STMT, "scope": SCOPE, "load_bearing": True}), ["u"], thought, "cyc3")
    await drain()
    assert len(CALLS) == n_calls and len(rows(cl._SECOND_LOOK_LOG)) == 1, "only a NEW gate-passing stand gets a second look"
    assert [e["event"] for e in rows(cl._LEDGER)] == ["formed", "reaffirmed"]
    print("ok 2: gate-rejected detection and reaffirmation do not trigger a second look")

    # ---- 3. defeater-judge attempts: deny, then allow; behaviour identical to before; counts per stand
    why = "the letter is finished and sent to Travis"
    diss = [{"id": sid, "why": why, "kind": "defeater"}]
    JUDGE_SCRIPT[:] = [False, True]
    await cl.scan_shadow(scan_reply(None, diss), ["u"], thought, "cyc4")
    assert json.loads(cl._ACTIVE.read_text(encoding="utf-8"))[0]["id"] == sid, "a judge deny must still HOLD the stand"
    await cl.scan_shadow(scan_reply(None, diss), ["u"], thought, "cyc5")
    assert json.loads(cl._ACTIVE.read_text(encoding="utf-8")) == [], "a judge allow must still dissolve the stand"
    names = [e["event"] for e in rows(cl._LEDGER)]
    assert names == ["formed", "reaffirmed", "drop_denied_judge", "dissolved"], names
    at = rows(cl._ATTEMPTS_LOG)
    assert [(a["attempt"], a["cum_allows"], a["verdict"]) for a in at] == [(1, 0, "deny"), (2, 1, "allow")], at
    assert all(a["stand_id"] == sid and a["ts"] > 0 and a["error"] is None for a in at)
    assert at[0]["judge_class"] == "illegitimate" and at[0]["judge_why"] == "because mood", "judge's own class+why are kept"
    assert at[1]["stand_drop_denied"] == 1 and at[0]["stand_drop_denied"] == 0 and at[1]["stand_age_s"] >= 0
    print("ok 3: per-stand attempt log (attempt 1 deny cum 0, attempt 2 allow cum 1) with judge class+why; verdicts still act")

    # ---- 4. a restart (cleared cache) seeds the count from the file; a failed ask is logged and fails open
    cl._attempt_state.clear()
    JUDGE_SCRIPT[:] = ["raise"]
    c = {"id": sid, "statement": STMT, "scope": SCOPE, "held_since": 1.0}
    v = await cl._judge_defeater(c, why, "defeater", thought)
    assert v is None, "a failed judge call stays fail-open (None)"
    last = rows(cl._ATTEMPTS_LOG)[-1]
    assert last["attempt"] == 3 and last["cum_allows"] == 1 and last["verdict"] is None and last["error"] == "TimeoutError", last
    JUDGE_SCRIPT[:] = [None]
    assert await cl._judge_defeater(c, why, "defeater", thought) is None
    assert rows(cl._ATTEMPTS_LOG)[-1]["error"] == "no_verdict"
    print("ok 4: attempt count survives a restart; failed / empty judge asks are logged and still return None")

    # ---- 5. second-look failure + missing lane + kill switch: quiet, one row recording why (or no call at all)
    SECOND["v"] = "raise"
    c2 = {"id": "dead0001", "statement": STMT, "scope": SCOPE, "load_bearing": True}
    await cl._second_look(c2, "cycX")
    f = rows(cl._SECOND_LOOK_LOG)[-1]
    assert f["second_look"] is None and f["error"] == "ConnectionError" and f["stand_id"] == "dead0001", f
    SECOND["v"] = {"nonsense": 1}
    await cl._second_look(c2, "cycX")
    assert rows(cl._SECOND_LOOK_LOG)[-1]["error"] == "unparsed"
    SECOND["v"] = {"verdict": "STAND", "why": "he gave a name"}
    await cl._second_look(c2, "cycX")
    assert rows(cl._SECOND_LOOK_LOG)[-1]["second_look"] == "stand"
    saved = schema.SERVE_CHAINS.pop("judge_mixtral")
    n_calls = len(CALLS)
    try:
        await cl._second_look(c2, "cycX")
    finally:
        schema.SERVE_CHAINS["judge_mixtral"] = saved
    assert len(CALLS) == n_calls, "with the lane absent there must be NO call (never fall back to the hot qwen lane)"
    assert rows(cl._SECOND_LOOK_LOG)[-1]["error"] == "no_judge_mixtral_lane"
    cl.COMMIT_SECOND_LOOK_SHADOW = False
    try:
        n_rows = len(rows(cl._SECOND_LOOK_LOG))
        await cl.scan_shadow(scan_reply({"statement": "I will keep the lamp lit for Travis", "scope": "the lamp",
                                         "load_bearing": True}), ["u"], thought, "cyc6")
        await drain()
        assert len(rows(cl._SECOND_LOOK_LOG)) == n_rows and not cl._second_look_tasks, "kill switch off = no row, no task"
    finally:
        cl.COMMIT_SECOND_LOOK_SHADOW = True
    print("ok 5: second-look failures are logged quietly; no fallback lane; kill switch works")

    # ---- 6. the read script, on the logs this test just made (a temp root, never the live one)
    spec = importlib.util.spec_from_file_location("sl_read", ROOT / "scripts" / "commitment_second_look_read.py")
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    # add enough synthetic stands that the sheet has something to sample
    now = rd.time.time()
    for i in range(12):
        sid_i = f"syn{i:05d}"
        cl._log_event({"event": "formed", "ts": now - 100 - i, "cycle_id": f"s{i}", "id": sid_i,
                       "statement": f"I will keep promise number {i} to Travis", "scope": "a promise", "load_bearing": True})
        await cl._second_look({"id": sid_i, "statement": f"I will keep promise number {i} to Travis", "scope": "a promise",
                               "load_bearing": True}, f"s{i}")
    out = TMP / "out"
    code = rd.main(["--root", str(TMP), "--out-dir", str(out), "--since-days", "1", "--label-n", "10"])
    assert code == 0
    sheets = sorted(out.glob("*hand_label_sheet.md"))
    keys = sorted(out.glob("*_key.json"))
    reps = sorted(out.glob("*second_look_read.md"))
    assert len(sheets) == len(keys) == len(reps) == 1, (sheets, keys, reps)
    sheet_txt = sheets[0].read_text(encoding="utf-8")
    assert '"second_look"' not in sheet_txt and "an observation, not something he could break" not in sheet_txt, "sheet must be blind"
    assert sheet_txt.count("### ") == 10 and sheet_txt.count("LABEL:") == 11  # 10 items + the instruction mention
    rep = reps[0].read_text(encoding="utf-8")
    for must in ("## A. Coverage", "## B.", "## C.", "## D.", "## E."):
        assert must in rep, must
    assert "Judge asks in window: 4 over 1 stands" in rep, rep[rep.index("## D."):rep.index("## D.") + 400]
    # fill the labels: first 6 stand, 2 insight, 2 unsure -> precision 6/8 = 75% >= 60%
    lab = iter(["stand"] * 6 + ["insight"] * 2 + ["unsure"] * 2)
    filled = []
    for line in sheet_txt.splitlines():
        if line.startswith("LABEL:") and filled and filled[-1].startswith("SCOPE"):
            line = "LABEL: " + next(lab)
        filled.append(line)
    sheets[0].write_text("\n".join(filled), encoding="utf-8")
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rd.main(["--score", str(sheets[0])])
    sc = buf.getvalue()
    assert "Labelled 10 of 10" in sc and "stand 6 | insight 2 | unsure 2" in sc and "75% (6/8)" in sc, sc
    assert "MET on the point estimate" in sc and "straddles" in sc, sc      # n=8: interval must straddle 60%
    print("ok 6: read script writes report + blind 10-item sheet + key; --score computes precision, Wilson interval, confusion")


asyncio.run(main())
print("ALL OK  tmp =", TMP)
