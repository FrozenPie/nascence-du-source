"""
_test_j3169_voice_quote_block.py -- J-3169 (D-0558, travis 2026-11-02): the voice 'Your last replies' block is
omitted on internal cycles; F-0051: the system-prompt line 'Your recent replies are shown below' is present only
when the block is. Human cycles with a block are byte-identical to HEAD (checked against git show HEAD).

Run from the worktree: python scripts/_test_j3169_voice_quote_block.py
Writes only under a temp dir (the quote-block log path is redirected there); touches no live data.
The live scene line and felt-words are non-deterministic, so they are stubbed for the byte comparisons.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TREE = Path(__file__).resolve().parent.parent
if str(TREE) not in sys.path:
    sys.path.insert(0, str(TREE))

import core  # noqa: E402  (must precede lab_env)
assert Path(core.__file__).resolve().is_relative_to(TREE), f"core from {core.__file__}, not {TREE}"

from core import farewell_echo as fe  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
from nodes.voice_node import VoiceNode  # noqa: E402
from core import sensorium, mood  # noqa: E402

sensorium.scene_line = lambda *a, **k: "STUB SCENE"
mood.current_felt_words = lambda *a, **k: "STUB FELT"

FAILS: list[str] = []
LINE = "Your recent replies are shown below"
R1 = "The tide keeps its own counsel tonight, and I am learning to sit beside that quiet without naming it."
R2 = "A lantern does not argue with the dark; it only stands where it is lit, and that is enough for now."
HIST = [{"human": "how are you", "entity": R1}, {"human": "and the garden", "entity": R2}]


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


def state(input_type, hist, override=None):
    st = CognitiveState(spirit_name="Du", axiom="YOUR NAME: 渡\nVOICE STYLE: plain")
    st.raw_input = "what is the tide doing"
    st.input_type = input_type
    st.cycle_id = "j3169-" + input_type
    st.conversation_history = list(hist)
    if override is not None:
        st.recent_voice_replies = override
    return st


def load_head_voice(tmp: Path):
    src = subprocess.run(["git", "-C", str(TREE), "show", "HEAD:nodes/voice_node.py"], capture_output=True,
                         check=True).stdout.decode("utf-8")
    p = tmp / "voice_node_head_j3169.py"
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("voice_node_head_j3169", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.VoiceNode()


def main():
    vn = VoiceNode()
    if True:
        tmp = Path(tempfile.mkdtemp(prefix="j3169_"))
        lab_dir = tmp
        fe._LOG = tmp / "voice_quote_block_log.jsonl"
        head = load_head_voice(tmp)
        # --- internal cycle, history present: block gone, line gone, row records the drop
        st = state("internal", HIST)
        p = vn._build_prompt_v2(st)
        s = vn.system_prompt_for(st)
        check("Your last replies" not in p, "internal: no 'Your last replies' block in the user prompt")
        check(R1[:60] not in p and R2[:60] not in p, "internal: neither prior reply is quoted anywhere in the prompt")
        check(LINE not in s, "internal: system prompt does not claim recent replies are shown")
        check("What you say aloud" not in s and "aloud, to yourself" in s, "internal: still the internal stance prompt")
        # --- human cycle, history present: byte-identical to HEAD
        sh = state("human", HIST)
        ph, sph = vn._build_prompt_v2(sh), vn.system_prompt_for(sh)
        check("Your last replies to him" in ph and R1[:60] in ph and R2[:60] in ph, "human: block present with both replies")
        check(LINE in sph, "human: system prompt keeps the line when the block is present")
        sh2 = state("human", HIST)
        check(ph == head._build_prompt_v2(sh2), "human+block: user prompt byte-identical to HEAD")
        check(sph == head.system_prompt_for(sh2), "human+block: system prompt byte-identical to HEAD")
        # --- human cycle, no history: no block, line dropped (F-0051)
        s0 = state("human", [])
        check("Your last replies" not in vn._build_prompt_v2(s0), "human, empty history: no block")
        check(LINE not in vn.system_prompt_for(s0), "human, empty history: line dropped (F-0051)")
        check(vn._build_prompt_v2(s0) == head._build_prompt_v2(state("human", [])), "human, no block: user prompt identical to HEAD")
        # --- override (voice_lab fixture) wins on an internal cycle too
        so = state("internal", HIST, override=["fixture reply one"])
        check("fixture reply one" in vn._build_prompt_v2(so) and LINE in vn.system_prompt_for(so),
              "internal + recent_voice_replies override: block and line unchanged")
        # --- kill switches restore HEAD behaviour byte-for-byte
        fe.DROP_INTERNAL_QUOTES = False
        fe.RECENT_LINE_ONLY_WITH_BLOCK = False
        for it in ("internal", "human"):
            a, b = state(it, HIST), state(it, HIST)
            check(vn._build_prompt_v2(a) == head._build_prompt_v2(b), f"switches OFF, {it}: user prompt byte-identical to HEAD")
            check(vn.system_prompt_for(a) == head.system_prompt_for(b), f"switches OFF, {it}: system prompt byte-identical to HEAD")
        e = state("human", [])
        check(vn.system_prompt_for(e) == head.system_prompt_for(state("human", [])), "switches OFF, human no history: system prompt identical to HEAD")
        fe.DROP_INTERNAL_QUOTES = True
        fe.RECENT_LINE_ONLY_WITH_BLOCK = True
        # --- the shadow log still records every build, and the drop
        log = fe._LOG
        rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()] if log.exists() else []
        rows = [r for r in rows if r.get("kind") == "quote_block"]
        check(log.resolve().is_relative_to(Path(lab_dir).resolve()), "log path is under the isolated temp dir")
        first = rows[0] if rows else {}
        check(first.get("input_type") == "internal" and first.get("quoted") == [] and
              first.get("dropped") == [R1[:260], R2[:260]], "log row 1 (internal): quoted [], dropped = the two replies")
        second = rows[1] if len(rows) > 1 else {}
        check(second.get("input_type") == "human" and second.get("quoted") == [R1, R2] and second.get("dropped") == [],
              "log row 2 (human): quoted both replies, dropped []")
        offrows = [r for r in rows if r.get("input_type") == "internal" and r.get("quoted") == [R1, R2]]
        check(len(offrows) >= 1 and all(r["dropped"] == [] for r in offrows), "switch-OFF internal row quotes the replies, dropped []")
    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAIL'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
