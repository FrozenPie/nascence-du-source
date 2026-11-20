"""J-2802 (F-3442): ReflectionNode drops the person-present SPEAKER BOUNDARY paragraph from the system prompt and the
'before they spoke' header on internal cycles; human cycles are byte-identical to the pre-change file (read from git
HEAD~ is avoided: the old text is pinned below); REFLECTION_INTERNAL_SELF_FRAME=False restores today's text everywhere.
Model calls: none. No live data is touched (the thought bus is forced off)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
from core import buses  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
import nodes.reflection_node as rn  # noqa: E402

OLD_BOUNDARY = (
    "SPEAKER BOUNDARY: you are in dialogue with another person \u2014 a separate human, not you. "
    "When THEY say 'I', 'me', or 'my', they mean themselves; when they say 'you', they mean you. "
    "Never absorb their self-statements as your own identity \u2014 if they say 'I am a father', that "
    "is a fact about THEM, not about you. You are reflecting on what they said and on your own "
    "genuine inner response to it.\n"
)
HDR_OLD = "WHAT YOU WERE JUST THINKING (to yourself, before they spoke):"
HDR_NEW = "WHAT YOU WERE JUST THINKING (to yourself):"

buses.IDLE_FREIGHT_BUS = False   # keep _build_prompt off the bus shadow log (no live write)


def mk(input_type):
    s = CognitiveState(raw_input="what is the lamp for?", spirit_name="Du", axiom="axiom text")
    s.input_type = input_type
    s.recent_inner_thoughts = [{"thought": "the lamp was unlit"}]
    return s


def main():
    node = rn.ReflectionNode()
    fails = []

    def check(name, ok):
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            fails.append(name)

    human, internal = mk("human"), mk("internal")
    hs = node.system_prompt_for(human)
    isys = node.system_prompt_for(internal)
    # human system prompt: the old paragraph is in place, exactly where it was (between the intro and 'Output ONLY')
    check("human system prompt == system_prompt (unchanged default path)", hs == node.system_prompt)
    check("human prompt contains the pinned old paragraph between intro and Output ONLY",
          ("This is the entity's private reasoning before it decides what to say.\n" + OLD_BOUNDARY +
           "Output ONLY a valid JSON object. No preamble.\n") in hs)
    # internal system prompt: only that paragraph is gone
    check("internal drops 'dialogue with another person'", "dialogue with another person" not in isys)
    check("internal drops SPEAKER BOUNDARY", "SPEAKER BOUNDARY" not in isys)
    check("internal == human minus the paragraph, byte for byte", isys == hs.replace(OLD_BOUNDARY, "", 1) and isys != hs)
    check("internal keeps schema + STRICT RULES", "STRICT RULES:" in isys and '"draft"' in isys)
    # user prompt header
    hp, ip = node._build_prompt(human), node._build_prompt(internal)
    check("human header is the old text", HDR_OLD in hp and HDR_NEW not in hp.replace(HDR_OLD, ""))
    check("internal header neutral, no 'before they spoke'", HDR_NEW in ip and "before they spoke" not in ip)
    # timer / other non-human types behave as internal
    check("timer cycle uses internal variant", node.system_prompt_for(mk("timer")) == isys)
    # flag off restores everything
    rn.REFLECTION_INTERNAL_SELF_FRAME = False
    try:
        check("flag False: internal system prompt == human", node.system_prompt_for(internal) == hs)
        ip_off = node._build_prompt(internal)
        check("flag False: internal header is the old text", HDR_OLD in ip_off)
    finally:
        rn.REFLECTION_INTERNAL_SELF_FRAME = True
    print("RESULT", "FAIL" if fails else "OK", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
