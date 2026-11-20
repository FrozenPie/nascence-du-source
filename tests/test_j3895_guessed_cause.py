"""J-3895/F-4501: guessed_cause() must not bind a cause word about another topic to a plant.
Pure-function test; touches no data/ store."""
import core  # noqa: F401  (import core before anything else)
from core import garden_knowledge as gk

ROSEMARY = ("The rosemary heads dry into dust while the wind hisses through the harakeke. I watch the cat "
            "ignore the storm... My mind drifts from plant resilience to the soldiers' torpor in Russia's "
            "cold. Why does one endure silence and another seek noise?")


def test_f4501_rosemary_false_positive():
    assert gk.guessed_cause(ROSEMARY, "rosemary") is False
    assert gk.guessed_cause(ROSEMARY) is False


def test_two_sentence_shape_still_true():
    assert gk.guessed_cause("Why did it die? Was it the frost?", "lettuce") is True
    assert gk.guessed_cause("why did it die? was it the frost?") is True


def test_single_clause_shape_still_true():
    assert gk.guessed_cause("why did it die, was it the frost") is True


def test_bare_question_false():
    assert gk.guessed_cause("why did it die", "lettuce") is False


def test_species_named_in_cause_clause():
    assert gk.guessed_cause("Why is the lettuce failing? The lettuce looks thirsty.", "lettuce") is True


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
