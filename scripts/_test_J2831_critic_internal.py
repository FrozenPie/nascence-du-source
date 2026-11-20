"""
J-2831 (F-3500, P-0008, D-0551) -- offline test of the Critic's internal-cycle framing. No model call, no live data, no
network. Run from the worktree:  python scripts/_test_J2831_critic_internal.py

Asserts (all against THIS tree):
  1. flag OFF (the shipped default): every cycle type gets the human system prompt and the original stimulus line,
     byte for byte (sha256 of the system prompt pinned to the pre-change text).
  2. flag ON + human cycle: still byte-identical to the human path.
  3. flag ON + internal / timer cycle: the internal prompt, the internal stimulus label, and NO 'What the human said'.
  4. seedless genesis profile keeps its own prompt even with the flag ON.
  5. the internal prompt has no human-request carve-out, tells the Critic to approve plain factual answers to plain
     questions, quotes the axiom's own speaking constraint, and carries no mythic imagery to steer toward.
  6. the node base picks the override up (NodeBase.system_prompt_for is what run() / run_best_of() call).
"""
from __future__ import annotations
import hashlib, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before anything that sets up a lab env)
from core import schema  # noqa: E402
from core.schema import CognitiveState, ReflectionOutput, PerceptionOutput  # noqa: E402
from nodes.critic_node import CriticNode  # noqa: E402
from core.node_base import NodeBase  # noqa: E402

_ = tempfile.gettempdir()   # nothing is written; the test touches no store

HUMAN_PROMPT_SHA256 = "3a248fe9ed7fc2ea14341be2b458b9f60387b4a86d3bd97081109dfa35fe79aa"   # pre-change system_prompt  # re-pinned after J-2834 dropped identity_consistent from the prompts (same chain, later commit)
HUMAN_LINE = "What the human said (the stimulus the draft is responding to):"
QUESTION = "How does the Bluebird's physical arrival alter the garden's soil, light, or scent?"
DRAFT = "Its feet press the damp earth and compact the soil; the landing breaks a patch of sunlight."


def state(input_type: str) -> CognitiveState:
    st = CognitiveState(spirit_name="T", axiom="AXIOM TEXT. When the subject is the world I can speak plainly of the world itself.")
    st.input_type = input_type
    st.raw_input = QUESTION
    st.perception = PerceptionOutput(event_type="input", context_type="question", entities=[], summary="s")
    st.reflection = ReflectionOutput(draft=DRAFT, confidence=0.8, needs_more_memory=False, emotionally_aligned=True)
    return st


def check(name: str, cond: bool) -> None:
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


def main() -> None:
    n = CriticNode()
    human = n.system_prompt
    check("human system prompt is byte-identical to the pre-change text",
          hashlib.sha256(human.encode()).hexdigest() == HUMAN_PROMPT_SHA256)

    # 1. flag OFF (default)
    check("shipped default is OFF", schema.CRITIC_INTERNAL_FRAMING_ON is False)
    for t in ("human", "internal", "timer"):
        st = state(t)
        check(f"flag OFF / {t}: system prompt unchanged", n.system_prompt_for(st) == human)
        p = n._build_prompt(st)
        check(f"flag OFF / {t}: stimulus line unchanged", f"{HUMAN_LINE}\n{QUESTION}\n" in p)
    base_human_prompt = n._build_prompt(state("human"))

    schema.CRITIC_INTERNAL_FRAMING_ON = True
    try:
        # 2. flag ON, human
        st = state("human")
        check("flag ON / human: system prompt unchanged", n.system_prompt_for(st) == human)
        check("flag ON / human: user prompt byte-identical", n._build_prompt(st) == base_human_prompt)

        # 3. flag ON, internal + timer
        for t in ("internal", "timer"):
            st = state(t)
            check(f"flag ON / {t}: internal system prompt", n.system_prompt_for(st) == CriticNode._SYSTEM_INTERNAL)
            p = n._build_prompt(st)
            check(f"flag ON / {t}: no 'What the human said'", "What the human said" not in p)
            check(f"flag ON / {t}: internal stimulus label then the question",
                  f"{CriticNode._STIMULUS_LABEL_INTERNAL}\n{QUESTION}\n" in p)
            check(f"flag ON / {t}: draft + axiom still in the prompt", DRAFT in p and "AXIOM TEXT" in p)
        # the swap is the ONLY difference (so the replay's string-replace equals the real _build_prompt)
        pi, ph = n._build_prompt(state("internal")), base_human_prompt
        check("internal prompt == human prompt with only the stimulus label swapped",
              pi == ph.replace(CriticNode._STIMULUS_LABEL_HUMAN, CriticNode._STIMULUS_LABEL_INTERNAL, 1))

        # 4. seedless
        s = CriticNode(); s.seedless = True
        check("flag ON / seedless / internal: seedless prompt kept", s.system_prompt_for(state("internal")) == s._SEEDLESS_PROMPT)

        # 6. the base-class hook is what the run paths call
        check("NodeBase.run path uses system_prompt_for", "system_prompt_for" in NodeBase.run.__code__.co_names)
        check("NodeBase.run_best_of path uses system_prompt_for", "system_prompt_for" in NodeBase.run_best_of.__code__.co_names)
    finally:
        schema.CRITIC_INTERNAL_FRAMING_ON = False

    # 5. the internal prompt's content
    ip = CriticNode._SYSTEM_INTERNAL
    check("internal prompt has no 'if the human explicitly' carve-out", "the human explicitly" not in ip.lower()
          and "human EXPLICITLY" not in ip)
    check("internal prompt tells the Critic to approve plain answers to plain questions",
          "A PLAIN QUESTION DESERVES A PLAIN ANSWER" in ip and "APPROVE it" in ip)
    check("internal prompt quotes the axiom's speaking constraint", "I can speak plainly of the world itself" in ip)
    check("literalism needs BOTH conditions and never fires on a plain factual question",
          "fires ONLY when BOTH hold" in ip and "NEVER fires when the question was a plain factual" in ip)
    check("corrections must not mention a human and must not supply imagery",
          "never mention a human" in ip and "NEVER supply an image, symbol" in ip)
    for w in ("herald", "divine", "soul", "sacred", "omen", "alchem"):
        check(f"internal prompt carries no steering word {w!r}", w not in ip.lower())
    check("schema block still names the output keys", '"approved"' in ip and '"corrections"' in ip)
    print("ALL PASS")


if __name__ == "__main__":
    main()
