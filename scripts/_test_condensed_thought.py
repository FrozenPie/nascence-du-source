"""
J-2281 — tests for core/condensed_thought.py (Phase 0 shadow twin) and its one hook in nodes/inner_monologue_node.py.
Asserts the plan's §4.2 / §6 law: the twin's output cannot reach thought / hands / train / pulse / store /
recent_inner_thoughts / moment.record. No live-store writes: the ledger is redirected to a temp file, the model
call is faked, the embedder is faked. Never touches :11433.

  python scripts/_test_condensed_thought.py
"""
from __future__ import annotations

import ast
import asyncio
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import condensed_thought as ct  # noqa: E402
import core.model_client as mc  # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="ct_J2281_")) / "ledger.jsonl"
    ct.LEDGER = tmp
    import numpy as np
    ct._embed = lambda s: (np.ones(4, dtype="float32") / 2.0) if s else None   # unit vector, no model load
    calls = []

    async def fake_ok(urls, sysp, user, **kw):
        calls.append(kw)
        return {"kind": "fragment", "words": "cold hands", "about": "the cold", "open": False}

    async def fake_boom(*a, **kw):
        raise ValueError("hub down")

    real = mc.call_node_json

    def run(**kw):
        base = dict(urls=["http://x"], user_prompt="seed", paragraph="I notice the cold on my hands.",
                    p_about="the cold", p_open=False, temperature=0.75, source=None, train_id="t1", step=2)
        base.update(kw)
        return asyncio.run(ct.shadow_tick(**base))

    try:
        # 1 flag off -> no call, no row
        ct.CONDENSED_TWIN = False
        mc.call_node_json = fake_ok
        check(run() is None and not calls and not tmp.exists(), "flag off: no call, no row, returns None")
        # 2 flag on, sampled -> one call, one row, None returned, call shape honours D-0460 / §4.1
        ct.CONDENSED_TWIN, ct._rng = True, (lambda: 0.0)
        r = run()
        rows = tmp.read_text(encoding="utf-8").splitlines() if tmp.exists() else []
        rows = [x for x in rows if '"marker"' not in x]   # D-0633 (J-3245): the once-per-process twin_restart marker is not a twin row
        check(r is None, "flag on: shadow_tick returns None (nothing for the caller to assign)")
        check(len(calls) == 1 and calls[0]["max_tokens"] == 48 and calls[0]["temperature"] == 0.75,
              "one call, max_tokens=48, same temperature as the paragraph")
        import json
        row = json.loads(rows[0]) if rows else {}
        need = {"ts", "train_id", "step", "tick_source", "paragraph", "twin", "about_cos_prev_twin",
                "about_cos_prev_paragraph", "body_cos_paragraph_vs_twin", "latency_ms", "judge"}
        check(len(rows) == 1 and need <= set(row), "one §4.3-shaped row written")
        check(row.get("twin", {}).get("words_n") == 2 and row.get("twin", {}).get("kind") == "fragment",
              "twin words_n/kind recorded")
        # 3 rate gate
        ct._rng = lambda: 0.99
        n = len(calls)
        run()
        check(len(calls) == n, "rate gate: unsampled tick makes no call (TWIN_RATE=%.2f)" % ct.TWIN_RATE)
        # 4 fail-open
        ct._rng = lambda: 0.0
        mc.call_node_json = fake_boom
        ok = True
        try:
            r = run()
        except Exception:
            ok = False
        last = json.loads(tmp.read_text(encoding="utf-8").splitlines()[-1])
        check(ok and r is None and last.get("failed") == "ValueError", "fail-open: hub error logged as a failed row, no raise")
        # 5 normalize
        check(ct.normalize({"kind": "silent", "words": "x"})["words"] == "", "silent carries no words")
        check(ct.normalize({"kind": "weird", "words": ""})["kind"] == "silent", "unknown kind + no words -> silent")
    finally:
        mc.call_node_json = real
        ct.CONDENSED_TWIN = False

    # 6 defaults as ruled
    import importlib
    fresh = importlib.reload(ct)
    check(fresh.CONDENSED_TWIN is True and fresh.TWIN_RATE == 0.25 and fresh.TWIN_MAX_TOKENS == 48,
          "shipped defaults: CONDENSED_TWIN=True (D-0471, J-2349), TWIN_RATE=0.25, max_tokens=48 (restart-gated)")

    # 6b cost kill (D-0460, plan s6): read_condensed_thought flags an idle-gap-median rise of > 5 s (temp stores only)
    import json as _json
    import importlib.util
    assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
    spec = importlib.util.spec_from_file_location("rct_J2349", ROOT / "scripts" / "read_condensed_thought.py")
    rct = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rct)
    td = Path(tempfile.mkdtemp(prefix="ct_J2349_"))
    rct.SHADOW, rct.VERDICTS, rct.STREAM = td / "s.jsonl", td / "v.jsonl", td / "d.jsonl"
    boot = 10_000_000.0

    def _gaps_rows(gap_before, gap_after):
        ts = [boot - 86400 + i * gap_before for i in range(10)] + [boot + 100 + i * gap_after for i in range(10)]
        rct.STREAM.write_text(chr(10).join(_json.dumps({"ts": t}) for t in ts), encoding="utf-8")

    rct.SHADOW.write_text(_json.dumps({"ts": boot + 1, "row_id": "a", "paragraph": {"words_n": 30, "valence_regex": 0.0}, "latency_ms": 900,
                                       "twin": {"words_n": 2, "kind": "fragment", "words": "x", "valence_regex": 0.0}}), encoding="utf-8")
    _gaps_rows(60, 68)
    check(rct.sheet(boot)["kill"]["cost_kill_gap_gt_5s"] is True, "cost kill: idle-gap median +8 s trips the > 5 s check")
    _gaps_rows(60, 63)
    check(rct.sheet(boot)["kill"]["cost_kill_gap_gt_5s"] is False, "cost kill: idle-gap median +3 s does not trip it")

    # 6c J-2838: reader artifacts - nonzero valence arm, about-length control, echo rows, live hours
    def _row(i, words, about, tv_, pv_, tcos, pcos, ts_):
        return {"ts": ts_, "row_id": "r%d" % i, "paragraph": {"words_n": 30, "valence_regex": pv_}, "latency_ms": 900,
                "about_cos_prev_twin": tcos, "about_cos_prev_paragraph": pcos,
                "twin": {"words_n": len(words.split()), "kind": "fragment", "words": words, "about": about, "valence_regex": tv_}}
    rows6 = [_row(0, "Open", "a b", 0.0, -0.4, 0.1, 0.9, boot + 1),
             _row(1, "open the book", "a b", 0.0, -0.3, 0.1, 0.9, boot + 61),
             _row(2, "quiet dread", "a b c d e f g", 0.5, -0.2, 0.9, 0.9, boot + 121),
             _row(3, "bright", "a b", 0.3, 0.1, 0.2, 0.9, boot + 181),
             _row(4, "slow", "a b", 0.0, -0.5, 0.9, 0.9, boot + 100000)]
    rct.SHADOW.write_text(chr(10).join(_json.dumps(r) for r in rows6), encoding="utf-8")
    _gaps_rows(60, 63)
    s6 = rct.sheet(boot)
    check(s6["echo_rows"] == 2, "echo rows counted (open / open the book, case-insensitive)")
    check(s6["m7_zero_share_twin"] == 0.6 and s6["m7_nonzero_rows"] == 2, "metric 7 prints twin zero-share and non-zero row count")
    check(s6["m7_valence_twin_mean_nonzero"] == 0.4 and s6["m7_valence_para_mean_nonzero"] == -0.05,
          "metric 7 non-zero-only comparison uses rows where twin valence is non-zero")
    check(s6["m5_about_long_rows"] == 1 and s6["m5_transition_twin_about_le5"] == 0.75,
          "metric 5 reported again without rows whose about exceeds 5 words")
    check(s6["m4_twin_words_median_noecho"] == 1 and s6["m2_genuine_rate_noecho"] is None,
          "metrics 2/4 recomputed excluding echo rows")
    check(s6["live_hours"] < 0.2 and s6["live_hours_gate"] == 168 and s6["live_hours_ready"] is False,
          "live hours count only gaps <= 30 min (the 100000 s gap is excluded)")

    # 7 module imports nothing that writes to Du's stores / hands / trains / pulse / moments
    src = (ROOT / "core" / "condensed_thought.py").read_text(encoding="utf-8")
    mods = {(n.module or "") + ":" + ",".join(a.name for a in n.names) for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.ImportFrom)}
    allowed = {"__future__:annotations", "core.narrative_quality:_seg_valence", "core.stream_drive:_is_grounded",
               "core.memory.store:_embed", "core.model_client:call_node_json", "core:shadow_log", "pathlib:Path"}
    check(mods <= allowed, f"module imports only read-only helpers (extra: {sorted(mods - allowed)})")

    # 8 the hook: exactly one reference to condensed_thought in the node, a bare `await` statement whose
    #    result is discarded, passed only scalar expressions (never state/self)
    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    tree = ast.parse(node)
    hooks = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "shadow_tick" and isinstance(n.func.value, ast.Name) and n.func.value.id == "_ct"]
    check(len(hooks) == 1, "exactly one shadow_tick call site in inner_monologue_node.py")
    exprs = [n for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Await)
             and n.value.value in hooks]
    check(len(exprs) == 1, "the hook is a bare await statement (return value discarded, never assigned)")
    names_in_args = {x.id for h in hooks for kw in h.keywords for x in ast.walk(kw.value) if isinstance(x, ast.Name)}
    check("state" not in names_in_args, "the hook is never handed `state` (no CognitiveState write path)")
    check(node.count("condensed_thought as _ct") == 1 and node.count("_ct.") == 1,
          "`_ct` is referenced nowhere else in the node")

    print(f"\n{len(FAILS)} failure(s)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
