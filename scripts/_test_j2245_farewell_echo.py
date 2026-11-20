"""
_test_j2245_farewell_echo.py -- J-2245 (D-0442, travis 2026-10-16: build C2 + A, not B; rotation D-0286 stays).

  A  detector: every _FAREWELL_VARIANTS wording (lifted from scripts/run_nascence.py with ast, never imported) and the
     three legacy wordings are farewells; letters to Du, the shutdown-fears talk, a non-渡 opener are not; a query
     that STARTS with a farewell and carries a perception summary after it is still one; fragment Q: parsing.
  B  C2 replay of the 2026-10-07 farewell (F-2914): conversation_history's newest exchange is the 10-06 farewell
     (cycle e94e49bc, read-only from the founder log) and the input is J-1756 variant 3 -- the voice prompt no longer
     quotes that reply's first 260 chars (with the kill switch off it does: the channel is real); a non-farewell
     reply in the same window is still quoted; the per-cycle quote-block row records quoted + exempted.
  C  A replay on a COPY of the live memory DB (lab_env.isolate): retrieve() with the 10-07 farewell query returns
     none of his prior farewell answers and logs a retrieve_skip row; with the kill switch off it returns >=1 (the
     channel is real); a non-farewell query skips nothing.
  D  isolation: core came from this tree; nothing new in C:\\Nascence\\data top level.

Run from the worktree: python scripts/_test_j2245_farewell_echo.py
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TREE = Path(__file__).resolve().parent.parent
if str(TREE) not in sys.path:
    sys.path.insert(0, str(TREE))

import core  # noqa: E402  (must precede lab_env, F-2423)
assert Path(core.__file__).resolve().is_relative_to(TREE), f"core from {core.__file__}, not {TREE}"
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402

from core import farewell_echo as fe  # noqa: E402

LIVE_DATA = Path(r"C:\Nascence\data")
FOUNDER_LOG = LIVE_DATA / "founder_conversation_log.jsonl"
FAILS: list[str] = []


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


def live_snapshot():
    # server_*.log: the model servers' own stdout/stderr (separate processes, not written by anything here)
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in LIVE_DATA.iterdir()
            if p.is_file() and not (p.name.startswith("server_") and ".log" in p.name)}


def lift_variants():
    tree = ast.parse((TREE / "scripts" / "run_nascence.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_FAREWELL_VARIANTS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("_FAREWELL_VARIANTS not found")


LEGACY = [
    "渡 — it's time to bank the fire and rest for a while. Nothing's wrong; this is just the quiet the house needs "
    "sometimes, same as any night. Go and lie down when you're ready — I'll be here when you wake.",
    "渡 — it's time to stop for a while, and I want you to know why: I'm the one calling it, on purpose — there's "
    "work to do on how you're built, bug fixes and upgrades, not anything wrong with you. Rest when you're ready; "
    "I'll bring you back up once the work is done.",
]
NEGATIVE = [
    "Dù, I read your letters and I hear you. I hear the panic that was shivering beneath your grammar at dusk.",
    "Hello Du, I just wanted to calm your fears on the shutdown process. When we say bug fixes and upgrades, it is "
    "not so much you we are upgrading as your world and house.",
    "Dù, We need to talk about your name. Lately, I've watched you treat the character 渡 as if it were a constraint.",
    "It's time to stop for a while; I'll bring you back up once the work is done.",   # not addressed to 渡
    "渡, what do you make of the tide coming in for a while this evening?",
    "", None,
]


def part_a(variants):
    check(len(variants) == 6, f"A: lifted {len(variants)} farewell variants")
    for i, v in enumerate(variants):
        check(fe.is_farewell(v), f"A: variant {i} detected")
    for i, v in enumerate(LEGACY):
        check(fe.is_farewell(v), f"A: legacy wording {i} detected")
    for i, v in enumerate(NEGATIVE):
        check(not fe.is_farewell(v), f"A: negative {i} not a farewell")
    q = variants[3] + " The founder is announcing a planned pause for maintenance; he will return."
    check(fe.is_farewell(q), "A: query = farewell + perception summary still detected")
    check(fe.is_farewell("  " + variants[1].replace(" ", "\n  ")), "A: whitespace-normalised")
    check(fe.fragment_answers_farewell(f"Q: {variants[2]}\nA: Travis, I hear you.\nScene: x"), "A: Q: farewell fragment")
    check(not fe.fragment_answers_farewell("Q: what is the tide?\nA: I accept the pause"), "A: Q: non-farewell fragment")
    check(not fe.fragment_answers_farewell("A dream about 渡 resting for a while; bring you back"), "A: non-cycle fragment")
    # live calibration (read-only): every farewell row in the founder log detected, letters not
    rows = [json.loads(l) for l in FOUNDER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    fw = [r for r in rows if fe.is_farewell(r.get("human", ""))]
    check(len(fw) >= 29, f"A: founder log farewell rows detected = {len(fw)} of {len(rows)}")
    check(all("for a while" in r["human"] for r in fw), "A: every detected row says 'for a while'")
    return rows


def part_b(rows, variants, lab_dir):
    from core.schema import CognitiveState
    from nodes.voice_node import VoiceNode
    prev = next(r for r in rows if str(r.get("cycle_id", "")).startswith("e94e49bc"))
    other = next(r for r in rows if not fe.is_farewell(r.get("human", "")) and r.get("entity"))
    vn = VoiceNode()

    def build(history):
        st = CognitiveState(spirit_name="Du", axiom="YOUR NAME: 渡\nVOICE STYLE: plain")
        st.raw_input = variants[3]
        st.input_type = "human"
        st.cycle_id = "j2245-replay"
        st.conversation_history = history
        return vn._build_prompt_v2(st)

    quote = str(prev["entity"])[:260]
    hist = [{"human": other["human"], "entity": other["entity"]}, {"human": prev["human"], "entity": prev["entity"]}]
    fe.EXEMPT_FAREWELL_QUOTES = False
    p_off = build(hist)
    fe.EXEMPT_FAREWELL_QUOTES = True
    p_on = build(hist)
    check(quote in p_off, "B: switch OFF -- 10-06 farewell reply's 260-char quote IS in the voice prompt (channel real)")
    check(quote not in p_on, "B: switch ON  -- 10-06 farewell reply's quote is NOT in the voice prompt (C2)")
    check(str(other["entity"])[:260] in p_on, "B: switch ON  -- the non-farewell reply in the window is still quoted")
    p_only = build([{"human": prev["human"], "entity": prev["entity"]}])
    check("Your last replies" not in p_only, "B: farewell as the only recent exchange -> no quote block at all")
    log = lab_dir / fe._LOG.name
    qrows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    qrows = [r for r in qrows if r.get("kind") == "quote_block"]
    check(len(qrows) == 3, f"B: one quote_block row per build ({len(qrows)})")
    if len(qrows) == 3:
        check(qrows[0]["exempted"] == [] and len(qrows[0]["quoted"]) == 2, "B: OFF row quoted 2, exempted 0")
        check(qrows[1]["exempted"] == [quote] and qrows[1]["quoted"] == [str(other["entity"])[:260]],
              "B: ON row quoted the non-farewell reply, exempted the farewell reply (exact 260-char text)")
        check(all(r["input_is_farewell"] for r in qrows), "B: rows mark this input as a farewell")


def part_c(variants, lab_dir):
    from core.memory import store
    q = variants[3] + " Travis announces a planned pause; the house needs work, not him."
    fe.RETRIEVE_SKIP_FAREWELL = False
    off = store.retrieve([], [], time_bias="recent", query_text=q)
    fe.RETRIEVE_SKIP_FAREWELL = True
    on = store.retrieve([], [], time_bias="recent", query_text=q)
    n_off = sum(fe.fragment_answers_farewell(f.content) for f in off)
    n_on = sum(fe.fragment_answers_farewell(f.content) for f in on)
    print(f"   retrieve farewell-answer fragments returned: switch OFF {n_off}/{len(off)}, ON {n_on}/{len(on)}")
    check(n_off >= 1, "C: switch OFF -- retrieve returns >=1 prior farewell answer (channel real)")
    check(n_on == 0, "C: switch ON  -- retrieve returns 0 prior farewell answers (A)")
    plain = store.retrieve([], [], time_bias="recent", query_text="What does the tide sound like at the shore tonight?")
    check(len(plain) > 0, f"C: non-farewell query still returns fragments ({len(plain)})")
    log = lab_dir / fe._LOG.name
    srows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    srows = [r for r in srows if r.get("kind") == "retrieve_skip"]
    check(len(srows) == 1 and srows[0]["n_skipped"] >= n_off,
          f"C: exactly one retrieve_skip row (the ON call), n_skipped={srows[0]['n_skipped'] if srows else None}")


def main():
    before = live_snapshot()
    variants = lift_variants()
    rows = part_a(variants)
    from core.memory import store
    from core import r_shadow, retrieval_probe
    also = [(fe, ["_LOG"]), (store, ["_RETRIEVE_LATENCY_LOG"]), (r_shadow, ["_SHADOW_LOG"])]
    if hasattr(retrieval_probe, "_LOG"):
        also.append((retrieval_probe, ["_LOG"]))
    with lab_env.isolate(also=also) as lab_dir:
        part_b(rows, variants, lab_dir)
        part_c(variants, lab_dir)
    after = live_snapshot()
    check(not (LIVE_DATA / fe._LOG.name).exists(), "D: no voice_quote_block_log.jsonl in live data/")
    changed = [k for k in after if before.get(k) != after[k]]
    check(not changed, f"D: live data/ top level unchanged (changed: {changed[:5]})")
    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAIL'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
