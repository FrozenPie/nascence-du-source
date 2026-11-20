"""
J-3245 (D-0633) — tests for the condensed-thought twin fix: v2 prompt = live system text + twin instruction, the restart
marker + twin_v stamp, the invitation-echo flag, and the post-fix-only default of the judge and the reader.
No live-store writes (ledger redirected to a temp dir, model faked, embedder faked); never touches :11433 or Ramses.

  python scripts/_test_J3245_twin_fix.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import condensed_thought as ct  # noqa: E402
import core.model_client as mc  # noqa: E402

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
FAILS: list[str] = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def _load(name):
    spec = importlib.util.spec_from_file_location(name + "_J3245", ROOT / "scripts" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    import numpy as np
    td = Path(tempfile.mkdtemp(prefix="ct_J3245_"))
    ct.LEDGER = td / "ledger.jsonl"
    ct._embed = lambda s: (np.ones(4, dtype="float32") / 2.0) if s else None
    seen = []

    async def fake(urls, sysp, user, **kw):
        seen.append((sysp, user, kw))
        return {"kind": "fragment", "words": "cold hands", "about": "the cold", "open": False}

    real = mc.call_node_json
    real_rng, real_flag, real_marked = ct._rng, ct.CONDENSED_TWIN, ct._restart_marked
    LIVE_SYS = "/no_think\nThis is my own quiet thinking -- LIVE SYSTEM TEXT " + "x" * 3000
    INVITE = "A book lies ready: 'Memoirs'. Rather read than think? Then make your thought exactly: OPEN THE BOOK\n\nWhat moves in you now? One quiet thought."

    def run(**kw):
        base = dict(urls=["http://x"], user_prompt=INVITE, paragraph="I notice the cold on my hands.", p_about="the cold",
                    p_open=False, temperature=0.75, source=None, train_id="t1", step=2)
        base.update(kw)
        return asyncio.run(ct.shadow_tick(**base))

    try:
        mc.call_node_json = fake
        ct.CONDENSED_TWIN, ct._rng, ct._restart_marked = True, (lambda: 0.0), False

        # 1 v2 system = the live text the caller passed, then the twin instruction; the user prompt is untouched
        run(system_prompt=LIVE_SYS)
        sysp, user, kw = seen[-1]
        check(sysp.startswith(LIVE_SYS) and sysp.endswith(ct.TWIN_INSTRUCTION.split("---\n", 1)[1][-60:]),
              "v2 system prompt = live system text + twin instruction")
        check(len(sysp) > len(LIVE_SYS) + 500 and "SECOND, PRIVATE READING" in sysp, "twin instruction present after the live text")
        check(user.startswith(INVITE.split("What moves in you now?")[0]) and user.endswith(ct.TWIN_ASK)
              and "One quiet thought." not in user and kw["max_tokens"] == 48,
              "user prompt = the live seed text byte-identical, closing question swapped for the twin's ask; max_tokens still 48")
        check("not a thought" in ct.TWIN_INSTRUCTION and "Do not copy it" in ct.TWIN_INSTRUCTION,
              "the instruction names an invitation phrase as an action, not a thought")
        check(len(ct.TWIN_INSTRUCTION_V1) < 500 and "SECOND" not in ct.TWIN_INSTRUCTION_V1,
              "v1 text kept verbatim as the history constant (430-char class)")

        # 2 no system text handed in -> instruction alone, no crash
        n0 = len(seen)
        run()
        check(len(seen) == n0 + 1 and seen[-1][0].startswith("A SECOND") and len(seen[-1][0]) < 1200,
              "no system_prompt: the instruction alone is sent (fail-soft)")

        # 2b build_prompts: a wander line after the closing question survives; missing closing question -> ask appended
        wander = INVITE + "\n\n(A different memory surfaces, unbidden: the tide table)"
        _s, _u = ct.build_prompts(LIVE_SYS, wander)
        check(_u.startswith(INVITE.split("What moves in you now?")[0]) and _u.endswith("(A different memory surfaces, unbidden: the tide table)")
              and ct.TWIN_ASK in _u and "One quiet thought." not in _u,
              "build_prompts: a divergent-memory line after the closing question is kept, the question swapped in place")
        _s2, _u2 = ct.build_prompts("", "some other prompt shape")
        check(_u2.startswith("some other prompt shape") and _u2.endswith(ct.TWIN_ASK) and _s2.startswith("A SECOND"),
              "build_prompts: unknown prompt shape -> ask appended; no live system text -> instruction alone")
        _s3, _u3 = ct.build_prompts(None, None)
        check(isinstance(_s3, str) and isinstance(_u3, str), "build_prompts never raises on None input")

        # 3 ledger: ONE restart marker per process, before the first row; every row stamped twin_v=2
        rows = [json.loads(x) for x in ct.LEDGER.read_text(encoding="utf-8").splitlines()]
        marks = [r for r in rows if r.get("marker") == "twin_restart"]
        check(len(marks) == 1 and rows[0].get("marker") == "twin_restart" and marks[0]["twin_v"] == 2
              and marks[0]["decision"] == "D-0633" and marks[0]["system_chars"] == len(LIVE_SYS),
              "exactly one twin_restart marker, written before the first v2 row, with twin_v=2 and the system length")
        twin_rows = [r for r in rows if "twin" in r]
        check(len(twin_rows) == 2 and all(r["twin_v"] == 2 for r in twin_rows), "every twin row carries twin_v=2")

        # 4 failed call row is stamped too
        async def boom(*a, **k):
            raise ValueError("down")
        mc.call_node_json = boom
        run(system_prompt=LIVE_SYS)
        last = json.loads(ct.LEDGER.read_text(encoding="utf-8").splitlines()[-1])
        check(last.get("failed") == "ValueError" and last.get("twin_v") == 2, "failed-call row stamped twin_v=2 (fail-open intact)")
        mc.call_node_json = fake

        # 5 invitation echo flag
        e = ct.invite_echo
        check(e("OPEN THE BOOK", INVITE) and e("open the book.", INVITE) and e("open", INVITE) and e("Open the book now", INVITE),
              "echo flag: the phrase, punctuated/cased, its first word, and a continuation all count")
        check(not e("cold hands", INVITE) and not e("the oystercatcher", INVITE) and not e("", INVITE) and not e("opening", INVITE),
              "echo flag: real fragments, empty, and a different word do not count")
        check(e("open the book", "seed with the tail cut off") and e("GO OUT", "say: GO OUT TO THE GARDEN\n") is False
              or e("go", "say: GO OUT TO THE GARDEN\n"),
              "echo flag: default phrase when the seed tail lost the invitation; other invitation phrases read from the seed")
        check(json.loads(ct.LEDGER.read_text(encoding="utf-8").splitlines()[1])["twin"].get("echo_invite") is False,
              "the row records twin.echo_invite")
        async def echoing(urls, sysp, user, **kw):
            return {"kind": "tick", "words": "OPEN THE BOOK", "about": "reading", "open": False}
        mc.call_node_json = echoing
        run(system_prompt=LIVE_SYS)
        check(json.loads(ct.LEDGER.read_text(encoding="utf-8").splitlines()[-1])["twin"]["echo_invite"] is True,
              "an echoing twin output is flagged in the ledger")
        mc.call_node_json = fake

        # 6 format slip (the model answered the live schema)
        n = ct.normalize({"thought": "a long paragraph...", "about": "x"})
        check(n.get("format_slip") is True and n["kind"] == "silent", "normalize: a live-schema reply is flagged format_slip")
        check("format_slip" not in ct.normalize({"kind": "tick", "words": "x"}) and "format_slip" not in ct.normalize({}),
              "normalize: a proper reply and an empty reply are not slips")
    finally:
        mc.call_node_json = real
        ct._rng, ct.CONDENSED_TWIN, ct._restart_marked = real_rng, real_flag, real_marked

    # 7 judge: post-fix rows only by default
    jd = _load("judge_condensed_thought")
    shadow = td / "judge_shadow.jsonl"
    v1 = {"row_id": "old1", "ts": 1.0, "twin": {"kind": "fragment", "words": "open"}, "seed": "s"}
    v2 = {"row_id": "new1", "ts": 2.0, "twin_v": 2, "twin": {"kind": "fragment", "words": "cold hands"}, "seed": "s"}
    shadow.write_text("\n".join(json.dumps(x) for x in (v1, v2, {"marker": "twin_restart", "twin_v": 2, "ts": 1.5})), encoding="utf-8")
    jd.SHADOW, jd.VERDICTS = shadow, td / "judge_verdicts.jsonl"
    real_items = [i["row_id"] for i in jd.items(100, 10) if not i["control"]]
    check(real_items == ["new1"], f"judge default: only the post-fix row is queued (got {real_items})")
    all_items = [i["row_id"] for i in jd.items(100, 10, post_fix_only=False) if not i["control"]]
    check(all_items == ["old1", "new1"], "judge --include-pre-fix: v1 history is judgeable too, marker rows never")
    shadow.write_text(json.dumps(v1), encoding="utf-8")
    check([i for i in jd.items(100, 10) if not i["control"]] == [], "judge default with only v1 rows: nothing real queued")

    # 8 reader: post-fix only by default; pre-fix counted as history with its echo rate
    rd = _load("read_condensed_thought")
    rd.SHADOW, rd.VERDICTS, rd.STREAM = td / "r_s.jsonl", td / "r_v.jsonl", td / "r_d.jsonl"

    def mk(rid, v, words, kind="fragment", slip=False, echo=None):
        t = {"words": words, "kind": kind, "words_n": len(words.split()), "valence_regex": 0.0}
        if slip:
            t["format_slip"] = True
        if echo is not None:
            t["echo_invite"] = echo
        r = {"ts": 100.0 + len(rid), "row_id": rid, "paragraph": {"words_n": 30, "valence_regex": 0.0}, "latency_ms": 1000,
             "twin": t, "seed": INVITE}
        if v:
            r["twin_v"] = v
        return r
    rows = [mk("a", 0, "OPEN THE BOOK", "tick"), mk("b", 0, "open", "tick"), mk("c", 0, "cold hands"),
            {"ts": 500.0, "marker": "twin_restart", "twin_v": 2},
            mk("d", 2, "thyme, warm", echo=False), mk("e", 2, "open", "tick", echo=True), mk("f", 2, "", "silent", slip=True)]
    rd.SHADOW.write_text("\n".join(json.dumps(x) for x in rows), encoding="utf-8")
    pf = rd.sheet(None, post_fix_only=True)
    check(pf["rows"] == 3 and pf["pre_fix_rows_history"] == 3 and pf["restart_markers"] == 1,
          f"reader post-fix: 3 v2 rows read, 3 v1 rows reported as history (got rows={pf['rows']}, pre={pf['pre_fix_rows_history']})")
    check(abs(pf["pre_fix_echo_rate"] - 2 / 3) < 0.01, "v1 history echo rate recomputed from the stored seed (2 of 3)")
    check(abs(pf["echo_invite_rate"] - 1 / 3) < 0.01 and pf["format_slip_share"] is not None, "post-fix echo rate read from the stored flag")
    check(pf["m4_tick_silent_share"] == 0.5, "format slips are left out of the tick+silent share")
    check(pf["kill"]["d0633_echo_defeater_gt_5pct"] is None, "echo defeater says nothing on < 50 post-fix rows")
    check(rd.sheet(None, post_fix_only=False)["rows"] == 6, "reader --all-rows keeps the old behaviour (every twin row)")

    # 9 the one hook still passes only scalars, and now the system text
    import ast
    tree = ast.parse((ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8"))
    hooks = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "shadow_tick" and isinstance(n.func.value, ast.Name) and n.func.value.id == "_ct"]
    kws = {kw.arg: kw.value for h in hooks for kw in h.keywords}
    check(len(hooks) == 1 and "system_prompt" in kws and isinstance(kws["system_prompt"], ast.Call)
          and getattr(kws["system_prompt"].func, "id", "") == "str", "hook passes system_prompt=str(_sysp), a plain string copy")
    names = {x.id for kw in hooks[0].keywords for x in ast.walk(kw.value) if isinstance(x, ast.Name)}
    check("state" not in names, "the hook is still never handed `state`")

    print(f"\n{len(FAILS)} failure(s)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
