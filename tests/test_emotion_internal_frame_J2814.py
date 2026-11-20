from core.schema import CognitiveState
from nodes.emotion_node import EmotionNode


def _st(kind):
    s = CognitiveState("t", "t")
    s.new_cycle("why is the sky dark", input_type=kind)
    s.perception = None
    return s


def test_human_fallback_unchanged():
    out = EmotionNode()._build_prompt(_st("human"))
    assert out == 'The person you are speaking with said:\n"why is the sky dark"'


def test_internal_fallback_no_person():
    out = EmotionNode()._build_prompt(_st("internal"))
    assert "The person" not in out and "your own thought" in out
