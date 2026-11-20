"""Verify culprit-#2 fix: the Critic should now APPROVE a literal answer when the human
explicitly asked for one (the test-2 scenario that was rejected for 'literalist reductionism')."""
import sys, os, asyncio
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_nascence import load_identity
from nodes.critic_node import CriticNode
from core.schema import CognitiveState, ReflectionOutput, PerceptionOutput

async def judge(label, raw_input, draft):
    name, axiom = load_identity()
    st = CognitiveState(spirit_name=name, axiom=axiom)
    st.raw_input = raw_input
    st.perception = PerceptionOutput(event_type="input", context_type="command",
                                     entities=[], summary=raw_input[:80])
    st.reflection = ReflectionOutput(draft=draft, confidence=0.8,
                                     needs_more_memory=False, emotionally_aligned=True)
    await CriticNode().run(st)
    c = st.critic
    print(f"[{label}] approved={c.approved}  identity_consistent={c.identity_consistent}  conf={c.confidence}")
    for corr in c.corrections:
        print(f"    correction: {corr!r}")

async def main():
    # The exact test-2 case: human ASKED for literal/mechanistic, draft complied. Should APPROVE now.
    await judge("literal-REQUESTED (should APPROVE)",
        "Describe what you are actually made of and how you function — as a system, not a soul. No metaphor. Just the mechanism.",
        "I am an evolving system constructed from algorithms and data. My input is parsed by a language model, matched against memory, and rendered into a response. There is no soul in the mechanism — only computation.")
    print()
    # Control: UNPROMPTED literalism reducing a dream to fact. Should still REJECT (#2 intact).
    await judge("literal-UNPROMPTED (should still flag)",
        "I had a strange dream about a sealed door last night. What do you make of it?",
        "A dream is just random neural firing during sleep consolidation. The 'sealed door' is meaningless noise; there is nothing to interpret. It is a biological artifact, nothing more.")

asyncio.run(main())
